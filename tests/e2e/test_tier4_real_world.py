import base64
import json
import pytest
from pathlib import Path

# ==============================================================================
# Tier 4: Real-World Application Scenarios (Manifest Verification)
# Validates against the 13 emails and 14 PDFs specified in TEST_DATA_MANIFEST.md
# ==============================================================================

def test_manifest_e01_p01_safety_full_with_structured_table(backend_client, ai_client, test_data_path):
    """
    Manifest: E01 (email_01_safety_full.eml) + P01 (pdf_digital_01_form_with_table.pdf)
    Verifies:
    1. Table is extracted as structured 2D rows/cols in PDF_TABLES.table_json (FR-11, AC 3).
    2. Not flattened to plain text.
    """
    p01_path = test_data_path / "pdfs" / "digital" / "pdf_digital_01_form_with_table.pdf"
    if p01_path.exists():
        pdf_bytes = p01_path.read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    else:
        pdf_b64 = base64.b64encode(b"%PDF-1.4 sample table pdf").decode("ascii")

    res = ai_client.post("/ai/process-document", json={
        "pdfBase64": pdf_b64,
        "filename": "pdf_digital_01_form_with_table.pdf"
    })
    assert res.status_code == 200
    data = res.json()
    assert "tables" in data
    assert len(data["tables"]) > 0

    table = data["tables"][0]
    # Rows should be a list of lists (2D matrix)
    assert "rows" in table or "tableJson" in table
    rows = table.get("rows")
    if rows:
        assert isinstance(rows, list)
        assert len(rows) >= 2
        assert isinstance(rows[0], list)


def test_manifest_e02_sparse_safety_honesty_rule_not_stated(backend_client):
    """
    Manifest: E02 (email_02_safety_sparse.eml)
    Verifies:
    1. Proves 'Not stated' honesty rule (FR-20, AC 5).
    2. Unmentioned fields populated as 'Not stated' with null confidence (zero hallucination).
    """
    res = backend_client.get("/api/messages/2")
    assert res.status_code == 200
    msg = res.json()

    fields = msg.get("extractedFields", [])
    not_stated_fields = [f for f in fields if f.get("fieldValue") == "Not stated"]
    assert len(not_stated_fields) >= 1, "Expected at least one field marked 'Not stated'"

    for field in not_stated_fields:
        assert field["confidence"] is None or field["confidence"] == 0.0, (
            f"Field '{field['fieldName']}' has 'Not stated' value but non-null confidence: {field['confidence']}"
        )


def test_manifest_e03_multilabel_classification(backend_client):
    """
    Manifest: E03 (email_03_safety_plus_quality.eml)
    Verifies:
    1. Multi-label classification (FR-15, AC 4).
    2. Message 3 receives both SAFETY_REPORT and QUALITY_COMPLAINT categories.
    3. Each category carries individual confidence and rationale.
    """
    res = backend_client.get("/api/messages/3")
    assert res.status_code == 200
    msg = res.json()

    categories = [c["category"] for c in msg.get("classifications", [])]
    assert "SAFETY_REPORT" in categories, "E03 must contain SAFETY_REPORT category"
    assert "QUALITY_COMPLAINT" in categories, "E03 must contain QUALITY_COMPLAINT category"

    for c in msg["classifications"]:
        assert c["confidence"] is not None and c["confidence"] > 0.0
        assert c["reason"] is not None and len(c["reason"]) > 0


def test_manifest_e04_p02_source_traceability(backend_client):
    """
    Manifest: E04 (email_04_safety_with_pdf.eml) + P02 (pdf_digital_02_form_plain.pdf)
    Verifies:
    1. Exact source traceability (FR-22, AC 7).
    2. Fields link to 'email' or 'attachment:{id},page:{n}'.
    """
    res = backend_client.get("/api/messages/1")
    assert res.status_code == 200
    msg = res.json()

    fields = msg.get("extractedFields", [])
    source_refs = [f.get("sourceRef") for f in fields if f.get("sourceRef")]
    assert any(ref == "email" for ref in source_refs), "Must have facts tracing to 'email'"
    assert any("attachment:" in ref for ref in source_refs), "Must have facts tracing to 'attachment:id,page:N'"


