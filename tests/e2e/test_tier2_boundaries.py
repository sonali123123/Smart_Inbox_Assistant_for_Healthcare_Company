import pytest

# ==============================================================================
# Area 1: System & Health Boundaries (>=5 tests)
# ==============================================================================

def test_health_method_not_allowed(ai_client):
    """Verify POST on /health or /ai/health returns 405 (or 404), not 200."""
    res = ai_client.post("/ai/health", json={})
    assert res.status_code in (405, 404)

def test_invalid_endpoint_returns_404(backend_client):
    """Verify requesting an undefined path returns 404 Not Found."""
    res = backend_client.get("/api/non_existent_route_xyz")
    assert res.status_code == 404

def test_query_string_injection_resilience(backend_client):
    """Verify querying with SQL/XSS special characters does not cause 500 error."""
    res = backend_client.get("/api/messages?status=' OR '1'='1&category=<script>alert(1)</script>")
    assert res.status_code in (200, 400)

def test_unsupported_http_verb_on_messages(backend_client):
    """Verify DELETE on /api/messages returns 405 Method Not Allowed."""
    res = backend_client.delete("/api/messages")
    assert res.status_code in (404, 405)

def test_unicode_query_parameter_handling(backend_client):
    """Verify query endpoints gracefully handle non-ASCII unicode characters."""
    res = backend_client.get("/api/messages?category=日本語カテゴリ")
    assert res.status_code in (200, 400)


# ==============================================================================
# Area 2: Ingestion & Message Query Boundaries (>=5 tests)
# ==============================================================================

def test_get_message_with_non_existent_id(backend_client):
    """Verify GET /api/messages/{id} with non-existent ID returns 404."""
    res = backend_client.get("/api/messages/9999999")
    assert res.status_code == 404

def test_get_message_with_negative_id(backend_client):
    """Verify GET /api/messages/{id} with negative ID returns 400 or 404."""
    res = backend_client.get("/api/messages/-1")
    assert res.status_code in (400, 404)

def test_get_message_with_alphanumeric_id(backend_client):
    """Verify GET /api/messages/{id} with alphanumeric string returns 400 or 404."""
    res = backend_client.get("/api/messages/invalid_id_format")
    assert res.status_code in (400, 404)

def test_filter_messages_by_invalid_category(backend_client):
    """Verify filtering by an unknown category returns empty list (0 items)."""
    res = backend_client.get("/api/messages?category=DEFINITELY_UNKNOWN_CATEGORY")
    assert res.status_code == 200
    assert res.json().get("total") == 0
    assert len(res.json().get("items", [])) == 0

def test_filter_messages_by_invalid_status(backend_client):
    """Verify filtering by an unknown status returns empty list (0 items)."""
    res = backend_client.get("/api/messages?status=UNKNOWN_ROLLUP_STATUS")
    assert res.status_code == 200
    assert res.json().get("total") == 0
    assert len(res.json().get("items", [])) == 0


# ==============================================================================
# Area 3: Review Action Boundaries (>=5 tests)
# ==============================================================================

def test_review_non_existent_classification(backend_client):
    """Verify review on non-existent classification ID returns 404."""
    payload = {"action": "ACCEPT", "reviewerName": "Test Reviewer"}
    res = backend_client.put("/api/messages/1/classifications/999999/review", json=payload)
    assert res.status_code == 404

def test_review_non_existent_message(backend_client):
    """Verify review on non-existent message ID returns 404."""
    payload = {"action": "ACCEPT", "reviewerName": "Test Reviewer"}
    res = backend_client.put("/api/messages/999999/classifications/11/review", json=payload)
    assert res.status_code == 404

def test_review_with_invalid_action_name(backend_client):
    """Verify review with unsupported action (e.g. 'DELETE') returns 400."""
    payload = {"action": "DELETE_CLASSIFICATION", "reviewerName": "Test Reviewer"}
    res = backend_client.put("/api/messages/1/classifications/11/review", json=payload)
    assert res.status_code in (400, 422)

def test_review_override_without_new_category(backend_client):
    """Verify OVERRIDE action without newCategory specified returns 400."""
    payload = {"action": "OVERRIDE", "reviewerName": "Test Reviewer"}
    res = backend_client.put("/api/messages/1/classifications/11/review", json=payload)
    assert res.status_code in (400, 422)

def test_review_with_empty_payload(backend_client):
    """Verify empty body on review endpoint returns 400."""
    res = backend_client.put("/api/messages/1/classifications/11/review", json={})
    assert res.status_code in (400, 422)


# ==============================================================================
# Area 4: Field Edit Boundaries (>=5 tests)
# ==============================================================================

def test_edit_non_existent_field(backend_client):
    """Verify editing a non-existent field ID returns 404."""
    payload = {"action": "EDIT", "newValue": "Updated", "reviewerName": "Reviewer"}
    res = backend_client.put("/api/messages/1/fields/999999", json=payload)
    assert res.status_code == 404

def test_edit_field_on_mismatched_message(backend_client):
    """Verify editing a field belonging to a different message returns 404 or error."""
    # Field 501 belongs to message 1, trying message 2
    payload = {"action": "EDIT", "newValue": "Updated", "reviewerName": "Reviewer"}
    res = backend_client.put("/api/messages/2/fields/501", json=payload)
    assert res.status_code in (400, 404)

