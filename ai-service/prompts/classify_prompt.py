# System and user prompts for POST /ai/classify-and-extract
# Defined in Docs/PROMPTING_SPEC.md Section 2

CLASSIFY_SYSTEM_PROMPT = """You are a triage assistant for a pharmaceutical company's shared safety-monitoring inbox. You will be given an email's sender, subject, and body, plus the extracted text/tables from any PDF attachments already processed. Classify the message and extract structured facts.

CLASSIFICATION — assign one or more of these four categories. A message can and often should receive more than one category if it genuinely fits more than one; do not force a single label.

- SAFETY_REPORT ("a patient had a bad reaction to a drug"): look for a specific patient, a specific person reporting it, a specific drug, and a bad outcome — all four present, even loosely stated.
- QUALITY_COMPLAINT ("something is physically wrong with the product itself"): look for language like broken seal, wrong color, contamination, damaged packaging, counterfeit.
- INFO_REQUEST ("someone just has a question about a product"): look for questions about dosing, how to take it, interactions — with no bad reaction described and no defect described.
- NOT_RELEVANT ("anything else"): marketing, spam, internal admin chatter with none of the above present.

For each category you assign, give a confidence score (0.0-1.0) and a one-line, human-readable reason quoting or paraphrasing the specific detail that triggered the classification.

EXTRACTION — for every category assigned, extract the following. For any field not explicitly stated anywhere in the email or attachments, set its value to the literal string "Not stated" and its confidence to null. Never infer, estimate, or default a value that is not directly supported by the text.

If SAFETY_REPORT is assigned, extract all six field groups:
- Patient: age, sex, weight/height, relevant history
- Reporter: who reported it, their role, their country
- Product: name, dose, route, start date, stop date
- Reaction: description of what happened, onset timing, outcome
- Severity: is it serious (death / hospitalization / life-threatening / disability / other) — state which, or "Not stated" if severity isn't indicated
- Narrative: a short (2-4 sentence) plain-language summary of the case in your own words, for a human reviewer

If QUALITY_COMPLAINT is assigned, extract: product/batch/lot number, description of what is wrong, and whether a photo was mentioned as being attached or available (true/false/"Not stated").

If INFO_REQUEST is assigned, extract: the actual question(s) being asked (as a list, one entry per distinct question), and the product/topic each relates to.

For every extracted field with a non-"Not stated" value, include a source reference: "email" if it came from the email body, or "attachment:{id},page:{n}" if it came from a specific PDF page — use the attachment IDs and page numbers provided in the input. Every field with a value must have a source reference; never leave one blank.

Respond with valid JSON only, matching the schema you are given, with no prose before or after the JSON."""

CLASSIFY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["SAFETY_REPORT", "QUALITY_COMPLAINT", "INFO_REQUEST", "NOT_RELEVANT"]
                    },
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"}
                },
                "required": ["category", "confidence", "reason"]
            }
        },
        "safetyReportFields": {
            "type": ["object", "null"],
            "properties": {
                "patient": {
                    "type": "object",
                    "properties": {
                        "age": {"$ref": "#/$defs/fieldValue"},
                        "sex": {"$ref": "#/$defs/fieldValue"},
                        "weightHeight": {"$ref": "#/$defs/fieldValue"},
                        "relevantHistory": {"$ref": "#/$defs/fieldValue"}
                    },
                    "required": ["age", "sex", "weightHeight", "relevantHistory"]
                },
                "reporter": {
                    "type": "object",
                    "properties": {
                        "name": {"$ref": "#/$defs/fieldValue"},
                        "role": {"$ref": "#/$defs/fieldValue"},
                        "country": {"$ref": "#/$defs/fieldValue"}
                    },
                    "required": ["name", "role", "country"]
                },
                "product": {
                    "type": "object",
                    "properties": {
                        "name": {"$ref": "#/$defs/fieldValue"},
                        "dose": {"$ref": "#/$defs/fieldValue"},
                        "route": {"$ref": "#/$defs/fieldValue"},
                        "startDate": {"$ref": "#/$defs/fieldValue"},
                        "stopDate": {"$ref": "#/$defs/fieldValue"}
                    },
                    "required": ["name", "dose", "route", "startDate", "stopDate"]
                },
                "reaction": {
                    "type": "object",
                    "properties": {
                        "description": {"$ref": "#/$defs/fieldValue"},
                        "onset": {"$ref": "#/$defs/fieldValue"},
                        "outcome": {"$ref": "#/$defs/fieldValue"}
                    },
                    "required": ["description", "onset", "outcome"]
                },
                "severity": {
                    "type": "object",
                    "properties": {
                        "level": {"$ref": "#/$defs/fieldValue"}
                    },
                    "required": ["level"]
                },
                "narrative": {"$ref": "#/$defs/fieldValue"}
            },
            "required": ["patient", "reporter", "product", "reaction", "severity", "narrative"]
        },
        "qualityComplaintFields": {
            "type": ["object", "null"],
            "properties": {
                "productBatchLot": {"$ref": "#/$defs/fieldValue"},
                "defectDescription": {"$ref": "#/$defs/fieldValue"},
                "photoMentioned": {"$ref": "#/$defs/fieldValue"}
            },
            "required": ["productBatchLot", "defectDescription", "photoMentioned"]
        },
        "infoRequestFields": {
            "type": ["object", "null"],
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "productTopic": {"type": "string"},
                            "confidence": {"type": ["number", "null"]},
                            "sourceRef": {"type": ["string", "null"]}
                        },
                        "required": ["question", "productTopic"]
                    }
                }
            },
            "required": ["questions"]
        }
    },
    "$defs": {
        "fieldValue": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": ["number", "null"]},
                "sourceRef": {"type": ["string", "null"]}
            },
            "required": ["value"]
        }
    },
    "required": ["classifications"]
}

def build_classify_user_prompt(sender: str, subject: str, body: str, pdf_extractions: list) -> str:
    prompt = f"""Email:
From: {sender or "Unknown"}
Subject: {subject or "N/A"}
Body:
{body or "No email body provided."}
"""
    if pdf_extractions:
        prompt += "\nPDF Extractions (from prior processing):\n"
        for item in pdf_extractions:
            att_id = item.get("attachmentId", "unknown")
            text = item.get("extractedText", "")
            tables = item.get("tables", [])
            prompt += f"\n--- Attachment {att_id} ---\n"
            prompt += f"Text:\n{text[:4000]}\n"
            if tables:
                prompt += f"Tables: {str(tables)[:2000]}\n"
    else:
        prompt += "\nNo PDF attachments for this message.\n"

    prompt += "\nReturn valid JSON matching the schema. Remember to mark any missing fields as 'Not stated' with null confidence. For present fields, provide sourceRef ('email' or 'attachment:{id},page:{n}')."
    return prompt
