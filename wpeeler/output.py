"""
WPeeler - Web Design DNA Extractor

Módulo de output: formatação Rich e salvamento JSON.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Importações relativas ajustadas para execução direta
try:
    from .models import (
        AnimationProfile,
        ColorPalette,
        FontScale,
        SiteVisualDNA,
        SpacingPattern,
        Typography,
    )
    from .utils import extract_domain
except ImportError:
    from models import (
        AnimationProfile,
        ColorPalette,
        FontScale,
        SiteVisualDNA,
        SpacingPattern,
        Typography,
    )
    from utils import extract_domain

logger = logging.getLogger(__name__)
console = Console()


def format_report(dna: SiteVisualDNA) -> None:
    """
    Exibe relatório formatado no terminal usando Rich.

    Args:
        dna: Objeto SiteVisualDNA com os dados analisados
    """
    console.print()

    # Header
    header = Text()
    header.append("🎨 WPeeler - Web Design DNA\n", style="bold magenta")
    header.append(f"URL: {dna.url}", style="dim")
    console.print(Panel(header, border_style="magenta"))

    # Typography
    typography_table = Table(title="📝 Tipografia", border_style="cyan", show_header=True)
    typography_table.add_column("Propriedade", style="cyan")
    typography_table.add_column("Valor", style="white")

    typography_table.add_row(
        "Família Predominante",
        dna.typography.predominant_family or "N/A",
    )
    typography_table.add_row(
        "Line Height Base",
        str(dna.typography.line_height_base or "N/A"),
    )

    # Size scale
    size_scale = dna.typography.size_scale.model_dump()
    for key, value in size_scale.items():
        if value is not None:
            typography_table.add_row(f"Font-size ({key})", f"{value}px")

    console.print(typography_table)
    console.print()

    # Spacing
    spacing_table = Table(title="📏 Espaçamento", border_style="green", show_header=True)
    spacing_table.add_column("Propriedade", style="green")
    spacing_table.add_column("Valor", style="white")

    spacing_table.add_row(
        "Valores Comuns (px)",
        ", ".join(map(str, dna.spacing.common_values_px)) or "N/A",
    )
    spacing_table.add_row(
        "Container Max-Width",
        dna.spacing.container_max_width or "N/A",
    )
    spacing_table.add_row(
        "Grid Base",
        f"{dna.spacing.grid_base}px" if dna.spacing.grid_base else "N/A",
    )

    console.print(spacing_table)
    console.print()

    # Colors
    colors_table = Table(title="🎨 Cores", border_style="yellow", show_header=True)
    colors_table.add_column("Papel", style="yellow")
    colors_table.add_column("Cor", style="white")
    colors_table.add_column("Preview", justify="center")

    colors = dna.colors.model_dump()
    color_roles = [
        ("background", "Background"),
        ("text_primary", "Texto Primário"),
        ("text_secondary", "Texto Secundário"),
        ("accent", "Destaque"),
    ]

    for key, label in color_roles:
        color = colors.get(key)
        if color:
            preview = "■" * 3
            colors_table.add_row(label, color.upper(), Text(preview, style=f"bold {color}"))

    # Palette completa
    palette = colors.get("palette_hex", [])
    if palette:
        palette_preview = "  ".join([f"■ {c.upper()}" for c in palette[:5]])
        colors_table.add_row("Paleta Completa", ", ".join(palette), palette_preview)

    console.print(colors_table)
    console.print()

    # Animations
    animations_table = Table(
        title="⚡ Animações", border_style="blue", show_header=True
    )
    animations_table.add_column("Propriedade", style="blue")
    animations_table.add_column("Valor", style="white")

    animations_table.add_row(
        "Duração Hover",
        dna.animations.hover_duration or "N/A",
    )
    animations_table.add_row(
        "Easing",
        dna.animations.easing or "N/A",
    )

    common_transitions = dna.animations.common_transitions
    if common_transitions:
        for i, transition in enumerate(common_transitions[:3], 1):
            animations_table.add_row(
                f"Transição #{i}" if i > 1 else "Transições Comuns",
                transition,
            )

    console.print(animations_table)
    console.print()


def save_json(
    dna: SiteVisualDNA,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Salva o DNA visual em arquivo JSON.

    Args:
        dna: Objeto SiteVisualDNA
        output_path: Caminho opcional para o arquivo. Se None, gera nome automático.

    Returns:
        Path do arquivo salvo
    """
    if output_path is None:
        # Gera nome automático: wpeeler_<domain>_<timestamp>.json
        domain = extract_domain(dna.url)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"wpeeler_{domain}_{timestamp}.json"
        output_path = Path.cwd() / filename

    # Garante que é um Path
    output_path = Path(output_path)

    # Serializa para JSON
    json_content = dna.model_dump_json()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        logger.info(f"JSON saved to {output_path}")
        console.print(f"\n💾 JSON salvo em: [bold green]{output_path}[/bold green]")
    except IOError as e:
        logger.error(f"Failed to save JSON: {e}")
        console.print(f"\n❌ Erro ao salvar JSON: {e}")
        raise

    return output_path


