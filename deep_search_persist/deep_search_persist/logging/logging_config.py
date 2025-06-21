"""
Centralized logging configuration for deep_search_persist using loguru.

This module configures a standardized logging setup with:
- Console output for interactive use
- File output with rotation for persistent logs
- Consistent formatting across all log sources
- Support for both synchronous and asynchronous logging contexts

Usage:
    from deep_search_persist.logging.logging_config import logger

    # Regular logging
    logger.info("Processing started")
    logger.debug("Detailed information")

    # Logging with context
    logger.info("User query processed", user_id="123", query="example")

    # Error logging
    try:
        # code that might fail
        pass
    except Exception as e:
        logger.exception(f"Operation failed: {str(e)}")
"""

import asyncio
import inspect
import os
import sys
from datetime import datetime
from functools import wraps  # type: ignore
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union, cast

if sys.version_info >= (3, 10):
    from typing import ParamSpec, overload
else:
    from typing_extensions import ParamSpec, overload

from loguru import logger

# Type variables for return type preservation in decorators
# T = TypeVar("T") # Commented out for overload refactor using R
R = TypeVar("R")
P = ParamSpec("P")

# Clear existing handlers
logger.remove()

# Determine log directory
LOG_DIR = Path(__file__).parents[3] / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Log file path with rotation
LOG_FILE = LOG_DIR / "deep_search.log"

# Configure log format
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Configure logger with console output
logger.configure(
    handlers=[
        # Console handler (INFO level)
        {"sink": sys.stderr, "format": LOG_FORMAT, "level": "INFO"},
        # File handler (DEBUG level, with rotation)
        {
            "sink": str(LOG_FILE),
            "format": LOG_FORMAT,
            "level": "DEBUG",
            "rotation": "10 MB",  # Rotate at 10 MB
            "retention": 5,  # Keep 5 rotated files
            "compression": "zip",  # Compress rotated logs
            "enqueue": True,  # Use a queue for thread-safety
            "backtrace": True,  # Show traceback information
            "diagnose": True,  # Show variables in traceback
        },
    ],
)


# Add context manager for organized transaction logging
class LogContext:
    """Context manager for organizing logs within a logical transaction.

    Args:
        name: Name of the logical transaction or operation
        **kwargs: Additional context fields to include in logs

    Example:
        ```python
        with LogContext("user_registration", user_id="123"):
            # code that registers a user
            pass
        ```
    """

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.context = kwargs

    def __enter__(self):
        logger.info(f"Starting {self.name}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Error in {self.name}: {exc_val}", **self.context)
        else:
            logger.info(f"Completed {self.name}", **self.context)


# Add asynchronous context manager for async operations
class AsyncLogContext:
    """Async context manager for organizing logs within async code.

    Args:
        name: Name of the logical transaction or operation
        **kwargs: Additional context fields to include in logs

    Example:
        ```python
        async with AsyncLogContext("database_query", table="users"):
            # async code that queries database
            pass
        ```
    """

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.context = kwargs

    async def __aenter__(self):
        logger.info(f"Starting async {self.name}", **self.context)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Error in async {self.name}: {exc_val}", **self.context)
        else:
            logger.info(f"Completed async {self.name}", **self.context)


def is_coroutine_function(func: Callable[..., Any]) -> bool:
    """Check if a function is a coroutine function.

    Args:
        func: The function to check

    Returns:
        True if the function is a coroutine function, False otherwise
    """
    return asyncio.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


def log_operation(operation_name: str, level: str = "INFO"):
    """Decorator for logging function operations.

    Automatically detects if the decorated function is asynchronous
    and applies the appropriate logging wrapper.

    Args:
        operation_name: Name of the operation being logged
        level: Log level for the operation (default: INFO)

    Example:
        ```python
        @log_operation("user_search")
        def search_users(query: str):
            # code that searches users
            pass

        @log_operation("database_query", level="DEBUG")
        async def fetch_user(user_id: str):
            # async code that fetches a user
            pass
        ```

    Returns:
        The wrapped function with logging
    """

    @overload
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...

    @overload
    def decorator(func: Callable[P, R]) -> Callable[P, R]: ...

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Extract context info from kwargs if available
            log_context_value = kwargs.pop("log_context", None)
            context: dict[str, Any] = log_context_value if isinstance(log_context_value, dict) else {}
            log_func = getattr(logger, level.lower())

            log_func(f"Starting {operation_name}", **context)
            try:
                typed_sync_func = cast(Callable[P, Any], func)
                result: Any = typed_sync_func(*args, **kwargs)
                log_func(f"Completed {operation_name}", **context)
                return result
            except Exception as e:
                logger.exception(f"Error in {operation_name}: {str(e)}", **context)
                raise

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Extract context info from kwargs if available
            log_context_value = kwargs.pop("log_context", None)
            context: dict[str, Any] = log_context_value if isinstance(log_context_value, dict) else {}
            log_func = getattr(logger, level.lower())

            log_func(f"Starting async {operation_name}", **context)
            try:
                # Explicitly cast func to an async callable type for the type checker
                typed_async_func = cast(Callable[P, Awaitable[Any]], func)
                result: Any = await typed_async_func(*args, **kwargs)
                log_func(f"Completed async {operation_name}", **context)
                return result
            except Exception as e:
                logger.exception(f"Error in async {operation_name}: {str(e)}", **context)
                raise

        # Return appropriate wrapper based on if the function is a coroutine
        if is_coroutine_function(func):
            return async_wrapper
        return wrapper

    return decorator


def init_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_file: Optional[Union[str, Path]] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """Initialize or reinitialize logging with custom settings.

    Args:
        console_level: Log level for console output (default: INFO)
        file_level: Log level for file output (default: DEBUG)
        log_file: Optional custom log file path (default: None, uses default)
        rotation: When to rotate logs (default: 10 MB)
        retention: How long to keep logs (default: 1 week)
    """
    # Clear existing handlers
    logger.remove()

    # Use custom or default log file
    log_file_path = log_file if log_file else LOG_FILE

    # Ensure parent directory exists
    if isinstance(log_file_path, str):
        log_file_path = Path(log_file_path)
    log_file_path.parent.mkdir(exist_ok=True, parents=True)

    # Configure with new settings
    logger.configure(
        handlers=[
            {"sink": sys.stderr, "format": LOG_FORMAT, "level": console_level},
            {
                "sink": str(log_file_path),
                "format": LOG_FORMAT,
                "level": file_level,
                "rotation": rotation,
                "retention": retention,
                "compression": "zip",
                "enqueue": True,
                "backtrace": True,
                "diagnose": True,
            },
        ],
    )

    logger.info(f"Logging initialized - console:{console_level}, file:{file_level}")


# Export needed objects
__all__ = ["logger", "LogContext", "AsyncLogContext", "log_operation", "init_logging"]
