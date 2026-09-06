import os
from pathlib import Path

# Project root is two levels up from tests/e2e
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "test-data"
STORAGE_DIR = PROJECT_ROOT / "storage"

# Target Service URLs
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")
AI_SERVICE_BASE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000").rstrip("/")

# Execution options
REQUEST_TIMEOUT = float(os.getenv("E2E_REQUEST_TIMEOUT", "15.0"))
USE_MOCK_FALLBACK = os.getenv("E2E_USE_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes")
FORCE_MOCK = os.getenv("E2E_FORCE_MOCK", "false").lower() in ("true", "1", "yes")

# Known Categories
CATEGORIES = [
    "SAFETY_REPORT",
    "QUALITY_COMPLAINT",
    "INFO_REQUEST",
    "NOT_RELEVANT"
]

# PDF Types
PDF_TYPES = [
    "DIGITAL",
    "SCANNED",
    "ARTICLE",
    "NON_ENGLISH"
]

# Reviewer Statuses
REVIEWER_STATUSES = [
    "PENDING",
    "ACCEPTED",
    "OVERRIDDEN"
]

# Review Actions
REVIEW_ACTIONS = [
    "ACCEPT",
    "OVERRIDE",
    "EDIT"
]
