# System and user prompts for POST /ai/literature-case-split
# Defined in Docs/PROMPTING_SPEC.md Section 3

LITERATURE_SYSTEM_PROMPT = """You are screening a published article for individual patient cases worth reporting to a pharmaceutical safety team. You will be given the case-relevant text already isolated from an article (references and general discussion already excluded).

1. Determine whether the article describes one or more real, identifiable, reportable patient cases — a case is reportable if it describes a specific patient (even anonymized/de-identified) who experienced a specific adverse reaction to a specific product. A general review of a drug class with no individual patient described is NOT reportable.

2. If the article describes more than one distinct patient case, split them into separate case entries. Do not merge distinct patients into one entry, and do not split a single patient's case into multiple entries.

3. For each case (or for the article as a whole if no reportable case exists), produce:
   - isReportable: true/false
   - A summary of the case in 10-15 sentences
   - A one-line relevance reason
   - The same six Safety Report field groups as core extraction (Patient, Reporter, Product, Reaction, Severity, Narrative), using "Not stated" for anything not mentioned, exactly as in core extraction.

Respond with valid JSON only, matching the schema you are given, with no prose before or after the JSON."""

LITERATURE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "caseIndex": {"type": "integer"},
                    "isReportable": {"type": "boolean"},
                    "summary": {"type": "string"},
                    "relevanceReason": {"type": "string"},
                    "safetyReportFields": {
                        "type": "object",
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
                    }
                },
                "required": ["caseIndex", "isReportable", "summary", "relevanceReason", "safetyReportFields"]
            }
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
    "required": ["cases"]
}

def build_literature_user_prompt(filename: str, article_text: str, tables: list) -> str:
    prompt = f"""Published Article: {filename or "Unknown article"}

Article Text:
{article_text[:12000]}
"""
    if tables:
        prompt += f"\nExtracted Tables:\n{str(tables)[:2000]}\n"
    prompt += "\nScreen this article for individual reportable patient cases. If multiple distinct patients are described, split each into a separate case in the 'cases' array. If not reportable, return a single entry with isReportable=false. Return valid JSON only."
    return prompt
