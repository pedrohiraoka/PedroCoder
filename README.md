# MVP Crawler/Web Scraper - Arquitetura de Dados

```
/workspace/
├── config/
│   └── sites.yaml           # Configuração de seletores por domínio
├── src/
│   ├── __init__.py
│   ├── crawler.py           # Gerenciamento de fila, HTTP, delays, robots.txt
│   ├── parser.py            # Extração com BeautifulSoup, mapeamento para schema
│   ├── models.py            # Pydantic models (Company, Contact, Service, Price)
│   ├── storage.py           # Salvamento em SQLite/CSV/JSON
│   ├── utils.py             # Normalização, logging, retries, helpers
│   └── cli.py               # Interface de linha de comando
├── tests/
│   ├── __init__.py
│   ├── test_parser.py       # Testes de parsing
│   └── test_models.py       # Testes de validação
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
└── README.md                # Documentação e instruções
```

## 📋 VISÃO GERAL

Este MVP implementa um crawler/web scraper ético e modular com:
- **Gerenciamento de URLs**: Fila de semente, controle de visitados, paginação
- **Coleta robusta**: Retries exponenciais, timeout, respeito a robots.txt
- **Parsing configurável**: Seletores CSS/XPath por domínio
- **Validação rigorosa**: Schema Pydantic, normalização de dados
- **Armazenamento flexível**: JSON, CSV e SQLite
- **Observabilidade**: Logging estruturado, métricas de execução
- **CLI amigável**: Interface via Typer

## 🚀 INSTALAÇÃO E EXECUÇÃO

### 1. Instalar dependências
```bash
cd /workspace
pip install -r requirements.txt
```

### 2. Configurar sites para crawl
Edite `config/sites.yaml` com os seletores do site alvo.

### 3. Executar o crawler
```bash
# Crawling básico
python main.py crawl --url https://exemplo.com/empresas

# Com opções avançadas
python main.py crawl --url https://exemplo.com/empresas --max-pages 50 --delay 2.0 --output json

# Exportar para SQLite
python main.py crawl --url https://exemplo.com/empresas --database companies.db

# Ver ajuda completa
python main.py --help
```

## ⚖️ COMPLIANCE & BOAS PRÁTICAS

- ✅ Verifica robots.txt antes de cada crawl
- ✅ Delay configurável entre requisições (padrão: 1.5s)
- ✅ Respeita códigos 429/503 e header Retry-After
- ✅ User-Agent identificável
- ✅ Opção de desativar crawl recursivo
- ⚠️ **NÃO armazene dados sensíveis sem consentimento**
- ⚠️ **SEMPRE verifique os Termos de Serviço do site alvo**

## 📊 ARQUITETURA DO PIPELINE

```
[URL Seed] → [Fila] → [HTTP Request + Retry] → [Parser] → [Validation] → [Storage]
                ↑           ↓                      ↓
          [Visitados]  [robots.txt]          [Schema Pydantic]
```

## 🔧 COMO ADICIONAR NOVOS SITES

1. Edite `config/sites.yaml`
2. Adicione nova entrada com domínio e seletores CSS/XPath
3. Execute o crawler apontando para o novo domínio

## 📈 PRÓXIMOS PASSOS (V2)

- [ ] Suporte a JavaScript rendering (Playwright)
- [ ] Pool de proxies rotativos
- [ ] Banco de dados externo (PostgreSQL)
- [ ] Processamento assíncrono (asyncio)
- [ ] API REST para controle do crawler
- [ ] Dashboard de monitoramento

## ⚠️ AVISO LEGAL

Este software é fornecido para fins educacionais e de pesquisa. 
O usuário é responsável por:
- Verificar e respeitar os Termos de Serviço de cada site
- Cumprir a legislação aplicável (LGPD, GDPR, etc.)
- Não causar sobrecarga nos servidores alvo
- Obter consentimento quando necessário para coleta de dados

Use com responsabilidade.
