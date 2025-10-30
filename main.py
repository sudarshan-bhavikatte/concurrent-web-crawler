"""
Concurrent Web Crawler and Indexer
Main CLI entry point for the crawler system.
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the crawler system.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Concurrent Web Crawler and Indexer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --max-depth 2 --concurrency 5
  %(prog)s https://example.com --domain example.com --rate-limit 10
        """
    )
    
    # Required arguments
    parser.add_argument(
        'start_url',
        help='Starting URL for the crawler'
    )
    
    # Optional arguments
    parser.add_argument(
        '--max-depth',
        type=int,
        default=None,
        help='Maximum crawl depth (default: unlimited)'
    )
    
    parser.add_argument(
        '--domain',
        type=str,
        default=None,
        help='Restrict crawling to this domain (default: no restriction)'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=10,
        help='Maximum concurrent requests (default: 10)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=5.0,
        help='Requests per second per domain (default: 5.0)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='crawler_index.db',
        help='Database file path (default: crawler_index.db)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    return parser.parse_args()


async def main_async(args: argparse.Namespace) -> None:
    """
    Main asynchronous entry point for the crawler.
    
    Args:
        args: Parsed command-line arguments
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting crawler with URL: {args.start_url}")
    logger.info(f"Configuration: concurrency={args.concurrency}, "
                f"rate_limit={args.rate_limit}, max_depth={args.max_depth}")
    
    # TODO: Initialize components and start crawling
    # This will be implemented in subsequent tasks
    logger.info("Crawler initialization complete")


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Run the crawler
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logging.info("Crawler interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Crawler failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
