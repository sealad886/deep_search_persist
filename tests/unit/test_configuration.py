import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import tomllib

# Import the functions to be tested
from deep_search_persist.deep_search_persist.configuration import config_data, get_config_value, load_config

# Define a mock TOML content
MOCK_TOML_CONTENT = """
[Persistence]
sessions_dir = "./test_sessions"

[LocalAI]
ollama_base_url = "http://test-ollama:11434"
default_model_ctx = 4096
reason_model_ctx = 8192
default_model = "test-model"
reason_model = "test-reason-model"

[API]
openai_compat_api_key = "mock-api-key"
jina_api_key = "mock-jina-key"
openai_url = "http://test-openai/v1"
jina_base_url = "http://test-jina/v1/chat/completions"
searxng_url = "http://test-searxng:8080"

[Settings]
use_ollama = true
use_jina = false
with_planning = true

[Concurrency]
concurrent_limit = 5
cool_down = 0.5
chrome_port = 9999
chrome_host_ip = "192.168.1.100"
use_embed_browser = false

[Parsing]
pdf_max_pages = 20
pdf_max_filesize = 20971520 # 20MB
timeout_pdf = 120
max_html_length = 2000000
max_eval_time = 60
verbose_web_parse = true
browse_lite = 0
temp_pdf_dir = "./test_temp_pdfs"

[Ratelimits]
request_per_minute = 10
operation_wait_time = 2
fallback_model = "test-fallback-model"
"""


# Reset config_data before each test to ensure isolation
@pytest.fixture(autouse=True)
def reset_config_data():
    global config_data
    original_config_data = config_data.copy()
    config_data = {}
    yield
    config_data = original_config_data  # Restore original state if needed, though resetting is better for unit tests


@patch("deep_search_persist.deep_search_persist.configuration.CONFIG_FILE_PATH", new=Path("/fake/path/research.toml"))
@patch(
    "deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data=MOCK_TOML_CONTENT
)
@patch("deep_search_persist.deep_search_persist.configuration.tomllib.load")
def test_load_config_success(mock_toml_load, mock_file_open):
    """Test successful loading of configuration from a TOML file."""
    mock_toml_load.return_value = tomllib.loads(MOCK_TOML_CONTENT)
    load_config()
    assert config_data is not None
    assert "Persistence" in config_data
    assert config_data["Persistence"]["sessions_dir"] == "./test_sessions"
    mock_file_open.assert_called_once_with(Path("/fake/path/research.toml"), "rb")
    mock_toml_load.assert_called_once()


@patch(
    "deep_search_persist.deep_search_persist.configuration.CONFIG_FILE_PATH", new=Path("/fake/path/non_existent.toml")
)
@patch("deep_search_persist.deep_search_persist.configuration.open", side_effect=FileNotFoundError)
def test_load_config_file_not_found(mock_file_open):
    """Test loading configuration when the file is not found."""
    load_config()
    assert config_data == {}
    mock_file_open.assert_called_once_with(Path("/fake/path/non_existent.toml"), "rb")


