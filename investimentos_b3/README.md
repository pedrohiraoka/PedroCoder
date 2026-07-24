# Acompanhamento de Carteira de Investimentos B3

Aplicação CLI (Command Line Interface) robusta, modular e orientada a objetos para gerenciar ativos da bolsa brasileira (B3). O foco é a precisão dos dados utilizando fontes oficiais e gratuitas.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração Inicial](#configuração-inicial)
- [Uso Prático](#uso-prático)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Bibliotecas Utilizadas](#bibliotecas-utilizadas)
- [Exemplos de Exportação](#exemplos-de-exportação)

---

## Visão Geral

Esta aplicação permite:

- ✅ **Gerenciar Carteira**: Adicionar, remover e listar ações e FIIs
- ✅ **Cotações em Tempo Real**: Dados oficiais da B3 via `brasa-marketdata`
- ✅ **Indicadores Fundamentalistas**: P/L, P/VP, Dividend Yield via `pynvest`
- ✅ **Registro de Proventos**: Dividendos e JCP recebidos
- ✅ **Cálculos Automáticos**: Lucro/prejuízo, Dividend Yield on Cost
- ✅ **Exportação JSON**: Snapshot completo da carteira com métricas

---

## Pré-requisitos

- **Python 3.10 ou superior**
- pip (gerenciador de pacotes Python)
- Conexão com internet (para coleta de dados)

Verifique sua versão do Python:

```bash
python --version
# ou
python3 --version
```

---

## Instalação

### 1. Clone ou navegue até o diretório do projeto

```bash
cd investimentos_b3
```

### 2. Crie um ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Verifique a instalação

```bash
python cli.py --help
```

---

## Configuração Inicial

### Cache do brasa-marketdata

O `brasa-marketdata` gerencia automaticamente seu cache local na primeira execução. Ao buscar dados históricos ou cotações pela primeira vez, os dados são baixados e armazenados localmente para consultas futuras mais rápidas.

**Importante**: A primeira execução pode ser mais lenta enquanto o cache é construído. Execuções subsequentes serão significativamente mais rápidas.

O cache é armazenado em:
- Linux/Mac: `~/.cache/brasa/`
- Windows: `C:\Users\<usuario>\AppData\Local\brasa\`

---

## Uso Prático

### Comandos Disponíveis

```bash
python cli.py --help
```

### 1. Adicionar uma Ação (ex: PETR4)

```bash
python cli.py add PETR4 --quantity 100 --price 35.50 --type ACAO
```

**Parâmetros:**
- `PETR4`: Ticker do ativo
- `--quantity 100`: Quantidade de ações
- `--price 35.50`: Preço médio de compra (R$)
- `--type ACAO`: Tipo de ativo (ACAO ou FII)

### 2. Adicionar um FII (ex: HGLG11)

```bash
python cli.py add HGLG11 --quantity 50 --price 105.00 --type FII
```

### 3. Atualizar Posição Existente

Executar o comando `add` novamente para o mesmo ticker atualiza a posição, calculando automaticamente o novo preço médio ponderado:

```bash
# Adiciona mais 50 ações de PETR4 a R$ 38.00
python cli.py add PETR4 --quantity 50 --price 38.00 --type ACAO
```

### 4. Listar Ativos Cadastrados

```bash
python cli.py list
```

**Saída esperada:**
```
┌─────────────────────┐
│   Carteira de Ativos │
├──────────┬──────┬───────┬─────────────┬────────────┤
│ Ticker   │ Tipo │  Qtd  │ Preço Médio │ Criado Em  │
├──────────┼──────┼───────┼─────────────┼────────────┤
│ HGLG11   │ FII  │    50 │ R$   105.00 │ 2024-01-15 │
│ PETR4    │ ACAO │   100 │ R$    35.50 │ 2024-01-10 │
└──────────┴──────┴───────┴─────────────┴────────────┘
```

### 5. Visualizar Resumo da Carteira

```bash
python cli.py show
```

Este comando busca cotações atuais e indicadores fundamentalistas, calculando:
- Valor investido vs. valor de mercado
- Lucro/prejuízo absoluto e percentual
- Dividend Yield on Cost

**Saída esperada:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                      Resumo da Carteira                              │
├────────┬───────┬─────────────┬───────────┬────────────┬───────────┤
│ Ticker │  Qtd  │ Preço Médio │   Atual   │ Investido  │ Mercado   │
├────────┼───────┼─────────────┼───────────┼────────────┼───────────┤
│ PETR4  │   100 │ R$   35.50  │ R$  37.20 │ R$ 3,550.00│ R$ 3,720.00│
│ HGLG11 │    50 │ R$  105.00  │ R$  98.50 │ R$ 5,250.00│ R$ 4,925.00│
└────────┴───────┴─────────────┴───────────┴────────────┴───────────┘

╭────────────────────────────────────────────────────────────────────╮
│                     Resumo Financeiro                               │
├────────────────────────────────────────────────────────────────────┤
│ Total Investido:      R$ 8,800.00                                  │
│ Valor de Mercado:     R$ 8,645.00                                  │
│ Lucro/Prejuízo:       R$ -155.00 (-1.76%)                          │
│ Total Proventos:      R$ 450.00                                    │
│ Ativos:               2                                            │
╰────────────────────────────────────────────────────────────────────╯
```

### 6. Registrar um Dividendo Recebido

```bash
python cli.py dividend PETR4 --date 2024-01-15 --value 0.85
```

**Parâmetros:**
- `PETR4`: Ticker do ativo
- `--date 2024-01-15`: Data do pagamento (YYYY-MM-DD)
- `--value 0.85`: Valor por ação (R$)

### 7. Registrar JCP (Juros sobre Capital Próprio)

```bash
python cli.py dividend BBAS3 --date 2024-02-20 --value 1.20 --type JCP
```

### 8. Visualizar Histórico de Proventos

```bash
# Todos os proventos
python cli.py history

# Filtrar por ticker específico
python cli.py history --ticker PETR4
```

### 9. Remover um Ativo

```bash
python cli.py remove PETR4
```

⚠️ **Atenção**: Isso remove apenas o ativo da carteira. O histórico de proventos associados é mantido.

### 10. Exportar Carteira para JSON

```bash
# Exportação padrão
python cli.py export

# Com caminho personalizado
python cli.py export --output minha_carteira_2024.json

# Incluindo dados brutos
python cli.py export --raw
```

---

## Estrutura do Projeto

```
investimentos_b3/
├── data_fetcher.py      # Coleta de dados (brasa, pynvest)
├── portfolio_manager.py # Gerenciamento da carteira e cálculos
├── exporter.py          # Exportação para JSON
├── cli.py               # Interface de linha de comando
├── requirements.txt     # Dependências do projeto
├── README.md            # Este arquivo
├── data/                # Diretório para dados locais (opcional)
└── tests/               # Testes unitários (futuro)
```

### Módulos

| Módulo | Responsabilidade |
|--------|------------------|
| `data_fetcher.py` | Integração com APIs externas (brasa-marketdata, pynvest). Tratamento de erros de rede e dados faltantes. |
| `portfolio_manager.py` | Lógica de negócio, CRUD de ativos, registro de proventos, cálculos financeiros, persistência SQLite. |
| `exporter.py` | Serialização de dados para JSON com estrutura hierárquica clara. |
| `cli.py` | Ponto de entrada, parsing de argumentos, interface com usuário (rich). |

---

## Bibliotecas Utilizadas

### Por que estas bibliotecas?

| Biblioteca | Finalidade | Vantagens |
|------------|-----------|-----------|
| **brasa-marketdata** | Cotações e históricos | ✅ Dados oficiais da B3<br>✅ Cache local automático<br>✅ Gratuito e sem limites de requisição<br>✅ Mantido pela comunidade |
| **pynvest** | Indicadores fundamentalistas | ✅ Scraping do Fundamentus<br>✅ Amplo conjunto de indicadores<br>✅ Fonte confiável para análise fundamentalista |
| **pandas** | Manipulação de dados | ✅ Performance em operações numéricas<br>✅ Fácil integração com outras bibliotecas |
| **rich** | Interface CLI | ✅ Tabelas bonitas e formatadas<br>✅ Feedback visual claro<br>✅ Cross-platform |
| **sqlite3** | Persistência | ✅ Nativo do Python<br>✅ Sem dependências externas<br>✅ Leve e eficiente |

### Comparativo: brasa vs yfinance vs pynvest

| Característica | brasa-marketdata | yfinance | pynvest |
|---------------|------------------|----------|---------|
| Fonte de dados | B3 oficial | Yahoo Finance | Fundamentus |
| Foco | Ações brasileiras | Global | Fundamentalistas BR |
| Cache local | ✅ Sim | ✅ Sim | ❌ Não |
| Dados fundamentalistas | Parcial | Parcial | ✅ Completo |
| Confiabilidade B3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Requer API Key | ❌ Não | ❌ Não | ❌ Não |

**Nossa abordagem**: Combinamos `brasa-marketdata` (cotações oficiais) com `pynvest` (fundamentalistas completos) para obter o melhor de cada fonte.

---

## Exemplos de Exportação

### Estrutura do JSON Exportado

```json
{
  "meta_dados": {
    "versao_exportacao": "1.0",
    "data_geracao": "2024-01-15T10:30:00",
    "fonte_dados": {
      "cotacoes": "brasa-marketdata (B3 oficial)",
      "fundamentalistas": "pynvest (Fundamentus)"
    },
    "moeda": "BRL",
    "mercado": "B3 - Brasil Bolsa Balcão"
  },
  "resumo_financeiro": {
    "total_investido": 8800.00,
    "total_market_value": 8645.00,
    "total_profit_loss": -155.00,
    "total_profit_loss_pct": -1.76,
    "total_dividends_received": 450.00,
    "assets_count": 2,
    "by_type": {
      "ACAO": {"count": 1, "invested": 3550.00, "market": 3720.00},
      "FII": {"count": 1, "invested": 5250.00, "market": 4925.00}
    }
  },
  "carteira_ativa": {
    "total_ativos": 2,
    "acoes": {
      "quantidade": 1,
      "lista": [
        {
          "ticker": "PETR4",
          "quantidade": 100,
          "preco_medio": 35.50,
          "cotacao_atual": 37.20,
          "valor_investido": 3550.00,
          "valor_mercado": 3720.00,
          "lucro_prejuizo": 170.00,
          "lucro_prejuizo_percentual": 4.79,
          "dividend_yield_on_cost": 2.40,
          "indicadores_fundamentalistas": {
            "p_l": 4.5,
            "p_vp": 0.85,
            "dividend_yield": 8.5
          }
        }
      ]
    },
    "fiis": {...}
  },
  "historico_proventos": {
    "total_registros": 5,
    "total_por_tipo": {
      "dividendos": 350.00,
      "jcp": 100.00,
      "geral": 450.00
    },
    "por_ativo": {
      "PETR4": [...],
      "HGLG11": [...]
    }
  }
}
```

---

## Fluxo de Trabalho Sugerido

1. **Primeira configuração**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Adicione seus ativos**:
   ```bash
   python cli.py add PETR4 -q 100 -p 35.50
   python cli.py add HGLG11 -q 50 -p 105.00 -t FII
   ```

3. **Registre proventos históricos** (opcional):
   ```bash
   python cli.py dividend PETR4 -d 2023-12-15 -v 0.75
   python cli.py dividend HGLG11 -d 2023-12-20 -v 0.95
   ```

4. **Acompanhe regularmente**:
   ```bash
   python cli.py show  # Ver performance atualizada
   ```

5. **Exporte para backup/análise**:
   ```bash
   python cli.py export --output backup_$(date +%Y%m%d).json
   ```

---

## Tratamento de Erros

A aplicação inclui tratamento robusto de erros:

- **Falhas de rede**: Se `brasa` ou `pynvest` falharem, a aplicação continua com dados disponíveis
- **Dados faltantes**: Cotações ou indicadores indisponíveis são marcados como "N/A"
- **Validação de entrada**: Quantidades e preços negativos são rejeitados
- **Logs detalhados**: Use `--verbose` (futuro) para debug

---

## Limitações Conhecidas

1. **pynvest depende do Fundamentus**: Se o site mudar sua estrutura, pode requerer atualização
2. **Cache do brasa**: Primeira execução é mais lenta (download inicial de dados)
3. **Dados intraday**: A aplicação usa dados de fechamento (end-of-day)

---

## Contribuição

Contribuições são bem-vindas! Sugestões:
- Adicionar novos indicadores fundamentalistas
- Integração com outras fontes de dados
- Relatórios gráficos
- Backtesting simples

---

## Licença

MIT License - Sinta-se livre para usar e modificar.

---

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs no console
2. Certifique-se de ter conexão com internet
3. Execute `python cli.py --help` para ver todos os comandos

**Boa sorte nos investimentos! 📈**
