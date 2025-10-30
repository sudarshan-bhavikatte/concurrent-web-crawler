# Design Document: Concurrent Web Crawler + Indexer

## Overview

The Concurrent Web Crawler + Indexer is a Python-based asynchronous web crawling system that fetches web pages, extracts content and links, and stores indexed data in a SQLite database. The system uses asyncio for concurrency, aiohttp for HTTP requests, and BeautifulSoup for HTML parsing.

The architecture follows a modular design with four main components:
- **Fetcher**: Handles HTTP requests asynchronously
- **Parser**: Extracts content and links from HTML
- **Queue Manager**: Manages URL queue and visited tracking
- **Indexer**: Persists crawled data to SQLite

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Crawler System                          │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ CLI Handler  │─────▶│Queue Manager │                   │
│  └──────────────┘      └──────┬───────┘                   │
│                               │                            │
│                               ▼                            │
│                    ┌──────────────────┐                   │
│                    │  Crawler Engine  │                   │
│                    │  (asyncio tasks) │                   │
│                    └────────┬─────────┘                   │
│                             │                             │
│              ┌──────────────┼──────────────┐             │
│              ▼              ▼              ▼             │
│         ┌─────────┐    ┌────────┐    ┌─────────┐       │
│         │ Fetcher │───▶│ Parser │───▶│ Indexer │       │
│         └─────────┘    └────────┘    └────┬────┘       │
│              │                              │            │
│              ▼                              ▼            │
│         ┌─────────┐                   ┌─────────┐       │
│         │ aiohttp │                   │ SQLite  │       │
│         └─────────┘                   └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Concurrency Model

The system uses asyncio's event loop with the following concurrency controls:
- **Semaphore**: Limits concurrent HTTP requests (default: 10)
- **Rate Limiter**: Per-domain rate limiting using token bucket algorithm
- **Task Pool**: Dynamic task creation for URL processing

### Data Flow

1. User provides starting URL via CLI
2. Queue Manager initializes with starting URL
3. Crawler Engine spawns worker tasks up to concurrency limit
4. Each worker:
   - Dequeues URL from Queue Manager
   - Fetcher retrieves page content
   - Parser extracts text and links
   - Indexer stores content in database
   - Parser's discovered links added to Queue Manager
5. Process continues until queue is empty

## Components and Interfaces

### 1. Queue Manager

**Responsibility**: Manage URL queue, track visited URLs, enforce crawl depth and domain restrictions.

**Interface**:
```python
class QueueManager:
    def __init__(self, start_url: str, max_depth: Optional[int] = None, 
                 allowed_domain: Optional[str] = None):
        """Initialize queue with starting URL and constraints."""
        
    async def get_next_url(self) -> Optional[Tuple[str, int]]:
        """Get next URL to crawl with its depth. Returns None if queue empty."""
        
    async def add_urls(self, urls: List[str], current_depth: int) -> None:
        """Add discovered URLs to queue if not visited and within constraints."""
        
    def mark_visited(self, url: str) -> None:
        """Mark URL as visited to prevent re-crawling."""
        
    def is_empty(self) -> bool:
        """Check if queue has remaining URLs."""
        
    def get_stats(self) -> Dict[str, int]:
        """Return statistics: queued, visited, failed."""
```

**Implementation Details**:
- Use `asyncio.Queue` for thread-safe URL queue
- Use `set` for O(1) visited URL lookups
- Store URLs with depth information: `(url, depth)`
- Normalize URLs before adding (lowercase, remove fragments)
- Filter URLs based on domain restriction if specified

### 2. Fetcher Component

**Responsibility**: Fetch web pages asynchronously with error handling and retries.

**Interface**:
```python
class Fetcher:
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """Initialize fetcher with timeout and retry settings."""
        
    async def fetch(self, url: str) -> FetchResult:
        """Fetch URL and return result with content or error."""
        
    async def close(self) -> None:
        """Close aiohttp session."""
```

**Data Structures**:
```python
@dataclass
class FetchResult:
    url: str
    success: bool
    status_code: Optional[int]
    content: Optional[str]
    error: Optional[str]
    fetch_time: float
```

**Implementation Details**:
- Use single `aiohttp.ClientSession` shared across all requests
- Set User-Agent: "ConcurrentCrawler/1.0"
- Implement exponential backoff: 1s, 2s, 4s for retries
- Handle common exceptions: `ClientError`, `TimeoutError`, `asyncio.TimeoutError`
- Only fetch HTML content (check Content-Type header)
- Limit response size to 10MB to prevent memory issues

### 3. Parser Component

**Responsibility**: Extract title, text content, and links from HTML.

**Interface**:
```python
class Parser:
    def __init__(self, base_url: str):
        """Initialize parser with base URL for link resolution."""
        
    def parse(self, html: str, page_url: str) -> ParseResult:
        """Parse HTML and extract structured data."""
```

