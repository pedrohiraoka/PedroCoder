# Extrator de Dados de FIIs - B3

## Descrição do Projeto

Este é um script CLI (Command Line Interface) robusto e modular para extrair dados fundamentalistas de **Fundos de Investimento Imobiliário (FIIs)** da bolsa brasileira (B3). O script utiliza a biblioteca `pynvest` como fonte primária de dados (via site Fundamentus) com fallback automático para scraping direto caso a biblioteca falhe.

### Características Principais

- **Extrator ETL puro**: Apenas coleta e estrutura dados brutos, sem cálculos de rentabilidade ou projeções
- **Resiliente**: Tratamento de erros por ticker individual, permitindo continuidade mesmo com falhas
- **Rate limiting**: Pausa de 1 segundo entre requisições para evitar bloqueios
- **Dados limpos**: Conversão automática de formatos brasileiros (R$, %, vírgula decimal) para floats
- **Output otimizado para IA**: JSON hierárquico em snake_case pronto para consumo por LLMs

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou navegue até o diretório do projeto:**

```bash
cd /workspace
```

2. **Crie um ambiente virtual (recomendado):**

```bash
python3 -m venv venv
```

3. **Ative o ambiente virtual:**

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

4. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

---

## Como Usar

### Execução Básica

Execute o script e forneça os tickers quando solicitado:

```bash
python extrator_fiis.py
```

### Exemplo de Interação

```
============================================================
EXTRATOR DE DADOS DE FIIs - B3
============================================================

Digite os tickers dos FIIs separados por vírgula: HGLG11, KNCR11, VGHF11

Processando 3 ticker(s): HGLG11, KNCR11, VGHF11
------------------------------------------------------------
2026-07-24 20:42:10 - INFO - [1/3] Processando HGLG11...
  ✓ HGLG11: Dados coletados com sucesso
2026-07-24 20:42:12 - INFO - [2/3] Processando KNCR11...
  ✓ KNCR11: Dados coletados com sucesso
2026-07-24 20:42:14 - INFO - [3/3] Processando VGHF11...
  ✓ VGHF11: Dados coletados com sucesso
2026-07-24 20:42:15 - INFO - Dados exportados para: dados_fiis_brutos.json

============================================================
RESUMO DA EXTRAÇÃO
============================================================
Total solicitados: 3
Sucesso: 3
Falha: 0
Arquivo gerado: dados_fiis_brutos.json
============================================================
```

### Formato de Entrada

- Separe os tickers por **vírgula**
- Espaços em branco são tratados automaticamente
- Case insensitive (HGLG11 = hglg11)
- Caracteres inválidos são removidos automaticamente

**Exemplos válidos:**
```
HGLG11, KNCR11, VGHF11
hglg11,kncr11,vghf11
HGLG11,  KNCR11 ,  VGHF11
```

---

## Estrutura do JSON Gerado

O arquivo `dados_fiis_brutos.json` segue este schema:

```json
{
  "metadata": {
    "data_extracao": "2026-07-25T14:30:00+00:00",
    "fonte": "Fundamentus (via pynvest/scraper)",
    "total_tickers_solicitados": 3,
    "total_tickers_sucesso": 2,
    "total_tickers_falha": 1
  },
  "fiis": {
    "HGLG11": {
      "status": "sucesso",
      "dados_gerais": {
        "nome": "PÁTRIA LOG - FUNDO DE INVESTIMENTO IMOBILIÁRIO...",
        "segmento": "Multicategoria",
        "data_ult_cot": "23/07/2026"
      },
      "mercado": {
        "cotacao": 147.75,
        "valor_mercado": 6737660000.0,
        "nro_cotas": 45601745.0,
        "vp_cota": 166.0
      },
      "indicadores": {
        "p_vp": 0.89,
        "dividend_yield": 8.9,
        "ffo_yield": 6.58,
        "liquidez_media_diaria": 15247500.0
      },
      "oscilacoes": {
        "dia": -0.03,
        "mes": -1.43,
        "doze_meses": 4.0
      },
      "ultimo_rendimento": {
        "valor": 11.62,
        "data": null
      }
    },
    "AAAA11": {
      "status": "erro",
      "mensagem": "Ticker não encontrado ou falha na conexão."
    }
  }
}
```

