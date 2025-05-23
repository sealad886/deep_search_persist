"""
Tests for the local_ai module in the docker/persist service.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..deep_search_persist.configuration import (
    JINA_API_KEY,
    JINA_BASE_URL,
    PDF_MAX_FILESIZE,
    PDF_MAX_PAGES,
    USE_EMBED_BROWSER,
)
from ..deep_search_persist.local_ai import (
    call_ollama_async,
    call_openrouter_async,
    download_pdf,
    fetch_webpage_text_async,
    get_cleaned_html,
    get_domain,
    is_pdf_url,
    process_pdf,
)

# The following imports were previously removed due to Flake8 errors,
# but they are actually used in the file.
# from ..deep_search_persist.configuration import (
# BROWSE_LITE, USE_JINA, REQUEST_PER_MINUTE, TEMP_PDF_DIR
# )


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    mock_session = MagicMock()
    mock_session.post = MagicMock()  # Changed to MagicMock
    mock_session.get = MagicMock()  # Changed to MagicMock
    return mock_session


class TestOpenRouter:
    """Tests for call_openrouter_async."""

    @pytest.mark.anyio
    @pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
    @patch("deep_search_persist.local_ai.OPERATION_WAIT_TIME", 0.01)
    @patch("deep_search_persist.local_ai.REQUEST_PER_MINUTE", 1)  # Limit to 1 req/min for testing
    @patch("time.time")
    @patch("deep_search_persist.local_ai.anyio.sleep")
    async def test_call_openrouter_rate_limit(
        self, mock_anyio_sleep, mock_time_time, mock_aiohttp_session, anyio_backend
    ):
        """Test rate limiting in call_openrouter_async."""
        if anyio_backend == "trio":
            pytest.skip("Mocking of anyio.sleep and time.time for rate limit test is problematic with trio backend")
        # Mock time to control rate limiting
        mock_time_time.side_effect = [100.0, 100.1, 100.2]  # Simulate rapid calls

        # Mock response for the first call
        mock_response_1_obj = AsyncMock()
        mock_response_1_obj.status = 200
        mock_response_1_obj.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response 1"}}]})
        async_cm1 = MagicMock()
        async_cm1.__aenter__ = AsyncMock(return_value=mock_response_1_obj)
        async_cm1.__aexit__ = AsyncMock(return_value=False)

        # Mock response for the second call (should be rate limited)
        mock_response_2_obj = AsyncMock()
        mock_response_2_obj.status = 200
        mock_response_2_obj.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response 2"}}]})
        async_cm2 = MagicMock()
        async_cm2.__aenter__ = AsyncMock(return_value=mock_response_2_obj)
        async_cm2.__aexit__ = AsyncMock(return_value=False)

        mock_aiohttp_session.post.side_effect = [async_cm1, async_cm2]

        # First call should succeed
        response_1 = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response_1 == "Response 1"

        # Second call should be delayed due to rate limiting
        with patch("deep_search_persist.local_ai.anyio.sleep", AsyncMock()) as mock_sleep:  # Patched anyio.sleep
            response_2 = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello again"}])
            assert response_2 == "Response 2"
            mock_sleep.assert_called_once()  # Check that sleep was called

    @pytest.mark.anyio
    async def test_call_openrouter_success(self, mock_aiohttp_session):
        """Test successful call to OpenRouter."""
        mock_response_object = AsyncMock()
        mock_response_object.status = 200
        mock_response_object.json = AsyncMock(return_value={"choices": [{"message": {"content": "Test response"}}]})
        async_cm = MagicMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_response_object)
        async_cm.__aexit__ = AsyncMock(return_value=False)
        mock_aiohttp_session.post.return_value = async_cm

        response = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response == "Test response"

    @pytest.mark.anyio
    async def test_call_openrouter_empty_response_fallback(self, mock_aiohttp_session):
        """Test fallback when OpenRouter returns an empty response."""
        # Mock empty response for initial call
        mock_empty_response_obj = AsyncMock()
        mock_empty_response_obj.status = 200
        mock_empty_response_obj.json = AsyncMock(
            return_value={"choices": [{"message": {"content": ""}}]}  # Empty content
        )
        async_cm_empty = MagicMock()
        async_cm_empty.__aenter__ = AsyncMock(return_value=mock_empty_response_obj)
        async_cm_empty.__aexit__ = AsyncMock(return_value=False)

        # Mock successful response for fallback call
        mock_fallback_response_obj = AsyncMock()
        mock_fallback_response_obj.status = 200
        mock_fallback_response_obj.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "Fallback response"}}]}
        )
        async_cm_fallback = MagicMock()
        async_cm_fallback.__aenter__ = AsyncMock(return_value=mock_fallback_response_obj)
        async_cm_fallback.__aexit__ = AsyncMock(return_value=False)

        # Configure side_effect to return different responses for initial and fallback calls
        mock_aiohttp_session.post.side_effect = [async_cm_empty, async_cm_fallback]

        response = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response == "Fallback response"

    @pytest.mark.anyio
    async def test_call_openrouter_api_error_fallback(self, mock_aiohttp_session):
        """Test fallback when OpenRouter API returns an error."""
        # Mock API error for initial call
        mock_error_response_obj = AsyncMock()
        mock_error_response_obj.status = 429  # Rate limit error
        mock_error_response_obj.text = AsyncMock(return_value="Rate limit exceeded")
        async_cm_error_initial = MagicMock()
        async_cm_error_initial.__aenter__ = AsyncMock(return_value=mock_error_response_obj)
        async_cm_error_initial.__aexit__ = AsyncMock(return_value=False)

        # Mock successful response for fallback call
        mock_fallback_response_obj = AsyncMock()
        mock_fallback_response_obj.status = 200
        mock_fallback_response_obj.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "Fallback response"}}]}
        )
        async_cm_error_fallback = MagicMock()
        async_cm_error_fallback.__aenter__ = AsyncMock(return_value=mock_fallback_response_obj)
        async_cm_error_fallback.__aexit__ = AsyncMock(return_value=False)

        # Configure side_effect
        mock_aiohttp_session.post.side_effect = [
            async_cm_error_initial,
            async_cm_error_fallback,
        ]

        response = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response == "Fallback response"

    @pytest.mark.anyio
    async def test_call_openrouter_exception(self, mock_aiohttp_session):
        """Test exception handling in call_openrouter_async."""
        mock_aiohttp_session.post.side_effect = Exception("Network error")

        response = await call_openrouter_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response is None


class TestOllama:
    """Tests for call_ollama_async."""

    @patch("deep_search_persist.local_ai.AsyncClient")
    @pytest.mark.anyio
    async def test_call_ollama_success(self, MockAsyncClient, mock_aiohttp_session):
        """Test successful call to Ollama."""
        mock_ollama_client = MockAsyncClient.return_value
        mock_ollama_client.chat = AsyncMock(
            return_value=self.async_generator(
                [
                    {"message": {"content": "Test "}},
                    {"message": {"content": "response"}},
                ]
            )
        )

        response = await call_ollama_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response == "Test response"

    @patch("deep_search_persist.local_ai.AsyncClient")
    @pytest.mark.anyio
    async def test_call_ollama_exception(self, MockAsyncClient, mock_aiohttp_session):
        """Test exception handling in call_ollama_async."""
        mock_ollama_client = MockAsyncClient.return_value
        mock_ollama_client.chat.side_effect = Exception("Ollama error")

        response = await call_ollama_async(mock_aiohttp_session, [{"role": "user", "content": "Hello"}])
        assert response is None

    @staticmethod
    async def async_generator(items):
        """Helper to create an async generator for mocking."""
        for item in items:
            yield item


class TestURLHelpers:
    """Tests for URL helper functions."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("http://example.com/document.pdf", True),
            ("http://example.com/document.PDF", True),
            ("http://example.com/image.jpg", False),
            ("http://example.com/no_extension", False),
        ],
    )
    def test_is_pdf_url(self, url, expected):
        """Test is_pdf_url with various URLs."""
        assert is_pdf_url(url) == expected

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("http://example.com/path", "example.com"),
            ("https://www.example.co.uk/path", "www.example.co.uk"),
            ("ftp://user:pass@example.com:21/path", "example.com"),
        ],
    )
    def test_get_domain(self, url, expected):
        """Test get_domain with various URLs."""
        assert get_domain(url) == expected


