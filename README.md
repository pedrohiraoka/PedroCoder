# Extrator de Dados de FIIs - B3 (Fundamentus)

Script CLI robusto e modular para extração de dados fundamentalistas de Fundos de Investimento Imobiliário (FIIs) listados na bolsa brasileira (B3). Os dados são coletados do site [Fundamentus](https://www.fundamentus.com.br) utilizando a biblioteca `pynvest` com fallback para scraping direto via `requests`/`BeautifulSoup`.

## 📋 Descrição do Projeto

Este script realiza um processo ETL (Extract, Transform, Load) simplificado:

1. **Extract**: Coleta dados brutos de FIIs diretamente do Fundamentus
2. **Transform**: Limpa e estrutura os dados no formato JSON otimizado para consumo por IA/LLM
3. **Load**: Exporta os dados para arquivo JSON e baixa relatórios gerenciais em PDF

### Funcionalidades Principais

- ✅ Coleta de indicadores fundamentalistas específicos de FIIs
- ✅ Download automático do último relatório gerencial de cada FII
- ✅ Tratamento robusto de erros (continua processando mesmo com falhas individuais)
- ✅ Rate limiting para evitar bloqueios do site origem
- ✅ Limpeza automática de valores monetários brasileiros (R$, %, vírgulas decimais)
- ✅ Type hints e docstrings conforme PEP 8
- ✅ Saída JSON hierárquica e limpa para fácil consumo por modelos de IA

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Conexão com internet

### Passo a Passo

1. **Clone ou navegue até o diretório do projeto:**

```bash
cd /workspace
```

2. **Crie um ambiente virtual (recomendado):**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

4. **Verifique a instalação:**

```bash
python extrator_fiis.py --help  # Se implementar help
# ou simplesmente execute o script
python extrator_fiis.py
```

## 💻 Uso

### Execução Básica

```bash
python extrator_fiis.py
```

O script solicitará os tickers via prompt:

```
Digite os tickers dos FIIs separados por vírgula: HGLG11, KNCR11, VGHF11
```

### Exemplo de Entrada

```
HGLG11, KNCR11, VGHF11
```

Ou com espaços extras (o script trata automaticamente):

```
  hglg11 , knCr11 ,VGHF11  
```

### Saída Gerada

Após a execução bem-sucedida, serão gerados os seguintes arquivos no diretório atual:

1. **`dados_fiis_brutos.json`** - Dados estruturados de todos os FIIs
2. **`{TICKER}.pdf`** - Relatório gerencial de cada FII (ex: `HGLG11.pdf`)

## 📊 Estrutura do JSON Gerado

O arquivo JSON segue um esquema hierárquico otimizado para consumo por IA:

```json
{
  "metadata": {
    "data_extracao": "2026-07-25T11:37:48",
    "fonte": "Fundamentus (via pynvest/scraper)",
    "total_tickers_solicitados": 3,
    "total_tickers_sucesso": 3,
    "total_tickers_falha": 0
  },
  "fiis": {
    "HGLG11": {
      "status": "sucesso",
      "dados_gerais": {
        "nome": "PÁTRIA LOG - FUNDO DE INVESTIMENTO IMOBILIÁRIO",
        "segmento": "Multicategoria",
        "data_ult_cot": "24/07/2026"
      },
      "mercado": {
        "cotacao": 147.76,
        "valor_mercado": 6738110000.0,
        "nro_cotas": 45601745.0,
        "vp_cota": 166.0
      },
      "indicadores": {
        "p_vp": 0.89,
        "dividend_yield": 8.9,
        "ffo_yield": 6.58,
        "liquidez_media_diaria": 15278000.0
      },
      "oscilacoes": {
        "dia": 0.01,
        "mes": -1.42,
        "doze_meses": 4.38
      },
      "rendimento_anualizado": {
        "valor": 11.62,
        "data_referencia": "24/07/2026",
        "periodo": "últimos 12 meses"
      },
      "relatorio": {
        "link": "https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=...",
        "arquivo_baixado": "HGLG11.pdf",
        "status_download": "sucesso"
      }
    },
    "TICKER_INVALIDO": {
      "status": "erro",
      "mensagem": "Ticker não encontrado ou falha na conexão."
    }
  }
}
```

### Campos do JSON

#### Metadata
| Campo | Descrição |
|-------|-----------|
| `data_extracao` | Timestamp ISO 8601 da extração |
| `fonte` | Origem dos dados |
| `total_tickers_solicitados` | Quantidade de tickers informados |
| `total_tickers_sucesso` | Tickers processados com sucesso |
| `total_tickers_falha` | Tickers que falharam |

#### Dados por FII (sucesso)
| Campo | Descrição | Tipo |
|-------|-----------|------|
| `dados_gerais.nome` | Nome completo do FII | string |
| `dados_gerais.segmento` | Segmento de atuação | string |
| `dados_gerais.data_ult_cot` | Data da última cotação | string |
| `mercado.cotacao` | Preço atual da cota | float |
| `mercado.valor_mercado` | Valor de mercado total | float |
| `mercado.nro_cotas` | Número total de cotas | float |
| `mercado.vp_cota` | Valor patrimonial por cota | float |
| `indicadores.p_vp` | Preço sobre Valor Patrimonial | float |
| `indicadores.dividend_yield` | Dividend Yield (%) | float |
| `indicadores.ffo_yield` | FFO Yield (%) | float |
| `indicadores.liquidez_media_diaria` | Liquidez média diária (R$) | float |
| `oscilacoes.dia` | Variação no dia (%) | float |
| `oscilacoes.mes` | Variação no mês (%) | float |
| `oscilacoes.doze_meses` | Variação em 12 meses (%) | float |
| `rendimento_anualizado.valor` | Rendimento por cota últimos 12 meses | float |
| `rendimento_anualizado.data_referencia` | Data de referência | string |
| `rendimento_anualizado.periodo` | Período de referência | string |
| `relatorio.link` | URL do relatório gerencial | string |
| `relatorio.arquivo_baixado` | Nome do arquivo PDF baixado | string |
| `relatorio.status_download` | Status do download | string |

#### Dados por FII (erro)
| Campo | Descrição |
|-------|-----------|
| `status` | Sempre "erro" |
| `mensagem` | Descrição do erro ocorrido |

## 📁 Organização dos Relatórios PDF

Os relatórios gerenciais são salvos no **mesmo diretório** onde o script é executado, com o nome `{TICKER}.pdf`:

```
/workspace/
├── extrator_fiis.py
├── dados_fiis_brutos.json
├── HGLG11.pdf
├── KNCR11.pdf
└── VGHF11.pdf
```

### Características dos PDFs Baixados

- **Formato**: PDF original da B3/FNET
- **Conteúdo**: Relatório gerencial mais recente disponível
- **Nomeação**: `{TICKER}.pdf` (ex: `HGLG11.pdf`)
- **Localização**: Mesmo diretório do arquivo JSON

## 🔧 Troubleshooting

### Erros Comuns e Soluções

#### 1. "Ticker não encontrado ou falha na conexão"

**Causas possíveis:**
- Ticker digitado incorretamente
- Ticker não é um FII listado na B3
- Problemas temporários de conexão com o Fundamentus

**Soluções:**
- Verifique se o ticker está correto (ex: `HGLG11`, não `HGLG11.SA`)
- Teste acessar https://www.fundamentus.com.br manualmente
- Aguarde alguns minutos e tente novamente

#### 2. "Timeout na conexão"

**Causas:**
- Lentidão na rede
- Site de origem sobrecarregado

**Soluções:**
- Verifique sua conexão com a internet
- Tente novamente em outro horário
- O script já possui timeout configurado (15 segundos)

#### 3. Bloqueio de IP / Rate Limiting

**Sintomas:**
- Múltiplas requisições falhando consecutivamente
- Mensagens de erro HTTP 429 ou 403

**Soluções:**
- O script já implementa rate limiting (1 segundo entre requisições)
- Para muitos tickers, execute em lotes menores
- Aguarde alguns minutos entre execuções

#### 4. "pynvest não disponível"

**Causa:** Biblioteca pynvest não instalada corretamente

**Solução:**
```bash
pip install -r requirements.txt --upgrade
```

#### 5. PDF não é baixado

**Causas possíveis:**
- Link do relatório indisponível no Fundamentus
- Problemas de permissão de escrita no diretório

**Soluções:**
- Verifique se há permissão de escrita no diretório
- O JSON indicará `"status_download": "erro"` com a mensagem específica
- Alguns FIIs podem não ter relatórios disponíveis publicamente

### Boas Práticas

1. **Execute em lotes**: Para muitos tickers (>20), divida em múltiplas execuções
2. **Verifique o JSON**: Sempre revise o `metadata.total_tickers_falha` após execução
3. **Mantenha atualizado**: O layout do Fundamentus pode mudar; mantenha as dependências atualizadas
4. **Respeite o site**: Não remova o rate limiting ou faça requisições em massa

## 🛡️ Considerações Importantes

### Limitações

- **Dados em tempo real**: As cotações podem ter delay de 15-20 minutos
- **Disponibilidade de relatórios**: Nem todos os FIIs têm relatórios disponíveis
- **Fallback de scraping**: O scraping direto (fallback) está parcialmente implementado

### Aviso Legal

Este script é fornecido **apenas para fins educacionais e de pesquisa**. Os dados são obtidos de fontes públicas e podem conter erros ou atrasos. Não utilize estas informações como única base para decisões de investimento.

- Consulte sempre fontes oficiais (B3, sites das gestoras)
- Verifique a data dos dados antes de tomar decisões
- Este script não constitui recomendação de investimento

## 📝 Licença

Este projeto é distribuído sem restrições de uso, desde que creditada a autoria.

## 🤝 Contribuição

Sugestões de melhorias são bem-vindas:

- Adicionar suporte a mais fontes de dados
- Implementar cache local para evitar requisições repetidas
- Adicionar validação mais rigorosa de tickers
- Implementar modo verbose/silent

---

**Autor**: Engenheiro de Dados Sênior & Especialista em Web Scraping  
**Versão**: 1.0.0  
**Última atualização**: Julho 2026
