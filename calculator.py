"""
Módulo de cálculos financeiros para a carteira de investimentos.

Este módulo contém a lógica de negócio pura para calcular métricas
como valor de mercado, lucro/prejuízo, yield on cost, dividend yield, etc.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from dataclasses import dataclass

from models import Ativo, Provento, Carteira, TipoAtivo
import data_fetcher


@dataclass
class AtivoConsolidado:
    """
    Representa um ativo com dados consolidados (carteira + mercado).

    Attributes:
        ticker: Código do ativo.
        tipo: Tipo do ativo (ACAO ou FII).
        quantidade: Quantidade possuída.
        preco_medio: Preço médio de compra.
        preco_atual: Cotação atual do ativo.
        valor_investido: Valor total investido (quantidade * preço médio).
        valor_mercado: Valor atual de mercado (quantidade * preço atual).
        lucro_prejuizo: Diferença entre valor de mercado e valor investido.
        lucro_prejuizo_percentual: Lucro/prejuízo em porcentagem.
        yield_on_cost: Retorno sobre custo (dividendos 12m / preço médio).
        dividend_yield: Dividend yield atual (dividendos 12m / preço atual).
        total_proventos_12m: Total de proventos recebidos nos últimos 12 meses.
        total_proventos_recebidos: Total histórico de proventos recebidos.
        proventos: Lista de proventos do ativo.
        erro_cotacao: Indica se houve erro ao buscar cotação.
        erro_dividendos: Indica se houve erro ao buscar dividendos.
    """
    ticker: str
    tipo: TipoAtivo
    quantidade: float
    preco_medio: float
    preco_atual: Optional[float]
    valor_investido: float
    valor_mercado: Optional[float]
    lucro_prejuizo: Optional[float]
    lucro_prejuizo_percentual: Optional[float]
    yield_on_cost: Optional[float]
    dividend_yield: Optional[float]
    total_proventos_12m: float
    total_proventos_recebidos: float
    proventos: List[Provento]
    erro_cotacao: bool = False
    erro_dividendos: bool = False

    def to_dict(self) -> dict:
        """Converte o ativo consolidado para dicionário."""
        return {
            "ticker": self.ticker,
            "tipo": self.tipo.value,
            "quantidade": self.quantidade,
            "preco_medio": round(self.preco_medio, 2),
            "preco_atual": round(self.preco_atual, 2) if self.preco_atual else None,
            "valor_investido": round(self.valor_investido, 2),
            "valor_mercado": round(self.valor_mercado, 2) if self.valor_mercado else None,
            "lucro_prejuizo": round(self.lucro_prejuizo, 2) if self.lucro_prejuizo else None,
            "lucro_prejuizo_percentual": round(self.lucro_prejuizo_percentual, 2) if self.lucro_prejuizo_percentual else None,
            "yield_on_cost": self.yield_on_cost,
            "dividend_yield": self.dividend_yield,
            "total_proventos_12m": round(self.total_proventos_12m, 2),
            "total_proventos_recebidos": round(self.total_proventos_recebidos, 2),
            "proventos": [p.to_dict() for p in self.proventos],
            "erro_cotacao": self.erro_cotacao,
            "erro_dividendos": self.erro_dividendos
        }


@dataclass
class ResumoCarteira:
    """
    Representa o resumo consolidado da carteira.

    Attributes:
        valor_total_investido: Soma de todos os valores investidos.
        valor_total_mercado: Soma de todos os valores de mercado atuais.
        lucro_prejuizo_total: Lucro/prejuízo total da carteira.
        lucro_prejuizo_percentual: Lucro/prejuízo percentual da carteira.
        total_proventos_12m: Total de proventos recebidos nos últimos 12 meses.
        yield_on_cost_carteira: Yield on cost médio ponderado da carteira.
        dividend_yield_carteira: Dividend yield médio ponderado da carteira.
        quantidade_ativos: Número de ativos na carteira.
        data_atualizacao: Data/hora da última atualização.
    """
    valor_total_investido: float
    valor_total_mercado: Optional[float]
    lucro_prejuizo_total: Optional[float]
    lucro_prejuizo_percentual: Optional[float]
    total_proventos_12m: float
    yield_on_cost_carteira: Optional[float]
    dividend_yield_carteira: Optional[float]
    quantidade_ativos: int
    data_atualizacao: str

    def to_dict(self) -> dict:
        """Converte o resumo para dicionário."""
        return {
            "valor_total_investido": round(self.valor_total_investido, 2),
            "valor_total_mercado": round(self.valor_total_mercado, 2) if self.valor_total_mercado else None,
            "lucro_prejuizo_total": round(self.lucro_prejuizo_total, 2) if self.lucro_prejuizo_total else None,
            "lucro_prejuizo_percentual": round(self.lucro_prejuizo_percentual, 2) if self.lucro_prejuizo_percentual else None,
            "total_proventos_12m": round(self.total_proventos_12m, 2),
            "yield_on_cost_carteira": self.yield_on_cost_carteira,
            "dividend_yield_carteira": self.dividend_yield_carteira,
            "quantidade_ativos": self.quantidade_ativos,
            "data_atualizacao": self.data_atualizacao
        }


def calcular_valor_mercado(ativo: Ativo, preco_atual: Optional[float]) -> Optional[float]:
    """
    Calcula o valor de mercado de um ativo.

    Args:
        ativo: Objeto Ativo.
        preco_atual: Preço atual do ativo.

    Returns:
        Valor de mercado ou None se preço atual não disponível.
    """
    if preco_atual is None:
        return None
    return ativo.quantidade * preco_atual


def calcular_lucro_prejuizo(
    valor_investido: float,
    valor_mercado: Optional[float]
) -> Optional[float]:
    """
    Calcula o lucro ou prejuízo de um ativo.

    Args:
        valor_investido: Valor total investido.
        valor_mercado: Valor atual de mercado.

    Returns:
        Lucro/prejuízo ou None se valor de mercado não disponível.
    """
    if valor_mercado is None:
        return None
    return valor_mercado - valor_investido


def calcular_lucro_prejuizo_percentual(
    valor_investido: float,
    lucro_prejuizo: Optional[float]
) -> Optional[float]:
    """
    Calcula o lucro ou prejuízo em porcentagem.

    Args:
        valor_investido: Valor total investido.
        lucro_prejuizo: Lucro/prejuízo absoluto.

    Returns:
        Lucro/prejuízo percentual ou None.
    """
    if lucro_prejuizo is None or valor_investido == 0:
        return None
    return (lucro_prejuizo / valor_investido) * 100


def calcular_yield_on_cost(
    proventos_12m: float,
    preco_medio: float
) -> Optional[float]:
    """
    Calcula o Yield on Cost (retorno sobre custo).

    Args:
        proventos_12m: Total de proventos dos últimos 12 meses por cota.
        preco_medio: Preço médio de compra.

    Returns:
        YoC em percentual ou None.
    """
    if preco_medio <= 0 or proventos_12m == 0:
        return None
    return round((proventos_12m / preco_medio) * 100, 2)


def calcular_dividend_yield(
    proventos_12m: float,
    preco_atual: Optional[float]
) -> Optional[float]:
    """
    Calcula o Dividend Yield atual.

    Args:
        proventos_12m: Total de proventos dos últimos 12 meses por cota.
        preco_atual: Preço atual do ativo.

    Returns:
        DY em percentual ou None.
    """
    if preco_atual is None or preco_atual <= 0 or proventos_12m == 0:
        return None
    return round((proventos_12m / preco_atual) * 100, 2)


def filtrar_proventos_ultimos_12meses(proventos: List[Provento]) -> List[Provento]:
    """
    Filtra proventos dos últimos 12 meses.

    Args:
        proventos: Lista completa de proventos.

    Returns:
        Lista de proventos dos últimos 12 meses.
    """
    data_limite = date.today() - timedelta(days=365)
    return [p for p in proventos if p.data >= data_limite]


def consolidar_ativo(ativo: Ativo) -> AtivoConsolidado:
    """
    Consolida todos os dados de um ativo (carteira + mercado).

    Esta função busca dados atualizados do yfinance e calcula
    todas as métricas para o ativo.

    Args:
        ativo: Objeto Ativo da carteira.

    Returns:
        Objeto AtivoConsolidado com todas as métricas calculadas.
    """
    # Buscar cotação atual
    preco_atual = data_fetcher.obter_cotacao_atual(ativo.ticker)
    erro_cotacao = preco_atual is None
    
    if erro_cotacao:
        print(f"[AVISO] Não foi possível obter cotação para {ativo.ticker}")
    
    # Buscar proventos
    proventos = data_fetcher.obter_historico_dividendos(ativo.ticker)
    erro_dividendos = len(proventos) == 0 and not erro_cotacao
    
    # Atualizar proventos no ativo
    # Mantemos apenas proventos que não estão já registrados
    proventos_existentes = {(p.data, p.valor_por_cota) for p in ativo.proventos}
    novos_proventos = [
        p for p in proventos 
        if (p.data, p.valor_por_cota) not in proventos_existentes
    ]
    
    # Adicionar novos proventos ao ativo
    for provento in novos_proventos:
        ativo.adicionar_provento(provento)
    
    # Calcular métricas
    valor_investido = ativo.valor_investido
    valor_mercado = calcular_valor_mercado(ativo, preco_atual)
    lucro_prejuizo = calcular_lucro_prejuizo(valor_investido, valor_mercado)
    lp_percentual = calcular_lucro_prejuizo_percentual(valor_investido, lucro_prejuizo)
    
    # Proventos últimos 12 meses
    proventos_12m = filtrar_proventos_ultimos_12meses(ativo.proventos)
    total_proventos_12m_por_cota = sum(p.valor_por_cota for p in proventos_12m)
    total_proventos_12m = total_proventos_12m_por_cota * ativo.quantidade
    
    # Total histórico recebido
    total_proventos_recebidos = ativo.total_proventos_recebidos()
    
    # Yields
    yoc = calcular_yield_on_cost(total_proventos_12m_por_cota, ativo.preco_medio)
    dy = calcular_dividend_yield(total_proventos_12m_por_cota, preco_atual)
    
    return AtivoConsolidado(
        ticker=ativo.ticker,
        tipo=ativo.tipo,
        quantidade=ativo.quantidade,
        preco_medio=ativo.preco_medio,
        preco_atual=preco_atual,
        valor_investido=valor_investido,
        valor_mercado=valor_mercado,
        lucro_prejuizo=lucro_prejuizo,
        lucro_prejuizo_percentual=lp_percentual,
        yield_on_cost=yoc,
        dividend_yield=dy,
        total_proventos_12m=total_proventos_12m,
        total_proventos_recebidos=total_proventos_recebidos,
        proventos=ativo.proventos.copy(),
        erro_cotacao=erro_cotacao,
        erro_dividendos=erro_dividendos
    )


def consolidar_carteira(carteira: Carteira) -> tuple[List[AtivoConsolidado], ResumoCarteira]:
    """
    Consolida toda a carteira calculando métricas para cada ativo.

    Args:
        carteira: Objeto Carteira.

    Returns:
        Tupla com lista de AtivoConsolidado e ResumoCarteira.
    """
    ativos_consolidados = []
    
    valor_total_investido = 0.0
    valor_total_mercado = 0.0
    total_proventos_12m_carteira = 0.0
    soma_yoc_ponderado = 0.0
    soma_dy_ponderado = 0.0
    
    for ativo in carteira.listar_ativos():
        consolidado = consolidar_ativo(ativo)
        ativos_consolidados.append(consolidado)
        
        # Acumular para resumo
        valor_total_investido += consolidado.valor_investido
        
        if consolidado.valor_mercado is not None:
            valor_total_mercado += consolidado.valor_mercado
        
        total_proventos_12m_carteira += consolidado.total_proventos_12m
        
        # Para yield ponderado, precisamos do peso de cada ativo
        if consolidado.yield_on_cost is not None and consolidado.valor_investido > 0:
            peso = consolidado.valor_investido
            soma_yoc_ponderado += consolidado.yield_on_cost * peso
        
        if consolidado.dividend_yield is not None and consolidado.valor_mercado:
            peso = consolidado.valor_mercado
            soma_dy_ponderado += consolidado.dividend_yield * peso
    
    # Calcular resumo
    lucro_prejuizo_total = calcular_lucro_prejuizo(
        valor_total_investido,
        valor_total_mercado if valor_total_mercado > 0 else None
    )
    lp_percentual = calcular_lucro_prejuizo_percentual(
        valor_total_investido,
        lucro_prejuizo_total
    )
    
    # Yield on cost ponderado da carteira
    yoc_carteira = None
    if soma_yoc_ponderado > 0 and valor_total_investido > 0:
        yoc_carteira = round(soma_yoc_ponderado / valor_total_investido, 2)
    
    # Dividend yield ponderado da carteira
    dy_carteira = None
    if soma_dy_ponderado > 0 and valor_total_mercado and valor_total_mercado > 0:
        dy_carteira = round(soma_dy_ponderado / valor_total_mercado, 2)
    
    resumo = ResumoCarteira(
        valor_total_investido=valor_total_investido,
        valor_total_mercado=valor_total_mercado if valor_total_mercado > 0 else None,
        lucro_prejuizo_total=lucro_prejuizo_total,
        lucro_prejuizo_percentual=lp_percentual,
        total_proventos_12m=total_proventos_12m_carteira,
        yield_on_cost_carteira=yoc_carteira,
        dividend_yield_carteira=dy_carteira,
        quantidade_ativos=len(ativos_consolidados),
        data_atualizacao=date.today().isoformat()
    )
    
    return ativos_consolidados, resumo


def formatar_moeda(valor: Optional[float]) -> str:
    """
    Formata um valor como moeda brasileira (R$).

    Args:
        valor: Valor a ser formatado.

    Returns:
        String formatada como R$ X.XXX,XX.
    """
    if valor is None:
        return "N/A"
    return f"R$ {valor:,.2f}"


def formatar_percentual(valor: Optional[float]) -> str:
    """
    Formata um valor como percentual.

    Args:
        valor: Valor a ser formatado.

    Returns:
        String formatada como X,XX%.
    """
    if valor is None:
        return "N/A"
    return f"{valor:.2f}%"
