from __future__ import annotations

import asyncio
import mimetypes
import sys
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union, Literal, List
from urllib.parse import urlparse

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override  # type: ignore[no-redef]

from docling.datamodel.document import ConversionResult

# Type variable for generic return types
T = TypeVar('T')

# Type checking imports
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from playwright.async_api import Page, Download

import aiohttp  # Added for type hinting
import anyio  # Added for anyio.sleep
from docling.document_converter import DocumentConverter  # type: ignore
from loguru import logger
from ollama import AsyncClient
from playwright.async_api import async_playwright
from pydantic import BaseModel  # type: ignore

from .configuration import app_config
from .helper_classes import Message, Messages
from .logging.logging_config import log_operation
from .llm_providers import LLMProviderFactory

# Added for test_call_openrouter_rate_limit
OPERATION_WAIT_TIME = 1

# Global semaphore for concurrency control
global_semaphore: Optional[asyncio.Semaphore] = None

def get_global_semaphore() -> asyncio.Semaphore:
    """Initializes and returns the global semaphore."""
    global global_semaphore
    if global_semaphore is None:
        logger.debug("Initializing global_semaphore", concurrent_limit=app_config.concurrent_limit)
        global_semaphore = asyncio.Semaphore(app_config.concurrent_limit)
    assert global_semaphore is not None, "Global semaphore should be initialized here"
    return global_semaphore

# Domain-based rate limiting
domain_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)  # domain -> asyncio.Lock
domain_next_allowed_time: dict[str, float] = defaultdict(float)  # domain -> float (epoch time)
openrouter_last_request_times: list[float] = []  # Track request times for rate limiting

# Global lock for PDF processing
pdf_processing_lock = asyncio.Lock()


@dataclass
class OllamaArgs:
    """Configuration for Ollama API requests.

    Attributes:
        model: The model to use for the request.
        max_tokens: Maximum number of tokens to generate (0 for no limit).
        ctx: Context window size in tokens (None for default).
    """
    model: str
    max_tokens: int = 0
    ctx: int | None = None

    @override  # type: ignore[misc, unused-ignore]
    def __repr__(self) -> str:
        """Return a string representation of the OllamaArgs instance."""
        return f"<OllamaArgs model={self.model!r} max_tokens={self.max_tokens} ctx={self.ctx}>"




# ----------------------
# LLM Call Routing
@log_operation("llm_call", level="DEBUG")
async def call_llm_async(
    session: aiohttp.ClientSession,
    messages: Messages,
    model: str,
    ctx: int,
    max_tokens_override: Optional[int] = None,
    force_ollama: bool = False,
) -> Union[str, None]:
    """Call the LLM with the provided messages and return the response."""
    try:
        max_tokens = max_tokens_override if max_tokens_override is not None else 20000

        logger.debug(
            "Initiating LLM call",
            model=model,
            message_count=len(messages),
            llm_provider=app_config.llm_provider,
            force_ollama=force_ollama,
            max_tokens=max_tokens,
        )

        if force_ollama or app_config.llm_provider == "ollama":
            # Use the Ollama provider
            provider = LLMProviderFactory.get_ollama_provider()
            response = await provider.generate(messages, model, max_tokens, ctx)
            logger.debug(
                "Ollama call completed",
                model=model,
                response_length=len(response) if response else 0,
            )
        elif app_config.llm_provider == "lmstudio":
            # Use the LMStudio provider
            provider = LLMProviderFactory.get_lmstudio_provider()
            response = await provider.generate(messages, model, max_tokens, ctx, session=session)
            logger.debug(
                "LMStudio call completed",
                model=model,
                response_length=len(response) if response else 0,
            )
        elif app_config.llm_provider == "openai_compatible":
            # Use the OpenAI-compatible provider
            provider = LLMProviderFactory.get_openai_provider()
            response = await provider.generate(messages, model, max_tokens, ctx, session=session)
            logger.debug(
                "OpenAI-compatible call completed",
                model=model,
                response_length=len(response) if response else 0,
            )
        else:
            logger.error(
                "LLM call routing error",
                llm_provider=app_config.llm_provider,
                force_ollama=force_ollama,
                model=model,
            )
            return None

        return response
    except Exception as e:
        logger.exception("LLM call failed", model=model, error=str(e))
        return None