class TestPDFProcessing:
    """Tests for PDF processing functions."""

    @patch("deep_search_persist.local_ai.DocumentConverter")
    @pytest.mark.anyio
    async def test_process_pdf_success(self, MockDocumentConverter):
        """Test successful PDF processing."""
        mock_converter = MockDocumentConverter.return_value
        mock_converter.convert = MagicMock(return_value="PDF content")

        pdf_path = MagicMock()  # Mock Path object
        result = await process_pdf(pdf_path)

        assert result == "PDF content"
        mock_converter.convert.assert_called_once_with(
            str(pdf_path), max_num_pages=PDF_MAX_PAGES, max_file_size=PDF_MAX_FILESIZE
        )

    @patch("deep_search_persist.local_ai.DocumentConverter")
    @patch("deep_search_persist.local_ai.anyio.fail_after", side_effect=TimeoutError)  # Patched anyio.fail_after
    @pytest.mark.anyio
    async def test_process_pdf_timeout(self, mock_fail_after, MockDocumentConverter):  # Renamed mock_wait_for
        """Test PDF processing timeout."""
        pdf_path = MagicMock()
        result = await process_pdf(pdf_path)

        assert result == "Parser unable to parse the resource within defined time."
        mock_fail_after.assert_called_once()  # Check that fail_after was used

    @patch("deep_search_persist.local_ai.TEMP_PDF_DIR", MagicMock())  # Mock TEMP_PDF_DIR
    @pytest.mark.anyio
    async def test_download_pdf_success(self):
        """Test successful PDF download."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.pdf = AsyncMock()

        url = "http://example.com/document.pdf"
        pdf_path = await download_pdf(mock_page, url)

        assert pdf_path is not None
        mock_page.goto.assert_called_once_with(url, timeout=30000)
        mock_page.pdf.assert_called_once()

    @pytest.mark.anyio
    async def test_download_pdf_error(self):
        """Test PDF download error."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Download error")

        url = "http://example.com/document.pdf"
        pdf_path = await download_pdf(mock_page, url)

        assert pdf_path is None


