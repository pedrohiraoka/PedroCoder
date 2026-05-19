#!/usr/bin/env python3
"""
WebTextBackup MVP - Main Entry Point
CLI interface for extracting and backing up text content from websites.
"""

import argparse
import sys
from src.cli import run_cli


def main():
    parser = argparse.ArgumentParser(
        description="WebTextBackup MVP - Extract and backup text content from websites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single page mode
  python web_backup.py --url "https://example.com/article"

  # Crawl entire site (depth 2, 2s delay)
  python web_backup.py --url "https://example.com" --mode crawl --depth 2 --delay 2

  # Custom output directory and text format
  python web_backup.py --url "https://example.com" --output ./my_backup --format txt
        """
    )

    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="The target URL to extract or crawl (required)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "crawl"],
        default="single",
        help="Operation mode: 'single' for one page, 'crawl' for entire site (default: single)"
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum crawl depth for 'crawl' mode (default: 2)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./backup_output",
        help="Output directory for saved files (default: ./backup_output)"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between requests to avoid overloading the server (default: 1.0)"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "txt"],
        default="md",
        help="Output file format: 'md' for Markdown, 'txt' for plain text (default: md)"
    )

    parser.add_argument(
        "--user-agent",
        type=str,
        default="WebTextBackupBot/1.0 (+https://github.com/webtextbackup)",
        help="Custom User-Agent string for HTTP requests (default: WebTextBackupBot/1.0)"
    )

    args = parser.parse_args()

    try:
        run_cli(args)
    except KeyboardInterrupt:
        print("\n\n>> Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
