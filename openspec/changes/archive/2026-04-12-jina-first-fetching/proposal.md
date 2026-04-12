## Why

JavaScript-heavy news sources (e.g., Gatsby, Next.js SPAs) return empty article lists because the content is rendered client-side. Direct HTTP fetching only retrieves the app shell, not the actual articles. The Jina Reader API executes JavaScript and returns rendered content, solving this reliably. Currently Jina is only used as a fallback for 403 errors on individual articles, but it should be the primary fetch method for all pages.

## What Changes

- **Jina-first fetching**: All page fetches (listing pages and article pages) will use Jina Reader API as the primary method
- **Unified fetch utility**: New `fetch_page()` function centralizes all page fetching logic
- **Markdown input to AI**: AI prompts updated to accept markdown content (Jina's output format) instead of HTML
- **HTML output preserved**: Article `content` field continues to store HTML for display (AI converts markdown to HTML)
- **Remove direct HTTP fetching**: No fallback to `requests.get()` - Jina is required
- **Remove HTML cleaning**: `clean_html()` and BeautifulSoup no longer needed (Jina returns clean markdown)
- **Remove PDF handling**: Jina handles PDFs natively, `pdfminer` dependency removed
- **JINA_API_KEY required**: Environment variable becomes mandatory for the scraping pipeline

## Capabilities

### New Capabilities

- `jina-fetching`: Unified page fetching via Jina Reader API with markdown output

### Modified Capabilities

- `scraping-pipeline`: Fetching method changes from direct HTTP to Jina, input format changes from HTML to markdown

## Impact

- **Code**: `news_source.py` and `news_article.py` significantly simplified
- **Dependencies**: Can remove `pdfminer.six` from requirements; `beautifulsoup4` and `lxml` may become optional (check other usages)
- **Configuration**: `JINA_API_KEY` environment variable now required (was optional fallback)
- **API costs**: All fetches now go through Jina API (increased usage vs. free direct HTTP)
