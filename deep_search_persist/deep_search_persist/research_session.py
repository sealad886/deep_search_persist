import datetime
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

from .helper_classes import Messages


class ResearchSession(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    end_time: Optional[str] = None
    status: str = "running"  # running | completed | interrupted | error
    user_query: str
    system_instruction: Optional[str] = None
    settings: Dict[str, Any]
    iterations: List[Dict[str, Any]] = Field(default_factory=list)
    aggregated_data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "all_search_queries": [],
            "aggregated_contexts": [],
            "last_plan": None,
            "last_completed_iteration": -1,
        }
    )
    chat_history: Messages = Field(default_factory=Messages)
    mongo_object_id: Optional[ObjectId] = None
    
    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        # Serialize chat_history to a list of dicts for Mongo
        d["chat_history"] = (
            self.chat_history.to_list_of_dicts() if hasattr(self.chat_history, "to_list_of_dicts") else []
        )
        return d

    final_report: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "user_query": self.user_query,
            "system_instruction": self.system_instruction,
            "settings": self.settings,
            "iterations": self.iterations,
            "aggregated_data": self.aggregated_data,
            "chat_history": (self.chat_history.to_list_of_dicts() if self.chat_history else []),
            "final_report": self.final_report,
            "error_message": self.error_message,
        }

    def save_session(self, filepath: Path):
        """
        **DEPRECATED**
        Saves the current session state to a JSON file.
        """
        # TODO: Remove this method in the next major release
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving session {self.session_id} to {filepath}: {e}")

    @classmethod
    def load_session(cls, filepath: Path) -> Optional["ResearchSession"]:
        """
        **DEPRECATED**
        Loads a session from a JSON file.
        """
        # TODO: Remove this method in the next major release
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            # Recreate the session object from loaded data
            session = cls(
                user_query=data["user_query"],
                system_instruction=data.get("system_instruction"),
                settings=data["settings"],
            )
            session.session_id = data["session_id"]
            session.start_time = data["start_time"]
            session.end_time = data.get("end_time")
            session.status = data.get("status", "unknown")  # Default status if missing
            session.iterations = data.get("iterations", [])
            # Default structure if missing
            session.aggregated_data = data.get(
                "aggregated_data",
                {
                    "all_search_queries": [],
                    "aggregated_contexts": [],
                    "last_plan": None,
                    "last_completed_iteration": -1,
                },
            )
            session.mongo_object_id = data.get("mongo_object_id")

            chat_history_data = data.get("chat_history")
            if chat_history_data is not None:
                try:
                    session.chat_history = Messages.from_list_of_dicts(chat_history_data)
                # More specific exception handling for chat history
                except Exception as e_chat:
                    print(
                        f"Error loading chat_history for session {session.session_id}: {e_chat}. "
                        "Initializing empty chat history."
                    )
                    # Initialize to empty if loading fails
                    session.chat_history = Messages()
            else:
                # Initialize to empty if not present
                session.chat_history = Messages()

            session.final_report = data.get("final_report")
            session.error_message = data.get("error_message")
            return session
        except Exception as e:
            print(f"Error loading session from {filepath}: {e}")
            return None
