"""
session_persistence.py
MongoDB-backed session persistence for Deep Search research sessions.
"""

import hashlib
import json
import time
from abc import ABCMeta
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, Iterable, List, Literal, MutableSequence, Optional, Tuple
from typing_extensions import TypeAlias

from bson import ObjectId
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Extra
from typing_extensions import Self

from ..logging.logging_config import AsyncLogContext, LogContext
from ..persistence.utils import DatetimeException, clean_dict, from_iso, to_iso


# --- Status Constants ---
class SessionStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    _INIT = "init"

    @classmethod
    def __contains__(cls, item: object) -> bool:
        # Allows checking if a string is a valid status value, e.g., "running" in SessionStatuses
        if isinstance(item, str):
            return item in {member.value for member in cls}
        # Allows checking if an enum member is part of the enum, e.g., SessionStatuses.RUNNING in SessionStatuses
        return isinstance(item, cls)

    @classmethod
    def get_all_values(cls) -> Tuple[str, ...]:
        """Returns a tuple of all string values of the statuses."""
        return tuple(member.value for member in cls)


# --- Pydantic Session Summary ---
class SessionSummary(BaseModel):
    status_types: ClassVar[type[SessionStatus]] = SessionStatus  # Assign the Enum class

    session_id: str
    user_query: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus._INIT  # Use the Enum type directly
    current_iteration: Optional[int] = None
    last_error: Optional[str] = None


class SessionSummaryList(BaseModel):
    sessions: List[SessionSummary]
    _start_time: Optional[datetime] = None  # The datetime of the first SessionSummary in the SessionSummaryList
    _end_time: Optional[datetime] = None  # The datetime of the last SessionSummary in the SessionSummaryList

    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    def __deepcopy__(self, memo: Optional[Dict[int, Any]] = None) -> Self:
        import copy
        return copy.deepcopy(self, memo)

    def __copy__(self) -> Self:
        return self.__deepcopy__()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SessionSummaryList):
            return False
        return self.sessions == value.sessions

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __func_datetime(
        self, internal_param_name: Literal["_start_time", "_end_time"], func: Callable[[Iterable[datetime]], datetime]
    ) -> Optional[datetime]:
        if not hasattr(self, internal_param_name):
            logger.critical("Development bug. Please report.")
            raise DatetimeException()

        # Use getattr instead of self.get() since BaseModel doesn't have get() method
        current_value = getattr(self, internal_param_name, None)
        if current_value:
            return current_value
        elif self.sessions and isinstance(self.sessions, List) and len(self.sessions) > 0:
            # Calculate the datetime value using the provided function
            datetime_values = [s.created_at for s in self.sessions if s.created_at]
            if datetime_values:
                calculated_value = func(datetime_values)
                setattr(self, internal_param_name, calculated_value)
                return calculated_value
        return None

    @property
    def start_time(self) -> Optional[datetime]:
        return self.__func_datetime("_start_time", min)

    @property
    def end_time(self) -> Optional[datetime]:
        return self.__func_datetime("_end_time", max)

    def add_session(self, session: SessionSummary) -> None:
        # add the session
        try:
            self.sessions.append(session)
        except AttributeError:
            self.sessions = [session]

        # confirm start and end times of the SessionSummaryList are accurate
        if session.created_at is not None:
            if self._start_time is None:
                self._start_time = session.created_at
            else:
                self._start_time = min(self._start_time, session.created_at)

        # The end_time logic is missing, add it here
        if session.created_at is not None:
            if self._end_time is None:
                self._end_time = session.created_at
            else:
                self._end_time = max(self._end_time, session.created_at)