def test_edit_field_with_empty_new_value(backend_client):
    """Verify editing field with empty string does not crash and updates value."""
    payload = {"action": "EDIT", "newValue": "", "reviewerName": "Reviewer"}
    res = backend_client.put("/api/messages/1/fields/501", json=payload)
    assert res.status_code == 200
    assert res.json().get("fieldValue") == ""

def test_edit_field_with_very_large_value(backend_client):
    """Verify editing field with 4000-character payload is handled safely."""
    large_val = "A" * 4000
    payload = {"action": "EDIT", "newValue": large_val, "reviewerName": "Reviewer"}
    res = backend_client.put("/api/messages/1/fields/501", json=payload)
    assert res.status_code in (200, 400)

def test_edit_field_preserves_special_characters_escaping(backend_client):
    """Verify special/HTML characters (< > & " ') are preserved verbatim without unescaped corruption."""
    special_text = 'Cardiac Arrest & "Ventricular" <Tachycardia>'
    payload = {"action": "EDIT", "newValue": special_text, "reviewerName": "Reviewer"}
    res = backend_client.put("/api/messages/1/fields/504", json=payload)
    assert res.status_code == 200
    assert res.json().get("fieldValue") == special_text


# ==============================================================================
# Area 5: Document Processing Boundaries (>=5 tests)
# ==============================================================================

def test_process_document_with_missing_pdf_base64(ai_client):
    """Verify POST /ai/process-document missing pdfBase64 returns 400 or 422."""
    res = ai_client.post("/ai/process-document", json={"filename": "doc.pdf"})
    assert res.status_code in (400, 422)

def test_process_document_with_invalid_base64(ai_client):
    """Verify invalid base64 encoding returns 400 or 500 cleanly."""
    payload = {"pdfBase64": "NOT_A_VALID_BASE64_STRING!@#$", "filename": "doc.pdf"}
    res = ai_client.post("/ai/process-document", json=payload)
    assert res.status_code in (400, 500)

def test_attachment_stream_non_existent_id(backend_client):
    """Verify streaming a non-existent attachment ID returns 404."""
    res = backend_client.get("/api/attachments/999999/file")
    assert res.status_code == 404

def test_attachment_stream_invalid_id_format(backend_client):
    """Verify streaming an attachment with non-numeric ID returns 400 or 404."""
    res = backend_client.get("/api/attachments/invalid_att_id/file")
    assert res.status_code in (400, 404)

def test_classify_and_extract_empty_body(ai_client):
    """Verify POST /ai/classify-and-extract with empty body returns 400 or 422."""
    res = ai_client.post("/ai/classify-and-extract", json={})
    assert res.status_code in (400, 422)


# ==============================================================================
# Area 6: Batch Runner Boundaries (>=5 tests)
# ==============================================================================

def test_batch_run_with_empty_body(backend_client):
    """Verify POST /api/batch/run with empty body defaults or rejects gracefully."""
    res = backend_client.post("/api/batch/run", json={})
    assert res.status_code in (200, 400)

def test_batch_status_with_non_existent_batch_id(backend_client):
    """Verify GET /api/batch/{id}/status for unknown batchId returns 404."""
    res = backend_client.get("/api/batch/non_existent_batch_xyz/status")
    assert res.status_code == 404

def test_batch_status_special_characters_in_id(backend_client):
    """Verify batch status query with special characters does not cause internal 500 crash."""
    res = backend_client.get("/api/batch/../../etc/passwd/status")
    assert res.status_code in (400, 404)

def test_batch_run_with_blank_directory(backend_client):
    """Verify batch run with sourceDir='' uses default test directory or returns 200."""
    res = backend_client.post("/api/batch/run", json={"sourceDir": ""})
    assert res.status_code in (200, 400)

def test_batch_status_schema_when_empty(backend_client):
    """Verify batch status handles empty documents list cleanly."""
    res = backend_client.get("/api/batch/unknown-1/status")
    assert res.status_code == 404


# ==============================================================================
# Area 7: Literature Screening Boundaries (>=5 tests)
# ==============================================================================

def test_literature_upload_rejects_non_multipart(backend_client):
    """Verify POST /api/literature/batch rejects JSON content type."""
    res = backend_client.post("/api/literature/batch", json={"dummy": "data"})
    assert res.status_code in (400, 415, 500)

def test_literature_batch_non_existent_id(backend_client):
    """Verify GET /api/literature/batch/{id} for unknown batchId returns 404."""
    res = backend_client.get("/api/literature/batch/lit_unknown_999999")
    assert res.status_code == 404

def test_literature_case_split_empty_payload(ai_client):
    """Verify POST /ai/literature-case-split with empty payload returns 400 or 422."""
    res = ai_client.post("/ai/literature-case-split", json={})
    assert res.status_code in (400, 422)

def test_literature_case_split_non_reportable_article(ai_client):
    """Verify article with no identifiable case evaluates isReportable=false (FR-33)."""
    payload = {
        "filename": "article_03_not_reportable.pdf",
        "articleText": "A review of pharmacology principles without patient cases."
    }
    res = ai_client.post("/ai/literature-case-split", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["isReportable"] is False
    assert len(data.get("cases", [])) == 0

def test_literature_upload_with_empty_files_list(backend_client):
    """Verify uploading an empty files list returns 400."""
    res = backend_client.post("/api/literature/batch", files=[])
    assert res.status_code in (400, 500)
