import os
from pathlib import Path
from unittest.mock import patch, mock_open
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from deep_search_persist.deep_search_persist.configuration import AppConfig

# Define a mock TOML content
MOCK_TOML_CONTENT_INCOMPLETE_REVISED = """
[Persistence]
sessions_dir = "./test_sessions_incomplete" # Loaded

[LocalAI]
# ollama_base_url is missing (default: "http://localhost:11434")
default_model = "test-model-incomplete"    # Loaded
# default_model_ctx is missing (default: -1, or actual default from AppConfig class if not -1)

[API]
openai_compat_api_key = "key_from_incomplete_toml" # Loaded
# searxng_url is missing (default: "http://localhost:8080")

[Settings]
# use_ollama is missing (default: True)
with_planning = false # Loaded

[Concurrency]
cool_down = 2.5  # Loaded
# concurrent_limit is missing (default: 3)

[Logging]
# level is missing (default: "INFO")
rotation = "5 MB" # Loaded
"""

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



@patch("deep_search_persist.deep_search_persist.configuration.CONFIG_FILE_PATH", new=Path("/fake/path/research.toml"))
@patch("deep_search_persist.deep_search_persist.configuration.Path.exists")
@patch("deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data=MOCK_TOML_CONTENT)
def test_load_config_success(mock_open_file, mock_path_exists):
    """Test successful loading of configuration from a TOML file using AppConfig."""
    mock_path_exists.return_value = True # Ensure CONFIG_FILE_PATH.exists() is true

    # Instantiate AppConfig - this will trigger the loading logic in __post_init__
    # Explicitly pass the path to ensure the patched path is used for this instance.
    test_app_config = AppConfig(config_file_path=Path("/fake/path/research.toml"))

    assert test_app_config.sessions_dir == "./test_sessions"
    assert test_app_config.ollama_base_url == "http://test-ollama:11434"
    assert test_app_config.default_model_ctx == 4096
    assert test_app_config.use_ollama is True
    assert test_app_config.concurrent_limit == 5

    # Check that the mock file was opened at the patched CONFIG_FILE_PATH
    mock_open_file.assert_called_once_with(Path("/fake/path/research.toml"), "rb")
    # tomllib.load is called internally by AppConfig, no need to mock it directly for this test if open is mocked correctly.
    # If we wanted to test tomllib.load behavior (e.g. exceptions), we would mock tomllib.load.


@patch("deep_search_persist.deep_search_persist.configuration.Path.exists")
def test_load_config_file_not_found(mock_path_exists):
    """Test AppConfig initialization when the config file is not found."""
    mock_config_path = Path("/fake/path/non_existent.toml")
    mock_path_exists.return_value = False

    # Instantiate AppConfig, passing the path that mock_path_exists is configured for
    test_app_config = AppConfig(config_file_path=mock_config_path)

    # Assert that AppConfig instance uses default values
    # These defaults come from the AppConfig class definition itself.
    assert test_app_config.sessions_dir == "./sessions"
    assert test_app_config.ollama_base_url == "http://localhost:11434"
    assert test_app_config.default_model == "mistral-openorca:latest"
    assert test_app_config.use_ollama is True # Default from AppConfig class
    mock_path_exists.assert_called_once_with()


@patch("deep_search_persist.deep_search_persist.configuration.Path.exists")
@patch("deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data="invalid toml")
@patch("deep_search_persist.deep_search_persist.configuration.tomllib.load")
@patch("deep_search_persist.deep_search_persist.configuration.logger.error") # To check if error is logged
def test_load_config_toml_decode_error(mock_logger_error, mock_toml_load, mock_open_file, mock_path_exists):
    """Test AppConfig initialization when TOML decoding fails."""
    mock_config_path = Path("/fake/path/invalid.toml")
    mock_path_exists.return_value = True
    mock_toml_load.side_effect = tomllib.TOMLDecodeError("Invalid TOML", "", 0)

    test_app_config = AppConfig(config_file_path=mock_config_path)

    # Assert that AppConfig instance uses default values
    assert test_app_config.sessions_dir == "./sessions"
    assert test_app_config.ollama_base_url == "http://localhost:11434"

    mock_open_file.assert_called_once_with(mock_config_path, "rb")
    mock_toml_load.assert_called_once()
    mock_logger_error.assert_called_once() # Check that an error was logged


@patch("deep_search_persist.deep_search_persist.configuration.Path.exists")
@patch("deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data=MOCK_TOML_CONTENT_INCOMPLETE_REVISED)
def test_app_config_uses_defaults_for_missing_toml_keys(mock_open_file, mock_path_exists):
    """Test that AppConfig uses class-defined defaults for keys missing in TOML."""
    mock_config_path = Path("/fake/path/incomplete_research.toml")
    mock_path_exists.return_value = True

    test_app_config = AppConfig(config_file_path=mock_config_path)

    # Assert values that ARE in MOCK_TOML_CONTENT_INCOMPLETE_REVISED are loaded
    assert test_app_config.sessions_dir == Path("./test_sessions_incomplete") # Path object
    assert test_app_config.default_model == "test-model-incomplete"
    assert test_app_config.openai_compat_api_key == "key_from_incomplete_toml"
    assert test_app_config.with_planning is False # Loaded as false
    assert test_app_config.cool_down == 2.5
    assert test_app_config.log_rotation == "5 MB"

    # Assert values that are MISSING in MOCK_TOML_CONTENT_INCOMPLETE_REVISED use AppConfig defaults
    # These defaults are from the AppConfig._get_config_value calls
    assert test_app_config.ollama_base_url == "http://localhost:11434"
    assert test_app_config.default_model_ctx == -1 # Default from _get_config_value
    assert test_app_config.base_searxng_url == "http://localhost:8080"
    assert test_app_config.use_ollama is True
    assert test_app_config.concurrent_limit == 3 # Default from _get_config_value
    assert test_app_config.log_level == "INFO"

    mock_open_file.assert_called_once_with(mock_config_path, "rb")


@patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://env-ollama:11434"}) # Corrected ENV VAR NAME
@patch("deep_search_persist.deep_search_persist.configuration.Path.exists")
@patch("deep_search_persist.deep_search_persist.configuration.open", new_callable=mock_open, read_data=MOCK_TOML_CONTENT) # MOCK_TOML_CONTENT has ollama_base_url in [LocalAI]
def test_app_config_overrides_toml_with_env_var(mock_open_file, mock_path_exists, _mock_env_dict_unused): # _mock_env_dict_unused from @patch.dict
    """Test AppConfig prioritizes environment variables over TOML values."""
    mock_config_path = Path("/fake/path/research.toml")
    mock_path_exists.return_value = True # Simulate TOML file exists

    # Instantiate AppConfig. It should load from the mocked TOML and then apply env overrides.
    # The environment variable OLLAMA_BASE_URL is set by @patch.dict
    test_app_config = AppConfig(config_file_path=mock_config_path)

    # Assert that the ollama_base_url is from the environment variable, not the TOML file.
    # MOCK_TOML_CONTENT defines: ollama_base_url = "http://toml-ollama:11434" in its [LocalAI] section
    # Environment variable OLLAMA_BASE_URL is "http://env-ollama:11434"
    assert test_app_config.ollama_base_url == "http://env-ollama:11434"

    # Check that the file was attempted to be read and path checked
    mock_open_file.assert_called_once_with(mock_config_path, "rb")
    mock_path_exists.assert_called_once_with(mock_config_path)
