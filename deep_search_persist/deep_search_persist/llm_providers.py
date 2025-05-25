"""
LLM Provider Interface and Implementations

This module provides a extensible interface for different LLM inference engines,
making it easy to add support for new providers in the future.
"""
import asyncio
import ast
import json
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List, Union, Literal
import aiohttp
from loguru import logger
from ollama import AsyncClient

from .helper_classes import Messages
from .configuration import (
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    OPENAI_URL,
    OPENAI_COMPAT_API_KEY,
    REQUEST_PER_MINUTE,
    FALLBACK_MODEL,
)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from the LLM."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs
    ) -> Optional[str]:
        """Generate complete response from the LLM."""
        pass
    
    # TODO: This should only be called after streaming is done. Only the completed response can be parsed for Markdown formatting.
    def clean_markdown_response(self, response: str) -> str:
        """
        Clean markdown code blocks from LLM responses.
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Cleaned response with markdown code blocks removed
        """
        if not response:
            return response
            
        cleaned_response = response.strip()
        if cleaned_response.startswith("```"):
            # Remove markdown code blocks
            lines = cleaned_response.split('\n')
            start_idx = 0
            end_idx = len(lines)
            
            # Find start of actual content (skip ```python or ``` line)
            for i, line in enumerate(lines):
                if line.strip().startswith('['):
                    start_idx = i
                    break
            
            # Find end of actual content (before closing ```)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().endswith(']'):
                    end_idx = i + 1
                    break
                elif lines[i].strip() == '```':
                    end_idx = i
                    break
            
            cleaned_response = '\n'.join(lines[start_idx:end_idx]).strip()
        
        return cleaned_response
    
    def parse_python_list(self, response: str) -> Union[List[str], Literal["<done>"], List]:
        """
        Parse a Python list from LLM response, handling markdown code blocks.
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Parsed list, "<done>" token, or empty list on failure
        """
        if not response:
            logger.warning("Empty response received for list parsing")
            return []
        
        cleaned_response = response.strip()
        
        # Check for the special "<done>" token first
        if cleaned_response == "<done>":
            return "<done>"
        
        try:
            # Clean markdown if present
            cleaned_response = self.clean_markdown_response(response)
            
            # Attempt to parse the response as a Python list
            parsed = ast.literal_eval(cleaned_response)
            if isinstance(parsed, list):
                logger.debug("Successfully parsed Python list", count=len(parsed))
                return parsed
            else:
                logger.error("Parsed response is not a list", response_type=type(parsed).__name__, response=response)
                return []
        except (SyntaxError, ValueError) as e:
            logger.exception("Failed to parse Python list from LLM response", error=str(e), response=response, cleaned_response=cleaned_response)
            return []
    
    async def generate_and_parse_list(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs
    ) -> Union[List[str], Literal["<done>"], List]:
        """
        Generate response and parse it as a Python list.
        
        Args:
            messages: Messages to send to the LLM
            model: Model to use
            max_tokens: Maximum tokens to generate
            ctx: Context length
            **kwargs: Additional arguments
            
        Returns:
            Parsed list, "<done>" token, or empty list on failure
        """
        try:
            response = await self.generate(messages, model, max_tokens, ctx, **kwargs)
            if response:
                return self.parse_python_list(response)
            else:
                logger.warning("LLM returned empty response for list generation")
                return []
        except Exception as e:
            logger.exception("Error in generate_and_parse_list", error=str(e))
            return []


