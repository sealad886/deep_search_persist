import json
from datetime import datetime, timezone

import pytest

from deep_search_persist.deep_search_persist.helper_classes import (
    Message,
    Messages,
    MessageStorageError,
    MessageValidationError,
)

# --- Unit tests for Message class ---


def test_message_creation():
    """Test creating a Message object with minimal required fields."""
    message = Message(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"
    assert isinstance(message.timestamp, datetime)
    assert message.metadata == {}


def test_message_creation_with_metadata():
    """Test creating a Message object with metadata."""
    metadata = {"source": "test", "id": 123}
    message = Message(role="assistant", content="Response.", metadata=metadata)
    assert message.role == "assistant"
    assert message.content == "Response."
    assert isinstance(message.timestamp, datetime)
    assert message.metadata == metadata


def test_message_creation_with_timestamp():
    """Test creating a Message object with a specific timestamp."""
    specific_time = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
    message = Message(role="system", content="Instruction.", timestamp=specific_time)
    assert message.role == "system"
    assert message.content == "Instruction."
    assert message.timestamp == specific_time
    assert message.metadata == {}


def test_message_to_dict():
    """Test converting a Message object to a dictionary."""
    specific_time = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
    message = Message(role="user", content="Test message.", timestamp=specific_time, metadata={"key": "value"})
    message_dict = message.to_dict()
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Test message."
    assert message_dict["timestamp"] == specific_time.isoformat()
    assert message_dict["metadata"] == {"key": "value"}


def test_message_from_dict_valid():
    """Test creating a Message object from a valid dictionary."""
    specific_time_str = "2023-10-27T10:00:00+00:00"
    message_data = {
        "role": "assistant",
        "content": "Reply.",
        "timestamp": specific_time_str,
        "metadata": {"status": "ok"},
    }
    message = Message.from_dict(message_data)
    assert message.role == "assistant"
    assert message.content == "Reply."
    assert message.timestamp == datetime.fromisoformat(specific_time_str)
    assert message.metadata == {"status": "ok"}


def test_message_from_dict_missing_required():
    """Test creating a Message object from a dictionary missing required fields."""
    message_data_missing_role = {"content": "Content only."}
    with pytest.raises(MessageValidationError, match="Required fields 'role' or 'content' are missing."):
        Message.from_dict(message_data_missing_role)

    message_data_missing_content = {"role": "user"}
    with pytest.raises(MessageValidationError, match="Required fields 'role' or 'content' are missing."):
        Message.from_dict(message_data_missing_content)


def test_message_from_dict_invalid_timestamp():
    """Test creating a Message object from a dictionary with an invalid timestamp format."""
    message_data_invalid_timestamp = {"role": "user", "content": "Content.", "timestamp": "invalid-time"}
    with pytest.raises(MessageValidationError, match="Invalid timestamp format"):
        Message.from_dict(message_data_invalid_timestamp)


def test_message_to_json():
    """Test converting a Message object to a JSON string."""
    specific_time = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
    message = Message(role="system", content="Json test.", timestamp=specific_time)
    json_str = message.to_json()
    loaded_data = json.loads(json_str)
    assert loaded_data["role"] == "system"
    assert loaded_data["content"] == "Json test."
    assert loaded_data["timestamp"] == specific_time.isoformat()


def test_message_from_json():
    """Test creating a Message object from a JSON string."""
    json_str = '{"role": "user", "content": "From JSON.", "timestamp": "2023-10-27T11:00:00+00:00", "metadata": {"source": "json"}}'
    message = Message.from_json(json_str)
    assert message.role == "user"
    assert message.content == "From JSON."
    assert message.timestamp == datetime.fromisoformat("2023-10-27T11:00:00+00:00")
    assert message.metadata == {"source": "json"}


def test_message_from_json_malformed():
    """Test creating a Message object from a malformed JSON string."""
    malformed_json_str = '{"role": "user", "content": "Malformed", "timestamp": "2023-10-27T11:00:00+00:00", "metadata": {"source": "json"'  # Missing closing brace
    with pytest.raises(MessageValidationError, match="Malformed JSON"):
        Message.from_json(malformed_json_str)


# --- Unit tests for Messages class ---


def test_messages_creation_empty():
    """Test creating an empty Messages container."""
    messages = Messages()
    assert len(messages) == 0
    assert messages.get_messages() == []


def test_messages_creation_with_list():
    """Test creating a Messages container with a list of Message objects."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    messages = Messages(messages=[msg1, msg2])
    assert len(messages) == 2
    retrieved_messages = messages.get_messages()
    assert len(retrieved_messages) == 2
    assert retrieved_messages[0] == msg1
    assert retrieved_messages[1] == msg2


def test_messages_creation_with_single_message():
    """Test creating a Messages container with a single Message object."""
    msg1 = Message(role="user", content="Msg 1")
    messages = Messages(messages=[msg1])
    assert len(messages) == 1
    retrieved_messages = messages.get_messages()
    assert len(retrieved_messages) == 1
    assert retrieved_messages[0] == msg1


def test_messages_add_message_object():
    """Test adding a Message object to the container."""
    messages = Messages()
    msg1 = Message(role="user", content="Msg 1")
    messages.add_message(msg1)
    assert len(messages) == 1
    assert messages.get_messages()[0] == msg1


def test_messages_add_messages_object():
    """Test adding another Messages object to the container."""
    messages1 = Messages()
    msg1 = Message(role="user", content="Msg 1")
    messages1.add_message(msg1)

    messages2 = Messages()
    msg2 = Message(role="assistant", content="Msg 2")
    messages2.add_message(msg2)

    messages1.add_message(messages2)
    assert len(messages1) == 2
    retrieved_messages = messages1.get_messages()
    assert retrieved_messages[0] == msg1
    assert retrieved_messages[1] == msg2


def test_messages_add_message_components():
    """Test adding a message using sender, content, and metadata."""
    messages = Messages()
    messages.add_message("user", "Component message.", metadata={"source": "components"})
    assert len(messages) == 1
    msg = messages.get_messages()[0]
    assert msg.role == "user"
    assert msg.content == "Component message."
    assert msg.metadata == {"source": "components"}
    assert isinstance(msg.timestamp, datetime)


def test_messages_add_message_invalid_sender():
    """Test adding a message with an invalid sender role."""
    messages = Messages()
    with pytest.raises(MessageValidationError, match="Sender 'invalid_role' is not allowed."):
        messages.add_message("invalid_role", "Content.")


def test_messages_to_list_of_dicts():
    """Test converting Messages to a list of dictionaries."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    messages = Messages(messages=[msg1, msg2])
    list_of_dicts = messages.to_list_of_dicts()
    assert isinstance(list_of_dicts, list)
    assert len(list_of_dicts) == 2
    assert list_of_dicts[0]["role"] == "user"
    assert list_of_dicts[1]["content"] == "Msg 2"


def test_messages_to_openai_format():
    """Test converting Messages to OpenAI API format."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    messages = Messages(messages=[msg1, msg2])
    openai_format = messages.to_openai_format()
    assert isinstance(openai_format, list)
    assert len(openai_format) == 2
    assert openai_format[0] == {"role": "user", "content": "Msg 1"}
    assert openai_format[1] == {"role": "assistant", "content": "Msg 2"}


def test_messages_from_list_of_dicts():
    """Test creating Messages from a list of dictionaries."""
    list_of_dicts = [
        {"role": "user", "content": "Dict Msg 1"},
        {"role": "assistant", "content": "Dict Msg 2", "metadata": {"source": "dict"}},
    ]
    messages = Messages.from_list_of_dicts(list_of_dicts)
    assert len(messages) == 2
    retrieved_messages = messages.get_messages()
    assert retrieved_messages[0].role == "user"
    assert retrieved_messages[0].content == "Dict Msg 1"
    assert retrieved_messages[1].role == "assistant"
    assert retrieved_messages[1].content == "Dict Msg 2"
    assert retrieved_messages[1].metadata == {"source": "dict"}


def test_messages_from_list_of_dicts_invalid_item():
    """Test creating Messages from a list with an invalid item type."""
    list_with_invalid = [{"role": "user", "content": "Valid"}, "invalid_item"]
    with pytest.raises(MessageValidationError, match="Item at index 1 is not a dictionary"):
        Messages.from_list_of_dicts(list_with_invalid)


def test_messages_from_list_of_dicts_invalid_message_data():
    """Test creating Messages from a list with invalid message dictionary data."""
    list_with_invalid_msg = [{"role": "user", "content": "Valid"}, {"content": "Missing role"}]
    with pytest.raises(MessageValidationError, match="Error parsing message at index 1 from dictionary"):
        Messages.from_list_of_dicts(list_with_invalid_msg)


def test_messages_get_messages_returns_copy():
    """Test that get_messages returns a copy of the internal list."""
    msg1 = Message(role="user", content="Msg 1")
    messages = Messages(messages=[msg1])
    retrieved_messages = messages.get_messages()
    assert retrieved_messages[0] == msg1
    assert retrieved_messages is not messages._messages  # Ensure it's a different list object


def test_messages_pretty_print():
    """Test the pretty_print method."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2", metadata={"key": "value"})
    messages = Messages(messages=[msg1, msg2])
    pretty_output = messages.pretty_print()
    assert "[user]: Msg 1" in pretty_output
    assert "[assistant]: Msg 2" in pretty_output
    assert 'Metadata: {"key": "value"}' in pretty_output


