import base64
import os
import sys
import socket
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import requests
from tests.e2e.config import (
    BACKEND_BASE_URL,
    AI_SERVICE_BASE_URL,
    TEST_DATA_DIR,
    REQUEST_TIMEOUT,
    USE_MOCK_FALLBACK,
    FORCE_MOCK
)
from tests.e2e.mock_server import MockServer

def is_service_alive(url: str) -> bool:
    try:
        r = requests.get(f"{url}/health", timeout=1.0)
        return r.status_code in (200, 404)
    except Exception:
        try:
            r = requests.get(f"{url}/api/messages", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

@pytest.fixture(scope="session")
def service_urls():
    backend_live = False if FORCE_MOCK else is_service_alive(BACKEND_BASE_URL)
    ai_live = False if FORCE_MOCK else is_service_alive(AI_SERVICE_BASE_URL)

    mock_server = None
    if backend_live and ai_live and not FORCE_MOCK:
        yield {
            "backend": BACKEND_BASE_URL,
            "ai": AI_SERVICE_BASE_URL,
            "is_mock": False
        }
    elif USE_MOCK_FALLBACK or FORCE_MOCK:
        # Start embedded mock server handling both backend and AI endpoints
        port = find_free_port()
        mock_server = MockServer(host="127.0.0.1", port=port)
        mock_server.start()
        url = f"http://127.0.0.1:{port}"
        yield {
            "backend": url,
            "ai": url,
            "is_mock": True,
            "server": mock_server
        }
        mock_server.stop()
    else:
        raise RuntimeError("Live services are offline and mock fallback is disabled.")

@pytest.fixture
def backend_client(service_urls):
    session = requests.Session()
    base_url = service_urls["backend"]

    class Client:
        def get(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.get(f"{base_url}{endpoint}", **kwargs)

        def post(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.post(f"{base_url}{endpoint}", **kwargs)

        def put(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.put(f"{base_url}{endpoint}", **kwargs)

        def delete(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.delete(f"{base_url}{endpoint}", **kwargs)

    return Client()

@pytest.fixture
def ai_client(service_urls):
    session = requests.Session()
    base_url = service_urls["ai"]

    class AiClient:
        def get(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.get(f"{base_url}{endpoint}", **kwargs)

        def post(self, endpoint, **kwargs):
            kwargs.setdefault("timeout", REQUEST_TIMEOUT)
            return session.post(f"{base_url}{endpoint}", **kwargs)

    return AiClient()

@pytest.fixture
def test_data_path():
    return TEST_DATA_DIR

@pytest.fixture
def sample_pdf_b64():
    raw = b"%PDF-1.4 sample PDF binary stream for test execution"
    return base64.b64encode(raw).decode("ascii")
