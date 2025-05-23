from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from .configuration import DEFAULT_MODEL, REASON_MODEL
from .helper_classes import Message, Messages


class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelObject]


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="deep_researcher")
    messages: Messages
    streaming: bool = False
    max_iterations: Optional[int] = Field(default=15, ge=1, le=50)
    max_search_items: Optional[int] = Field(default=4, ge=1, le=50)
    default_model: Optional[str] = Field(
        default=DEFAULT_MODEL,
        description="Override the default model from config",
        examples=["phi4-reasoning", "gemma3:4b"],
    )
    reason_model: Optional[str] = Field(
        default=REASON_MODEL,
        description="Override the reason model from config",
        examples=["qwen3-14b", "qwen3-4b"],
    )
    # Add system_instruction if needed, or extract from messages
    system_instruction: Optional[str] = Field(default=None, description="Optional system instruction override")


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]


# Session Management Models
class SessionSummary(BaseModel):
    session_id: str
    user_query: str
    status: str
    start_time: datetime
    # Add other relevant summary fields if needed, e.g., end_time
    end_time: Optional[datetime] = None


class SessionSummaryList(BaseModel):
    sessions: List[SessionSummary]
    start_time: str