class TestHTMLProcessing:
    """Tests for HTML processing functions."""

    @pytest.mark.anyio
    async def test_get_cleaned_html_success(self):
        """Test successful HTML cleaning."""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="<body>Cleaned HTML</body>")

        html = await get_cleaned_html(mock_page)
        assert html == "<body>Cleaned HTML</body>"

    @patch("deep_search_persist.local_ai.anyio.fail_after", side_effect=TimeoutError)  # Patched anyio.fail_after
    @pytest.mark.anyio
    async def test_get_cleaned_html_timeout(self, mock_fail_after):  # Renamed mock_wait_for
        """Test HTML cleaning timeout."""
        mock_page = AsyncMock()
        html = await get_cleaned_html(mock_page)

        assert html == "Parser unable to extract HTML within defined time."
        mock_fail_after.assert_called_once()  # Check that fail_after was used


class TestFetchWebpage:
    """Tests for fetch_webpage_text_async."""

    @patch("deep_search_persist.local_ai.USE_JINA", True)
    @pytest.mark.anyio
    async def test_fetch_webpage_jina_success(self, mock_aiohttp_session):
        """Test successful webpage fetch with Jina."""
        mock_response_object = AsyncMock()
        mock_response_object.status = 200
        mock_response_object.text = AsyncMock(return_value="Jina content")

        async_cm = MagicMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_response_object)
        async_cm.__aexit__ = AsyncMock(return_value=False)
        mock_aiohttp_session.get.return_value = async_cm

        url = "http://example.com"
        content = await fetch_webpage_text_async(mock_aiohttp_session, url)

        assert content == "Jina content"
        mock_aiohttp_session.get.assert_called_once_with(
            f"{JINA_BASE_URL}{url}", headers={"Authorization": f"Bearer {JINA_API_KEY}"}
        )

    @patch("deep_search_persist.local_ai.USE_JINA", False)
    @patch("deep_search_persist.local_ai.async_playwright")
    @pytest.mark.anyio
    async def test_fetch_webpage_playwright_html_success(self, mock_async_playwright, mock_aiohttp_session):
        """Test successful HTML webpage fetch with Playwright."""
        # Mock Playwright components
        mock_playwright = mock_async_playwright.return_value.__aenter__.return_value
        mock_browser = (
            mock_playwright.chromium.launch.return_value
            if USE_EMBED_BROWSER
            else mock_playwright.chromium.connect_over_cdp.return_value
        )
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value

        mock_page.goto = AsyncMock()
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.evaluate = AsyncMock(return_value="Main content")  # For BROWSE_LITE

        # Mock get_cleaned_html and call_ollama_async for non-lite mode
        with (
            patch(
                "deep_search_persist.local_ai.get_cleaned_html",
                AsyncMock(return_value="Cleaned HTML"),
            ) as mock_get_cleaned_html,
            patch(
                "deep_search_persist.local_ai.call_ollama_async",
                AsyncMock(return_value="Ollama processed HTML"),
            ) as mock_call_ollama,
        ):

            url = "http://example.com"

            # Test with BROWSE_LITE = True
            with patch("deep_search_persist.local_ai.BROWSE_LITE", True):
                content_lite = await fetch_webpage_text_async(mock_aiohttp_session, url)
                assert content_lite == "# Test Page\nMain content"

            # Test with BROWSE_LITE = False
            with patch("deep_search_persist.local_ai.BROWSE_LITE", False):
                content_full = await fetch_webpage_text_async(mock_aiohttp_session, url)
                assert content_full == "# Test Page\nOllama processed HTML"
                mock_get_cleaned_html.assert_called_once()
                mock_call_ollama.assert_called_once()

    # Add more tests for PDF fetching with Playwright, error handling, concurrency, etc.
