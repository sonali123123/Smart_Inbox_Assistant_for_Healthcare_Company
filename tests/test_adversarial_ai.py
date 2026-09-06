"""
Adversarial Stress Test Suite for Python AI Service
Milestone M1 — Challenger 1

Tests:
1. Route discovery and endpoint registration in FastAPI app.
2. Adversarial stress-testing of `clean_json_response` across all 3 routers:
   - classify_route
   - document_route
   - literature_route
3. Live HTTP route invocation using FastAPI TestClient:
   - Health checks (/health, /ai/health)
   - 422 validation on malformed inputs
   - Mocked Gemini responses with conversational chatter and fences
"""

import sys
import os
import json
import re
try:
    import pytest
except ImportError:
    class DummyMark:
        def parametrize(self, *args, **kwargs):
            return lambda func: func
        def xfail(self, *args, **kwargs):
            return lambda func: func
    class DummyPytest:
        mark = DummyMark()
        def raises(self, exc):
            class RaisesContext:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    return exc_type is not None and issubclass(exc_type, exc)
            return RaisesContext()
        def fail(self, msg):
            raise AssertionError(msg)
    pytest = DummyPytest()
from pathlib import Path

# Ensure ai-service is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_SERVICE_DIR = PROJECT_ROOT / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Import main application and route modules
import main
from routes import classify_route, document_route, literature_route


# ============================================================================
# 1. ROUTE DISCOVERY TESTS
# ============================================================================

def test_fastapi_app_instance():
    """Verify FastAPI app is properly instantiated."""
    assert isinstance(main.app, FastAPI)
    assert main.app.title == "Smart Inbox Assistant - AI Service"


def test_route_discovery():
    """Verify all 6 required routes are registered with correct HTTP methods."""
    openapi_paths = main.app.openapi().get("paths", {})
    routes = {
        path: {m.upper() for m in methods.keys()}
        for path, methods in openapi_paths.items()
    }
    
    expected_routes = {
        "/health": {"GET"},
        "/ai/health": {"GET"},
        "/ai/process-document": {"POST"},
        "/ai/classify-and-extract": {"POST"},
        "/ai/literature-case-split": {"POST"},
        "/ai/screen-literature": {"POST"},
    }
    
    for path, methods in expected_routes.items():
        assert path in routes, f"Missing route: {path}"
        assert methods.issubset(routes[path]), f"Route {path} missing methods {methods - routes[path]}"


# ============================================================================
# 2. ADVERSARIAL STRESS TESTS FOR clean_json_response
# ============================================================================

CLEANERS = [
    ("classify_route", classify_route.clean_json_response),
    ("document_route", document_route.clean_json_response),
    ("literature_route", literature_route.clean_json_response),
]

