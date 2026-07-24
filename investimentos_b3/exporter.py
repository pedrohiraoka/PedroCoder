"""
Módulo responsável pela exportação de dados da carteira.

Exporta dados consolidados para JSON com estrutura hierárquica clara.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)


class ExporterError(Exception):
    """Exceção personalizada para erros no Exporter."""
    pass


class Exporter:
    """
    Exportador de dados da carteira para JSON.
    
    Gera arquivos JSON bem estruturados contendo:
    - Meta dados da exportação
    - Carteira ativa com métricas
    - Histórico de proventos
    - Resumo financeiro
    """
    
    def __init__(self, portfolio_manager: PortfolioManager):
        """
        Inicializa o exportador.
        
        Args:
            portfolio_manager: Instância do gerenciador de carteira.
        """
        self.portfolio_manager = portfolio_manager
    
    def export_to_json(
        self, 
        output_path: Optional[str] = None,
        include_raw_data: bool = False
    ) -> str:
        """
        Exporta snapshot completo da carteira para JSON.
        
        Args:
            output_path: Caminho do arquivo de saída. 
                        Se None, usa 'investimentos_export.json'.
            include_raw_data: Se True, inclui dados brutos adicionais.
            
        Returns:
            Caminho do arquivo gerado.
        """
        if output_path is None:
            output_path = "investimentos_export.json"
        
        output_file = Path(output_path)
        
        try:
            # Coleta todos os dados
            export_data = self._build_export_structure(include_raw_data)
            
            # Serializa para JSON com formatação bonita
            json_str = json.dumps(
                export_data,
                indent=2,
                ensure_ascii=False,
                default=str  # Para lidar com objetos datetime
            )
            
            # Escreve no arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            logger.info(f"Dados exportados com sucesso para {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            raise ExporterError(f"Falha na exportação: {str(e)}")
    
    def _build_export_structure(self, include_raw_data: bool = False) -> Dict[str, Any]:
        """
        Constrói a estrutura hierárquica de dados para exportação.
        
        Args:
            include_raw_data: Se True, inclui dados brutos adicionais.
            
        Returns:
            Dicionário com estrutura completa de exportação.
        """
        # Obtém métricas calculadas
        metrics = self.portfolio_manager.calculate_portfolio_metrics()
        
        # Obtém resumo financeiro
        summary = self.portfolio_manager.get_portfolio_summary()
        
        # Obtém histórico de proventos
        dividend_history = self.portfolio_manager.get_dividend_history()
        
        # Monta estrutura principal
        export_data = {
            "meta_dados": {
                "versao_exportacao": "1.0",
                "data_geracao": datetime.now().isoformat(),
                "fonte_dados": {
                    "cotacoes": "brasa-marketdata (B3 oficial)",
                    "fundamentalistas": "pynvest (Fundamentus)"
                },
                "moeda": "BRL",
                "mercado": "B3 - Brasil Bolsa Balcão"
            },
            "resumo_financeiro": summary,
            "carteira_ativa": self._format_active_portfolio(metrics),
            "historico_proventos": self._format_dividend_history(dividend_history),
        }
        
        # Adiciona dados brutos se solicitado
        if include_raw_data:
            export_data["dados_brutos"] = {
                "ativos_raw": self.portfolio_manager.get_all_assets(),
                "proventos_raw": dividend_history
            }
        
        return export_data
    
    def _format_active_portfolio(self, metrics: list) -> Dict[str, Any]:
        """
        Formata a carteira ativa para exportação.
        
        Args:
            metrics: Lista de métricas dos ativos.
            
        Returns:
            Dicionário formatado com carteira ativa.
        """
        # Separa por tipo de ativo
        acoes = []
        fiis = []
        
        for metric in metrics:
            asset_data = {
                "ticker": metric['ticker'],
                "quantidade": metric['quantity'],
                "preco_medio": metric['average_price'],
                "cotacao_atual": metric['current_price'],
                "valor_investido": metric['invested_value'],
                "valor_mercado": metric['market_value'],
                "lucro_prejuizo": metric['profit_loss'],
                "lucro_prejuizo_percentual": metric['profit_loss_pct'],
                "total_proventos_recebidos": metric['total_dividends_received'],
                "dividend_yield_on_cost": metric['dividend_yield_on_cost'],
                "indicadores_fundamentalistas": metric['fundamentals'],
                "ultima_atualizacao": metric['last_updated']
            }
            
            if metric['asset_type'] == 'FII':
                fiis.append(asset_data)
            else:
                acoes.append(asset_data)
        
        return {
            "total_ativos": len(metrics),
            "acoes": {
                "quantidade": len(acoes),
                "lista": acoes
            },
            "fiis": {
                "quantidade": len(fiis),
                "lista": fiis
            }
        }
    
    def _format_dividend_history(self, dividends: list) -> Dict[str, Any]:
        """
        Formata histórico de proventos para exportação.
        
        Args:
            dividends: Lista de registros de proventos.
            
        Returns:
            Dicionário formatado com histórico.
        """
        # Agrupa por ticker
        by_ticker = {}
        total_by_type = {'DIVIDENDO': 0, 'JCP': 0}
        
        for div in dividends:
            ticker = div['ticker']
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            
            by_ticker[ticker].append({
                "data": div['date'],
                "tipo": div['record_type'],
                "valor_por_cota": div['value_per_share'],
                "valor_total": div['total_value'],
                "registrado_em": div['created_at']
            })
            
            # Soma por tipo
            record_type = div['record_type']
            if record_type in total_by_type:
                total_by_type[record_type] += div['total_value']
        
        return {
            "total_registros": len(dividends),
            "total_por_tipo": {
                "dividendos": round(total_by_type['DIVIDENDO'], 2),
                "jcp": round(total_by_type['JCP'], 2),
                "geral": round(total_by_type['DIVIDENDO'] + total_by_type['JCP'], 2)
            },
            "por_ativo": by_ticker
        }
    
    def export_to_json_string(self, include_raw_data: bool = False) -> str:
        """
        Exporta dados como string JSON (sem salvar em arquivo).
        
        Args:
            include_raw_data: Se True, inclui dados brutos adicionais.
            
        Returns:
            String JSON formatada.
        """
        export_data = self._build_export_structure(include_raw_data)
        
        return json.dumps(
            export_data,
            indent=2,
            ensure_ascii=False,
            default=str
        )
    
    def validate_export(self, output_path: str) -> bool:
        """
        Valida se um arquivo JSON exportado é válido.
        
        Args:
            output_path: Caminho do arquivo a validar.
            
        Returns:
            True se válido, False caso contrário.
        """
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verifica estrutura básica
            required_keys = ['meta_dados', 'resumo_financeiro', 'carteira_ativa', 'historico_proventos']
            for key in required_keys:
                if key not in data:
                    logger.error(f"Chave obrigatória ausente: {key}")
                    return False
            
            logger.info(f"Arquivo {output_path} validado com sucesso.")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}")
            return False
