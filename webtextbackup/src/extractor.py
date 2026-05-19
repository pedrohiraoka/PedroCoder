"""
Content Extractor Module
Handles fetching HTML and extracting main text content using trafilatura.
"""

import requests
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional, Tuple
import trafilatura
from bs4 import BeautifulSoup


class ContentExtractor:
    """
    Responsible for fetching web pages, checking robots.txt,
    and extracting clean text content.
    """
    
    def __init__(self, user_agent: str = "WebTextBackupBot/1.0", timeout: int = 10):
        """
        Initialize the extractor with session configuration.
        
        Args:
            user_agent: User-Agent string for HTTP requests
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        # Cache for robots.txt parsers per domain
        self._robots_parsers = {}
    
    def _get_robots_parser(self, url: str) -> RobotFileParser:
        """
        Get or create a RobotFileParser for the domain of the given URL.
        
        Args:
            url: Any URL from the domain
            
        Returns:
            RobotFileParser instance for the domain
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self._robots_parsers:
            rp = RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            try:
                response = self.session.get(robots_url, timeout=5)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    # If no robots.txt, allow all
                    rp.parse(["User-agent: *", "Disallow:"])
            except Exception:
                # If we can't fetch robots.txt, assume allowed
                rp.parse(["User-agent: *", "Disallow:"])
            
            self._robots_parsers[domain] = rp
        
        return self._robots_parsers[domain]
    
    def check_robots_txt(self, url: str) -> bool:
        """
        Check if the URL is allowed by robots.txt.
        
        Args:
            url: The URL to check
            
        Returns:
            True if allowed, False if disallowed
        """
        parser = self._get_robots_parser(url)
        return parser.can_fetch("*", url)
    
    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch the HTML content of a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string, or None if failed
        """
        try:
            print(f"     -> Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                print(f"     -> Warning: Content-type is not HTML ({content_type})")
            
            return response.text
        except requests.exceptions.Timeout:
            print(f"     -> Error: Timeout while fetching {url}")
        except requests.exceptions.ConnectionError:
            print(f"     -> Error: Connection refused for {url}")
        except requests.exceptions.HTTPError as e:
            print(f"     -> Error: HTTP {e.response.status_code} for {url}")
        except Exception as e:
            print(f"     -> Error: Unexpected error fetching {url}: {e}")
        
        return None
    
    def extract_content(self, html: str, url: str, output_format: str = 'md') -> Tuple[Optional[str], Optional[str]]:
        """
        Extract main content from HTML using trafilatura.
        
        Args:
            html: Raw HTML content
            url: Source URL (used for metadata)
            output_format: 'md' for Markdown, 'txt' for plain text
            
        Returns:
            Tuple of (title, content) or (None, None) if extraction fails
        """
        if not html:
            return None, None
        
        try:
            # Use trafilatura's meta extraction for title
            soup = BeautifulSoup(html, 'lxml')
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            
            # Configure trafilatura for optimal extraction
            # include_comments=False, include_tables=False for cleaner output
            if output_format == 'md':
                content = trafilatura.extract(
                    html,
                    url=url,
                    include_formatting=True,
                    include_links=False,
                    include_tables=False,
                    include_comments=False,
                    output_format='markdown'
                )
            else:  # txt
                content = trafilatura.extract(
                    html,
                    url=url,
                    include_formatting=False,
                    include_links=False,
                    include_tables=False,
                    include_comments=False,
                    output_format='txt'
                )
            
            if not content or len(content.strip()) < 50:
                # If trafilatura fails to find meaningful content, try fallback
                print(f"     -> Warning: Low content detected, trying fallback extraction")
                content = self._fallback_extract(soup, output_format)
            
            return title, content
            
        except Exception as e:
            print(f"     -> Error: Failed to extract content: {e}")
            return None, None
    
    def _fallback_extract(self, soup: BeautifulSoup, output_format: str = 'txt') -> str:
        """
        Fallback extraction method if trafilatura fails.
        Removes script, style, nav, footer, header tags and extracts text.
        
        Args:
            soup: BeautifulSoup object
            output_format: 'md' or 'txt'
            
        Returns:
            Extracted text content
        """
        # Remove unwanted tags
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
            tag.decompose()
        
        # Remove common ad/container classes
        for tag in soup.find_all(class_=True):
            class_str = ' '.join(tag.get('class', []))
            if any(x in class_str.lower() for x in ['ad', 'banner', 'sponsor', 'cookie', 'modal']):
                tag.decompose()
        
        # Get text from body or html
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n\n'.join(lines)