ADVERSARIAL_CASES = [
    # Case 1: Standard fenced JSON with lowercase tag
    (
        "standard_fence_lowercase",
        "```json\n{\"patient\": \"John Doe\", \"age\": 45, \"valid\": true}\n```",
        {"patient": "John Doe", "age": 45, "valid": True}
    ),
    # Case 2: Uppercase language identifier
    (
        "standard_fence_uppercase",
        "```JSON\n{\"patient\": \"Jane Doe\", \"severity\": \"HIGH\"}\n```",
        {"patient": "Jane Doe", "severity": "HIGH"}
    ),
    # Case 3: Mixed-case language identifier
    (
        "mixed_case_fence",
        "```Json\n{\"category\": \"SAFETY_REPORT\"}\n```",
        {"category": "SAFETY_REPORT"}
    ),
    # Case 4: Unlabeled markdown fence
    (
        "unlabeled_fence",
        "```\n{\"product\": \"Amoxicillin 500mg\", \"batch\": \"B12345\"}\n```",
        {"product": "Amoxicillin 500mg", "batch": "B12345"}
    ),
    # Case 5: Pure JSON without fences
    (
        "pure_json_no_fences",
        "{\"status\": \"CONFIRMED\", \"confidence\": 0.98, \"items\": [1, 2, 3]}",
        {"status": "CONFIRMED", "confidence": 0.98, "items": [1, 2, 3]}
    ),
    # Case 6: Leading and trailing whitespace with newlines
    (
        "padded_whitespace",
        "  \n\n  ```json\n{\"trimmed\": true}\n```  \n\n  ",
        {"trimmed": True}
    ),
    # Case 7: Conversational preface and trailing commentary
    (
        "conversational_chatter",
        "Here is the extraction result from the document:\n```json\n{\"reaction\": \"Rash\", \"outcome\": \"Recovered\"}\n```\nPlease let me know if you need additional details.",
        {"reaction": "Rash", "outcome": "Recovered"}
    ),
    # Case 8: Leading markdown headers, subheaders, and bullet lists
    (
        "markdown_headers_and_bullets",
        "# Clinical Assessment Report\n## Extraction Summary\n* Model: Gemini 3.5 Flash-Lite\n* Status: Completed\n\n```json\n{\"report_id\": \"CR-9921\", \"flags\": [\"URGENT\"]}\n```\n\n### End of Report",
        {"report_id": "CR-9921", "flags": ["URGENT"]}
    ),
    # Case 9: Fence tag with trailing spaces and tabs before newline
    (
        "fence_with_trailing_tag_whitespace",
        "```json   \t  \n{\"whitespace_after_tag\": true}\n```",
        {"whitespace_after_tag": True}
    ),
    # Case 10: Unfenced JSON embedded in conversational prose
    (
        "unfenced_with_prose",
        "Certainly! The model identified: {\"verdict\": \"ACCEPT\", \"score\": 0.91} as requested.",
        {"verdict": "ACCEPT", "score": 0.91}
    ),
    # Case 11: Deeply nested objects and arrays
    (
        "deeply_nested_structure",
        "```json\n{\"level1\": {\"level2\": {\"level3\": [{\"key\": \"val\", \"nested_list\": [10, 20, {\"deep\": true}]}]}}}\n```",
        {"level1": {"level2": {"level3": [{"key": "val", "nested_list": [10, 20, {"deep": True}]}]}}}
    ),
    # Case 12: Escaped double quotes inside string fields
    (
        "escaped_double_quotes",
        "```json\n{\"note\": \"Patient stated: \\\"I experienced dizziness after taking the pill.\\\"\", \"code\": 101}\n```",
        {"note": 'Patient stated: "I experienced dizziness after taking the pill."', "code": 101}
    ),
    # Case 13: Escaped backslashes, newlines, and tabs in string values
    (
        "escaped_special_chars",
        "```json\n{\"filepath\": \"C:\\\\Data\\\\Records\\\\file.pdf\", \"multiline\": \"Line 1\\nLine 2\\tTabbed\"}\n```",
        {"filepath": "C:\\Data\\Records\\file.pdf", "multiline": "Line 1\nLine 2\tTabbed"}
    ),
    # Case 14: Top-level JSON Array
    (
        "top_level_array",
        "```json\n[{\"caseId\": 1, \"type\": \"ADVERSE_EVENT\"}, {\"caseId\": 2, \"type\": \"COMPLAINT\"}]\n```",
        [{"caseId": 1, "type": "ADVERSE_EVENT"}, {"caseId": 2, "type": "COMPLAINT"}]
    ),
    # Case 15: Numeric edge cases (negative numbers, floats, scientific notation, zero)
    (
        "numeric_variations",
        "```json\n{\"neg_int\": -42, \"float_val\": -0.00543, \"scientific\": 1.25e-4, \"zero\": 0}\n```",
        {"neg_int": -42, "float_val": -0.00543, "scientific": 1.25e-4, "zero": 0}
    ),
    # Case 16: Booleans and null values
    (
        "booleans_and_null",
        "```json\n{\"is_active\": true, \"is_deleted\": false, \"alternate_name\": null}\n```",
        {"is_active": True, "is_deleted": False, "alternate_name": None}
    ),
    # Case 17: Unicode, accents, Japanese/Chinese, and emojis
    (
        "unicode_and_emojis",
        "```json\n{\"patient\": \"José García\", \"hospital\": \"Hôpital de Genève\", \"japanese\": \"有害事象\", \"emoji\": \"💊⚠️\"}\n```",
        {"patient": "José García", "hospital": "Hôpital de Genève", "japanese": "有害事象", "emoji": "💊⚠️"}
    ),
    # Case 18: Multiple fences where the first fence IS the JSON and second is notes
    (
        "multiple_fences_json_first",
        "```json\n{\"result\": \"success\"}\n```\nAdditional info:\n```text\nProcess completed in 300ms\n```",
        {"result": "success"}
    ),
]


