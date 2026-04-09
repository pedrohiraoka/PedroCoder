#!/usr/bin/env python3
"""
Text-based Web Browser CLI

A command-line interface that simulates a simplified web browser,
operating exclusively in text mode. Users can search, view results,
select pages, and navigate content with various actions.
"""

import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

import click
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from readability import Document


# Constants
MAX_PAGE_SIZE = 1 * 1024 * 1024  # 1 MB
REQUEST_DELAY = 1.0  # seconds between requests to same host
CACHE_DIR = Path.home() / ".text_browser_cache"
SESSION_FILE = Path.home() / ".text_browser_session.json"


@dataclass
class SearchResult:
    """Represents a single search result."""
    number: int
    title: str
    domain: str
    snippet: str
    url: str


@dataclass
class PageContent:
    """Represents extracted content from a webpage."""
    url: str
    domain: str
    title: str
    summary_short: str
    summary_detailed: str
    paragraphs: list[str]
    links: list[tuple[str, str]]  # (text, url)
    raw_text: str


@dataclass
class SessionContext:
    """Maintains session state."""
    last_query: str = ""
    results: list[SearchResult] = field(default_factory=list)
    visited_pages: dict[str, PageContent] = field(default_factory=dict)
    saved_snippets: list[str] = field(default_factory=list)
    current_page: Optional[PageContent] = None
    host_last_request: dict[str, float] = field(default_factory=dict)


