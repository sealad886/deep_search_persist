from datetime import datetime, timedelta, timezone

import pytest

from deep_search_persist.deep_search_persist.persistence.utils import DatetimeException, clean_dict, from_iso, to_iso

# --- Unit tests for date/time conversion functions ---


def test_to_iso_datetime():
    """Test converting a datetime object to ISO 8601 string."""
    dt_obj = datetime(2023, 10, 27, 10, 30, 0, tzinfo=timezone.utc)
    iso_str = to_iso(dt_obj)
    assert iso_str == "2023-10-27T10:30:00+00:00"


def test_to_iso_none():
    """Test converting None to ISO 8601 string."""
    iso_str = to_iso(None)
    assert iso_str is None


def test_to_iso_non_datetime():
    """Test converting a non-datetime object to ISO 8601 string (should return None)."""
    iso_str = to_iso("not a datetime")
    assert iso_str is None


def test_from_iso_valid_string():
    """Test converting a valid ISO 8601 string to datetime object."""
    iso_str = "2023-10-27T10:30:00+00:00"
    dt_obj = from_iso(iso_str)
    assert isinstance(dt_obj, datetime)
    assert dt_obj == datetime(2023, 10, 27, 10, 30, 0, tzinfo=timezone.utc)


def test_from_iso_valid_string_zulu():
    """Test converting a valid ISO 8601 string with Z (Zulu time) to datetime object."""
    iso_str = "2023-10-27T10:30:00Z"
    dt_obj = from_iso(iso_str)
    assert isinstance(dt_obj, datetime)
    assert dt_obj == datetime(2023, 10, 27, 10, 30, 0, tzinfo=timezone.utc)


def test_from_iso_none():
    """Test converting None from ISO 8601 string."""
    dt_obj = from_iso(None)
    assert dt_obj is None


def test_from_iso_invalid_string():
    """Test converting an invalid ISO 8601 string (should return None)."""
    dt_obj = from_iso("invalid-time-string")
    assert dt_obj is None


def test_from_iso_non_string():
    """Test converting a non-string value from ISO 8601 (should return None)."""
    dt_obj = from_iso("not a string")
    assert dt_obj is None


# --- Unit tests for dictionary cleaning function ---


def test_clean_dict_removes_none_and_empty_strings():
    """Test that clean_dict removes keys with None or empty string values."""
    input_dict = {
        "key1": "value1",
        "key2": None,
        "key3": "",
        "key4": 0,
        "key5": False,
        "key6": " ",  # Should not be removed
        "key7": [],  # Should not be removed
        "key8": {},  # Should not be removed
    }
    cleaned = clean_dict(input_dict)
    assert cleaned == {
        "key1": "value1",
        "key4": 0,
        "key5": False,
        "key6": " ",
        "key7": [],
        "key8": {},
    }


def test_clean_dict_nested():
    """Test clean_dict with nested dictionaries."""
    input_dict = {
        "key1": "value1",
        "nested": {
            "nested_key1": "nested_value1",
            "nested_key2": None,
            "nested_key3": "",
            "nested_key4": {},
        },
        "key2": None,
    }
    cleaned = clean_dict(input_dict)
    assert cleaned == {
        "key1": "value1",
        "nested": {
            "nested_key1": "nested_value1",
            "nested_key4": {},
        },
    }


def test_clean_dict_list_of_dicts():
    """Test clean_dict with a list containing dictionaries."""
    input_dict = {
        "list_key": [
            {"item1_key1": "value1", "item1_key2": None},
            {"item2_key1": "", "item2_key2": "value2"},
            {},
            None,  # None in list should be kept
        ],
        "key": "value",
    }
    cleaned = clean_dict(input_dict)
    assert cleaned == {
        "list_key": [
            {"item1_key1": "value1"},
            {"item2_key2": "value2"},
            {},
            None,
        ],
        "key": "value",
    }


def test_clean_dict_empty_dict():
    """Test clean_dict with an empty dictionary."""
    input_dict = {}
    cleaned = clean_dict(input_dict)
    assert cleaned == {}


def test_clean_dict_none_input():
    """Test clean_dict with None as input."""
    cleaned = clean_dict(None)
    assert cleaned is None


def test_clean_dict_non_dict_input():
    """Test clean_dict with non-dictionary input."""
    input_str = "just a string"
    cleaned = clean_dict(input_str)
    assert cleaned == input_str

    input_list = [1, 2, None, ""]
    cleaned = clean_dict(input_list)
    assert cleaned == input_list