@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
@pytest.mark.parametrize("case_id,raw_input,expected", ADVERSARIAL_CASES)
def test_clean_json_response_cases(router_name, cleaner, case_id, raw_input, expected):
    """Stress-test clean_json_response across routers on diverse adversarial cases."""
    parsed = cleaner(raw_input)
    assert parsed == expected, f"[{router_name}] Failed on case {case_id}: expected {expected}, got {parsed}"


# ============================================================================
# 3. EDGE CASE BOUNDARY & FAILURE BEHAVIOR
# ============================================================================

@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
def test_clean_json_response_empty_string(router_name, cleaner):
    """Verify cleaner raises JSONDecodeError on empty input."""
    with pytest.raises(json.JSONDecodeError):
        cleaner("")


@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
def test_clean_json_response_whitespace_only(router_name, cleaner):
    """Verify cleaner raises JSONDecodeError on whitespace-only input."""
    with pytest.raises(json.JSONDecodeError):
        cleaner("   \n\t  \n  ")


@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
def test_clean_json_response_invalid_json(router_name, cleaner):
    """Verify cleaner raises JSONDecodeError on unparseable garbage."""
    with pytest.raises(json.JSONDecodeError):
        cleaner("This is completely non-JSON plain text with no brackets at all.")


# ============================================================================
# 4. CRITICAL ADVERSARIAL FAILURE MODES (CHALLENGE SUITE)
# ============================================================================

@pytest.mark.xfail(reason="Vulnerability: Destructive assignment 'text = candidate' drops valid subsequent JSON fences", strict=False)
@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
def test_clean_json_multiple_fences_non_json_first(router_name, cleaner):
    """
    Adversarial Challenge:
    LLM provides an explanatory non-JSON code block FIRST, followed by the JSON block.
    Tests whether the cleaner recovers and extracts the valid JSON block.
    """
    adversarial_input = (
        "Here is the schema I followed:\n"
        "```markdown\n"
        "# Schema Note: All fields are required\n"
        "```\n"
        "And here is the resulting JSON:\n"
        "```json\n"
        "{\"actual_result\": true, \"count\": 42}\n"
        "```"
    )
    # Check behavior of current implementation
    try:
        result = cleaner(adversarial_input)
        assert result == {"actual_result": True, "count": 42}
    except json.JSONDecodeError:
        pytest.fail(f"[{router_name}] FAILED: Non-JSON first fence caused fatal parse failure on valid subsequent JSON fence!")


@pytest.mark.xfail(reason="Vulnerability: Embedded backticks in JSON strings match fence regex before JSON parse", strict=False)
@pytest.mark.parametrize("router_name,cleaner", CLEANERS)
def test_clean_json_embedded_backticks_in_json_string(router_name, cleaner):
    """
    Adversarial Challenge:
    A valid JSON string contains triple backticks in its value (e.g. medical note quoting code or formatted text).
    Tests whether regex greedy/non-greedy fence matching breaks string literal contents.
    """
    adversarial_input = '{"summary": "Patient noted ```mild nausea``` symptoms", "score": 1}'
    try:
        result = cleaner(adversarial_input)
        assert result == {"summary": "Patient noted ```mild nausea``` symptoms", "score": 1}
    except json.JSONDecodeError:
        pytest.fail(f"[{router_name}] FAILED: Embedded backticks inside JSON string field corrupted parsing!")


