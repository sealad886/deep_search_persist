"""
Tests for the configuration module in the docker/persist service.
"""

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to import the module in a way that we can mock its config loading
# This is a bit tricky as 'config.read' happens at import time.
# One way is to ensure our mocks are in place *before* the first import
# or to reload the module after setting up mocks.

# For simplicity in this test, we'll assume that if we patch configparser globally,
# subsequent imports of `configuration` module (if any test runner reloads it)
# or direct access to its variables will use the mocked config.


@pytest.fixture(scope="module", autouse=True)
def mock_config_parser():
    """
    Mocks configparser to control config values for all tests in this module.
    This autouse fixture ensures config is mocked before configuration.py is
    potentially re-imported or its variables accessed by test functions.
    """
    mock_config = configparser.ConfigParser()
    mock_config.read_dict(
        {
            "Parsing": {
                "temp_pdf_dir": "/mocked/pdf/dir",
                "pdf_max_pages": "10",
                "pdf_max_filesize": "5000000",
                "timeout_pdf": "30",
                "max_html_length": "1000000",
                "max_eval_time": "10",
                "verbose_web_parse_detail": "False",
                "browse_lite": "0",
            },
            "LocalAI": {
                "ollama_base_url": "http://mock-ollama:11434",
                "default_model_ctx": "4096",
                "reason_model_ctx": "8192",
            },
            "API": {
                "openai_compat_api_key": "mock_openai_key",
                "jina_api_key": "mock_jina_key",
                "openai_url": "http://mock-openai/v1",
                "jina_base_url": "https://mock.jina.ai/",
                "searxng_url": "http://mock-searxng",
            },
            "Settings": {
                "use_ollama": "True",
                "use_jina": "False",
                "with_planning": "True",
                "default_model": "mock_default_model",
                "reason_model": "mock_reason_model",
            },
            "Concurrency": {
                "concurrent_limit": "5",
                "cool_down": "1.0",
                "chrome_port": "9223",
                "chrome_host_ip": "127.0.0.1",
                "use_embed_browser": "True",
            },
            "Ratelimits": {
                "request_per_minute": "60",
                "operation_wait_time": "0",
                "fallback_model": "mock_fallback_model",
            },
        }
    )
    # Patch the ConfigParser class to always return our mock_config instance
    with patch("configparser.ConfigParser", return_value=mock_config) as patched_constructor:
        # Also, patch the 'read' method of this specific mock_config instance
        # so that when configuration.py calls config.read(), it doesn't load the real file.
        # The 'read' method normally returns a list of successfully parsed filenames.
        # Assign to _ to indicate it's intentionally unused
        with patch.object(mock_config, "read", return_value=[]) as _:
            import importlib

            # It's crucial that 'configuration' is imported *after* the patches are active
            # and reloaded to pick up the mocked ConfigParser and its mocked 'read'.
            from ..deep_search_persist import configuration

            importlib.reload(configuration)  # Reload to apply mocks at module's top level
            yield patched_constructor  # Fixture needs to yield something


class TestConfigurationLoading:
    """Tests that configuration values are loaded correctly."""

    def test_persistence_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import SESSIONS_DIR, TEMP_PDF_DIR

        assert SESSIONS_DIR == Path("./simple-webui/logs/sessions")  # This is hardcoded
        assert TEMP_PDF_DIR == Path("/mocked/pdf/dir")

    def test_local_ai_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import DEFAULT_MODEL_CTX, OLLAMA_BASE_URL, REASON_MODEL_CTX

        assert OLLAMA_BASE_URL == "http://mock-ollama:11434"
        assert DEFAULT_MODEL_CTX == 4096
        assert REASON_MODEL_CTX == 8192

    def test_api_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import (
            BASE_SEARXNG_URL,
            JINA_API_KEY,
            JINA_BASE_URL,
            OPENAI_COMPAT_API_KEY,
            OPENAI_URL,
        )

        assert OPENAI_COMPAT_API_KEY == "mock_openai_key"
        assert JINA_API_KEY == "mock_jina_key"
        assert OPENAI_URL == "http://mock-openai/v1"
        assert JINA_BASE_URL == "https://mock.jina.ai/"
        assert BASE_SEARXNG_URL == "http://mock-searxng"

    def test_general_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import DEFAULT_MODEL, REASON_MODEL, USE_JINA, USE_OLLAMA, WITH_PLANNING

        assert USE_OLLAMA is True
        assert USE_JINA is False
        assert WITH_PLANNING is True
        assert DEFAULT_MODEL == "mock_default_model"
        assert REASON_MODEL == "mock_reason_model"

    def test_concurrency_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import (
            CHROME_HOST_IP,
            CHROME_PORT,
            USE_EMBED_BROWSER,
            concurrent_limit,
            cool_down,
        )

        assert concurrent_limit == 5
        assert cool_down == 1.0
        assert CHROME_PORT == 9223
        assert CHROME_HOST_IP == "127.0.0.1"
        assert USE_EMBED_BROWSER is True

    def test_parsing_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import (
            BROWSE_LITE,
            MAX_EVAL_TIME,
            MAX_HTML_LENGTH,
            PDF_MAX_FILESIZE,
            PDF_MAX_PAGES,
            TIMEOUT_PDF,
            VERBOSE_WEB_PARSE,
        )

        assert PDF_MAX_PAGES == 10
        assert PDF_MAX_FILESIZE == 5000000
        assert TIMEOUT_PDF == 30
        assert MAX_HTML_LENGTH == 1000000
        assert MAX_EVAL_TIME == 10
        assert VERBOSE_WEB_PARSE is False
        assert BROWSE_LITE == 0

    def test_ratelimit_settings(self, mock_config_parser):
        from ..deep_search_persist.configuration import FALLBACK_MODEL, OPERATION_WAIT_TIME, REQUEST_PER_MINUTE

        assert REQUEST_PER_MINUTE == 60
        assert OPERATION_WAIT_TIME == 0
        assert FALLBACK_MODEL == "mock_fallback_model"

    def test_openrouter_last_request_times_initialization(self, mock_config_parser):
        # This tests the global list defined in configuration.py
        from ..deep_search_persist.configuration import openrouter_last_request_times

        assert openrouter_last_request_times == []