def print_summary(dna: SiteVisualDNA) -> None:
    """
    Imprime resumo rápido do DNA visual.

    Args:
        dna: Objeto SiteVisualDNA
    """
    summary = []

    # Tipografia
    if dna.typography.predominant_family:
        summary.append(f"📝 Fonte: {dna.typography.predominant_family}")

    # Cores
    if dna.colors.accent:
        summary.append(f"🎨 Accent: {dna.colors.accent.upper()}")

    # Grid
    if dna.spacing.grid_base:
        summary.append(f"📏 Grid: {dna.spacing.grid_base}px")

    # Animações
    if dna.animations.hover_duration:
        summary.append(f"⚡ Hover: {dna.animations.hover_duration}")

    if summary:
        console.print("\n" + " | ".join(summary), style="dim")


def create_site_visual_dna(
    url: str,
    analysis_result: dict[str, Any],
) -> SiteVisualDNA:
    """
    Cria objeto SiteVisualDNA a partir dos resultados da análise.

    Args:
        url: URL analisada
        analysis_result: Dict retornado pelo analyzer

    Returns:
        Objeto SiteVisualDNA validado
    """
    typography_data = analysis_result.get("typography", {})
    spacing_data = analysis_result.get("spacing", {})
    colors_data = analysis_result.get("colors", {})
    animations_data = analysis_result.get("animations", {})

    # Cria FontScale
    size_scale_data = typography_data.get("size_scale", {})
    font_scale = FontScale(
        h1=size_scale_data.get("h1"),
        h2=size_scale_data.get("h2"),
        h3=size_scale_data.get("h3"),
        h4=size_scale_data.get("h4"),
        h5=size_scale_data.get("h5"),
        h6=size_scale_data.get("h6"),
        body=size_scale_data.get("body"),
        small=size_scale_data.get("small"),
    )

    # Cria Typography
    typography = Typography(
        predominant_family=typography_data.get("predominant_family", "unknown"),
        size_scale=font_scale,
        line_height_base=typography_data.get("line_height_base"),
    )

    # Cria SpacingPattern
    spacing = SpacingPattern(
        common_values_px=spacing_data.get("common_values_px", []),
        container_max_width=spacing_data.get("container_max_width"),
        grid_base=spacing_data.get("grid_base"),
    )

    # Cria ColorPalette
    colors = ColorPalette(
        background=colors_data.get("background"),
        text_primary=colors_data.get("text_primary"),
        text_secondary=colors_data.get("text_secondary"),
        accent=colors_data.get("accent"),
        palette_hex=colors_data.get("palette_hex", []),
    )

    # Cria AnimationProfile
    animations = AnimationProfile(
        hover_duration=animations_data.get("hover_duration"),
        easing=animations_data.get("easing"),
        common_transitions=animations_data.get("common_transitions", []),
    )

    # Cria SiteVisualDNA
    return SiteVisualDNA(
        url=url,
        typography=typography,
        spacing=spacing,
        colors=colors,
        animations=animations,
    )
