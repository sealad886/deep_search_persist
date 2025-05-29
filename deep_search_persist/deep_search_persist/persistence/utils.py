from datetime import datetime
from typing import Any, Optional, Union

from bson import ObjectId


# --- Utility Functions ---
def to_iso(dt: Union[datetime, str, None]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, str):
        # Try to parse string as datetime first
        try:
            # Handle Z suffix (Zulu time)
            dt_str = dt
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            parsed_dt = datetime.fromisoformat(dt_str)
            return parsed_dt.isoformat()
        except ValueError:
            return None  # Return None for invalid datetime strings
    if isinstance(dt, datetime):
        return dt.isoformat()
    return None  # Return None for non-datetime objects


def from_iso(dt: Optional[str]) -> Optional[datetime]:
    if dt is None:
        return None
    if not isinstance(dt, str):
        return None
    try:
        # Handle Z suffix (Zulu time)
        if dt.endswith('Z'):
            dt = dt[:-1] + '+00:00'
        return datetime.fromisoformat(dt)
    except ValueError:
        return None  # Return None for invalid format strings


def clean_dict(obj: Any) -> Any:
    # Recursively convert datetime to isoformat, remove None and empty strings, and handle non-serializable types.
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            cleaned_value = clean_dict(v)
            # Remove None values and empty strings
            if cleaned_value is not None and cleaned_value != "":
                cleaned[k] = cleaned_value
        return cleaned
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
