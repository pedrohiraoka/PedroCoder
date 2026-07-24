"""
Módulo responsável pela coleta de dados financeiros.

Integração com:
- brasa-marketdata: Para cotações e históricos oficiais da B3
- pynvest: Para indicadores fundamentalistas do Fundamentus
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import pandas as pd

# Tentativa de importação das bibliotecas externas
try:
    import brasa as brasa_marketdata
    BRASA_AVAILABLE = True
except ImportError:
    BRASA_AVAILABLE = False
    brasa_marketdata = None

try:
    import pynvest
    PYNVEST_AVAILABLE = True
except ImportError:
    PYNVEST_AVAILABLE = False
    pynvest = None

logger = logging.getLogger(__name__)


class DataFetcherError(Exception):
    """Exceção personalizada para erros no DataFetcher."""
    pass


class DataFetcher:
    """
    Classe responsável por buscar dados de mercado e fundamentalistas.
    
    Utiliza brasa-marketdata para dados de cotação e histórico,
    e pynvest para indicadores fundamentalistas.
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Inicializa o DataFetcher.
        
        Args:
            use_cache: Se True, utiliza o cache local do brasa quando disponível.
        """
        self.use_cache = use_cache
        self._brasa_initialized = False
        
        if not BRASA_AVAILABLE:
            logger.warning("brasa-marketdata não disponível. Dados de mercado indisponíveis.")
        
        if not PYNVEST_AVAILABLE:
            logger.warning("pynvest não disponível. Dados fundamentalistas indisponíveis.")
    
    def _ensure_brasa_ready(self) -> None:
        """Garante que o brasa esteja pronto para uso."""
        if not BRASA_AVAILABLE:
            raise DataFetcherError("brasa-marketdata não está instalado.")
        
        if not self._brasa_initialized:
            # O brasa gerencia seu próprio cache internamente
            self._brasa_initialized = True
            logger.info("brasa-marketdata inicializado com sucesso.")
    
    def get_current_quote(self, ticker: str) -> Optional[float]:
        """
        Obtém a cotação atual de um ativo.
        
        Args:
            ticker: Ticker do ativo (ex: 'PETR4', 'HGLG11').
            
        Returns:
            Preço atual do ativo ou None se não disponível.
        """
        try:
            self._ensure_brasa_ready()
            
            # brasa usa a função get_quotes para obter cotações
            # O formato pode variar, ajustamos conforme necessário
            df = brasa_marketdata.get_quotes(tickers=ticker)
            
            if df is not None and not df.empty:
                # Tenta encontrar a coluna de preço de fechamento ou último preço
                if 'Close' in df.columns:
                    return float(df['Close'].iloc[-1])
                elif 'close' in df.columns:
                    return float(df['close'].iloc[-1])
                elif 'PRECO' in df.columns:
                    return float(df['PRECO'].iloc[-1])
                else:
                    # Pega o último valor numérico disponível
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                    if len(numeric_cols) > 0:
                        return float(df[numeric_cols[0]].iloc[-1])
            
            logger.warning(f"Cotação não encontrada para {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar cotação para {ticker}: {str(e)}")
            return None
    
    def get_historical_data(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Obtém dados históricos de um ativo.
        
        Args:
            ticker: Ticker do ativo.
            start_date: Data inicial no formato 'YYYY-MM-DD'.
            end_date: Data final no formato 'YYYY-MM-DD' ou None para hoje.
            
        Returns:
            DataFrame com dados históricos ou None se não disponível.
        """
        try:
            self._ensure_brasa_ready()
            
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            df = brasa_marketdata.get_history(
                tickers=ticker,
                start=start_date,
                end=end_date
            )
            
            if df is not None and not df.empty:
                return df
            
            logger.warning(f"Dados históricos não encontrados para {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico para {ticker}: {str(e)}")
            return None
    
    def get_fundamental_indicators(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Obtém indicadores fundamentalistas de um ativo.
        
        Args:
            ticker: Ticker do ativo.
            
        Returns:
            Dicionário com indicadores ou None se não disponível.
        """
        if not PYNVEST_AVAILABLE:
            logger.warning("pynvest não disponível.")
            return None
        
        try:
            # pynvest fornece scraping do Fundamentus
            # A API pode variar, tentamos abordagens diferentes
            
            # Tenta obter dados completos da empresa
            data = pynvest.get_complete_info(ticker)
            
            if data:
                indicators = {
                    'p_l': data.get('p_l'),
                    'p_vp': data.get('p_vp'),
                    'dividend_yield': data.get('dividend_yield'),
                    'roe': data.get('roe'),
                    'roa': data.get('roa'),
                    'margem_liquida': data.get('margem_liquida'),
                    'ebitda': data.get('ebitda'),
                    'receita_liquida': data.get('receita_liquida'),
                    'valor_mercado': data.get('valor_mercado'),
                    'valor_empresa': data.get('valor_empresa'),
                    'numero_acoes': data.get('numero_acoes'),
                }
                
                # Filtra valores None
                indicators = {k: v for k, v in indicators.items() if v is not None}
                
                if indicators:
                    return indicators
            
            # Fallback: tenta abordagem alternativa
            logger.info(f"Tentando abordagem alternativa para {ticker}")
            return self._get_fundamentals_fallback(ticker)
            
        except Exception as e:
            logger.error(f"Erro ao buscar fundamentalistas para {ticker}: {str(e)}")
            return self._get_fundamentals_fallback(ticker)
    
    def _get_fundamentals_fallback(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Abordagem fallback para obter fundamentalistas.
        
        Args:
            ticker: Ticker do ativo.
            
        Returns:
            Dicionário com indicadores ou None.
        """
        try:
            # Tenta usar funções específicas do pynvest
            if hasattr(pynvest, 'get_price_to_earnings'):
                p_l = pynvest.get_price_to_earnings(ticker)
            else:
                p_l = None
            
            if hasattr(pynvest, 'get_dividend_yield'):
                dy = pynvest.get_dividend_yield(ticker)
            else:
                dy = None
            
            if hasattr(pynvest, 'get_price_to_book'):
                p_vp = pynvest.get_price_to_book(ticker)
            else:
                p_vp = None
            
            indicators = {}
            if p_l is not None:
                indicators['p_l'] = p_l
            if dy is not None:
                indicators['dividend_yield'] = dy
            if p_vp is not None:
                indicators['p_vp'] = p_vp
            
            return indicators if indicators else None
            
        except Exception as e:
            logger.error(f"Fallback também falhou para {ticker}: {str(e)}")
            return None
    
    def get_multiple_quotes(self, tickers: List[str]) -> Dict[str, Optional[float]]:
        """
        Obtém cotações múltiplas de uma vez.
        
        Args:
            tickers: Lista de tickers.
            
        Returns:
            Dicionário mapeando ticker -> cotação.
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.get_current_quote(ticker)
        return results
    
    def get_multiple_fundamentals(
        self, 
        tickers: List[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Obtém indicadores fundamentalistas múltiplos de uma vez.
        
        Args:
            tickers: Lista de tickers.
            
        Returns:
            Dicionário mapeando ticker -> indicadores.
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.get_fundamental_indicators(ticker)
        return results
