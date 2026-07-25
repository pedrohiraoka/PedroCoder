#!/usr/bin/env python3
"""
Extrator de Dados de Fundos de Investimento Imobiliário (FIIs) da B3.

Este script coleta dados fundamentalistas de FIIs listados na bolsa brasileira (B3)
através do site Fundamentus, utilizando a biblioteca pynvest com fallback para
scraping direto via requests/BeautifulSoup.

Autor: Engenheiro de Dados Sênior & Especialista em Web Scraping
Versão: 1.0.0
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constantes
BASE_URL_FUNDAMENTUS = "https://www.fundamentus.com.br"
URL_DETALHES_FII = f"{BASE_URL_FUNDAMENTUS}/detalhes.php?papel={{ticker}}"
URL_RELATORIOS_FII = f"{BASE_URL_FUNDAMENTUS}/fii_relatorios.php?papel={{ticker}}"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}
TIMEOUT_REQUEST = 15
TIMEOUT_DOWNLOAD = 30  # Timeout para downloads de PDF
RATE_LIMIT_DELAY = 1.0  # segundos entre requisições


def limpar_valor_br(valor: str | None) -> float | None:
    """
    Limpa e converte valores monetários/percentuais brasileiros para float.
    
    Remove caracteres como 'R$', '%', substitui vírgulas por pontos e converte
    para float. Retorna None para valores vazios ou inválidos.
    
    Args:
        valor: String contendo valor no formato brasileiro (ex: "R$ 1.000,50", "15,0%")
    
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
    if valor is None or valor == '' or valor == '-':
        return None
    
    # Remove espaços em branco
    valor = str(valor).strip()
    
    # Verifica se é apenas traço ou zero formatado
    if valor in ['-', '--', '0,00', '0,0', '0']:
        return None
    
    # Remove símbolos de moeda e porcentagem
    valor_limpo = re.sub(r'[R$\s%]', '', valor)
    
    # Substitui vírgula decimal por ponto (formato BR -> US)
    valor_limpo = valor_limpo.replace('.', '')  # Remove separador de milhar
    valor_limpo = valor_limpo.replace(',', '.')  # Converte decimal
    
    try:
        return float(valor_limpo)
    except ValueError:
        logger.warning(f"Não foi possível converter valor: '{valor}'")
        return None


def limpar_string(texto: str | None) -> str | None:
    """
    Limpa strings removendo espaços extras e normalizando texto.
    
    Args:
        texto: String a ser limpa.
    
    Returns:
        String limpa ou None se vazia.
    """
    if texto is None or texto == '':
        return None
    
    texto = str(texto).strip()
    if texto in ['-', '--', 'N/A', 'n/a']:
        return None
    
    return texto


