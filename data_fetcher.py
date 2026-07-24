"""
Módulo responsável por buscar dados financeiros via yfinance.

Este módulo implementa funções para obter cotações atuais, histórico
de dividendos e outras informações de ativos da bolsa brasileira (B3).
Trata automaticamente o sufixo .SA para ativos brasileiros.
"""

import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from models import Provento, TipoProvento


def normalizar_ticker(ticker: str) -> str:
    """
    Normaliza o ticker adicionando o sufixo .SA se necessário.

    Args:
        ticker: O código do ativo (ex: PETR4, HGLG11).

    Returns:
        O ticker formatado para busca no yfinance (ex: PETR4.SA).
    """
    ticker = ticker.upper().strip()
    if not ticker.endswith(".SA"):
        return f"{ticker}.SA"
    return ticker


def remover_sufixo_sa(ticker: str) -> str:
    """
    Remove o sufixo .SA de um ticker para exibição.

    Args:
        ticker: O código do ativo com ou sem sufixo.

    Returns:
        O ticker sem o sufixo .SA.
    """
    ticker = ticker.upper().strip()
    if ticker.endswith(".SA"):
        return ticker[:-3]
    return ticker


def obter_ticker_yf(ticker: str) -> yf.Ticker:
    """
    Obtém um objeto Ticker do yfinance.

    Args:
        ticker: O código do ativo.

    Returns:
        Um objeto yf.Ticker configurado para o ativo.
    """
    ticker_normalizado = normalizar_ticker(ticker)
    return yf.Ticker(ticker_normalizado)


def obter_cotacao_atual(ticker: str) -> Optional[float]:
    """
    Obtém a cotação atual de um ativo.

    Args:
        ticker: O código do ativo.

    Returns:
        O preço atual do ativo ou None se houver falha.
    """
    try:
        ticker_yf = obter_ticker_yf(ticker)
        # Tenta obter o preço de fechamento mais recente
        info = ticker_yf.info
        # yfinance pode retornar diferentes chaves dependendo do ativo
        preco = info.get('regularMarketPrice') or info.get('currentPrice')
        
        if preco is not None:
            return float(preco)
        
        # Fallback: tentar obter via history
        hist = ticker_yf.history(period="1d")
        if not hist.empty and 'Close' in hist.columns:
            return float(hist['Close'].iloc[-1])
        
        return None
    except Exception as e:
        print(f"[ERRO] Falha ao obter cotação para {ticker}: {e}")
        return None


def obter_historico_dividendos(
    ticker: str, 
    periodo_anos: int = 5
) -> List[Provento]:
    """
    Obtém o histórico de dividendos e proventos de um ativo.

    Args:
        ticker: O código do ativo.
        periodo_anos: Quantidade de anos de histórico para buscar.

    Returns:
        Uma lista de objetos Provento ordenados por data (mais recente primeiro).
    """
    try:
        ticker_yf = obter_ticker_yf(ticker)
        ticker_limpo = remover_sufixo_sa(ticker)
        
        # Buscar histórico de dividends e splits
        # yfinance retorna dividends como uma Series
        dividends = ticker_yf.dividends
        
        if dividends is None or dividends.empty:
            return []
        
        # Filtrar apenas os últimos N anos
        data_inicio = date.today() - timedelta(days=periodo_anos * 365)
        
        # Converter índice para timezone-naive para comparação
        dividends_naive = dividends.copy()
        if hasattr(dividends.index, 'tz') and dividends.index.tz is not None:
            dividends_naive.index = dividends.index.tz_localize(None)
        
        # Filtrar por data
        mask = dividends_naive.index >= pd.Timestamp(data_inicio)
        dividends_filtrado = dividends_naive[mask]
        
        proventos = []
        for data_pgto, valor in dividends_filtrado.items():
            # Determinar tipo de provento
            # yfinance não diferencia claramente entre dividendo e JCP
            # Para simplificação, consideramos como DIVIDENDO
            # Em uma implementação mais avançada, poderíamos consultar
            # fontes adicionais para classificação
            tipo_provento = TipoProvento.DIVIDENDO
            
            # Para FIIs, usamos RENDIMENTO
            # Isso é uma heurística baseada no padrão do ticker
            if ticker_limpo[-1] == '1' and ticker_limpo[-2].isdigit():
                # Padrão de FII (ex: HGLG11, MXRF11)
                tipo_provento = TipoProvento.RENDIMENTO
            
            provento = Provento(
                data=data_pgto.date(),
                valor_por_cota=float(valor),
                tipo=tipo_provento,
                ticker=ticker_limpo
            )
            proventos.append(provento)
        
        # Ordenar por data (mais recente primeiro)
        proventos.sort(key=lambda p: p.data, reverse=True)
        return proventos
        
    except Exception as e:
        print(f"[ERRO] Falha ao obter dividendos para {ticker}: {e}")
        return []


