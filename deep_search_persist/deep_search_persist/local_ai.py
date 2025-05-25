import asyncio
from dataclasses import dataclass
import mimetypes
import time
from collections import defaultdict
from typing import Any, AsyncGenerator, DefaultDict, List, Literal, LiteralString, Optional, Union  # Added AsyncGenerator, Union, Optional
from urllib.parse import urlparse

import aiohttp  # Added for type hinting
import anyio  # Added for anyio.sleep
from docling.document_converter import DocumentConverter  # type: ignore
from loguru import logger
from ollama import AsyncClient
from playwright.async_api import async_playwright
from pydantic import BaseModel  # type: ignore

from .configuration import (
    BROWSE_LITE,
    CHROME_HOST_IP,
    CHROME_PORT,
    CONCURRENT_LIMIT,
    COOL_DOWN,
    DEFAULT_MODEL,
    DEFAULT_MODEL_CTX,
    FALLBACK_MODEL,
    JINA_API_KEY,
    JINA_BASE_URL,
    MAX_EVAL_TIME,
    MAX_HTML_LENGTH,
    OLLAMA_BASE_URL,
    OPENAI_COMPAT_API_KEY,
    OPENAI_URL,
    PDF_MAX_FILESIZE,
    PDF_MAX_PAGES,
    REQUEST_PER_MINUTE,
    TEMP_PDF_DIR,
    TIMEOUT_PDF,
    USE_EMBED_BROWSER,
    USE_JINA,
    USE_OLLAMA,
)
from .helper_classes import Message, Messages
from .logging.logging_config import log_operation
from .llm_providers import LLMProviderFactory

# Added for test_call_openrouter_rate_limit
OPERATION_WAIT_TIME = 1

# Global semaphore for concurrency control
global global_semaphore
global_semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
domain_locks: DefaultDict[str, asyncio.Lock] = defaultdict(asyncio.Lock)  # domain -> asyncio.Lock
domain_next_allowed_time: DefaultDict[str, float] = defaultdict(lambda: 0.0)  # domain -> float (epoch time)
openrouter_last_request_times: list = []  # Initialize for rate limiting

# Global lock for PDF processing
pdf_processing_lock = asyncio.Lock()


