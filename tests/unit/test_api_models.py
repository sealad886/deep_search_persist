from datetime import datetime, timezone

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
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages

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
        ModelObject(created=1678886400, owned_by="test-owner")  # type: ignore  # Missing id
    with pytest.raises(ValidationError):
        ModelObject(id="test-model", owned_by="test-owner")  # type: ignore # Missing created
    with pytest.raises(ValidationError):
        ModelObject(id="test-model", created=1678886400)  # type: ignore # Missing owned_by


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
    model1 = ModelObject(id="model-1", created=1, owned_by="owner-1")
    with pytest.raises(ValidationError):
        ModelList(data=[model1, "not a model"])


# --- Unit tests for ChatCompletionChoice ---


def test_chat_completion_choice_creation():
    """Test creating a ChatCompletionChoice."""
    message = Message(role="assistant", content="Test response.")
    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
    assert choice.index == 0
    assert choice.message == message
    assert choice.finish_reason == "stop"


def test_chat_completion_choice_missing_required_fields():
    """Test creating a ChatCompletionChoice with missing required fields."""
    message = Message(role="assistant", content="Test response.")
    with pytest.raises(ValidationError):
        ChatCompletionChoice(message=message, finish_reason="stop")  # Missing index
    with pytest.raises(ValidationError):
        ChatCompletionChoice(index=0, finish_reason="stop")  # Missing message
    with pytest.raises(ValidationError):
        ChatCompletionChoice(index=0, message=message)  # Missing finish_reason


# --- Unit tests for ChatCompletionResponse ---


def test_chat_completion_response_creation():
    """Test creating a ChatCompletionResponse."""
    message = Message(role="assistant", content="Test.")
    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
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
    message = Message(role="assistant", content="Test.")
    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
    with pytest.raises(ValidationError):
        ChatCompletionResponse(
            object="chat.completion", created=1678886400, model="test-model", choices=[choice]
        )  # Missing id
    with pytest.raises(ValidationError):
        ChatCompletionResponse(
            id="chatcmpl-123", model="test-model", choices=[choice]
        )  # Missing created
    with pytest.raises(ValidationError):
        ChatCompletionResponse(
            id="chatcmpl-123", created=1678886400, choices=[choice]
        )  # Missing model


# --- Unit tests for ChatCompletionRequest ---


def test_chat_completion_request_creation_minimal():
    """Test creating a ChatCompletionRequest with minimal required fields."""
    user_message = Message(role="user", content="Hello")
    messages = Messages([user_message])
    request = ChatCompletionRequest(messages=messages)
    assert isinstance(request.messages, Messages)
    assert len(request.messages.messages) == 1
    assert request.messages.messages[0].content == "Hello"
    assert request.model == "deep_researcher"  # Default value
    assert request.system_instruction is None  # Default is None
    assert request.max_iterations == 15  # Default value


def test_chat_completion_request_creation_full():
    """Test creating a ChatCompletionRequest with all fields."""
    user_message = Message(role="user", content="Hello")
    assistant_message = Message(role="assistant", content="Hi")
    messages = Messages([user_message, assistant_message])
    request = ChatCompletionRequest(
        messages=messages,
        model="gpt-4",
        system_instruction="Be helpful",
        max_iterations=5,
        max_search_items=10,
        default_model="custom-model"
    )
    assert isinstance(request.messages, Messages)
    assert len(request.messages.messages) == 2
    assert request.model == "gpt-4"
    assert request.system_instruction == "Be helpful"
    assert request.max_iterations == 5
    assert request.max_search_items == 10
    assert request.default_model == "custom-model"


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
        user_query="What is AI?",
        status="completed",
        start_time=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2023, 10, 27, 12, 30, 0, tzinfo=timezone.utc),
    )
    assert summary.session_id == "session-123"
    assert summary.user_query == "What is AI?"
    assert summary.status == "completed"
    assert isinstance(summary.start_time, datetime)
    assert isinstance(summary.end_time, datetime)


def test_session_summary_missing_required():
    """Test creating a SessionSummary with missing required fields."""
    with pytest.raises(ValidationError):
        SessionSummary(user_query="What is AI?", status="completed")  # Missing session_id and start_time


def test_session_summary_valid_creation():
    """Test creating a SessionSummary with minimal required fields."""
    summary = SessionSummary(
        session_id="session-123",
        user_query="What is AI?",
        status="running",
        start_time=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    )
    assert summary.session_id == "session-123"
    assert summary.user_query == "What is AI?"
    assert summary.status == "running"
    assert summary.end_time is None  # Optional field


# --- Unit tests for SessionSummaryList ---


def test_session_summary_list_creation_empty():
    """Test creating an empty SessionSummaryList."""
    summary_list = SessionSummaryList(sessions=[])
    assert isinstance(summary_list.sessions, list)
    assert len(summary_list.sessions) == 0


def test_session_summary_list_with_data():
    """Test creating a SessionSummaryList with SessionSummary data."""
    summary1 = SessionSummary(
        session_id="s1",
        user_query="Query 1",
        status="completed",
        start_time=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    )
    summary2 = SessionSummary(
        session_id="s2",
        user_query="Query 2",
        status="running",
        start_time=datetime(2023, 10, 27, 13, 0, 0, tzinfo=timezone.utc)
    )
    summary_list = SessionSummaryList(sessions=[summary1, summary2])

    assert isinstance(summary_list.sessions, list)
    assert len(summary_list.sessions) == 2
    assert summary_list.sessions[0] == summary1
    assert summary_list.sessions[1] == summary2


def test_session_summary_list_invalid_data_type():
    """Test creating a SessionSummaryList with invalid data type in the list."""
    summary1 = SessionSummary(
        session_id="s1",
        user_query="Query 1",
        status="completed",
        start_time=datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    )
    with pytest.raises(ValidationError):
        SessionSummaryList(sessions=[summary1, "not a summary"])
