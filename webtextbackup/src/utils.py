"""
Utility functions for URL handling, file naming, and common operations.
"""

import os
import re
from urllib.parse import urlparse, urljoin, urldefrag


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL by adding https:// if missing, removing fragments,
    and resolving relative paths.
    
    Args:
        url: The URL to normalize
        base_url: Base URL for resolving relative paths
        
    Returns:
        Normalized absolute URL
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        if base_url:
            parsed_base = urlparse(base_url)
            url = f"{parsed_base.scheme}://{url}"
        else:
            url = f"https://{url}"
    
    # Remove fragment (#something)
    url, _ = urldefrag(url)
    
    # Resolve relative URLs if base_url is provided
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Normalize trailing slashes for consistency (except for root)
    parsed = urlparse(url)
    if parsed.path and not parsed.path.endswith('/') and not os.path.splitext(parsed.path)[1]:
        # Only add trailing slash if no file extension
        pass  # Keep as is for flexibility
    
    return url.strip('/')


def get_domain(url: str) -> str:
    """
    Extract the domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain string (e.g., 'example.com')
    """
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_internal_url(url: str, base_domain: str) -> bool:
    """
    Check if a URL belongs to the same domain (internal link).
    
    Args:
        url: The URL to check
        base_domain: The base domain to compare against
        
    Returns:
        True if internal, False otherwise
    """
    url_domain = get_domain(url)
    # Check exact match or subdomain match
    return url_domain == base_domain or url_domain.endswith(f".{base_domain}")


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be used as a filename.
    Removes/replaces invalid characters and truncates if too long.
    
    Args:
        filename: The original filename
        max_length: Maximum length of the filename
        
    Returns:
        Sanitized filename safe for all OS
    """
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_. ')
    
    # Truncate if too long (preserve extension if present)
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        if ext:
            sanitized = name[:max_length-len(ext)] + ext
        else:
            sanitized = sanitized[:max_length]
    
    # Ensure we have at least some name
    if not sanitized or sanitized == '.':
        sanitized = 'unnamed'
    
    return sanitized


def create_directory_structure(output_dir: str, url_path: str) -> str:
    """
    Create directory structure mirroring the URL path.
    
    Args:
        output_dir: Base output directory
        url_path: Path component from URL (e.g., '/blog/post-1')
        
    Returns:
        Full directory path where file should be saved
    """
    # Remove leading slash and split path
    path_parts = [p for p in url_path.strip('/').split('/') if p]
    
    # Build full path
    full_path = output_dir
    for part in path_parts[:-1]:  # All parts except the last (which is the filename)
        full_path = os.path.join(full_path, sanitize_filename(part))
    
    # Create directories
    os.makedirs(full_path, exist_ok=True)
    
    return full_path


def get_url_path_for_filename(url: str) -> str:
    """
    Extract the path component from URL for creating directory structure.
    
    Args:
        url: The full URL
        
    Returns:
        Path component (e.g., '/blog/post-1' from 'https://example.com/blog/post-1')
    """
    parsed = urlparse(url)
    return parsed.path if parsed.path else '/'
