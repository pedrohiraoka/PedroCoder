# Text Browser CLI

A command-line interface that simulates a simplified web browser, operating exclusively in text mode. Users can search the web using DuckDuckGo, view results, select pages, and navigate content with various actions like copying URLs, saving snippets, and viewing summaries.

## Features

- **Search**: Perform DuckDuckGo searches directly from the terminal
- **Results Display**: View numbered search results with titles, domains, snippets, and URLs
- **Content Extraction**: Fetch and extract main text content from web pages (removes ads, menus, etc.)
- **Summaries**: Get short or detailed summaries of page content
- **Filters**: Filter searches by site, filetype, language, and region
- **Actions**: 
  - Open pages in external browser
  - Copy URLs to clipboard
  - Save snippets/paragraphs
  - Browse links within pages
  - Return to search results
- **Session Persistence**: Saves your last query and saved snippets between sessions
- **Caching**: Caches summaries to avoid redundant requests
- **Rate Limiting**: Respects rate limits (1 second delay between requests to same host)
- **Robots.txt**: Checks robots.txt before accessing pages
- **Size Limits**: Limits page downloads to 1MB

## Installation

```bash
pip install click requests beautifulsoup4 ddgs readability-lxml lxml
```

## Usage

### Basic Usage

```bash
python text_browser.py
```

### With Initial Search Query

```bash
python text_browser.py -q "python programming"
```

### Help

```bash
python text_browser.py --help
```

## Commands

### General Commands

| Command | Description |
|---------|-------------|
| `<query>` | Search DuckDuckGo |
| `/search <query>` | Explicit search command |
| `filtrar <query>` | Search with filters |
| `mais` | Show more results from last search |
| `salvar [n]` | Save result/snippet number n |
| `resumir [n]` | Summarize result n |
| `resumir [n] detalhado` | Detailed summary of result n |
| `help` | Show help information |
| `quit` / `exit` / `sair` | Exit application |

### When Viewing a Page

| Command | Description |
|---------|-------------|
| `voltar` | Return to search results |
| `abrir-externo` | Open in default browser |
| `copiar-url` | Copy URL to clipboard |
| `salvar-trecho n` | Save paragraph n |
| `links` | Show all links on page |
| `buscar-links` | Search within page links |
| `resumo detalhado` | Show detailed summary |

### Search Filters

Use these filters in your queries:

- `site:example.com` - Search only within a specific domain
- `filetype:pdf` - Search for specific file types
- `lang:pt` - Filter by language
- `region:br` - Filter by region

**Examples:**
```
python site:python.org
manual filetype:pdf
noticias lang:pt region:br
```

## Architecture

The application is divided into several components:

- **TextBrowser**: Main application class managing session state
- **SearchResult**: Data class representing search results
- **PageContent**: Data class holding extracted page content
- **SessionContext**: Maintains session state (history, saved items, etc.)

### Key Functions

- `search(query)`: Perform DuckDuckGo search
- `fetch_and_extract_content(url)`: Fetch and extract page content
- `display_results(results)`: Show formatted search results
- `display_page_content(page)`: Show extracted page content
- `handle_command(command)`: Process user commands
- `_check_robots_txt(url)`: Check robots.txt permissions
- `_respect_rate_limit(url)`: Enforce rate limiting
- `_apply_filters(query)`: Parse search filters

## Dependencies

- `click`: CLI framework
- `requests`: HTTP library
- `beautifulsoup4`: HTML parsing
- `ddgs`: DuckDuckGo search API
- `readability-lxml`: Content extraction

## Example Session

```
$ python text_browser.py
============================================================
Text Browser CLI
============================================================
Type 'help' for commands, 'quit' to exit
============================================================
> python programming

============================================================
Search Results (10 found)
============================================================

[1] Python (programming language)
     Domain: en.wikipedia.org
     URL: https://en.wikipedia.org/wiki/Python_(programming_language)
     Python is a high-level, general-purpose programming language...

[2] Welcome to Python.org
     Domain: www.python.org
     URL: https://www.python.org/
     Python is a versatile and easy-to-learn programming language...

------------------------------------------------------------
Actions: Enter number to open | 'mais' for more | 'filtrar' | 'salvar [n]' | 'resumir [n]'
============================================================

> 2
Opening: https://www.python.org/

============================================================
[1] Welcome to Python.org
Domínio: www.python.org
URL: https://www.python.org/
---
Resumo Curto: Python is a versatile and easy-to-learn programming language...
---
Trechos Principais:
(https://www.python.org/#p=1) "Welcome to Python.org"...
---
Ações Disponíveis:
  [abrir-externo] - Abrir no navegador padrão
  [copiar-url] - Copiar URL para área de transferência
  [salvar-trecho n] - Salvar trecho número n
  [voltar] - Voltar aos resultados
  [buscar-links] - Buscar na página
  [links] - Mostrar links da página
  [resumo detalhado] - Ver resumo detalhado
============================================================

[page]> voltar
> quit
Goodbye!
```

## License

MIT License