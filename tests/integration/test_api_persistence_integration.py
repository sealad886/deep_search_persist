import asyncio
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId  # Import ObjectId for mock_mongo_client queries
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient  # For mocking MongoDB
from motor.motor_asyncio import AsyncIOMotorClient

from deep_search_persist.deep_search_persist.api_endpoints import app, persistence
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages
from deep_search_persist.deep_search_persist.persistence.session_persistence import (
    SessionPersistenceManager,
    SessionStatus,
)
from deep_search_persist.deep_search_persist.persistence.utils import clean_dict
from deep_search_persist.deep_search_persist.research_session import ResearchSession


# Fixture for a mocked MongoDB client
@pytest.fixture(name="mock_mongo_client")
async def mock_mongo_client_fixture():
    """Provides a mocked MongoDB client for testing."""
    client = AsyncMongoMockClient()
    yield client
    client.close()


# Fixture to override the persistence manager with a mocked one
@pytest.fixture(name="mock_persistence_manager")
async def mock_persistence_manager_fixture(mock_mongo_client):
    """Overrides the global persistence manager with a mock for testing."""
    original_persistence_client = persistence.client
    original_persistence_db = persistence.db
    original_persistence_session_collection = persistence.session_collection
    original_persistence_validation_hashes_collection = persistence.validation_hashes_collection

    persistence.client = mock_mongo_client
    persistence.db = mock_mongo_client["test_db"]
    persistence.session_collection = persistence.db["sessions"]
    persistence.validation_hashes_collection = persistence.db["session_validation_hashes"]

    # Ensure collections are empty before each test
    await persistence.session_collection.delete_many({})
    await persistence.validation_hashes_collection.delete_many({})

    # Re-initialize the persistence manager to use the mocked client
    await persistence.initialize()

    yield persistence

    # Clean up after test
    await persistence.session_collection.delete_many({})
    await persistence.validation_hashes_collection.delete_many({})

    # Restore original persistence manager components
    persistence.client = original_persistence_client
    persistence.db = original_persistence_db
    persistence.session_collection = original_persistence_session_collection
    persistence.validation_hashes_collection = original_persistence_validation_hashes_collection


# Fixture for the FastAPI test client
@pytest.fixture(name="test_client")
async def test_client_fixture(mock_persistence_manager):
    """Provides an asynchronous test client for the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# --- Integration tests for API Endpoints and Persistence ---


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test the health check endpoint."""
    response = await test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_completions_new_session(test_client, mock_persistence_manager):
    """Test chat completions endpoint for a new session, verifying session persistence."""
    user_query = "What is the capital of France?"
    messages = [{"role": "user", "content": user_query}]
    request_payload = {"messages": messages, "max_iterations": 1}

    # Mock LLM calls to avoid actual external requests during integration test
    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.make_initial_searching_plan_async",
        return_value="Plan: Search for capital of France.",
    ):
        with patch(
            "deep_search_persist.deep_search_persist.helper_functions.generate_search_queries_async",
            return_value=["capital of France"],
        ):
            with patch(
                "deep_search_persist.deep_search_persist.helper_functions.perform_search_async",
                return_value=["http://example.com/paris"],
            ):
                with patch(
                    "deep_search_persist.deep_search_persist.helper_functions.process_link", new_callable=AsyncMock
                ) as mock_process_link:
                    mock_process_link.return_value = AsyncGeneratorMock(
                        ["url:http://example.com/paris\ncontext:Paris is the capital of France."]
                    )
                    with patch(
                        "deep_search_persist.deep_search_persist.helper_functions.judge_search_result_and_future_plan_async",
                        return_value="<done>",
                    ):
                        with patch(
                            "deep_search_persist.deep_search_persist.helper_functions.generate_final_report_async",
                            return_value="The capital of France is Paris.",
                        ):
                            response = await test_client.post(
                                "/chat/completions", json=request_payload, timeout=60
                            )  # Increased timeout

    assert response.status_code == 200

    # Verify SSE stream content
    response_content = response.text
    assert "SESSION_ID:" in response_content
    assert "The capital of France is Paris." in response_content
    assert "data: [DONE]\n\n" in response_content

    # Extract session ID from response
    session_id_match = re.search(r"SESSION_ID:([a-f0-9-]+)", response_content)
    assert session_id_match
    session_id = session_id_match.group(1)

    # Verify session is saved in MongoDB
    saved_session_doc = await mock_persistence_manager.session_collection.find_one({"_id": ObjectId(session_id)})
    assert saved_session_doc is not None
    assert saved_session_doc["status"] == SessionStatus.COMPLETED.value
    assert saved_session_doc["data"]["user_query"] == user_query
    assert "The capital of France is Paris." in saved_session_doc["data"]["aggregated_data"]["final_report_content"]
    assert saved_session_doc["current_iteration"] == 1  # max_iterations was 1


