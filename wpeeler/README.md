# WPeeler - Web Design DNA Extractor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**WPeeler** é uma ferramenta de análise estética que extrai a "Alma Matemática" (DNA visual) de websites. Não é um scraper de conteúdo, mas um analisador de padrões de design que retorna tipografia, escala de espaçamentos, paleta de cores e tempos de animação.

## 🚀 Instalação

```bash
pip install -r requirements.txt
```

## 📖 Uso

```bash
python main.py https://exemplo.com
```

### Opções da CLI

```
usage: main.py [-h] [--output OUTPUT] [--verbose] url

WPeeler - Web Design DNA Extractor

positional arguments:
  url            URL do site para análise

options:
  -h, --help     show this help message and exit
  --output PATH  Caminho para salvar o JSON (padrão: wpeeler_<domain>_<timestamp>.json)
  --verbose      Habilitar logs detalhados
```

## 📤 Formato de Saída

A ferramenta gera um relatório no terminal e salva um arquivo JSON com a seguinte estrutura:

```json
{
  "url": "https://exemplo.com",
  "scraped_at": "2025-04-18T10:30:00Z",
  "typography": {
    "predominant_family": "Inter, system-ui, sans-serif",
    "size_scale": {"h1": 40, "h2": 32, "h3": 24, "body": 16, "small": 14},
    "line_height_base": 1.5
  },
  "spacing": {
    "common_values_px": [8, 16, 24, 40, 80],
    "container_max_width": "1200px",
    "grid_base": 8
  },
  "colors": {
    "background": "#ffffff",
    "text_primary": "#111827",
    "accent": "#3b82f6",
    "palette_hex": ["#ffffff", "#111827", "#3b82f6", "#f3f4f6", "#9ca3af"]
  },
  "animations": {
    "hover_duration": "0.25s",
    "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
    "common_transitions": ["background-color 0.2s ease", "transform 0.25s ease-in-out"]
  }
}
```

## ⚙️ Arquitetura

```
wpeeler/
├── main.py           # CLI entrypoint
├── fetcher.py        # Download HTML + extração de CSS
├── parser.py         # Parse de CSS com tinycss2
├── analyzer.py       # Heurísticas de análise
├── models.py         # Modelos Pydantic
├── output.py         # Formatação Rich + JSON
└── utils.py          # Utilitários comuns
```

## 🔍 Limitações do MVP

1. **Análise estática**: Não executa JavaScript, portanto estilos aplicados dinamicamente não são capturados
2. **@import aninhado**: Suporte limitado a imports recursivos profundos
3. **CSS-in-JS**: Não analisa estilos injetados via JavaScript (styled-components, emotion, etc.)
4. **Variáveis CSS**: Extrai variáveis (--var) mas não resolve valores computados
5. **Conversão de unidades**: Assume 1rem = 16px e 1em = 16px (pode variar conforme contexto)
6. **Cores agrupadas**: Agrupamento por similaridade RGB com tolerância de 15%

## 🧪 Exemplos de Teste

```bash
# Analisar Stripe
python main.py https://stripe.com

# Analisar Vercel
python main.py https://vercel.com

# Com saída personalizada
python main.py https://example.com --output resultado.json --verbose
```

## 📝 Licença

MIT License
