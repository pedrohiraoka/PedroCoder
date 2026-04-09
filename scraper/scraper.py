"""
Main async scraper module for the web scraper.
Handles asynchronous HTTP requests and coordinates scraping operations.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientError, ClientTimeout

from .config import ScraperConfig
from .parser import parse_page
from .storage import DataStorage

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Exception raised for scraper errors."""
    pass


class AsyncScraper:
    """
    Asynchronous web scraper with configurable behavior.
    
    Features:
    - Concurrent requests with configurable limit
    - Custom headers and timeouts
    - Configurable data extraction via CSS selectors
    - Robust error handling and retry logic
    - Progress tracking and logging
    """
    
    def __init__(self, config: ScraperConfig):
        """
        Initialize the async scraper.
        
        Args:
            config: ScraperConfig instance with scraping configuration.
        """
        self.config = config
        self.storage = DataStorage(config.output_file, config.output_format)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        
        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'pages_failed': 0,
            'items_extracted': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"Initialized AsyncScraper with {len(config.urls)} URLs")
    
    async def _create_session(self) -> None:
        """Create aiohttp client session with configured settings."""
        timeout = ClientTimeout(total=self.config.timeout)
        
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent,
            ssl=False  # Disable SSL verification for broader compatibility
        )
        
        self.session = aiohttp.ClientSession(
            headers=self.config.headers,
            timeout=timeout,
            connector=connector
        )
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        logger.debug(f"Created session with timeout={self.config.timeout}s, max_concurrent={self.config.max_concurrent}")
    
    async def _close_session(self) -> None:
        """Close the aiohttp client session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("Session closed")
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a single page asynchronously.
        
        Args:
            url: URL to fetch.
            
        Returns:
            HTML content as string, or None if failed.
        """
        if not self.session:
            raise ScraperError("Session not initialized")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text(encoding='utf-8')
                    logger.debug(f"Successfully fetched {url} ({len(html)} bytes)")
                    return html
                elif response.status == 404:
                    logger.warning(f"Page not found (404): {url}")
                    return None
                else:
                    logger.warning(f"HTTP error {response.status} for {url}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except ClientError as e:
            logger.error(f"Client error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    async def scrape_url(self, url: str, base_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL with rate limiting.
        
        Args:
            url: URL to scrape.
            base_url: Base URL for resolving relative links.
            
        Returns:
            Dictionary with extracted data, or None if failed.
        """
        async with self.semaphore:
            logger.info(f"Scraping: {url}")
            
            # Apply delay before request
            await asyncio.sleep(self.config.delay)
            
            # Fetch the page
            html = await self.fetch_page(url)
            
            if html is None:
                self.stats['pages_failed'] += 1
                return None
            
            # Parse and extract data
            try:
                result = parse_page(
                    html=html,
                    selectors=self.config.selectors,
                    link_selectors=self.config.link_selectors,
                    extract_links_flag=self.config.follow_links,
                    parser='lxml'
                )
                
                # Add metadata
                result['_url'] = url
                result['_scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Resolve relative links if needed
                if self.config.follow_links and '_links' in result and base_url:
                    resolved_links = []
                    for link in result['_links']:
                        absolute_link = urljoin(base_url, link)
                        if self._is_valid_url(absolute_link):
                            resolved_links.append(absolute_link)
                    result['_links'] = resolved_links
                
                self.stats['pages_scraped'] += 1
                self.stats['items_extracted'] += 1
                
                logger.info(f"Successfully scraped {url}")
                return result
                
            except Exception as e:
                logger.error(f"Error parsing {url}: {e}")
                self.stats['pages_failed'] += 1
                return None
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and should be followed.
        
        Args:
            url: URL to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False
    
    async def scrape_all(self) -> List[Dict[str, Any]]:
        """
        Scrape all configured URLs concurrently.
        
        Returns:
            List of dictionaries containing extracted data.
        """
        if not self.config.urls:
            logger.warning("No URLs to scrape")
            return []
        
        await self._create_session()
        
        try:
            self.stats['start_time'] = time.time()
            logger.info(f"Starting scrape of {len(self.config.urls)} URLs")
            
            # Create tasks for all URLs
            tasks = [
                self.scrape_url(url, urlparse(url).scheme + '://' + urlparse(url).netloc)
                for url in self.config.urls
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed with exception: {result}")
                    self.stats['pages_failed'] += 1
                elif result is not None:
                    successful_results.append(result)
                    self.storage.add(result)
            
            self.stats['end_time'] = time.time()
            elapsed = self.stats['end_time'] - self.stats['start_time']
            
            logger.info(
                f"Scraping completed: {self.stats['pages_scraped']} succeeded, "
                f"{self.stats['pages_failed']} failed in {elapsed:.2f}s"
            )
            
            return successful_results
            
        finally:
            await self._close_session()
    
    async def scrape_with_crawl(
        self,
        start_urls: Optional[List[str]] = None,
        max_pages: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrape with crawling capability (follow links).
        
        Args:
            start_urls: Starting URLs (uses config.urls if None).
            max_pages: Maximum number of pages to scrape.
            
        Returns:
            List of dictionaries containing extracted data.
        """
        if not self.config.follow_links:
            logger.warning("Crawling requested but follow_links is disabled in config")
            return await self.scrape_all()
        
        start_urls = start_urls or self.config.urls
        visited = set()
        to_visit = list(start_urls)
        results = []
        
        await self._create_session()
        
        try:
            self.stats['start_time'] = time.time()
            logger.info(f"Starting crawl from {len(start_urls)} URLs (max {max_pages} pages)")
            
            while to_visit and len(visited) < max_pages:
                url = to_visit.pop(0)
                
                # Normalize URL
                url = url.rstrip('/')
                if url in visited:
                    continue
                
                visited.add(url)
                logger.info(f"Crawling ({len(visited)}/{max_pages}): {url}")
                
                # Scrape the page
                result = await self.scrape_url(
                    url,
                    urlparse(url).scheme + '://' + urlparse(url).netloc
                )
                
                if result:
                    results.append(result)
                    self.storage.add(result)
                    
                    # Add new links to visit
                    new_links = result.get('_links', [])
                    for link in new_links:
                        link = link.rstrip('/')
                        if link not in visited and link not in to_visit:
                            # Only follow links from same domain
                            if urlparse(link).netloc == urlparse(url).netloc:
                                to_visit.append(link)
                                logger.debug(f"Queued: {link}")
            
            self.stats['end_time'] = time.time()
            elapsed = self.stats['end_time'] - self.stats['start_time']
            self.stats['pages_scraped'] = len(results)
            
            logger.info(
                f"Crawl completed: {len(results)} pages scraped, "
                f"{len(to_visit)} URLs queued in {elapsed:.2f}s"
            )
            
            return results
            
        finally:
            await self._close_session()
    
    def save_results(self) -> str:
        """
        Save all scraped results to the output file.
        
        Returns:
            Path to the saved file.
        """
        return self.storage.save()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics.
        
        Returns:
            Dictionary with statistics.
        """
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['elapsed_time'] = stats['end_time'] - stats['start_time']
        stats['success_rate'] = (
            stats['pages_scraped'] / (stats['pages_scraped'] + stats['pages_failed'])
            if (stats['pages_scraped'] + stats['pages_failed']) > 0
            else 0
        )
        return stats
    
    def __repr__(self) -> str:
        return f"AsyncScraper(urls={len(self.config.urls)}, storage={self.storage})"
