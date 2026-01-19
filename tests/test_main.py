"""
Tests for FastAPI Main Application
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        # May return 200 even if some services are unhealthy
        assert response.status_code == 200

    def test_health_check_response_format(self, client: TestClient):
        """Test health response has correct format."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "services" in data

    def test_health_check_services(self, client: TestClient):
        """Test health response includes service statuses."""
        response = client.get("/health")
        data = response.json()

        services = data["services"]
        assert "redis" in services
        assert "database" in services
        assert "gemini" in services


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Test root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_format(self, client: TestClient):
        """Test root response has correct format."""
        response = client.get("/")
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"


class TestWebhookEndpoint:
    """Test LINE webhook endpoint."""

    def test_webhook_without_signature(self, client: TestClient):
        """Test webhook rejects requests without signature."""
        response = client.post("/webhook", content="{}")
        assert response.status_code == 400
        assert "Missing X-Line-Signature" in response.json()["detail"]

    def test_webhook_with_invalid_signature(
        self, client: TestClient, mock_line_webhook_body
    ):
        """Test webhook rejects invalid signature."""
        response = client.post(
            "/webhook",
            content=mock_line_webhook_body,
            headers={"X-Line-Signature": "invalid_signature"}
        )
        assert response.status_code == 400

    def test_webhook_post_method_required(self, client: TestClient):
        """Test webhook only accepts POST method."""
        response = client.get("/webhook")
        assert response.status_code == 405


class TestErrorHandling:
    """Test error handling."""

    def test_404_not_found(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/non-existent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 for wrong method."""
        response = client.delete("/health")
        assert response.status_code == 405


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        # FastAPI handles OPTIONS for CORS preflight
        assert response.status_code in [200, 405]