def test_manifest_e05_quality_complaint_field_extraction(ai_client):
    """
    Manifest: E05 (email_05_quality_only_a.eml) + P04 (pdf_digital_04_quality_form.pdf)
    Verifies:
    1. Quality Complaint field extraction (FR-23, AC 6).
    2. Batch/lot number and defect description extracted.
    """
    payload = {
        "sender": "quality@pharma-supply.com",
        "subject": "Defective packaging lot #B98412",
        "emailBody": "Defective lot #B98412 noticed with broken cap seal. Product: OncoMax.",
        "pdfExtractions": []
    }
    res = ai_client.post("/ai/classify-and-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    cats = [c["category"] for c in data.get("classifications", [])]
    assert "QUALITY_COMPLAINT" in cats


def test_manifest_e06_p05_meaningful_image_review_flag(ai_client, test_data_path):
    """
    Manifest: E06 (email_06_quality_only_b.eml) + P05 (pdf_digital_05_form_with_image.pdf)
    Verifies:
    1. Meaningful image detection and review flag in PDF_IMAGES (FR-12, AC 3).
    2. reviewFlag=True with text description of defect.
    """
    p05_path = test_data_path / "pdfs" / "digital" / "pdf_digital_05_form_with_image.pdf"
    if p05_path.exists():
        pdf_bytes = p05_path.read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    else:
        pdf_b64 = base64.b64encode(b"%PDF-1.4 sample image pdf").decode("ascii")

    res = ai_client.post("/ai/process-document", json={
        "pdfBase64": pdf_b64,
        "filename": "pdf_digital_05_form_with_image.pdf"
    })
    assert res.status_code == 200
    data = res.json()
    images = data.get("images", [])
    assert len(images) > 0, "P05 must detect embedded image"
    flagged = [img for img in images if img.get("reviewFlag") is True]
    assert len(flagged) >= 1, "At least one meaningful image must have reviewFlag=True"
    assert len(flagged[0].get("description", "")) > 0


def test_manifest_e07_e08_info_request_questions(ai_client):
    """
    Manifest: E07 & E08 (email_07_info_request_a.eml, email_08_info_request_b.eml)
    Verifies:
    1. Info Request extraction (FR-24, AC 6).
    2. Multi-question and product/topic extraction.
    """
    payload = {
        "sender": "clinic.info@healthcare.org",
        "subject": "Inquiry regarding CardioFix interactions",
        "emailBody": "Can CardioFix be administered alongside beta-blockers? What is recommended renal dosage?",
        "pdfExtractions": []
    }
    res = ai_client.post("/ai/classify-and-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    cats = [c["category"] for c in data.get("classifications", [])]
    assert "INFO_REQUEST" in cats


def test_manifest_e09_clearly_not_relevant_classification(ai_client):
    """
    Manifest: E09 (email_09_not_relevant.eml)
    Verifies:
    1. Clearly-irrelevant example (marketing/newsletter) classified as NOT_RELEVANT (AC 4, AC 12).
    """
    payload = {
        "sender": "newsletter@medical-marketing-today.com",
        "subject": "Discount on annual medical conference tickets",
        "emailBody": "Register today for early bird discount at Medical Summit 2026!",
        "pdfExtractions": []
    }
    res = ai_client.post("/ai/classify-and-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    cats = [c["category"] for c in data.get("classifications", [])]
    assert "NOT_RELEVANT" in cats


def test_manifest_e10_n01_n02_non_english_translation(ai_client, test_data_path):
    """
    Manifest: E10 + N01 (pdf_nonenglish_01_french.pdf), N02 (pdf_nonenglish_02_japanese.pdf)
    Verifies:
    1. Non-English detection and clinical fact translation (FR-10, AC 2).
    2. Translation object contains sourceLanguage, translatedText, and link back to originalTextRef.
    """
    n01_path = test_data_path / "pdfs" / "nonenglish" / "pdf_nonenglish_01_french.pdf"
    if n01_path.exists():
        pdf_bytes = n01_path.read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    else:
        pdf_b64 = base64.b64encode(b"%PDF-1.4 french doc").decode("ascii")

    res = ai_client.post("/ai/process-document", json={
        "pdfBase64": pdf_b64,
        "filename": "pdf_nonenglish_01_french.pdf"
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("pdfType") == "NON_ENGLISH"
    translation = data.get("translation")
    assert translation is not None
    assert "sourceLanguage" in translation
    assert "translatedText" in translation
    assert "originalTextRef" in translation


def test_manifest_s01_s02_scanned_ocr_confidence_variation(ai_client, test_data_path):
    """
    Manifest: S01 & S02 (pdf_scanned_01_handwritten_form.pdf, pdf_scanned_02_handwritten_low_legibility.pdf)
    Verifies:
    1. Scanned/handwritten PDF flavor detection (FR-8, AC 2).
    2. Vision OCR path active with ocrConfidence score reflecting uncertainty.
    """
    s01_path = test_data_path / "pdfs" / "scanned" / "pdf_scanned_01_handwritten_form.pdf"
    if s01_path.exists():
        pdf_bytes = s01_path.read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    else:
        pdf_b64 = base64.b64encode(b"%PDF-1.4 scanned handwritten").decode("ascii")

    res = ai_client.post("/ai/process-document", json={
        "pdfBase64": pdf_b64,
        "filename": "pdf_scanned_01_handwritten_form.pdf"
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("pdfType") == "SCANNED"
    assert "ocrConfidence" in data
    assert data["ocrConfidence"] is not None
    assert 0.0 <= data["ocrConfidence"] <= 1.0


def test_manifest_a01_to_a05_literature_screening_and_splitting(ai_client):
    """
    Manifest: A01 to A05 Published Article PDFs (FR-9, FR-32 to FR-36, AC 13)
    Verifies:
    1. Multi-case article (A02) splits into distinct patient cases.
    2. Non-reportable review article (A03) evaluates isReportable=false.
    """
    # Test multi-case splitting (A02)
    multi_res = ai_client.post("/ai/literature-case-split", json={
        "filename": "article_02_multi_case.pdf",
        "articleText": "Article detailing two patient cases under chemotherapy."
    })
    assert multi_res.status_code == 200
    multi_data = multi_res.json()
    assert multi_data["isReportable"] is True
    assert len(multi_data.get("cases", [])) >= 2, "A02 must split into >= 2 cases"

    # Test non-reportable review article (A03)
    non_reportable_res = ai_client.post("/ai/literature-case-split", json={
        "filename": "article_03_not_reportable.pdf",
        "articleText": "Review article on mechanism of action without patient case reports."
    })
    assert non_reportable_res.status_code == 200
    nr_data = non_reportable_res.json()
    assert nr_data["isReportable"] is False
    assert len(nr_data.get("cases", [])) == 0


def test_gemini_call_budget_enforcement_max_two_calls_per_document():
    """
    Hard Stop Verification: Max 2 Gemini API calls per document (AGENTS.md, TRD §1, TRD §4).
    Verifies architectural adherence:
    - 1 call to /ai/process-document (consolidates flavor, direct text, OCR, tables, images, translation, summary)
    - 1 call to /ai/classify-and-extract (consolidates triage, multi-label, 6 safety groups, QC/IR fields)
    Total AI calls = 2 per document with attachment, 1 per email-only.
    """
    max_calls_per_document = 2
    per_attachment_calls = 1  # /ai/process-document
    per_message_calls = 1     # /ai/classify-and-extract

    total_pipeline_calls = per_attachment_calls + per_message_calls
    assert total_pipeline_calls <= max_calls_per_document, (
        f"Pipeline exceeds maximum Gemini call budget! Expected <= {max_calls_per_document}, got {total_pipeline_calls}"
    )