@log_operation("llm_call_parse_list", level="DEBUG")
async def call_llm_async_parse_list(
    session: aiohttp.ClientSession,
    messages: Messages,
    model: str,
    ctx: int,
    max_tokens_override: Optional[int] = None,
    force_ollama: bool = False,
) -> Union[List[str], Literal["<done>"], List[Any]]:
    """Call the LLM and parse the response as a Python list."""
    try:
        max_tokens = max_tokens_override if max_tokens_override is not None else 20000

        logger.debug(
            "Initiating LLM call for list parsing",
            model=model,
            message_count=len(messages),
            llm_provider=app_config.llm_provider,
            force_ollama=force_ollama,
            max_tokens=max_tokens,
        )

        if force_ollama or app_config.llm_provider == "ollama":
            # Use the Ollama provider
            provider = LLMProviderFactory.get_ollama_provider()
            result = await provider.generate_and_parse_list(messages, model, max_tokens, ctx, session=session)
            logger.debug(
                "Ollama list parsing completed",
                model=model,
                result_type=type(result).__name__,
                result_length=len(result) if isinstance(result, list) else 1,
            )
        elif app_config.llm_provider == "lmstudio":
            # Use the LMStudio provider
            provider = LLMProviderFactory.get_lmstudio_provider()
            result = await provider.generate_and_parse_list(messages, model, max_tokens, ctx, session=session)
            logger.debug(
                "LMStudio list parsing completed",
                model=model,
                result_type=type(result).__name__,
                result_length=len(result) if isinstance(result, list) else 1,
            )
        elif app_config.llm_provider == "openai_compatible":
            # Use the OpenAI-compatible provider
            provider = LLMProviderFactory.get_openai_provider()
            result = await provider.generate_and_parse_list(messages, model, max_tokens, ctx, session=session)
            logger.debug(
                "OpenAI-compatible list parsing completed",
                model=model,
                result_type=type(result).__name__,
                result_length=len(result) if isinstance(result, list) else 1,
            )
        else:
            logger.error(
                "LLM call routing error",
                llm_provider=app_config.llm_provider,
                force_ollama=force_ollama,
                model=model,
            )
            return []

        return result
    except Exception as e:
        logger.exception("LLM list parsing call failed", model=model, error=str(e))
        return []


