"""
Configuration management for deep_search_persist.
Handles loading and validation of configuration settings from TOML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib
from loguru import logger

from .logging.logging_config import LogContext, log_operation

# Initialize configuration globals
CONFIG_FILE_PATH = (
    Path("/app/config/research.toml")
    if os.getenv("DOCKER_CONTAINER")
    else Path(__file__).resolve().parent.parent / "research.toml"
)
config_data: Dict[str, Dict[str, Any]] = {}


@log_operation("load_config", level="DEBUG")
def load_config() -> None:
    """Load configuration from TOML file."""
    global config_data

    try:
        logger.info("Loading configuration", config_path=str(CONFIG_FILE_PATH))

        if not CONFIG_FILE_PATH.exists():
            logger.warning(
                "Configuration file not found, using defaults",
                config_path=str(CONFIG_FILE_PATH),
            )
            config_data = {}
            return

        with open(CONFIG_FILE_PATH, "rb") as f:
            config_data = tomllib.load(f)
            logger.debug("Configuration loaded successfully", sections=list(config_data.keys()))

    except tomllib.TOMLDecodeError as e:
        logger.exception(
            "Failed to parse TOML configuration",
            config_path=str(CONFIG_FILE_PATH),
            error=str(e),
        )
        config_data = {}
    except Exception as e:
        logger.exception(
            "Unexpected error loading configuration",
            config_path=str(CONFIG_FILE_PATH),
            error=str(e),
        )
        config_data = {}


@log_operation("get_config_value", level="DEBUG")
def get_config_value(section: str, key: str, default: Any = None, value_type: Any = str) -> Any:
    """Get a configuration value with type conversion and validation.

    Args:
        section: Configuration section name
        key: Configuration key name
        default: Default value if key is not found
        value_type: Expected type for the value

    Returns:
        The configuration value converted to the specified type
    """
    # Ensure config is loaded
    if not config_data:
        load_config()

    # Convert string type hints to actual types
    if isinstance(value_type, str):
        try:
            value_type = eval(value_type)
        except Exception as e:
            logger.error("Invalid value_type string", value_type=value_type, error=str(e))
            value_type = str

    # If no type provided, default to str
    if value_type is None:
        value_type = str

    try:
        # Get value from config or use default
        value = config_data.get(section, {}).get(key)

        if value is None and default is None:
            logger.warning("Missing mandatory configuration key", section=section, key=key)
            raise KeyError(f"Mandatory key '{key}' not found in section '{section}'")

        if value is None:
            logger.info(
                "Using default configuration value",
                section=section,
                key=key,
                default=default,
            )
            return default

        # Type conversion
        if value_type == bool and isinstance(value, str):
            result = value.lower() in ("true", "yes", "1", "on")
            logger.debug("Converted string to boolean", value=value, result=result)
            return result
        elif value_type in (int, float, str):
            try:
                result = value_type(value)
                logger.debug(
                    "Converted value to type",
                    value=value,
                    type=value_type.__name__,
                    result=result,
                )
                return result
            except (ValueError, TypeError) as e:
                logger.error(
                    "Type conversion failed",
                    section=section,
                    key=key,
                    value=value,
                    target_type=value_type.__name__,
                    error=str(e),
                )
                return default

        return value

    except Exception as e:
        logger.exception(
            "Error retrieving configuration value",
            section=section,
            key=key,
            error=str(e),
        )
        return default


# Initial configuration load
load_config()

# ---------------------------
# Persistence Settings
# ---------------------------
SESSIONS_DIR = Path(get_config_value("Persistence", "sessions_dir", "./simple-webui/logs/sessions"))
logger.debug("Sessions directory configured", sessions_dir=str(SESSIONS_DIR))

# ---------------------------
# Local AI Settings
# ---------------------------
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    get_config_value("LocalAI", "ollama_base_url", "http://localhost:11434"),
)
DEFAULT_MODEL_CTX = get_config_value("LocalAI", "default_model_ctx", -1, value_type=int)
REASON_MODEL_CTX = get_config_value("LocalAI", "reason_model_ctx", -1, value_type=int)
DEFAULT_MODEL = get_config_value("LocalAI", "default_model", "llama2:latest")
REASON_MODEL = get_config_value("LocalAI", "reason_model", "llama2:latest")

logger.success(
    "Local AI settings configured",
    ollama_url=OLLAMA_BASE_URL,
    default_ctx=DEFAULT_MODEL_CTX,
    reason_ctx=REASON_MODEL_CTX,
    default_model=DEFAULT_MODEL,
    reason_model=REASON_MODEL,
)

# ---------------------------
# API Settings
# ---------------------------
OPENAI_COMPAT_API_KEY = get_config_value("API", "openai_compat_api_key", "YOUR_API_KEY_HERE")
JINA_API_KEY = os.getenv("JINA_API_KEY", get_config_value("API", "jina_api_key", None))
OPENAI_URL = get_config_value("API", "openai_url", "https://api.openai.com/v1")
JINA_BASE_URL = get_config_value("API", "jina_base_url", "https://api.jina.ai/v1/chat/completions")
BASE_SEARXNG_URL = get_config_value("API", "searxng_url", "http://localhost:8080")

logger.success(
    "API endpoints configured",
    openai_url=OPENAI_URL,
    jina_url=JINA_BASE_URL,
    searxng_url=BASE_SEARXNG_URL,
)

# ---------------------------
# General Settings
# ---------------------------
USE_OLLAMA = get_config_value("Settings", "use_ollama", True, value_type=bool)
USE_JINA = get_config_value("Settings", "use_jina", False, value_type=bool)
WITH_PLANNING = get_config_value("Settings", "with_planning", True, value_type=bool)

logger.success(
    "General settings configured",
    use_ollama=USE_OLLAMA,
    use_jina=USE_JINA,
    with_planning=WITH_PLANNING,
)

# -------------------------------
# Concurrency Settings
# -------------------------------
CONCURRENT_LIMIT = get_config_value("Concurrency", "concurrent_limit", 3, value_type=int)
COOL_DOWN = get_config_value("Concurrency", "cool_down", 1.0, value_type=float)
CHROME_PORT = get_config_value("Concurrency", "chrome_port", 9222, value_type=int)  # Using correct parameter name
CHROME_HOST_IP = get_config_value("Concurrency", "chrome_host_ip", "127.0.0.1")
USE_EMBED_BROWSER = get_config_value("Concurrency", "use_embed_browser", True, value_type=bool)

logger.success(
    "Concurrency settings configured",
    concurrent_limit=CONCURRENT_LIMIT,
    cool_down=COOL_DOWN,
    chrome_port=CHROME_PORT,
    chrome_host=CHROME_HOST_IP,
    use_embed_browser=USE_EMBED_BROWSER,
)

# ---------------------
# Parsing Settings
# ---------------------
PDF_MAX_PAGES = get_config_value("Parsing", "pdf_max_pages", 10, value_type=int)
PDF_MAX_FILESIZE = get_config_value(
    "Parsing", "pdf_max_filesize", 10 * 1024 * 1024, value_type=int
)  # 10MB default filesize limit
TIMEOUT_PDF = get_config_value("Parsing", "timeout_pdf", 60, value_type=int)  # 60 seconds default timeout
MAX_HTML_LENGTH = get_config_value("Parsing", "max_html_length", 1000000, value_type=int)  # 1 million characters limit
MAX_EVAL_TIME = get_config_value("Parsing", "max_eval_time", 30, value_type=int)  # 30 seconds maximum evaluation time
VERBOSE_WEB_PARSE = get_config_value("Parsing", "verbose_web_parse", False, value_type=bool)
BROWSE_LITE = get_config_value("Parsing", "browse_lite", 1, value_type=int)  # 0 for full parsing, 1 for lite parsing

logger.success(
    "Parsing settings configured",
    pdf_max_pages=PDF_MAX_PAGES,
    pdf_max_filesize=PDF_MAX_FILESIZE,
    timeout_pdf=TIMEOUT_PDF,
    max_html_length=MAX_HTML_LENGTH,
    max_eval_time=MAX_EVAL_TIME,
    verbose_parse=VERBOSE_WEB_PARSE,
    browse_lite=BROWSE_LITE,
)

# Set up temporary PDF directory
TEMP_PDF_DIR = Path(get_config_value("Parsing", "temp_pdf_dir", "./temp_pdfs"))
if not TEMP_PDF_DIR.exists():
    TEMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Created temporary PDF directory", path=str(TEMP_PDF_DIR))


# ----------------------
# Rate Limit Settings
# ----------------------
REQUEST_PER_MINUTE = get_config_value(
    "Ratelimits", "request_per_minute", -1, value_type=int
)  # -1 means no rate limiting
OPERATION_WAIT_TIME = get_config_value("Ratelimits", "operation_wait_time", 0, value_type=int)  # 0 means no wait time
FALLBACK_MODEL = get_config_value(
    "Ratelimits", "fallback_model", DEFAULT_MODEL
)  # Use default model if no fallback specified

logger.success(
    "Rate limit settings configured",
    requests_per_minute=REQUEST_PER_MINUTE,
    wait_time=OPERATION_WAIT_TIME,
    fallback_model=FALLBACK_MODEL,
)

# Rate limiting for OpenRouter/OpenAI compatible API
openrouter_last_request_times: list[float] = []

logger.success("Configuration module initialized successfully")
