from datetime import datetime
from typing import Any, Optional, Union

from bson import ObjectId


# --- Utility Functions ---
def to_iso(dt: Union[datetime, str, None]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def from_iso(dt: Optional[str]) -> Optional[datetime]:
    if dt is None:
        return None
    return datetime.fromisoformat(dt)


def clean_dict(obj: Any) -> Any:
    # Recursively convert datetime to isoformat and remove non-serializable types.
    if isinstance(obj, dict):
        return {k: clean_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_dict(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj


class DatetimeException(Exception):
    pass


__all__ = [
    "clean_dict",
    "to_iso",
    "from_iso",
    "DatetimeException",
]