**Data Structures**:
```python
@dataclass
class ParseResult:
    title: str
    text_content: str
    keywords: List[str]
    links: List[str]
```

**Implementation Details**:
- Use BeautifulSoup with 'html.parser'
- Extract title from `<title>` tag
- Extract text from body, excluding `<script>` and `<style>` tags
- Generate keywords: extract top 10 most frequent words (excluding stop words)
- Extract links from `<a href>` attributes
- Convert relative URLs to absolute using `urllib.parse.urljoin`
- Filter out non-HTTP(S) URLs (mailto:, javascript:, etc.)
- Normalize URLs (remove fragments, lowercase scheme/domain)

### 4. Indexer Component

**Responsibility**: Store crawled data in SQLite database.

**Interface**:
```python
class Indexer:
    def __init__(self, db_path: str = "crawler_index.db"):
        """Initialize indexer and create database schema."""
        
    async def index_page(self, url: str, title: str, keywords: List[str], 
                        text_preview: str) -> None:
        """Store or update page in database."""
        
    async def close(self) -> None:
        """Close database connection."""
```

**Implementation Details**:
- Use `aiosqlite` for async database operations
- Create index on URL column for fast lookups
- Store text preview (first 500 characters) instead of full content
- Use UPSERT (INSERT OR REPLACE) to handle duplicate URLs
- Store keywords as JSON array

### 5. Rate Limiter

**Responsibility**: Enforce per-domain rate limits.

**Interface**:
```python
class RateLimiter:
    def __init__(self, requests_per_second: float = 5.0):
        """Initialize rate limiter with requests per second limit."""
        
    async def acquire(self, domain: str) -> None:
        """Wait if necessary to respect rate limit for domain."""
```

**Implementation Details**:
- Use token bucket algorithm per domain
- Track last request time per domain in dictionary
- Calculate required delay: `max(0, min_interval - time_since_last)`
- Use `asyncio.sleep()` for delays

### 6. Crawler Engine

**Responsibility**: Orchestrate crawling process with worker tasks.

**Interface**:
```python
class CrawlerEngine:
    def __init__(self, queue_manager: QueueManager, fetcher: Fetcher,
                 parser: Parser, indexer: Indexer, rate_limiter: RateLimiter,
                 concurrency: int = 10):
        """Initialize crawler with components and concurrency limit."""
        
    async def crawl(self) -> CrawlStats:
        """Start crawling process and return statistics."""
        
    async def _worker(self) -> None:
        """Worker coroutine that processes URLs from queue."""
```

**Data Structures**:
```python
@dataclass
class CrawlStats:
    pages_fetched: int
    pages_failed: int
    pages_indexed: int
    elapsed_time: float
```

**Implementation Details**:
- Use `asyncio.Semaphore` to limit concurrent workers
- Create worker tasks dynamically as URLs become available
- Each worker loops: get URL → fetch → parse → index → add links
- Graceful shutdown on Ctrl+C (SIGINT)
- Aggregate statistics from all workers

### 7. CLI Handler

**Responsibility**: Parse command-line arguments and initialize crawler.

**Interface**:
```python
def main() -> None:
    """Entry point for CLI."""
```

**Implementation Details**:
- Use `argparse` for argument parsing
- Required argument: `start_url`
- Optional arguments:
  - `--max-depth`: Maximum crawl depth (default: unlimited)
  - `--domain`: Restrict crawling to domain (default: no restriction)
  - `--concurrency`: Concurrent requests (default: 10)
  - `--rate-limit`: Requests per second per domain (default: 5)
  - `--db-path`: Database file path (default: crawler_index.db)
  - `--timeout`: Request timeout in seconds (default: 10)
- Setup logging with INFO level to console
- Run crawler with `asyncio.run()`

## Data Models

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    keywords TEXT,  -- JSON array
    text_preview TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_url ON pages(url);
