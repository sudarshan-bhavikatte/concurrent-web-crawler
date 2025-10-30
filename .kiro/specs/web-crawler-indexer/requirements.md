# Requirements Document

## Introduction

This document specifies the requirements for a concurrent web crawler and indexer system. The system shall fetch web pages asynchronously, extract content and links, maintain a queue of URLs to visit, and store indexed content in a database. The crawler shall respect concurrency limits and rate limiting while providing visibility into crawling progress.

## Glossary

- **Crawler System**: The complete web crawling and indexing application
- **Fetcher Component**: The module responsible for retrieving web pages via HTTP
- **Parser Component**: The module responsible for extracting text and links from HTML
- **Indexer Component**: The module responsible for storing extracted content in the database
- **Queue Manager**: The module responsible for managing unvisited URLs and tracking visited URLs
- **Concurrency Limit**: The maximum number of simultaneous HTTP requests
- **Rate Limit**: The maximum number of requests per time period to a domain
- **Crawl Depth**: The maximum number of link hops from the starting URL

## Requirements

### Requirement 1

**User Story:** As a developer, I want to set up the project environment with necessary dependencies, so that I can begin implementing the crawler system.

#### Acceptance Criteria

1. THE Crawler System SHALL use Python as the implementation language
2. THE Crawler System SHALL include aiohttp library for asynchronous HTTP requests
3. THE Crawler System SHALL include beautifulsoup4 library for HTML parsing
4. THE Crawler System SHALL include asyncio library for concurrency management
5. THE Crawler System SHALL include sqlite3 library for data persistence

### Requirement 2

**User Story:** As a developer, I want to fetch web pages asynchronously, so that the crawler can retrieve multiple pages concurrently.

#### Acceptance Criteria

1. WHEN a URL is dequeued for fetching, THE Fetcher Component SHALL send an HTTP GET request using aiohttp
2. IF an HTTP request times out after 10 seconds, THEN THE Fetcher Component SHALL log the timeout error and mark the URL as failed
3. IF an HTTP request returns a non-2xx status code, THEN THE Fetcher Component SHALL log the error status and mark the URL as failed
4. WHEN an HTTP request succeeds, THE Fetcher Component SHALL return the response body and status code
5. THE Fetcher Component SHALL set a User-Agent header identifying the crawler

### Requirement 3

**User Story:** As a developer, I want to parse HTML content to extract text and links, so that the crawler can index content and discover new pages.

#### Acceptance Criteria

1. WHEN HTML content is received, THE Parser Component SHALL extract the page title
2. WHEN HTML content is received, THE Parser Component SHALL extract text content from the body
3. WHEN HTML content is received, THE Parser Component SHALL extract all hyperlinks
4. WHEN a hyperlink is extracted, THE Parser Component SHALL normalize the URL to absolute form
5. WHEN a hyperlink is extracted, THE Parser Component SHALL filter out non-HTTP and non-HTTPS URLs

### Requirement 4

**User Story:** As a developer, I want to manage a queue of URLs to visit, so that the crawler can systematically explore web pages without revisiting them.

#### Acceptance Criteria

1. THE Queue Manager SHALL maintain a queue of unvisited URLs
2. THE Queue Manager SHALL maintain a set of visited URLs to prevent duplicate visits
3. WHEN a new URL is discovered, THE Queue Manager SHALL add it to the queue only if it has not been visited
4. WHEN the Fetcher Component requests work, THE Queue Manager SHALL provide the next unvisited URL
5. WHEN a URL fetch completes, THE Queue Manager SHALL mark the URL as visited

### Requirement 5

**User Story:** As a developer, I want to control concurrency, so that the crawler does not overwhelm target servers or exhaust system resources.

#### Acceptance Criteria

1. THE Crawler System SHALL limit concurrent HTTP requests using asyncio.Semaphore
2. THE Crawler System SHALL accept a configurable concurrency limit parameter with a default value of 10
3. WHEN the concurrency limit is reached, THE Crawler System SHALL queue additional fetch requests until capacity becomes available
4. THE Crawler System SHALL respect a configurable rate limit per domain measured in requests per second
5. WHEN a domain rate limit is approached, THE Crawler System SHALL delay requests to that domain

### Requirement 6

**User Story:** As a developer, I want to store indexed content in a database, so that crawled data can be persisted and queried.

#### Acceptance Criteria

1. THE Indexer Component SHALL store each crawled page in a SQLite database
2. WHEN storing a page, THE Indexer Component SHALL record the URL, title, and extracted keywords
3. THE Indexer Component SHALL prevent duplicate entries for the same URL
4. WHEN a URL is already indexed, THE Indexer Component SHALL update the existing record
5. THE Indexer Component SHALL create the database schema automatically if it does not exist

### Requirement 7

**User Story:** As a user, I want to start the crawler with command-line arguments, so that I can specify the starting URL and crawl parameters.

#### Acceptance Criteria

1. THE Crawler System SHALL accept a starting URL as a required command-line argument
2. WHERE a maximum crawl depth is specified, THE Crawler System SHALL stop following links beyond that depth
3. WHERE a domain restriction is specified, THE Crawler System SHALL only crawl URLs within that domain
4. WHERE a concurrency limit is specified, THE Crawler System SHALL use that value instead of the default
5. THE Crawler System SHALL display help text when invoked with a help flag

### Requirement 8

**User Story:** As a user, I want to see crawling progress and statistics, so that I can monitor the crawler's operation.

#### Acceptance Criteria

1. WHILE the crawler is running, THE Crawler System SHALL log each URL as it is fetched
2. WHILE the crawler is running, THE Crawler System SHALL log errors with sufficient detail for debugging
3. WHEN the crawl completes, THE Crawler System SHALL display the total number of pages fetched
4. WHEN the crawl completes, THE Crawler System SHALL display the total number of errors encountered
5. WHEN the crawl completes, THE Crawler System SHALL display the elapsed time

### Requirement 9

**User Story:** As a developer, I want the crawler to handle errors gracefully, so that temporary failures do not stop the entire crawl.

#### Acceptance Criteria

1. IF a fetch operation fails, THEN THE Crawler System SHALL retry the request up to 3 times with exponential backoff
2. IF a fetch operation fails after all retries, THEN THE Crawler System SHALL log the failure and continue with other URLs
3. IF a parsing operation fails, THEN THE Crawler System SHALL log the error and continue with other URLs
4. IF a database operation fails, THEN THE Crawler System SHALL log the error and continue with other URLs
5. THE Crawler System SHALL continue running until the URL queue is empty or a stop signal is received

### Requirement 10

**User Story:** As a developer, I want the project to be well-documented and packaged, so that others can understand and use the crawler.

#### Acceptance Criteria

1. THE Crawler System SHALL include a README file with usage instructions
2. THE Crawler System SHALL include a requirements.txt file listing all dependencies
3. THE Crawler System SHALL include example output showing indexed results
4. THE Crawler System SHALL include docstrings for all public functions and classes
5. THE Crawler System SHALL follow PEP 8 style guidelines for Python code