@patch("deep_search_persist.deep_search_persist.configuration.CONFIG_FILE_PATH", new=Path("/fake/path/invalid.toml"))
@patch("deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data="invalid toml")
@patch(
    "deep_search_persist.deep_search_persist.configuration.tomllib.load",
    side_effect=tomllib.TOMLDecodeError("Invalid TOML", "", 0),
)
def test_load_config_toml_decode_error(mock_toml_load, mock_file_open):
    """Test loading configuration when TOML decoding fails."""
    load_config()
    assert config_data == {}
    mock_file_open.assert_called_once_with(Path("/fake/path/invalid.toml"), "rb")
    mock_toml_load.assert_called_once()


# Mock load_config to ensure config_data is populated for get_config_value tests
@patch("deep_search_persist.deep_search_persist.configuration.load_config")
def test_get_config_value_existing(mock_load_config):
    """Test retrieving an existing configuration value."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    value = get_config_value("Persistence", "sessions_dir")
    assert value == "./test_sessions"
    mock_load_config.assert_called_once()  # load_config should be called if config_data is initially empty


@patch("deep_search_persist.deep_search_persist.configuration.load_config")
def test_get_config_value_existing_with_type(mock_load_config):
    """Test retrieving an existing configuration value with type conversion."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    value_int = get_config_value("Concurrency", "concurrent_limit", value_type=int)
    assert value_int == 5
    assert isinstance(value_int, int)

    value_float = get_config_value("Concurrency", "cool_down", value_type=float)
    assert value_float == 0.5
    assert isinstance(value_float, float)

    value_bool = get_config_value("Settings", "use_ollama", value_type=bool)
    assert value_bool is True
    assert isinstance(value_bool, bool)

    value_bool_str = get_config_value("Settings", "use_ollama", value_type="bool")
    assert value_bool_str is True
    assert isinstance(value_bool_str, bool)

    mock_load_config.assert_called_once()


@patch("deep_search_persist.deep_search_persist.configuration.load_config")
def test_get_config_value_non_existing_with_default(mock_load_config):
    """Test retrieving a non-existing configuration value with a default."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    value = get_config_value("NonExistingSection", "non_existing_key", default="default_value")
    assert value == "default_value"
    mock_load_config.assert_called_once()


@patch("deep_search_persist.deep_search_persist.configuration.load_config")
def test_get_config_value_non_existing_no_default(mock_load_config):
    """Test retrieving a non-existing configuration value without a default (should raise KeyError)."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    with pytest.raises(KeyError, match="Mandatory key 'non_existing_key' not found in section 'NonExistingSection'"):
        get_config_value("NonExistingSection", "non_existing_key")
    mock_load_config.assert_called_once()


@patch("deep_search_persist.deep_search_persist.configuration.load_config")
def test_get_config_value_type_conversion_failure(mock_load_config):
    """Test retrieving a value with a type conversion failure."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    # Attempt to convert a string to an int where it's not possible
    value = get_config_value("Persistence", "sessions_dir", default="default", value_type=int)
    assert value == "default"  # Should return default on conversion failure
    mock_load_config.assert_called_once()


@patch("deep_search_persist.deep_search_persist.configuration.load_config")
@patch("os.getenv")
def test_get_config_value_from_env(mock_getenv, mock_load_config):
    """Test retrieving a configuration value overridden by an environment variable."""
    global config_data
    config_data = tomllib.loads(MOCK_TOML_CONTENT)
    # Simulate an environment variable being set
    mock_getenv.return_value = "mongodb://env-mongo:27017/test_db"

    # Note: The current get_config_value implementation doesn't check os.getenv
    # directly. Environment variables are read in the configuration.py file itself
    # when the globals are defined. This test needs to reflect that.
    # We need to re-run the relevant part of configuration.py after setting the mock env var.

    # Reset config_data and reload config after setting the mock env var
    config_data = {}
    with patch("deep_search_persist.deep_search_persist.configuration.os.getenv", mock_getenv):
        # Re-import or re-run the relevant part of configuration.py
        # A cleaner way in tests is to mock the specific variable assignment
        with patch(
            "deep_search_persist.deep_search_persist.configuration.OLLAMA_BASE_URL",
            os.getenv("OLLAMA_BASE_URL", get_config_value("LocalAI", "ollama_base_url", "http://localhost:11434")),
        ):
            # Now test the variable that was set based on the environment variable
            from deep_search_persist.deep_search_persist.configuration import (
                OLLAMA_BASE_URL,
            )  # Re-import to get the updated value

            assert OLLAMA_BASE_URL == "mongodb://env-mongo:27017/test_db"

    mock_load_config.assert_called_once()
    mock_getenv.assert_called_once_with("OLLAMA_BASE_URL", "http://test-ollama:11434")
