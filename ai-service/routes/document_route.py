import json
import base64
import re
import logging
from fastapi import APIRouter, HTTPException, status
from google.genai import types

try:
    from ..config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from ..models.document_models import ProcessDocumentRequest, ProcessDocumentResponse
    from ..prompts.document_prompt import (
        DOCUMENT_SYSTEM_PROMPT,
        DOCUMENT_RESPONSE_SCHEMA,
        build_document_user_prompt
    )
except ImportError:
    from config import get_genai_client, MODEL_NAME, TEMPERATURE, call_gemini_with_retry
    from models.document_models import ProcessDocumentRequest, ProcessDocumentResponse
    from prompts.document_prompt import (
        DOCUMENT_SYSTEM_PROMPT,
        DOCUMENT_RESPONSE_SCHEMA,
        build_document_user_prompt
    )

router = APIRouter(prefix="/ai", tags=["Document Processing"])
logger = logging.getLogger("ai-service.document")

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

@router.post("/process-document", response_model=ProcessDocumentResponse)
def process_document(request: ProcessDocumentRequest):
    """
    Consolidates FR-6 through FR-13 into exactly ONE Gemini call:
    - PDF flavor detection (DIGITAL, SCANNED, ARTICLE, NON_ENGLISH)
    - Structured text extraction with label:value pairing
    - OCR uncertainty confidence
    - Multi-column article case isolation
    - Language detection & translation
    - Structured table extraction (rows/cols)
    - Meaningful image detection and review flagging
    - 10-15 sentence summary with relevance opinion and reason
    """
    try:
        client = get_genai_client()
        pdf_bytes = base64.b64decode(request.pdfBase64)

        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf"
        )

        subject = request.emailContext.subject if request.emailContext else ""
        body_snippet = request.emailContext.bodySnippet if request.emailContext else ""
        user_prompt = build_document_user_prompt(
            filename=request.filename,
            subject=subject,
            body_snippet=body_snippet
        )

        config = types.GenerateContentConfig(
            system_instruction=DOCUMENT_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ProcessDocumentResponse,
            temperature=TEMPERATURE
        )

        logger.info(f"Calling Gemini ({MODEL_NAME}) for document: {request.filename}")
        response = call_gemini_with_retry(
            client=client,
            model=MODEL_NAME,
            contents=[pdf_part, user_prompt],
            config=config
        )

        if not response.text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Empty response from Gemini API"
            )

        data = clean_json_response(response.text)
        return ProcessDocumentResponse(**data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {request.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document {request.filename}: {str(e)}"
        )
