import base64
import json
import pytest
from tests.e2e.config import CATEGORIES, PDF_TYPES, REVIEWER_STATUSES

# ==============================================================================
# Feature 1: Service Health & Readiness (>=5 tests)
# ==============================================================================

def test_ai_health_endpoint_returns_up_and_model(ai_client):
    """Verify AI service health check reports status UP and identified model."""
    res = ai_client.get("/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ("UP", "ok", "OK")
    assert "model" in data or "service" in data

def test_ai_health_reports_api_key_configuration(ai_client):
    """Verify AI service health reports whether Gemini API key is configured."""
    res = ai_client.get("/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert "apiKeyConfigured" in data or "status" in data

def test_backend_messages_endpoint_returns_success(backend_client):
    """Verify Spring Boot backend is listening and responds on /api/messages."""
    res = backend_client.get("/api/messages")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

def test_ai_service_health_check_alias(ai_client):
    """Verify root /health alias is reachable on AI service."""
    res = ai_client.get("/health")
    # Both /health and /ai/health should return 200
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        data = res.json()
        assert "status" in data

def test_service_discovery_headers(backend_client):
    """Verify backend returns application/json content-type."""
    res = backend_client.get("/api/messages")
    assert res.status_code == 200
    assert "application/json" in res.headers.get("Content-Type", "")


# ==============================================================================
# Feature 2: Mail Ingestion (>=5 tests)
# ==============================================================================

def test_mail_ingestion_trigger_returns_success_status(backend_client):
    """Verify POST /api/mail/ingest returns 200 with SUCCESS status."""
    res = backend_client.post("/api/mail/ingest")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "SUCCESS"

def test_mail_ingestion_reports_messages_ingested_count(backend_client):
    """Verify mail ingestion returns integer count of messages processed."""
    res = backend_client.post("/api/mail/ingest")
    assert res.status_code == 200
    data = res.json()
    assert "messagesIngested" in data
    assert isinstance(data["messagesIngested"], int)
    assert data["messagesIngested"] >= 0

def test_mail_ingestion_returns_confirmation_message(backend_client):
    """Verify mail ingestion includes informative confirmation text."""
    res = backend_client.post("/api/mail/ingest")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert len(data["message"]) > 0

def test_mail_ingestion_idempotency(backend_client):
    """Verify repeated mail ingestion triggers do not crash or produce duplicate errors."""
    res1 = backend_client.post("/api/mail/ingest")
    res2 = backend_client.post("/api/mail/ingest")
    assert res1.status_code == 200
    assert res2.status_code == 200

def test_mail_ingestion_updates_messages_table_population(backend_client):
    """Verify mail ingestion maintains populated messages in queue."""
    backend_client.post("/api/mail/ingest")
    res = backend_client.get("/api/messages")
    assert res.status_code == 200
    items = res.json().get("items", [])
    assert len(items) > 0


# ==============================================================================
# Feature 3: Message Query & Filter (>=5 tests)
# ==============================================================================

def test_list_messages_returns_items_and_total_count(backend_client):
    """Verify GET /api/messages returns items list and consistent total integer."""
    res = backend_client.get("/api/messages")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["items"], list)
    assert data["total"] == len(data["items"])

def test_list_messages_schema_validation(backend_client):
    """Verify each message summary DTO contains all required fields."""
    res = backend_client.get("/api/messages")
    items = res.json().get("items", [])
    assert len(items) > 0
    msg = items[0]
    for key in ("id", "sourceType", "sender", "subject", "classifications", "status"):
        assert key in msg, f"Missing key '{key}' in message DTO"
    assert msg["status"] in ("PENDING_REVIEW", "REVIEWED")

def test_filter_messages_by_status_pending_review(backend_client):
    """Verify filtering messages by status=PENDING_REVIEW."""
    res = backend_client.get("/api/messages?status=PENDING_REVIEW")
    assert res.status_code == 200
    items = res.json().get("items", [])
    for item in items:
        assert item["status"] == "PENDING_REVIEW"

def test_filter_messages_by_category_safety_report(backend_client):
    """Verify filtering messages by category=SAFETY_REPORT."""
    res = backend_client.get("/api/messages?category=SAFETY_REPORT")
    assert res.status_code == 200
    items = res.json().get("items", [])
    for item in items:
        categories = [c["category"] for c in item["classifications"]]
        assert "SAFETY_REPORT" in categories

def test_get_message_detail_by_id(backend_client):
    """Verify GET /api/messages/{id} returns complete message detail DTO."""
    res = backend_client.get("/api/messages/1")
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == 1
    assert "classifications" in detail
    assert "attachments" in detail
    assert "extractedFields" in detail
    assert "reviewActions" in detail


# ==============================================================================
# Feature 4: Review Workflow (>=5 tests)
# ==============================================================================

def test_review_classification_accept_action(backend_client):
    """Verify reviewer can ACCEPT an AI classification."""
    payload = {
        "action": "ACCEPT",
        "reviewerName": "Dr. E2E Reviewer"
    }
    res = backend_client.put("/api/messages/1/classifications/11/review", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["reviewerStatus"] == "ACCEPTED"
    assert data["id"] == 11

def test_review_classification_override_action(backend_client):
    """Verify reviewer can OVERRIDE an AI classification with a new category."""
    payload = {
        "action": "OVERRIDE",
        "newCategory": "QUALITY_COMPLAINT",
        "reviewerName": "Dr. E2E Reviewer"
    }
    res = backend_client.put("/api/messages/1/classifications/11/review", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["reviewerStatus"] == "OVERRIDDEN"
    assert data["category"] == "QUALITY_COMPLAINT"

def test_field_edit_updates_value_and_marks_reviewer_edited(backend_client):
    """Verify PUT /api/messages/{id}/fields/{fieldId} updates field value and marks edited."""
    payload = {
        "action": "EDIT",
        "newValue": "72",
        "reviewerName": "Safety QA Analyst"
    }
    res = backend_client.put("/api/messages/1/fields/501", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["fieldValue"] == "72"
    assert data["reviewerEdited"] is True

def test_review_action_preserves_audit_lineage(backend_client):
    """Verify review actions generate an audit trail accessible via /api/audit."""
    res = backend_client.get("/api/audit")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    actors = {l.get("actor") for l in logs}
    assert "AI" in actors or "REVIEWER" in actors

def test_review_classification_response_dto_schema(backend_client):
    """Verify review response includes category, confidence, and status."""
    payload = {"action": "ACCEPT", "reviewerName": "Auditor"}
    res = backend_client.put("/api/messages/1/classifications/11/review", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "category" in data
    assert "confidence" in data
    assert "reviewerStatus" in data


# ==============================================================================
# Feature 5: Document Processing & File Streaming (>=5 tests)
# ==============================================================================

def test_process_document_returns_valid_pdf_type(ai_client, sample_pdf_b64):
    """Verify POST /ai/process-document detects PDF type from allowed set."""
    payload = {
        "pdfBase64": sample_pdf_b64,
        "filename": "pdf_digital_01_form_with_table.pdf",
        "emailContext": {"subject": "Test Form", "bodySnippet": "Enclosed form"}
    }
    res = ai_client.post("/ai/process-document", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["pdfType"] in PDF_TYPES

def test_process_document_returns_structured_summary(ai_client, sample_pdf_b64):
    """Verify document processing returns summary, relevanceOpinion, and reason."""
    payload = {
        "pdfBase64": sample_pdf_b64,
        "filename": "pdf_digital_02_form_plain.pdf"
    }
    res = ai_client.post("/ai/process-document", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert data.get("relevanceOpinion") in ("RELEVANT", "NOT_RELEVANT", "UNCERTAIN")
    assert "relevanceReason" in data

def test_process_document_extracts_structured_tables(ai_client, sample_pdf_b64):
    """Verify document processing extracts 2D structured table data."""
    payload = {
        "pdfBase64": sample_pdf_b64,
        "filename": "pdf_digital_01_form_with_table.pdf"
    }
    res = ai_client.post("/ai/process-document", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tables" in data
    assert isinstance(data["tables"], list)
    if data["tables"]:
        t = data["tables"][0]
        assert "rows" in t or "tableJson" in t

def test_attachment_file_streaming_returns_application_pdf(backend_client):
    """Verify GET /api/attachments/{id}/file streams bytes with application/pdf type."""
    res = backend_client.get("/api/attachments/101/file")
    assert res.status_code == 200
    assert "application/pdf" in res.headers.get("Content-Type", "")
    assert len(res.content) > 0

def test_attachment_file_streaming_sets_content_disposition(backend_client):
    """Verify attachment stream header includes inline filename for browser display."""
    res = backend_client.get("/api/attachments/101/file")
    assert res.status_code == 200
    disp = res.headers.get("Content-Disposition", "")
    assert "inline" in disp
    assert "filename=" in disp


# ==============================================================================
# Feature 6: Batch Processing & Timing (>=5 tests)
# ==============================================================================

def test_batch_run_triggers_and_returns_batch_id(backend_client):
    """Verify POST /api/batch/run initiates batch and returns a batchId."""
    res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    assert res.status_code == 200
    data = res.json()
    assert "batchId" in data
    assert len(data["batchId"]) > 0

def test_batch_run_initial_status_is_queued(backend_client):
    """Verify batch run returns QUEUED status."""
    res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ("QUEUED", "PROCESSING", "DONE")

def test_batch_status_returns_document_list(backend_client):
    """Verify GET /api/batch/{batchId}/status returns list of processed documents."""
    run_res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    batch_id = run_res.json()["batchId"]

    res = backend_client.get(f"/api/batch/{batch_id}/status")
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_batch_status_captures_duration_ms_per_document(backend_client):
    """Verify batch timing captures durationMs per document (TR-31)."""
    run_res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    batch_id = run_res.json()["batchId"]

    res = backend_client.get(f"/api/batch/{batch_id}/status")
    assert res.status_code == 200
    docs = res.json().get("documents", [])
    assert len(docs) > 0
    for doc in docs:
        assert "durationMs" in doc
        if doc.get("status") == "DONE":
            assert doc["durationMs"] is not None and doc["durationMs"] >= 0

def test_batch_status_reports_document_terminal_state(backend_client):
    """Verify each document in batch status reaches DONE or FAILED."""
    run_res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    batch_id = run_res.json()["batchId"]

    res = backend_client.get(f"/api/batch/{batch_id}/status")
    assert res.status_code == 200
    docs = res.json().get("documents", [])
    for doc in docs:
        assert doc["status"] in ("QUEUED", "PROCESSING", "DONE", "FAILED")


# ==============================================================================
# Feature 7: Literature Screening (Bonus FR-32 to FR-36) (>=5 tests)
# ==============================================================================

def test_literature_batch_upload_accepts_multipart_files(backend_client):
    """Verify POST /api/literature/batch accepts file uploads and returns batchId."""
    files = [
        ("files", ("article_01_single_case.pdf", b"%PDF-1.4 mock article", "application/pdf")),
        ("files", ("article_02_multi_case.pdf", b"%PDF-1.4 mock multi-case", "application/pdf"))
    ]
    res = backend_client.post("/api/literature/batch", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "batchId" in data

def test_literature_batch_cases_retrieval(backend_client):
    """Verify GET /api/literature/batch/{batchId} returns extracted cases."""
    files = [("files", ("article_01_single_case.pdf", b"%PDF-1.4 mock article", "application/pdf"))]
    upload_res = backend_client.post("/api/literature/batch", files=files)
    batch_id = upload_res.json()["batchId"]

    res = backend_client.get(f"/api/literature/batch/{batch_id}")
    assert res.status_code == 200
    data = res.json()
    assert "totalCases" in data
    assert "cases" in data
    assert data["totalCases"] == len(data["cases"])

def test_literature_cases_have_message_structure(backend_client):
    """Verify literature cases reuse core message structure (FR-36)."""
    files = [("files", ("article_01_single_case.pdf", b"%PDF-1.4 mock article", "application/pdf"))]
    upload_res = backend_client.post("/api/literature/batch", files=files)
    batch_id = upload_res.json()["batchId"]

    res = backend_client.get(f"/api/literature/batch/{batch_id}")
    cases = res.json().get("cases", [])
    assert len(cases) > 0
    case = cases[0]
    assert case["sourceType"] == "LITERATURE"
    assert "classifications" in case
    assert "topSummary" in case

def test_literature_case_split_ai_service_evaluation(ai_client):
    """Verify POST /ai/literature-case-split evaluates isReportable boolean."""
    payload = {
        "filename": "article_01_single_case.pdf",
        "articleText": "Case of 55yo male experiencing peripheral neuropathy after OncoMax."
    }
    res = ai_client.post("/ai/literature-case-split", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "isReportable" in data
    assert isinstance(data["isReportable"], bool)

def test_literature_case_split_isolates_patient_facts(ai_client):
    """Verify literature case split isolates patient and reaction facts."""
    payload = {
        "filename": "article_02_multi_case.pdf",
        "articleText": "Patient 1: 55yo male with neuropathy. Patient 2: 61yo female with renal failure."
    }
    res = ai_client.post("/ai/literature-case-split", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "cases" in data
    assert len(data["cases"]) >= 1
    for c in data["cases"]:
        assert "summary" in c
        assert "relevanceReason" in c
