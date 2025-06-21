"""
Configuration management for deep_search_persist.
Handles loading and validation of configuration settings from TOML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Literal

try:
    import tomllib
except ImportError:
    # For Python versions < 3.11, use the tomli library
    import tomli as tomllib
from loguru import logger

from dataclasses import dataclass, field
# from .logging.logging_config import log_operation # Temporarily removed for log_operation

@dataclass
class AppConfig:
    # Configurable paths and settings
    config_file_path: Path = field(init=True)
    sessions_dir: Path = field(init=False)
    ollama_base_url: str = field(init=False)
    default_model_ctx: int = field(init=False)
    reason_model_ctx: int = field(init=False)
    default_model: str = field(init=False)
    reason_model: str = field(init=False)
    openai_compat_api_key: str = field(init=False)
    jina_api_key: Optional[str] = field(init=False)
    openai_url: str = field(init=False)
    lmstudio_base_url: str = field(init=False)
    lmstudio_api_key: Optional[str] = field(init=False)
    jina_base_url: str = field(init=False)
    base_searxng_url: str = field(init=False)
    llm_provider: Literal["ollama", "lmstudio", "openai_compatible"] = field(init=False)
    use_jina: bool = field(init=False)
    with_planning: bool = field(init=False)

    # Concurrency Settings
    concurrent_limit: int = field(init=False)
    cool_down: float = field(init=False)
    chrome_port: int = field(init=False)
    chrome_host_ip: str = field(init=False)
    use_embed_browser: bool = field(init=False)

    # Parsing Settings
    pdf_max_pages: int = field(init=False)
    pdf_max_filesize: int = field(init=False)
    timeout_pdf: int = field(init=False)
    max_html_length: int = field(init=False)
    max_eval_time: int = field(init=False)
    verbose_web_parse: bool = field(init=False)
    browse_lite: int = field(init=False) # 0 for full parsing, 1 for lite parsing

    # Search Settings
    search_max_results: int = field(init=False)
    search_max_tokens_per_page: int = field(init=False)
    search_max_tokens_total: int = field(init=False)
    search_max_char_per_page: int = field(init=False)
    search_max_char_total: int = field(init=False)

    # Summarization Settings
    summarize_max_tokens: int = field(init=False)
    summarize_max_chunks: int = field(init=False)

    # Logging Settings
    log_level: str = field(init=False)
    log_rotation: str = field(init=False)
    log_retention: str = field(init=False)
    log_format: str = field(init=False)

    # Rate Limit Settings
    request_per_minute: int = field(init=False)
    operation_wait_time: int = field(init=False)
    fallback_model_config: str = field(init=False)

    # Temp PDF Directory
    temp_pdf_dir: Path = field(init=False)

    # Internal state for loaded configuration data
    _config_data: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        self.config_file_path = (
            Path("/app/config/research.toml")
            if os.getenv("DOCKER_CONTAINER")
            else Path(__file__).resolve().parent.parent / "research.toml"
        )
        self._load_config()

        # Persistence Settings
        self.sessions_dir = Path(self._get_config_value("Persistence", "sessions_dir", "./simple-webui/logs/sessions"))
        logger.debug("Sessions directory configured", sessions_dir=str(self.sessions_dir))

        # Local AI Settings
        self.ollama_base_url = os.getenv(
            "OLLAMA_BASE_URL",
            self._get_config_value("LocalAI", "ollama_base_url", "http://localhost:11434"),
        )
        self.default_model_ctx = self._get_config_value("LocalAI", "default_model_ctx", -1, value_type=int)
        self.reason_model_ctx = self._get_config_value("LocalAI", "reason_model_ctx", -1, value_type=int)
        self.default_model = self._get_config_value("LocalAI", "default_model", "llama2:latest")
        self.reason_model = self._get_config_value("LocalAI", "reason_model", "llama2:latest")
        logger.success(
            "Local AI settings configured",
            ollama_url=self.ollama_base_url,
            default_ctx=self.default_model_ctx,
            reason_ctx=self.reason_model_ctx,
            default_model=self.default_model,
            reason_model=self.reason_model,
        )

        # API Settings
        self.openai_compat_api_key = self._get_config_value("API", "openai_compat_api_key", "YOUR_API_KEY_HERE")
        self.jina_api_key = os.getenv("JINA_API_KEY", self._get_config_value("API", "jina_api_key", ""))
        self.openai_url = self._get_config_value("API", "openai_url", "https://api.openai.com/v1")
        self.lmstudio_base_url = self._get_config_value("API", "lmstudio_base_url", "http://localhost:1234/v1/chat/completions")
        self.lmstudio_api_key = os.getenv("LMSTUDIO_API_KEY", self._get_config_value("API", "lmstudio_api_key", ""))
        self.jina_base_url = self._get_config_value("API", "jina_base_url", "https://api.jina.ai/v1/chat/completions")
        self.base_searxng_url = self._get_config_value("API", "searxng_url", "http://localhost:8080")
        logger.success(
            "API endpoints configured",
            openai_url=self.openai_url,
            lmstudio_url=self.lmstudio_base_url,
            jina_url=self.jina_base_url,
            searxng_url=self.base_searxng_url,
        )

        # General Settings
        self.llm_provider = self._get_config_value("Settings", "llm_provider", "ollama", value_type=str)
        self.use_jina = self._get_config_value("Settings", "use_jina", False, value_type=bool)
        self.with_planning = self._get_config_value("Settings", "with_planning", True, value_type=bool)
        
        # Validate llm_provider value
        valid_providers = ["ollama", "lmstudio", "openai_compatible"]
        if self.llm_provider not in valid_providers:
            logger.warning(f"Invalid llm_provider '{self.llm_provider}', defaulting to 'ollama'")
            self.llm_provider = "ollama"
        
        logger.success(
            "General settings configured",
            llm_provider=self.llm_provider,
            use_jina=self.use_jina,
            with_planning=self.with_planning,
        )

        # Concurrency Settings
        self.concurrent_limit = self._get_config_value("Concurrency", "concurrent_limit", 3, value_type=int)
        self.cool_down = self._get_config_value("Concurrency", "cool_down", 1.0, value_type=float)
        self.chrome_port = self._get_config_value("Concurrency", "chrome_port", 9222, value_type=int)
        self.chrome_host_ip = self._get_config_value("Concurrency", "chrome_host_ip", "127.0.0.1")
        self.use_embed_browser = self._get_config_value("Concurrency", "use_embed_browser", True, value_type=bool)
        logger.success(
            "Concurrency settings configured",
            concurrent_limit=self.concurrent_limit,
            cool_down=self.cool_down,
            chrome_port=self.chrome_port,
            chrome_host=self.chrome_host_ip,
            use_embed_browser=self.use_embed_browser,
        )

        # Parsing Settings
        self.pdf_max_pages = self._get_config_value("Parsing", "pdf_max_pages", 10, value_type=int)
        self.pdf_max_filesize = self._get_config_value("Parsing", "pdf_max_filesize", 10 * 1024 * 1024, value_type=int)
        self.timeout_pdf = self._get_config_value("Parsing", "timeout_pdf", 60, value_type=int)
        self.max_html_length = self._get_config_value("Parsing", "max_html_length", 1000000, value_type=int)
        self.max_eval_time = self._get_config_value("Parsing", "max_eval_time", 30, value_type=int)
        self.verbose_web_parse = self._get_config_value("Parsing", "verbose_web_parse", False, value_type=bool)
        self.browse_lite = self._get_config_value("Parsing", "browse_lite", 1, value_type=int)
        logger.success(
            "Parsing settings configured",
            pdf_max_pages=self.pdf_max_pages,
            pdf_max_filesize=self.pdf_max_filesize,
            timeout_pdf=self.timeout_pdf,
            max_html_length=self.max_html_length,
            max_eval_time=self.max_eval_time,
            verbose_web_parse=self.verbose_web_parse,
            browse_lite=self.browse_lite,
        )

        # Search Settings
        self.search_max_results = self._get_config_value("Search", "max_results", 5, value_type=int)
        self.search_max_tokens_per_page = self._get_config_value("Search", "max_tokens_per_page", 1000, value_type=int)
        self.search_max_tokens_total = self._get_config_value("Search", "max_tokens_total", 4000, value_type=int)
        self.search_max_char_per_page = self._get_config_value("Search", "max_char_per_page", 4000, value_type=int)
        self.search_max_char_total = self._get_config_value("Search", "max_char_total", 16000, value_type=int)
        logger.success(
            "Search settings configured",
            max_results=self.search_max_results,
            max_tokens_per_page=self.search_max_tokens_per_page,
            max_tokens_total=self.search_max_tokens_total,
            max_char_per_page=self.search_max_char_per_page,
            max_char_total=self.search_max_char_total,
        )

        # Summarization Settings
        self.summarize_max_tokens = self._get_config_value("Summarization", "max_tokens", 1000, value_type=int)
        self.summarize_max_chunks = self._get_config_value("Summarization", "max_chunks", 5, value_type=int)
        logger.success(
            "Summarization settings configured",
            max_tokens=self.summarize_max_tokens,
            max_chunks=self.summarize_max_chunks,
        )

        # Logging Settings
        self.log_level = self._get_config_value("Logging", "level", "INFO")
        self.log_rotation = self._get_config_value("Logging", "rotation", "10 MB")
        self.log_retention = self._get_config_value("Logging", "retention", "5 days")
        self.log_format = self._get_config_value(
            "Logging",
            "format",
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )
        logger.success(
            "Logging settings configured",
            level=self.log_level,
            rotation=self.log_rotation,
            retention=self.log_retention,
        )
        # Environment Settings - Placeholder for future use
        # Example: self.api_key = self._get_config_value("Environment", "api_key", "your_default_api_key")
        # logger.success("Environment settings configured")

        # Rate Limit Settings
        self.request_per_minute = self._get_config_value("Ratelimits", "request_per_minute", -1, value_type=int)
        self.operation_wait_time = self._get_config_value("Ratelimits", "operation_wait_time", 0, value_type=int)
        self.fallback_model_config = self._get_config_value("Ratelimits", "fallback_model", self.default_model) # Uses default_model from LocalAI as fallback's default
        logger.success(
            "Rate limit settings configured",
            requests_per_minute=self.request_per_minute,
            wait_time=self.operation_wait_time,
            fallback_model=self.fallback_model_config,
        )

        # Temp PDF Directory
        self.temp_pdf_dir = Path(self._get_config_value("Parsing", "temp_pdf_dir", "./temp_pdfs"))
        logger.success("Temporary PDF directory configured", temp_pdf_dir=str(self.temp_pdf_dir))

    # @log_operation("_load_config", level="DEBUG") # Temporarily removed
    def _load_config(self) -> None:
        """Load configuration from TOML file into self._config_data."""
        if os.getenv("PYTEST_CURRENT_TEST"):
            logger.info("Pytest environment detected: Skipping TOML file load. AppConfig will use defaults and environment variables.")
            self._config_data = {}
            return

        try:
            logger.info("Loading configuration", config_path=str(self.config_file_path))
            if not self.config_file_path.exists():
                logger.warning(
                    "Configuration file not found, using defaults",
                    config_path=str(self.config_file_path),
                )
                self._config_data = {}
                return

            with open(self.config_file_path, "rb") as f:
                self._config_data = tomllib.load(f)
                logger.debug("Configuration loaded successfully", sections=list(self._config_data.keys()))

        except tomllib.TOMLDecodeError as e:
            logger.exception(
                "Failed to parse TOML configuration",
                config_path=str(self.config_file_path),
                error=str(e),
            )
            self._config_data = {}
        except Exception as e:
            logger.exception(
                "Unexpected error loading configuration",
                config_path=str(self.config_file_path),
                error=str(e),
            )
            self._config_data = {}

    # @log_operation("_get_config_value", level="DEBUG") # Temporarily removed
    def _get_config_value(self, section: str, key: str, default: Any = None, value_type: Any = str) -> Any:
        """Get a configuration value from self._config_data with type conversion and validation."""
        actual_value_type = str
        if isinstance(value_type, str):
            try:
                actual_value_type = eval(value_type)
            except Exception as e:
                logger.error("Invalid value_type string for eval", value_type_str=value_type, error=str(e))
                actual_value_type = str
        elif value_type is not None:
            actual_value_type = value_type

        try:
            value = self._config_data.get(section, {}).get(key)

            if value is None and default is None:
                logger.warning("Missing mandatory configuration key", section=section, key=key)
                raise KeyError(f"Mandatory key '{key}' not found in section '{section}' and no default provided.")

            if value is None:
                logger.info("Using default configuration value", section=section, key=key, default=default)
                return default

            if actual_value_type == bool and isinstance(value, str):
                result = value.lower() in ("true", "yes", "1", "on")
                logger.debug("Converted string to boolean", value=value, result=result)
                return result
            elif actual_value_type in (int, float, str):
                try:
                    result = actual_value_type(value)
                    logger.debug("Converted value to type", value=value, type=actual_value_type.__name__, result=result)
                    return result
                except (ValueError, TypeError) as e:
                    logger.error("Type conversion failed, using default", section=section, key=key, value=value, target_type=actual_value_type.__name__, error=str(e))
                    return default

            logger.debug("Returning value as is (no specific conversion applied)", value=value, type=type(value).__name__)
            return value

        except Exception as e:
            logger.exception("Error retrieving configuration value, using default", section=section, key=key, error=str(e))
            return default

# Create a single, globally accessible instance to be imported by other modules
app_config = AppConfig(Path("./research.toml"))

# Set up temporary PDF directory
TEMP_PDF_DIR = Path(app_config._get_config_value("Parsing", "temp_pdf_dir", "./temp_pdfs"))
if not TEMP_PDF_DIR.exists():
    TEMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Created temporary PDF directory", path=str(TEMP_PDF_DIR))

logger.success("Configuration module initialized successfully")
