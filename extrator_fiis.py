"""
Extrator de Dados de Fundos de Investimento Imobiliário (FIIs) da B3.

Este módulo fornece uma interface de linha de comando (CLI) robusta para extrair
dados fundamentalistas de FIIs brasileiros utilizando a biblioteca pynvest
(com fallback para scraping direto via requests/BeautifulSoup).

Autor: Engenheiro de Dados Sênior
Data: 2026
"""

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def limpar_valor_br(valor: str | None) -> float | None:
    """
    Converte strings financeiras brasileiras para float.

    Remove caracteres como 'R$', '%', substitui vírgulas por pontos
    e converte para float. Retorna None para valores vazios ou inválidos.

    Args:
        valor: String no formato brasileiro (ex: "R$ 1.000,50", "15,0%", "-").

    Returns:
        Float convertido ou None se o valor for inválido/vazio.

    Examples:
        >>> limpar_valor_br("R$ 1.000,50")
        1000.5
        >>> limpar_valor_br("15,0%")
        15.0
        >>> limpar_valor_br("-")
        None
    """
    if valor is None or valor == "" or valor.strip() == "-" or valor.strip() == "":
        return None

    # Remove espaços em branco
    valor_str = str(valor).strip()

    # Remove símbolos de moeda e porcentagem
    valor_str = valor_str.replace("R$", "").replace("%", "").strip()

    # Verifica se é vazio após limpeza
    if valor_str == "" or valor_str == "-":
        return None

    try:
        # Substitui vírgula por ponto para conversão decimal brasileira
        valor_str = valor_str.replace(".", "").replace(",", ".")
        return float(valor_str)
    except ValueError:
        logger.warning(f"Não foi possível converter '{valor}' para float.")
        return None


def limpar_string(valor: str | None) -> str | None:
    """
    Limpa strings removendo espaços extras e normalizando.

    Args:
        valor: String a ser limpa.

    Returns:
        String limpa ou None se vazia.
    """
    if valor is None or valor == "" or valor.strip() == "-":
        return None
    return str(valor).strip()


def coletar_dados_fii_pynvest(ticker: str) -> dict[str, Any] | None:
    """
    Coleta dados de um FII usando a biblioteca pynvest.

    Args:
        ticker: Ticker do FII (ex: "HGLG11").

    Returns:
        Dicionário com os dados brutos do FII ou None em caso de falha.
    """
    try:
        from pynvest.scrappers.fundamentus import Fundamentus

        fundamentus = Fundamentus()
        df = fundamentus.coleta_indicadores_de_ativo(ticker)

        if df is None or df.empty:
            logger.warning(f"Nenhum dado retornado pelo pynvest para {ticker}.")
            return None

        return df.to_dict("records")[0]
    except Exception as e:
        logger.error(f"Erro ao coletar dados com pynvest para {ticker}: {e}")
        return None


def coletar_dados_fii_scraper(ticker: str) -> dict[str, Any] | None:
    """
    Fallback: Coleta dados de um FII via scraping direto do Fundamentus.

    Args:
        ticker: Ticker do FII (ex: "HGLG11").

    Returns:
        Dicionário com os dados brutos do FII ou None em caso de falha.
    """
    url = f"https://fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        dados = {"fii": ticker.upper()}

        # Extrai tabelas da página
        tabelas = soup.find_all("table")

        for tabela in tabelas:
            linhas = tabela.find_all("tr")
            for linha in linhas:
                cols = linha.find_all("td")
                if len(cols) >= 2:
                    chave = cols[0].get_text(strip=True).lower().replace(" ", "_")
                    valor = cols[1].get_text(strip=True)
                    dados[chave] = valor

        if len(dados) <= 1:  # Apenas o ticker foi encontrado
            return None

        return dados
    except Exception as e:
        logger.error(f"Erro no scraper direto para {ticker}: {e}")
        return None


def estruturar_dados_fii(ticker: str, dados_brutos: dict[str, Any]) -> dict[str, Any]:
    """
    Estrutura e limpa os dados brutos do FII conforme esquema JSON esperado.

    Args:
        ticker: Ticker do FII.
        dados_brutos: Dicionário com dados brutos extraídos.

    Returns:
        Dicionário estruturado conforme schema definido.
    """
    # Mapeamento de colunas do pynvest para o schema desejado
    dados_gerais = {
        "nome": limpar_string(dados_brutos.get("nome_fii")),
        "segmento": limpar_string(dados_brutos.get("segmento")),
        "data_ult_cot": limpar_string(dados_brutos.get("dt_ult_cot")),
    }

    mercado = {
        "cotacao": limpar_valor_br(dados_brutos.get("vlr_cot")),
        "valor_mercado": limpar_valor_br(dados_brutos.get("vlr_mercado")),
        "nro_cotas": limpar_valor_br(dados_brutos.get("num_cotas")),
        "vp_cota": limpar_valor_br(dados_brutos.get("vlr_vp_sobre_cota")),
    }

    indicadores = {
        "p_vp": limpar_valor_br(dados_brutos.get("vlr_p_sobre_vp")),
        "dividend_yield": limpar_valor_br(dados_brutos.get("vlr_div_yield")),
        "ffo_yield": limpar_valor_br(dados_brutos.get("vlr_ffo_yield")),
        "liquidez_media_diaria": limpar_valor_br(dados_brutos.get("vol_med_neg_2m")),
    }

    oscilacoes = {
        "dia": limpar_valor_br(dados_brutos.get("pct_var_dia")),
        "mes": limpar_valor_br(dados_brutos.get("pct_var_mes")),
        "doze_meses": limpar_valor_br(dados_brutos.get("pct_var_12m")),
    }

    # Último rendimento - tenta extrair do dividendo sobre cota
    ultimo_rendimento = {
        "valor": limpar_valor_br(dados_brutos.get("vlr_dividendo_sobre_cota")),
        "data": None,  # Data específica do último rendimento não está disponível diretamente
    }

    return {
        "status": "sucesso",
        "dados_gerais": dados_gerais,
        "mercado": mercado,
        "indicadores": indicadores,
        "oscilacoes": oscilacoes,
        "ultimo_rendimento": ultimo_rendimento,
    }


