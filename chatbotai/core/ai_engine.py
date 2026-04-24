"""
AI Engine module for ChatBotAI.

Provides the interface for AI model inference, currently supporting Ollama
with Llama family models for local, private AI processing.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional

from ..core.models import Message, MessageRole

logger = logging.getLogger(__name__)


class BaseAIEngine(ABC):
    """
    Abstract base class for AI engine implementations.

    This class defines the interface that all AI engine implementations
    must follow to ensure compatibility with the ChatBotAI framework.
    """

    @abstractmethod
    def generate_response(
        self, messages: List[Message], **kwargs: Any
    ) -> str:
        """
        Generate a response based on the conversation history.

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters for generation.

        Returns:
            The generated response text.
        """
        pass

    @abstractmethod
    def generate_stream(
        self, messages: List[Message], **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response.

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters for generation.

        Yields:
            Chunks of the generated response text.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI engine is available and ready.

        Returns:
            True if the engine is available, False otherwise.
        """
        pass


class OllamaEngine(BaseAIEngine):
    """
    AI Engine implementation using Ollama for local LLM inference.

    This engine connects to a local Ollama instance to generate responses
    using Llama family models or any other model available in Ollama.

    Attributes:
        model_name: Name of the model to use (e.g., 'llama3.2', 'llama3.1').
        base_url: Base URL of the Ollama API server.
        timeout: Request timeout in seconds.
    """

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_TIMEOUT = 60

    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize the Ollama AI engine.

        Args:
            model_name: Name of the Ollama model to use.
            base_url: Base URL of the Ollama API server.
            timeout: Request timeout in seconds.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self._client = None

        logger.info(
            "Initialized OllamaEngine with model '%s' at %s",
            self.model_name,
            self.base_url,
        )

    def _get_client(self) -> Any:
        """
        Get or create the Ollama client instance.

        Returns:
            The Ollama client instance.
        """
        if self._client is None:
            try:
                import ollama

                self._client = ollama.Client(host=self.base_url)
                logger.debug("Created new Ollama client instance")
            except ImportError:
                logger.error(
                    "ollama package not installed. Run: pip install ollama"
                )
                raise
        return self._client

    def _format_messages(
        self, messages: List[Message]
    ) -> List[Dict[str, str]]:
        """
        Format internal Message objects for Ollama API.

        Args:
            messages: List of Message objects.

        Returns:
            List of dictionaries formatted for Ollama API.
        """
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        return formatted

    def generate_response(
        self, messages: List[Message], **kwargs: Any
    ) -> str:
        """
        Generate a response using Ollama.

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters (temperature, top_p, etc.).

        Returns:
            The generated response text.

        Raises:
            RuntimeError: If the Ollama server is unavailable.
        """
        try:
            client = self._get_client()
            formatted_messages = self._format_messages(messages)

            options = {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }

            response = client.chat(
                model=self.model_name,
                messages=formatted_messages,
                options=options,
            )

            content = response["message"]["content"]
            logger.debug("Generated response of length %d", len(content))
            return content

        except Exception as e:
            logger.error("Error generating response: %s", str(e))
            raise RuntimeError(f"Failed to generate response: {e}") from e

    def generate_stream(
        self, messages: List[Message], **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response using Ollama.

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters for generation.

        Yields:
            Chunks of the generated response text.
        """
        try:
            client = self._get_client()
            formatted_messages = self._format_messages(messages)

            options = {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }

            stream = client.chat(
                model=self.model_name,
                messages=formatted_messages,
                options=options,
                stream=True,
            )

            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            logger.error("Error in streaming response: %s", str(e))
            raise RuntimeError(f"Streaming failed: {e}") from e

    def is_available(self) -> bool:
        """
        Check if the Ollama server is available.

        Returns:
            True if the server responds, False otherwise.
        """
        try:
            client = self._get_client()
            client.list()
            return True
        except Exception:
            logger.warning("Ollama server is not available")
            return False

    def list_models(self) -> List[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names available in Ollama.
        """
        try:
            client = self._get_client()
            models = client.list()
            return [model["name"] for model in models.get("models", [])]
        except Exception as e:
            logger.error("Error listing models: %s", str(e))
            return []
