import asyncio
import json
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from deep_search_persist.deep_search_persist.configuration import app_config
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages
from deep_search_persist.deep_search_persist.helper_functions import (
    extract_relevant_context_async,
    generate_final_report_async,
    generate_search_queries_async,
    get_new_search_queries_async,
    is_page_useful_async,
    judge_search_result_and_refine_plan_async,
    make_initial_searching_plan_async,
    perform_search_async,
    process_link,
)
from deep_search_persist.deep_search_persist.local_ai import call_llm_async, call_llm_async_parse_list, fetch_webpage_text_async


# Fixture for an aiohttp client session
@pytest.fixture
async def http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    async with aiohttp.ClientSession() as session:
        yield session


# --- Integration tests for LLM Interaction Helper Functions ---


@pytest.mark.asyncio
async def test_call_llm_async_openrouter_success(http_session):
    """Test call_llm_async with OpenRouter success."""
    messages = Messages([Message(role="user", content="Hello")])
    mock_response_content = "Mocked OpenRouter response."

    with patch(
        "deep_search_persist.deep_search_persist.local_ai.call_openrouter_async", new_callable=AsyncMock
    ) as mock_openrouter:
        mock_openrouter.return_value = mock_response_content
        with patch.object(app_config, 'use_ollama', False):
            response = await call_llm_async(http_session, messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
            assert response == mock_response_content
            mock_openrouter.assert_called_once_with(http_session, messages, model=app_config.default_model)


@pytest.mark.asyncio
async def test_call_llm_async_ollama_success(http_session):
    """Test call_llm_async with Ollama success."""
    messages = Messages([Message(role="user", content="Hello")])
    mock_response_content = "Mocked Ollama response."

    class MockAsyncGenerator:
        def __init__(self, content):
            self.content = content
            self.index = 0

        async def __aiter__(self):
            for char in self.content:
                yield char
                await asyncio.sleep(0.001)  # Simulate async behavior

    with patch(
        "deep_search_persist.deep_search_persist.local_ai.call_ollama_async", new_callable=AsyncMock
    ) as mock_ollama:
        mock_ollama.return_value = MockAsyncGenerator(mock_response_content)
        with patch.object(app_config, 'use_ollama', True):
            response = await call_llm_async(http_session, messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
            assert response == mock_response_content
            mock_ollama.assert_called_once()  # Args are passed to the inner call_ollama_async


@pytest.mark.asyncio
async def test_make_initial_searching_plan_async(http_session):
    """Test make_initial_searching_plan_async."""
    user_message = Message(role="user", content="Research about quantum computing.")
    messages = Messages([user_message])
    mock_plan = "1. Define quantum computing. 2. Explore applications."

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async", new_callable=AsyncMock
    ) as mock_call_llm:
        mock_call_llm.return_value = mock_plan
        plan = await make_initial_searching_plan_async(http_session, messages)
        assert plan == mock_plan
        mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_judge_search_result_and_refine_plan_async(http_session):
    """Test judge_search_result_and_refine_plan_async."""
    user_message = Message(role="user", content="Quantum computing research.")
    messages = Messages([user_message])
    current_plan = "Initial plan."
    all_contexts_str = "Context 1. Context 2."
    mock_next_plan = "Updated research plan with more focus on quantum algorithms."

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async", new_callable=AsyncMock
    ) as mock_call_llm:
        mock_call_llm.return_value = mock_next_plan
        next_plan = await judge_search_result_and_refine_plan_async(
            http_session, messages, current_plan, all_contexts_str
        )
        assert next_plan == mock_next_plan
        mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_generate_search_queries_async(http_session):
    """Test generate_search_queries_async with new centralized parsing."""
    query_plan = "Find recent advancements in AI."
    mock_queries = ["AI advancements 2023", "latest AI research"]

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async_parse_list", new_callable=AsyncMock
    ) as mock_call_llm_parse:
        mock_call_llm_parse.return_value = mock_queries  # Returns parsed list directly
        queries = await generate_search_queries_async(http_session, query_plan)
        assert queries == mock_queries
        mock_call_llm_parse.assert_called_once()


