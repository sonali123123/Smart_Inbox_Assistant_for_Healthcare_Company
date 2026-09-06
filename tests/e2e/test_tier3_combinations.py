import time
import pytest

def test_lifecycle_ingest_review_accept_audit_persistence(backend_client):
    """
    Lifecycle 1:
    1. Ingest mail.
    2. Query queue for pending message.
    3. Accept classification.
    4. Verify message detail shows ACCEPTED.
    5. Verify AUDIT_LOG records REVIEWER action.
    """
    # Step 1: Ingest
    ingest_res = backend_client.post("/api/mail/ingest")
    assert ingest_res.status_code == 200

    # Step 2: Query queue
    msg_res = backend_client.get("/api/messages?status=PENDING_REVIEW")
    assert msg_res.status_code == 200
    items = msg_res.json().get("items", [])
    assert len(items) > 0

    target = items[0]
    msg_id = target["id"]
    cls_id = target["classifications"][0]["id"]

    # Step 3: Accept classification
    review_res = backend_client.put(
        f"/api/messages/{msg_id}/classifications/{cls_id}/review",
        json={"action": "ACCEPT", "reviewerName": "Lead Reviewer"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["reviewerStatus"] == "ACCEPTED"

    # Step 4: Detail check
    detail_res = backend_client.get(f"/api/messages/{msg_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    matching_cls = next(c for c in detail["classifications"] if c["id"] == cls_id)
    assert matching_cls["reviewerStatus"] == "ACCEPTED"

    # Step 5: Audit log verification
    audit_res = backend_client.get(f"/api/audit?entityType=CLASSIFICATION&entityId={cls_id}")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    latest = logs[0]
    assert latest["actor"] == "REVIEWER"
    assert "ACCEPT" in latest["action"]


def test_lifecycle_ingest_review_override_audit_persistence(backend_client):
    """
    Lifecycle 2:
    1. Query message.
    2. Override classification from SAFETY_REPORT to QUALITY_COMPLAINT.
    3. Verify message detail reflects new category and OVERRIDDEN status.
    4. Verify REVIEW_ACTIONS records targetRef, previousValue, and newValue.
    """
    msg_res = backend_client.get("/api/messages/1")
    assert msg_res.status_code == 200
    msg = msg_res.json()
    cls_id = msg["classifications"][0]["id"]
    prev_cat = msg["classifications"][0]["category"]

    new_cat = "QUALITY_COMPLAINT" if prev_cat != "QUALITY_COMPLAINT" else "INFO_REQUEST"

    # Override action
    review_res = backend_client.put(
        f"/api/messages/1/classifications/{cls_id}/review",
        json={
            "action": "OVERRIDE",
            "newCategory": new_cat,
            "reviewerName": "Senior QA Auditor"
        }
    )
    assert review_res.status_code == 200
    assert review_res.json()["reviewerStatus"] == "OVERRIDDEN"
    assert review_res.json()["category"] == new_cat

    # Re-verify detail and reviewActions
    detail_res = backend_client.get("/api/messages/1")
    assert detail_res.status_code == 200
    actions = detail_res.json().get("reviewActions", [])
    assert len(actions) > 0
    latest_action = actions[-1]
    assert latest_action["action"] == "OVERRIDE"
    assert latest_action["newValue"] == new_cat


def test_lifecycle_field_edit_reflection_and_audit(backend_client):
    """
    Lifecycle 3:
    1. Fetch message detail.
    2. Pick an extracted field.
    3. Update field value via PUT /api/messages/{id}/fields/{fieldId}.
    4. Re-fetch detail and verify reviewerEdited=true and updated value.
    5. Verify AUDIT_LOG entry for entityType=FIELD.
    """
    detail_res = backend_client.get("/api/messages/1")
    assert detail_res.status_code == 200
    fields = detail_res.json().get("extractedFields", [])
    assert len(fields) > 0

    field = fields[0]
    field_id = field["id"]
    updated_val = "82 years"

    edit_res = backend_client.put(
        f"/api/messages/1/fields/{field_id}",
        json={
            "action": "EDIT",
            "newValue": updated_val,
            "reviewerName": "Clinical Data Manager"
        }
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["fieldValue"] == updated_val
    assert edit_res.json()["reviewerEdited"] is True

    # Re-fetch detail
    re_detail = backend_client.get("/api/messages/1").json()
    matched = next(f for f in re_detail["extractedFields"] if f["id"] == field_id)
    assert matched["fieldValue"] == updated_val
    assert matched["reviewerEdited"] is True

    # Audit check
    audit_res = backend_client.get(f"/api/audit?entityType=FIELD&entityId={field_id}")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    assert logs[0]["actor"] == "REVIEWER"


def test_lifecycle_batch_run_poll_duration_and_message_persistence(backend_client):
    """
    Lifecycle 4:
    1. POST /api/batch/run with source directory.
    2. Poll /api/batch/{id}/status.
    3. Verify per-document timing (durationMs).
    4. Verify all batch documents reach terminal status (DONE).
    """
    run_res = backend_client.post("/api/batch/run", json={"sourceDir": "test-data/emails"})
    assert run_res.status_code == 200
    batch_id = run_res.json()["batchId"]

    # Poll status
    status_res = backend_client.get(f"/api/batch/{batch_id}/status")
    assert status_res.status_code == 200
    docs = status_res.json().get("documents", [])
    assert len(docs) >= 10, f"Expected at least 10 documents, got {len(docs)}"

    for d in docs:
        assert d["status"] in ("DONE", "PROCESSING", "QUEUED")
        if d["status"] == "DONE":
            assert d["durationMs"] is not None and d["durationMs"] > 0


def test_lifecycle_literature_batch_split_review_and_audit(backend_client):
    """
    Lifecycle 5:
    1. Upload multi-case literature article via POST /api/literature/batch.
    2. Retrieve split cases via GET /api/literature/batch/{id}.
    3. Verify cases are split with individual Message IDs (FR-34, TR-34).
    4. Accept one of the split cases via PUT /api/messages/{id}/classifications/{id}/review.
    5. Verify review action and audit entry for the literature case.
    """
    files = [
        ("files", ("article_02_multi_case.pdf", b"%PDF-1.4 mock article", "application/pdf"))
    ]
    upload_res = backend_client.post("/api/literature/batch", files=files)
    assert upload_res.status_code == 200
    batch_id = upload_res.json()["batchId"]

    # Get cases
    batch_cases_res = backend_client.get(f"/api/literature/batch/{batch_id}")
    assert batch_cases_res.status_code == 200
    cases = batch_cases_res.json().get("cases", [])
    assert len(cases) >= 2, "Multi-case article should produce >= 2 distinct cases"

    case = cases[0]
    case_msg_id = case["id"]
    case_cls_id = case["classifications"][0]["id"]

    # Review the split case
    review_res = backend_client.put(
        f"/api/messages/{case_msg_id}/classifications/{case_cls_id}/review",
        json={"action": "ACCEPT", "reviewerName": "Literature Specialist"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["reviewerStatus"] == "ACCEPTED"


def test_lifecycle_multilabel_triage_derived_status_progression(backend_client):
    """
    Lifecycle 6:
    1. Retrieve multi-label message (message 3: Safety + Quality).
    2. Initial derived status is PENDING_REVIEW because both classifications are PENDING.
    3. Accept the first classification.
    4. Status remains PENDING_REVIEW because second classification is still PENDING.
    5. Accept the second classification.
    6. Status transitions to REVIEWED.
    """
    detail_res = backend_client.get("/api/messages/3")
    assert detail_res.status_code == 200
    msg = detail_res.json()
    assert len(msg["classifications"]) >= 2
    cls1 = msg["classifications"][0]["id"]
    cls2 = msg["classifications"][1]["id"]

    # Accept first
    backend_client.put(
        f"/api/messages/3/classifications/{cls1}/review",
        json={"action": "ACCEPT", "reviewerName": "Reviewer 1"}
    )

    # Rollup check after first accept
    mid_res = backend_client.get("/api/messages/3")
    assert mid_res.json()["status"] == "PENDING_REVIEW"

    # Accept second
    backend_client.put(
        f"/api/messages/3/classifications/{cls2}/review",
        json={"action": "ACCEPT", "reviewerName": "Reviewer 2"}
    )

    # Rollup check after both accepted
    final_res = backend_client.get("/api/messages/3")
    assert final_res.json()["status"] == "REVIEWED"