CREATE INDEX IF NOT EXISTS idx_crawled_at ON pages(crawled_at);
```

### In-Memory Data Structures

- **URL Queue**: `asyncio.Queue[Tuple[str, int]]` - (url, depth) pairs
- **Visited Set**: `Set[str]` - normalized URLs
- **Domain Rate Tracking**: `Dict[str, float]` - domain → last request timestamp
- **Statistics**: Atomic counters using `asyncio.Lock` for thread safety

## Error Handling

### Error Categories and Strategies

1. **Network Errors** (DNS, connection, timeout)
   - Strategy: Retry with exponential backoff (max 3 attempts)
   - Logging: Log at WARNING level with URL and error type
   - Recovery: Continue with next URL

2. **HTTP Errors** (4xx, 5xx status codes)
   - Strategy: No retry for 4xx, retry once for 5xx
   - Logging: Log at INFO level with status code
   - Recovery: Continue with next URL

3. **Parsing Errors** (malformed HTML, encoding issues)
   - Strategy: No retry, skip page
   - Logging: Log at WARNING level with URL
   - Recovery: Continue with next URL

4. **Database Errors** (write failures, disk full)
   - Strategy: Retry once after 1 second delay
   - Logging: Log at ERROR level
   - Recovery: If retry fails, continue crawling but log data loss

5. **System Errors** (out of memory, file descriptor limit)
   - Strategy: Graceful shutdown
   - Logging: Log at CRITICAL level
   - Recovery: Save current state and exit

### Error Tracking

- Maintain error counters by category
- Include error summary in final statistics
- Optionally write failed URLs to separate file for retry

## Testing Strategy

### Unit Tests

1. **Queue Manager Tests**
   - Test URL normalization
   - Test depth limiting
   - Test domain filtering
   - Test duplicate prevention

2. **Parser Tests**
   - Test link extraction with various HTML structures
   - Test relative URL resolution
   - Test keyword extraction
   - Test handling of malformed HTML

3. **Rate Limiter Tests**
   - Test delay calculation
   - Test per-domain isolation
   - Test concurrent access

4. **Indexer Tests**
   - Test database schema creation
   - Test UPSERT behavior
   - Test keyword JSON serialization

### Integration Tests

1. **End-to-End Crawl Test**
   - Create local test HTML files
   - Run crawler on local file:// URLs
   - Verify all pages indexed correctly

2. **Concurrency Test**
   - Mock HTTP server with delays
   - Verify concurrent requests respect limit
   - Verify rate limiting works

3. **Error Handling Test**
   - Mock server returning various error codes
   - Verify retry logic
   - Verify crawler continues after errors

### Performance Testing

- Benchmark crawl speed (pages/second)
- Monitor memory usage during large crawls
- Test with various concurrency levels
- Profile with cProfile to identify bottlenecks

## Performance Considerations

### Optimization Strategies

1. **Connection Pooling**: Single aiohttp session reuses connections
2. **DNS Caching**: aiohttp handles DNS caching automatically
3. **Memory Management**: 
   - Limit response size to 10MB
   - Store only text preview in database
   - Clear parsed HTML from memory after processing
4. **Database Performance**:
   - Use batch inserts if indexing many pages
   - Create indexes on frequently queried columns
   - Use WAL mode for better concurrent write performance

### Scalability Limits

- Single-process design suitable for ~10,000 pages
- For larger crawls, consider:
  - Distributed queue (Redis, RabbitMQ)
  - Multiple crawler instances
  - Separate indexing service
  - PostgreSQL instead of SQLite

## Configuration

### Default Configuration

```python
DEFAULT_CONFIG = {
    'concurrency': 10,
    'rate_limit': 5.0,  # requests per second
    'timeout': 10,  # seconds
    'max_retries': 3,
    'max_response_size': 10 * 1024 * 1024,  # 10MB
    'user_agent': 'ConcurrentCrawler/1.0',
    'db_path': 'crawler_index.db',
}
```

### Environment Variables

- `CRAWLER_CONCURRENCY`: Override default concurrency
- `CRAWLER_RATE_LIMIT`: Override default rate limit
- `CRAWLER_DB_PATH`: Override default database path

## Logging

### Log Levels

- **DEBUG**: Detailed flow information (URL queue operations)
- **INFO**: Progress updates (URL fetched, page indexed)
- **WARNING**: Recoverable errors (fetch failures, parse errors)
- **ERROR**: Serious errors (database failures)
- **CRITICAL**: System failures requiring shutdown

### Log Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Log Output

- Console: INFO and above
- Optional file logging for DEBUG level

## Security Considerations

1. **robots.txt**: Not implemented in MVP, but should be added
2. **URL Validation**: Filter javascript:, data:, and other dangerous schemes
3. **Resource Limits**: Enforce timeout and response size limits
4. **SQL Injection**: Use parameterized queries (handled by aiosqlite)
5. **Path Traversal**: Validate database path is within allowed directory

## Future Enhancements

1. **robots.txt Support**: Respect crawl directives
2. **Sitemap Support**: Parse and prioritize sitemap URLs
3. **JavaScript Rendering**: Use Playwright for SPA crawling
4. **Content Deduplication**: Hash-based duplicate detection
5. **Elasticsearch Integration**: Full-text search capabilities
6. **Distributed Crawling**: Multi-instance coordination
7. **Politeness Policies**: Configurable crawl delays per domain
8. **Resume Capability**: Save/restore crawler state
9. **Web UI**: Dashboard for monitoring and results browsing
10. **Export Formats**: JSON, CSV export of indexed data