def obter_informacoes_ativo(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Obtém informações gerais sobre um ativo.

    Args:
        ticker: O código do ativo.

    Returns:
        Um dicionário com informações do ativo ou None se houver falha.
    """
    try:
        ticker_yf = obter_ticker_yf(ticker)
        info = ticker_yf.info
        
        if not info:
            return None
        
        return {
            "nome": info.get('longName', info.get('shortName', 'N/A')),
            "setor": info.get('sector', info.get('industry', 'N/A')),
            "mercado": info.get('market', 'B3'),
            "tipo": determinar_tipo_ativo(ticker, info),
        }
    except Exception as e:
        print(f"[ERRO] Falha ao obter informações para {ticker}: {e}")
        return None


def determinar_tipo_ativo(ticker: str, info: Optional[Dict] = None) -> str:
    """
    Determina se um ativo é AÇÃO ou FII baseado no ticker ou informações.

    Args:
        ticker: O código do ativo.
        info: Informações opcionais do yfinance.

    Returns:
        'FII' ou 'ACAO'.
    """
    ticker_limpo = remover_sufixo_sa(ticker).upper()
    
    # Heurística baseada no padrão do ticker
    # FIIs geralmente terminam em 11 (ex: HGLG11, MXRF11)
    if len(ticker_limpo) >= 2 and ticker_limpo[-2:].isdigit():
        if ticker_limpo[-2:] == '11':
            return 'FII'
    
    # Ações geralmente terminam em 3, 4, 5, 6, 7, 8, 9, 10
    # ON (3), PN (4), UNT (5), etc.
    ultimo_caractere = ticker_limpo[-1]
    if ultimo_caractere.isdigit() and ultimo_caractere in '3456789':
        return 'ACAO'
    
    # Se terminar em 10 também é ação (UNT)
    if len(ticker_limpo) >= 2 and ticker_limpo[-2:] == '10':
        return 'ACAO'
    
    # Default: assumir AÇÃO
    return 'ACAO'


def validar_ticker(ticker: str) -> bool:
    """
    Valida se um ticker existe e está disponível no yfinance.

    Args:
        ticker: O código do ativo.

    Returns:
        True se o ticker for válido, False caso contrário.
    """
    try:
        ticker_yf = obter_ticker_yf(ticker)
        # Tenta acessar informações básicas
        info = ticker_yf.info
        # Verifica se há algum dado relevante
        return bool(info and (info.get('regularMarketPrice') or info.get('symbol')))
    except Exception:
        return False


def obter_yield_on_cost(ticker: str, preco_medio: float) -> Optional[float]:
    """
    Calcula o Yield on Cost (YoC) baseado nos últimos 12 meses de dividendos.

    Args:
        ticker: O código do ativo.
        preco_medio: O preço médio de compra do investidor.

    Returns:
        O YoC em percentual (ex: 8.5 para 8.5%) ou None se houver falha.
    """
    try:
        proventos = obter_historico_dividendos(ticker, periodo_anos=1)
        
        if not proventos:
            return None
        
        total_dividendos_12m = sum(p.valor_por_cota for p in proventos)
        
        if preco_medio <= 0:
            return None
        
        yoc = (total_dividendos_12m / preco_medio) * 100
        return round(yoc, 2)
    except Exception as e:
        print(f"[ERRO] Falha ao calcular YoC para {ticker}: {e}")
        return None


def obter_dividend_yield_atual(ticker: str) -> Optional[float]:
    """
    Obtém o Dividend Yield atual (últimos 12 meses) baseado no preço atual.

    Args:
        ticker: O código do ativo.

    Returns:
        O DY em percentual ou None se houver falha.
    """
    try:
        proventos = obter_historico_dividendos(ticker, periodo_anos=1)
        preco_atual = obter_cotacao_atual(ticker)
        
        if not proventos or preco_atual is None or preco_atual <= 0:
            return None
        
        total_dividendos_12m = sum(p.valor_por_cota for p in proventos)
        dy = (total_dividendos_12m / preco_atual) * 100
        return round(dy, 2)
    except Exception as e:
        print(f"[ERRO] Falha ao calcular DY para {ticker}: {e}")
        return None
