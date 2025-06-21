# tests/e2e/test_research_workflow.py
import asyncio
import json
import re

import httpx
import pytest

from deep_search_persist.deep_search_persist.configuration import app_config  # Import app_config
# BASE_SEARXNG_URL, DEFAULT_MODEL, and OLLAMA_BASE_URL will be accessed via app_config
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages
from deep_search_persist.deep_search_persist.persistence.session_persistence import SessionStatus
from deep_search_persist.deep_search_persist.research_session import ResearchSession

# Base URL for the FastAPI application running in Docker
# This should point to the app-persist service within the Docker network,
# or localhost if running tests outside Docker but connecting to Docker services.
# For E2E tests, we assume the Docker environment is up and accessible.
API_BASE_URL = "http://localhost:8000/v1"  # Assuming port 8000 is exposed from app-persist


# Fixture for the FastAPI test client (connecting to the running Docker service)
@pytest.fixture(scope="module")
async def e2e_test_client():
    """Provides an asynchronous test client for the FastAPI app running in Docker."""
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        yield client


# Helper to read SSE stream
async def read_sse_stream(response):
    """Reads and collects data from an SSE stream."""
    full_content = ""
    async for chunk in response.aiter_bytes():
        chunk_str = chunk.decode("utf-8")
        full_content += chunk_str
    return full_content


@pytest.mark.asyncio
async def test_e2e_full_research_workflow(e2e_test_client):
    """
    Tests the full end-to-end research workflow, including chat completions,
    session persistence, and report generation.
    This test requires the full Docker environment (app, mongo, searxng, ollama) to be running.
    """
    user_query = "Summarize the main benefits of renewable energy sources."
    messages = [{"role": "user", "content": user_query}]
    request_payload = {"messages": messages, "max_iterations": 2}

    print(f"\n--- Starting E2E Test: Full Research Workflow for '{user_query}' ---")

    # 1. Initiate a new research session via chat completions
    print("Sending chat completions request...")
    response = await e2e_test_client.post(
        "/chat/completions", json=request_payload, timeout=300.0
    )  # Increased timeout for E2E

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    stream_content = await read_sse_stream(response)
    print("Received SSE stream content.")
    # print(f"Stream Content:\n{stream_content}") # Uncomment for debugging

    # Verify key stages of the workflow are present in the stream
    assert "SESSION_ID:" in stream_content
    assert "<think>Generating initial research plan..." in stream_content
    assert "<think>Iteration 1/2: Generating search queries..." in stream_content
    assert "<think>Research phase concluded. Generating final report..." in stream_content
    assert "Research session completed." in stream_content
    assert "data: [DONE]\n\n" in stream_content

    # Extract session ID
    session_id_match = re.search(r"SESSION_ID:([a-f0-9-]+)", stream_content)
    assert session_id_match, "Session ID not found in stream."
    session_id = session_id_match.group(1)
    print(f"Session ID: {session_id}")

    # 2. Verify session exists and is completed via GET /sessions
    print(f"Verifying session '{session_id}' status via GET /sessions...")
    sessions_response = await e2e_test_client.get("/sessions")
    assert sessions_response.status_code == 200
    sessions_list = sessions_response.json()

    found_session_summary = next((s for s in sessions_list["sessions"] if s["session_id"] == session_id), None)
    assert found_session_summary is not None, f"Session {session_id} not found in /sessions list."
    assert found_session_summary["status"] == SessionStatus.COMPLETED.value
    # Note: user_query is not returned by list_sessions endpoint, so cannot assert here.

    # 3. Retrieve full session data via GET /sessions/{session_id}
    print(f"Retrieving full session data for '{session_id}' via GET /sessions/{{session_id}}...")
    full_session_response = await e2e_test_client.get(f"/sessions/{session_id}")
    assert full_session_response.status_code == 200
    full_session_data = full_session_response.json()

    assert full_session_data["session_id"] == session_id
    assert full_session_data["user_query"] == user_query
    assert full_session_data["status"] == SessionStatus.COMPLETED.value
    assert "final_report_content" in full_session_data["aggregated_data"]
    assert full_session_data["aggregated_data"]["final_report_content"] != ""
    print("Full session data retrieved and verified.")

    # 4. Verify session history via GET /sessions/{session_id}/history
    print(f"Verifying session history for '{session_id}' via GET /sessions/{{session_id}}/history...")
    history_response = await e2e_test_client.get(f"/sessions/{session_id}/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert "history" in history_data
    assert len(history_data["history"]) >= 1  # At least initial state and final state
    print("Session history retrieved and verified.")

    # 5. Test rollback (optional, as it modifies state, but good for E2E)
    # Rollback to iteration 0 (initial state)
    print(f"Attempting to rollback session '{session_id}' to iteration 0...")
    rollback_response = await e2e_test_client.post(f"/sessions/{session_id}/rollback/0")
    assert rollback_response.status_code == 200
    assert rollback_response.json() == {"status": "rolled back", "iteration": 0}
    print("Session rollback successful.")

    # Verify session data after rollback
    rolled_back_session_response = await e2e_test_client.get(f"/sessions/{session_id}")
    assert rolled_back_session_response.status_code == 200
    rolled_back_session_data = rolled_back_session_response.json()
    assert rolled_back_session_data["current_iteration"] == 0
    assert rolled_back_session_data["status"] == SessionStatus.RUNNING.value  # Rolled back to running state
    print("Session data verified after rollback.")

    # 6. Delete the session
    print(f"Deleting session '{session_id}'...")
    delete_response = await e2e_test_client.delete(f"/sessions/{session_id}")
    assert delete_response.status_code == 204  # No Content
    print("Session deletion successful.")

    # Verify session is no longer listed
    sessions_after_delete_response = await e2e_test_client.get("/sessions")
    assert sessions_after_delete_response.status_code == 200
    sessions_list_after_delete = sessions_after_delete_response.json()
    assert not any(
        s["session_id"] == session_id for s in sessions_list_after_delete["sessions"]
    ), f"Session {session_id} still found after deletion."
    print("Session verified as deleted from list.")

    print("--- E2E Test: Full Research Workflow Completed Successfully ---")


# You might add more E2E tests here for specific scenarios, e.g.,
# - Testing with different max_iterations
# - Testing error handling during research (e.g., LLM failure, search failure)
# - Testing resume functionality more thoroughly
# - Testing specific data integrity aspects after multiple operations
