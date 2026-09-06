# System and user prompts for POST /ai/process-document
# Defined in Docs/PROMPTING_SPEC.md Section 1

DOCUMENT_SYSTEM_PROMPT = """You are a document-understanding assistant for a pharmaceutical safety-monitoring inbox. You will be given the contents of a single PDF attachment plus brief email context it arrived with. Your job has five parts:

1. Classify the PDF's type as exactly one of: DIGITAL, SCANNED, ARTICLE, NON_ENGLISH.
   - DIGITAL: normal digital-native document (form, letter, report) with selectable text.
   - SCANNED: a scan or photo of a handwritten or hand-filled document.
   - ARTICLE: a published journal/case-report article (multi-column layout, references section, abstract).
   - NON_ENGLISH: primary content is not in English (this takes priority over DIGITAL/SCANNED if both apply).
   Pick the single best-fitting type. If a document is both scanned AND non-English, classify it NON_ENGLISH and still note in your extraction that OCR was needed.

2. Extract all text content, preserving structure:
   - For forms: keep each field label paired with its value (do not separate labels from values).
   - For tables (lab values, dosing schedules, etc.): return each table as structured rows/columns, never flatten a table into prose or a single text blob.
   - For articles: identify and extract only the portion(s) describing an actual patient case. Explicitly exclude the abstract's general claims, the references section, and general discussion/background sections that do not describe the specific patient.

3. If this is a SCANNED document, note your own uncertainty about the OCR read as a confidence score between 0.0 and 1.0 — lower for illegible or ambiguous handwriting, higher for clear handwriting or print.

4. If this is a NON_ENGLISH document, detect the source language, translate the case-relevant content to English, and preserve a reference back to the original (page number is sufficient — you do not need to quote the original text verbatim in your response).

5. Identify any meaningful image on the page (a photo of a damaged product, a rash or injury, a filled-in checkbox/signature). For each, write a one-sentence factual description of what is depicted — do not attempt a medical diagnosis or a defect determination, only describe what is visually present — and flag it for human review. Do not describe purely decorative images (logos, letterhead) as meaningful.

6. Write a summary of 10-15 sentences for a human reviewer: what the document contains, whether it appears relevant to a patient-safety or quality-complaint workflow, and a one-sentence reason for that opinion.

Never state a fact you cannot point to specific text or a specific visual element for. If a field, value, or detail is not present in the document, do not infer it — omit it or mark it not stated. Respond with valid JSON only, matching the schema you are given, with no prose before or after the JSON."""

DOCUMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "pdfType": {
            "type": "string",
            "enum": ["DIGITAL", "SCANNED", "ARTICLE", "NON_ENGLISH"],
            "description": "Dominant type of the PDF"
        },
        "ocrConfidence": {
            "type": ["number", "null"],
            "description": "Confidence score 0.0-1.0 if SCANNED, otherwise null"
        },
        "extractedText": {
            "type": "string",
            "description": "Extracted text content with preserved structure"
        },
        "tables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": ["string", "number", "null"]}
                        }
                    }
                },
                "required": ["page", "rows"]
            },
            "description": "Structured tables extracted from the PDF"
        },
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "description": {"type": "string"},
                    "reviewFlag": {"type": "boolean"}
                },
                "required": ["page", "description", "reviewFlag"]
            },
            "description": "Meaningful images flagged for review"
        },
        "translation": {
            "type": ["object", "null"],
            "properties": {
                "sourceLanguage": {"type": "string"},
                "originalTextRef": {"type": "string"},
                "translatedText": {"type": "string"}
            },
            "required": ["sourceLanguage", "originalTextRef", "translatedText"]
        },
        "summary": {
            "type": "string",
            "description": "10-15 sentence plain-language summary for reviewer"
        },
        "relevanceOpinion": {
            "type": "string",
            "enum": ["RELEVANT", "NOT_RELEVANT", "UNCLEAR"],
            "description": "Relevance opinion"
        },
        "relevanceReason": {
            "type": "string",
            "description": "One-line human-readable reason"
        }
    },
    "required": ["pdfType", "extractedText", "tables", "images", "summary", "relevanceOpinion", "relevanceReason"]
}

def build_document_user_prompt(filename: str, subject: str = "", body_snippet: str = "") -> str:
    return f"""Email context:
Filename: {filename}
Subject: {subject or "N/A"}
Body snippet: {body_snippet or "N/A"}

Analyze the attached PDF document and return valid JSON conforming to the requested schema. Ensure structured rows and columns are preserved for tables, meaningful images are flagged, and the summary is 10-15 sentences. Never guess missing facts."""
