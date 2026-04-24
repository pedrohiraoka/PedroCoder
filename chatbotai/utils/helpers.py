"""
Utility functions for ChatBotAI.

Provides common helper functions used throughout the framework.
"""

import hashlib
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        A unique identifier string.
    """
    unique_id = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing potentially harmful content.

    Args:
        text: The text to sanitize.

    Returns:
        Sanitized text.
    """
    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: The text to truncate.
        max_length: Maximum length in characters.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def hash_content(content: str) -> str:
    """
    Generate a hash of content.

    Args:
        content: The content to hash.

    Returns:
        SHA256 hash of the content.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_markdown_links(text: str) -> List[Dict[str, str]]:
    """
    Parse markdown links from text.

    Args:
        text: Text containing markdown links.

    Returns:
        List of dictionaries with 'text' and 'url' keys.
    """
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    matches = re.findall(pattern, text)
    return [{"text": match[0], "url": match[1]} for match in matches]


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Markdown text containing code blocks.

    Returns:
        List of dictionaries with 'language' and 'code' keys.
    """
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [{"language": match[0] or "text", "code": match[1].strip()}
            for match in matches]


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as an ISO timestamp string.

    Args:
        dt: Datetime to format (defaults to now).

    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_timestamp(timestamp: str) -> datetime:
    """
    Parse an ISO timestamp string to datetime.

    Args:
        timestamp: ISO format timestamp string.

    Returns:
        Parsed datetime object.
    """
    return datetime.fromisoformat(timestamp)


def calculate_token_estimate(text: str) -> int:
    """
    Estimate the number of tokens in a text.

    This is a rough estimate based on character count.
    Actual token counts may vary by model.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    # Rough estimate: ~4 characters per token for English
    return len(text) // 4


def split_long_message(
    text: str, max_length: int = 2000
) -> List[str]:
    """
    Split a long message into smaller chunks.

    Args:
        text: The text to split.
        max_length: Maximum length per chunk.

    Returns:
        List of text chunks.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    for word in text.split():
        if len(current_chunk) + len(word) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = word + " "
        else:
            current_chunk += word + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary.
        override: Dictionary with values to override.

    Returns:
        Merged dictionary.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and \
           isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def retry_on_failure(
    max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions on failure.

    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Delay between retries in seconds.
        exceptions: Tuple of exceptions to catch.

    Returns:
        Decorator function.
    """
    def decorator(func):
        import time
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        "Attempt %d/%d failed: %s",
                        attempt + 1,
                        max_attempts,
                        str(e),
                    )
                    if attempt < max_attempts - 1:
                        time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
