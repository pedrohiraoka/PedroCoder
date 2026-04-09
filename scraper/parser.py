"""
Parser module for the async web scraper.
Handles HTML parsing and data extraction using BeautifulSoup.
"""

import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Exception raised for parsing errors."""
    pass


def parse_html(html: str, parser: str = 'lxml') -> BeautifulSoup:
    """
    Parse HTML content using BeautifulSoup.
    
    Args:
        html: Raw HTML string to parse.
        parser: Parser to use ('lxml', 'html.parser', 'html5lib').
        
    Returns:
        BeautifulSoup object.
        
    Raises:
        ParseError: If parsing fails.
    """
    try:
        soup = BeautifulSoup(html, parser)
        logger.debug(f"HTML parsed successfully with {parser} parser")
        return soup
    except Exception as e:
        raise ParseError(f"Failed to parse HTML: {e}")


def extract_data(soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract data from parsed HTML using CSS selectors.
    
    Args:
        soup: BeautifulSoup object containing parsed HTML.
        selectors: Dictionary mapping field names to CSS selectors.
                   Supports special suffixes:
                   - ':text' for text content (default)
                   - ':html' for inner HTML
                   - ':attr:name' for attribute value (e.g., 'href:attr:href')
                   - ':all' for multiple elements (returns list)
                   
    Returns:
        Dictionary with extracted data.
    """
    data = {}
    
    for field_name, selector in selectors.items():
        try:
            value = _extract_field(soup, selector, field_name)
            data[field_name] = value
            logger.debug(f"Extracted '{field_name}' using selector '{selector}'")
        except Exception as e:
            logger.warning(f"Failed to extract '{field_name}': {e}")
            data[field_name] = None
    
    return data


def _extract_field(soup: BeautifulSoup, selector: str, field_name: str) -> Any:
    """
    Extract a single field from soup based on selector syntax.
    
    Args:
        soup: BeautifulSoup object.
        selector: CSS selector with optional suffix.
        field_name: Name of the field (for logging).
        
    Returns:
        Extracted value (string, list, or None).
    """
    # Check for :all suffix (multiple elements)
    if selector.endswith(':all'):
        base_selector = selector[:-4]
        elements = soup.select(base_selector)
        return [_get_element_text(el) for el in elements]
    
    # Check for :attr: suffix (attribute extraction)
    if '::attr(' in selector:
        # New syntax: selector::attr(name)
        parts = selector.split('::attr(')
        base_selector = parts[0]
        attr_name = parts[1].rstrip(')') if len(parts) > 1 else 'href'
        element = soup.select_one(base_selector)
        if element and element.has_attr(attr_name):
            return element[attr_name]
        return None
    
    # Legacy syntax: selector:attr:name
    if ':attr:' in selector:
        parts = selector.split(':attr:')
        base_selector = parts[0]
        attr_name = parts[1] if len(parts) > 1 else 'href'
        element = soup.select_one(base_selector)
        if element and element.has_attr(attr_name):
            return element[attr_name]
        return None
    
    # Check for :html suffix (inner HTML)
    if selector.endswith(':html'):
        base_selector = selector[:-5]
        element = soup.select_one(base_selector)
        if element:
            return str(element)
        return None
    
    # Check for ::class special syntax to get class attribute
    if '::class' in selector:
        base_selector = selector.replace('::class', '')
        element = soup.select_one(base_selector)
        if element and element.has_attr('class'):
            return ' '.join(element['class'])
        return None
    
    # Default: extract text content
    # (also handles selectors ending with :text)
    base_selector = selector.replace(':text', '')
    element = soup.select_one(base_selector)
    return _get_element_text(element) if element else None


def _get_element_text(element) -> Optional[str]:
    """
    Get clean text content from an element.
    
    Args:
        element: BeautifulSoup element.
        
    Returns:
        Stripped text content or None.
    """
    if element is None:
        return None
    text = element.get_text(separator=' ', strip=True)
    return text if text else None


def extract_links(soup: BeautifulSoup, link_selectors: List[str]) -> List[str]:
    """
    Extract links from parsed HTML.
    
    Args:
        soup: BeautifulSoup object.
        link_selectors: List of CSS selectors for finding links.
        
    Returns:
        List of href values.
    """
    links = []
    
    for selector in link_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                if element.has_attr('href'):
                    href = element['href']
                    if href and href not in links:
                        links.append(href)
            logger.debug(f"Found {len(links)} links using selector '{selector}'")
        except Exception as e:
            logger.warning(f"Error extracting links with selector '{selector}': {e}")
    
    return links


def parse_page(
    html: str,
    selectors: Dict[str, str],
    link_selectors: Optional[List[str]] = None,
    extract_links_flag: bool = False,
    parser: str = 'lxml'
) -> Dict[str, Any]:
    """
    Parse a page and extract all configured data.
    
    Args:
        html: Raw HTML content.
        selectors: Data extraction selectors.
        link_selectors: Selectors for finding links.
        extract_links_flag: Whether to extract links.
        parser: HTML parser to use.
        
    Returns:
        Dictionary containing extracted data and optionally links.
    """
    soup = parse_html(html, parser)
    result = extract_data(soup, selectors)
    
    if extract_links_flag and link_selectors:
        links = extract_links(soup, link_selectors)
        result['_links'] = links
        logger.debug(f"Extracted {len(links)} links")
    
    return result
