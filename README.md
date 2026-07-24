# Coletor de Dados Brutos - B3

Script utilitário em Python para coleta e exportação de dados brutos de ativos da Bolsa de Valores do Brasil (B3). Este script foi desenvolvido para ser consumido por sistemas de IA externa, fornecendo dados estruturados e limpos.

## 🎯 Objetivo

Criar uma aplicação CLI que:
1. Recebe uma lista de tickers via input de texto simples
2. Baixa dados históricos e fundamentais brutos usando `brasa-marketdata` e `pynvest`
3. Exporta os dados para um arquivo JSON estruturado
4. **NÃO** realiza cálculos de carteira, rentabilidade ou métricas pessoais

## 📋 Requisitos

- Python 3.10+
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

### 1. Clone ou acesse o diretório do projeto

```bash
cd /workspace
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Verifique a instalação

```bash
python -c "import brasa; import pynvest; print('Instalação OK!')"
```

## ⚙️ Configuração do Cache do BRASA

O `brasa-marketdata` utiliza cache local para evitar downloads repetidos dos mesmos dados. Na **primeira execução**, o script fará o download completo dos dados históricos da B3, o que pode levar alguns minutos dependendo da sua conexão.

### Localização do Cache

Por padrão, o cache é armazenado em:
- **Linux/Mac**: `~/.brasa-cache/` ou `/workspace/.brasa-cache/`
- **Windows**: `%USERPROFILE%\.brasa-cache\`

### Configuração Personalizada (Opcional)

Para definir um caminho personalizado para o cache:

```python
import brasa
brasa.set_cache_path("/caminho/para/seu/cache")
```

Ou via variável de ambiente:

```bash
export BRASA_CACHE_PATH="/caminho/para/seu/cache"
```

### Limpando o Cache

Se necessário, limpe o cache para forçar novo download:

```bash
rm -rf ~/.brasa-cache/*
# ou
rm -rf /workspace/.brasa-cache/*
```

## 💻 Uso

### Execução Básica

```bash
python main.py
```

### Exemplo de Interação

```
============================================================
COLETOR DE DADOS BRUTOS - B3
============================================================

Digite os tickers separados por vírgula (ex: PETR4, VALE3, HGLG11):
> PETR4, VALE3, HGLG11, ABCD99

10:30:45 - INFO - Tickers recebidos: ['PETR4', 'VALE3', 'HGLG11', 'ABCD99']
10:30:45 - INFO - Validando tickers na base de dados...
10:30:46 - INFO -   ✓ PETR4 - Válido
10:30:47 - INFO -   ✓ VALE3 - Válido
10:30:48 - INFO -   ✓ HGLG11 - Válido
10:30:49 - WARNING -   ✗ ABCD99 - Inválido ou não encontrado
10:30:49 - INFO - Tickers válidos: 3
10:30:49 - WARNING - Tickers ignorados: ['ABCD99']

------------------------------------------------------------
INICIANDO COLETA DE DADOS
------------------------------------------------------------

10:30:49 - INFO - [1/3] Processando PETR4...
10:31:15 - INFO - [2/3] Processando VALE3...
10:31:42 - INFO - [3/3] Processando HGLG11...

------------------------------------------------------------
GERANDO ARQUIVO DE SAÍDA
------------------------------------------------------------

10:32:00 - INFO - Arquivo exportado com sucesso: /workspace/dados_brutos_carteira.json

============================================================
COLETA CONCLUÍDA COM SUCESSO!
============================================================
Arquivo gerado: /workspace/dados_brutos_carteira.json
Total de ativos processados: 3
Tickers ignorados (inválidos): 1
```

## 📁 Estrutura do Arquivo de Saída

O arquivo `dados_brutos_carteira.json` possui a seguinte estrutura:

```json
{
  "metadata": {
    "gerado_em": "2026-07-25T10:00:00",
    "fonte_dados": ["B3 (via brasa-marketdata)", "Fundamentus (via pynvest)"],
    "tickers_solicitados": ["PETR4", "VALE3", "HGLG11"],
    "tickers_validos": ["PETR4", "VALE3", "HGLG11"],
    "tickers_invalidos": [],
    "versao_script": "1.0.0",
    "observacoes": [...]
  },
  "ativos": {
    "PETR4": {
      "dados_cadastrais": {
        "ticker": "PETR4",
        "nome_empresa": "PETRÓLEO BRASILEIRO S.A. - PETROBRAS",
        ...
      },
      "historico_cotacoes": [
        {"data": "2024-01-02", "abertura": 35.50, "maxima": 36.20, ...},
        ...
      ],
      "indicadores_fundamentalistas": {
        "ticker": "PETR4",
        "preco_lucro": 4.52,
        "preco_valor_patrimonial": 1.23,
        "dividend_yield": 0.1542,
        ...
      },
      "proventos_historicos": [...]
    }
  },
  "resumo_validacao": {
    "total_solicitados": 3,
    "total_validos": 3,
    "total_invalidos": 0,
    "invalidos_detalhes": []
  }
}
```

## 📊 Campos Disponíveis

### Dados Cadastrais (Origem: B3)
- `ticker`: Código de negociação
- `nome_empresa`: Razão social da empresa
- `especificacao_papel`: Tipo do ativo (ON, PN, UNT, etc.)
- `moeda_referencia`: Moeda de negociação (BRL)
- `data_primeira_negociacao`: Data do primeiro pregão
- `data_ultima_negociacao`: Data do último pregão disponível

### Histórico de Cotações (Origem: B3 - COTAHIST)
- `data`: Data do pregão
- `abertura`: Preço de abertura
- `maxima`: Preço máximo do dia
- `minima`: Preço mínimo do dia
- `fechamento`: Preço de fechamento
- `volume`: Volume financeiro negociado
- E outros campos disponíveis no COTAHIST

### Indicadores Fundamentalistas (Origem: Fundamentus via pynvest)
- `preco_lucro`: P/L
- `preco_valor_patrimonial`: P/VP
- `preco_vendas`: PSR
- `dividend_yield`: DY
- `margem_bruta`, `margem_ebit`, `margem_liquida`: Margens
- `roe`, `roa`: Retornos
- `liquidez_corrente`: Liquidez
- E diversos outros indicadores

### Proventos Históricos (Origem: B3 - Eventos Corporativos)
- Dividendos
- Juros sobre Capital Próprio (JCP)
- Bonificações
- Subscrições

## 🔧 Tratamento de Erros

O script foi desenvolvido com resiliência:

1. **Tickers Inválidos**: São identificados e reportados, mas não interrompem a execução
2. **Falha no pynvest**: Se o scraping do Fundamentus falhar, os dados do brasa são mantidos e o campo é marcado como `null` ou `"indisponivel"`
3. **Dados Ausentes**: Campos sem dados são representados como `null` no JSON

## 📝 Notas Importantes

1. **Primeira Execução**: Pode demorar vários minutos devido ao download inicial do cache do brasa
2. **Conexão Internet**: Necessária para download de dados e scraping do Fundamentus
3. **Dados em Tempo Real**: Os dados de cotação têm defasagem de pelo menos 1 dia útil
4. **pynvest Instável**: O scraping do Fundamentus pode falhar intermitentemente

## 🐛 Troubleshooting

### Erro: "brasa-marketdata não encontrado"
```bash
pip install brasa-marketdata
```

### Erro: "pynvest não encontrado"
```bash
pip install pynvest
```
(Opcional - o script funciona sem ele, mas sem dados fundamentalistas)

### Erro: Timeout na primeira execução
- Verifique sua conexão com a internet
- O download inicial pode levar 5-10 minutos
- Aguarde até completar

### Cache corrompido
```bash
rm -rf ~/.brasa-cache/*
python main.py  # Forçará novo download
```

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais e de pesquisa.

## 🤝 Contribuição

Sinta-se à vontade para reportar issues ou sugerir melhorias.

---

**Desenvolvido para consumo por IA externa - Dados brutos e estruturados.**
