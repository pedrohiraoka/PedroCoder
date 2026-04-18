"""
WPeeler - Web Design DNA Extractor

Módulo de modelos Pydantic para validação e serialização da saída.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FontScale(BaseModel):
    """Escala tipográfica do site."""

    h1: Optional[float] = Field(None, description="Tamanho da fonte h1 em px")
    h2: Optional[float] = Field(None, description="Tamanho da fonte h2 em px")
    h3: Optional[float] = Field(None, description="Tamanho da fonte h3 em px")
    h4: Optional[float] = Field(None, description="Tamanho da fonte h4 em px")
    h5: Optional[float] = Field(None, description="Tamanho da fonte h5 em px")
    h6: Optional[float] = Field(None, description="Tamanho da fonte h6 em px")
    body: Optional[float] = Field(None, description="Tamanho da fonte base em px")
    small: Optional[float] = Field(None, description="Tamanho da fonte pequena em px")


class Typography(BaseModel):
    """Análise tipográfica completa."""

    predominant_family: str = Field(..., description="Família de fonte predominante")
    size_scale: FontScale = Field(..., description="Escala de tamanhos de fonte")
    line_height_base: Optional[float] = Field(None, description="Altura de linha base")


class SpacingPattern(BaseModel):
    """Padrões de espaçamento identificados."""

    common_values_px: list[int] = Field(
        default_factory=list, description="Valores mais comuns em pixels"
    )
    container_max_width: Optional[str] = Field(
        None, description="Largura máxima do container"
    )
    grid_base: Optional[int] = Field(None, description="Base do grid (ex: 8px)")


class ColorPalette(BaseModel):
    """Paleta de cores extraída."""

    background: Optional[str] = Field(None, description="Cor de fundo principal")
    text_primary: Optional[str] = Field(None, description="Cor de texto primária")
    text_secondary: Optional[str] = Field(None, description="Cor de texto secundária")
    accent: Optional[str] = Field(None, description="Cor de destaque/acentuação")
    palette_hex: list[str] = Field(
        default_factory=list, description="Lista de cores em hexadecimal"
    )


class AnimationProfile(BaseModel):
    """Perfil de animações e transições."""

    hover_duration: Optional[str] = Field(
        None, description="Duração comum de hover em segundos"
    )
    easing: Optional[str] = Field(
        None, description="Função de easing mais comum"
    )
    common_transitions: list[str] = Field(
        default_factory=list, description="Transições mais comuns"
    )


class SiteVisualDNA(BaseModel):
    """Modelo principal contendo todo o DNA visual do site."""

    url: str = Field(..., description="URL analisada")
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp da análise"
    )
    typography: Typography = Field(..., description="Análise tipográfica")
    spacing: SpacingPattern = Field(..., description="Padrões de espaçamento")
    colors: ColorPalette = Field(..., description="Paleta de cores")
    animations: AnimationProfile = Field(..., description="Perfil de animações")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}

    def model_dump_json(self, **kwargs) -> str:
        """Serializa o modelo para JSON com tratamento de datetime."""
        data = self.model_dump()
        data["scraped_at"] = self.scraped_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        import json

        return json.dumps(data, ensure_ascii=False, indent=2)