class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation."""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        # Clean up the base URL - remove trailing /v1 if present
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        self.base_url = base_url
        self.client = AsyncClient(host=base_url)
        logger.debug("Initialized OllamaProvider", base_url=base_url)
    
    async def generate_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Ollama."""
        try:
            ollama_formatted_messages = messages.to_openai_format()
            options = {"num_predict": max_tokens}
            if ctx > 2000:
                options["num_ctx"] = ctx
            
            logger.debug("Starting Ollama streaming chat", model=model, message_count=len(messages))
            
            # Await the coroutine to get the async iterator
            stream = await self.client.chat(
                model=model,
                messages=ollama_formatted_messages,
                stream=True,
                options=options,
            )
            
            # Now iterate through the async iterator
            async for part in stream:
                if part.get("message") and part["message"].get("content"):
                    content = part["message"]["content"]
                    if content:  # Only yield non-empty content
                        yield content
                        
        except Exception as e:
            logger.exception("Error in Ollama streaming", model=model, error=str(e))
            # Yield an error message to ensure the generator produces something
            yield f"Error: Ollama streaming failed - {str(e)}"
    
    async def generate(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs
    ) -> Optional[str]:
        """Generate complete response from Ollama by collecting stream."""
        try:
            response_parts = []
            async for part in self.generate_stream(messages, model, max_tokens, ctx, **kwargs):
                response_parts.append(part)
            
            response = "".join(response_parts) if response_parts else None
            logger.debug("Ollama complete response", model=model, response_length=len(response) if response else 0)
            return response
            
        except Exception as e:
            logger.exception("Error in Ollama complete generation", model=model, error=str(e))
            return None


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible API provider (OpenRouter, etc.)."""
    
    def __init__(self, base_url: str = OPENAI_URL, api_key: str = OPENAI_COMPAT_API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self.last_request_times: List[float] = []
        logger.debug("Initialized OpenAICompatibleProvider", base_url=base_url)
    
    async def _apply_rate_limiting(self, model: str):
        """Apply rate limiting for the specified model."""
        if model == DEFAULT_MODEL and REQUEST_PER_MINUTE > 0:
            import time
            current_time = time.time()
            
            # Remove requests older than 1 minute
            self.last_request_times = [
                t for t in self.last_request_times 
                if current_time - t < 60
            ]
            
            # Check if we've exceeded the rate limit
            if len(self.last_request_times) >= REQUEST_PER_MINUTE:
                sleep_time = 60 - (current_time - self.last_request_times[0]) + 1
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
            
            # Record this request
            self.last_request_times.append(current_time)
    
    async def generate_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        session: Optional[aiohttp.ClientSession] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from OpenAI-compatible API."""
        if not session:
            raise ValueError("OpenAI-compatible provider requires aiohttp session")
        
        await self._apply_rate_limiting(model)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": model,
                "messages": messages.to_openai_format(),
                "max_tokens": max_tokens,
                "stream": True,
            }
            
            logger.debug("Starting OpenAI-compatible streaming", model=model, message_count=len(messages))
            
            async with session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("OpenAI API error", status=response.status, error=error_text)
                    yield f"Error: API returned {response.status} - {error_text}"
                    return
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: ') and not line_str.endswith('[DONE]'):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.exception("Error in OpenAI-compatible streaming", model=model, error=str(e))
            yield f"Error: OpenAI-compatible streaming failed - {str(e)}"
    
    async def generate(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        session: Optional[aiohttp.ClientSession] = None,
        **kwargs
    ) -> Optional[str]:
        """Generate complete response from OpenAI-compatible API."""
        try:
            response_parts = []
            async for part in self.generate_stream(messages, model, max_tokens, ctx, session=session, **kwargs):
                response_parts.append(part)
            
            response = "".join(response_parts) if response_parts else None
            logger.debug("OpenAI-compatible complete response", model=model, response_length=len(response) if response else 0)
            return response
            
        except Exception as e:
            logger.exception("Error in OpenAI-compatible complete generation", model=model, error=str(e))
            return None


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, LLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_type: str, **kwargs) -> LLMProvider:
        """Get or create a provider instance."""
        if provider_type not in cls._providers:
            if provider_type == "ollama":
                cls._providers[provider_type] = OllamaProvider(**kwargs)
            elif provider_type == "openai_compatible":
                cls._providers[provider_type] = OpenAICompatibleProvider(**kwargs)
            else:
                raise ValueError(f"Unknown provider type: {provider_type}")
        
        return cls._providers[provider_type]
    
    @classmethod
    def get_ollama_provider(cls) -> "OllamaProvider":
        """Convenience method to get Ollama provider."""
        provider = cls.get_provider("ollama")
        if isinstance(provider, OllamaProvider):
            return provider
        raise ValueError("Expected OllamaProvider")
    
    @classmethod
    def get_openai_provider(cls) -> "OpenAICompatibleProvider":
        """Convenience method to get OpenAI-compatible provider."""
        provider = cls.get_provider("openai_compatible")
        if isinstance(provider, OpenAICompatibleProvider):
            return provider
        raise ValueError("Expected OpenAICompatibleProvider")
