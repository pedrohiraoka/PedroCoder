"""
Unit tests for ChatBotAI framework.

Basic test suite covering core functionality.
"""

import pytest
from datetime import datetime

from chatbotai.core.models import Message, MessageRole, ConversationContext
from chatbotai.core.conversation_manager import ConversationManager, TopicRouter
from chatbotai.memory.backends import VolatileMemory, PersistentMemory
from chatbotai.handlers.function_handler import FunctionHandler
from chatbotai.utils.helpers import generate_id, sanitize_text, truncate_text


class TestMessage:
    """Tests for the Message data class."""

    def test_create_message(self) -> None:
        """Test creating a message."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, world!",
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"
        assert isinstance(msg.timestamp, datetime)

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Test response"
        assert "timestamp" in data

    def test_message_from_dict(self) -> None:
        """Test creating message from dictionary."""
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"key": "value"},
        }
        msg = Message.from_dict(data)
        assert msg.role == MessageRole.USER
        assert msg.content == "Test message"
        assert msg.metadata["key"] == "value"


class TestConversationContext:
    """Tests for ConversationContext."""

    def test_create_context(self) -> None:
        """Test creating a conversation context."""
        ctx = ConversationContext(
            conversation_id="test-123",
            user_id="user-456",
        )
        assert ctx.conversation_id == "test-123"
        assert ctx.user_id == "user-456"
        assert ctx.topic is None
        assert len(ctx.messages) == 0

    def test_add_message(self) -> None:
        """Test adding messages to context."""
        ctx = ConversationContext(
            conversation_id="test-123",
            user_id="user-456",
        )
        msg = Message(role=MessageRole.USER, content="Hello")
        ctx.add_message(msg)
        assert len(ctx.messages) == 1
        assert ctx.messages[0].content == "Hello"

    def test_get_recent_messages(self) -> None:
        """Test retrieving recent messages."""
        ctx = ConversationContext(
            conversation_id="test-123",
            user_id="user-456",
        )
        for i in range(15):
            ctx.add_message(
                Message(role=MessageRole.USER, content=f"Message {i}")
            )
        recent = ctx.get_recent_messages(count=5)
        assert len(recent) == 5
        assert recent[-1].content == "Message 14"

    def test_clear_history(self) -> None:
        """Test clearing conversation history."""
        ctx = ConversationContext(
            conversation_id="test-123",
            user_id="user-456",
        )
        ctx.add_message(Message(role=MessageRole.USER, content="Hello"))
        assert len(ctx.messages) == 1
        ctx.clear_history()
        assert len(ctx.messages) == 0


class TestTopicRouter:
    """Tests for TopicRouter."""

    def test_register_trigger(self) -> None:
        """Test registering topic triggers."""
        router = TopicRouter()
        router.register_trigger("greeting", r"\b(hi|hello)\b")
        assert "greeting" in router._triggers

    def test_detect_topic(self) -> None:
        """Test topic detection."""
        router = TopicRouter()
        router.register_trigger("greeting", r"\b(hi|hello)\b", confidence=0.9)
        router.register_trigger("farewell", r"\b(bye|goodbye)\b")

        topic, confidence = router.detect_topic("Hello there!")
        assert topic == "greeting"
        assert confidence == 0.9

    def test_default_topic(self) -> None:
        """Test default topic for unmatched messages."""
        router = TopicRouter()
        router.register_trigger("greeting", r"\b(hi|hello)\b")
        topic, confidence = router.detect_topic("Random message")
        assert topic == "general"


class TestConversationManager:
    """Tests for ConversationManager."""

    def test_create_conversation(self) -> None:
        """Test creating conversations."""
        manager = ConversationManager()
        ctx = manager.create_conversation(user_id="user-123")
        assert ctx.user_id == "user-123"
        assert ctx.conversation_id is not None

    def test_get_conversation(self) -> None:
        """Test retrieving conversations."""
        manager = ConversationManager()
        ctx = manager.create_conversation(user_id="user-123")
        retrieved = manager.get_conversation(ctx.conversation_id)
        assert retrieved is not None
        assert retrieved.user_id == "user-123"

    def test_delete_conversation(self) -> None:
        """Test deleting conversations."""
        manager = ConversationManager()
        ctx = manager.create_conversation(user_id="user-123")
        assert manager.delete_conversation(ctx.conversation_id) is True
        assert manager.get_conversation(ctx.conversation_id) is None

    def test_process_user_message(self) -> None:
        """Test processing user messages."""
        manager = ConversationManager()
        ctx = manager.create_conversation(user_id="user-123")
        msg, topic, confidence = manager.process_user_message(
            ctx.conversation_id, "Hello!"
        )
        assert msg is not None
        assert msg.role == MessageRole.USER


class TestVolatileMemory:
    """Tests for VolatileMemory."""

    def test_save_and_load(self) -> None:
        """Test saving and loading data."""
        memory = VolatileMemory()
        memory.save("key1", {"data": "value1"})
        result = memory.load("key1")
        assert result is not None
        assert result["data"] == "value1"

    def test_delete(self) -> None:
        """Test deleting data."""
        memory = VolatileMemory()
        memory.save("key1", {"data": "value1"})
        assert memory.delete("key1") is True
        assert memory.load("key1") is None

    def test_exists(self) -> None:
        """Test checking existence."""
        memory = VolatileMemory()
        assert memory.exists("nonexistent") is False
        memory.save("key1", {"data": "value1"})
        assert memory.exists("key1") is True


class TestFunctionHandler:
    """Tests for FunctionHandler."""

    def test_register_function(self) -> None:
        """Test registering functions."""
        handler = FunctionHandler()

        @handler.register(name="add_numbers", description="Add two numbers")
        def add(a: int, b: int) -> int:
            return a + b

        assert "add_numbers" in handler._functions

    def test_execute_function(self) -> None:
        """Test executing registered functions."""
        handler = FunctionHandler()

        @handler.register(name="multiply")
        def multiply(x: int, y: int) -> int:
            return x * y

        result = handler.execute("multiply", {"x": 5, "y": 3})
        assert result == 15

    def test_execute_missing_function(self) -> None:
        """Test executing non-existent function."""
        handler = FunctionHandler()
        with pytest.raises(KeyError):
            handler.execute("nonexistent")


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_generate_id(self) -> None:
        """Test ID generation."""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) == 8

    def test_generate_id_with_prefix(self) -> None:
        """Test ID generation with prefix."""
        id_with_prefix = generate_id("test")
        assert id_with_prefix.startswith("test_")

    def test_sanitize_text(self) -> None:
        """Test text sanitization."""
        dirty_text = "Hello\x00World\n\n\nTest"
        clean = sanitize_text(dirty_text)
        assert "\x00" not in clean
        assert "HelloWorld Test" == clean

    def test_truncate_text(self) -> None:
        """Test text truncation."""
        long_text = "A" * 100
        truncated = truncate_text(long_text, max_length=50)
        assert len(truncated) == 50
        assert truncated.endswith("...")

    def test_truncate_short_text(self) -> None:
        """Test truncating already short text."""
        short_text = "Hello"
        truncated = truncate_text(short_text, max_length=50)
        assert truncated == "Hello"
