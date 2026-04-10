#!/usr/bin/env python3
"""
Site Cloner MVP - A Python CLI tool that wraps wget for cloning static and dynamic websites.

This module provides a command-line interface to clone websites using wget with
configurable parameters for mirroring, filtering, and error handling.

Author: MVP Site Cloner
Version: 1.0.0
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if the provided URL is well-formed.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain_name(url: str) -> str:
    """
    Extract the domain name from a URL to use as default output directory.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain name sanitized for use as directory name
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Replace invalid characters for directory names
    domain = re.sub(r'[^\w\-_]', '_', domain)
    
    return domain


def build_wget_command(
    url: str,
    output_dir: str,
    user_agent: Optional[str] = None,
    max_retries: int = 3,
    exclude_types: Optional[List[str]] = None,
    delay: int = 0,
    static_only: bool = True
) -> List[str]:
    """
    Build the wget command with all necessary arguments for site cloning.
    
    Args:
        url: The URL to clone
        output_dir: Directory to save cloned files
        user_agent: Custom User-Agent string
        max_retries: Maximum number of retries per file
        exclude_types: List of file extensions to exclude
        delay: Delay in seconds between requests
        static_only: Whether to use static-only mode
        
    Returns:
        List of command arguments for subprocess
    """
    # Base wget command with recommended parameters for mirroring
    cmd = [
        'wget',
        '--mirror',           # Turn on options suitable for mirroring
        '--convert-links',    # Convert links to make them suitable for local viewing
        '--adjust-extension', # Save HTML documents with .html extension
        '--page-requisites',  # Download all files necessary to display HTML page
        '--no-parent',        # Don't ascend to parent directory
        '-e', 'robots=off',   # Ignore robots.txt restrictions
        '--tries', str(max_retries),  # Set number of retries
        '-P', output_dir,     # Specify directory prefix
        url
    ]
    
    # Add custom User-Agent if specified
    if user_agent:
        cmd.insert(-1, '--user-agent')
        cmd.insert(-1, user_agent)
    
    # Add delay between requests if specified
    if delay > 0:
        cmd.insert(-1, '--wait')
        cmd.insert(-1, str(delay))
    
    # Add excluded file types if specified
    if exclude_types:
        reject_pattern = ','.join(exclude_types)
        cmd.insert(-1, '--reject')
        cmd.insert(-1, reject_pattern)
    
    return cmd


def check_wget_available() -> bool:
    """
    Check if wget is available in the system PATH.
    
    Returns:
        True if wget is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['wget', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def create_output_directory(output_dir: str) -> bool:
    """
    Create the output directory if it doesn't exist.
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        logger.error(f"Permission denied: Cannot create directory '{output_dir}'")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory '{output_dir}': {e}")
        return False


def execute_wget(command: List[str]) -> int:
    """
    Execute the wget command and return the exit code.
    
    Args:
        command: List of command arguments
        
    Returns:
        Exit code from wget process
    """
    try:
        logger.info(f"Executing: {' '.join(command)}")
        result = subprocess.run(
            command,
            check=False,
            timeout=None  # No timeout for long-running downloads
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        logger.error("Download timed out")
        return -1
    except KeyboardInterrupt:
        logger.warning("Download interrupted by user")
        return -2
    except Exception as e:
        logger.error(f"Error executing wget: {e}")
        return -3


def clone_site(
    url: str,
    output_dir: str,
    user_agent: Optional[str] = None,
    max_retries: int = 3,
    exclude_types: Optional[List[str]] = None,
    delay: int = 0,
    static_only: bool = True,
    dynamic_mode: bool = False
) -> int:
    """
    Main function to clone a website.
    
    Args:
        url: The URL to clone
        output_dir: Directory to save cloned files
        user_agent: Custom User-Agent string
        max_retries: Maximum number of retries per file
        exclude_types: List of file extensions to exclude
        delay: Delay in seconds between requests
        static_only: Whether to use static-only mode
        dynamic_mode: Whether to use dynamic mode (future feature)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("=" * 60)
    logger.info("Site Cloner MVP - Starting clone operation")
    logger.info("=" * 60)
    
    # Validate URL
    if not validate_url(url):
        logger.error(f"Invalid URL provided: {url}")
        return 1
    
    logger.info(f"Target URL: {url}")
    logger.info(f"Output directory: {output_dir}")
    
    # Handle dynamic mode (not yet implemented)
    if dynamic_mode:
        logger.warning("Dynamic mode is currently under development.")
        logger.warning("For dynamic sites, consider using tools like Puppeteer or Playwright.")
        logger.info("Proceeding with static cloning method...")
    
    # Check if wget is available
    if not check_wget_available():
        logger.error("wget is not installed or not in PATH. Please install wget.")
        return 2
    
    # Create output directory
    if not create_output_directory(output_dir):
        logger.error("Failed to create output directory")
        return 3
    
    logger.info(f"Directory '{output_dir}' ready")
    
    # Build wget command
    command = build_wget_command(
        url=url,
        output_dir=output_dir,
        user_agent=user_agent,
        max_retries=max_retries,
        exclude_types=exclude_types,
        delay=delay,
        static_only=static_only
    )
    
    logger.info("Starting download...")
    logger.info("-" * 60)
    
    # Execute wget
    exit_code = execute_wget(command)
    
    # Report results
    logger.info("-" * 60)
    if exit_code == 0:
        logger.info("✓ Clone completed successfully!")
        logger.info(f"Files saved to: {os.path.abspath(output_dir)}")
    elif exit_code == -2:
        logger.warning("Clone was interrupted by user")
    else:
        logger.error(f"✗ Clone failed with exit code: {exit_code}")
        logger.error("Check the error messages above for details")
    
    logger.info("=" * 60)
    
    return exit_code


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog='site_cloner',
        description='Clone/mirror websites using wget with configurable options.',
        epilog='Example: python site_cloner.py https://example.com -o ./backup --max-retries 3 --exclude-types zip,exe',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        'url',
        type=str,
        help='URL of the website to clone (required)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default=None,
        help='Output directory for cloned files (default: domain name from URL)'
    )
    
    parser.add_argument(
        '--static-only',
        action='store_true',
        default=True,
        help='Use static-only mode with optimized wget parameters (default behavior)'
    )
    
    parser.add_argument(
        '--dynamic-mode',
        action='store_true',
        help='Enable dynamic mode (currently under development)'
    )
    
    parser.add_argument(
        '--user-agent',
        type=str,
        default=None,
        help='Custom User-Agent string for wget requests'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        metavar='N',
        help='Maximum number of retries per file (default: 3)'
    )
    
    parser.add_argument(
        '--exclude-types',
        type=str,
        default=None,
        metavar='EXT1,EXT2',
        help='Comma-separated list of file extensions to exclude (e.g., zip,mp4,exe)'
    )
    
    parser.add_argument(
        '--delay',
        type=int,
        default=0,
        metavar='SECONDS',
        help='Delay in seconds between requests to be gentle with the server (default: 0)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the site cloner application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = extract_domain_name(args.url)
        logger.info(f"No output directory specified, using: {output_dir}")
    
    # Parse exclude types
    exclude_types = None
    if args.exclude_types:
        exclude_types = [ext.strip() for ext in args.exclude_types.split(',')]
        logger.debug(f"Excluding file types: {exclude_types}")
    
    # Execute clone operation
    exit_code = clone_site(
        url=args.url,
        output_dir=output_dir,
        user_agent=args.user_agent,
        max_retries=args.max_retries,
        exclude_types=exclude_types,
        delay=args.delay,
        static_only=args.static_only,
        dynamic_mode=args.dynamic_mode
    )
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
