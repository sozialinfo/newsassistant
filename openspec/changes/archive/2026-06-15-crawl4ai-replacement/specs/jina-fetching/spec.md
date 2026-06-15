## REMOVED Requirements

### Requirement: Jina Reader API fetching

**Reason**: Replaced by crawl4ai server (see `crawl4ai-fetching/spec.md`)
**Migration**: Switch to self-hosted crawl4ai Docker container

### Requirement: Jina fetch timeout

**Reason**: Replaced by crawl4ai timeout handling

### Requirement: Jina transient error handling

**Reason**: Replaced by crawl4ai error handling

### Requirement: Jina permanent error handling

**Reason**: Replaced by crawl4ai error handling

### Requirement: Content length truncation

**Reason**: Re-implemented in crawl4ai fetch utility (same behavior)