def test_messages_pretty_print_empty():
    """Test pretty_print on an empty Messages container."""
    messages = Messages()
    assert messages.pretty_print() == "No messages in the container."


def test_messages_filter_by_sender():
    """Test filtering messages by sender."""
    msg1 = Message(role="user", content="User msg 1")
    msg2 = Message(role="assistant", content="Assistant msg 1")
    msg3 = Message(role="user", content="User msg 2")
    messages = Messages(messages=[msg1, msg2, msg3])

    user_messages = messages.filter_by_sender("user")
    assert len(user_messages) == 2
    assert all(msg.role == "user" for msg in user_messages)
    assert user_messages.get_messages()[0].content == "User msg 1"
    assert user_messages.get_messages()[1].content == "User msg 2"

    assistant_messages = messages.filter_by_sender("assistant")
    assert len(assistant_messages) == 1
    assert assistant_messages.get_messages()[0].role == "assistant"
    assert assistant_messages.get_messages()[0].content == "Assistant msg 1"

    system_messages = messages.filter_by_sender("system")
    assert len(system_messages) == 0


def test_messages_filter_by_sender_invalid_sender():
    """Test filtering with an invalid sender string."""
    messages = Messages()
    with pytest.raises(MessageValidationError, match="Sender for filtering must be a non-empty string."):
        messages.filter_by_sender("")


