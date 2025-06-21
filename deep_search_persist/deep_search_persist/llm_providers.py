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
from typing_extensions import override
import aiohttp
from loguru import logger
from ollama import AsyncClient

from .helper_classes import Messages
from .configuration import app_config


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs: Any
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

    def parse_python_list(self, response: str) -> Union[List[str], Literal["<done>"], List[Any]]:
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
        **kwargs: Any
    ) -> Union[List[str], Literal["<done>"], List[Any]]:
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
    base_url: str
    client: AsyncClient

    def __init__(self, base_url: str = app_config.ollama_base_url):
        # Clean up the base URL - remove trailing /v1 if present
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        self.base_url = base_url
        self.client = AsyncClient(host=base_url)
        logger.debug("Initialized OllamaProvider", base_url=base_url)

    async def _create_ollama_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int,
        ctx: int,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        try:
            ollama_formatted_messages = messages.to_openai_format()
            options = {"num_predict": max_tokens}
            if ctx > 2000:
                options["num_ctx"] = ctx

            logger.debug("Starting Ollama streaming chat", model=model, message_count=len(messages))

            stream = await self.client.chat(
                model=model,
                messages=ollama_formatted_messages,
                stream=True,
                options=options,
                **kwargs
            )

            async for part in stream:
                if part and isinstance(part, dict):
                    if part.get("message") and isinstance(part["message"], dict) and "content" in part["message"]:
                        content = part["message"]["content"]
                        if content and isinstance(content, str):
                            yield content

        except Exception as e:
            logger.exception("Error in Ollama streaming", model=model, error=str(e))
            yield f"Error: Ollama streaming failed - {str(e)}"

    @override
    def generate_stream(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from Ollama.

        Args:
            messages: The messages to send to the LLM
            model: The model to use for generation
            max_tokens: Maximum number of tokens to generate
            ctx: Context length
            **kwargs: Additional arguments to pass to the LLM

        Yields:
            str: Chunks of the generated response (when the returned coroutine is awaited and iterated)
        """
        return self._create_ollama_stream(messages, model, max_tokens, ctx, **kwargs)

    @override
    async def generate(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        **kwargs: Any
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

    def __init__(self, base_url: str = app_config.openai_url, api_key: str = app_config.openai_compat_api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.last_request_times: List[float] = []
        logger.debug("Initialized OpenAICompatibleProvider", base_url=base_url)

    async def _apply_rate_limiting(self, model: str):
        """Apply rate limiting for the specified model."""
        if model == app_config.default_model and app_config.request_per_minute > 0:
            import time
            current_time = time.time()

            # Remove requests older than 1 minute
            self.last_request_times = [
                t for t in self.last_request_times
                if current_time - t < 60
            ]

            # Check if we've exceeded the rate limit
            if len(self.last_request_times) >= app_config.request_per_minute:
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


class LMStudioProvider(LLMProvider):
    """LMStudio local inference server provider."""

    def __init__(
        self, base_url: str = app_config.lmstudio_base_url, api_key: Optional[str] = app_config.lmstudio_api_key
    ):
        self.base_url = base_url
        self.api_key = api_key or ""  # LMStudio doesn't require API key by default
        self.last_request_times: List[float] = []
        logger.debug("Initialized LMStudioProvider", base_url=base_url)

    async def _apply_rate_limiting(self, model: str):
        """Apply rate limiting for the specified model."""
        if model == app_config.default_model and app_config.request_per_minute > 0:
            import time
            current_time = time.time()

            # Remove requests older than 1 minute
            self.last_request_times = [
                t for t in self.last_request_times
                if current_time - t < 60
            ]

            # Check if we've exceeded the rate limit
            if len(self.last_request_times) >= app_config.request_per_minute:
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
        """Generate streaming response from LMStudio API."""
        if not session:
            raise ValueError("LMStudio provider requires aiohttp session")

        await self._apply_rate_limiting(model)

        try:
            headers = {
                "Content-Type": "application/json",
            }

            # Add API key header only if provided
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": model,
                "messages": messages.to_openai_format(),
                "max_tokens": max_tokens,
                "stream": True,
            }

            logger.debug("Starting LMStudio streaming", model=model, message_count=len(messages))

            async with session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("LMStudio API error", status=response.status, error=error_text)
                    yield f"Error: LMStudio API returned {response.status} - {error_text}"
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
            logger.exception("Error in LMStudio streaming", error=str(e))
            yield f"Error: {str(e)}"

    @override
    async def generate(
        self,
        messages: Messages,
        model: str,
        max_tokens: int = 20000,
        ctx: int = 0,
        session: Optional[aiohttp.ClientSession] = None,
        **kwargs
    ) -> Optional[str]:
        """Generate complete response from LMStudio API."""
        if not session:
            logger.error("LMStudio provider requires aiohttp session")
            return None

        await self._apply_rate_limiting(model)

        try:
            headers = {
                "Content-Type": "application/json",
            }

            # Add API key header only if provided
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": model,
                "messages": messages.to_openai_format(),
                "max_tokens": max_tokens,
                "stream": False,
            }

            logger.debug("Making LMStudio non-streaming request", model=model, message_count=len(messages))

            async with session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("LMStudio API error", status=response.status, error=error_text)
                    return None

                data = await response.json()
                if 'choices' in data and data['choices']:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    logger.debug("LMStudio response received", content_length=len(content))
                    return content

                logger.warning("No choices in LMStudio response", response=data)
                return None

        except Exception as e:
            logger.exception("Error in LMStudio generation", error=str(e))
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
            elif provider_type == "lmstudio":
                cls._providers[provider_type] = LMStudioProvider(**kwargs)
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

    @classmethod
    def get_lmstudio_provider(cls) -> "LMStudioProvider":
        """Convenience method to get LMStudio provider."""
        provider = cls.get_provider("lmstudio")
        if isinstance(provider, LMStudioProvider):
            return provider
        raise ValueError("Expected LMStudioProvider")