class TextBrowser:
    """Main text browser application class."""

    def __init__(self):
        self.session = SessionContext()
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_session()

    def _load_session(self):
        """Load previous session from file."""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.session.last_query = data.get("last_query", "")
                    self.session.saved_snippets = data.get("saved_snippets", [])
            except (json.JSONDecodeError, IOError):
                pass

    def _save_session(self):
        """Save current session to file."""
        try:
            data = {
                "last_query": self.session.last_query,
                "saved_snippets": self.session.saved_snippets,
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            click.echo(f"Warning: Could not save session: {e}", err=True)

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached_summary(self, url: str, mode: str = "short") -> Optional[str]:
        """Retrieve cached summary if available."""
        cache_key = f"{self._get_cache_key(url)}_{mode}"
        cache_file = self.cache_dir / cache_key
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return f.read()
            except IOError:
                pass
        return None

    def _cache_summary(self, url: str, summary: str, mode: str = "short"):
        """Cache a summary for a URL."""
        cache_key = f"{self._get_cache_key(url)}_{mode}"
        cache_file = self.cache_dir / cache_key
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(summary)
        except IOError:
            pass

    def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt (basic check)."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                # Basic parsing - check for Disallow rules
                path = parsed.path
                for line in response.text.split("\n"):
                    line = line.strip()
                    if line.lower().startswith("disallow:"):
                        disallowed = line.split(":", 1)[1].strip()
                        if disallowed and path.startswith(disallowed):
                            return False
            return True
        except requests.RequestException:
            # If we can't fetch robots.txt, assume allowed
            return True

    def _respect_rate_limit(self, url: str):
        """Enforce rate limiting per host."""
        parsed = urlparse(url)
        host = parsed.netloc
        now = time.time()
        
        if host in self.session.host_last_request:
            elapsed = now - self.session.host_last_request[host]
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)
        
        self.session.host_last_request[host] = time.time()

    def _apply_filters(self, query: str) -> tuple[str, dict]:
        """
        Parse and apply search filters from query.
        Returns cleaned query and filter parameters.
        """
        filters = {}
        parts = query.split()
        clean_parts = []

        for part in parts:
            if part.startswith("site:"):
                filters["site"] = part[5:]
            elif part.startswith("filetype:"):
                filters["filetype"] = part[9:]
            elif part.startswith("lang:"):
                filters["lang"] = part[5:]
            elif part.startswith("region:"):
                filters["region"] = part[7:]
            else:
                clean_parts.append(part)

        return " ".join(clean_parts), filters

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """
        Perform a DuckDuckGo search and return results.
        """
        clean_query, filters = self._apply_filters(query)
        self.session.last_query = clean_query

        ddgs = DDGS()
        results = []

        try:
            # Build search parameters
            search_query = clean_query
            
            if filters.get("site"):
                search_query = f"site:{filters['site']} {clean_query}"
            if filters.get("filetype"):
                search_query = f"{clean_query} filetype:{filters['filetype']}"
            
            search_kwargs = {"max_results": max_results}
            if filters.get("region"):
                search_kwargs["region"] = filters["region"]

            ddg_results = list(ddgs.text(search_query, **search_kwargs))

            for i, r in enumerate(ddg_results, 1):
                parsed_url = urlparse(r.get("href", ""))
                domain = parsed_url.netloc or "unknown"
                snippet = r.get("body", "")[:200]
                
                results.append(SearchResult(
                    number=i,
                    title=r.get("title", "No title"),
                    domain=domain,
                    snippet=snippet,
                    url=r.get("href", ""),
                ))

            self.session.results = results
            return results

        except Exception as e:
            click.echo(f"Search error: {e}", err=True)
            return []

    def fetch_and_extract_content(self, url: str) -> Optional[PageContent]:
        """
        Fetch a URL and extract its main content.
        Handles errors, paywalls, and dynamic content gracefully.
        """
        # Check robots.txt
        if not self._check_robots_txt(url):
            click.echo("Warning: This URL may be restricted by robots.txt", err=True)

        # Rate limiting
        self._respect_rate_limit(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TextBrowser/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                stream=True,
                allow_redirects=True,
            )

            # Check content length
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_PAGE_SIZE:
                click.echo("Error: Page too large (>1MB)", err=True)
                return None

            # Read content with size limit
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_PAGE_SIZE:
                    click.echo("Error: Page content exceeded size limit", err=True)
                    return None

            # Detect paywalls or login requirements
            text_preview = content[:1000].decode("utf-8", errors="ignore").lower()
            if any(phrase in text_preview for phrase in [
                "subscribe", "paywall", "login required", "sign in to continue",
                "premium content", "access denied"
            ]):
                click.echo("Warning: This page may require login or subscription", err=True)

            # Parse HTML
            try:
                html = content.decode("utf-8", errors="ignore")
                doc = Document(html)
                soup = BeautifulSoup(doc.summary(), "html.parser")
            except Exception as e:
                click.echo(f"Parsing error: {e}", err=True)
                return None

            # Extract title
            title = doc.short_title() or soup.find("title")
            title = str(title).strip() if title else "No title"

            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"]):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    paragraphs.append(text)

            # Generate summaries
            summary_short = self._generate_summary(paragraphs, mode="short")
            summary_detailed = self._generate_summary(paragraphs, mode="detailed")

            # Cache summaries
            self._cache_summary(url, summary_short, "short")
            self._cache_summary(url, summary_detailed, "detailed")

            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)[:100]
                href = urljoin(url, a["href"])
                if text and href.startswith("http"):
                    links.append((text, href))

            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            page_content = PageContent(
                url=url,
                domain=domain,
                title=title,
                summary_short=summary_short,
                summary_detailed=summary_detailed,
                paragraphs=paragraphs,
                links=links[:50],  # Limit to 50 links
                raw_text=soup.get_text(separator="\n", strip=True)[:10000],
            )

            self.session.visited_pages[url] = page_content
            self.session.current_page = page_content

            return page_content

        except requests.exceptions.SSLError:
            click.echo("Error: SSL certificate verification failed", err=True)
            return None
        except requests.exceptions.Timeout:
            click.echo("Error: Request timed out", err=True)
            return None
        except requests.exceptions.RequestException as e:
            click.echo(f"Network error: {e}", err=True)
            return None
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            return None

    def _generate_summary(self, paragraphs: list[str], mode: str = "short") -> str:
        """Generate a summary from paragraphs."""
        if not paragraphs:
            return "No content available."

        if mode == "short":
            # Take first 2-3 significant paragraphs
            selected = []
            for p in paragraphs[:5]:
                if len(p) > 50:
                    selected.append(p)
                if len(selected) >= 3:
                    break
            return " ".join(selected)[:500] + ("..." if len(" ".join(selected)) > 500 else "")
        else:
            # Detailed mode - up to 800 words
            words = 0
            selected = []
            for p in paragraphs:
                selected.append(p)
                words += len(p.split())
                if words >= 800:
                    break
            return "\n\n".join(selected)

    def display_results(self, results: list[SearchResult]):
        """Display search results in formatted list."""
        if not results:
            click.echo("No results found.")
            return

        click.echo(f"\n{'='*60}")
        click.echo(f"Search Results ({len(results)} found)")
        click.echo(f"{'='*60}\n")

        for r in results:
            click.echo(f"[{r.number}] {r.title}")
            click.echo(f"     Domain: {r.domain}")
            click.echo(f"     URL: {r.url[:70]}{'...' if len(r.url) > 70 else ''}")
            click.echo(f"     {r.snippet[:150]}{'...' if len(r.snippet) > 150 else ''}")
            click.echo()

        click.echo("-"*60)
        click.echo("Actions: Enter number to open | 'mais' for more | 'filtrar' | 'salvar [n]' | 'resumir [n]'")
        click.echo(f"{'='*60}\n")

    def display_page_content(self, page: PageContent, detailed: bool = False):
        """Display extracted page content."""
        click.echo(f"\n{'='*60}")
        click.echo(f"[1] {page.title}")
        click.echo(f"Domínio: {page.domain}")
        click.echo(f"URL: {page.url}")
        click.echo("---")
        
        summary = page.summary_detailed if detailed else page.summary_short
        click.echo(f"Resumo {'Detalhado' if detailed else 'Curto'}: {summary}")
        click.echo("---")
        
        click.echo("Trechos Principais:")
        for i, p in enumerate(page.paragraphs[:5], 1):
            click.echo(f"({page.url}#p={i}) \"{p[:200]}{'...' if len(p) > 200 else ''}\"")
        
        click.echo("---")
        click.echo("Ações Disponíveis:")
        click.echo("  [abrir-externo] - Abrir no navegador padrão")
        click.echo("  [copiar-url] - Copiar URL para área de transferência")
        click.echo("  [salvar-trecho n] - Salvar trecho número n")
        click.echo("  [voltar] - Voltar aos resultados")
        click.echo("  [buscar-links] - Buscar na página")
        click.echo("  [links] - Mostrar links da página")
        click.echo("  [resumo detalhado] - Ver resumo detalhado")
        click.echo(f"{'='*60}\n")

    def handle_command(self, command: str) -> bool:
        """
        Handle user command. Returns True to continue, False to exit.
        """
        command = command.strip().lower()

        if command in ("quit", "exit", "sair"):
            self._save_session()
            click.echo("Goodbye!")
            return False

        if command == "help":
            self._show_help()
            return True

        # Empty command
        if not command:
            return True

        # Search command
        if command.startswith("/search ") or command.startswith("/buscar "):
            query = command.split(" ", 1)[1] if " " in command else ""
            if query:
                results = self.search(query)
                self.display_results(results)
            return True

        # Number selection (open result)
        if command.isdigit():
            num = int(command)
            if 1 <= num <= len(self.session.results):
                result = self.session.results[num - 1]
                click.echo(f"Opening: {result.url}")
                page = self.fetch_and_extract_content(result.url)
                if page:
                    self.display_page_content(page)
                else:
                    click.echo("Failed to load page. Try [abrir-externo]?")
            else:
                click.echo(f"Invalid number. Choose 1-{len(self.session.results)}.")
            return True

        # Filter command
        if command.startswith("filtrar") or command.startswith("filter"):
            parts = command.split(None, 1)
            if len(parts) > 1:
                query = parts[1]
                results = self.search(query)
                self.display_results(results)
            else:
                click.echo("Usage: filtrar <query> [site:example.com] [filetype:pdf]")
            return True

        # Save result
        if command.startswith("salvar"):
            parts = command.split()
            if len(parts) >= 2 and parts[1].isdigit():
                num = int(parts[1])
                if 1 <= num <= len(self.session.results):
                    result = self.session.results[num - 1]
                    self.session.saved_snippets.append(f"{result.title}: {result.url}")
                    click.echo(f"Saved: {result.title}")
            return True

        # Summarize result
        if command.startswith("resumir"):
            parts = command.split()
            detailed = "detalhado" in command
            if len(parts) >= 2 and parts[1].isdigit():
                num = int(parts[1])
                if 1 <= num <= len(self.session.results):
                    result = self.session.results[num - 1]
                    page = self.fetch_and_extract_content(result.url)
                    if page:
                        self.display_page_content(page, detailed=detailed)
            return True

        # More results
        if command == "mais":
            if self.session.last_query:
                click.echo(f"Searching more for: {self.session.last_query}")
                results = self.search(self.session.last_query, max_results=20)
                self.display_results(results)
            else:
                click.echo("No previous search to show more results.")
            return True

        # When viewing a page
        if self.session.current_page:
            page = self.session.current_page

            if command == "voltar":
                self.session.current_page = None
                self.display_results(self.session.results)
                return True

            if command == "abrir-externo":
                import webbrowser
                webbrowser.open(page.url)
                click.echo(f"Opened in external browser: {page.url}")
                return True

            if command == "copiar-url":
                # Try to copy to clipboard
                try:
                    import subprocess
                    subprocess.run(["xclip", "-selection", "clipboard"], input=page.url.encode(), check=False)
                    click.echo("URL copied to clipboard!")
                except FileNotFoundError:
                    click.echo(f"URL: {page.url} (copy manually)")
                return True

            if command.startswith("salvar-trecho"):
                parts = command.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(page.paragraphs):
                        self.session.saved_snippets.append(page.paragraphs[idx])
                        click.echo(f"Saved snippet {parts[1]}")
                return True

            if command == "buscar-links" or command == "buscar":
                click.echo("Links encontrados na página:")
                for i, (text, url) in enumerate(page.links[:20], 1):
                    click.echo(f"  [{i}] {text} -> {url[:50]}...")
                return True

            if command == "links":
                click.echo(f"\nTodos os links ({len(page.links)}):")
                for text, url in page.links:
                    click.echo(f"  • {text}")
                    click.echo(f"    {url}")
                return True

            if "resumo detalhado" in command:
                self.display_page_content(page, detailed=True)
                return True

        # Default: treat as search query
        results = self.search(command)
        self.display_results(results)

        return True

    def _show_help(self):
        """Show help information."""
        click.echo("""
Text Browser CLI - Help
=======================

Commands:
  <number>          Open search result by number
  <query>           Search DuckDuckGo
  /search <query>   Explicit search command
  filtrar <query>   Search with filters (site:, filetype:, lang:)
  mais              Show more results from last search
  salvar [n]        Save result/snippet number n
  resumir [n]       Summarize result n
  resumir [n] detalhado  Detailed summary
  
When viewing a page:
  voltar            Return to search results
  abrir-externo     Open in default browser
  copiar-url        Copy URL to clipboard
  salvar-trecho n   Save paragraph n
  links             Show all links
  buscar-links      Search within page links
  resumo detalhado  Show detailed summary

General:
  help              Show this help
  quit/exit/sair    Exit application

Filter examples:
  python site:python.org
  manual filetype:pdf
  noticias lang:pt region:br
""")


@click.command()
@click.option("--query", "-q", help="Initial search query")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(query: Optional[str], verbose: bool):
    """
    Text-based Web Browser CLI
    
    A simplified text-mode web browser that allows searching,
    viewing, and navigating web content from the command line.
    """
    browser = TextBrowser()
    
    click.echo("="*60)
    click.echo("Text Browser CLI")
    click.echo("="*60)
    click.echo("Type 'help' for commands, 'quit' to exit")
    click.echo("="*60)

    if query:
        results = browser.search(query)
        browser.display_results(results)

    # Main loop
    while True:
        try:
            prompt = "> " if not browser.session.current_page else "[page]> "
            user_input = click.prompt(prompt, default="", show_default=False)
            
            if not user_input and query:
                # First empty input after initial query
                continue
                
            if not browser.handle_command(user_input):
                break
                
        except KeyboardInterrupt:
            click.echo("\nInterrupted. Type 'quit' to exit.")
        except EOFError:
            browser._save_session()
            click.echo("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