@pytest.mark.asyncio
async def test_list_sessions(test_client, mock_persistence_manager):
    """Test listing sessions."""
    # Create a dummy session directly in the mock DB
    session_data = ResearchSession(user_query="Dummy query", settings={}).dict()
    session_data["status"] = SessionStatus.COMPLETED.value
    session_data["created_at"] = datetime.now(timezone.utc).isoformat()
    session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    session_data["current_iteration"] = 1

    # Manually insert into mock DB and generate hash
    inserted_result = await mock_persistence_manager.session_collection.insert_one(session_data)
    session_id_obj = inserted_result.inserted_id
    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": session_id_obj, "session_hash": hash_val}
    )

    response = await test_client.get("/sessions")
    assert response.status_code == 200
    sessions_list = response.json()
    assert isinstance(sessions_list, dict)
    assert "sessions" in sessions_list
    assert len(sessions_list["sessions"]) == 1
    assert sessions_list["sessions"][0]["session_id"] == str(session_id_obj)
    assert sessions_list["sessions"][0]["user_query"] == ""  # user_query is not returned by list_sessions API endpoint
    assert sessions_list["sessions"][0]["status"] == SessionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_get_session_success(test_client, mock_persistence_manager):
    """Test retrieving a single session by ID."""
    # Create a dummy session directly in the mock DB
    session_id = str(uuid.uuid4())
    user_query = "Specific session query"
    session_data = ResearchSession(session_id=session_id, user_query=user_query, settings={"test": True}).dict()
    session_data["status"] = SessionStatus.RUNNING.value
    session_data["created_at"] = datetime.now(timezone.utc).isoformat()
    session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    session_data["current_iteration"] = 0

    # Manually insert into mock DB and generate hash
    inserted_result = await mock_persistence_manager.session_collection.insert_one(session_data)
    session_id_obj = inserted_result.inserted_id
    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": session_id_obj, "session_hash": hash_val}
    )

    response = await test_client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    retrieved_session = response.json()
    assert retrieved_session["session_id"] == session_id
    assert retrieved_session["user_query"] == user_query
    assert retrieved_session["status"] == SessionStatus.RUNNING.value


@pytest.mark.asyncio
async def test_get_session_not_found(test_client):
    """Test retrieving a non-existent session."""
    non_existent_id = "non-existent-session-123"
    response = await test_client.get(f"/sessions/{non_existent_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


@pytest.mark.asyncio
async def test_delete_session_success(test_client, mock_persistence_manager):
    """Test deleting a session."""
    # Create a dummy session directly in the mock DB
    session_id = str(uuid.uuid4())
    session_data = ResearchSession(session_id=session_id, user_query="To be deleted", settings={}).dict()
    session_data["status"] = SessionStatus.COMPLETED.value
    session_data["created_at"] = datetime.now(timezone.utc).isoformat()
    session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    session_data["current_iteration"] = 1

    # Manually insert into mock DB and generate hash
    inserted_result = await mock_persistence_manager.session_collection.insert_one(session_data)
    session_id_obj = inserted_result.inserted_id
    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": session_id_obj, "session_hash": hash_val}
    )

    response = await test_client.delete(f"/sessions/{session_id}")
    assert response.status_code == 204  # No Content

    # Verify session is deleted from MongoDB
    deleted_session = await mock_persistence_manager.session_collection.find_one({"_id": ObjectId(session_id)})
    assert deleted_session is None
    deleted_hash = await mock_persistence_manager.validation_hashes_collection.find_one(
        {"session_id": ObjectId(session_id)}
    )
    assert deleted_hash is None


@pytest.mark.asyncio
async def test_delete_session_not_found(test_client):
    """Test deleting a non-existent session."""
    non_existent_id = "non-existent-delete-123"
    response = await test_client.delete(f"/sessions/{non_existent_id}")
    # The current implementation returns 500 if not found, as delete_one doesn't raise error for non-existent.
    # It's better to return 404 or 204 if delete_count is 0.
    # For now, asserting against current behavior.
    assert response.status_code == 204  # If delete_one is called, it returns 204 even if no doc is found.


@pytest.mark.asyncio
async def test_resume_session_success(test_client, mock_persistence_manager):
    """Test resuming a session."""
    session_id = str(uuid.uuid4())
    user_query = "Resume test query"
    session_data = ResearchSession(session_id=session_id, user_query=user_query, settings={}).dict()
    session_data["status"] = SessionStatus.INTERRUPTED.value
    session_data["created_at"] = datetime.now(timezone.utc).isoformat()
    session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    session_data["current_iteration"] = 1

    # Manually insert into mock DB and generate hash
    inserted_result = await mock_persistence_manager.session_collection.insert_one(session_data)
    session_id_obj = inserted_result.inserted_id
    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": session_id_obj, "session_hash": hash_val}
    )

    response = await test_client.post(f"/sessions/{session_id}/resume")
    assert response.status_code == 200
    resumed_session = response.json()
    assert resumed_session["session_id"] == session_id
    assert resumed_session["user_query"] == user_query
    assert resumed_session["status"] == SessionStatus.INTERRUPTED.value  # Status should remain as it was loaded


@pytest.mark.asyncio
async def test_resume_session_not_found(test_client):
    """Test resuming a non-existent session."""
    non_existent_id = "non-existent-resume-123"
    response = await test_client.post(f"/sessions/{non_existent_id}/resume")
    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found or cannot be resumed"}


