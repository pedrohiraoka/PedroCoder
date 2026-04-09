"""
Models - Definição de Schemas com Pydantic

Define os modelos de dados para validação e serialização
dos dados extraídos pelo crawler.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, EmailStr, HttpUrl
import re


class Price(BaseModel):
    """Modelo para representação de preços."""
    
    valor: float = Field(..., description="Valor numérico do preço")
    moeda: str = Field(default="BRL", description="Código da moeda (ISO 4217)")
    formato_original: Optional[str] = Field(None, description="Formato original antes da conversão")
    tipo: Optional[str] = Field(None, description="Tipo de preço (unitário, mensal, anual, etc.)")
    
    @field_validator('valor')
    @classmethod
    def validate_valor_positivo(cls, v: float) -> float:
        """Garante que o valor é não-negativo."""
        if v < 0:
            raise ValueError("O valor deve ser não-negativo")
        return v
    
    @field_validator('moeda')
    @classmethod
    def validate_moeda(cls, v: str) -> str:
        """Normaliza código da moeda para maiúsculas."""
        return v.upper() if v else "BRL"


class Service(BaseModel):
    """Modelo para representação de serviços."""
    
    nome: str = Field(..., description="Nome do serviço")
    descricao: Optional[str] = Field(None, description="Descrição detalhada do serviço")
    preco: Optional[Price] = Field(None, description="Preço do serviço")
    categoria: Optional[str] = Field(None, description="Categoria do serviço")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")


class Contact(BaseModel):
    """Modelo para informações de contato."""
    
    email: Optional[EmailStr] = Field(None, description="Endereço de e-mail válido")
    telefone: Optional[str] = Field(None, description="Número de telefone normalizado")
    website: Optional[HttpUrl] = Field(None, description="URL do website")
    endereco: Optional[str] = Field(None, description="Endereço físico completo")
    redes_sociais: Optional[Dict[str, str]] = Field(default_factory=dict, description="Links de redes sociais")
    
    @field_validator('telefone')
    @classmethod
    def normalize_telefone(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza número de telefone removendo caracteres não-numéricos."""
        if not v:
            return v
        # Remove tudo exceto dígitos e +
        cleaned = re.sub(r'[^\d+]', '', v)
        # Limita a 15 caracteres (número internacional máximo)
        return cleaned[:15] if len(cleaned) > 15 else cleaned


class Company(BaseModel):
    """Modelo principal para representação de empresas."""
    
    id: Optional[int] = Field(None, description="ID único (para banco de dados)")
    nome: str = Field(..., min_length=1, description="Nome da empresa")
    descricao: Optional[str] = Field(None, description="Descrição da empresa")
    contato: Optional[Contact] = Field(None, description="Informações de contato")
    servicos: List[Service] = Field(default_factory=list, description="Lista de serviços oferecidos")
    precos: List[Price] = Field(default_factory=list, description="Lista de preços gerais")
    categoria: Optional[str] = Field(None, description="Categoria/segmento da empresa")
    url_origem: Optional[HttpUrl] = Field(None, description="URL onde os dados foram coletados")
    data_coleta: datetime = Field(default_factory=datetime.utcnow, description="Data/hora da coleta")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")
    
    @field_validator('nome')
    @classmethod
    def strip_nome(cls, v: str) -> str:
        """Remove espaços extras do nome."""
        return ' '.join(v.split())
    
    @field_validator('descricao')
    @classmethod
    def clean_descricao(cls, v: Optional[str]) -> Optional[str]:
        """Limpa descrição removendo espaços extras e caracteres estranhos."""
        if not v:
            return v
        # Remove múltiplos espaços e newlines
        cleaned = ' '.join(v.split())
        # Remove caracteres de controle
        cleaned = ''.join(c for c in cleaned if ord(c) >= 32 or c in '\n\t')
        return cleaned.strip() if cleaned else None


class CrawledPage(BaseModel):
    """Modelo para representar uma página crawlada com seus dados."""
    
    url: HttpUrl = Field(..., description="URL da página")
    status_code: int = Field(..., description="Código HTTP de resposta")
    company: Optional[Company] = Field(None, description="Dados da empresa extraídos")
    companies: List[Company] = Field(default_factory=list, description="Múltiplas empresas (listagem)")
    html_size: int = Field(0, description="Tamanho do HTML em bytes")
    tempo_processamento: float = Field(0.0, description="Tempo de processamento em segundos")
    erros: List[str] = Field(default_factory=list, description="Lista de erros encontrados")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do crawl")
    
    @property
    def sucesso(self) -> bool:
        """Indica se o crawl foi bem-sucedido."""
        return self.status_code == 200 and len(self.erros) == 0
    
    @property
    def total_empresas(self) -> int:
        """Retorna o total de empresas extraídas."""
        if self.company:
            return 1
        return len(self.companies)


class CrawlerStats(BaseModel):
    """Estatísticas de execução do crawler."""
    
    urls_visitadas: int = Field(0, description="Total de URLs visitadas")
    urls_sucesso: int = Field(0, description="URLs com sucesso")
    urls_falha: int = Field(0, description="URLs com falha")
    empresas_extraidas: int = Field(0, description="Total de empresas extraídas")
    tempo_total: float = Field(0.0, description="Tempo total de execução em segundos")
    tempo_medio_por_requisicao: float = Field(0.0, description="Tempo médio por requisição")
    inicio: datetime = Field(default_factory=datetime.utcnow, description="Início da execução")
    fim: Optional[datetime] = Field(None, description="Fim da execução")
    
    def adicionar_pagina(self, page: CrawledPage) -> None:
        """Adiciona estatísticas de uma página."""
        self.urls_visitadas += 1
        if page.sucesso:
            self.urls_sucesso += 1
        else:
            self.urls_falha += 1
        self.empresas_extraidas += page.total_empresas
    
    def finalizar(self) -> None:
        """Finaliza as estatísticas calculando médias."""
        self.fim = datetime.utcnow()
        self.tempo_total = (self.fim - self.inicio).total_seconds()
        if self.urls_visitadas > 0:
            self.tempo_medio_por_requisicao = self.tempo_total / self.urls_visitadas
