from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, ClassVar, Dict, Generator, Iterator, List, Optional, overload

from loguru import logger
from pydantic import BaseModel, Field

from .logging.logging_config import LogContext


###
# Define custom exceptions
###
class MessageValidationError(Exception):
    """Custom exception for errors during message validation."""

    pass


class MessageStorageError(Exception):
    """Custom exception for errors during message storage or retrieval."""

    pass


class Message(BaseModel):
    """
    Represents a single message with a sender, content, timestamp, and metadata.

    Attributes:
        sender (str): The identifier of the message sender (e.g., "user", "assistant").
        content (str): The textual content of the message.
        timestamp (datetime): The date and time when the message was created or received.
                               Defaults to the current time if not provided.
        metadata (Dict[str, Any]): A dictionary for any additional information
                                   associated with the message. Defaults to an empty dict.
    """

    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Message object to a dictionary.

        The timestamp is converted to an ISO 8601 string format.

        Returns:
            Dict[str, Any]: A dictionary representation of the message.
        """
        data = self.dict()  # Use Pydantic's dict method
        if isinstance(data.get("timestamp"), datetime):  # Check if timestamp exists and is datetime
            data["timestamp"] = data["timestamp"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """
        Creates a Message object from a dictionary.

        The 'timestamp' field in the dictionary can be either an ISO 8601 string
        or a datetime object. If it's a string, it will be parsed.

        Args:
            data (Dict[str, Any]): A dictionary containing message data.
                                   Expected keys: "role", "content".
                                   Optional keys: "timestamp", "metadata".

        Returns:
            Message: An instance of the Message class.

        Raises:
            MessageValidationError: If required fields are missing or if the timestamp
                                    format is invalid.
        """
        with LogContext(
            "Message.from_dict",
            data_keys=list(data.keys()) if isinstance(data, dict) else None,
        ):
            if not all(k in data for k in ["role", "content"]):
                logger.error(
                    "Message validation failed: missing required fields 'role' or 'content'",
                    data_keys=list(data.keys()),
                )
                raise MessageValidationError("Required fields 'role' or 'content' are missing.")

            role_val = data["role"]
            content = data["content"]

            if not isinstance(role_val, str) or not role_val:
                logger.error("Message validation failed: invalid role", role=role_val)
                raise MessageValidationError("Role must be a non-empty string.")
            if not isinstance(content, str):  # Allow empty content as per current spec
                logger.error(
                    "Message validation failed: invalid content type",
                    content_type=type(content).__name__,
                )
                raise MessageValidationError("Content must be a string.")

        timestamp_data = data.get("timestamp")
        parsed_timestamp: Optional[datetime] = None

        if timestamp_data is not None:
            if isinstance(timestamp_data, datetime):
                parsed_timestamp = timestamp_data
            elif isinstance(timestamp_data, str):
                try:
                    parsed_timestamp = datetime.fromisoformat(timestamp_data)
                except ValueError:
                    logger.error(
                        "Message validation failed: invalid timestamp format",
                        timestamp=timestamp_data,
                    )
                    raise MessageValidationError(
                        f"Invalid timestamp format: '{timestamp_data}'. " "Expected ISO 8601 string or datetime object."
                    )
            else:
                logger.error(
                    "Message validation failed: invalid timestamp type",
                    timestamp_type=type(timestamp_data).__name__,
                )
                raise MessageValidationError("Timestamp must be an ISO 8601 string or a datetime object.")

        message_args: Dict[str, Any] = {
            "role": role_val,
            "content": content,
            "metadata": data.get("metadata", {}),  # Defaults to empty dict if not present
        }
        if parsed_timestamp is not None:
            message_args["timestamp"] = parsed_timestamp

        return cls(**message_args)

    @classmethod
    def from_json(cls, json_str: str) -> Message:
        """
        Creates a Message object from a JSON string.

        The JSON string should represent a dictionary with keys "sender",
        "content", and optionally "timestamp" and "metadata".

        Args:
            json_str (str): A JSON string representing a message.
        Returns:
            Message: An instance of the Message class.
        Raises:
            MessageValidationError: If the JSON string is malformed or if required fields are missing.
        """
        try:
            data = json.loads(json_str)
            logger.debug("Successfully parsed message from JSON", data_keys=list(data.keys()))
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse message JSON", error=str(e))
            raise MessageValidationError(f"Malformed JSON: {e}")

        return cls.from_dict(data)
        # Add any additional validation or processing if needed

    def to_json(self) -> str:
        """
        Serializes the Message object to a JSON string.
        The timestamp is converted to an ISO 8601 string format.
        Returns:
            str: A JSON string representation of the message.
        """
        data = self.to_dict()
        if "timestamp" in data:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat()
        return json.dumps(data, ensure_ascii=False, indent=4)  # ensure_ascii=False is good for broader char support
        # Add any additional serialization options if needed


class Messages(BaseModel):
    """
    A container class for managing a collection of Message objects.

    This class provides functionalities to add, load, save, and manipulate
    a list of messages. It also enforces constraints like allowed senders.

    Attributes:
        ALLOWED_ROLES (List[str]): A class-level list of valid sender identifiers.
    """

    ALLOWED_ROLES: ClassVar[List[str]] = ["user", "assistant", "system"]

    messages: List[Message] = Field(default_factory=list)

    def __init__(self, messages: Optional[List[Message]] = None) -> None:
        """
        Initializes the Messages container.

        Args:
            messages (Optional[List[Message]]): An optional list of Message objects
                                                to initialize the container with.
                                                If None, an empty list is created.
                                                The provided list is copied to prevent
                                                external modification.
        """
        super().__init__(messages=messages if messages is not None else [])
        with LogContext("Messages.__init__"):
            if (
                messages is not None
                and isinstance(messages, List)
                and all(isinstance(msg, Message) for msg in messages)
            ):
                logger.debug("Messages container initialized with list", count=len(messages))
            elif isinstance(messages, Message):
                logger.debug("Messages container initialized with single message")
            else:
                logger.debug("Messages container initialized empty")

    @overload
    def add_message(self, message: Message) -> None: ...

    @overload
    def add_message(self, messages: Messages) -> None: ...

    @overload
    def add_message(self, sender: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None: ...

    def add_message(self, *args, **kwargs) -> None:
        """
        Adds a message to the internal list.

        This method is overloaded to accept either a Message or Messages object or
        individual components (sender, content, metadata) to create a new Message.

        There are three ways to add messages:

        Args:
        Method 1: Add a single Message object.
            message (Message): A Message instance to add.

        Method 2: Add a Messages objects.
            messages (Messages): An instantiated Messages object.

        Method 3: Add a new message using sender, content, and optional metadata.
            sender (Messages.ALLOWED_ROLES): The identifier of the message sender.
            Allowed senders are defined in Messages.ALLOWED_ROLES.
            content (str): The textual content of the message.
            metadata (Optional[Dict[str, Any]]): Additional metadata for the message in
            {key: value} format.

        Raises:
            TypeError: If the provided argument is not a Message object or if the arguments
            are invalid.
            MessageValidationError: If the sender is not in ALLOWED_ROLES or if
            sender/content/metadata are not valid.
        """
        with LogContext("Messages.add_message"):
            if len(args) == 1:
                if isinstance(args[0], Message):
                    message = args[0]
                    self.messages.append(message)
                    logger.debug("Added single message to container", role=message.role)
                elif isinstance(args[0], Messages):
                    messages = args[0]
                    if not all(isinstance(msg, Message) for msg in messages):
                        logger.error("Invalid message type in Messages container")
                        raise TypeError("All items in Messages must be of type Message.")
                    self.messages.extend(messages.messages)  # Directly access the messages list
                    logger.debug(
                        "Added messages from another container",
                        count=len(self.messages),
                    )
            elif 2 >= len(args) >= 3 and isinstance(args[0], str) and isinstance(args[1], str):
                sender, content = args[0], args[1]
                metadata = kwargs.get("metadata", None)
                if not isinstance(sender, str) or not sender:
                    logger.error("Invalid sender format", sender=sender)
                    raise MessageValidationError("Sender must be a non-empty string.")
                if sender not in Messages.ALLOWED_ROLES:
                    logger.warning(
                        "Sender not in allowed roles",
                        sender=sender,
                        allowed_roles=Messages.ALLOWED_ROLES,
                    )
                    raise MessageValidationError(
                        f"Sender '{sender}' is not allowed. Allowed senders: {Messages.ALLOWED_ROLES}"
                    )
                if not isinstance(content, str):
                    logger.error("Invalid content type", content_type=type(content).__name__)
                    raise MessageValidationError("Content must be a string.")

                message_metadata = metadata if metadata is not None else {}
                new_message = Message(role=sender, content=content, metadata=message_metadata)
                self.messages.append(new_message)
                logger.debug(
                    "Added new message with explicit parameters",
                    role=sender,
                    content_length=len(content),
                )
            else:
                logger.error("Invalid argument format for add_message")
                raise TypeError("Invalid arguments for add_message")

    @classmethod
    def load_from_json(cls, filepath: str) -> Messages:
        """
        Loads messages from a JSON file.

        The JSON file is expected to contain a list of dictionaries, where each
        dictionary represents a message.

        Args:
            filepath (str): The path to the JSON file.

        Returns:
            Messages: A new Messages instance populated with data from the file.

        Raises:
            MessageStorageError: If the file is not found, cannot be read,
                                 or if the JSON is malformed.
            MessageValidationError: If the data within the JSON is not valid for
                                    creating Message objects.
        """
        with LogContext("Messages.load_from_json", filepath=filepath):
            try:
                logger.info("Loading messages from JSON file", filepath=filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        logger.debug(
                            "Successfully loaded JSON data",
                            item_count=(len(data) if isinstance(data, list) else "not a list"),
                        )
                    except json.JSONDecodeError as e:
                        logger.exception("Failed to parse JSON file", error=str(e))
                        raise MessageStorageError(f"Malformed JSON in file: {filepath}. Error: {e}")
            except FileNotFoundError:
                logger.error("File not found during message loading", filepath=filepath)
                raise MessageStorageError(f"File not found: {filepath}")
            except IOError as e:
                logger.exception("IO error during message loading", error=str(e))
                raise MessageStorageError(f"Error reading file: {filepath}. Error: {e}")

            if not isinstance(data, list):
                logger.error("Invalid JSON data format", type=type(data).__name__)
                raise MessageValidationError("JSON data must be a list of message dictionaries.")
            loadedmessages: List[Message] = []  # Initialize loadedmessages here

        return cls(messages=loadedmessages)

    def save_to_json(self, filepath: str) -> None:
        """
        Saves all messages to a JSON file.

        The messages are stored as a list of dictionaries.

        Args:
            filepath (str): The path to the JSON file where messages will be saved.
                            If the file exists, it will be overwritten.
                            Parent directories will be created if they don't exist.

        Raises:
            MessageStorageError: If there's an error writing to the file (e.g.,
                                 permission issues, disk full).
        """
        with LogContext("Messages.save_to_json", filepath=filepath):
            logger.info(
                "Saving messages to JSON file",
                filepath=filepath,
                message_count=len(self.messages),
            )
            try:
                dir_name = os.path.dirname(filepath)
                if dir_name:  # Ensure directory exists only if path includes a directory
                    os.makedirs(dir_name, exist_ok=True)  # Corrected this line

                list_of_dicts = self.to_list_of_dicts()
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(list_of_dicts, f, indent=4)
                logger.debug("Successfully saved messages to JSON", filepath=filepath)
            except IOError as e:
                logger.exception(
                    "IO error while saving messages to JSON",
                    filepath=filepath,
                    error=str(e),
                )
                raise MessageStorageError(f"Error writing to file {filepath}: {e}")
            except Exception as e:  # Catch other potential errors
                logger.exception(
                    "Unexpected error while saving messages to JSON",
                    filepath=filepath,
                    error=str(e),
                )
                raise MessageStorageError(f"An unexpected error occurred while saving to {filepath}: {e}")

    def to_list_of_dicts(self) -> List[Dict[str, Any]]:
        """
        Converts all messages in the container to a list of dictionaries.

        Returns:
            List[Dict[str, Any]]: A list where each item is a dictionary
                                   representation of a Message object.
        """
        return [message.to_dict() for message in self.messages]

    def to_openai_format(self) -> List[Dict[str, str]]:
        """
        Converts the list of Message objects to the OpenAI API format.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, where each dictionary
                                   has "role" (from message.sender) and "content"
                                   (from message.content) keys.
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    @classmethod
    def from_list_of_dicts(cls, data: List[Dict[str, Any]]) -> Messages:
        """
        Creates a Messages instance from a list of dictionaries.

        Each dictionary in the list should be a valid representation of a Message.

        Args:
            data (List[Dict[str, Any]]): A list of dictionaries, where each
                                         dictionary can be parsed into a Message object.

        Returns:
            Messages: A new Messages instance populated with the provided data.

        Raises:
            MessageValidationError: If any dictionary in the list cannot be
                                    parsed into a valid Message object.
        """
        loadedmessages: List[Message] = []
        if not isinstance(data, list):
            raise MessageValidationError("Input data must be a list of dictionaries.")

        for i, msg_data in enumerate(data):
            if not isinstance(msg_data, dict):
                raise MessageValidationError(f"Item at index {i} is not a dictionary: {type(msg_data)}")
            try:
                loadedmessages.append(Message.from_dict(msg_data))
            except MessageValidationError as e:
                raise MessageValidationError(f"Error parsing message at index {i} from dictionary: {e}")
        return cls(messages=loadedmessages)

    def get_messages(self) -> List[Message]:
        """
        Returns a copy of the internal list of messages.

        This prevents direct modification of the internal list from outside the class.

        Returns:
            List[Message]: A new list containing all Message objects.
        """
        return list(self.messages)

    def pretty_print(self) -> str:
        """
        Generates a multi-line, human-readable string representation of all messages.

        Each message is formatted to show its sender, timestamp, and content.

        Returns:
            str: A formatted string of all messages. If no messages, returns
                 a string indicating that.
        """
        if not self.messages:
            return "No messages in the container."

        output_lines = []
        for msg in self.messages:
            try:
                # Ensure timestamp is datetime for strftime
                ts = msg.timestamp
                if isinstance(ts, str):  # Should not happen if from_dict is used correctly
                    ts = datetime.fromisoformat(ts)
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):  # Fallback if timestamp is malformed
                ts_str = str(msg.timestamp)

            line = f"[{ts_str}] {msg.role}: {msg.content}"
            output_lines.append(line)
            if msg.metadata:
                try:
                    metadata_str = json.dumps(msg.metadata, ensure_ascii=False)
                    output_lines.append(f"  Metadata: {metadata_str}")
                except TypeError:  # Handle non-serializable metadata gracefully
                    output_lines.append(f"  Metadata: (Unserializable: {type(msg.metadata)})")
        return "\n".join(output_lines)

    def filter_by_sender(self, sender: str) -> Messages:
        """
        Creates and returns a new Messages instance containing only messages
        from the specified sender.

        Args:
            sender (str): The sender identifier to filter messages by.

        Returns:
            Messages: A new Messages instance with the filtered messages.

        Raises:
            MessageValidationError: If the sender string is invalid (e.g., empty).
        """
        if not isinstance(sender, str) or not sender:
            raise MessageValidationError("Sender for filtering must be a non-empty string.")

        filteredmessages = [msg for msg in self.messages if msg.role == sender]
        return Messages(messages=filteredmessages)

    def sort_by_timestamp(self, reverse: bool = False) -> None:
        """
        Sorts the internal list of messages in-place based on their timestamp.

        Args:
            reverse (bool): If True, sorts in descending order (newest first).
                            If False (default), sorts in ascending order (oldest first).
        """
        self.messages.sort(key=lambda msg: msg.timestamp, reverse=reverse)

    def __getitem__(self, index: int) -> Message:
        """
        Retrieves a message by its index.

        Args:
            index (int): The index of the message to retrieve.

        Returns:
            Message: The Message object at the specified index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self.messages[index]

    def __iter__(self) -> Generator[Message, None, None]:  # type: ignore[override]
        """
        Yields messages from the container.

        Allows iterating through the Messages object directly (e.g., in a for loop).

        Yields:
            Message: The next message in the container.
        """
        # This makes __iter__ a generator function, returning a Generator object.
        yield from self.messages

    def __len__(self) -> int:
        """
        Returns the number of messages in the container.

        Returns:
            int: The total count of messages.
        """
        return len(self.messages)

    def __repr__(self) -> str:
        """
        Returns an unambiguous string representation of the Messages object.

        Useful for debugging.

        Returns:
            str: A string representation like 'Messages(count=X)'.
        """
        return f"Messages(count={len(self.messages)})"

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the messages.

        Delegates to the `pretty_print` method.

        Returns:
            str: A formatted string of all messages.
        """
        return self.pretty_print()