def coletar_dados_fii(ticker: str) -> dict[str, Any]:
    """
    Coleta dados de um FII tentando pynvest primeiro, depois fallback para scraper.

    Args:
        ticker: Ticker do FII.

    Returns:
        Dicionário estruturado com status e dados ou erro.
    """
    ticker_limpo = ticker.strip().upper()

    # Tenta pynvest primeiro
    dados_brutos = coletar_dados_fii_pynvest(ticker_limpo)

    # Fallback para scraper direto se pynvest falhar
    if dados_brutos is None:
        logger.info(f"Tentando fallback com scraper direto para {ticker_limpo}...")
        dados_brutos = coletar_dados_fii_scraper(ticker_limpo)

    if dados_brutos is None:
        return {
            "status": "erro",
            "mensagem": "Ticker não encontrado ou falha na conexão.",
        }

    # Estrutura os dados
    return estruturar_dados_fii(ticker_limpo, dados_brutos)


def parse_tickers_input(input_str: str) -> list[str]:
    """
    Processa a entrada do usuário extraindo tickers válidos.

    Args:
        input_str: String de entrada do usuário.

    Returns:
        Lista de tickers limpos e validados.
    """
    if not input_str or input_str.strip() == "":
        return []

    # Separa por vírgula, remove espaços, converte para maiúsculas
    tickers_raw = [t.strip().upper() for t in input_str.split(",")]

    # Filtra tickers válidos (alfanuméricos, 4-6 caracteres típicos de FIIs)
    tickers_validos = []
    for ticker in tickers_raw:
        # Remove caracteres inválidos
        ticker_limpo = re.sub(r"[^A-Z0-9]", "", ticker)
        if ticker_limpo and 4 <= len(ticker_limpo) <= 8:
            tickers_validos.append(ticker_limpo)

    return tickers_validos


def exportar_para_json(resultado: dict[str, Any], caminho_arquivo: str) -> None:
    """
    Exporta o resultado para arquivo JSON formatado.

    Args:
        resultado: Dicionário com metadata e dados dos FIIs.
        caminho_arquivo: Caminho do arquivo JSON de saída.
    """
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    logger.info(f"Dados exportados para: {caminho_arquivo}")


def main() -> None:
    """
    Função principal do script CLI.

    Orquestra todo o fluxo de extração de dados de FIIs:
    1. Solicita tickers ao usuário
    2. Valida e processa entrada
    3. Coleta dados de cada ticker com rate limiting
    4. Estrutura resultados
    5. Exporta para JSON
    """
    print("=" * 60)
    print("EXTRATOR DE DADOS DE FIIs - B3")
    print("=" * 60)
    print()

    # Solicita entrada do usuário
    entrada = input("Digite os tickers dos FIIs separados por vírgula: ")

    # Processa tickers
    tickers = parse_tickers_input(entrada)

    if not tickers:
        print("\nNenhum ticker válido fornecido. Encerrando programa.")
        sys.exit(0)

    print(f"\nProcessando {len(tickers)} ticker(s): {', '.join(tickers)}")
    print("-" * 60)

    # Inicializa estrutura de resultados
    fiis_data: dict[str, Any] = {}
    total_sucesso = 0
    total_falha = 0

    # Coleta dados de cada ticker
    for i, ticker in enumerate(tickers):
        logger.info(f"[{i + 1}/{len(tickers)}] Processando {ticker}...")

        try:
            resultado = coletar_dados_fii(ticker)
            fiis_data[ticker] = resultado

            if resultado["status"] == "sucesso":
                total_sucesso += 1
                print(f"  ✓ {ticker}: Dados coletados com sucesso")
            else:
                total_falha += 1
                print(f"  ✗ {ticker}: {resultado.get('mensagem', 'Erro desconhecido')}")
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar {ticker}: {e}")
            fiis_data[ticker] = {
                "status": "erro",
                "mensagem": f"Erro interno: {str(e)}",
            }
            total_falha += 1

        # Rate limiting entre requisições
        if i < len(tickers) - 1:
            time.sleep(1)

    # Monta resultado final
    resultado_final = {
        "metadata": {
            "data_extracao": datetime.now(timezone.utc).isoformat(),
            "fonte": "Fundamentus (via pynvest/scraper)",
            "total_tickers_solicitados": len(tickers),
            "total_tickers_sucesso": total_sucesso,
            "total_tickers_falha": total_falha,
        },
        "fiis": fiis_data,
    }

    # Exporta para JSON
    arquivo_saida = "dados_fiis_brutos.json"
    exportar_para_json(resultado_final, arquivo_saida)

    print()
    print("=" * 60)
    print("RESUMO DA EXTRAÇÃO")
    print("=" * 60)
    print(f"Total solicitados: {len(tickers)}")
    print(f"Sucesso: {total_sucesso}")
    print(f"Falha: {total_falha}")
    print(f"Arquivo gerado: {arquivo_saida}")
    print("=" * 60)


if __name__ == "__main__":
    main()
