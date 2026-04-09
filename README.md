# Async Web Scraper

Um MVP (Produto Mínimo Viável) de Web Scraping em Python que é **modular**, **assíncrono**, **configurável** e **escalável**. Este projeto representa uma melhoria significativa em relação às abordagens básicas vistas em tutoriais tradicionais.

## Características Principais

- ✅ **Configuração Centralizada**: Configure URLs, headers, seletores CSS, e mais via arquivos YAML ou JSON
- ✅ **Execução Assíncrona**: Utiliza `asyncio` e `aiohttp` para scraping eficiente de múltiplas páginas simultaneamente
- ✅ **Parsing Flexível**: BeautifulSoup4 para parsing de HTML com suporte a seletores CSS avançados
- ✅ **Extração Configurável**: Defina quais dados extrair usando seletores CSS personalizados
- ✅ **Armazenamento Versátil**: Exporte dados para JSON ou CSV
- ✅ **Tratamento Robusto de Erros**: Lida com timeouts, erros de rede, 404, e erros de parsing
- ✅ **Logging Detalhado**: Registre eventos, requisições, e erros para debugging e monitoramento
- ✅ **Modo Crawling**: Opcionalmente siga links para scrapear múltiplas páginas automaticamente

## Instalação

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

### Instalando Dependências

```bash
pip install -r requirements.txt
```

Ou instale manualmente:

```bash
pip install aiohttp beautifulsoup4 lxml pyyaml
```

## Estrutura do Projeto

```
workspace/
├── scraper/
│   ├── __init__.py      # Pacote principal
│   ├── config.py        # Módulo de configuração
│   ├── parser.py        # Módulo de parsing HTML
│   ├── scraper.py       # Scraper assíncrono principal
│   ├── storage.py       # Módulo de armazenamento
│   └── main.py          # Interface de linha de comando
├── config.yaml          # Exemplo de configuração YAML
├── config.json          # Exemplo de configuração JSON
├── requirements.txt     # Dependências do projeto
└── README.md            # Este arquivo
```

## Uso Básico

### Via Linha de Comando

```bash
# Usando configuração YAML
python -m scraper.main --config config.yaml

# Usando configuração JSON
python -m scraper.main --config config.json

# Com output verbose
python -m scraper.main --config config.yaml --verbose

# Sobrescrevendo arquivo de saída
python -m scraper.main --config config.yaml --output resultados.json

# Modo crawling (segue links)
python -m scraper.main --config config.yaml --crawl --max-pages 50
```

### Via Código Python

```python
import asyncio
from scraper import AsyncScraper, ScraperConfig

# Carregar configuração
config = ScraperConfig.load('config.yaml')

# Criar scraper
scraper = AsyncScraper(config)

# Executar scraping
async def main():
    results = await scraper.scrape_all()
    
    # Salvar resultados
    output_path = scraper.save_results()
    print(f"Dados salvos em: {output_path}")
    
    # Ver estatísticas
    stats = scraper.get_stats()
    print(f"Páginas scrapeadas: {stats['pages_scraped']}")
    print(f"Taxa de sucesso: {stats['success_rate']:.1%}")

# Executar
asyncio.run(main())
```

## Configuração

### Arquivo YAML de Exemplo

```yaml
# URLs para scraping
urls:
  - https://example.com/page1
  - https://example.com/page2

# Headers HTTP personalizados
headers:
  User-Agent: "Mozilla/5.0 (compatible; MyScraper/1.0)"
  Accept-Language: "en-US,en;q=0.9"

# Delay entre requisições (segundos)
delay: 1.0

# Timeout da requisição (segundos)
timeout: 30

# Seletores CSS para extração de dados
selectors:
  title: "h1"
  content: ".article-content"
  links: "a[href]:all"
  image: ".main-image:attr:src"

# Seguir links (modo crawling)
follow_links: false

# Seletores para extrair links
link_selectors:
  - "a[href]"

# Máximo de requisições concorrentes
max_concurrent: 5

# Arquivo de saída
output_file: "output/data.json"

# Formato de saída: 'json' ou 'csv'
output_format: "json"
```

### Sintaxe dos Seletores

O scraper suporta sintaxes especiais para extração flexível:

| Sintaxe | Descrição | Exemplo |
|---------|-----------|---------|
| `selector` | Extrai texto (padrão) | `title: "h1"` |
| `selector:text` | Extrai texto explicitamente | `content: "p:text"` |
| `selector:html` | Extrai HTML interno | `body: ".article:html"` |
| `selector:attr:name` | Extrai atributo | `image: "img:attr:src"` |
| `selector:all` | Extrai múltiplos elementos | `links: "a:all"` |

## Módulos

### `config.py`
Gerencia carregamento e validação de configuração a partir de arquivos YAML ou JSON.

### `parser.py`
Responsável por parsear HTML e extrair dados usando BeautifulSoup4 com seletores CSS configuráveis.

### `scraper.py`
Implementa o scraper assíncrono principal com:
- Requisições HTTP concorrentes com limite configurável
- Tratamento robusto de erros
- Suporte a crawling (seguir links)
- Estatísticas de execução

### `storage.py`
Gerencia armazenamento de dados em formatos JSON ou CSV.

### `main.py`
Interface de linha de comando para execução fácil do scraper.

## Exemplo de Saída

### JSON

```json
[
  {
    "title": "A Light in the Attic",
    "price": "£51.77",
    "availability": "In stock",
    "description": "There's something inside...",
    "category": "Poetry",
    "rating": "Three",
    "_url": "https://books.toscrape.com/...",
    "_scraped_at": "2024-01-15 10:30:45"
  }
]
```

### CSV

```csv
title,price,availability,description,category,rating,_url,_scraped_at
"A Light in the Attic",£51.77,In stock,"There's something...",Poetry,Three,https://...,2024-01-15 10:30:45
```

## Vantagens sobre Abordagens Síncronas

| Característica | Síncrono | Assíncrono (Este Projeto) |
|---------------|----------|---------------------------|
| Requisições simultâneas | ❌ Uma por vez | ✅ Múltiplas concurrentes |
| Tempo para N páginas | N × tempo_médio | ≈ tempo_médio + overhead |
| Uso de recursos | Baixo | Otimizado |
| Escalabilidade | Limitada | Alta |

## Tratamento de Erros

O scraper lida gracefulmente com:
- ⏱️ Timeouts de rede
- 🔌 Erros de conexão
- 📄 Páginas não encontradas (404)
- 🚫 Erros HTTP (500, 502, etc.)
- 🧩 Erros de parsing HTML

Todos os erros são logados e o scraping continua para as URLs restantes.

## Boas Práticas

1. **Respeite os servidores**: Use delays adequados entre requisições
2. **Verifique robots.txt**: Sempre verifique `/robots.txt` do site alvo
3. **Use headers apropriados**: Identifique seu scraper claramente
4. **Monitore logs**: Use logging verbose para debugging
5. **Teste seletores**: Valide seletores CSS antes de scraping em larga escala

## Limitações

- Não suporta JavaScript rendering (para sites SPA, considere Selenium ou Playwright)
- Parsing XPath não implementado (apenas seletores CSS)
- Não inclui autenticação complexa (cookies, OAuth, etc.)

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

## Licença

MIT License - Sinta-se livre para usar e modificar.

## Referências

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