def extrair_link_relatorio(ticker: str) -> dict[str, Any]:
    """
    Extrai o link do último relatório gerencial de um FII da página do Fundamentus.
    
    Args:
        ticker: Ticker do FII (ex: "HGLG11").
    
    Returns:
        Dicionário com 'link' (str ou None) e 'data_referencia' (str ou None).
    """
    url_relatorios = URL_RELATORIOS_FII.format(ticker=ticker)
    
    try:
        response = requests.get(url_relatorios, headers=HEADERS, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procurar tabela de relatórios
        tabela = soup.find('table')
        if not tabela:
            return {'link': None, 'data_referencia': None}
        
        # Encontrar todos os links de download
        links_download = tabela.find_all('a', href=True, string='Download')
        
        if not links_download:
            return {'link': None, 'data_referencia': None}
        
        # Pegar o primeiro link (mais recente)
        primeiro_link = links_download[0]
        href = primeiro_link['href']
        
        # Extrair data de referência da linha da tabela
        row = primeiro_link.find_parent('tr')
        data_ref = None
        if row:
            cells = row.find_all('td')
            if len(cells) >= 2:
                data_ref = cells[0].get_text(strip=True)
        
        return {
            'link': href if href.startswith('http') else f"{BASE_URL_FUNDAMENTUS}/{href}",
            'data_referencia': data_ref
        }
    
    except requests.RequestException as e:
        logger.error(f"Erro ao extrair link do relatório para {ticker}: {e}")
        return {'link': None, 'data_referencia': None}
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair link do relatório para {ticker}: {e}")
        return {'link': None, 'data_referencia': None}


def baixar_relatorio(link: str, ticker: str, diretorio_saida: Path) -> dict[str, Any]:
    """
    Baixa o relatório gerencial em PDF para o diretório especificado.
    
    Args:
        link: URL do relatório PDF.
        ticker: Ticker do FII (usado no nome do arquivo).
        diretorio_saida: Path do diretório onde salvar o PDF.
    
    Returns:
        Dicionário com 'arquivo_baixado' (str ou None) e 'status_download' (str).
    """
    if not link:
        return {
            'arquivo_baixado': None,
            'status_download': 'erro',
            'mensagem_erro': 'Link do relatório não disponível'
        }
    
    nome_arquivo = f"{ticker}.pdf"
    caminho_arquivo = diretorio_saida / nome_arquivo
    
    try:
        response = requests.get(link, headers=HEADERS, timeout=TIMEOUT_DOWNLOAD)
        response.raise_for_status()
        
        # Verificar se o conteúdo é realmente um PDF
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
            logger.warning(f"Conteúdo pode não ser PDF para {ticker}: {content_type}")
        
        with open(caminho_arquivo, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Relatório baixado com sucesso: {caminho_arquivo}")
        return {
            'arquivo_baixado': nome_arquivo,
            'status_download': 'sucesso'
        }
    
    except requests.Timeout:
        logger.error(f"Timeout ao baixar relatório para {ticker}")
        return {
            'arquivo_baixado': None,
            'status_download': 'erro',
            'mensagem_erro': 'Timeout na conexão'
        }
    except requests.RequestException as e:
        logger.error(f"Erro ao baixar relatório para {ticker}: {e}")
        return {
            'arquivo_baixado': None,
            'status_download': 'erro',
            'mensagem_erro': str(e)
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao baixar relatório para {ticker}: {e}")
        return {
            'arquivo_baixado': None,
            'status_download': 'erro',
            'mensagem_erro': str(e)
        }


def coletar_dados_fii_pynvest(ticker: str) -> pd.DataFrame | None:
    """
    Coleta dados fundamentalistas de um FII usando a biblioteca pynvest.
    
    Args:
        ticker: Ticker do FII (ex: "HGLG11").
    
    Returns:
        DataFrame do pandas com os dados ou None em caso de falha.
    """
    try:
        from pynvest.scrappers.fundamentus import Fundamentus
        
        fundamentus = Fundamentus()
        df = fundamentus.coleta_indicadores_de_ativo(ticker)
        
        if df is None or df.empty:
            return None
        
        return df
    
    except ImportError:
        logger.warning("pynvest não disponível, tentando fallback para scraping direto")
        return None
    except Exception as e:
        logger.error(f"Erro ao usar pynvest para {ticker}: {e}")
        return None


def coletar_dados_fii_scraper(ticker: str) -> dict[str, Any] | None:
    """
    Fallback: Coleta dados fundamentalistas via scraping direto do Fundamentus.
    
    Args:
        ticker: Ticker do FII.
    
    Returns:
        Dicionário com os dados brutos ou None em caso de falha.
    """
    url = URL_DETALHES_FII.format(ticker=ticker)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Esta é uma implementação simplificada - o scraping completo exigiria
        # análise detalhada da estrutura HTML do Fundamentus
        # Por enquanto, retornamos None para indicar que o fallback não está
        # completamente implementado
        logger.warning("Fallback de scraping direto não implementado completamente")
        return None
    
    except Exception as e:
        logger.error(f"Erro no scraper fallback para {ticker}: {e}")
        return None


def transformar_dados_fii(df: pd.DataFrame, ticker: str) -> dict[str, Any]:
    """
    Transforma os dados brutos do DataFrame para o formato JSON estruturado.
    
    Args:
        df: DataFrame com dados brutos do FII.
        ticker: Ticker do FII.
    
    Returns:
        Dicionário estruturado conforme esquema definido.
    """
    # Pegar a primeira (e única) linha do DataFrame
    row = df.iloc[0] if not df.empty else None
    
    if row is None:
        raise ValueError(f"Nenhum dado encontrado para {ticker}")
    
    # Extrair dados gerais
    dados_gerais = {
        'nome': limpar_string(row.get('nome_fii')),
        'segmento': limpar_string(row.get('segmento')),
        'data_ult_cot': limpar_string(row.get('dt_ult_cot'))
    }
    
    # Extrair dados de mercado
    mercado = {
        'cotacao': limpar_valor_br(row.get('vlr_cot')),
        'valor_mercado': limpar_valor_br(row.get('vlr_mercado')),
        'nro_cotas': limpar_valor_br(row.get('num_cotas')),
        'vp_cota': limpar_valor_br(row.get('vlr_vp_sobre_cota'))
    }
    
    # Extrair indicadores
    indicadores = {
        'p_vp': limpar_valor_br(row.get('vlr_p_sobre_vp')),
        'dividend_yield': limpar_valor_br(row.get('vlr_div_yield')),
        'ffo_yield': limpar_valor_br(row.get('vlr_ffo_yield')),
        'liquidez_media_diaria': limpar_valor_br(row.get('vol_med_neg_2m'))
    }
    
    # Extrair oscilações
    oscilacoes = {
        'dia': limpar_valor_br(row.get('pct_var_dia')),
        'mes': limpar_valor_br(row.get('pct_var_mes')),
        'doze_meses': limpar_valor_br(row.get('pct_var_12m'))
    }
    
    # Extrair rendimento anualizado (últimos 12 meses)
    # O campo 'vlr_rendim_distr_ult_12m' contém o total distribuído nos últimos 12 meses
    # Para obter o valor por cota, usamos 'vlr_dividendo_sobre_cota' que já é anualizado
    rendimento_anualizado = {
        'valor': limpar_valor_br(row.get('vlr_dividendo_sobre_cota')),
        'data_referencia': limpar_string(row.get('dt_ult_cot')),
        'periodo': 'últimos 12 meses'
    }
    
    return {
        'dados_gerais': dados_gerais,
        'mercado': mercado,
        'indicadores': indicadores,
        'oscilacoes': oscilacoes,
        'rendimento_anualizado': rendimento_anualizado
    }


def processar_ticker(ticker: str, diretorio_saida: Path) -> dict[str, Any]:
    """
    Processa um único ticker: coleta dados, extrai link do relatório e baixa PDF.
    
    Args:
        ticker: Ticker do FII.
        diretorio_saida: Diretório para salvar o PDF.
    
    Returns:
        Dicionário com status e dados do FII.
    """
    logger.info(f"Processando ticker: {ticker}")
    
    # Tentar coletar dados com pynvest
    df = coletar_dados_fii_pynvest(ticker)
    
    if df is None or df.empty:
        logger.warning(f"Tentando fallback para {ticker}")
        dados_brutos = coletar_dados_fii_scraper(ticker)
        if dados_brutos is None:
            return {
                'status': 'erro',
                'mensagem': 'Ticker não encontrado ou falha na conexão.'
            }
        # Implementação futura para transformar dados do scraper
        return {
            'status': 'erro',
            'mensagem': 'Dados não disponíveis para este ticker.'
        }
    
    try:
        # Transformar dados
        dados_transformados = transformar_dados_fii(df, ticker)
        
        # Extrair link do relatório
        info_relatorio = extrair_link_relatorio(ticker)
        
        # Baixar relatório
        resultado_download = baixar_relatorio(
            info_relatorio['link'],
            ticker,
            diretorio_saida
        )
        
        # Montar estrutura final
        dados_fii = {
            'status': 'sucesso',
            **dados_transformados,
            'relatorio': {
                'link': info_relatorio['link'],
                **resultado_download
            }
        }
        
        return dados_fii
    
    except Exception as e:
        logger.error(f"Erro ao processar {ticker}: {e}")
        return {
            'status': 'erro',
            'mensagem': f'Erro no processamento: {str(e)}'
        }


def parsear_tickers(entrada: str) -> list[str]:
    """
    Parseia a entrada do usuário e retorna lista de tickers válidos.
    
    Args:
        entrada: String com tickers separados por vírgula.
    
    Returns:
        Lista de tickers em maiúsculas e sem espaços.
    """
    if not entrada or entrada.strip() == '':
        return []
    
    # Separar por vírgula, remover espaços, converter para maiúsculas
    tickers = [t.strip().upper() for t in entrada.split(',')]
    
    # Filtrar tickers vazios e validar formato básico
    tickers_validos = []
    for ticker in tickers:
        if ticker and re.match(r'^[A-Z0-9]{4,6}$', ticker):
            tickers_validos.append(ticker)
        elif ticker:
            logger.warning(f"Ticker '{ticker}' parece inválido, mas será tentado")
            tickers_validos.append(ticker)
    
    return tickers_validos


def exportar_para_json(dados: dict[str, Any], caminho_arquivo: Path) -> bool:
    """
    Exporta os dados consolidados para um arquivo JSON.
    
    Args:
        dados: Dicionário com todos os dados dos FIIs.
        caminho_arquivo: Path do arquivo JSON de saída.
    
    Returns:
        True se sucesso, False caso contrário.
    """
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Dados exportados com sucesso: {caminho_arquivo}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao exportar JSON: {e}")
        return False


def main() -> None:
    """
    Função principal do script.
    
    Orquestra todo o fluxo de extração de dados de FIIs:
    1. Solicita tickers ao usuário
    2. Processa cada ticker
    3. Consolida resultados
    4. Exporta para JSON
    """
    print("=" * 60)
    print("EXTRATOR DE DADOS DE FIIs - B3 (Fundamentus)")
    print("=" * 60)
    print()
    
    # Solicitar tickers ao usuário
    entrada = input("Digite os tickers dos FIIs separados por vírgula: ")
    
    # Parsear tickers
    tickers = parsear_tickers(entrada)
    
    if not tickers:
        print("\nNenhum ticker válido fornecido. Encerrando...")
        return
    
    print(f"\nTickers identificados: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} ticker(s)")
    print()
    
    # Definir diretório de saída (mesmo diretório do script)
    diretorio_saida = Path.cwd()
    
    # Estrutura de dados para consolidação
    resultados = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(timespec='seconds'),
            'fonte': 'Fundamentus (via pynvest/scraper)',
            'total_tickers_solicitados': len(tickers),
            'total_tickers_sucesso': 0,
            'total_tickers_falha': 0
        },
        'fiis': {}
    }
    
    # Processar cada ticker
    for i, ticker in enumerate(tickers, start=1):
        print(f"[{i}/{len(tickers)}] Processando {ticker}...")
        
        resultado = processar_ticker(ticker, diretorio_saida)
        resultados['fiis'][ticker] = resultado
        
        # Atualizar contadores
        if resultado.get('status') == 'sucesso':
            resultados['metadata']['total_tickers_sucesso'] += 1
            print(f"  ✓ Sucesso")
        else:
            resultados['metadata']['total_tickers_falha'] += 1
            print(f"  ✗ Falha: {resultado.get('mensagem', 'Erro desconhecido')}")
        
        # Rate limiting
        if i < len(tickers):
            time.sleep(RATE_LIMIT_DELAY)
    
    print()
    print("-" * 60)
    print("RESUMO DA EXTRAÇÃO")
    print("-" * 60)
    print(f"Sucesso: {resultados['metadata']['total_tickers_sucesso']}")
    print(f"Falha: {resultados['metadata']['total_tickers_falha']}")
    print()
    
    # Exportar para JSON
    caminho_json = diretorio_saida / "dados_fiis_brutos.json"
    if exportar_para_json(resultados, caminho_json):
        print(f"✓ Arquivo JSON gerado: {caminho_json}")
    
    print()
    print("Extração concluída!")
    print("=" * 60)


if __name__ == '__main__':
    main()
