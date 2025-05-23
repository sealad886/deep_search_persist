from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest
from pydantic import ValidationError

from deep_search_persist.deep_search_persist.helper_classes import (  # Assuming Messages and Message are used in ResearchSession
    Message,
    Messages,
)
from deep_search_persist.deep_search_persist.research_session import ResearchSession

# --- Unit tests for ResearchSession ---


def test_research_session_creation_minimal():
    """Test creating a ResearchSession with minimal required fields."""
    session = ResearchSession(user_query="Test query", settings={})
    assert isinstance(session.session_id, str)
    assert isinstance(session.start_time, str)
    assert session.end_time is None
    assert session.status == "running"
    assert session.user_query == "Test query"
    assert session.system_instruction is None
    assert isinstance(session.settings, dict)
    assert session.iterations == []
    assert isinstance(session.aggregated_data, dict)
    assert "all_search_queries" in session.aggregated_data
    assert "aggregated_contexts" in session.aggregated_data
    assert "last_plan" in session.aggregated_data
    assert "last_completed_iteration" in session.aggregated_data
    assert isinstance(session.chat_history, Messages)
    assert session.final_report is None
    assert session.error_message is None


def test_research_session_creation_full():
    """Test creating a ResearchSession with all fields."""
    settings = {"max_iterations": 5, "model": "gpt-4"}
    chat_history = Messages(messages=[Message(role="user", content="Hello")])
    session = ResearchSession(
        session_id="test-session-123",
        start_time="2023-10-27T14:00:00+00:00",
        end_time="2023-10-27T15:00:00+00:00",
        status="completed",
        user_query="Full test query",
        system_instruction="Follow instructions",
        settings=settings,
        iterations=[{"iteration": 0, "data": {}}],
        aggregated_data={
            "all_search_queries": ["q1"],
            "aggregated_contexts": ["c1"],
            "last_plan": "plan",
            "last_completed_iteration": 0,
        },
        chat_history=chat_history,
        final_report="Final report content",
        error_message="No errors",
    )
    assert session.session_id == "test-session-123"
    assert session.start_time == "2023-10-27T14:00:00+00:00"
    assert session.end_time == "2023-10-27T15:00:00+00:00"
    assert session.status == "completed"
    assert session.user_query == "Full test query"
    assert session.system_instruction == "Follow instructions"
    assert session.settings == settings
    assert session.iterations == [{"iteration": 0, "data": {}}]
    assert session.aggregated_data == {
        "all_search_queries": ["q1"],
        "aggregated_contexts": ["c1"],
        "last_plan": "plan",
        "last_completed_iteration": 0,
    }
    assert isinstance(session.chat_history, Messages)
    assert len(session.chat_history) == 1
    assert session.chat_history.get_messages()[0].content == "Hello"
    assert session.final_report == "Final report content"
    assert session.error_message == "No errors"


def test_research_session_missing_required():
    """Test creating a ResearchSession with missing required fields."""
    with pytest.raises(ValidationError):
        ResearchSession(settings={})  # type: ignore # Missing user_query


def test_research_session_to_dict():
    """Test converting a ResearchSession object to a dictionary."""
    settings = {"max_iterations": 2}
    chat_history = Messages(
        messages=[Message(role="user", content="Msg 1"), Message(role="assistant", content="Msg 2")]
    )
    session = ResearchSession(
        session_id="dict-test-session",
        user_query="Dict test",
        status="interrupted",
        settings=settings,
        chat_history=chat_history,
    )
    session_dict = session.to_dict()

    assert session_dict["session_id"] == "dict-test-session"
    assert session_dict["user_query"] == "Dict test"
    assert session_dict["status"] == "interrupted"
    assert session_dict["settings"] == settings
    assert isinstance(session_dict["chat_history"], list)
    assert len(session_dict["chat_history"]) == 2
    assert session_dict["chat_history"][0]["content"] == "Msg 1"
    assert session_dict["chat_history"][1]["content"] == "Msg 2"
    assert "start_time" in session_dict
    assert session_dict["end_time"] is None
    assert session_dict["iterations"] == []
    assert "aggregated_data" in session_dict
    assert session_dict["final_report"] is None
    assert session_dict["error_message"] is None


# Note: load_session and save_session methods in ResearchSession are marked as DEPRECATED
# and rely on file system operations, which are typically avoided in pure unit tests.
# Testing of persistence logic should be handled by integration tests with a mock database.
# Therefore, unit tests for these specific methods are omitted here based on the test plan's
# focus on testing the persistence manager with a database.
