"""
Unit tests for LLM provider classes and response parsing.
Tests the centralized parsing logic and provider factory.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deep_search_persist.deep_search_persist.llm_providers import (
    LLMProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    LLMProviderFactory,
)
from deep_search_persist.deep_search_persist.helper_classes import Message, Messages


class TestLLMProviderBaseParsing:
    """Test the base LLM provider parsing methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing abstract base class methods
        class ConcreteLLMProvider(LLMProvider):
            async def generate_stream(self, messages, model, max_tokens=20000, ctx=0, **kwargs):
                yield "test"
            
            async def generate(self, messages, model, max_tokens=20000, ctx=0, **kwargs):
                return "test response"
        
        self.provider = ConcreteLLMProvider()

    def test_clean_markdown_response_no_markdown(self):
        """Test cleaning response without markdown blocks."""
        response = '["query1", "query2", "query3"]'
        result = self.provider.clean_markdown_response(response)
        assert result == response

    def test_clean_markdown_response_with_markdown(self):
        """Test cleaning response with markdown code blocks."""
        response = '''```python
["query1", "query2", "query3"]
```'''
        expected = '["query1", "query2", "query3"]'
        result = self.provider.clean_markdown_response(response)
        assert result == expected

    def test_clean_markdown_response_complex_markdown(self):
        """Test cleaning response with complex markdown and extra content."""
        response = '''Here's the result:
```python
[
    "AI research trends", 
    "machine learning advancements",
    "neural network developments"
]
```
This is the output.'''
        result = self.provider.clean_markdown_response(response)
        # Should extract the list content from the markdown block
        assert "[" in result and "]" in result
        assert "AI research trends" in result
        assert "machine learning advancements" in result

    def test_clean_markdown_response_empty(self):
        """Test cleaning empty response."""
        assert self.provider.clean_markdown_response("") == ""

    def test_parse_python_list_valid_list(self):
        """Test parsing valid Python list string."""
        response = '["query1", "query2", "query3"]'
        result = self.provider.parse_python_list(response)
        assert result == ["query1", "query2", "query3"]

    def test_parse_python_list_done_token(self):
        """Test parsing <done> token."""
        response = "<done>"
        result = self.provider.parse_python_list(response)
        assert result == "<done>"

    def test_parse_python_list_with_markdown(self):
        """Test parsing list wrapped in markdown."""
        response = '''```python
["query1", "query2"]
```'''
        result = self.provider.parse_python_list(response)
        assert result == ["query1", "query2"]

    def test_parse_python_list_invalid_syntax(self):
        """Test parsing invalid Python syntax."""
        response = '["query1", "query2"'  # Missing closing bracket
        result = self.provider.parse_python_list(response)
        assert result == []

    def test_parse_python_list_not_a_list(self):
        """Test parsing valid Python but not a list."""
        response = '"just a string"'
        result = self.provider.parse_python_list(response)
        assert result == []

    def test_parse_python_list_empty_response(self):
        """Test parsing empty response."""
        result = self.provider.parse_python_list("")
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_and_parse_list_success(self):
        """Test successful generation and parsing of list."""
        mock_response = '["query1", "query2"]'
        
        # Mock the generate method
        self.provider.generate = AsyncMock(return_value=mock_response)
        
        result = await self.provider.generate_and_parse_list(
            Messages([Message(role="user", content="test")]),
            "test-model"
        )
        
        assert result == ["query1", "query2"]
        self.provider.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_and_parse_list_done_token(self):
        """Test generation returning <done> token."""
        mock_response = "<done>"
        
        # Mock the generate method
        self.provider.generate = AsyncMock(return_value=mock_response)
        
        result = await self.provider.generate_and_parse_list(
            Messages([Message(role="user", content="test")]),
            "test-model"
        )
        
        assert result == "<done>"

    @pytest.mark.asyncio
    async def test_generate_and_parse_list_empty_response(self):
        """Test generation returning empty response."""
        # Mock the generate method
        self.provider.generate = AsyncMock(return_value=None)
        
        result = await self.provider.generate_and_parse_list(
            Messages([Message(role="user", content="test")]),
            "test-model"
        )
        
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_and_parse_list_exception(self):
        """Test generation raising exception."""
        # Mock the generate method to raise exception
        self.provider.generate = AsyncMock(side_effect=Exception("Test error"))
        
        result = await self.provider.generate_and_parse_list(
            Messages([Message(role="user", content="test")]),
            "test-model"
        )
        
        assert result == []