# ============================================================================
# 5. FASTAPI TESTCLIENT HTTP VERIFICATION
# ============================================================================

client = TestClient(main.app)

def test_http_health_endpoint():
    """Test GET /health returns 200 with required keys."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "ai-service"
    assert "model" in data
    assert "apiKeyConfigured" in data


def test_http_ai_health_endpoint():
    """Test GET /ai/health returns identical 200 response."""
    resp = client.get("/ai/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "ai-service"


def test_http_classify_422_on_empty_body():
    """Test POST /ai/classify-and-extract returns 422 on empty body."""
    resp = client.post("/ai/classify-and-extract", json={})
    assert resp.status_code == 422


def test_http_process_document_422_on_empty_body():
    """Test POST /ai/process-document returns 422 on empty body."""
    resp = client.post("/ai/process-document", json={})
    assert resp.status_code == 422


def test_http_literature_split_422_on_empty_body():
    """Test POST /ai/literature-case-split returns 422 on empty body."""
    resp = client.post("/ai/literature-case-split", json={})
    assert resp.status_code == 422


def test_http_screen_literature_422_on_empty_body():
    """Test POST /ai/screen-literature alias returns 422 on empty body."""
    resp = client.post("/ai/screen-literature", json={})
    assert resp.status_code == 422


# ============================================================================
# 6. MOCKED GEMINI PIPELINE TESTS
# ============================================================================

def test_mocked_gemini_classify_fenced_response():
    """Verify classify endpoint processes fenced JSON with conversational chatter from Gemini."""
    mock_gemini_text = (
        "Here is the classification according to guidelines:\n"
        "```json\n"
        "{\n"
        "  \"classifications\": [\n"
        "    {\"category\": \"SAFETY_REPORT\", \"confidence\": 0.95, \"reason\": \"Adverse event reported\"}\n"
        "  ],\n"
        "  \"safetyReportFields\": {\n"
        "    \"patient\": {\"age\": {\"value\": \"45\", \"confidence\": 0.9, \"sourceRef\": \"email\"}},\n"
        "    \"product\": {\"name\": {\"value\": \"Aspirin\", \"confidence\": 0.95, \"sourceRef\": \"email\"}},\n"
        "    \"reaction\": {\"description\": {\"value\": \"Rash\", \"confidence\": 0.85, \"sourceRef\": \"email\"}}\n"
        "  }\n"
        "}\n"
        "```\n"
        "Extraction finished."
    )
    
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = mock_gemini_text
    mock_client.models.generate_content.return_value = mock_resp
    
    with patch("routes.classify_route.get_genai_client", return_value=mock_client):
        resp = client.post("/ai/classify-and-extract", json={
            "emailBody": "Patient took Aspirin and got a rash.",
            "sender": "dr@example.com",
            "subject": "Adverse event"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["classifications"]) == 1
        assert data["classifications"][0]["category"] == "SAFETY_REPORT"
        assert data["safetyReportFields"]["patient"]["age"]["value"] == "45"


def test_mocked_gemini_classify_empty_response_returns_502():
    """Verify classify endpoint returns 502 Bad Gateway when Gemini returns empty response."""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = ""
    mock_client.models.generate_content.return_value = mock_resp
    
    with patch("routes.classify_route.get_genai_client", return_value=mock_client):
        resp = client.post("/ai/classify-and-extract", json={
            "emailBody": "Sample body",
            "sender": "sender@example.com",
            "subject": "Subject"
        })
        assert resp.status_code == 502
        assert "Empty response from Gemini API" in resp.json()["detail"]


def test_mocked_gemini_process_document_success():
    """Verify document route processes base64 PDF and extracts fields via mocked Gemini."""
    mock_gemini_text = json.dumps({
        "pdfType": "DIGITAL",
        "ocrConfidence": None,
        "extractedText": "Form 3500A: Patient age 50",
        "tables": [{"page": 1, "rows": [["Col1", "Col2"], ["Val1", "Val2"]]}],
        "images": [],
        "translation": None,
        "summary": "This is a 10-sentence summary of the adverse event document.",
        "relevanceOpinion": "RELEVANT",
        "relevanceReason": "Contains adverse event data"
    })
    
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = f"```json\n{mock_gemini_text}\n```"
    mock_client.models.generate_content.return_value = mock_resp
    
    dummy_pdf_b64 = "JVBERi0xLjQKJeLjz9MKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZz4+ZW5kb2JqCnRyYWlsZXI8PC9Sb290IDEgMCBSPj4lJUVPRg=="
    
    with patch("routes.document_route.get_genai_client", return_value=mock_client):
        resp = client.post("/ai/process-document", json={
            "pdfBase64": dummy_pdf_b64,
            "filename": "test.pdf",
            "emailContext": {"subject": "Test", "bodySnippet": "Snippet"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["pdfType"] == "DIGITAL"
        assert len(data["tables"]) == 1
        assert data["relevanceOpinion"] == "RELEVANT"


def test_mocked_gemini_screen_literature_success():
    """Verify literature screening endpoint handles split cases via mocked Gemini."""
    mock_gemini_text = json.dumps({
        "cases": [
            {
                "caseIndex": 1,
                "isReportable": True,
                "summary": "Case 1 details from clinical journal.",
                "relevanceReason": "Patient developed acute kidney injury",
                "safetyReportFields": {
                    "patient": {"age": {"value": "62", "confidence": 0.95}}
                }
            }
        ]
    })
    
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = f"```json\n{mock_gemini_text}\n```"
    mock_client.models.generate_content.return_value = mock_resp
    
    with patch("routes.literature_route.get_genai_client", return_value=mock_client):
        resp = client.post("/ai/screen-literature", json={
            "articleText": "A 62-year-old male developed acute kidney injury after starting therapy.",
            "filename": "article.pdf"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cases"]) == 1
        assert data["cases"][0]["isReportable"] is True
        assert data["cases"][0]["caseIndex"] == 1


# ============================================================================
# STANDALONE EXECUTION RUNNER
# ============================================================================

def run_all_tests():
    print("=" * 70)
    print("RUNNING ADVERSARIAL STRESS TEST SUITE FOR AI SERVICE")
    print("=" * 70)
    
    # 1. Routes
    print("\n--- [Phase 1] FastAPI Route Discovery ---")
    test_fastapi_app_instance()
    print("PASS: FastAPI app instantiated successfully.")
    test_route_discovery()
    print("PASS: All 6 endpoints correctly mapped with proper HTTP methods.")

    # 2. Adversarial cases for clean_json_response
    print("\n--- [Phase 2] clean_json_response 18 Standard & Edge Cases ---")
    pass_count = 0
    fail_count = 0
    for router_name, cleaner in CLEANERS:
        print(f"\nTesting Router: {router_name}")
        for case_id, raw_input, expected in ADVERSARIAL_CASES:
            try:
                parsed = cleaner(raw_input)
                assert parsed == expected
                print(f"  [PASS] {case_id}")
                pass_count += 1
            except Exception as e:
                print(f"  [FAIL] {case_id}: {e}")
                fail_count += 1

    # 3. Boundaries
    print("\n--- [Phase 3] Boundary & Error Conditions ---")
    for router_name, cleaner in CLEANERS:
        for name, fn, arg in [
            ("empty_string", cleaner, ""),
            ("whitespace_only", cleaner, "   \n\t  "),
            ("non_json_prose", cleaner, "Random conversational words with no brackets."),
        ]:
            try:
                fn(arg)
                print(f"  [FAIL] [{router_name}] {name} did not raise JSONDecodeError!")
                fail_count += 1
            except json.JSONDecodeError:
                print(f"  [PASS] [{router_name}] {name} properly raised JSONDecodeError.")
                pass_count += 1

    # 4. Adversarial Challenges
    print("\n--- [Phase 4] Adversarial Challenge Probes ---")
    challenge_findings = []
    for router_name, cleaner in CLEANERS:
        # Challenge 1: Non-JSON first fence
        adversarial_input_1 = (
            "Schema explanation:\n"
            "```markdown\n"
            "# Non-JSON Block\n"
            "```\n"
            "Output:\n"
            "```json\n"
            "{\"actual_result\": true, \"count\": 42}\n"
            "```"
        )
        try:
            res1 = cleaner(adversarial_input_1)
            if res1 == {"actual_result": True, "count": 42}:
                print(f"  [PASS] [{router_name}] Non-JSON first fence handled.")
                pass_count += 1
            else:
                print(f"  [FAIL] [{router_name}] Non-JSON first fence returned unexpected: {res1}")
                fail_count += 1
                challenge_findings.append((router_name, "Non-JSON first fence", str(res1)))
        except Exception as e:
            print(f"  [VULNERABILITY DETECTED] [{router_name}] Non-JSON first fence caused crash: {type(e).__name__}: {e}")
            challenge_findings.append((router_name, "Non-JSON first fence", f"{type(e).__name__}: {e}"))

        # Challenge 2: Embedded backticks in JSON string
        adversarial_input_2 = '{"summary": "Patient noted ```mild nausea``` symptoms", "score": 1}'
        try:
            res2 = cleaner(adversarial_input_2)
            if res2 == {"summary": "Patient noted ```mild nausea``` symptoms", "score": 1}:
                print(f"  [PASS] [{router_name}] Embedded backticks handled.")
                pass_count += 1
            else:
                print(f"  [FAIL] [{router_name}] Embedded backticks returned unexpected: {res2}")
                fail_count += 1
                challenge_findings.append((router_name, "Embedded backticks", str(res2)))
        except Exception as e:
            print(f"  [VULNERABILITY DETECTED] [{router_name}] Embedded backticks caused crash: {type(e).__name__}: {e}")
            challenge_findings.append((router_name, "Embedded backticks", f"{type(e).__name__}: {e}"))

    # 5. FastAPI TestClient
    print("\n--- [Phase 5] FastAPI TestClient HTTP Invocations ---")
    for test_fn, name in [
        (test_http_health_endpoint, "GET /health"),
        (test_http_ai_health_endpoint, "GET /ai/health"),
        (test_http_classify_422_on_empty_body, "POST /ai/classify-and-extract 422 check"),
        (test_http_process_document_422_on_empty_body, "POST /ai/process-document 422 check"),
        (test_http_literature_split_422_on_empty_body, "POST /ai/literature-case-split 422 check"),
        (test_http_screen_literature_422_on_empty_body, "POST /ai/screen-literature 422 check"),
    ]:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            pass_count += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            fail_count += 1

    # 6. Mocked Gemini Pipeline Execution
    print("\n--- [Phase 6] Mocked Gemini Pipeline Invocations ---")
    for test_fn, name in [
        (test_mocked_gemini_classify_fenced_response, "POST /ai/classify-and-extract (fenced + chatter)"),
        (test_mocked_gemini_classify_empty_response_returns_502, "POST /ai/classify-and-extract (empty -> 502)"),
        (test_mocked_gemini_process_document_success, "POST /ai/process-document (base64 PDF extraction)"),
        (test_mocked_gemini_screen_literature_success, "POST /ai/screen-literature (multi-case split)"),
    ]:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            pass_count += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            fail_count += 1

    print("\n" + "=" * 70)
    print(f"SUMMARY: Standard/Edge Tests Passed: {pass_count}")
    print(f"         Confirmed Adversarial Vulnerabilities: {len(challenge_findings)}")
    print(f"         Unexpected Regressions / Failures: {fail_count}")
    print("=" * 70)
    return pass_count, fail_count, challenge_findings


if __name__ == "__main__":
    passed, regressions, findings = run_all_tests()
    # Exit with code 0 if all expected and edge tests passed and zero unexpected regressions occurred
    sys.exit(0 if regressions == 0 else 1)
