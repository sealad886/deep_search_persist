"""
Unit tests for local_ai module functions.
Tests the new call_llm_async_parse_list function and routing logic.
"""
import pytest
from unittest.mock import AsyncMock, patch

from deep_search_persist.deep_search_persist.local_ai import (
    call_llm_async,
    call_llm_async_parse_list,
)
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages


class TestCallLLMAsyncParseList:
    """Test the new call_llm_async_parse_list function."""

    @pytest.fixture
    async def http_session(self):
        """Mock HTTP session."""
        return AsyncMock()

    @pytest.fixture
    def messages(self):
        """Test messages."""
        return Messages([Message(role="user", content="Generate search queries")])

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_ollama_success(self, http_session, messages):
        """Test successful parsing with Ollama provider."""
        expected_queries = ["query1", "query2", "query3"]
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", True):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.return_value = expected_queries
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == expected_queries
                mock_provider.generate_and_parse_list.assert_called_once_with(
                    messages, "test-model", 20000, 4000
                )

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_openai_success(self, http_session, messages):
        """Test successful parsing with OpenAI-compatible provider."""
        expected_queries = ["query1", "query2"]
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", False):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_openai_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.return_value = expected_queries
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == expected_queries
                mock_provider.generate_and_parse_list.assert_called_once_with(
                    messages, "test-model", 20000, 4000, session=http_session
                )

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_done_token(self, http_session, messages):
        """Test parsing returning <done> token."""
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", True):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.return_value = "<done>"
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == "<done>"

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_force_ollama(self, http_session, messages):
        """Test forcing Ollama provider regardless of configuration."""
        expected_queries = ["forced_query"]
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", False):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.return_value = expected_queries
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000, force_ollama=True
                )
                
                assert result == expected_queries
                mock_provider.generate_and_parse_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_max_tokens_override(self, http_session, messages):
        """Test max_tokens override parameter."""
        custom_max_tokens = 5000
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", True):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.return_value = []
                mock_factory.return_value = mock_provider
                
                await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000, 
                    max_tokens_override=custom_max_tokens
                )
                
                mock_provider.generate_and_parse_list.assert_called_once_with(
                    messages, "test-model", custom_max_tokens, 4000
                )

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_exception_handling(self, http_session, messages):
        """Test exception handling returns empty list."""
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", True):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate_and_parse_list.side_effect = Exception("Test error")
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async_parse_list(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == []

    @pytest.mark.asyncio
    async def test_call_llm_async_parse_list_routing_error(self, http_session, messages):
        """Test routing configuration error."""
        # Set invalid configuration state
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", False):
            result = await call_llm_async_parse_list(
                http_session, messages, "test-model", 4000, force_ollama=False
            )
            
            # Should return empty list when routing fails
            assert result == []


class TestCallLLMAsyncCompatibility:
    """Test that the original call_llm_async still works correctly."""

    @pytest.fixture
    async def http_session(self):
        """Mock HTTP session."""
        return AsyncMock()

    @pytest.fixture
    def messages(self):
        """Test messages."""
        return Messages([Message(role="user", content="Hello world")])

    @pytest.mark.asyncio
    async def test_call_llm_async_ollama_unchanged(self, http_session, messages):
        """Test that original call_llm_async function works unchanged."""
        expected_response = "Hello! How can I help you today?"
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", True):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_ollama_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate.return_value = expected_response
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == expected_response
                mock_provider.generate.assert_called_once_with(
                    messages, "test-model", 20000, 4000
                )

    @pytest.mark.asyncio
    async def test_call_llm_async_openai_unchanged(self, http_session, messages):
        """Test that original call_llm_async works with OpenAI provider."""
        expected_response = "OpenAI response"
        
        with patch("deep_search_persist.deep_search_persist.configuration.USE_OLLAMA", False):
            with patch(
                "deep_search_persist.deep_search_persist.local_ai.LLMProviderFactory.get_openai_provider"
            ) as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.generate.return_value = expected_response
                mock_factory.return_value = mock_provider
                
                result = await call_llm_async(
                    http_session, messages, "test-model", 4000
                )
                
                assert result == expected_response
                mock_provider.generate.assert_called_once_with(
                    messages, "test-model", 20000, 4000, session=http_session
                )