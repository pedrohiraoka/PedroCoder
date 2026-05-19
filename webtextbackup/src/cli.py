"""
CLI Module
Handles command-line interface logic and orchestrates the backup process.
"""

import os
from argparse import Namespace

from .extractor import ContentExtractor
from .crawler import Crawler
from .utils import normalize_url, get_domain


def run_cli(args: Namespace) -> None:
    """
    Main CLI entry point that orchestrates the backup process.
    
    Args:
        args: Parsed command-line arguments
    """
    print("\n" + "=" * 60)
    print(">> WebTextBackup MVP")
    print("=" * 60)
    
    # Validate and normalize URL
    url = normalize_url(args.url)
    print(f">> Target URL: {url}")
    print(f">> Mode: {args.mode}")
    
    # Create output directory
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)
    print(f">> Output Directory: {output_dir}")
    
    # Initialize extractor
    extractor = ContentExtractor(
        user_agent=args.user_agent,
        timeout=15
    )
    
    if args.mode == 'single':
        # Single page mode
        run_single_mode(extractor, url, output_dir, args.format)
    elif args.mode == 'crawl':
        # Crawl mode
        run_crawl_mode(extractor, url, output_dir, args.depth, args.delay, args.format)
    else:
        print(f"[ERROR] Unknown mode: {args.mode}")
        return
    
    print("\n>> Operation completed successfully!")


def run_single_mode(
    extractor: ContentExtractor,
    url: str,
    output_dir: str,
    output_format: str
) -> None:
    """
    Execute single page extraction mode.
    
    Args:
        extractor: ContentExtractor instance
        url: Target URL
        output_dir: Output directory
        output_format: 'md' or 'txt'
    """
    print(f"\n>> Mode: Single Page Extraction")
    print(f">> Format: {output_format}")
    print("=" * 60)
    
    # Check robots.txt
    print(f"\n[INFO] Checking robots.txt...")
    if not extractor.check_robots_txt(url):
        print("[ERROR] Access denied by robots.txt")
        return
    print("     -> Allowed by robots.txt")
    
    # Fetch HTML
    html = extractor.fetch_html(url)
    if not html:
        print("\n[ERROR] Failed to fetch page content")
        return
    
    # Extract content
    print(f"\n[INFO] Extracting content...")
    title, content = extractor.extract_content(html, url, output_format)
    
    if not title or not content:
        print("\n[ERROR] No meaningful content could be extracted")
        print("     -> This might be a JavaScript-heavy site (not supported in MVP)")
        print("     -> Or the page has very little text content")
        return
    
    print(f"     -> Title: {title}")
    print(f"     -> Content length: {len(content)} characters")
    
    # Save file
    print(f"\n[INFO] Saving file...")
    try:
        from .utils import sanitize_filename
        
        # Generate filename from title or URL
        parsed_url = __import__('urllib.parse', fromlist=['urlparse']).urlparse(url)
        path_parts = [p for p in parsed_url.path.strip('/').split('/') if p]
        
        if path_parts:
            filename_base = path_parts[-1].split('?')[0]
            filename = sanitize_filename(filename_base)
            if not filename or filename == '.':
                filename = sanitize_filename(title)[:50]
        else:
            filename = sanitize_filename(title)[:50] if title else "page"
        
        # Ensure extension
        if not filename.endswith(f'.{output_format}'):
            filename = f"{filename.split('.')[0]}.{output_format}"
        
        file_path = os.path.join(output_dir, filename)
        
        # Prepare content with metadata
        if output_format == 'md':
            full_content = f"# {title}\n\n**Source:** {url}\n\n---\n\n{content}"
        else:
            full_content = f"{title}\n\nSource: {url}\n\n{'='*50}\n\n{content}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"     -> Saved: {file_path}")
        print(f"\n[SUCCESS] Page extracted and saved successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to save file: {e}")


def run_crawl_mode(
    extractor: ContentExtractor,
    url: str,
    output_dir: str,
    max_depth: int,
    delay: float,
    output_format: str
) -> None:
    """
    Execute crawl mode for entire site extraction.
    
    Args:
        extractor: ContentExtractor instance
        url: Root URL to start crawling
        output_dir: Output directory
        max_depth: Maximum crawl depth
        delay: Delay between requests
        output_format: 'md' or 'txt'
    """
    print(f"\n>> Mode: Site Crawl")
    print(f">> Max Depth: {max_depth}")
    print(f">> Delay: {delay}s")
    print(f">> Format: {output_format}")
    print("=" * 60)
    
    # Warn about crawl scope
    domain = get_domain(url)
    print(f"\n[INFO] Will only crawl internal links within domain: {domain}")
    print(f"[INFO] Respecting robots.txt rules")
    print(f"[INFO] Press Ctrl+C to stop at any time")
    
    # Initialize and run crawler
    crawler = Crawler(
        extractor=extractor,
        output_dir=output_dir,
        max_depth=max_depth,
        delay=delay,
        output_format=output_format
    )
    
    crawler.crawl(url)
