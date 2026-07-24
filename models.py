"""
Models para a aplicação de acompanhamento de carteira de investimentos.

Este módulo define as estruturas de dados principais usando dataclasses
com tipagem estática para representar ativos e proventos.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum


class TipoAtivo(Enum):
    """Enumeração para tipos de ativos suportados."""
    ACAO = "ACAO"
    FII = "FII"


class TipoProvento(Enum):
    """Enumeração para tipos de proventos."""
    DIVIDENDO = "DIVIDENDO"
    JCP = "JCP"  # Juros sobre Capital Próprio
    RENDIMENTO = "RENDIMENTO"  # Para FIIs
    BONIFICACAO = "BONIFICACAO"


@dataclass
class Provento:
    """
    Representa um provento (dividendo, JCP, rendimento) pago por um ativo.

    Attributes:
        data: Data do pagamento do provento.
        valor_por_cota: Valor pago por cota/ação.
        tipo: Tipo do provento (DIVIDENDO, JCP, RENDIMENTO, etc.).
        ticker: Ticker do ativo que pagou o provento.
    """
    data: date
    valor_por_cota: float
    tipo: TipoProvento
    ticker: str

    def __post_init__(self) -> None:
        """Valida os dados após inicialização."""
        if self.valor_por_cota < 0:
            raise ValueError("O valor por cota não pode ser negativo.")

    def to_dict(self) -> dict:
        """Converte o provento para um dicionário serializável."""
        return {
            "data": self.data.isoformat(),
            "valor_por_cota": round(self.valor_por_cota, 4),
            "tipo": self.tipo.value,
            "ticker": self.ticker
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Provento":
        """Cria uma instância de Provento a partir de um dicionário."""
        return cls(
            data=date.fromisoformat(data["data"]),
            valor_por_cota=float(data["valor_por_cota"]),
            tipo=TipoProvento(data["tipo"]),
            ticker=data["ticker"]
        )


@dataclass
class Ativo:
    """
    Representa um ativo na carteira do usuário.

    Attributes:
        ticker: Código do ativo (ex: PETR4, HGLG11).
        tipo: Tipo do ativo (ACAO ou FII).
        quantidade: Quantidade de cotas/ações possuídas.
        preco_medio: Preço médio de compra por cota/ação.
        proventos: Lista de proventos recebidos deste ativo.
    """
    ticker: str
    tipo: TipoAtivo
    quantidade: float
    preco_medio: float
    proventos: List[Provento] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valida os dados após inicialização."""
        if self.quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        if self.preco_medio <= 0:
            raise ValueError("O preço médio deve ser positivo.")
        # Normaliza o ticker para maiúsculas
        object.__setattr__(self, 'ticker', self.ticker.upper())

    @property
    def valor_investido(self) -> float:
        """Calcula o valor total investido no ativo."""
        return self.quantidade * self.preco_medio

    def adicionar_provento(self, provento: Provento) -> None:
        """Adiciona um provento à lista de proventos do ativo."""
        if provento.ticker != self.ticker:
            raise ValueError(
                f"Ticker do provento ({provento.ticker}) não corresponde "
                f"ao ticker do ativo ({self.ticker})."
            )
        self.proventos.append(provento)

    def total_proventos_recebidos(self) -> float:
        """Calcula o total de proventos recebidos."""
        return sum(p.valor_por_cota for p in self.proventos) * self.quantidade

    def to_dict(self) -> dict:
        """Converte o ativo para um dicionário serializável."""
        return {
            "ticker": self.ticker,
            "tipo": self.tipo.value,
            "quantidade": self.quantidade,
            "preco_medio": round(self.preco_medio, 2),
            "proventos": [p.to_dict() for p in self.proventos]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ativo":
        """Cria uma instância de Ativo a partir de um dicionário."""
        proventos = [
            Provento.from_dict(p) for p in data.get("proventos", [])
        ]
        return cls(
            ticker=data["ticker"],
            tipo=TipoAtivo(data["tipo"]),
            quantidade=float(data["quantidade"]),
            preco_medio=float(data["preco_medio"]),
            proventos=proventos
        )


@dataclass
class Carteira:
    """
    Representa a carteira completa de investimentos do usuário.

    Attributes:
        ativos: Dicionário mapeando tickers para objetos Ativo.
    """
    ativos: dict[str, Ativo] = field(default_factory=dict)

    def adicionar_ativo(self, ativo: Ativo) -> None:
        """Adiciona ou atualiza um ativo na carteira."""
        self.ativos[ativo.ticker] = ativo

    def remover_ativo(self, ticker: str) -> bool:
        """Remove um ativo da carteira pelo ticker."""
        ticker = ticker.upper()
        if ticker in self.ativos:
            del self.ativos[ticker]
            return True
        return False

    def obter_ativo(self, ticker: str) -> Optional[Ativo]:
        """Obtém um ativo da carteira pelo ticker."""
        return self.ativos.get(ticker.upper())

    def listar_ativos(self) -> List[Ativo]:
        """Retorna uma lista com todos os ativos da carteira."""
        return list(self.ativos.values())

    def to_dict(self) -> dict:
        """Converte a carteira para um dicionário serializável."""
        return {
            "ativos": {
                ticker: ativo.to_dict() 
                for ticker, ativo in self.ativos.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Carteira":
        """Cria uma instância de Carteira a partir de um dicionário."""
        carteira = cls()
        for ticker, ativo_data in data.get("ativos", {}).items():
            carteira.adicionar_ativo(Ativo.from_dict(ativo_data))
        return carteira
