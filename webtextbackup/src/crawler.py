"""
Crawler Module
Handles recursive crawling of websites, discovering internal links,
and managing the URL queue.
"""

import time
from collections import deque
from typing import Set, List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from .extractor import ContentExtractor
from .utils import (
    normalize_url,
    get_domain,
    is_internal_url,
    sanitize_filename,
    create_directory_structure,
    get_url_path_for_filename,
)


class Crawler:
    """
    Responsible for crawling websites recursively,
    discovering internal links, and coordinating extraction.
    """
    
    def __init__(
        self,
        extractor: ContentExtractor,
        output_dir: str,
        max_depth: int = 2,
        delay: float = 1.0,
        output_format: str = 'md'
    ):
        """
        Initialize the crawler.
        
        Args:
            extractor: ContentExtractor instance for fetching and extracting content
            output_dir: Base directory for saving files
            max_depth: Maximum crawl depth
            delay: Delay between requests in seconds
            output_format: 'md' or 'txt'
        """
        self.extractor = extractor
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.delay = delay
        self.output_format = output_format
        
        # Track visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        
        # Statistics
        self.success_count = 0
        self.error_count = 0
    
    def extract_links_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract all internal links from HTML content.
        
        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of normalized internal URLs
        """
        if not html:
            return []
        
        base_domain = get_domain(base_url)
        links = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            for anchor in soup.find_all('a', href=True):
                href = anchor['href'].strip()
                
                # Skip fragments, javascript, mailto, tel, etc.
                if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    continue
                
                # Normalize and resolve relative URLs
                absolute_url = normalize_url(href, base_url)
                
                # Check if internal
                if is_internal_url(absolute_url, base_domain):
                    # Remove fragment
                    parsed = urlparse(absolute_url)
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"
                    
                    links.append(clean_url)
        
        except Exception as e:
            print(f"     -> Warning: Error parsing links: {e}")
        
        return links
    
    def save_content(self, url: str, title: str, content: str) -> bool:
        """
        Save extracted content to a file.
        
        Args:
            url: Source URL
            title: Page title
            content: Extracted text content
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not content:
            return False
        
        try:
            # Determine filename and path
            parsed = urlparse(url)
            path = parsed.path if parsed.path else '/'
            
            # If path is root or empty, use index
            if path == '/':
                filename = "index"
                dir_path = self.output_dir
            else:
                # Use the last part of path as filename
                path_parts = [p for p in path.strip('/').split('/') if p]
                if path_parts:
                    # Use URL path for directory structure
                    filename_base = path_parts[-1]
                    # Remove query string from filename if present
                    filename_base = filename_base.split('?')[0]
                    # Sanitize
                    filename = sanitize_filename(filename_base)
                    if not filename or filename == '.':
                        filename = sanitize_filename(title)[:50] if title else "page"
                    
                    # Create directory structure
                    dir_path = create_directory_structure(self.output_dir, path)
                else:
                    filename = "index"
                    dir_path = self.output_dir
            
            # Ensure filename has extension
            ext = self.output_format
            if not filename.endswith(f'.{ext}'):
                # Remove any existing extension
                filename = filename.split('.')[0]
                filename = f"{filename}.{ext}"
            
            # Full file path
            file_path = f"{dir_path}/{filename}" if dir_path != self.output_dir else f"{self.output_dir}/{filename}"
            
            # Prepare content with title header
            if self.output_format == 'md':
                full_content = f"# {title}\n\n**Source:** {url}\n\n---\n\n{content}"
            else:
                full_content = f"{title}\n\nSource: {url}\n\n{'='*50}\n\n{content}"
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"     -> Saved: {file_path}")
            return True
            
        except Exception as e:
            print(f"     -> Error: Failed to save file: {e}")
            return False
    
    def process_url(self, url: str, current_depth: int = 0) -> List[str]:
        """
        Process a single URL: fetch, extract, save, and discover links.
        
        Args:
            url: URL to process
            current_depth: Current crawl depth
            
        Returns:
            List of discovered internal links
        """
        print(f"\n[{len(self.visited_urls) + 1}] Processing (depth {current_depth}): {url}")
        
        # Check robots.txt
        if not self.extractor.check_robots_txt(url):
            print(f"     -> Skipped: Disallowed by robots.txt")
            return []
        
        # Fetch HTML
        html = self.extractor.fetch_html(url)
        if not html:
            self.error_count += 1
            return []
        
        # Extract content
        title, content = self.extractor.extract_content(html, url, self.output_format)
        
        if title and content:
            # Save to file
            if self.save_content(url, title, content):
                self.success_count += 1
            else:
                self.error_count += 1
        else:
            print(f"     -> Warning: No meaningful content extracted")
            self.error_count += 1
        
        # Extract links for further crawling
        new_links = self.extract_links_from_html(html, url)
        
        return new_links
    
    def crawl(self, start_url: str) -> None:
        """
        Start the crawling process from a given URL.
        
        Args:
            start_url: The root URL to start crawling from
        """
        # Normalize start URL
        start_url = normalize_url(start_url).rstrip('/')
        base_domain = get_domain(start_url)
        
        print(f"\n>> Starting Crawl")
        print(f">> Base URL: {start_url}")
        print(f">> Base Domain: {base_domain}")
        print(f">> Max Depth: {self.max_depth}")
        print(f">> Output Directory: {self.output_dir}")
        print(f">> Delay: {self.delay}s")
        print(f">> Format: {self.output_format}")
        print(f"=" * 60)
        
        # Queue: (url, depth)
        queue = deque([(start_url, 0)])
        
        while queue:
            url, depth = queue.popleft()
            
            # Normalize URL for comparison
            url = url.rstrip('/')
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Skip if max depth reached (except for processing the URL itself)
            if depth > self.max_depth:
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Process URL and get new links
            new_links = self.process_url(url, depth)
            
            # Add new links to queue if within depth limit
            if depth < self.max_depth:
                for link in new_links:
                    link_normalized = link.rstrip('/')
                    if link_normalized not in self.visited_urls:
                        queue.append((link_normalized, depth + 1))
            
            # Apply delay (if there are more items to process)
            if queue:
                print(f"     -> Waiting {self.delay}s...")
                time.sleep(self.delay)
        
        # Print summary
        print(f"\n" + "=" * 60)
        print(f">> Crawl Complete!")
        print(f">> Total URLs Visited: {len(self.visited_urls)}")
        print(f">> Successful Extractions: {self.success_count}")
        print(f">> Errors/Warnings: {self.error_count}")
        print(f">> Output Directory: {self.output_dir}")
