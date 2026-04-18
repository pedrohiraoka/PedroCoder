"""
WPeeler - Web Design DNA Extractor

Módulo de análise: heurísticas para extrair padrões visuais do CSS.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Optional

# Importações relativas ajustadas para execução direta
try:
    from .parser import CSSDeclaration, extract_all_declarations
    from .utils import (
        colors_are_similar,
        find_gcd,
        normalize_to_px,
        parse_color_value,
        rgb_to_hex,
    )
except ImportError:
    from parser import CSSDeclaration, extract_all_declarations
    from utils import (
        colors_are_similar,
        find_gcd,
        normalize_to_px,
        parse_color_value,
        rgb_to_hex,
    )

logger = logging.getLogger(__name__)

# Propriedades CSS relevantes para cada categoria
FONT_PROPERTIES = {
    "font-family",
    "font-size",
    "font-weight",
    "line-height",
    "font-style",
}

SPACING_PROPERTIES = {"padding", "margin", "max-width", "width", "gap"}

COLOR_PROPERTIES = {
    "color",
    "background-color",
    "background",
    "border-color",
    "border-top-color",
    "border-right-color",
    "border-bottom-color",
    "border-left-color",
    "outline-color",
    "fill",
    "stroke",
}

ANIMATION_PROPERTIES = {
    "transition",
    "transition-duration",
    "transition-timing-function",
    "animation",
    "animation-duration",
    "animation-timing-function",
}


def analyze_css(css_sources: dict[str, str]) -> dict[str, Any]:
    """
    Analisa fontes CSS e extrai padrões visuais.

    Args:
        css_sources: Dict {url: css_content}

    Returns:
        Dict com análises de typography, spacing, colors, animations
    """
    logger.info(f"Analyzing {len(css_sources)} CSS sources")

    declarations = extract_all_declarations(css_sources)
    logger.info(f"Extracted {len(declarations)} CSS declarations")

    if not declarations:
        return _empty_analysis()

    # Agrupa declarações por propriedade
    by_property: dict[str, list[CSSDeclaration]] = {}
    for decl in declarations:
        prop = decl.property_name
        if prop not in by_property:
            by_property[prop] = []
        by_property[prop].append(decl)

    # Executa análises
    typography = analyze_typography(by_property)
    spacing = analyze_spacing(by_property)
    colors = analyze_colors(by_property)
    animations = analyze_animations(by_property)

    return {
        "typography": typography,
        "spacing": spacing,
        "colors": colors,
        "animations": animations,
    }


def _empty_analysis() -> dict[str, Any]:
    """Retorna estrutura vazia de análise."""
    return {
        "typography": {
            "predominant_family": "unknown",
            "size_scale": {},
            "line_height_base": None,
        },
        "spacing": {
            "common_values_px": [],
            "container_max_width": None,
            "grid_base": 8,
        },
        "colors": {
            "background": None,
            "text_primary": None,
            "text_secondary": None,
            "accent": None,
            "palette_hex": [],
        },
        "animations": {
            "hover_duration": None,
            "easing": None,
            "common_transitions": [],
        },
    }


def analyze_typography(
    by_property: dict[str, list[CSSDeclaration]],
) -> dict[str, Any]:
    """
    Analisa padrões tipográficos.

    Args:
        by_property: Declarações agrupadas por propriedade

    Returns:
        Dict com predominant_family, size_scale, line_height_base
    """
    result = {
        "predominant_family": "unknown",
        "size_scale": {},
        "line_height_base": None,
    }

    # Font-family predominante
    if "font-family" in by_property:
        families = [
            decl.value.strip('"\'')
            for decl in by_property["font-family"]
            if decl.value and decl.value not in ("inherit", "initial")
        ]
        if families:
            counter = Counter(families)
            result["predominant_family"] = counter.most_common(1)[0][0]

    # Font-size por seletor
    if "font-size" in by_property:
        size_by_selector: dict[str, list[float]] = {}

        for decl in by_property["font-size"]:
            if not decl.selector:
                continue

            px_value = normalize_to_px(decl.value)
            if px_value is None:
                continue

            selector = decl.selector.lower()

            # Categoriza por tipo de seletor
            category = _categorize_selector(selector)
            if category not in size_by_selector:
                size_by_selector[category] = []
            size_by_selector[category].append(px_value)

        # Calcula mediana por categoria
        size_scale = {}
        for category, sizes in size_by_selector.items():
            if sizes:
                sorted_sizes = sorted(sizes)
                median_idx = len(sorted_sizes) // 2
                size_scale[category] = int(round(sorted_sizes[median_idx]))

        result["size_scale"] = size_scale

    # Line-height base
    if "line-height" in by_property:
        line_heights = []
        for decl in by_property["line-height"]:
            # Tenta parsear como número unitless
            try:
                val = decl.value.strip()
                if val.replace(".", "").isdigit():
                    lh = float(val)
                    if 1.0 <= lh <= 2.5:  # Faixa razoável
                        line_heights.append(lh)
                else:
                    px_lh = normalize_to_px(val)
                    if px_lh and 16 <= px_lh <= 40:
                        # Converte para ratio assumindo font-size 16px
                        line_heights.append(px_lh / 16.0)
            except (ValueError, TypeError):
                continue

        if line_heights:
            result["line_height_base"] = round(
                sum(line_heights) / len(line_heights), 2
            )

    return result


def _categorize_selector(selector: str) -> str:
    """
    Categoriza um seletor CSS em categorias tipográficas.

    Args:
        selector: Seletor CSS

    Returns:
        Categoria (h1, h2, h3, h4, h5, h6, body, small, etc.)
    """
    selector = selector.lower().strip()

    # Headings
    if re.match(r"^h1\b", selector):
        return "h1"
    if re.match(r"^h2\b", selector):
        return "h2"
    if re.match(r"^h3\b", selector):
        return "h3"
    if re.match(r"^h4\b", selector):
        return "h4"
    if re.match(r"^h5\b", selector):
        return "h5"
    if re.match(r"^h6\b", selector):
        return "h6"

    # Body/base
    if selector in ("body", "html", ":root"):
        return "body"

    # Small text
    if "small" in selector or "caption" in selector or "footnote" in selector:
        return "small"

    # Paragraphs
    if "p" == selector or "paragraph" in selector:
        return "body"

    # Links
    if "a" == selector or "link" in selector:
        return "body"

    # Default to body
    return "body"


def analyze_spacing(
    by_property: dict[str, list[CSSDeclaration]],
) -> dict[str, Any]:
    """
    Analisa padrões de espaçamento.

    Args:
        by_property: Declarações agrupadas por propriedade

    Returns:
        Dict com common_values_px, container_max_width, grid_base
    """
    all_spacing_values: list[int] = []
    max_widths: list[tuple[int, str]] = []

    # Extrai valores de padding/margin
    for prop in ["padding", "margin", "padding-top", "padding-right", "padding-bottom",
                 "padding-left", "margin-top", "margin-right", "margin-bottom", "margin-left",
                 "gap", "row-gap", "column-gap"]:
        if prop not in by_property:
            continue

        for decl in by_property[prop]:
            # Valores podem ser múltiplos (ex: padding: 10px 20px)
            values = decl.value.split()
            for val in values:
                px = normalize_to_px(val)
                if px is not None and px >= 0:
                    rounded = int(round(px))
                    if rounded <= 500:  # Ignora valores extremos
                        all_spacing_values.append(rounded)

    # Extrai max-width
    for prop in ["max-width", "width"]:
        if prop not in by_property:
            continue

        for decl in by_property[prop]:
            val = decl.value.strip()
            if val in ("auto", "100%", "fit-content", "min-content"):
                continue

            # Tenta extrair valor em px
            match = re.search(r"(\d+(?:\.\d+)?)(px)?", val)
            if match:
                num = float(match.group(1))
                if 600 <= num <= 2000:  # Faixa típica de container
                    max_widths.append((int(round(num)), val))

    result = {
        "common_values_px": [],
        "container_max_width": None,
        "grid_base": 8,
    }

    # Top 5 valores mais comuns
    if all_spacing_values:
        counter = Counter(all_spacing_values)
        top_5 = counter.most_common(5)
        result["common_values_px"] = [val for val, _ in top_5]

        # Calcula grid base (GCD dos valores comuns)
        if len(top_5) >= 2:
            values = [val for val, _ in top_5[:5]]
            result["grid_base"] = find_gcd(values)

    # Max-width mais comum
    if max_widths:
        counter = Counter([val for _, val in max_widths])
        result["container_max_width"] = counter.most_common(1)[0][0]

    return result


def analyze_colors(
    by_property: dict[str, list[CSSDeclaration]],
) -> dict[str, Any]:
    """
    Analisa paleta de cores.

    Args:
        by_property: Declarações agrupadas por propriedade

    Returns:
        Dict com background, text_primary, accent, palette_hex
    """
    # Coleta todas as cores válidas
    color_occurrences: list[tuple[tuple[int, int, int], str, str]] = []  # (rgb, hex, property)

    for prop in COLOR_PROPERTIES:
        if prop not in by_property:
            continue

        for decl in by_property[prop]:
            rgb = parse_color_value(decl.value)
            if rgb is not None:
                hex_color = rgb_to_hex(*rgb)
                color_occurrences.append((rgb, hex_color, prop))

    if not color_occurrences:
        return {
            "background": None,
            "text_primary": None,
            "text_secondary": None,
            "accent": None,
            "palette_hex": [],
        }

    # Agrupa cores similares
    unique_colors: list[tuple[tuple[int, int, int], str, int]] = []  # (rgb, hex, count)

    for rgb, hex_color, prop in color_occurrences:
        found_similar = False
        for existing_rgb, existing_hex, count in unique_colors:
            if colors_are_similar(rgb, existing_rgb):
                found_similar = True
                break
        if not found_similar:
            unique_colors.append((rgb, hex_color, 1))
        else:
            # Incrementa count da cor similar
            idx = unique_colors.index((existing_rgb, existing_hex, count))
            unique_colors[idx] = (existing_rgb, existing_hex, count + 1)

    # Ordena por frequência
    unique_colors.sort(key=lambda x: x[2], reverse=True)

    # Identifica papéis das cores
    background = None
    text_primary = None
    text_secondary = None
    accent = None

    # Background: cor mais clara entre as mais frequentes
    for rgb, hex_color, _ in unique_colors[:10]:
        brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
        if brightness > 200:  # Cor clara
            background = hex_color
            break

    # Text primary: cor mais escura entre as mais frequentes
    for rgb, hex_color, _ in unique_colors[:10]:
        brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
        if brightness < 80:  # Cor escura
            text_primary = hex_color
            break

    # Accent: cor com saturação moderada-alta que não é preto/branco/cinza
    for rgb, hex_color, _ in unique_colors[:15]:
        r, g, b = rgb
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        saturation = (max_c - min_c) / max_c if max_c > 0 else 0
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        # Saturação > 30% e não muito escura/clara
        if saturation > 0.3 and 50 < brightness < 200:
            accent = hex_color
            break

    # Top 5 cores para palette
    palette_hex = [hex_color for _, hex_color, _ in unique_colors[:5]]

    return {
        "background": background,
        "text_primary": text_primary,
        "text_secondary": text_secondary,
        "accent": accent,
        "palette_hex": palette_hex,
    }


def analyze_animations(
    by_property: dict[str, list[CSSDeclaration]],
) -> dict[str, Any]:
    """
    Analisa padrões de animação e transição.

    Args:
        by_property: Declarações agrupadas por propriedade

    Returns:
        Dict com hover_duration, easing, common_transitions
    """
    durations: list[str] = []
    easings: list[str] = []
    transitions: list[str] = []

    # Processa transition shorthand
    if "transition" in by_property:
        for decl in by_property["transition"]:
            val = decl.value.strip()
            if val and val not in ("none", "inherit", "initial"):
                transitions.append(val)

                # Extrai duração
                duration_match = re.search(r"(\d+(?:\.\d+)?)(m?s)", val)
                if duration_match:
                    num = float(duration_match.group(1))
                    unit = duration_match.group(2)
                    if unit == "ms":
                        num /= 1000
                    if 0.05 <= num <= 2.0:  # Faixa razoável
                        durations.append(f"{num:.2f}s")

                # Extrai easing
                easing_patterns = [
                    r"(ease-in-out|ease-in|ease-out|ease|linear)",
                    r"(cubic-bezier\([^)]+\))",
                ]
                for pattern in easing_patterns:
                    easing_match = re.search(pattern, val)
                    if easing_match:
                        easings.append(easing_match.group(1))
                        break

    # Processa transition-duration separadamente
    if "transition-duration" in by_property:
        for decl in by_property["transition-duration"]:
            val = decl.value.strip()
            duration_match = re.search(r"(\d+(?:\.\d+)?)(m?s)", val)
            if duration_match:
                num = float(duration_match.group(1))
                unit = duration_match.group(2)
                if unit == "ms":
                    num /= 1000
                if 0.05 <= num <= 2.0:
                    durations.append(f"{num:.2f}s")

    # Processa transition-timing-function
    if "transition-timing-function" in by_property:
        for decl in by_property["transition-timing-function"]:
            val = decl.value.strip()
            if val and val not in ("inherit", "initial"):
                easings.append(val)

    result = {
        "hover_duration": None,
        "easing": None,
        "common_transitions": [],
    }

    # Duração mais comum (para hover)
    if durations:
        counter = Counter(durations)
        result["hover_duration"] = counter.most_common(1)[0][0]

    # Easing mais comum
    if easings:
        counter = Counter(easings)
        result["easing"] = counter.most_common(1)[0][0]

    # Transições mais comuns
    if transitions:
        counter = Counter(transitions)
        result["common_transitions"] = [
            t for t, _ in counter.most_common(5)
        ]

    return result
