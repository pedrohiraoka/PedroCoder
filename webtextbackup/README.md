# WebTextBackup MVP

A simple Python command-line tool to extract and backup text content from websites. Perfect for archiving, content migration, or offline reading.

## Features

- **Single Page Mode**: Extract text from a specific URL
- **Crawl Mode**: Recursively crawl and extract text from an entire website
- **Smart Content Extraction**: Automatically removes ads, navigation, footers, and other boilerplate
- **Robots.txt Respect**: Ethically checks and obeys robots.txt rules
- **Clean Output**: Saves content in Markdown or plain text format
- **Directory Mirroring**: In crawl mode, creates folder structure matching the website

## Requirements

- Python 3.8 or higher

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage - Single Page

Extract text from a single page:

```bash
python web_backup.py --url "https://example.com/article"
```

### Crawl Entire Site

Crawl a website recursively (default depth: 2):

```bash
python web_backup.py --url "https://example.com" --mode crawl
```

### Advanced Options

```bash
# Custom output directory
python web_backup.py --url "https://example.com" --output ./my_backup

# Change crawl depth
python web_backup.py --url "https://example.com" --mode crawl --depth 3

# Add delay between requests (be polite!)
python web_backup.py --url "https://example.com" --mode crawl --delay 2

# Output as plain text instead of Markdown
python web_backup.py --url "https://example.com" --format txt

# Custom User-Agent
python web_backup.py --url "https://example.com" --user-agent "MyBot/1.0"
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--url` | (required) | Target URL to extract or crawl |
| `--mode` | `single` | Operation mode: `single` or `crawl` |
| `--depth` | `2` | Maximum crawl depth (crawl mode only) |
| `--output` | `./backup_output` | Output directory for saved files |
| `--delay` | `1.0` | Delay in seconds between requests |
| `--format` | `md` | Output format: `md` (Markdown) or `txt` |
| `--user-agent` | `WebTextBackupBot/1.0` | Custom User-Agent string |

## Examples

### Example 1: Backup a Blog Post

```bash
python web_backup.py --url "https://myblog.com/my-awesome-post" --output ./blog_backup
```

Output: `./blog_backup/my-awesome-post.md`

### Example 2: Archive a Documentation Site

```bash
python web_backup.py --url "https://docs.example.com" --mode crawl --depth 3 --delay 1.5
```

Output: 
```
./backup_output/
├── index.md
├── getting-started.md
├── api/
│   ├── reference.md
│   └── endpoints.md
└── guides/
    └── tutorial.md
```

### Example 3: Quick Text Export

```bash
python web_backup.py --url "https://news.site.com/story" --format txt
```

## How It Works

1. **URL Validation**: Normalizes and validates the input URL
2. **Robots.txt Check**: Verifies if crawling is allowed
3. **Content Fetching**: Downloads HTML with proper headers
4. **Smart Extraction**: Uses [trafilatura](https://github.com/adbar/trafilatura) to identify and extract main content
5. **Cleanup**: Removes ads, navigation, scripts, styles, and other boilerplate
6. **Save**: Outputs clean Markdown or plain text file

## Limitations (MVP)

- **No JavaScript Support**: Sites that load content dynamically via JavaScript may not work properly
- **Single Domain**: Crawl mode only follows links within the same domain
- **No Authentication**: Cannot access pages requiring login
- **Rate Limiting**: Some sites may block requests if delay is too low

## Troubleshooting

### "No meaningful content could be extracted"

This usually means:
- The site loads content via JavaScript (not supported in MVP)
- The page has very little text content
- The site has unusual HTML structure

**Solution**: Try a different page or check if the site has a mobile/AMP version.

### "Access denied by robots.txt"

The website explicitly blocks bots from accessing certain pages.

**Solution**: Respect the robots.txt rules. You cannot bypass this ethically.

### Connection errors or timeouts

- Increase the delay: `--delay 3`
- Check your internet connection
- The target server might be temporarily unavailable

### Empty or incomplete output

- The site might use heavy JavaScript
- Try increasing timeout (edit `extractor.py`)
- Some sites have anti-bot measures

## Ethical Considerations

⚠️ **Important**: This tool is designed for ethical web scraping:

1. **Respects robots.txt**: Automatically checks and obeys rules
2. **Polite crawling**: Uses delays between requests to avoid overloading servers
3. **Clear identification**: Uses identifiable User-Agent string
4. **Personal use only**: You are responsible for compliance with copyright laws

**Do not use this tool to:**
- Scrape copyrighted content for redistribution
- Overload servers with aggressive crawling
- Bypass access controls or authentication
- Collect personal data without consent

## License

MIT License - See LICENSE file for details

## Contributing

This is an MVP. Contributions welcome for:
- JavaScript rendering support (optional)
- Better error handling
- Additional output formats
- Progress bars and better UI

## Changelog

### v0.1.0 (MVP)
- Initial release
- Single page extraction
- Site crawling with depth control
- Markdown and text output
- Robots.txt compliance
