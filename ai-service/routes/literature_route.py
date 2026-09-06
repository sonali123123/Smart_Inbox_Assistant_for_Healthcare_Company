import json
import re
import logging
from fastapi import APIRouter, HTTPException, status
from google.genai import types

try:
    from ..config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from ..models.literature_models import LiteratureSplitRequest, LiteratureSplitResponse
    from ..prompts.literature_prompt import (
        LITERATURE_SYSTEM_PROMPT,
        LITERATURE_RESPONSE_SCHEMA,
        build_literature_user_prompt
    )
except ImportError:
    from config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from models.literature_models import LiteratureSplitRequest, LiteratureSplitResponse
    from prompts.literature_prompt import (
        LITERATURE_SYSTEM_PROMPT,
        LITERATURE_RESPONSE_SCHEMA,
        build_literature_user_prompt
    )

router = APIRouter(prefix="/ai", tags=["Literature Screening"])
logger = logging.getLogger("ai-service.literature")

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

@router.post("/literature-case-split", response_model=LiteratureSplitResponse)
@router.post("/screen-literature", response_model=LiteratureSplitResponse)
def literature_case_split(request: LiteratureSplitRequest):
    """
    Implements bonus FR-32 to FR-36:
    - Screens an article for identifiable, reportable patient cases
    - Splits multiple cases into distinct entries
    - Extracts standard Safety Report fields for each case
    """
    try:
        client = get_genai_client()

        user_prompt = build_literature_user_prompt(
            filename=request.filename or "",
            article_text=request.articleText,
            tables=request.tables
        )

        config = types.GenerateContentConfig(
            system_instruction=LITERATURE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=LiteratureSplitResponse,
            temperature=TEMPERATURE
        )

        logger.info(f"Calling Gemini ({MODEL_NAME}) for literature case split: '{request.filename}'")
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
        return LiteratureSplitResponse(
            filename=request.filename,
            cases=data.get("cases", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error splitting literature cases for '{request.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to split literature cases: {str(e)}"
        )
