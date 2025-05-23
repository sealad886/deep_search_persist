from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest
from pydantic import ValidationError

from deep_search_persist.deep_search_persist.api_models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelList,
    ModelObject,
    SessionSummary,
    SessionSummaryList,
)
from deep_search_persist.deep_search_persist.helper_classes import Message  # Assuming Message is used in api_models

# --- Unit tests for ModelObject ---


def test_model_object_creation():
    """Test creating a ModelObject."""
    model = ModelObject(id="test-model", created=1678886400, owned_by="test-owner")
    assert model.id == "test-model"
    assert model.created == 1678886400
    assert model.owned_by == "test-owner"


def test_model_object_missing_required_fields():
    """Test creating a ModelObject with missing required fields."""
    with pytest.raises(ValidationError):
        ModelObject(created=1678886400, owned_by="test-owner")  # Missing id
    with pytest.raises(ValidationError):
        ModelObject(id="test-model", owned_by="test-owner")  # Missing created
    with pytest.raises(ValidationError):
        ModelObject(id="test-model", created=1678886400)  # Missing owned_by


# --- Unit tests for ModelList ---


def test_model_list_creation_empty():
    """Test creating an empty ModelList."""
    model_list = ModelList(data=[])
    assert isinstance(model_list.data, list)
    assert len(model_list.data) == 0
    assert model_list.object == "list"


def test_model_list_creation_with_data():
    """Test creating a ModelList with ModelObject data."""
    model1 = ModelObject(id="model-1", created=1, owned_by="owner-1")
    model2 = ModelObject(id="model-2", created=2, owned_by="owner-2")
    model_list = ModelList(data=[model1, model2])
    assert isinstance(model_list.data, list)
    assert len(model_list.data) == 2
    assert model_list.data[0] == model1
    assert model_list.data[1] == model2
    assert model_list.object == "list"


def test_model_list_invalid_data_type():
    """Test creating a ModelList with invalid data type in the list."""
    with pytest.raises(ValidationError):
        ModelList(data=[{"id": "model-1", "created": 1, "owned_by": "owner-1"}, "not a model"])


# --- Unit tests for ChatCompletionChoice ---


def test_chat_completion_choice_creation():
    """Test creating a ChatCompletionChoice."""
    message = {"role": "assistant", "content": "Test response."}
    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
    assert choice.index == 0
    assert choice.message == message
    assert choice.finish_reason == "stop"


def test_chat_completion_choice_missing_required_fields():
    """Test creating a ChatCompletionChoice with missing required fields."""
    message = {"role": "assistant", "content": "Test response."}
    with pytest.raises(ValidationError):
        ChatCompletionChoice(message=message, finish_reason="stop")  # Missing index
    with pytest.raises(ValidationError):
        ChatCompletionChoice(index=0, finish_reason="stop")  # Missing message
    with pytest.raises(ValidationError):
        ChatCompletionChoice(index=0, message=message)  # Missing finish_reason


# --- Unit tests for ChatCompletionResponse ---


def test_chat_completion_response_creation():
    """Test creating a ChatCompletionResponse."""
    choice = ChatCompletionChoice(index=0, message={"role": "assistant", "content": "Test."}, finish_reason="stop")
    response = ChatCompletionResponse(
        id="chatcmpl-123", object="chat.completion", created=1678886400, model="test-model", choices=[choice]
    )
    assert response.id == "chatcmpl-123"
    assert response.object == "chat.completion"
    assert response.created == 1678886400
    assert response.model == "test-model"
    assert isinstance(response.choices, list)
    assert len(response.choices) == 1
    assert response.choices[0] == choice


def test_chat_completion_response_missing_required_fields():
    """Test creating a ChatCompletionResponse with missing required fields."""
    choice = ChatCompletionChoice(index=0, message={"role": "assistant", "content": "Test."}, finish_reason="stop")
    with pytest.raises(ValidationError):
        ChatCompletionResponse(
            object="chat.completion", created=1678886400, model="test-model", choices=[choice]
        )  # Missing id
    with pytest.raises(ValidationError):
        ChatCompletionResponse(
            id="chatcmpl-123", created=1678886400, model="test-model", choices=[choice]
        )  # Missing object
    # Add more tests for other missing fields


# --- Unit tests for ChatCompletionRequest ---


