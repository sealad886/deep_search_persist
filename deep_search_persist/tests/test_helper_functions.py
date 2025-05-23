"""
Tests for the helper_functions module in the docker/persist service.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..deep_search_persist.configuration import BASE_SEARXNG_URL
from ..deep_search_persist.helper_functions import (
    extract_relevant_context_async,
    generate_final_report_async,
    generate_search_queries_async,
    generate_writing_plan_aync,
    get_new_search_queries_async,
    is_page_useful_async,
    judge_search_result_and_future_plan_aync,
    make_initial_searching_plan_async,
    perform_search_async,
    process_link,
)


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    mock_session = MagicMock()
    mock_session.post = MagicMock()  # Changed to MagicMock
    mock_session.get = MagicMock()  # Changed to MagicMock
    return mock_session


class TestAsyncHelperFunctions:
    """Tests for asynchronous helper functions."""

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_make_initial_searching_plan_async(
        self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session
    ):
        """Test make_initial_searching_plan_async."""
        mock_call_ollama.return_value = "Ollama plan <think>thought</think>"
        mock_call_openrouter.return_value = "OpenRouter plan <think>thought</think>"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            plan_ollama = await make_initial_searching_plan_async(mock_aiohttp_session, "user query")
            assert plan_ollama == "Ollama plan"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            plan_openrouter = await make_initial_searching_plan_async(mock_aiohttp_session, "user query")
            assert plan_openrouter == "OpenRouter plan"
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_judge_search_result_and_future_plan_aync(
        self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session
    ):
        """Test judge_search_result_and_future_plan_aync."""
        mock_call_ollama.return_value = "Ollama next plan <think>thought</think>"
        mock_call_openrouter.return_value = "OpenRouter next plan <think>thought</think>"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            plan_ollama = await judge_search_result_and_future_plan_aync(
                mock_aiohttp_session, "user query", "original plan", "context"
            )
            assert plan_ollama == "Ollama next plan"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            plan_openrouter = await judge_search_result_and_future_plan_aync(
                mock_aiohttp_session, "user query", "original plan", "context"
            )
            assert plan_openrouter == "OpenRouter next plan"
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_generate_writing_plan_aync(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test generate_writing_plan_aync."""
        mock_call_ollama.return_value = "Ollama writing plan <think>thought</think>"
        mock_call_openrouter.return_value = "OpenRouter writing plan <think>thought</think>"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            plan_ollama = await generate_writing_plan_aync(mock_aiohttp_session, "user query", "aggregated_contexts")
            assert plan_ollama == "Ollama writing plan"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            plan_openrouter = await generate_writing_plan_aync(
                mock_aiohttp_session, "user query", "aggregated_contexts"
            )
            assert plan_openrouter == "OpenRouter writing plan"
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_generate_search_queries_async(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test generate_search_queries_async."""
        mock_call_ollama.return_value = "['ollama_query1', 'ollama_query2']"
        mock_call_openrouter.return_value = "['openrouter_query1', 'openrouter_query2']"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            queries_ollama = await generate_search_queries_async(mock_aiohttp_session, "query plan")
            assert queries_ollama == ["ollama_query1", "ollama_query2"]
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            queries_openrouter = await generate_search_queries_async(mock_aiohttp_session, "query plan")
            assert queries_openrouter == ["openrouter_query1", "openrouter_query2"]
            mock_call_openrouter.assert_called_once()

    @pytest.mark.anyio
    async def test_perform_search_async_success(self, mock_aiohttp_session):
        """Test successful perform_search_async."""
        # Configure the mock for 'async with session.get(...) as resp:'
        mock_response_object = AsyncMock()
        mock_response_object.status = 200
        mock_response_object.json = AsyncMock(
            return_value={
                "results": [
                    {"url": "http://example.com/1"},
                    {"url": "http://example.com/2"},
                ]
            }
        )

        # mock_context_manager = AsyncMock() # Old approach
        # mock_context_manager.__aenter__.return_value = mock_response_object
        # mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        # mock_aiohttp_session.get.return_value = mock_context_manager

        # New approach: session.get() returns an object that is an async context manager
        # The object itself can be a MagicMock, but its __aenter__ and __aexit__ must be async def methods.
        async_cm = MagicMock()

        # Define async methods for __aenter__ and __aexit__
        async def mock_aenter(
            self_cm,
        ):  # __aenter__ should accept 'self' (the cm instance)
            return mock_response_object

        async def mock_aexit(*args):
            return False

        async_cm.__aenter__ = mock_aenter
        async_cm.__aexit__ = mock_aexit

        mock_aiohttp_session.get.return_value = async_cm

        links = await perform_search_async(mock_aiohttp_session, "search query")
        assert links == ["http://example.com/1", "http://example.com/2"]
        mock_aiohttp_session.get.assert_called_once_with(
            BASE_SEARXNG_URL, params={"q": "search query", "format": "json"}
        )

    @pytest.mark.anyio
    async def test_perform_search_async_error(self, mock_aiohttp_session):
        """Test error handling in perform_search_async."""
        mock_response_object = AsyncMock()
        mock_response_object.status = 500
        mock_response_object.text = AsyncMock(return_value="Server error")
        # Ensure json() doesn't raise an error if called unexpectedly after a text() call
        mock_response_object.json = AsyncMock(side_effect=Exception("json called after text"))

        # New approach: session.get() returns an object that is an async context manager
        # The object itself can be a MagicMock, but its __aenter__ and __aexit__ must be async def methods.
        async_cm_error = MagicMock()

        # Define async methods for __aenter__ and __aexit__
        async def mock_aenter_error(
            self_cm,
        ):  # __aenter__ should accept 'self' (the cm instance)
            return mock_response_object

        async def mock_aexit_error(*args):
            return False

        async_cm_error.__aenter__ = mock_aenter_error
        async_cm_error.__aexit__ = mock_aexit_error

        mock_aiohttp_session.get.return_value = async_cm_error

        links = await perform_search_async(mock_aiohttp_session, "search query")
        assert links == []

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_is_page_useful_async(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test is_page_useful_async."""
        mock_call_ollama.return_value = "Yes"
        mock_call_openrouter.return_value = "No"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            useful_ollama = await is_page_useful_async(mock_aiohttp_session, "user query", "page text", "page_url")
            assert useful_ollama == "Yes"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            useful_openrouter = await is_page_useful_async(mock_aiohttp_session, "user query", "page text", "page_url")
            assert useful_openrouter == "No"
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_extract_relevant_context_async(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test extract_relevant_context_async."""
        mock_call_ollama.return_value = "Ollama context"
        mock_call_openrouter.return_value = "OpenRouter context"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            context_ollama = await extract_relevant_context_async(
                mock_aiohttp_session,
                "user query",
                "search_query",
                "page text",
                "page_url",
            )
            assert context_ollama == "Ollama context"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            context_openrouter = await extract_relevant_context_async(
                mock_aiohttp_session,
                "user query",
                "search_query",
                "page text",
                "page_url",
            )
            assert context_openrouter == "OpenRouter context"
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_get_new_search_queries_async(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test get_new_search_queries_async."""
        mock_call_ollama.return_value = "['ollama_new_query']"
        mock_call_openrouter.return_value = "<done>"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            queries_ollama = await get_new_search_queries_async(
                mock_aiohttp_session, "user query", "plan", ["prev_query"], ["context"]
            )
            assert queries_ollama == ["ollama_new_query"]
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            queries_openrouter = await get_new_search_queries_async(
                mock_aiohttp_session, "user query", "plan", ["prev_query"], ["context"]
            )
            assert queries_openrouter == "<done>"  # This case needs to be handled by the caller
            mock_call_openrouter.assert_called_once()

    @patch("deep_search_persist.helper_functions.call_ollama_async")
    @patch("deep_search_persist.helper_functions.call_openrouter_async")
    @pytest.mark.anyio
    async def test_generate_final_report_async(self, mock_call_openrouter, mock_call_ollama, mock_aiohttp_session):
        """Test generate_final_report_async."""
        mock_call_ollama.return_value = "Ollama final report"
        mock_call_openrouter.return_value = "OpenRouter final report"

        # Test with Ollama
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", True):
            report_ollama = await generate_final_report_async(
                mock_aiohttp_session,
                "system_instruction",
                "user_query",
                "report_planning",
                ["context"],
            )
            assert report_ollama == "Ollama final report"
            mock_call_ollama.assert_called_once()

        # Test with OpenRouter
        with patch("deep_search_persist.helper_functions.USE_OLLAMA", False):
            report_openrouter = await generate_final_report_async(
                mock_aiohttp_session,
                "system_instruction",
                "user_query",
                "report_planning",
                ["context"],
            )
            assert report_openrouter == "OpenRouter final report"
            mock_call_openrouter.assert_called_once()

    @patch(
        "deep_search_persist.helper_functions.fetch_webpage_text_async",
        new_callable=AsyncMock,
    )
    @patch(
        "deep_search_persist.helper_functions.is_page_useful_async",
        new_callable=AsyncMock,
    )
    @patch(
        "deep_search_persist.helper_functions.extract_relevant_context_async",
        new_callable=AsyncMock,
    )
    @pytest.mark.anyio
    @pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
    async def test_process_link_useful(
        self,
        mock_extract_context,
        mock_is_page_useful,
        mock_fetch_webpage,
        mock_aiohttp_session,
        anyio_backend,
    ):
        if anyio_backend == "trio":
            pytest.skip("aiohttp (used by fetch_webpage_text_async) is incompatible with the trio event loop")
        """Test process_link when the page is useful."""
        mock_fetch_webpage.return_value = "Page content"
        mock_is_page_useful.return_value = "Yes"
        mock_extract_context.return_value = "Relevant context"

        results = []
        async for result in process_link(mock_aiohttp_session, "http://example.com", "user_query", "search_query"):
            results.append(result)

        assert len(results) == 1
        assert results[0] == "url:http://example.com\ncontext:Relevant context"
        mock_fetch_webpage.assert_called_once()
        mock_is_page_useful.assert_called_once()
        mock_extract_context.assert_called_once()

    @patch(
        "deep_search_persist.helper_functions.fetch_webpage_text_async",
        new_callable=AsyncMock,
    )
    @patch(
        "deep_search_persist.helper_functions.is_page_useful_async",
        new_callable=AsyncMock,
    )
    @patch(
        "deep_search_persist.helper_functions.extract_relevant_context_async",
        new_callable=AsyncMock,
    )
    @pytest.mark.anyio
    @pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
    async def test_process_link_not_useful(
        self,
        mock_extract_context,
        mock_is_page_useful,
        mock_fetch_webpage,
        mock_aiohttp_session,
        anyio_backend,
    ):
        if anyio_backend == "trio":
            pytest.skip("aiohttp (used by fetch_webpage_text_async) is incompatible with the trio event loop")
        """Test process_link when the page is not useful."""
        mock_fetch_webpage.return_value = "Page content"
        mock_is_page_useful.return_value = "No"

        results = []
        async for result in process_link(mock_aiohttp_session, "http://example.com", "user_query", "search_query"):
            results.append(result)

        assert len(results) == 0  # No context should be yielded
        mock_fetch_webpage.assert_called_once()
        mock_is_page_useful.assert_called_once()
        mock_extract_context.assert_not_called()  # Should not be called if page is not useful
