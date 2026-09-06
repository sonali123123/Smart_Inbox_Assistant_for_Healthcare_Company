import json
import re
import logging
from fastapi import APIRouter, HTTPException, status
from google.genai import types

try:
    from ..config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from ..models.classify_models import ClassifyRequest, ClassifyResponse
    from ..prompts.classify_prompt import (
        CLASSIFY_SYSTEM_PROMPT,
        CLASSIFY_RESPONSE_SCHEMA,
        build_classify_user_prompt
    )
except ImportError:
    from config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from models.classify_models import ClassifyRequest, ClassifyResponse
    from prompts.classify_prompt import (
        CLASSIFY_SYSTEM_PROMPT,
        CLASSIFY_RESPONSE_SCHEMA,
        build_classify_user_prompt
    )

router = APIRouter(prefix="/ai", tags=["Classification & Fact Extraction"])
logger = logging.getLogger("ai-service.classify")

def clean_json_response(raw_text: str) -> dict:
    """Strip any markdown fences or explanatory text and parse as JSON."""
    text = raw_text.strip()

    # 1. First attempt: if markdown fences exist, extract content between ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            text = candidate

    # 2. Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Fallback: extract the outermost JSON object {...} or array [...]
    brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    return json.loads(text)

@router.post("/classify-and-extract", response_model=ClassifyResponse)
def classify_and_extract(request: ClassifyRequest):
    """
    Consolidates FR-14 through FR-25 into exactly ONE Gemini call:
    - Multi-label category classification with confidence and reason
    - Deep extraction for Safety Reports (Patient, Reporter, Product, Reaction, Severity, Narrative)
    - Honest uncertainty: 'Not stated' with null confidence for missing fields (never guessing)
    - Quality complaint and Info request structured facts
    - Full source traceability ('email' or 'attachment:{id},page:{n}')
    """
    try:
        client = get_genai_client()

        pdf_extractions_data = [item.model_dump() for item in request.pdfExtractions]
        user_prompt = build_classify_user_prompt(
            sender=request.sender,
            subject=request.subject,
            body=request.emailBody,
            pdf_extractions=pdf_extractions_data
        )

        config = types.GenerateContentConfig(
            system_instruction=CLASSIFY_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ClassifyResponse,
            temperature=TEMPERATURE
        )

        logger.info(f"Calling Gemini ({MODEL_NAME}) for classification: subject='{request.subject}'")
        response = call_gemini_with_retry(
            client=client,
            model=MODEL_NAME,
            contents=[user_prompt],
            config=config
        )

        if not response.text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Empty response from Gemini API"
            )

        data = clean_json_response(response.text)
        return ClassifyResponse(**data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying message '{request.subject}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify and extract: {str(e)}"
        )