class TestOllamaProvider:
    """Test Ollama provider implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = OllamaProvider("http://localhost:11434")

    def test_init_url_cleaning(self):
        """Test URL cleaning during initialization."""
        # Test with /v1 suffix
        provider = OllamaProvider("http://localhost:11434/v1")
        assert provider.base_url == "http://localhost:11434"
        
        # Test without http prefix
        provider = OllamaProvider("localhost:11434")
        assert provider.base_url == "http://localhost:11434"
        
        # Test clean URL
        provider = OllamaProvider("http://localhost:11434")
        assert provider.base_url == "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        messages = Messages([Message(role="user", content="Hello")])
        
        # Mock the Ollama client
        mock_response = [
            {"message": {"content": "Hello"}},
            {"message": {"content": " world"}},
            {"message": {"content": "!"}}
        ]
        
        with patch.object(self.provider.client, 'chat', new_callable=AsyncMock) as mock_chat:
            async def mock_chat_generator():
                for response in mock_response:
                    yield response
            
            mock_chat.return_value = mock_chat_generator()
            
            result = []
            async for chunk in self.provider.generate_stream(messages, "test-model"):
                result.append(chunk)
            
            assert result == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_generate_complete(self):
        """Test complete generation by collecting stream."""
        messages = Messages([Message(role="user", content="Hello")])
        
        # Mock the generate_stream method
        async def mock_stream():
            yield "Hello"
            yield " world"
            yield "!"
        
        self.provider.generate_stream = AsyncMock(return_value=mock_stream())
        
        result = await self.provider.generate(messages, "test-model")
        assert result == "Hello world!"

    @pytest.mark.asyncio
    async def test_generate_stream_error(self):
        """Test error handling in streaming generation."""
        messages = Messages([Message(role="user", content="Hello")])
        
        with patch.object(self.provider.client, 'chat', side_effect=Exception("Connection error")):
            result = []
            async for chunk in self.provider.generate_stream(messages, "test-model"):
                result.append(chunk)
            
            assert len(result) == 1
            assert "Error: Ollama streaming failed" in result[0]


class TestOpenAICompatibleProvider:
    """Test OpenAI-compatible provider implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = OpenAICompatibleProvider(
            base_url="https://api.openai.com/v1/chat/completions",
            api_key="test-key"
        )

    @pytest.mark.asyncio
    async def test_generate_stream_success(self):
        """Test successful streaming generation."""
        messages = Messages([Message(role="user", content="Hello")])
        
        # Mock response data
        mock_lines = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n',
            b'data: {"choices": [{"delta": {"content": " world"}}]}\n\n',
            b'data: [DONE]\n\n'
        ]
        
        # Create mock session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.__aiter__ = AsyncMock(return_value=iter(mock_lines))
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = []
        async for chunk in self.provider.generate_stream(messages, "test-model", session=mock_session):
            result.append(chunk)
        
        assert result == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_generate_stream_error_response(self):
        """Test handling of error response from API."""
        messages = Messages([Message(role="user", content="Hello")])
        
        # Create mock session and error response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Unauthorized"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = []
        async for chunk in self.provider.generate_stream(messages, "test-model", session=mock_session):
            result.append(chunk)
        
        assert len(result) == 1
        assert "Error: API returned 401" in result[0]

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Mock time and rate limit settings
        with patch('time.time', return_value=1000.0):
            with patch('deep_search_persist.deep_search_persist.configuration.REQUEST_PER_MINUTE', 2):
                with patch('deep_search_persist.deep_search_persist.configuration.DEFAULT_MODEL', "test-model"):
                    # Fill up the rate limit
                    self.provider.last_request_times = [999.0, 999.5]  # Two recent requests
                    
                    # Mock asyncio.sleep to verify it's called
                    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                        await self.provider._apply_rate_limiting("test-model")
                        mock_sleep.assert_called_once()


class TestLLMProviderFactory:
    """Test LLM provider factory functionality."""
    
    def setup_method(self):
        """Clear factory cache before each test."""
        LLMProviderFactory._providers.clear()

    def test_get_ollama_provider(self):
        """Test getting Ollama provider."""
        provider = LLMProviderFactory.get_ollama_provider()
        assert isinstance(provider, OllamaProvider)
        
        # Test singleton behavior
        provider2 = LLMProviderFactory.get_ollama_provider()
        assert provider is provider2

    def test_get_openai_provider(self):
        """Test getting OpenAI-compatible provider."""
        provider = LLMProviderFactory.get_openai_provider()
        assert isinstance(provider, OpenAICompatibleProvider)
        
        # Test singleton behavior
        provider2 = LLMProviderFactory.get_openai_provider()
        assert provider is provider2

    def test_get_provider_unknown_type(self):
        """Test getting unknown provider type."""
        with pytest.raises(ValueError, match="Unknown provider type"):
            LLMProviderFactory.get_provider("unknown_type")

    def test_get_provider_with_kwargs(self):
        """Test getting provider with custom kwargs."""
        provider = LLMProviderFactory.get_provider("ollama", base_url="http://custom:1234")
        assert provider.base_url == "http://custom:1234"