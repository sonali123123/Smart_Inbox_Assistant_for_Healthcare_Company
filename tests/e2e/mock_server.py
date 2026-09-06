import http.server
import json
import threading
import time
import urllib.parse
from datetime import datetime, timezone

class MockServiceHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress standard logging to keep test console clean
        pass

    def _send_json(self, status_code: int, data: any):
        self.close_connection = True
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Connection", "close")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # AI Health check
        if path in ("/health", "/ai/health"):
            self._send_json(200, {
                "status": "UP",
                "service": "smart-inbox-ai-service",
                "model": "gemini-3.5-flash-lite",
                "apiKeyConfigured": True
            })
            return

        # List messages: GET /api/messages
        if path == "/api/messages":
            status_filter = query.get("status", [None])[0]
            cat_filter = query.get("category", [None])[0]
            src_filter = query.get("sourceType", [None])[0]

            results = []
            for m in self.server.state["messages"]:
                if status_filter and m["status"].upper() != status_filter.upper():
                    continue
                if cat_filter:
                    has_cat = any(c["category"].upper() == cat_filter.upper() for c in m["classifications"])
                    if not has_cat:
                        continue
                if src_filter and m["sourceType"].upper() != src_filter.upper():
                    continue
                results.append(m)

            self._send_json(200, {
                "items": results,
                "total": len(results)
            })
            return

        # Detail message: GET /api/messages/{id}
        if path.startswith("/api/messages/"):
            msg_id_str = path[len("/api/messages/"):]
            if "/" not in msg_id_str:
                try:
                    msg_id = int(msg_id_str)
                except ValueError:
                    self._send_json(400, {"error": "Invalid message ID format"})
                    return

                msg = next((m for m in self.server.state["messages"] if m["id"] == msg_id), None)
                if not msg:
                    self._send_json(404, {"error": f"Message not found with ID: {msg_id}"})
                    return

                # Build detail payload
                detail = dict(msg)
                detail["extractedFields"] = [f for f in self.server.state["extractedFields"] if f["messageId"] == msg_id]
                detail["attachments"] = [a for a in self.server.state["attachments"] if a["messageId"] == msg_id]
                detail["reviewActions"] = [ra for ra in self.server.state["reviewActions"] if ra["messageId"] == msg_id]
                self._send_json(200, detail)
                return

        # Attachment file streaming: GET /api/attachments/{id}/file
        if path.startswith("/api/attachments/") and path.endswith("/file"):
            att_id_str = path.split("/")[3]
            try:
                att_id = int(att_id_str)
            except ValueError:
                self._send_json(400, {"error": "Invalid attachment ID"})
                return

            att = next((a for a in self.server.state["attachments"] if a["id"] == att_id), None)
            if not att:
                self._send_json(404, {"error": f"Attachment not found: {att_id}"})
                return

            dummy_pdf = b"%PDF-1.4 mock pdf content for testing stream extraction"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'inline; filename="{att["filename"]}"')
            self.send_header("Content-Length", str(len(dummy_pdf)))
            self.end_headers()
            self.wfile.write(dummy_pdf)
            return

        # Batch status: GET /api/batch/{batchId}/status
        if path.startswith("/api/batch/") and path.endswith("/status"):
            batch_id = path.split("/")[3]
            batch = self.server.state["batches"].get(batch_id)
            if not batch:
                self._send_json(404, {"error": f"Batch not found: {batch_id}"})
                return
            self._send_json(200, batch)
            return

        # Literature batch cases: GET /api/literature/batch/{batchId}
        if path.startswith("/api/literature/batch/"):
            batch_id = path[len("/api/literature/batch/"):]
            lit_batch = self.server.state["literatureBatches"].get(batch_id)
            if not lit_batch:
                self._send_json(404, {"error": f"Literature batch not found: {batch_id}"})
                return
            self._send_json(200, {
                "batchId": batch_id,
                "totalCases": len(lit_batch["cases"]),
                "cases": lit_batch["cases"]
            })
            return

        # Audit logs: GET /api/audit
        if path == "/api/audit":
            entity_type = query.get("entityType", [None])[0]
            entity_id = query.get("entityId", [None])[0]

            logs = self.server.state["auditLogs"]
            if entity_type:
                logs = [l for l in logs if l["entityType"].upper() == entity_type.upper()]
            if entity_id:
                try:
                    eid = int(entity_id)
                    logs = [l for l in logs if l["entityId"] == eid]
                except ValueError:
                    pass
            self._send_json(200, logs)
            return

        self._send_json(404, {"error": "Endpoint not found", "path": path})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Mail ingest: POST /api/mail/ingest
        if path == "/api/mail/ingest":
            count = len(self.server.state["messages"])
            self._send_json(200, {
                "status": "SUCCESS",
                "messagesIngested": count,
                "message": f"Ingestion completed. {count} new messages enqueued for processing."
            })
            return

        # Batch run: POST /api/batch/run
        if path == "/api/batch/run":
            data = self._read_json()
            if data is None:
                self._send_json(400, {"error": "Malformed JSON payload"})
                return

            batch_id = f"batch-{int(time.time()*1000)}"
            doc_statuses = [
                {"filename": "email_01_safety_full.eml", "status": "DONE", "durationMs": 450, "errorMessage": None},
                {"filename": "email_02_safety_sparse.eml", "status": "DONE", "durationMs": 380, "errorMessage": None},
                {"filename": "email_03_safety_plus_quality.eml", "status": "DONE", "durationMs": 520, "errorMessage": None},
                {"filename": "email_04_safety_with_pdf.eml", "status": "DONE", "durationMs": 610, "errorMessage": None},
                {"filename": "email_05_quality_only_a.eml", "status": "DONE", "durationMs": 340, "errorMessage": None},
                {"filename": "email_06_quality_only_b.eml", "status": "DONE", "durationMs": 420, "errorMessage": None},
                {"filename": "email_07_info_request_a.eml", "status": "DONE", "durationMs": 290, "errorMessage": None},
                {"filename": "email_08_info_request_b.eml", "status": "DONE", "durationMs": 310, "errorMessage": None},
                {"filename": "email_09_not_relevant.eml", "status": "DONE", "durationMs": 250, "errorMessage": None},
                {"filename": "email_10_safety_non_english_context.eml", "status": "DONE", "durationMs": 580, "errorMessage": None},
                {"filename": "email_11_safety_scanned.eml", "status": "DONE", "durationMs": 720, "errorMessage": None},
                {"filename": "email_12_safety_scanned_2.eml", "status": "DONE", "durationMs": 810, "errorMessage": None},
                {"filename": "email_13_safety_japanese.eml", "status": "DONE", "durationMs": 690, "errorMessage": None}
            ]
            self.server.state["batches"][batch_id] = {
                "batchId": batch_id,
                "documents": doc_statuses
            }
            self._send_json(200, {"batchId": batch_id, "status": "QUEUED"})
            return

        # Literature upload: POST /api/literature/batch
        if path == "/api/literature/batch":
            content_type = self.headers.get("Content-Type", "")
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len > 0:
                self.rfile.read(content_len)

            if "multipart/form-data" not in content_type:
                self._send_json(400, {"error": "Expected multipart/form-data"})
                return

            batch_id = f"lit-{int(time.time()*1000)}"
            # Create synthetic split cases
            case1 = {
                "id": 201,
                "sourceType": "LITERATURE",
                "sender": "Journal of Clinical Pharmacology",
                "subject": "Article Case 1: Anaphylaxis to Drug A",
                "receivedDate": datetime.now(timezone.utc).isoformat(),
                "classifications": [
                    {"id": 301, "category": "SAFETY_REPORT", "confidence": 0.93, "reason": "Severe reaction described", "reviewerStatus": "PENDING"}
                ],
                "topSummary": "A 52-year-old female experienced anaphylaxis following first dose.",
                "status": "PENDING_REVIEW",
                "attachmentCount": 1
            }
            case2 = {
                "id": 202,
                "sourceType": "LITERATURE",
                "sender": "Journal of Clinical Pharmacology",
                "subject": "Article Case 2: Acute Kidney Injury to Drug A",
                "receivedDate": datetime.now(timezone.utc).isoformat(),
                "classifications": [
                    {"id": 302, "category": "SAFETY_REPORT", "confidence": 0.89, "reason": "Hospitalization due to AKI", "reviewerStatus": "PENDING"}
                ],
                "topSummary": "A 64-year-old male developed acute renal failure on day 7.",
                "status": "PENDING_REVIEW",
                "attachmentCount": 1
            }

            self.server.state["messages"].extend([case1, case2])
            self.server.state["literatureBatches"][batch_id] = {
                "batchId": batch_id,
                "cases": [case1, case2]
            }

            # Add audit entry
            self.server.state["auditLogs"].append({
                "id": len(self.server.state["auditLogs"]) + 1,
                "entityType": "LITERATURE_BATCH",
                "entityId": 201,
                "action": "UPLOAD_BATCH",
                "actor": "REVIEWER",
                "detailsJson": json.dumps({"batchId": batch_id, "casesSplit": 2}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            self._send_json(200, {"batchId": batch_id, "status": "QUEUED"})
            return

        # AI Document Process: POST /ai/process-document
        if path == "/ai/process-document":
            data = self._read_json()
            if not data or "pdfBase64" not in data:
                self._send_json(400, {"error": "Missing pdfBase64 in request body"})
                return

            try:
                import base64
                base64.b64decode(data["pdfBase64"], validate=True)
            except Exception:
                self._send_json(400, {"error": "Invalid base64 payload"})
                return

            filename = data.get("filename", "unknown.pdf")
            pdf_type = "DIGITAL"
            ocr_conf = None
            tables = []
            images = []
            translation = None

            if "scanned" in filename.lower():
                pdf_type = "SCANNED"
                ocr_conf = 0.78
            elif "article" in filename.lower():
                pdf_type = "ARTICLE"
            elif "nonenglish" in filename.lower() or "french" in filename.lower() or "japanese" in filename.lower():
                pdf_type = "NON_ENGLISH"
                translation = {
                    "sourceLanguage": "fr" if "french" in filename.lower() else "ja",
                    "originalTextRef": "Section 2.1",
                    "translatedText": "Patient experienced severe urticaria and facial edema."
                }

            if "table" in filename.lower() or "form" in filename.lower():
                tables.append({
                    "page": 1,
                    "rows": [
                        ["Test Name", "Result", "Reference Range"],
                        ["WBC", "11.5 x10^9/L", "4.5-11.0"],
                        ["ALT", "85 U/L", "7-56"]
                    ]
                })

            if "image" in filename.lower():
                images.append({
                    "page": 1,
                    "description": "Photograph of broken vial neck and defective seal.",
                    "reviewFlag": True
                })

            resp = {
                "pdfType": pdf_type,
                "ocrConfidence": ocr_conf,
                "extractedText": "Directly extracted clinical adverse event report.",
                "tables": tables,
                "images": images,
                "translation": translation,
                "summary": "This document contains a formal adverse event intake record.",
                "relevanceOpinion": "RELEVANT",
                "relevanceReason": "Contains identifiable patient, suspect drug, and adverse event reaction."
            }
            self._send_json(200, resp)
            return

        # AI Classify and Extract: POST /ai/classify-and-extract
        if path == "/ai/classify-and-extract":
            data = self._read_json()
            if not data:
                self._send_json(400, {"error": "Missing JSON body"})
                return

            subject = data.get("subject", "")
            body = data.get("emailBody", "")

            classifications = []
            if "safety" in subject.lower() or "reaction" in body.lower() or "patient" in body.lower():
                classifications.append({
                    "category": "SAFETY_REPORT",
                    "confidence": 0.92,
                    "reason": "Mentions adverse reaction and hospitalization."
                })
            if "defect" in subject.lower() or "quality" in subject.lower() or "vial" in body.lower():
                classifications.append({
                    "category": "QUALITY_COMPLAINT",
                    "confidence": 0.88,
                    "reason": "Mentions damaged packaging and broken seal."
                })
            if "info" in subject.lower() or "question" in body.lower() or "inquiry" in subject.lower():
                classifications.append({
                    "category": "INFO_REQUEST",
                    "confidence": 0.85,
                    "reason": "Medical inquiry regarding dosage and interactions."
                })
            if not classifications:
                classifications.append({
                    "category": "NOT_RELEVANT",
                    "confidence": 0.95,
                    "reason": "Marketing announcement without clinical content."
                })

            resp = {
                "classifications": classifications,
                "safetyReportFields": {
                    "patient": {
                        "age": {"value": "68", "confidence": 0.95, "sourceRef": "email"},
                        "sex": {"value": "Female", "confidence": 0.90, "sourceRef": "email"}
                    },
                    "reporter": {
                        "role": {"value": "Physician", "confidence": 0.92, "sourceRef": "email"}
                    },
                    "product": {
                        "name": {"value": "CardioFix", "confidence": 0.98, "sourceRef": "attachment:1,page:1"}
                    },
                    "reaction": {
                        "description": {"value": "Anaphylaxis", "confidence": 0.96, "sourceRef": "email"}
                    },
                    "severity": {
                        "level": {"value": "Hospitalization", "confidence": 0.94, "sourceRef": "email"}
                    },
                    "narrative": {
                        "value": "68-year-old female experienced anaphylaxis requiring emergency admission.",
                        "confidence": 0.91
                    }
                },
                "qualityComplaintFields": None,
                "infoRequestFields": None
            }
            self._send_json(200, resp)
            return

        # AI Literature Case Split: POST /ai/literature-case-split
        if path == "/ai/literature-case-split":
            data = self._read_json()
            if not data:
                self._send_json(400, {"error": "Missing JSON payload"})
                return

            filename = data.get("filename", "")
            is_reportable = "not_reportable" not in filename.lower()
            cases = []

            if is_reportable:
                cases.append({
                    "caseIndex": 1,
                    "patient": {"age": "55", "sex": "Male"},
                    "product": "OncoMax 50mg",
                    "reaction": "Grade 3 Neuropathy",
                    "summary": "55yo male developed peripheral neuropathy following cycle 3.",
                    "relevanceReason": "Identifiable patient and unexpected severe adverse event."
                })
                if "multi_case" in filename.lower():
                    cases.append({
                        "caseIndex": 2,
                        "patient": {"age": "61", "sex": "Female"},
                        "product": "OncoMax 50mg",
                        "reaction": "Acute Renal Impairment",
                        "summary": "61yo female experienced creatinine elevation on cycle 2.",
                        "relevanceReason": "Identifiable patient with serious ADR."
                    })

            self._send_json(200, {
                "filename": filename,
                "isReportable": is_reportable,
                "cases": cases
            })
            return

        self._send_json(404, {"error": "Endpoint not found", "path": path})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Review classification: PUT /api/messages/{id}/classifications/{classificationId}/review
        if "/classifications/" in path and path.endswith("/review"):
            parts = path.split("/")
            # ["", "api", "messages", "{id}", "classifications", "{classificationId}", "review"]
            if len(parts) == 7:
                try:
                    msg_id = int(parts[3])
                    cls_id = int(parts[5])
                except ValueError:
                    self._send_json(400, {"error": "Invalid ID format"})
                    return

                body = self._read_json()
                if body is None:
                    self._send_json(400, {"error": "Malformed request body"})
                    return

                action = body.get("action")
                new_cat = body.get("newCategory")
                reviewer_name = body.get("reviewerName")

                if not action or action.upper() not in ("ACCEPT", "OVERRIDE"):
                    self._send_json(400, {"error": f"Invalid review action: {action}. Must be ACCEPT or OVERRIDE"})
                    return

                if action.upper() == "OVERRIDE" and not new_cat:
                    self._send_json(400, {"error": "newCategory is required for OVERRIDE action"})
                    return

                msg = next((m for m in self.server.state["messages"] if m["id"] == msg_id), None)
                if not msg:
                    self._send_json(404, {"error": f"Message not found: {msg_id}"})
                    return

                cls = next((c for c in msg["classifications"] if c["id"] == cls_id), None)
                if not cls:
                    self._send_json(404, {"error": f"Classification not found: {cls_id}"})
                    return

                prev_val = cls["category"]
                new_val = new_cat if action.upper() == "OVERRIDE" else prev_val

                cls["reviewerStatus"] = "ACCEPTED" if action.upper() == "ACCEPT" else "OVERRIDDEN"
                if action.upper() == "OVERRIDE":
                    cls["category"] = new_cat

                # Update derived status
                has_pending = any(c["reviewerStatus"] == "PENDING" for c in msg["classifications"])
                msg["status"] = "PENDING_REVIEW" if has_pending else "REVIEWED"

                # Record ReviewAction
                self.server.state["reviewActions"].append({
                    "id": len(self.server.state["reviewActions"]) + 1,
                    "messageId": msg_id,
                    "reviewerName": reviewer_name or "Anonymous",
                    "action": action.upper(),
                    "targetRef": f"classification:{cls_id}",
                    "previousValue": prev_val,
                    "newValue": new_val,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                # Record AuditLog
                self.server.state["auditLogs"].append({
                    "id": len(self.server.state["auditLogs"]) + 1,
                    "entityType": "CLASSIFICATION",
                    "entityId": cls_id,
                    "action": f"{action.upper()}_CLASSIFICATION",
                    "actor": "REVIEWER",
                    "detailsJson": json.dumps({"reviewer": reviewer_name, "prev": prev_val, "new": new_val}),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                self._send_json(200, {
                    "id": cls["id"],
                    "category": cls["category"],
                    "confidence": cls["confidence"],
                    "reason": cls["reason"],
                    "reviewerStatus": cls["reviewerStatus"]
                })
                return

        # Field edit: PUT /api/messages/{id}/fields/{fieldId}
        if "/fields/" in path:
            parts = path.split("/")
            # ["", "api", "messages", "{id}", "fields", "{fieldId}"]
            if len(parts) == 6:
                try:
                    msg_id = int(parts[3])
                    field_id = int(parts[5])
                except ValueError:
                    self._send_json(400, {"error": "Invalid ID format"})
                    return

                body = self._read_json()
                if body is None:
                    self._send_json(400, {"error": "Malformed request body"})
                    return

                new_value = body.get("newValue")
                reviewer_name = body.get("reviewerName")

                field = next((f for f in self.server.state["extractedFields"] if f["id"] == field_id and f["messageId"] == msg_id), None)
                if not field:
                    self._send_json(404, {"error": f"Field not found: {field_id} on message {msg_id}"})
                    return

                prev_val = field["fieldValue"]
                field["fieldValue"] = new_value
                field["reviewerEdited"] = True

                self.server.state["reviewActions"].append({
                    "id": len(self.server.state["reviewActions"]) + 1,
                    "messageId": msg_id,
                    "reviewerName": reviewer_name or "Anonymous",
                    "action": "EDIT",
                    "targetRef": f"field:{field_id}",
                    "previousValue": prev_val,
                    "newValue": new_value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                self.server.state["auditLogs"].append({
                    "id": len(self.server.state["auditLogs"]) + 1,
                    "entityType": "FIELD",
                    "entityId": field_id,
                    "action": "EDIT_FIELD",
                    "actor": "REVIEWER",
                    "detailsJson": json.dumps({"reviewer": reviewer_name, "prev": prev_val, "new": new_value}),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                self._send_json(200, {
                    "id": field["id"],
                    "attachmentId": field.get("attachmentId"),
                    "fieldGroup": field["fieldGroup"],
                    "fieldName": field["fieldName"],
                    "fieldValue": field["fieldValue"],
                    "confidence": field["confidence"],
                    "sourceType": field["sourceType"],
                    "sourceRef": field["sourceRef"],
                    "reviewerEdited": field["reviewerEdited"]
                })
                return

        self._send_json(404, {"error": "Endpoint not found", "path": path})

    def do_DELETE(self):
        self.send_error(405, "Method Not Allowed")


def create_initial_state():
    return {
        "messages": [
            {
                "id": 1,
                "sourceType": "EMAIL",
                "sender": "dr.patel@hospital-central.org",
                "subject": "Adverse event report - CardioFix severe rash",
                "receivedDate": "2026-08-20T10:15:00Z",
                "bodyText": "Patient experienced widespread anaphylaxis and rash following 2nd dose of CardioFix.",
                "messageIdHeader": "<msg-001@hospital-central.org>",
                "createdAt": "2026-08-20T10:15:30Z",
                "status": "PENDING_REVIEW",
                "attachmentCount": 1,
                "topSummary": "Adverse drug reaction report describing anaphylaxis and rash after CardioFix.",
                "classifications": [
                    {
                        "id": 11,
                        "category": "SAFETY_REPORT",
                        "confidence": 0.95,
                        "reason": "Identifies patient, suspect drug, and severe reaction.",
                        "reviewerStatus": "PENDING"
                    }
                ]
            },
            {
                "id": 2,
                "sourceType": "EMAIL",
                "sender": "nurse.jane@clinic.org",
                "subject": "Sparse reaction note",
                "receivedDate": "2026-08-21T09:00:00Z",
                "bodyText": "Patient had severe reaction to Drug X, hospitalized. No other info.",
                "messageIdHeader": "<msg-002@clinic.org>",
                "createdAt": "2026-08-21T09:00:30Z",
                "status": "PENDING_REVIEW",
                "attachmentCount": 0,
                "topSummary": "Sparse safety report lacking patient demographics and reporter details.",
                "classifications": [
                    {
                        "id": 12,
                        "category": "SAFETY_REPORT",
                        "confidence": 0.72,
                        "reason": "Mention of reaction and hospitalization but sparse facts.",
                        "reviewerStatus": "PENDING"
                    }
                ]
            },
            {
                "id": 3,
                "sourceType": "EMAIL",
                "sender": "pharmacist.smith@pharma-care.com",
                "subject": "Broken seal and severe allergic reaction",
                "receivedDate": "2026-08-22T14:30:00Z",
                "bodyText": "The vial seal was broken and cloudy liquid injected. Patient subsequently suffered anaphylactic shock.",
                "messageIdHeader": "<msg-003@pharma-care.com>",
                "createdAt": "2026-08-22T14:30:45Z",
                "status": "PENDING_REVIEW",
                "attachmentCount": 0,
                "topSummary": "Dual event: broken seal packaging defect and anaphylactic reaction.",
                "classifications": [
                    {
                        "id": 13,
                        "category": "SAFETY_REPORT",
                        "confidence": 0.91,
                        "reason": "Severe allergic reaction and anaphylactic shock.",
                        "reviewerStatus": "PENDING"
                    },
                    {
                        "id": 14,
                        "category": "QUALITY_COMPLAINT",
                        "confidence": 0.89,
                        "reason": "Broken vial seal and cloudy formulation.",
                        "reviewerStatus": "PENDING"
                    }
                ]
            }
        ],
        "attachments": [
            {
                "id": 101,
                "messageId": 1,
                "filename": "pdf_digital_01_form_with_table.pdf",
                "contentType": "application/pdf",
                "isPdf": True,
                "pdfType": "DIGITAL",
                "loggedOnly": False,
                "summary": {
                    "id": 1,
                    "summaryText": "Digital AE intake form containing lab test values table.",
                    "relevanceOpinion": "RELEVANT",
                    "relevanceReason": "Formal hospital AE intake document."
                },
                "tables": [
                    {
                        "id": 1,
                        "pageNumber": 1,
                        "tableJson": json.dumps([
                            ["Lab Test", "Value", "Units"],
                            ["WBC", "12.4", "x10^9/L"],
                            ["CRP", "48", "mg/L"]
                        ])
                    }
                ],
                "images": [],
                "translation": None
            }
        ],
        "extractedFields": [
            {
                "id": 501,
                "messageId": 1,
                "attachmentId": 101,
                "fieldGroup": "PATIENT",
                "fieldName": "age",
                "fieldValue": "68",
                "confidence": 0.95,
                "sourceType": "EMAIL",
                "sourceRef": "email",
                "reviewerEdited": False
            },
            {
                "id": 502,
                "messageId": 1,
                "attachmentId": 101,
                "fieldGroup": "PATIENT",
                "fieldName": "sex",
                "fieldValue": "Female",
                "confidence": 0.92,
                "sourceType": "EMAIL",
                "sourceRef": "email",
                "reviewerEdited": False
            },
            {
                "id": 503,
                "messageId": 1,
                "attachmentId": 101,
                "fieldGroup": "PRODUCT",
                "fieldName": "name",
                "fieldValue": "CardioFix",
                "confidence": 0.98,
                "sourceType": "attachment:101,page:1",
                "sourceRef": "attachment:101,page:1",
                "reviewerEdited": False
            },
            {
                "id": 504,
                "messageId": 1,
                "attachmentId": 101,
                "fieldGroup": "REACTION",
                "fieldName": "description",
                "fieldValue": "Anaphylaxis and rash",
                "confidence": 0.94,
                "sourceType": "EMAIL",
                "sourceRef": "email",
                "reviewerEdited": False
            },
            {
                "id": 505,
                "messageId": 2,
                "attachmentId": None,
                "fieldGroup": "PATIENT",
                "fieldName": "age",
                "fieldValue": "Not stated",
                "confidence": None,
                "sourceType": "EMAIL",
                "sourceRef": "email",
                "reviewerEdited": False
            },
            {
                "id": 506,
                "messageId": 2,
                "attachmentId": None,
                "fieldGroup": "PATIENT",
                "fieldName": "sex",
                "fieldValue": "Not stated",
                "confidence": None,
                "sourceType": "EMAIL",
                "sourceRef": "email",
                "reviewerEdited": False
            }
        ],
        "reviewActions": [],
        "auditLogs": [
            {
                "id": 1,
                "entityType": "MESSAGE",
                "entityId": 1,
                "action": "AI_INGEST",
                "actor": "AI",
                "detailsJson": json.dumps({"classifiedCategories": ["SAFETY_REPORT"]}),
                "timestamp": "2026-08-20T10:16:00Z"
            }
        ],
        "batches": {},
        "literatureBatches": {}
    }


class MockServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        self.state = create_initial_state()

    def start(self):
        handler = MockServiceHandler
        self.httpd = http.server.ThreadingHTTPServer((self.host, self.port), handler)
        self.httpd.state = self.state
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        # Verify it is listening
        time.sleep(0.1)

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def reset_state(self):
        self.state = create_initial_state()
        if self.httpd:
            self.httpd.state = self.state
