"""
ChatBot Engine - Main orchestrator for the ChatBotAI framework.

This module provides the central ChatBot class that coordinates all
components of the framework.
"""

import logging
from typing import Any, Callable, Dict, Generator, List, Optional

from .ai_engine import BaseAIEngine, OllamaEngine
from .conversation_manager import ConversationManager
from .models import ConversationContext, Message, MessageRole

logger = logging.getLogger(__name__)


class ChatBot:
    """
    Main ChatBot engine that orchestrates all framework components.

    This class provides a unified interface for creating and managing
    AI-powered conversations with support for memory, integrations,
    and custom handlers.

    Attributes:
        ai_engine: The AI engine instance for response generation.
        conversation_manager: Manager for conversation contexts.
        system_prompt: Optional system prompt for behavior customization.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful, friendly, and knowledgeable assistant. "
        "Provide clear, accurate, and concise responses."
    )

    def __init__(
        self,
        ai_engine: Optional[BaseAIEngine] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the ChatBot engine.

        Args:
            ai_engine: AI engine instance (defaults to OllamaEngine).
            system_prompt: System prompt to guide AI behavior.
            **kwargs: Additional configuration options.
        """
        self.ai_engine = ai_engine or OllamaEngine()
        self.conversation_manager = ConversationManager()
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self._custom_handlers: Dict[str, Callable[..., Any]] = {}
        self._learning_data: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("ChatBot initialized with %s", type(self.ai_engine).__name__)

    def create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> ConversationContext:
        """
        Create a new conversation for a user.

        Args:
            user_id: Unique identifier for the user.
            conversation_id: Optional custom conversation ID.

        Returns:
            The created conversation context.
        """
        return self.conversation_manager.create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            initial_topic="general",
        )

    def chat(
        self,
        conversation_id: str,
        message: str,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Generator[str, None, None]:
        """
        Send a message and get a response.

        Args:
            conversation_id: The conversation identifier.
            message: The user's message.
            stream: Whether to stream the response.
            **kwargs: Additional parameters for AI generation.

        Returns:
            The AI response text or a generator for streaming.
        """
        # Process user message and detect topic
        _, topic, confidence = self.conversation_manager.process_user_message(
            conversation_id, message
        )

        # Check for custom handlers based on topic
        handler = self.conversation_manager.router.get_handler(topic)
        if handler and confidence > 0.8:
            try:
                response = handler(message, conversation_id)
                self.conversation_manager.add_message(
                    conversation_id, MessageRole.ASSISTANT, response
                )
                return response
            except Exception as e:
                logger.error("Handler error: %s", str(e))

        # Get conversation context messages
        context_messages = self.conversation_manager.get_context_messages(
            conversation_id
        )

        # Build messages list with system prompt
        messages: List[Message] = [
            Message(role=MessageRole.SYSTEM, content=self.system_prompt)
        ]
        messages.extend(context_messages)

        # Generate response using AI engine
        if stream:
            return self._stream_response(conversation_id, messages, **kwargs)
        else:
            return self._get_response(conversation_id, messages, **kwargs)

    def _get_response(
        self,
        conversation_id: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> str:
        """
        Get a non-streaming response from the AI engine.

        Args:
            conversation_id: The conversation identifier.
            messages: List of messages for context.
            **kwargs: Additional parameters for AI generation.

        Returns:
            The AI response text.
        """
        try:
            response = self.ai_engine.generate_response(messages, **kwargs)
            self.conversation_manager.add_message(
                conversation_id, MessageRole.ASSISTANT, response
            )
            return response
        except Exception as e:
            logger.error("Error getting response: %s", str(e))
            return (
                "I apologize, but I encountered an error processing your "
                f"request. Details: {str(e)}"
            )

    def _stream_response(
        self,
        conversation_id: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Stream a response from the AI engine.

        Args:
            conversation_id: The conversation identifier.
            messages: List of messages for context.
            **kwargs: Additional parameters for AI generation.

        Yields:
            Chunks of the AI response text.
        """
        full_response = ""
        try:
            for chunk in self.ai_engine.generate_stream(messages, **kwargs):
                full_response += chunk
                yield chunk

            self.conversation_manager.add_message(
                conversation_id, MessageRole.ASSISTANT, full_response
            )
        except Exception as e:
            logger.error("Error streaming response: %s", str(e))
            yield f"\n\n[Error: {str(e)}]"

    def register_topic_trigger(
        self,
        topic: str,
        pattern: str,
        handler: Optional[Callable[..., Any]] = None,
        confidence: float = 0.8,
    ) -> None:
        """
        Register a topic trigger with optional handler.

        Args:
            topic: The topic name.
            pattern: Regex pattern to match.
            handler: Optional handler function for this topic.
            confidence: Confidence threshold for triggering.
        """
        self.conversation_manager.router.register_trigger(
            topic, pattern, confidence
        )
        if handler:
            self.conversation_manager.router.register_handler(topic, handler)
        logger.info("Registered topic trigger: %s -> %s", pattern, topic)

    def register_custom_handler(
        self, name: str, handler: Callable[..., Any]
    ) -> None:
        """
        Register a custom handler function.

        Args:
            name: Name for the handler.
            handler: The handler function.
        """
        self._custom_handlers[name] = handler
        logger.info("Registered custom handler: %s", name)

    def get_conversation_history(
        self, conversation_id: str
    ) -> List[Message]:
        """
        Get the full message history for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            List of all messages in the conversation.
        """
        context = self.conversation_manager.get_conversation(conversation_id)
        if not context:
            return []
        return context.messages

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a conversation's message history.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            True if cleared successfully.
        """
        return self.conversation_manager.clear_conversation_history(
            conversation_id
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation entirely.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            True if deleted successfully.
        """
        return self.conversation_manager.delete_conversation(conversation_id)

    def learn_from_interaction(
        self,
        user_message: str,
        assistant_response: str,
        feedback_score: float = 1.0,
    ) -> None:
        """
        Store interaction data for incremental learning.

        Args:
            user_message: The user's message.
            assistant_response: The assistant's response.
            feedback_score: Quality score (0.0-1.0).
        """
        interaction_key = f"{user_message[:50]}..."
        self._learning_data[interaction_key] = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "feedback_score": feedback_score,
        }
        logger.debug("Stored learning data for interaction")

    def is_ready(self) -> bool:
        """
        Check if the chatbot is ready to process messages.

        Returns:
            True if the AI engine is available.
        """
        return self.ai_engine.is_available()
