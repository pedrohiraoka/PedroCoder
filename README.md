# Coletor de Dados Fundamentalistas - Fundamentus

## 📊 Descrição do Projeto

Este projeto é uma aplicação CLI (Command Line Interface) robusta desenvolvida em Python para **extração de dados fundamentalistas brutos** de ativos da bolsa brasileira (B3) diretamente do site [Fundamentus](https://www.fundamentus.com.br).

### Objetivos Principais

- ✅ Receber uma lista de tickers via input de texto simples (separados por vírgula)
- ✅ Extrair dados fundamentais brutos utilizando a biblioteca `pynvest` (com fallback para scraper customizado)
- ✅ Exportar dados brutos para um único arquivo JSON estruturado e limpo
- ✅ Otimizar o output para consumo por IAs externas
- ✅ **NÃO** realizar cálculos de carteira, rentabilidade ou métricas derivadas (apenas ETL)

### Funcionalidades

- **UX Simplificada**: Entrada de texto única com separação por vírgulas
- **Validação Automática**: Padronização de tickers (maiúsculas, remoção de caracteres inválidos)
- **Tratamento de Erros Robusto**: Continua processando mesmo se alguns tickers falharem
- **Rate Limiting**: Delay entre requisições para evitar bloqueios do site
- **Suporte Misto**: Processa tanto Ações quanto Fundos Imobiliários (FIIs)

---

## 🔧 Pré-requisitos

- **Python**: Versão 3.10 ou superior
- **Sistema Operacional**: Windows, macOS ou Linux
- **Conexão com Internet**: Necessária para acesso ao site Fundamentus

---

## 📦 Instalação

### 1. Clone o Repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>
```

### 2. Crie um Ambiente Virtual (venv)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Verifique a Instalação

```bash
python coletor.py --help  # Se implementar help, ou apenas execute
```

---

## 🚀 Como Usar

### Execução Básica

1. Execute o script:

```bash
python coletor.py
```

2. Quando solicitado, digite os tickers separados por vírgula:

```
Digite os tickers separados por vírgula (ex: PETR4, VALE3, HGLG11): PETR4, VALE3, HGLG11, BBSE3, ITSA4
```

3. Aguarde o processamento (o script exibirá o progresso)

4. O arquivo `dados_fundamentus_brutos.json` será gerado no diretório atual

### Exemplos de Entrada

```
# Ações apenas
PETR4, VALE3, BBAS3, ITUB4

# FIIs apenas
HGLG11, KNCR11, BTLG11, MXRF11

# Mistura de Ações e FIIs
PETR4, HGLG11, VALE3, KNIP11, ITSA4

# Com espaços extras (o script trata automaticamente)
  PETR4  ,  VALE3  ,  HGLG11  
```

### Saída Esperada

Após a execução, você verá um resumo:

```
======================================================================
RESUMO DA COLETA
======================================================================
Tickers solicitados: 5
Sucessos: 5
Erros: 0
Arquivo gerado: dados_fundamentus_brutos.json
======================================================================
```

---

## 📁 Estrutura do Arquivo JSON

O arquivo `dados_fundamentus_brutos.json` possui uma estrutura hierárquica clara e auto-descritiva:

```json
{
  "metadata": {
    "gerado_em": "2026-07-25T10:00:00-03:00",
    "fonte_dados": "Fundamentus (via pynvest)",
    "tickers_solicitados": ["PETR4", "VALE3", "HGLG11"],
    "tickers_processados_com_sucesso": ["PETR4", "VALE3"],
    "tickers_com_erro": ["HGLG11"],
    "total_tickers": 3,
    "sucessos": 2,
    "erros": 1
  },
  "ativos": {
    "PETR4": {
      "nome_empresa": "PETRÓLEO BRASILEIRO S.A. - PETROBRAS",
      "setor": "Petróleo, Gás e Biocombustíveis",
      "tipo_ativo": "Ação",
      "dados_fundamentalistas": {
        "cotacao": 35.50,
        "pl": 4.5,
        "pvp": 1.2,
        "psr": 0.8,
        "dividend_yield": 0.15,
        "p_ativo": 0.5,
        "p_cap_giro": 2.1,
        "p_ebit": 3.8,
        "p_ativo_circ_liq": 5.2,
        "ev_ebit": 4.2,
        "ev_ebitda": 3.5,
        "margem_ebit": 0.25,
        "margem_liquida": 0.18,
        "liquidez_corrente": 1.5,
        "roe": 0.25,
        "roa": 0.12,
        "divida_liquida_ebitda": 1.8,
        "divida_liquida_pl": 0.45
      },
      "status": "sucesso"
    },
    "HGLG11": {
      "status": "erro",
      "mensagem": "Ticker não encontrado no Fundamentus"
    }
  }
}
```

### Guia de Leitura para IA Consumidora

1. **Verifique o metadata** primeiro para entender o contexto da coleta
2. **Itere sobre `ativos`** para processar cada ticker
3. **Cheque o `status`** de cada ativo antes de usar os dados
4. **Dados null/None** indicam que a métrica não está disponível para aquele ativo
5. **Valores percentuais** (como dividend_yield, margens, ROE) estão em formato decimal (0.15 = 15%)

---

## 🛠️ Comandos Git Úteis

### Clonar o Repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>
```

### Criar Nova Branch

```bash
git checkout -b feature/nova-funcionalidade
```

### Fazer Commit das Alterações

```bash
git add .
git commit -m "Descrição clara e objetiva das alterações"
```

### Enviar para o Repositório Remoto

```bash
git push origin feature/nova-funcionalidade
```

### Verificar Status

```bash
git status
```

### Atualizar Branch Local com Mudanças Remotas

```bash
git pull origin main
```

---

## ⚠️ Troubleshooting

### Erro: HTTP 403 Forbidden

**Causa**: O site Fundamentus pode estar bloqueando requisições automatizadas.

**Solução**:
- O script já inclui headers de User-Agent para simular navegador
- Aumente o `DELAY_BETWEEN_REQUESTS` no código (padrão: 1.5s)
- Aguarde alguns minutos antes de tentar novamente

### Erro: Timeout na Conexão

**Causa**: Instabilidade no site Fundamentus ou conexão lenta.

**Solução**:
- Verifique sua conexão com a internet
- Tente executar novamente após alguns minutos
- O site pode estar em manutenção

### Erro: Ticker Não Encontrado

**Causa**: O ticker digitado não existe ou foi digitado incorretamente.

**Solução**:
- Verifique se o ticker está correto (ex: PETR4, não PETRA4)
- Alguns tickers podem ter sido deslistados
- O script continuará processando os demais tickers

### Erro: Módulo Não Encontrado

**Causa**: Dependências não instaladas corretamente.

**Solução**:
```bash
pip install -r requirements.txt --upgrade
```

### Dados Inconsistentes ou Faltantes

**Causa**: O site Fundamentus pode não ter todas as métricas para todos os ativos.

**Solução**:
- Valores `null` ou `None` são esperados para métricas não disponíveis
- FIIs têm métricas diferentes de Ações (ex: FFO Yield vs P/L)
- Consulte o site Fundamentus manualmente para verificar disponibilidade

---

## 📋 Métricas Extraídas

### Para Ações

| Métrica | Descrição |
|---------|-----------|
| cotacao | Cotação atual do ativo |
| pl | Preço sobre Lucro (P/L) |
| pvp | Preço sobre Valor Patrimonial (P/VP) |
| psr | Preço sobre Receita Líquida (PSR) |
| dividend_yield | Dividend Yield |
| p_ativo | Preço sobre Ativo |
| p_cap_giro | Preço sobre Capital de Giro |
| p_ebit | Preço sobre EBIT |
| p_ativo_circ_liq | Preço sobre Ativo Circulante Líquido |
| ev_ebit | Enterprise Value sobre EBIT |
| ev_ebitda | Enterprise Value sobre EBITDA |
| margem_ebit | Margem EBIT |
| margem_liquida | Margem Líquida |
| liquidez_corrente | Liquidez Corrente |
| roe | Return on Equity |
| roa | Return on Assets |
| divida_liquida_ebitda | Dívida Líquida / EBITDA |
| divida_liquida_pl | Dívida Líquida / Patrimônio Líquido |

### Para FIIs

| Métrica | Descrição |
|---------|-----------|
| cotacao | Cotação atual do fundo |
| pvp | Preço sobre Valor Patrimonial |
| dividend_yield | Dividend Yield |
| vlr_ffo_yield | FFO Yield |
| vlr_vp_sobre_cota | Valor Patrimonial por Cota |

---

## 📄 Licença

Este projeto é distribuído sob licença MIT.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📞 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com foco em qualidade, robustez e facilidade de uso para extração de dados fundamentalistas da B3.**