@pytest.mark.asyncio
async def test_generate_final_report_async(http_session):
    """Test generate_final_report_async."""
    user_message = Message(role="user", content="Report on climate change.")
    messages = Messages([user_message])
    report_planning = "Introduction, Causes, Effects, Solutions."
    all_contexts = ["Context A.", "Context B."]
    mock_report = "Final report content."

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async", new_callable=AsyncMock
    ) as mock_call_llm:
        mock_call_llm.return_value = mock_report
        report = await generate_final_report_async(http_session, messages, report_planning, all_contexts)
        assert report == mock_report
        mock_call_llm.assert_called_once()


# --- Integration tests for Web Interaction Helper Functions ---


@pytest.mark.asyncio
async def test_perform_search_async_success(http_session):
    """Test perform_search_async with successful response from SearXNG."""
    query = "test search"
    mock_searxng_response = {
        "results": [
            {"url": "http://link1.com"},
            {"url": "http://link2.com"},
        ]
    }

    with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_searxng_response
        mock_get.return_value.__aenter__.return_value = mock_resp

        links = await perform_search_async(http_session, query)
        assert links == ["http://link1.com", "http://link2.com"]
        mock_get.assert_called_once_with(app_config.base_searxng_url, params={"q": query, "format": "json"})


@pytest.mark.asyncio
async def test_fetch_webpage_text_async_playwright_html(http_session):
    """Test fetch_webpage_text_async with Playwright for HTML content."""
    url = "http://example.com/html"
    mock_title = "Example Page"
    mock_cleaned_html = "<div>Cleaned HTML content</div>"
    mock_markdown_text = "Markdown content"

    with patch.object(app_config, 'use_jina', False):
        with patch("deep_search_persist.deep_search_persist.configuration.USE_EMBED_BROWSER", True):
            with patch("playwright.async_api.async_playwright", new_callable=AsyncMock) as mock_playwright:
                mock_browser = AsyncMock()
                mock_context = AsyncMock()
                mock_page = AsyncMock()

                mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
                mock_browser.new_context.return_value = mock_context
                mock_context.new_page.return_value = mock_page

                mock_page.title.return_value = mock_title
                mock_page.evaluate.return_value = mock_cleaned_html  # For get_cleaned_html

                with patch(
                    "deep_search_persist.deep_search_persist.local_ai.helper_call_llm_async", new_callable=AsyncMock
                ) as mock_call_llm:
                    mock_call_llm.return_value = mock_markdown_text

                    result = await fetch_webpage_text_async(http_session, url)
                    assert result == f"# {mock_title}\n{mock_markdown_text}"
                    mock_page.goto.assert_called_once_with(url, timeout=30000)
                    mock_page.evaluate.assert_called_once()
                    mock_call_llm.assert_called_once()
                    mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_webpage_text_async_jina(http_session):
    """Test fetch_webpage_text_async with Jina."""
    url = "http://example.com/jina"
    mock_jina_response = "Jina fetched content."

    with patch.object(app_config, 'use_jina', True):
        with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.text.return_value = mock_jina_response
            mock_get.return_value.__aenter__.return_value = mock_resp

            result = await fetch_webpage_text_async(http_session, url)
            assert result == mock_jina_response
            mock_get.assert_called_once_with(
                f"{app_config.jina_base_url}{url}", headers={"Authorization": f"Bearer {app_config.jina_api_key}"}
            )


