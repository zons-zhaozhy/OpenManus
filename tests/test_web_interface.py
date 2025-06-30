"""
Web interface tests
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agent.manus import Manus
from app.interfaces.web_interface import WebInterface


@pytest.fixture
def mock_agent():
    """Mock Manus agent for testing"""
    mock = AsyncMock()
    mock.analyze_requirements.return_value = "Analysis result"
    mock.get_analysis_progress.return_value = 50
    mock.get_analysis_metrics.return_value = {
        "clarity": 0.8,
        "completeness": 0.7,
        "consistency": 0.9,
    }
    return mock


@pytest.fixture
def test_client(mock_agent):
    """Create test client"""
    interface = WebInterface()
    interface.agent = mock_agent

    with TestClient(interface.app) as client:
        yield client


def test_serve_frontend(test_client):
    """Test frontend page serving"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_chat_endpoint(test_client):
    """Test chat API endpoint"""
    response = test_client.post(
        "/api/chat", json={"message": "Create a web application"}
    )
    assert response.status_code == 200
    assert response.json()["response"] == "Analysis result"


def test_progress_endpoint(test_client):
    """Test progress tracking endpoint"""
    response = test_client.get("/api/progress")
    assert response.status_code == 200
    assert response.json()["progress"] == 50


def test_metrics_endpoint(test_client):
    """Test analysis metrics endpoint"""
    response = test_client.get("/api/metrics")
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["clarity"] == 0.8
    assert metrics["completeness"] == 0.7
    assert metrics["consistency"] == 0.9


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket communication"""
    interface = WebInterface()
    interface.agent = AsyncMock()

    with patch("fastapi.WebSocket") as mock_websocket:
        mock_websocket.receive_text.return_value = "Create a web application"
        await interface._handle_websocket(mock_websocket)

        mock_websocket.send_json.assert_called()


def test_error_handling(test_client, mock_agent):
    """Test error handling in API endpoints"""
    mock_agent.analyze_requirements.side_effect = Exception("Analysis error")

    response = test_client.post(
        "/api/chat", json={"message": "Create a web application"}
    )
    assert response.status_code == 500
    assert "error" in response.json()


def test_invalid_request(test_client):
    """Test invalid request handling"""
    response = test_client.post("/api/chat", json={"invalid": "data"})
    assert response.status_code == 422


def test_cors_headers(test_client):
    """Test CORS headers"""
    response = test_client.options("/api/chat")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_static_files(test_client):
    """Test static file serving"""
    response = test_client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
