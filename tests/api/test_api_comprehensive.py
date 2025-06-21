"""
Comprehensive API Tests

Tests all API endpoints and functionality.
"""

import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from deep_search_persist.deep_search_persist.api_endpoints import app
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages
from deep_search_persist.deep_search_persist.persistence.session_persistence import (
    SessionPersistenceManager, SessionStatus
)
from deep_search_persist.deep_search_persist.research_session import ResearchSession


@pytest.fixture
async def mock_persistence():
    """Create a mock persistence manager."""
    mock_client = AsyncMongoMockClient()
    persistence = SessionPersistenceManager("mongodb://mock:27017/test")
    
    # Replace the real MongoDB client with mock
    persistence.client = mock_client
    persistence.db = mock_client["test_db"]
    persistence.session_collection = persistence.db["sessions"]
    persistence.validation_hashes_collection = persistence.db["session_validation_hashes"]
    
    # Clear collections
    await persistence.session_collection.delete_many({})
    await persistence.validation_hashes_collection.delete_many({})
    
    return persistence


@pytest.fixture
def api_client():
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.mark.api
@pytest.mark.unit
class TestAPIHealthEndpoints:
    """Test API health and status endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_healthcheck_endpoint(self, api_client):
        """Test healthcheck endpoint."""
        response = api_client.get("/healthcheck")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.api
@pytest.mark.integration
class TestAPISessionEndpoints:
    """Test session management endpoints."""
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, mock_persistence_global, api_client):
        """Test listing sessions when none exist."""
        mock_persistence_global.list_sessions.return_value = []
        
        response = await api_client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        assert len(data["sessions"]) == 0
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, mock_persistence_global, api_client):
        """Test listing sessions with mock data."""
        from deep_search_persist.deep_search_persist.persistence.session_persistence import SessionSummary
        
        # Create mock session summary
        mock_session = SessionSummary(
            session_id="test-session-123",
            user_query="Test query",
            status=SessionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_persistence_global.list_sessions.return_value = [mock_session]
        
        response = await api_client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 1
        
        session = data["sessions"][0]
        assert session["session_id"] == "test-session-123"
        assert session["user_query"] == "Test query"
        assert session["status"] == "completed"
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_get_session_details(self, mock_persistence_global, api_client):
        """Test getting session details."""
        mock_session_data = {
            "session_id": "test-session-123",
            "user_query": "Test query",
            "status": "completed",
            "aggregated_data": {
                "final_report_content": "Test report content"
            }
        }
        
        mock_persistence_global.load_session.return_value = mock_session_data
        
        response = await api_client.get("/sessions/test-session-123")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["user_query"] == "Test query"
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_persistence_global, api_client):
        """Test getting non-existent session."""
        mock_persistence_global.load_session.side_effect = Exception("Session not found")
        
        response = await api_client.get("/sessions/nonexistent")
        assert response.status_code == 404
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_delete_session(self, mock_persistence_global, api_client):
        """Test deleting a session."""
        mock_persistence_global.delete_session.return_value = None
        
        response = await api_client.delete("/sessions/test-session-123")
        assert response.status_code == 204
        
        # Verify delete was called
        mock_persistence_global.delete_session.assert_called_once_with("test-session-123")


@pytest.mark.api
@pytest.mark.integration 
class TestAPIChatCompletions:
    """Test chat completions endpoint."""
    
    def create_valid_request(self):
        """Create a valid chat completion request."""
        return {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Test query"}
            ],
            "max_iterations": 2,
            "stream": False
        }
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @patch('deep_search_persist.deep_search_persist.helper_functions.make_initial_searching_plan_async')
    @pytest.mark.asyncio
    async def test_chat_completions_basic_structure(self, mock_plan, mock_persistence_global, api_client):
        """Test basic structure of chat completions."""
        # Mock persistence
        mock_persistence_global.save_session = AsyncMock()
        
        # Mock planning function to avoid external dependencies
        mock_plan.return_value = "Test initial plan"
        
        # Mock aiohttp session to avoid network calls
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            request_data = self.create_valid_request()
            request_data["stream"] = True  # Test streaming
            
            response = await api_client.post("/v1/chat/completions", json=request_data)
            
            # Should return 200 for streaming
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/plain; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_chat_completions_invalid_request(self, api_client):
        """Test invalid request handling."""
        # Missing required fields
        invalid_request = {
            "model": "test-model"
            # Missing messages
        }
        
        response = await api_client.post("/v1/chat/completions", json=invalid_request)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_completions_message_transformation(self, api_client):
        """Test message transformation logic."""
        # Test with various message formats
        test_cases = [
            # Standard format
            {
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Test"}
                ]
            },
            # With system message
            {
                "model": "test-model", 
                "messages": [
                    {"role": "system", "content": "System prompt"},
                    {"role": "user", "content": "User query"}
                ]
            }
        ]
        
        for request_data in test_cases:
            # This will test the transformation logic, even if the full request fails
            response = await api_client.post("/v1/chat/completions", json=request_data)
            # Should not fail due to message format (422 would indicate format error)
            assert response.status_code != 422


@pytest.mark.api
@pytest.mark.unit
class TestAPIRequestTransformation:
    """Test API request transformation logic."""
    
    def test_transform_chat_completion_request_list_messages(self):
        """Test transforming list of message dicts."""
        from deep_search_persist.deep_search_persist.api_endpoints import transform_chat_completion_request
        
        raw_request = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Test message"}
            ]
        }
        
        transformed = transform_chat_completion_request(raw_request)
        assert hasattr(transformed, 'messages')
        assert isinstance(transformed.messages, Messages)
        assert len(transformed.messages.get_messages()) == 1
        assert transformed.messages.get_messages()[0].role == "user"
        assert transformed.messages.get_messages()[0].content == "Test message"
    
    def test_transform_chat_completion_request_single_message(self):
        """Test transforming single message dict."""
        from deep_search_persist.deep_search_persist.api_endpoints import transform_chat_completion_request
        
        raw_request = {
            "model": "test-model", 
            "messages": {"role": "user", "content": "Single message"}
        }
        
        transformed = transform_chat_completion_request(raw_request)
        assert isinstance(transformed.messages, Messages)
        assert len(transformed.messages.get_messages()) == 1
    
    def test_transform_chat_completion_request_invalid_messages(self):
        """Test transforming invalid message format."""
        from deep_search_persist.deep_search_persist.api_endpoints import transform_chat_completion_request
        
        raw_request = {
            "model": "test-model",
            "messages": "invalid format"
        }
        
        with pytest.raises(ValueError):
            transform_chat_completion_request(raw_request)


@pytest.mark.api
@pytest.mark.integration
class TestAPIErrorHandling:
    """Test API error handling scenarios."""
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_persistence_global, api_client):
        """Test handling of database errors."""
        # Simulate database connection error
        mock_persistence_global.list_sessions.side_effect = Exception("Database connection failed")
        
        response = await api_client.get("/sessions")
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, api_client):
        """Test handling of malformed JSON."""
        # Send invalid JSON
        response = await api_client.post(
            "/v1/chat/completions",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_content_type(self, api_client):
        """Test handling of missing content type."""
        response = await api_client.post(
            "/v1/chat/completions",
            content='{"model": "test"}',
            # No content-type header
        )
        # Should still work with FastAPI's automatic parsing
        assert response.status_code in [200, 422, 500]  # Not a 400 Bad Request


@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance characteristics."""
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_concurrent_session_requests(self, mock_persistence_global, api_client):
        """Test handling of concurrent session requests."""
        mock_persistence_global.list_sessions.return_value = []
        
        # Make multiple concurrent requests
        tasks = []
        for _ in range(10):
            task = api_client.get("/sessions")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    @patch('deep_search_persist.deep_search_persist.api_endpoints.persistence')
    @pytest.mark.asyncio
    async def test_large_session_list_performance(self, mock_persistence_global, api_client):
        """Test performance with large session lists."""
        from deep_search_persist.deep_search_persist.persistence.session_persistence import SessionSummary
        
        # Create many mock sessions
        mock_sessions = []
        for i in range(100):
            session = SessionSummary(
                session_id=f"session-{i}",
                user_query=f"Query {i}",
                status=SessionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            mock_sessions.append(session)
        
        mock_persistence_global.list_sessions.return_value = mock_sessions
        
        response = await api_client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 100


if __name__ == "__main__":
    pytest.main([__file__])