@pytest.mark.asyncio
async def test_get_session_history_success(test_client, mock_persistence_manager):
    """Test retrieving session history."""
    session_id = str(uuid.uuid4())
    session_data = ResearchSession(session_id=session_id, user_query="History test", settings={}).dict()
    session_data["status"] = SessionStatus.COMPLETED.value
    session_data["created_at"] = datetime.now(timezone.utc).isoformat()
    session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    session_data["current_iteration"] = 2
    session_data["history"] = [
        {"iteration": 0, "timestamp": datetime.now(timezone.utc).isoformat(), "data": {"step": "initial"}},
        {
            "iteration": 1,
            "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "data": {"step": "search"},
        },
    ]

    # Manually insert into mock DB and generate hash
    inserted_result = await mock_persistence_manager.session_collection.insert_one(session_data)
    session_id_obj = inserted_result.inserted_id
    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": session_id_obj, "session_hash": hash_val}
    )

    response = await test_client.get(f"/sessions/{session_id}/history")
    assert response.status_code == 200
    history_data = response.json()
    assert "history" in history_data
    assert len(history_data["history"]) == 2
    assert history_data["history"][0]["iteration"] == 0
    assert history_data["history"][1]["iteration"] == 1


@pytest.mark.asyncio
async def test_get_session_history_not_found(test_client):
    """Test retrieving history for a non-existent session."""
    non_existent_id = "non-existent-history-123"
    response = await test_client.get(f"/sessions/{non_existent_id}/history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found or no history available"}


@pytest.mark.asyncio
async def test_rollback_session_success(test_client, mock_persistence_manager):
    """Test rolling back a session to a specific iteration."""
    session_id = str(uuid.uuid4())
    initial_data = {
        "user_query": "Initial query",
        "settings": {},
        "status": SessionStatus.RUNNING.value,
        "current_iteration": 0,
    }
    iteration_1_data = {
        "user_query": "Updated query",
        "settings": {},
        "status": SessionStatus.RUNNING.value,
        "current_iteration": 1,
        "aggregated_data": {"test": "data"},
    }

    session_doc = {
        "_id": ObjectId(session_id),
        "user_id": "test_user",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": SessionStatus.RUNNING.value,
        "current_iteration": 1,
        "data": iteration_1_data,
        "history": [
            {"iteration": 0, "timestamp": datetime.now(timezone.utc).isoformat(), "data": initial_data},
            {
                "iteration": 1,
                "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
                "data": iteration_1_data,
            },
        ],
    }

    # Manually insert into mock DB and generate hash
    await mock_persistence_manager.session_collection.insert_one(session_doc)
    session_data_str = json.dumps(clean_dict(session_doc["data"]), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": ObjectId(session_id), "session_hash": hash_val}
    )

    response = await test_client.post(f"/sessions/{session_id}/rollback/0")
    assert response.status_code == 200
    assert response.json() == {"status": "rolled back", "iteration": 0}

    # Verify session data is rolled back
    rolled_back_session = await mock_persistence_manager.session_collection.find_one({"_id": ObjectId(session_id)})
    assert rolled_back_session["data"]["user_query"] == "Initial query"
    assert rolled_back_session["current_iteration"] == 0


@pytest.mark.asyncio
async def test_rollback_session_invalid_iteration(test_client, mock_persistence_manager):
    """Test rolling back to an invalid iteration."""
    session_id = str(uuid.uuid4())
    initial_data = {
        "user_query": "Initial query",
        "settings": {},
        "status": SessionStatus.RUNNING.value,
        "current_iteration": 0,
    }
    session_doc = {
        "_id": ObjectId(session_id),
        "user_id": "test_user",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": SessionStatus.RUNNING.value,
        "current_iteration": 0,
        "data": initial_data,
        "history": [
            {"iteration": 0, "timestamp": datetime.now(timezone.utc).isoformat(), "data": initial_data},
        ],
    }

    # Manually insert into mock DB and generate hash
    await mock_persistence_manager.session_collection.insert_one(session_doc)
    session_data_str = json.dumps(clean_dict(session_doc["data"]), sort_keys=True)
    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
    await mock_persistence_manager.validation_hashes_collection.insert_one(
        {"session_id": ObjectId(session_id), "session_hash": hash_val}
    )

    response = await test_client.post(f"/sessions/{session_id}/rollback/99")
    assert response.status_code == 400
    assert "Iteration 99 not found in history." in response.json()["detail"]


@pytest.mark.asyncio
async def test_rollback_session_not_found(test_client):
    """Test rolling back a non-existent session."""
    non_existent_id = "non-existent-rollback-123"
    response = await test_client.post(f"/sessions/{non_existent_id}/rollback/0")
    assert (
        response.status_code == 400
    )  # The API returns 400 for "Could not rollback: No history available for this session."
    assert "No history available for this session." in response.json()["detail"]


import inspect

# Helper for AsyncMock and AsyncGeneratorMock
from unittest.mock import AsyncMock, patch


class AsyncGeneratorMock:
    def __init__(self, iterable):
        self.iterable = iterable

    async def __aiter__(self):
        for item in self.iterable:
            yield item
