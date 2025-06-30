"""
MCP server tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.mcp.server import MCPServer, create_app


@pytest.fixture
def mock_mcp():
    """Mock MCP for testing"""
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
def test_client(mock_mcp):
    """Create test client"""
    app = create_app()
    app.state.mcp = mock_mcp

    with TestClient(app) as client:
        yield client


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_analyze_requirements(test_client, mock_mcp):
    """Test requirements analysis endpoint"""
    response = test_client.post(
        "/analyze", json={"request": "Create a web application"}
    )
    assert response.status_code == 200
    assert response.json()["result"] == "Analysis result"


def test_get_progress(test_client, mock_mcp):
    """Test progress endpoint"""
    response = test_client.get("/progress")
    assert response.status_code == 200
    assert response.json()["progress"] == 50


def test_get_metrics(test_client, mock_mcp):
    """Test metrics endpoint"""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["clarity"] == 0.8
    assert metrics["completeness"] == 0.7
    assert metrics["consistency"] == 0.9


def test_invalid_request(test_client):
    """Test invalid request handling"""
    response = test_client.post("/analyze", json={"invalid": "data"})
    assert response.status_code == 422


def test_error_handling(test_client, mock_mcp):
    """Test error handling"""
    mock_mcp.analyze_requirements.side_effect = Exception("Analysis error")

    response = test_client.post(
        "/analyze", json={"request": "Create a web application"}
    )
    assert response.status_code == 500
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_websocket_connection(mock_mcp):
    """Test WebSocket communication"""
    server = MCPServer()
    server.mcp = mock_mcp

    with patch("fastapi.WebSocket") as mock_websocket:
        mock_websocket.receive_text.return_value = "Create a web application"
        await server._handle_websocket(mock_websocket)

        mock_websocket.send_json.assert_called()


def test_cors_headers(test_client):
    """Test CORS headers"""
    response = test_client.options("/analyze")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_server_startup():
    """Test server startup"""
    server = MCPServer()
    assert server.app is not None
    assert server.mcp is None  # MCP is initialized on first request


def test_server_shutdown():
    """Test server shutdown"""
    server = MCPServer()
    server.mcp = MagicMock()
    server.cleanup()
    server.mcp.cleanup.assert_called_once()