def test_messages_sort_by_timestamp():
    """Test sorting messages by timestamp."""
    msg1 = Message(role="user", content="Msg 1", timestamp=datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc))
    msg2 = Message(role="assistant", content="Msg 2", timestamp=datetime(2023, 10, 27, 11, 0, 0, tzinfo=timezone.utc))
    msg3 = Message(role="user", content="Msg 3", timestamp=datetime(2023, 10, 27, 9, 0, 0, tzinfo=timezone.utc))
    messages = Messages(messages=[msg1, msg2, msg3])

    messages.sort_by_timestamp()  # Ascending
    sorted_messages_asc = messages.get_messages()
    assert sorted_messages_asc[0] == msg3
    assert sorted_messages_asc[1] == msg1
    assert sorted_messages_asc[2] == msg2

    messages.sort_by_timestamp(reverse=True)  # Descending
    sorted_messages_desc = messages.get_messages()
    assert sorted_messages_desc[0] == msg2
    assert sorted_messages_desc[1] == msg1
    assert sorted_messages_desc[2] == msg3


def test_messages_getitem():
    """Test retrieving a message by index."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    messages = Messages(messages=[msg1, msg2])
    assert messages[0] == msg1
    assert messages[1] == msg2
    with pytest.raises(IndexError):
        messages[2]
    with pytest.raises(IndexError):
        messages[-3]


def test_messages_iter():
    """Test iterating through Messages."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    messages = Messages(messages=[msg1, msg2])
    iter_messages = list(messages)
    assert iter_messages == [msg1, msg2]


def test_messages_len():
    """Test getting the number of messages."""
    messages = Messages()
    assert len(messages) == 0
    messages.add_message("user", "Msg 1")
    assert len(messages) == 1
    messages.add_message("assistant", "Msg 2")
    assert len(messages) == 2


def test_messages_repr():
    """Test the __repr__ method."""
    messages = Messages()
    assert repr(messages) == "Messages(count=0)"
    messages.add_message("user", "Msg 1")
    assert repr(messages) == "Messages(count=1)"


def test_messages_str():
    """Test the __str__ method (delegates to pretty_print)."""
    msg1 = Message(role="user", content="Msg 1")
    messages = Messages(messages=[msg1])
    assert str(messages) == messages.pretty_print()