def test_chat_completion_request_creation_minimal():
    """Test creating a ChatCompletionRequest with minimal required fields."""
    messages = [{"role": "user", "content": "Hello"}]
    request = ChatCompletionRequest(messages=messages)
    assert isinstance(request.messages, list)  # messages is a list of dicts initially
    assert request.messages == messages
    assert request.model is None  # Default is None
    assert request.system_instruction is None  # Default is None
    assert request.max_iterations == 3  # Default value


def test_chat_completion_request_creation_full():
    """Test creating a ChatCompletionRequest with all fields."""
    messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
    request = ChatCompletionRequest(
        messages=messages,
        model="gpt-4",
        system_instruction="Be helpful",
        max_iterations=5,
        initial_plan="Start with search",
    )
    assert isinstance(request.messages, list)
    assert request.messages == messages
    assert request.model == "gpt-4"
    assert request.system_instruction == "Be helpful"
    assert request.max_iterations == 5
    assert request.initial_plan == "Start with search"


def test_chat_completion_request_missing_messages():
    """Test creating a ChatCompletionRequest with missing messages."""
    # messages is a required field in the Pydantic model
    with pytest.raises(ValidationError):
        ChatCompletionRequest()


# --- Unit tests for SessionSummary ---


def test_session_summary_creation():
    """Test creating a SessionSummary."""
    summary = SessionSummary(
        session_id="session-123",
        user_id="user-abc",
        created_at=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 10, 27, 12, 30, 0, tzinfo=timezone.utc),
        status="completed",  # Use string value for status
        current_iteration=3,
        last_error="None",
    )
    assert summary.session_id == "session-123"
    assert summary.user_id == "user-abc"
    assert isinstance(summary.created_at, datetime)
    assert isinstance(summary.updated_at, datetime)
    assert summary.status.value == "completed"  # Check the enum value
    assert summary.current_iteration == 3
    assert summary.last_error == "None"


def test_session_summary_missing_required():
    """Test creating a SessionSummary with missing required fields."""
    with pytest.raises(ValidationError):
        SessionSummary(user_id="user-abc")  # Missing session_id


def test_session_summary_invalid_status():
    """Test creating a SessionSummary with an invalid status string."""
    with pytest.raises(ValidationError):
        SessionSummary(session_id="session-123", status="invalid-status")


# --- Unit tests for SessionSummaryList ---


def test_session_summary_list_creation_empty():
    """Test creating an empty SessionSummaryList."""
    summary_list = SessionSummaryList(sessions=[])
    assert isinstance(summary_list.sessions, list)
    assert len(summary_list.sessions) == 0
    assert summary_list.start_time is None
    assert summary_list.end_time is None


def test_session_summary_list_with_data():
    """Test creating a SessionSummaryList with SessionSummary data."""
    summary1 = SessionSummary(
        session_id="s1", created_at=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc), status="completed"
    )
    summary2 = SessionSummary(
        session_id="s2", created_at=datetime(2023, 10, 27, 13, 0, 0, tzinfo=timezone.utc), status="running"
    )
    summary_list = SessionSummaryList(sessions=[summary1, summary2])

    assert isinstance(summary_list.sessions, list)
    assert len(summary_list.sessions) == 2
    assert summary_list.sessions[0] == summary1
    assert summary_list.sessions[1] == summary2
    assert summary_list.start_time == datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    assert summary_list.end_time == datetime(2023, 10, 27, 13, 0, 0, tzinfo=timezone.utc)


def test_session_summary_list_add_session():
    """Test adding a session to SessionSummaryList."""
    summary_list = SessionSummaryList(sessions=[])
    summary1 = SessionSummary(
        session_id="s1", created_at=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc), status="completed"
    )
    summary_list.add_session(summary1)
    assert len(summary_list.sessions) == 1
    assert summary_list.sessions[0] == summary1
    assert summary_list.start_time == datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    assert summary_list.end_time == datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

    summary2 = SessionSummary(
        session_id="s2", created_at=datetime(2023, 10, 27, 11, 0, 0, tzinfo=timezone.utc), status="running"
    )
    summary_list.add_session(summary2)
    assert len(summary_list.sessions) == 2
    assert summary_list.start_time == datetime(2023, 10, 27, 11, 0, 0, tzinfo=timezone.utc)
    assert summary_list.end_time == datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)


def test_session_summary_list_invalid_data_type():
    """Test creating a SessionSummaryList with invalid data type in the list."""
    summary1 = SessionSummary(
        session_id="s1", created_at=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc), status="completed"
    )
    with pytest.raises(ValidationError):
        SessionSummaryList(sessions=[summary1, "not a summary"])