# --- Main Persistence Manager ---
class SessionPersistenceManager:

    client: AsyncIOMotorClient[Any]
    db: AsyncIOMotorDatabase[Any]
    _session_summaries: Optional[SessionSummaryList] = None  # Private with type hint

    def __init__(self, mongo_uri: str, db_name: str = "deep_search"):
        logger.debug("Initializing SessionPersistenceManager", db_name=db_name)
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db: AsyncIOMotorDatabase[Any] = self.client[db_name]
        self.session_collection = self.db["sessions"]
        self.validation_hashes_collection = self.db["session_validation_hashes"]
        self.session_summaries: Optional[SessionSummaryList] = None  # Renamed for clarity
        logger.info("SessionPersistenceManager initialized", db_name=db_name)

    async def initialize(self) -> None:
        """Asynchronously load and validate sessions from MongoDB"""
        async with AsyncLogContext("session_persist.initialize"):
            logger.info("Initializing session persistence and loading sessions")
            start_time = time.time()
            valid_sessions: List[SessionSummary] = []  # Initialize here, specify type

            try:
                session_docs = await self.session_collection.find().to_list(None)
                logger.debug("Retrieved session documents from database", count=len(session_docs))

                for session_doc in session_docs:
                    # Initialize session_id for each document within the loop
                    current_session_id_str = "unknown_in_loop"  # Default for logging if _id is missing
                    try:  # Inner try for processing each session_doc
                        _session_id_obj = session_doc.get("_id")
                        if not _session_id_obj:
                            logger.error(
                                "Session document missing _id",
                                document_snippet=str(session_doc)[:100],
                            )
                            continue  # Skip this document

                        session_id = _session_id_obj  # Now it's an ObjectId
                        current_session_id_str = str(session_id)

                        validation_hash_doc = await self.validation_hashes_collection.find_one(
                            {"session_id": session_id}  # Use ObjectId for query
                        )

                        if not validation_hash_doc:
                            logger.warning(
                                "Missing validation hash for session",
                                session_id=current_session_id_str,
                            )
                            continue  # Skip this session, proceed to next in loop

                        stored_hash = validation_hash_doc["session_hash"]
                        session_data = session_doc.get("data", {})
                        session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
                        current_hash = hashlib.sha256(session_data_str.encode()).hexdigest()
                        logger.debug(
                            "Validating session hash",
                            session_id=current_session_id_str,
                            hash_match=(current_hash == stored_hash),
                        )

                        if current_hash == stored_hash:
                            # Pydantic validation and SessionSummary creation logic
                            db_status_str = session_doc.get("status", SessionStatus.ERROR.value)
                            if db_status_str not in SessionStatus:
                                logger.warning(
                                    "Session has invalid status. Defaulting to ERROR",
                                    session_id=current_session_id_str,
                                    invalid_status=db_status_str,
                                )
                                final_status = SessionStatus.ERROR
                            else:
                                final_status = SessionStatus(db_status_str)

                            created_dt = from_iso(session_doc.get("created_at")) or datetime.now(timezone.utc)
                            updated_dt = from_iso(session_doc.get("updated_at")) or datetime.now(timezone.utc)

                            valid_sessions.append(
                                SessionSummary(
                                    session_id=current_session_id_str,
                                    user_id=session_doc.get("user_id"),
                                    created_at=created_dt,
                                    updated_at=updated_dt,
                                    status=final_status,
                                    current_iteration=session_doc.get("current_iteration", 0),
                                    last_error=session_doc.get("last_error"),
                                )
                            )
                        else:
                            logger.warning(
                                "Hash mismatch for session",
                                session_id=current_session_id_str,
                            )

                    except Exception as e_inner_loop:  # Catch errors for a single session_doc processing
                        logger.exception(
                            "Error processing/validating individual session during initialization",
                            session_id=current_session_id_str,
                            error=str(e_inner_loop),
                        )
                        # Continue to the next session_doc by allowing the loop to iterate

                self.session_summaries = SessionSummaryList(sessions=valid_sessions)  # Assign after loop
                end_time = time.time()
                logger.info(
                    "Session persistence initialization completed",
                    session_count=len(valid_sessions),
                    duration_ms=round((end_time - start_time) * 1000, 2),
                )

            except Exception as e_outer:  # Outer except for major failures (e.g., DB connection)
                logger.exception(
                    "Failed to initialize session persistence (outer try)",
                    error=str(e_outer),
                )
                self.session_summaries = SessionSummaryList(sessions=[])  # Ensure it's initialized
                raise

    async def save_session(self, session: Any, iteration: int) -> None:
        """
        Save or update a session document. Stores a snapshot in history.
        """
        async with AsyncLogContext("session_persist.save_session"):
            start_time = time.time()
            utc_now = datetime.now(timezone.utc)

            session_id_val = getattr(session, "session_id", None)
            session_obj_id = getattr(session, "mongo_object_id", None)
            # Ensure mongo_object_id is a BSON ObjectId, create new if missing or incorrect type
            if not isinstance(session_obj_id, ObjectId):
                session_obj_id = ObjectId()
                session.mongo_object_id = session_obj_id
            session_data = session.model_dump() if hasattr(session, "model_dump") else dict(session)
            status_val = getattr(session, "status", SessionStatus.ERROR.value)
            if isinstance(status_val, SessionStatus):
                status_val = status_val.value
            elif status_val not in SessionStatus.get_all_values():
                status_val = SessionStatus.ERROR.value

            is_new_session = not session_id_val
            saved_session_id_str: Optional[str] = None  # To store the ID for logging

            try:  # Main try for the entire save operation (insert or update)
                if is_new_session:
                    logger.info(
                        "Saving a new session",
                        user_id=getattr(session, "user_id", None),
                    )
                    doc: Dict[str, Any] = {
                        "_id": session_obj_id,
                        "user_id": getattr(session, "user_id", None),
                        "created_at": to_iso(utc_now),
                        "updated_at": to_iso(utc_now),
                        "status": status_val,
                        "current_iteration": iteration,
                        "data": session_data,
                        "last_error": getattr(session, "error_message", None),
                        "version": 1,
                        "history": [],
                    }
                    db_response = await self.session_collection.insert_one(doc)
                    saved_session_id_obj = db_response.inserted_id
                    saved_session_id_str = str(session_obj_id)
                    session.session_id = saved_session_id_str  # Update the passed-in session object
                    logger.debug("New session created", session_id=saved_session_id_str)

                    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
                    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
                    await self.validation_hashes_collection.insert_one(
                        {
                            "session_id": session_obj_id,  # Use ObjectId
                            "session_hash": hash_val,
                        }
                    )
                    logger.debug(
                        "Validation hash saved for new session",
                        session_id=saved_session_id_str,
                    )
                else:
                    # Existing session
                    saved_session_id_str = str(session_obj_id)
                    logger.info("Updating session", session_id=saved_session_id_str)
                    update_doc = {
                        "status": status_val,
                        "current_iteration": iteration,
                        "data": session_data,
                        "last_error": getattr(session, "error_message", None),
                        "updated_at": to_iso(utc_now),
                    }
                    history_entry = {
                        "iteration": iteration,
                        "timestamp": to_iso(utc_now),
                        "data": session_data,
                    }
                    await self.session_collection.update_one(
                        {"_id": session_obj_id},
                        {"$set": update_doc, "$push": {"history": history_entry}},
                    )
                    # Update validation hash for existing session
                    session_data_str = json.dumps(clean_dict(session_data), sort_keys=True)
                    hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
                    await self.validation_hashes_collection.update_one(
                        {"session_id": session_obj_id},
                        {"$set": {"session_hash": hash_val}},
                        upsert=True,
                    )
                    logger.debug(
                        "Validation hash updated for existing session",
                        session_id=saved_session_id_str,
                    )

                end_time = time.time()
                logger.info(
                    "Session saved successfully",
                    session_id=saved_session_id_str,
                    is_new=is_new_session,
                    duration_ms=round((end_time - start_time) * 1000, 2),
                )

            except Exception as e:
                logger.exception(
                    "Error during save_session",
                    session_id=saved_session_id_str or "unknown",
                    is_new=is_new_session,
                    error=str(e),
                )
                raise

    async def load_session(self, session_id: str) -> Dict[str, Any]:
        async with AsyncLogContext("session_persist.load_session", session_id=session_id):
            start_time = time.time()
            logger.debug("Loading session", session_id=session_id)

            try:
                doc = await self.session_collection.find_one({"_id": ObjectId(session_id)})
                if not doc:
                    logger.warning("Session not found during load", session_id=session_id)
                    raise ValueError(f"Session {session_id} not found")  # This will be caught below

                end_time = time.time()
                session_data = clean_dict(doc.get("data", {}))
                logger.info(
                    "Session loaded successfully",
                    session_id=session_id,
                    duration_ms=round((end_time - start_time) * 1000, 2),
                )
                return session_data
            except ValueError as ve:  # Specifically catch ValueError for "not found"
                logger.warning(f"ValueError in load_session: {str(ve)}", session_id=session_id)
                raise  # Re-raise to be handled by caller
            except Exception as e:  # Catch other potential errors
                logger.exception("Generic error loading session", session_id=session_id, error=str(e))
                raise

    async def list_sessions(self, user_id: Optional[str] = None) -> List[SessionSummary]:
        async with AsyncLogContext("session_persist.list_sessions"):
            start_time = time.time()
            logger.debug("Listing sessions", user_id=user_id if user_id else "all")
            query = {"user_id": user_id} if user_id else {}
        projection = {
            "_id": 1,
            "data.user_query": 1,
            "user_id": 1,
            "created_at": 1,
            "updated_at": 1,
            "status": 1,
            "current_iteration": 1,
            "last_error": 1,
        }

        session_docs = await self.session_collection.find(query, projection).to_list(None)
        summaries = []
        for doc in session_docs:
            try:
                db_status_str = doc.get("status", SessionStatus.ERROR.value)
                if db_status_str not in SessionStatus:
                    logger.warning(
                        f"Session {doc['_id']} has invalid status '{db_status_str}' in list_sessions. Defaulting to ERROR."
                    )
                    final_status = SessionStatus.ERROR
                else:
                    final_status = SessionStatus(db_status_str)

                # Assuming MongoDB stores BSON dates, motor converts them to Python datetime.
                # If they are strings, from_iso would be needed.
                created_dt = doc.get("created_at") or datetime.now(timezone.utc)
                updated_dt = doc.get("updated_at") or datetime.now(timezone.utc)
                if not isinstance(created_dt, datetime):
                    created_dt = from_iso(str(created_dt)) or datetime.now(timezone.utc)
                if not isinstance(updated_dt, datetime):
                    updated_dt = from_iso(str(updated_dt)) or datetime.now(timezone.utc)

                # Extract user_query from the nested data field
                user_query = None
                if "data" in doc and isinstance(doc["data"], dict):
                    user_query = doc["data"].get("user_query")
                
                summaries.append(
                    SessionSummary(
                        session_id=str(doc["_id"]),
                        user_query=user_query,
                        user_id=doc.get("user_id"),
                        created_at=created_dt,
                        updated_at=updated_dt,
                        status=final_status,
                        current_iteration=doc.get("current_iteration", 0),
                        last_error=doc.get("last_error"),
                    )
                )
            except Exception as e:
                logger.exception(
                    "Error processing/validating session",
                    session_id=str(doc.get("_id", "unknown")),
                    error=str(e),
                )

        end_time = time.time()
        logger.info(
            "Session listing completed",
            count=len(summaries),
            user_id=user_id if user_id else "all",
            duration_ms=round((end_time - start_time) * 1000, 2),
        )
        return summaries

    async def delete_session(self, session_id: str) -> None:
        async with AsyncLogContext("session_persist.delete_session", session_id=session_id):
            start_time = time.time()
            logger.info("Deleting session", session_id=session_id)

            try:
                result = await self.session_collection.delete_one({"_id": ObjectId(session_id)})
                # Also delete the validation hash
                await self.validation_hashes_collection.delete_one({"session_id": ObjectId(session_id)})

                end_time = time.time()
                logger.info(
                    "Session deleted",
                    session_id=session_id,
                    deletion_count=result.deleted_count,
                    duration_ms=round((end_time - start_time) * 1000, 2),
                )
            except Exception as e:
                logger.exception("Error deleting session", session_id=session_id, error=str(e))
                raise

    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Load session for resuming (returns latest state)."""
        async with AsyncLogContext("session_persist.resume_session", session_id=session_id):
            logger.info("Resuming session", session_id=session_id)
            try:
                session_data = await self.load_session(session_id)
                logger.debug("Session resumed successfully", session_id=session_id)
                return session_data
            except Exception as e:
                logger.exception("Error resuming session", session_id=session_id, error=str(e))
                raise

    async def update_session_metadata(self, session_id: str, **kwargs) -> None:
        async with AsyncLogContext("session_persist.update_metadata", session_id=session_id):
            allowed = {"status", "last_error", "current_iteration", "updated_at"}
            update = {k: v for k, v in kwargs.items() if k in allowed}

            if update:
                logger.debug(
                    "Updating session metadata",
                    session_id=session_id,
                    fields=list(update.keys()),
                )

                try:
                    update["updated_at"] = to_iso(datetime.now(timezone.utc))
                    result = await self.session_collection.update_one({"_id": ObjectId(session_id)}, {"$set": update})

                    logger.info(
                        "Session metadata updated",
                        session_id=session_id,
                        modified_count=result.modified_count,
                        fields=list(update.keys()),
                    )
                except Exception as e:
                    logger.exception(
                        "Error updating session metadata",
                        session_id=session_id,
                        error=str(e),
                    )
                    raise

    async def get_iteration_history(self, session_id: str) -> List[Dict[str, Any]]:
        async with AsyncLogContext("session_persist.get_history", session_id=session_id):
            logger.debug("Retrieving iteration history", session_id=session_id)

            try:
                doc = await self.session_collection.find_one({"_id": ObjectId(session_id)}, {"history": 1})

                history = doc.get("history", []) if doc else []
                logger.info(
                    "Iteration history retrieved",
                    session_id=session_id,
                    iteration_count=len(history),
                )
                return history
            except Exception as e:
                logger.exception(
                    "Error retrieving iteration history",
                    session_id=session_id,
                    error=str(e),
                )
                raise

    async def rollback_to_iteration(self, session_id: str, iteration: int) -> None:
        async with AsyncLogContext("session_persist.rollback", session_id=session_id, iteration=iteration):
            logger.info(
                "Rolling back session to iteration",
                session_id=session_id,
                target_iteration=iteration,
            )

            try:
                # Get the history document
                doc = await self.session_collection.find_one({"_id": ObjectId(session_id)}, {"history": 1})

                if not doc or "history" not in doc:
                    logger.warning("No history available for rollback", session_id=session_id)
                    raise ValueError("No history available for this session.")

                # Find the right snapshot
                for snap in reversed(doc["history"]):
                    if snap["iteration"] == iteration:
                        # Update to the snapshot state
                        result = await self.session_collection.update_one(
                            {"_id": ObjectId(session_id)},
                            {
                                "$set": {
                                    "data": snap["data"],
                                    "current_iteration": iteration,
                                }
                            },
                        )

                        # Update validation hash
                        session_data_str = json.dumps(clean_dict(snap["data"]), sort_keys=True)
                        hash_val = hashlib.sha256(session_data_str.encode()).hexdigest()
                        await self.validation_hashes_collection.update_one(
                            {"session_id": ObjectId(session_id)},
                            {"$set": {"session_hash": hash_val}},
                            upsert=True,
                        )

                        logger.info(
                            "Session successfully rolled back",
                            session_id=session_id,
                            iteration=iteration,
                            modified_count=result.modified_count,
                        )
                        return

                # If we got here, the iteration wasn't found
                logger.warning(
                    "Requested iteration not found in history",
                    session_id=session_id,
                    target_iteration=iteration,
                    available_iterations=[snap["iteration"] for snap in doc["history"]],
                )
                raise ValueError(f"Iteration {iteration} not found in history.")

            except Exception as e:
                if not isinstance(e, ValueError):
                    logger.exception(
                        "Error during session rollback",
                        session_id=session_id,
                        iteration=iteration,
                        error=str(e),
                    )
                raise


# --- Usage Example (to be used in your FastAPI endpoints, not here) ---
# persistence = SessionPersistenceManager(os.getenv("MONGO_URI"))
# await persistence.save_session(session, iteration)
# session_data = await persistence.load_session(session_id)


__all__ = [
    "SessionPersistenceManager",
    "SessionStatus",
    "SessionSummary",
    "SessionSummaryList",
]