### Campos Extraídos

| Categoria | Campo | Descrição | Tipo |
|-----------|-------|-----------|------|
| **dados_gerais** | nome | Nome completo do FII | string |
| | segmento | Segmento de atuação | string |
| | data_ult_cot | Data da última cotação | string |
| **mercado** | cotacao | Preço atual da cota | float |
| | valor_mercado | Valor total de mercado | float |
| | nro_cotas | Número total de cotas | float |
| | vp_cota | Valor Patrimonial por cota | float |
| **indicadores** | p_vp | Preço sobre Valor Patrimonial | float |
| | dividend_yield | Dividend Yield (últimos 12 meses) | float |
| | ffo_yield | FFO Yield | float |
| | liquidez_media_diaria | Liquidez média diária (2 meses) | float |
| **oscilacoes** | dia | Variação percentual no dia | float |
| | mes | Variação percentual no mês | float |
| | doze_meses | Variação percentual em 12 meses | float |
| **ultimo_rendimento** | valor | Último dividendo pago por cota | float |
| | data | Data do último rendimento | string/null |

---

## Troubleshooting

### Erros Comuns

#### 1. "Ticker não encontrado ou falha na conexão"

**Causas possíveis:**
- Ticker inexistente ou digitado incorretamente
- Site Fundamentus indisponível
- Bloqueio temporário por excesso de requisições

**Soluções:**
- Verifique se o ticker está correto no site da B3 ou Fundamentus
- Aguarde alguns minutos e tente novamente
- Reduza a quantidade de tickers processados simultaneamente

#### 2. Timeout ou erro de conexão

**Causas possíveis:**
- Instabilidade na rede
- Site de origem lento ou fora do ar

**Soluções:**
- Verifique sua conexão com a internet
- Tente executar em outro horário

#### 3. Dados incompletos ou campos nulos

**Causas possíveis:**
- O FII pode não ter todos os indicadores disponíveis no Fundamentus
- Layout do site mudou (requer atualização do scraper)

**Soluções:**
- Verifique manualmente no site Fundamentus se os dados existem
- Reporte o problema para atualização do script

### Rate Limiting e Bloqueios

O script já implementa rate limiting nativo (1 segundo entre requisições). Se você ainda enfrentar bloqueios:

1. **Aumente o intervalo:** Edite a linha `time.sleep(1)` no código para `time.sleep(2)` ou mais
2. **Processe em lotes:** Execute o script múltiplas vezes com menos tickers cada
3. **Use proxy/VPN:** Em casos extremos de bloqueio por IP

### Atualização do Layout do Fundamentus

Se o site Fundamentus mudar seu layout, o fallback scraper pode parar de funcionar. Neste caso:

1. Verifique se a biblioteca `pynvest` foi atualizada
2. Se necessário, atualize as funções de parsing no código
3. Considere reportar o issue aos mantenedores do pynvest

---

## Boas Práticas Implementadas

- ✅ **Type Hints**: Todas as funções possuem anotações de tipo
- ✅ **Docstrings**: Documentação completa em todas as funções
- ✅ **PEP 8**: Código formatado conforme padrões Python
- ✅ **Tratamento de erros**: Try/except por ticker individual
- ✅ **Logging**: Logs informativos para debugging
- ✅ **Modularidade**: Funções separadas por responsabilidade
- ✅ **Data Wrangling**: Limpeza robusta de dados financeiros BR

---

## Licença

Este projeto é fornecido "como está" para fins educacionais e de automação de dados públicos.

---

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Adicionar novos indicadores
- Melhorar a documentação