@pytest.mark.asyncio
async def test_is_page_useful_async(http_session: aiohttp.ClientSession):
    """Test is_page_useful_async."""
    user_message = Message(role="user", content="Is this page useful for my query?")
    messages = Messages([user_message])
    page_text = "This page contains useful information."

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async", new_callable=AsyncMock
    ) as mock_call_llm:
        mock_call_llm.return_value = "Yes"
        usefulness = await is_page_useful_async(http_session, messages, page_text)
        assert usefulness == "Yes"
        mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_extract_relevant_context_async(http_session):
    """Test extract_relevant_context_async."""
    user_message = Message(role="user", content="Extract context.")
    messages = Messages([user_message])
    search_query = "context extraction"
    page_text = "This is some text. Relevant context is here. Irrelevant text."
    page_url = "http://example.com/context"
    mock_extracted_context = "Relevant context is here."

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async", new_callable=AsyncMock
    ) as mock_call_llm:
        mock_call_llm.return_value = mock_extracted_context
        context = await extract_relevant_context_async(http_session, messages, search_query, page_text)
        assert context == mock_extracted_context
        mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_get_new_search_queries_async(http_session):
    """Test get_new_search_queries_async with new centralized parsing."""
    user_message = Message(role="user", content="More queries needed?")
    messages = Messages([user_message])
    new_research_plan = "Continue research."
    previous_search_queries = ["old query"]
    all_contexts = ["old context"]
    mock_new_queries = ["new query 1", "new query 2"]

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async_parse_list", new_callable=AsyncMock
    ) as mock_call_llm_parse:
        mock_call_llm_parse.return_value = mock_new_queries  # Returns parsed list directly
        queries = await get_new_search_queries_async(
            http_session, messages, new_research_plan, previous_search_queries, all_contexts
        )
        assert queries == mock_new_queries
        mock_call_llm_parse.assert_called_once()


@pytest.mark.asyncio
async def test_get_new_search_queries_async_done_token(http_session):
    """Test get_new_search_queries_async returning <done> token."""
    user_message = Message(role="user", content="Research complete?")
    messages = Messages([user_message])
    new_research_plan = "Research is complete."
    previous_search_queries = ["old query"]
    all_contexts = ["comprehensive context"]

    with patch(
        "deep_search_persist.deep_search_persist.helper_functions.call_llm_async_parse_list", new_callable=AsyncMock
    ) as mock_call_llm_parse:
        mock_call_llm_parse.return_value = "<done>"  # Returns <done> token
        result = await get_new_search_queries_async(
            http_session, messages, new_research_plan, previous_search_queries, all_contexts
        )
        assert result == "<done>"
        mock_call_llm_parse.assert_called_once()


@pytest.mark.asyncio
async def test_process_link(http_session):
    """Test process_link end-to-end flow."""
    link = "http://example.com/process"
    search_query = "process test"
    user_message = Message(role="user", content="Process this link.")
    messages = Messages([user_message])

    mock_page_text = "<html><body>Useful content.</body></html>"
    mock_usefulness = "Yes"
    mock_extracted_context = "Useful content."

    with patch(
        "deep_search_persist.deep_search_persist.local_ai.fetch_webpage_text_async", new_callable=AsyncMock
    ) as mock_fetch_webpage:
        mock_fetch_webpage.return_value = mock_page_text
        with patch(
            "deep_search_persist.deep_search_persist.helper_functions.is_page_useful_async", new_callable=AsyncMock
        ) as mock_is_useful:
            mock_is_useful.return_value = mock_usefulness
            with patch(
                "deep_search_persist.deep_search_persist.helper_functions.extract_relevant_context_async",
                new_callable=AsyncMock,
            ) as mock_extract_context:
                mock_extract_context.return_value = mock_extracted_context

                chunks = []
                async for chunk in process_link(http_session, link, messages, search_query):
                    chunks.append(chunk)

                # Check for status messages and final context
                assert any(f"Fetching content from: {link}" in c for c in chunks)
                assert any(f"Page usefulness for {link}: {mock_usefulness}" in c for c in chunks)
                assert f"url:{link}\ncontext:{mock_extracted_context}" in chunks

                mock_fetch_webpage.assert_called_once_with(http_session, link)
                mock_is_useful.assert_called_once()
                mock_extract_context.assert_called_once()


# Helper for AsyncMock and AsyncGeneratorMock
class AsyncGeneratorMock:
    def __init__(self, iterable):
        self.iterable = iterable

    async def __aiter__(self):
        for item in self.iterable:
            yield item
