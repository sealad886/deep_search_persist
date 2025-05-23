"""
Tests for the FastAPI endpoints in the docker/persist service.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from ..deep_search_persist.api_endpoints import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_session_dir(monkeypatch, tmp_path):
    """
    Create a temporary directory for session files and patch the SESSIONS_DIR.
    """
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    monkeypatch.setattr("deep_search_persist.api_endpoints.SESSIONS_DIR", sessions_dir)
    return sessions_dir


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Test that the health check endpoint returns a 200 status code."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestModelsEndpoint:
    """Tests for the models endpoint."""

    def test_list_models(self, client):
        """Test that the models endpoint returns the expected model list."""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "deep_researcher"
        assert data["data"][0]["object"] == "model"
        assert data["data"][0]["owned_by"] == "deep_researcher"


class TestChatCompletionsEndpoint:
    """Tests for the chat completions endpoint."""

    @pytest.fixture
    def valid_request_data(self):
        """Create a valid request payload for the chat completions endpoint."""
        return {
            "model": "deep_researcher",
            "messages": [{"role": "user", "content": "What is the capital of France?"}],
            "stream": False,
            "max_iterations": 2,
            "max_search_items": 2,
        }

    @patch("deep_search_persist.api_endpoints.make_initial_searching_plan_async")
    @patch("deep_search_persist.api_endpoints.generate_search_queries_async")
    @patch("deep_search_persist.api_endpoints.perform_search_async")
    @patch("deep_search_persist.api_endpoints.fetch_webpage_text_async")
    @patch("deep_search_persist.api_endpoints.is_page_useful_async")
    @patch("deep_search_persist.api_endpoints.extract_relevant_context_async")
    @patch("deep_search_persist.api_endpoints.judge_search_result_and_future_plan_aync")
    @patch("deep_search_persist.api_endpoints.generate_writing_plan_aync")
    @pytest.mark.anyio
    async def test_chat_completions_success(
        self,
        mock_generate_writing_plan,
        mock_judge_search_result,
        mock_extract_context,
        mock_is_page_useful,
        mock_fetch_webpage,
        mock_perform_search,
        mock_generate_queries,
        mock_make_plan,
        client,
        valid_request_data,
        mock_session_dir,
    ):
        """Test successful chat completions request with mocked dependencies."""
        # Configure mocks
        mock_make_plan.return_value = "Research plan for testing"
        mock_generate_queries.return_value = ["query1", "query2"]
        mock_perform_search.return_value = [
            "http://example.com/1",
            "http://example.com/2",
        ]
        mock_fetch_webpage.return_value = "Sample webpage content"
        mock_is_page_useful.return_value = "Yes"
        mock_extract_context.return_value = "Relevant context from the webpage"
        mock_judge_search_result.return_value = "<done>"
        mock_generate_writing_plan.return_value = "Writing plan for the final report"

        # Make the request
        with patch("deep_search_persist.api_endpoints.ResearchSession.save_session") as mock_save:
            response = client.post("/chat/completions", json=valid_request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["model"] == "deep_researcher"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "Final Report:" in data["choices"][0]["message"]["content"]
        assert data["choices"][0]["finish_reason"] == "completed"

        # Verify session was saved
        assert mock_save.call_count > 0

    @patch("deep_search_persist.api_endpoints.make_initial_searching_plan_async")
    @pytest.mark.anyio
    async def test_chat_completions_error(self, mock_make_plan, client, valid_request_data):
        """Test error handling in chat completions endpoint."""
        # Configure mock to raise an exception
        mock_make_plan.side_effect = Exception("Test error")

        # Make the request
        response = client.post("/chat/completions", json=valid_request_data)

        # Verify response
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]

    def test_chat_completions_invalid_request(self, client):
        """Test chat completions with invalid request data."""
        # Missing required fields
        invalid_data = {
            "model": "deep_researcher"
            # Missing messages field
        }

        response = client.post("/chat/completions", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_chat_completions_invalid_max_iterations(self, client, valid_request_data):
        """Test chat completions with invalid max_iterations."""
        # Set max_iterations to an invalid value
        valid_request_data["max_iterations"] = 0  # Less than minimum allowed (1)

        response = client.post("/chat/completions", json=valid_request_data)
        assert response.status_code == 422  # Validation error