@dataclass
class OllamaArgs(dict):
    model: str
    max_tokens: int = 0
    ctx: Optional[int] = None
    
    def __repr__(self) -> str:
        return f"<OllamaArgs model={self.model} max_tokens={self.max_tokens} ctx={self.ctx}>"


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
            use_ollama=USE_OLLAMA,
            force_ollama=force_ollama,
            max_tokens=max_tokens,
        )

        if force_ollama or USE_OLLAMA:
            # Use the new Ollama provider
            provider = LLMProviderFactory.get_ollama_provider()
            response = await provider.generate(messages, model, max_tokens, ctx)
            logger.debug(
                "Ollama call completed",
                model=model,
                response_length=len(response) if response else 0,
            )
        elif not USE_OLLAMA and not force_ollama:
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
                use_ollama=USE_OLLAMA,
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
) -> Union[List[str], Literal["<done>"], List]:
    """Call the LLM and parse the response as a Python list."""
    try:
        max_tokens = max_tokens_override if max_tokens_override is not None else 20000
        
        logger.debug(
            "Initiating LLM call for list parsing",
            model=model,
            message_count=len(messages),
            use_ollama=USE_OLLAMA,
            force_ollama=force_ollama,
            max_tokens=max_tokens,
        )

        if force_ollama or USE_OLLAMA:
            # Use the new Ollama provider
            provider = LLMProviderFactory.get_ollama_provider()
            result = await provider.generate_and_parse_list(messages, model, max_tokens, ctx)
            logger.debug(
                "Ollama list parsing completed",
                model=model,
                result_type=type(result).__name__,
                result_length=len(result) if isinstance(result, list) else 1,
            )
        elif not USE_OLLAMA and not force_ollama:
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
                use_ollama=USE_OLLAMA,
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
    model: str = DEFAULT_MODEL,  # Explicitly type model
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
    if model == DEFAULT_MODEL and REQUEST_PER_MINUTE > 0:
        current_time = time.time()
        # Remove requests older than 60 seconds
        openrouter_last_request_times = [t for t in openrouter_last_request_times if current_time - t < 60]

        if len(openrouter_last_request_times) >= REQUEST_PER_MINUTE:
            # Wait until we can make another request
            oldest_time = openrouter_last_request_times[0]
            wait_time = 60 - (current_time - oldest_time)
            if wait_time > 0:
                await anyio.sleep(wait_time)  # Replaced asyncio.sleep

        # Add current request time
        openrouter_last_request_times.append(current_time)

    headers = {
        "Authorization": f"Bearer {OPENAI_COMPAT_API_KEY}",
        "X-Title": "OpenDeepResearcher, by Matt Shumer and Benhao Tang",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages.to_openai_format(),  # Use to_openai_format()
    }
    try:
        async with session.post(OPENAI_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                try:
                    content = result["choices"][0]["message"]["content"]
                    # If content is empty and not using fallback, retry with fallback model
                    if (not content or content.strip() == "") and not is_fallback:
                        print(f"Empty response from model, retrying with fallback model: {FALLBACK_MODEL}")
                        return await call_openrouter_async(session, messages, model=FALLBACK_MODEL, is_fallback=True)
                    return content
                except (KeyError, IndexError) as e:  # Conventional unused variable
                    error_msg = f"Unexpected OpenRouter/OpenAI compatible response structure: {result}"
                    print(error_msg)
                    return f"Error: {e}: {error_msg}"
            else:
                text = await resp.text()
                error_msg = f"OpenRouter/OpenAI compatible API error: {resp.status} - {text}"
                print(error_msg)
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
                    print(f"Rate limit/Context length hit, retrying with fallback model: {FALLBACK_MODEL}")
                    # Retry with fallback model, marking as fallback to prevent recursion
                    return await call_openrouter_async(session, messages, model=FALLBACK_MODEL, is_fallback=True)
                if is_fallback and any(phrase in text.lower() for phrase in rate_limit_phrases):
                    error_msg = (
                        "Rate limit hit/Context length hit even for fallback model, "
                        "consider choosing a model with larger context length as fallback "
                        "or other models/services."
                    )
                return f"Error: {error_msg}"
    except Exception as e:
        print("Error calling OpenRouter/OpenAI compatible API:", e)
        return None


# --------------------------
# Local AI and Browser use
# --------------------------
# Note: Ollama functionality has been moved to llm_providers.py for better extensibility
async def call_ollama_async(
    session: aiohttp.ClientSession,  # Added type hint
    messages: Messages,
    model: str = DEFAULT_MODEL,
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
    base_url = OLLAMA_BASE_URL
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


def is_pdf_url(url):
    parsed_url = urlparse(url)
    if parsed_url.path.lower().endswith(".pdf"):
        return True
    mime_type, _ = mimetypes.guess_type(url)
    return mime_type == "application/pdf"


def get_domain(url):
    parsed = urlparse(url)
    # Use .hostname to exclude port and userinfo, then convert to lower
    # If hostname is None (e.g. for mailto: links or relative paths), return empty string or handle as error
    hostname = parsed.hostname
    return hostname.lower() if hostname else ""


async def process_pdf(pdf_path):
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
        return converter.convert(str(pdf_path), max_num_pages=PDF_MAX_PAGES, max_file_size=PDF_MAX_FILESIZE)

    # Ensure no other async task runs while processing the PDF
    async with pdf_processing_lock:
        try:
            with anyio.fail_after(TIMEOUT_PDF):  # Replaced asyncio.wait_for
                return await docling_task()
        except TimeoutError:  # anyio.fail_after raises TimeoutError (from anyio.exceptions)
            return "Parser unable to parse the resource within defined time."


async def download_pdf(page, url):
    """
    Downloads a PDF from a webpage using Playwright and saves it locally.

    Args:
        page: The Playwright page object.
        url: The URL of the PDF to download.
    Returns:
        The path to the saved PDF file or None if an error occurs.
    """
    pdf_filename = TEMP_PDF_DIR / f"{hash(url)}.pdf"

    async def intercept_request(request):
        """Intercepts request to log PDF download attempts."""
        # Create Session instance
        # TODO: Need to pass session details properly here
        # session_instance = ResearchSession(user_query, system_instruction, settings)
        # session_instance.save_session(SESSIONS_DIR / f"{session_instance.session_id}.json")

        if request.resource_type == "document":
            print(f"Downloading PDF: {request.url}")

    # Attach the request listener
    page.on("request", intercept_request)

    try:
        await page.goto(url, timeout=30000)  # 30 seconds timeout
        await page.wait_for_load_state("networkidle")

        # Attempt to save PDF (works for direct links)
        await page.pdf(path=str(pdf_filename))
        return pdf_filename

    except Exception as e:
        print(f"Error downloading PDF {url}: {e}")
        return None


async def get_cleaned_html(page):
    """
    Extracts cleaned HTML from a page while enforcing a timeout.

    Args:
        page: The Playwright page object.
    Returns:
        The cleaned HTML content or an error message if extraction fails.
    """
    try:
        with anyio.fail_after(MAX_EVAL_TIME):  # Replaced asyncio.wait_for
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


async def fetch_webpage_text_async(session, url):
    """# Added docstring
    Asynchronously fetches the text content of a webpage using Playwright or Jina.
    If the URL is a PDF, it downloads and processes the PDF using Docling.
    If the URL is a webpage, it uses Playwright to fetch the HTML and processes it using Ollama.
    Respects concurrency limits and per-domain cooldown.

    Args:
        session: The aiohttp session object.
        url: The URL of the webpage to fetch.
    Returns:
        The text content of the webpage or an error message string if fetching fails.
    """

    if USE_JINA:
        """
        Asynchronously retrieve the text content of a webpage using Jina.
        The URL is appended to the Jina endpoint.
        """
        full_url = f"{JINA_BASE_URL}{url}"
        headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
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

        async with global_semaphore:  # Global concurrency limit
            async with domain_locks[domain]:  # Ensure only one request per domain at a time
                now = time.time()
                if now < domain_next_allowed_time[domain]:
                    # Replaced asyncio.sleep # Respect per-domain cooldown
                    await anyio.sleep(domain_next_allowed_time[domain] - now)

                async with async_playwright() as p:
                    # Attempt to connect to an already running Chrome instance
                    try:
                        if USE_EMBED_BROWSER:
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
                            browser = await p.chromium.connect_over_cdp(f"{CHROME_HOST_IP}:{CHROME_PORT}")
                    except Exception as e:
                        if USE_EMBED_BROWSER:
                            error_msg = "Failed to launch browser"
                        else:
                            error_msg = f"Failed to connect to Chrome on port {CHROME_PORT}"
                        logger.error(f"Playwright connection error: {error_msg}", error=str(e))
                        return error_msg

                    context = await browser.new_context()
                    page = await context.new_page()

                    # PDFs
                    if is_pdf_url(url):
                        if BROWSE_LITE:
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
                            if BROWSE_LITE:
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
                                cleaned_html = cleaned_html[:MAX_HTML_LENGTH]
                                helper_messages_for_reader = Messages(
                                    messages=[
                                        Message(role="user", content=cleaned_html),
                                    ]
                                )
                                # Don't get stuck when exceed reader-lm ctx
                                ollama_max_tokens = int(1.25 * MAX_HTML_LENGTH)
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
                domain_next_allowed_time[domain] = time.time() + COOL_DOWN

        return result
