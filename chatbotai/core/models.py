"""
Message data structures for the ChatBotAI framework.

This module defines the core message types used throughout the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(Enum):
    """Enumeration of possible message roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


@dataclass
class Message:
    """
    Represents a single message in a conversation.

    Attributes:
        role: The role of the message sender (user, assistant, system).
        content: The text content of the message.
        timestamp: When the message was created.
        metadata: Additional metadata associated with the message.
    """

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary representation.

        Returns:
            A dictionary containing all message attributes.
        """
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        Create a Message instance from a dictionary.

        Args:
            data: Dictionary containing message data.

        Returns:
            A new Message instance.
        """
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConversationContext:
    """
    Represents the context of an ongoing conversation.

    Attributes:
        conversation_id: Unique identifier for the conversation.
        user_id: Identifier for the user participating in the conversation.
        topic: Current topic or theme of the conversation.
        messages: List of messages in the conversation history.
        state: Current state of the conversation flow.
    """

    conversation_id: str
    user_id: str
    topic: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    state: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """
        Add a message to the conversation history.

        Args:
            message: The message to add.
        """
        self.messages.append(message)

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """
        Retrieve the most recent messages from the conversation.

        Args:
            count: Number of recent messages to retrieve.

        Returns:
            List of the most recent messages.
        """
        return self.messages[-count:]

    def clear_history(self) -> None:
        """Clear all messages from the conversation history."""
        self.messages.clear()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation context to a dictionary.

        Returns:
            Dictionary representation of the conversation context.
        """
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "messages": [msg.to_dict() for msg in self.messages],
            "state": self.state,
            "metadata": self.metadata,
        }
