"""
Conversation Manager for ChatBotAI.

Handles conversation flow, topic routing, and context management.
"""

import logging
import re
import uuid
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple

from .models import ConversationContext, Message, MessageRole

logger = logging.getLogger(__name__)


class TopicRouter:
    """
    Routes conversations based on semantic triggers and topics.

    This class manages topic detection and transition logic for
    context-aware conversation handling.
    """

    def __init__(self) -> None:
        """Initialize the topic router with empty trigger mappings."""
        self._triggers: Dict[str, List[Tuple[Pattern[str], float]]] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._default_topic = "general"

    def register_trigger(
        self,
        topic: str,
        pattern: str,
        confidence: float = 0.8,
    ) -> None:
        """
        Register a semantic trigger for topic detection.

        Args:
            topic: The topic name to associate with this trigger.
            pattern: Regex pattern to match against user input.
            confidence: Confidence score for this trigger (0.0-1.0).
        """
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        if topic not in self._triggers:
            self._triggers[topic] = []
        self._triggers[topic].append((compiled_pattern, confidence))
        logger.debug("Registered trigger for topic '%s': %s", topic, pattern)

    def register_handler(
        self, topic: str, handler: Callable[..., Any]
    ) -> None:
        """
        Register a handler function for a specific topic.

        Args:
            topic: The topic name.
            handler: Function to handle messages for this topic.
        """
        self._handlers[topic] = handler
        logger.debug("Registered handler for topic '%s'", topic)

    def detect_topic(self, message: str) -> Tuple[str, float]:
        """
        Detect the topic of a message based on registered triggers.

        Args:
            message: The user message to analyze.

        Returns:
            Tuple of (detected_topic, confidence_score).
        """
        best_topic = self._default_topic
        best_confidence = 0.0

        for topic, triggers in self._triggers.items():
            for pattern, confidence in triggers:
                if pattern.search(message):
                    if confidence > best_confidence:
                        best_topic = topic
                        best_confidence = confidence

        logger.debug(
            "Detected topic '%s' with confidence %.2f",
            best_topic,
            best_confidence,
        )
        return best_topic, best_confidence

    def get_handler(
        self, topic: str
    ) -> Optional[Callable[..., Any]]:
        """
        Get the handler function for a specific topic.

        Args:
            topic: The topic name.

        Returns:
            The handler function or None if not registered.
        """
        return self._handlers.get(topic)

    def set_default_topic(self, topic: str) -> None:
        """
        Set the default topic for unmatched messages.

        Args:
            topic: The default topic name.
        """
        self._default_topic = topic


class ConversationManager:
    """
    Manages conversation contexts, flow, and state transitions.

    This class handles the lifecycle of conversations, including
    creation, persistence, and context switching.
    """

    def __init__(self) -> None:
        """Initialize the conversation manager."""
        self._conversations: Dict[str, ConversationContext] = {}
        self._router = TopicRouter()
        self._max_history_length = 50
        self._context_window = 10

    def create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        initial_topic: Optional[str] = None,
    ) -> ConversationContext:
        """
        Create a new conversation context.

        Args:
            user_id: Identifier for the user.
            conversation_id: Optional custom conversation ID.
            initial_topic: Optional initial topic for the conversation.

        Returns:
            The newly created conversation context.
        """
        conv_id = conversation_id or str(uuid.uuid4())
        context = ConversationContext(
            conversation_id=conv_id,
            user_id=user_id,
            topic=initial_topic,
        )
        self._conversations[conv_id] = context
        logger.info("Created conversation %s for user %s", conv_id, user_id)
        return context

    def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Retrieve an existing conversation context.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            The conversation context or None if not found.
        """
        return self._conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation context.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            True if deleted, False if not found.
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info("Deleted conversation %s", conversation_id)
            return True
        return False

    def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Message]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation identifier.
            role: The role of the message sender.
            content: The message content.
            metadata: Optional additional metadata.

        Returns:
            The created message or None if conversation not found.
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return None

        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        context.add_message(message)

        # Trim history if exceeds maximum length
        if len(context.messages) > self._max_history_length:
            context.messages = context.messages[-self._max_history_length:]

        return message

    def process_user_message(
        self,
        conversation_id: str,
        content: str,
    ) -> Tuple[Optional[Message], str, float]:
        """
        Process a user message and detect topic changes.

        Args:
            conversation_id: The conversation identifier.
            content: The user message content.

        Returns:
            Tuple of (message, detected_topic, confidence).
        """
        message = self.add_message(
            conversation_id, MessageRole.USER, content
        )

        context = self.get_conversation(conversation_id)
        if not context:
            return message, "general", 0.0

        # Detect topic from message
        detected_topic, confidence = self._router.detect_topic(content)

        # Update conversation topic if confidence is high enough
        if confidence > 0.7 and detected_topic != context.topic:
            old_topic = context.topic
            context.topic = detected_topic
            logger.info(
                "Topic changed from '%s' to '%s' in conversation %s",
                old_topic,
                detected_topic,
                conversation_id,
            )

        return message, detected_topic, confidence

    def get_context_messages(
        self, conversation_id: str, count: Optional[int] = None
    ) -> List[Message]:
        """
        Get recent messages for AI context window.

        Args:
            conversation_id: The conversation identifier.
            count: Number of messages to retrieve (default: context_window).

        Returns:
            List of recent messages.
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return []

        msg_count = count or self._context_window
        return context.get_recent_messages(msg_count)

    def clear_conversation_history(self, conversation_id: str) -> bool:
        """
        Clear the message history for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            True if cleared, False if not found.
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return False

        context.clear_history()
        logger.info("Cleared history for conversation %s", conversation_id)
        return True

    @property
    def router(self) -> TopicRouter:
        """Get the topic router instance."""
        return self._router

    def get_active_conversations(
        self, user_id: Optional[str] = None
    ) -> List[ConversationContext]:
        """
        Get all active conversations, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter by.

        Returns:
            List of active conversation contexts.
        """
        conversations = list(self._conversations.values())
        if user_id:
            conversations = [
                c for c in conversations if c.user_id == user_id
            ]
        return conversations