# ----------------------
# Openrouter
async def call_openrouter_async(
    session: aiohttp.ClientSession,  # Added type hint
    messages: Messages,
    model: str = app_config.default_model,  # Explicitly type model
    is_fallback: bool = False,  # Explicitly type is_fallback
) -> Optional[str]:  # Added return type hint
    """
    Asynchronously call the OpenRouter/OpenAI compatible chat completion API with the provided messages.
    Returns the content of the assistant’s reply.

    Args:
        session: The session object to use for the request.
        messages: Messages object containing the messages to send to the model.
        model: The model to use for the request (default is DEFAULT_MODEL).
        is_fallback: Boolean indicating if this is a fallback request (default is False).
    Returns:
        The content of the assistant's reply or an error message.
    """
    global openrouter_last_request_times
    # Apply rate limiting only for DEFAULT_MODEL and when REQUEST_PER_MINUTE is set
    if model == app_config.default_model and app_config.request_per_minute > 0:
        current_time = time.time()
        # Remove requests older than 60 seconds
        openrouter_last_request_times = [t for t in openrouter_last_request_times if current_time - t < 60]

        if len(openrouter_last_request_times) >= app_config.request_per_minute:
            # Wait until we can make another request
            oldest_time = openrouter_last_request_times[0]
            wait_time = 60 - (current_time - oldest_time)
            if wait_time > 0:
                await anyio.sleep(wait_time)  # Replaced asyncio.sleep

        # Add current request time
        openrouter_last_request_times.append(current_time)

    headers = {
        "Authorization": f"Bearer {app_config.openai_compat_api_key}",
        "X-Title": "OpenDeepResearcher, by Matt Shumer and Benhao Tang",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages.to_openai_format(),  # Use to_openai_format()
    }
    try:
        async with session.post(app_config.openai_url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                try:
                    content = result["choices"][0]["message"]["content"]
                    # If content is empty and not using fallback, retry with fallback model
                    if (not content or content.strip() == "") and not is_fallback:
                        logger.warning(f"Empty response from model, retrying with fallback model: {app_config.fallback_model_config}")
                        return await call_openrouter_async(session, messages, model=app_config.fallback_model_config, is_fallback=True)
                    return content
                except (KeyError, IndexError) as e:  # Conventional unused variable
                    error_msg = f"Unexpected OpenRouter/OpenAI compatible response structure: {result}"
                    logger.error(error_msg)
                    return f"Error: {e}: {error_msg}"
            else:
                text = await resp.text()
                error_msg = f"OpenRouter/OpenAI compatible API error: {resp.status} - {text}"
                logger.error(error_msg)
                # Check if this is a rate limit error and we're using the default model and not already a fallback
                rate_limit_phrases = [
                    "rate limit",
                    "rate limits",
                    "ratelimit",
                    "rate_limit",
                    "rate-limit",
                    "context length",
                    "context-length",
                    "max tokens",
                    "max_tokens",
                ]
                if not is_fallback and any(phrase in text.lower() for phrase in rate_limit_phrases):
                    logger.warning(f"Rate limit/Context length hit, retrying with fallback model: {app_config.fallback_model_config}")
                    # Retry with fallback model, marking as fallback to prevent recursion
                    return await call_openrouter_async(session, messages, model=app_config.fallback_model_config, is_fallback=True)
                if is_fallback and any(phrase in text.lower() for phrase in rate_limit_phrases):
                    error_msg = (
                        "Rate limit hit/Context length hit even for fallback model, "
                        "consider choosing a model with larger context length as fallback "
                        "or other models/services."
                    )
                    logger.error(error_msg)
                return f"Error: {error_msg}"
    except Exception as e:
        logger.exception("Error calling OpenRouter/OpenAI compatible API")
        return None


# --------------------------
# Local AI and Browser use
# --------------------------
# Note: Ollama functionality has been moved to llm_providers.py for better extensibility
async def call_ollama_async(
    messages: Messages,
    model: str = app_config.default_model,
    max_tokens: int = 20000,
    ctx: int = 0,
) -> AsyncGenerator[str, None]:  # Added return type hint
    """
    Asynchronously call the Ollama chat completion API with the provided messages.
    Returns the content of the assistant’s reply.

    Args:
        session (): The session object to use for the request.
        messages: Messages object containing the messages to send to the model.
        model: The model to use for the request (default is DEFAULT_MODEL).
        max_tokens: The maximum number of tokens to generate (default is 20000).
        ctx: The context length (default is -1, which means no limit).
    Returns:
        The content of the assistant's reply or an error message.
    """

    # Ensure OLLAMA_BASE_URL is a valid URL (with scheme, and NO trailing /v1)
    base_url = app_config.ollama_base_url
    # Remove trailing /v1 if present (Ollama expects just host:port)
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    client = AsyncClient(host=base_url)
    try:
        ollama_formatted_messages = messages.to_openai_format()
        options = {"num_predict": max_tokens}
        if ctx > 2000:
            options["num_ctx"] = ctx

        # client.chat returns an AsyncIterator[ChatResponse]
        # We need to iterate through it and yield the content of each message part
        async for part in await client.chat(
            model=model,
            messages=ollama_formatted_messages,
            stream=True,
            options=options,
        ):
            if part.get("message") and part["message"].get("content"):
                yield part["message"]["content"]
    except Exception as e:
        logger.exception(
            f"Error calling Ollama API",
            base_url=str(client._client.base_url),
            error=str(e),
        )
        # Ensure the generator still completes if an error occurs before any yield
        # If an error occurs during streaming, it will be raised and handled by the caller.


def is_pdf_url(url: str) -> bool:
    """Check if the given URL points to a PDF file.

    Args:
        url: The URL to check.

    Returns:
        bool: True if the URL points to a PDF, False otherwise.
    """
    parsed_url = urlparse(url)
    if parsed_url.path.lower().endswith(".pdf"):
        return True
    mime_type, _ = mimetypes.guess_type(url)
    return mime_type == "application/pdf"


def get_domain(url: str) -> str:
    """Extract the domain from a URL.

    Args:
        url: The URL to extract the domain from.

    Returns:
        str: The lowercase domain name or an empty string if no domain found.
    """
    parsed = urlparse(url)
    # Use .hostname to exclude port and userinfo, then convert to lower
    # If hostname is None (e.g. for mailto: links or relative paths), return empty string
    hostname = parsed.hostname
    return hostname.lower() if hostname else ""


async def process_pdf(pdf_path: Path | str) -> Union[ConversionResult, str]:
    """
    Converts a local PDF file to text using Docling.
    Ensures only one PDF processing task runs at a time to prevent GPU OutOfMemoryError.

    Args:
        pdf_path: The path to the PDF file to process.
    Returns:
        The text content of the PDF or an error message if processing fails.
    """
    converter = DocumentConverter()

    async def docling_task():
        return converter.convert(str(pdf_path), max_num_pages=app_config.pdf_max_pages, max_file_size=app_config.pdf_max_filesize)

    # Ensure no other async task runs while processing the PDF
    async with pdf_processing_lock:
        try:
            with anyio.fail_after(app_config.timeout_pdf):  # Replaced asyncio.wait_for
                return await docling_task()
        except TimeoutError:  # anyio.fail_after raises TimeoutError (from anyio.exceptions)
            return "Parser unable to parse the resource within defined time."


async def download_pdf(page: 'Page', url: str) -> Optional[Path]:
    """
    Downloads a PDF from a webpage using Playwright and saves it locally.

    Args:
        page: The Playwright page object.
        url: The URL of the PDF to download.

    Returns:
        Optional[Path]: The path to the saved PDF file or None if an error occurs.

    Raises:
        TimeoutError: If the download takes longer than the specified timeout.
        Exception: For any other errors that occur during the download.
    """
    try:
        async with page.expect_download(timeout=30000) as download_info:  # 30 second timeout
            logger.info(f"Downloading PDF: {url}")
            _ = await page.goto(url, timeout=30000)  # 30 second timeout
            download = await download_info.value
            # Create a unique filename for the downloaded file
            filename = f"downloaded_{int(time.time())}.pdf"
            filepath = Path("/tmp") / filename
            await download.save_as(filepath)
            return filepath
    except TimeoutError as te:
        logger.error(f"Timeout while downloading PDF {url}: {te}")
        return None
    except Exception as e:
        logger.error(f"Error downloading PDF {url}: {e}")
        return None


async def get_cleaned_html(page: 'Page') -> str:
    """Extract and clean HTML content from a Playwright page.

    This function extracts the HTML content from a Playwright page, removes unnecessary
    elements (scripts, styles, etc.), and returns a cleaned version of the HTML.
    The operation is wrapped in a timeout to prevent hanging.

    Args:
        page: The Playwright page object to extract HTML from.

    Returns:
        str: The cleaned HTML content as a string, or an error message if extraction fails.

    Raises:
        TimeoutError: If the HTML extraction takes longer than MAX_EVAL_TIME.
        Exception: For any other errors that occur during HTML extraction.
    """
    try:
        with anyio.fail_after(app_config.max_eval_time):  # Replaced asyncio.wait_for
            cleaned_html = await page.evaluate(
                """
                () => {
                    let clone = document.cloneNode(true);

                    // Remove script, style, and noscript elements
                    clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());

                    // Optionally remove navigation and footer
                    clone.querySelectorAll('nav, footer, aside').forEach(el => el.remove());

                    return clone.body.innerHTML;
                }
            """
            )
        return cleaned_html
    except TimeoutError:  # anyio.fail_after raises TimeoutError (from anyio.exceptions)
        return "Parser unable to extract HTML within defined time."


async def fetch_webpage_text_async(session: aiohttp.ClientSession, url: str) -> str:
    """Asynchronously fetch and process web content from a given URL.

    This function handles different types of web content:
    - PDF files: Downloads and processes using Docling
    - Web pages: Fetches HTML and processes using Playwright and Ollama
    - Respects concurrency limits and domain cooldowns

    The function first checks if Jina is enabled (USE_JINA) and uses it for fetching.
    If Jina is not enabled or fails, it falls back to Playwright.

    Args:
        session: An aiohttp ClientSession for making HTTP requests.
        url: The URL of the webpage or PDF to fetch.

    Returns:
        str: The extracted text content of the webpage/PDF, or an error message
             if the fetch/processing fails.

    Raises:
        asyncio.TimeoutError: If any operation exceeds the maximum allowed time.
        aiohttp.ClientError: For HTTP request related errors.
        Exception: For any other unexpected errors during processing.
    """

    if app_config.use_jina:
        """
        Asynchronously retrieve the text content of a webpage using Jina.
        The URL is appended to the Jina endpoint.
        """
        full_url = f"{app_config.jina_base_url}{url}"
        headers = {"Authorization": f"Bearer {app_config.jina_api_key}"}
        try:
            async with session.get(full_url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    text = await resp.text()
                    logger.error(
                        f"Jina fetch error",
                        url=url,
                        status=resp.status,
                        response_text=text,
                    )
                    return f"Error: Jina fetch failed for {url} with status {resp.status}"
        except Exception as e:
            logger.exception("Error fetching webpage text with Jina", url=url, error=str(e))
            return f"Error: Exception while fetching with Jina for {url}: {str(e)}"
    else:
        """
        Fetches webpage HTML using Playwright, processes it using Ollama reader-lm:1.5b,
        or downloads and processes a PDF using Docling.
        Respects concurrency limits and per-domain cooldown.
        """
        domain = get_domain(url)

        async with get_global_semaphore():  # Global concurrency limit
            async with domain_locks[domain]:  # Ensure only one request per domain at a time
                now = time.time()
                if now < domain_next_allowed_time[domain]:
                    # Replaced asyncio.sleep # Respect per-domain cooldown
                    await anyio.sleep(domain_next_allowed_time[domain] - now)

                async with async_playwright() as p:
                    # Attempt to connect to an already running Chrome instance
                    try:
                        if app_config.use_embed_browser:
                            user_agent = (
                                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                            )
                            browser = await p.chromium.launch(
                                headless=True,
                                args=["--no-sandbox", "--disable-setuid-sandbox"],
                                firefox_user_prefs={"general.useragent.override": user_agent},
                            )
                        else:
                            browser = await p.chromium.connect_over_cdp(f"{app_config.chrome_host_ip}:{app_config.chrome_port}")
                    except Exception as e:
                        if app_config.use_embed_browser:
                            error_msg = "Failed to launch browser"
                        else:
                            error_msg = f"Failed to connect to Chrome on port {app_config.chrome_port}"
                        logger.error(f"Playwright connection error: {error_msg}", error=str(e))
                        return error_msg

                    context = await browser.new_context()
                    page = await context.new_page()

                    # PDFs
                    if is_pdf_url(url):
                        if app_config.browse_lite:
                            result = "PDF parsing is disabled in lite browsing mode."
                        else:
                            pdf_path = await download_pdf(page, url)
                            if pdf_path:
                                text = await process_pdf(pdf_path)
                                result = f"# PDF Content\n{text}"
                                # TODO: Need to pass session details properly here
                                # session_instance.aggregated_data['last_plan'] = plan
                                # session_instance.save_session(SESSIONS_DIR / f"{session_instance.session_id}.json")

                            else:
                                result = "Failed to download or process PDF"
                    else:
                        try:
                            await page.goto(url, timeout=30000)  # 30 seconds timeout to wait for loading
                            title = await page.title() or "Untitled Page"
                            if app_config.browse_lite:
                                # Extract main content using JavaScript inside Playwright
                                main_content = await page.evaluate(
                                    """
                                    () => {
                                        let mainEl = document.querySelector('main') || document.body;
                                        return mainEl.innerText.trim();
                                    }
                                """
                                )
                                result = f"# {title}\n{main_content}"
                            else:
                                # Clean HTML before sending to reader-lm
                                cleaned_html = await get_cleaned_html(page)
                                # Enforce a Maximum length for a webpage
                                cleaned_html = cleaned_html[:app_config.max_html_length]
                                helper_messages_for_reader = Messages(
                                    messages=[
                                        Message(role="user", content=cleaned_html),
                                    ]
                                )
                                # Don't get stuck when exceed reader-lm ctx
                                ollama_max_tokens = int(1.25 * app_config.max_html_length)
                                # Use the enhanced call_llm_async
                                markdown_text = await call_llm_async(
                                    session=session,
                                    messages=helper_messages_for_reader,
                                    model="reader-lm:0.5b",
                                    ctx=0,  # Explicitly set ctx for reader-lm
                                    max_tokens_override=ollama_max_tokens,
                                    force_ollama=True,  # Ensure this uses Ollama
                                )
                                result = f"# {title}\n{markdown_text if markdown_text else ''}"

                        except Exception as e:
                            logger.exception(
                                f"Error fetching or processing webpage content",
                                url=url,
                                error=str(e),
                            )
                            result = f"Failed to fetch {url}"

                    await browser.close()

                # Update next allowed time for this domain (cool down time per domain)
                domain_next_allowed_time[domain] = time.time() + app_config.cool_down

        return result
