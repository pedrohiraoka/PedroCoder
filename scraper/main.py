"""
Command-line interface for the async web scraper.
Provides a simple way to run the scraper from the terminal.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import AsyncScraper, ConfigError, ScraperConfig


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Async Web Scraper - A modular, configurable web scraping tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with config file
  python -m scraper.main --config config.yaml
  
  # Verbose output
  python -m scraper.main --config config.json --verbose
  
  # Override output file
  python -m scraper.main --config config.yaml --output results.json
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help='Path to configuration file (YAML or JSON)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Override output file path from config'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    parser.add_argument(
        '--crawl',
        action='store_true',
        help='Enable crawling mode (follow links)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum pages to crawl (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = ScraperConfig.load(args.config)
        
        # Override output file if specified
        if args.output:
            config.output_file = args.output
            logger.info(f"Output file overridden: {args.output}")
        
        # Enable crawling if requested
        if args.crawl:
            config.follow_links = True
            logger.info("Crawling mode enabled")
        
        # Create and run scraper
        scraper = AsyncScraper(config)
        
        logger.info("Starting scraper...")
        
        if args.crawl:
            # Run in crawl mode
            results = asyncio.run(
                scraper.scrape_with_crawl(max_pages=args.max_pages)
            )
        else:
            # Run in basic mode
            results = asyncio.run(scraper.scrape_all())
        
        # Save results
        output_path = scraper.save_results()
        logger.info(f"Results saved to {output_path}")
        
        # Print statistics
        stats = scraper.get_stats()
        print("\n" + "=" * 50)
        print("SCRAPING STATISTICS")
        print("=" * 50)
        print(f"Pages scraped:     {stats['pages_scraped']}")
        print(f"Pages failed:      {stats['pages_failed']}")
        print(f"Success rate:      {stats['success_rate']:.1%}")
        if 'elapsed_time' in stats:
            print(f"Elapsed time:      {stats['elapsed_time']:.2f}s")
        print("=" * 50)
        
        # Exit with error code if there were failures
        if stats['pages_failed'] > 0:
            logger.warning(f"{stats['pages_failed']} pages failed to scrape")
            sys.exit(1)
        
        sys.exit(0)
        
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(3)


if __name__ == '__main__':
    main()
