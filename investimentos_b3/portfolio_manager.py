"""
Módulo responsável pelo gerenciamento da carteira de investimentos.

Gerencia:
- Adição/remoção de ativos
- Cálculos financeiros (lucro/prejuízo, dividend yield on cost)
- Persistência em SQLite
- Registro de proventos
"""

import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


@dataclass
class Asset:
    """Representa um ativo na carteira."""
    ticker: str
    quantity: int
    average_price: float
    asset_type: str = 'ACAO'  # ACAO ou FII
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class DividendRecord:
    """Representa um registro de provento recebido."""
    ticker: str
    date: str
    value_per_share: float
    total_value: float
    record_type: str = 'DIVIDENDO'  # DIVIDENDO ou JCP
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class PortfolioManagerError(Exception):
    """Exceção personalizada para erros no PortfolioManager."""
    pass


class PortfolioManager:
    """
    Gerenciador da carteira de investimentos.
    
    Responsável por:
    - CRUD de ativos
    - Registro de proventos
    - Cálculos financeiros
    - Persistência em SQLite
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador da carteira.
        
        Args:
            db_path: Caminho para o banco de dados SQLite. 
                     Se None, usa 'carteira.db' no diretório atual.
        """
        if db_path is None:
            db_path = "carteira.db"
        
        self.db_path = Path(db_path)
        self.data_fetcher = DataFetcher()
        self._init_database()
    
    def _init_database(self) -> None:
        """Inicializa o banco de dados com as tabelas necessárias."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de ativos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL,
                    average_price REAL NOT NULL,
                    asset_type TEXT NOT NULL DEFAULT 'ACAO',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Tabela de proventos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dividends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    value_per_share REAL NOT NULL,
                    total_value REAL NOT NULL,
                    record_type TEXT NOT NULL DEFAULT 'DIVIDENDO',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (ticker) REFERENCES assets(ticker)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_ticker ON assets(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dividends_ticker ON dividends(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dividends_date ON dividends(date)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Banco de dados inicializado em {self.db_path}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
            raise PortfolioManagerError(f"Falha ao inicializar DB: {str(e)}")
    
    def add_asset(
        self, 
        ticker: str, 
        quantity: int, 
        average_price: float,
        asset_type: str = 'ACAO'
    ) -> bool:
        """
        Adiciona ou atualiza um ativo na carteira.
        
        Args:
            ticker: Ticker do ativo (ex: 'PETR4', 'HGLG11').
            quantity: Quantidade de cotas/ações.
            average_price: Preço médio de compra.
            asset_type: Tipo de ativo ('ACAO' ou 'FII').
            
        Returns:
            True se sucesso, False caso contrário.
        """
        try:
            ticker = ticker.upper().strip()
            
            if quantity <= 0:
                raise ValueError("Quantidade deve ser positiva.")
            
            if average_price <= 0:
                raise ValueError("Preço médio deve ser positivo.")
            
            if asset_type not in ['ACAO', 'FII']:
                raise ValueError("Tipo de ativo deve ser 'ACAO' ou 'FII'.")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # Verifica se já existe
            cursor.execute('SELECT quantity, average_price FROM assets WHERE ticker = ?', (ticker,))
            existing = cursor.fetchone()
            
            if existing:
                # Atualiza: calcula novo preço médio ponderado
                old_qty, old_avg_price = existing
                new_total_value = (old_qty * old_avg_price) + (quantity * average_price)
                new_total_qty = old_qty + quantity
                new_avg_price = new_total_value / new_total_qty
                
                cursor.execute('''
                    UPDATE assets 
                    SET quantity = ?, average_price = ?, updated_at = ?
                    WHERE ticker = ?
                ''', (new_total_qty, new_avg_price, now, ticker))
                
                logger.info(f"Ativo {ticker} atualizado. Novo preço médio: R$ {new_avg_price:.2f}")
            else:
                # Insert novo
                cursor.execute('''
                    INSERT INTO assets (ticker, quantity, average_price, asset_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ticker, quantity, average_price, asset_type, now, now))
                
                logger.info(f"Ativo {ticker} adicionado com {quantity} unidades a R$ {average_price:.2f}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar ativo {ticker}: {str(e)}")
            return False
    
    def remove_asset(self, ticker: str) -> bool:
        """
        Remove um ativo da carteira.
        
        Args:
            ticker: Ticker do ativo a remover.
            
        Returns:
            True se removido, False se não encontrado ou erro.
        """
        try:
            ticker = ticker.upper().strip()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM assets WHERE ticker = ?', (ticker,))
            
            if cursor.rowcount > 0:
                logger.info(f"Ativo {ticker} removido da carteira.")
                conn.commit()
                conn.close()
                return True
            else:
                logger.warning(f"Ativo {ticker} não encontrado.")
                conn.close()
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover ativo {ticker}: {str(e)}")
            return False
    
    def get_all_assets(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os ativos da carteira.
        
        Returns:
            Lista de dicionários com dados dos ativos.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ticker, quantity, average_price, asset_type, created_at, updated_at
                FROM assets
                ORDER BY ticker
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            assets = []
            for row in rows:
                assets.append({
                    'ticker': row[0],
                    'quantity': row[1],
                    'average_price': row[2],
                    'asset_type': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                })
            
            return assets
            
        except Exception as e:
            logger.error(f"Erro ao buscar ativos: {str(e)}")
            return []
    
    def get_asset(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um ativo específico.
        
        Args:
            ticker: Ticker do ativo.
            
        Returns:
            Dicionário com dados do ativo ou None se não encontrado.
        """
        assets = self.get_all_assets()
        for asset in assets:
            if asset['ticker'].upper() == ticker.upper():
                return asset
        return None
    
    def register_dividend(
        self,
        ticker: str,
        date: str,
        value_per_share: float,
        record_type: str = 'DIVIDENDO'
    ) -> bool:
        """
        Registra um provento recebido.
        
        Args:
            ticker: Ticker do ativo.
            date: Data do provento (YYYY-MM-DD).
            value_per_share: Valor por cota/ação.
            record_type: Tipo ('DIVIDENDO' ou 'JCP').
            
        Returns:
            True se sucesso, False caso contrário.
        """
        try:
            ticker = ticker.upper().strip()
            
            # Verifica se o ativo existe na carteira
            asset = self.get_asset(ticker)
            if not asset:
                logger.error(f"Ativo {ticker} não encontrado na carteira.")
                return False
            
            quantity = asset['quantity']
            total_value = quantity * value_per_share
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO dividends (ticker, date, value_per_share, total_value, record_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticker, date, value_per_share, total_value, record_type, now))
            
            conn.commit()
            conn.close()
            
            logger.info(
                f"Provento registrado: {ticker} - {record_type} de R$ {value_per_share:.2f}/cota "
                f"(total: R$ {total_value:.2f})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar provento: {str(e)}")
            return False
    
    def get_dividend_history(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém histórico de proventos.
        
        Args:
            ticker: Ticker específico ou None para todos.
            
        Returns:
            Lista de registros de proventos.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if ticker:
                cursor.execute('''
                    SELECT id, ticker, date, value_per_share, total_value, record_type, created_at
                    FROM dividends
                    WHERE ticker = ?
                    ORDER BY date DESC
                ''', (ticker.upper(),))
            else:
                cursor.execute('''
                    SELECT id, ticker, date, value_per_share, total_value, record_type, created_at
                    FROM dividends
                    ORDER BY date DESC
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            dividends = []
            for row in rows:
                dividends.append({
                    'id': row[0],
                    'ticker': row[1],
                    'date': row[2],
                    'value_per_share': row[3],
                    'total_value': row[4],
                    'record_type': row[5],
                    'created_at': row[6]
                })
            
            return dividends
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de proventos: {str(e)}")
            return []
    
    def get_total_dividends_by_ticker(self, ticker: str) -> float:
        """
        Obtém total de proventos recebidos de um ativo.
        
        Args:
            ticker: Ticker do ativo.
            
        Returns:
            Soma total dos proventos.
        """
        dividends = self.get_dividend_history(ticker)
        return sum(d['total_value'] for d in dividends)
    
    def calculate_portfolio_metrics(self) -> List[Dict[str, Any]]:
        """
        Calcula métricas completas da carteira.
        
        Returns:
            Lista de ativos com métricas calculadas.
        """
        assets = self.get_all_assets()
        metrics = []
        
        for asset in assets:
            ticker = asset['ticker']
            quantity = asset['quantity']
            avg_price = asset['average_price']
            
            # Busca cotação atual
            current_price = self.data_fetcher.get_current_quote(ticker)
            
            # Busca indicadores fundamentalistas
            fundamentals = self.data_fetcher.get_fundamental_indicators(ticker)
            
            # Calcula valores
            invested_value = quantity * avg_price
            market_value = quantity * current_price if current_price else 0
            profit_loss = market_value - invested_value
            profit_loss_pct = (profit_loss / invested_value * 100) if invested_value > 0 else 0
            
            # Calcula dividend yield on cost
            total_dividends = self.get_total_dividends_by_ticker(ticker)
            dy_on_cost = (total_dividends / invested_value * 100) if invested_value > 0 else 0
            
            metric = {
                'ticker': ticker,
                'asset_type': asset['asset_type'],
                'quantity': quantity,
                'average_price': round(avg_price, 2),
                'current_price': round(current_price, 2) if current_price else None,
                'invested_value': round(invested_value, 2),
                'market_value': round(market_value, 2),
                'profit_loss': round(profit_loss, 2),
                'profit_loss_pct': round(profit_loss_pct, 2),
                'total_dividends_received': round(total_dividends, 2),
                'dividend_yield_on_cost': round(dy_on_cost, 2),
                'fundamentals': fundamentals or {},
                'last_updated': datetime.now().isoformat()
            }
            
            metrics.append(metric)
        
        return metrics
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo financeiro da carteira.
        
        Returns:
            Dicionário com totais e percentuais.
        """
        metrics = self.calculate_portfolio_metrics()
        
        total_invested = sum(m['invested_value'] for m in metrics)
        total_market = sum(m['market_value'] for m in metrics)
        total_profit_loss = total_market - total_invested
        total_profit_loss_pct = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        total_dividends = sum(m['total_dividends_received'] for m in metrics)
        
        # Agrupa por tipo
        by_type = {}
        for m in metrics:
            asset_type = m['asset_type']
            if asset_type not in by_type:
                by_type[asset_type] = {'count': 0, 'invested': 0, 'market': 0}
            by_type[asset_type]['count'] += 1
            by_type[asset_type]['invested'] += m['invested_value']
            by_type[asset_type]['market'] += m['market_value']
        
        return {
            'total_invested': round(total_invested, 2),
            'total_market_value': round(total_market, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'total_profit_loss_pct': round(total_profit_loss_pct, 2),
            'total_dividends_received': round(total_dividends, 2),
            'assets_count': len(metrics),
            'by_type': {
                k: {
                    'count': v['count'],
                    'invested': round(v['invested'], 2),
                    'market': round(v['market'], 2)
                }
                for k, v in by_type.items()
            },
            'generated_at': datetime.now().isoformat()
        }
