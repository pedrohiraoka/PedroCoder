"""
WPeeler - Web Design DNA Extractor

Módulo de utilitários comuns para conversão, normalização e helpers.
"""

from __future__ import annotations

import re
from typing import Optional


# Constante de conversão: 1rem = 16px (assumção do MVP)
REM_TO_PX = 16.0
EM_TO_PX = 16.0


def normalize_to_px(value: str, base_size: float = 16.0) -> Optional[float]:
    """
    Normaliza um valor CSS para pixels.

    Args:
        value: Valor CSS (ex: "16px", "1rem", "1.5em", "24")
        base_size: Tamanho base para conversão (padrão 16px)

    Returns:
        Valor em pixels como float, ou None se não puder converter
    """
    if not value or value.strip() == "":
        return None

    value = value.strip().lower()

    # Ignora valores especiais
    if value in ("auto", "inherit", "initial", "unset", "transparent", "currentcolor"):
        return None

    # Pattern para extrair número e unidade
    match = re.match(r"^(-?\d+(?:\.\d+)?)(px|rem|em|%)?$", value)
    if not match:
        return None

    num_str, unit = match.groups()
    try:
        num = float(num_str)
    except ValueError:
        return None

    if unit == "px" or unit is None:
        return num
    elif unit == "rem":
        return num * REM_TO_PX
    elif unit == "em":
        return num * base_size
    elif unit == "%":
        # Porcentagem é relativa ao contexto, retornamos None para simplificar
        return None

    return None


def parse_color_value(value: str) -> Optional[tuple[int, int, int]]:
    """
    Parseia uma cor CSS e retorna tuple RGB (0-255).

    Suporta: hex (#rgb, #rrggbb), rgb(), rgba(), hsl(), hsla()
    Ignora: transparent, currentColor, inherit, etc.

    Args:
        value: String da cor CSS

    Returns:
        Tuple (R, G, B) ou None se não for cor válida
    """
    if not value:
        return None

    value = value.strip().lower()

    # Ignora valores especiais
    if value in ("transparent", "currentcolor", "inherit", "initial", "unset", ""):
        return None

    # Hex shorthand: #rgb -> #rrggbb
    hex_short = re.match(r"^#([0-9a-f])([0-9a-f])([0-9a-f])$", value)
    if hex_short:
        r, g, b = hex_short.groups()
        return (int(r * 2, 16), int(g * 2, 16), int(b * 2, 16))

    # Hex completo: #rrggbb
    hex_full = re.match(r"^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$", value)
    if hex_full:
        r, g, b = hex_full.groups()
        return (int(r, 16), int(g, 16), int(b, 16))

    # rgb() ou rgba()
    rgb_match = re.match(
        r"^rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)$", value
    )
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return (min(255, r), min(255, g), min(255, b))

    # hsl() ou hsla() - conversão simplificada
    hsl_match = re.match(
        r"^hsla?\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%(?:\s*,\s*[\d.]+)?\s*\)$",
        value,
    )
    if hsl_match:
        h = float(hsl_match.group(1)) / 360.0
        s = float(hsl_match.group(2)) / 100.0
        l = float(hsl_match.group(3)) / 100.0
        return hsl_to_rgb(h, s, l)

    return None


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """
    Converte HSL para RGB.

    Args:
        h: Hue (0-1)
        s: Saturation (0-1)
        l: Lightness (0-1)

    Returns:
        Tuple (R, G, B) com valores 0-255
    """
    if s == 0:
        r = g = b = l
    else:

        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Converte RGB para hexadecimal.

    Args:
        r, g, b: Valores 0-255

    Returns:
        String hexadecimal no formato #rrggbb
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """
    Calcula distância Euclidiana entre duas cores RGB.

    Args:
        c1: Tuple (R, G, B)
        c2: Tuple (R, G, B)

    Returns:
        Distância Euclidiana normalizada (0-441.67)
    """
    return (
        ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5
    )


def colors_are_similar(
    c1: tuple[int, int, int], c2: tuple[int, int, int], tolerance: float = 0.15
) -> bool:
    """
    Verifica se duas cores são similares dentro de uma tolerância.

    Args:
        c1: Tuple (R, G, B)
        c2: Tuple (R, G, B)
        tolerance: Tolerância de 0-1 (padrão 0.15 = 15%)

    Returns:
        True se as cores forem similares
    """
    max_distance = 441.67  # sqrt(255^2 * 3)
    distance = color_distance(c1, c2)
    return distance <= max_distance * tolerance


def extract_domain(url: str) -> str:
    """
    Extrai o domínio de uma URL.

    Args:
        url: URL completa

    Returns:
        Domínio limpo (ex: example.com)
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.replace("www.", "")


def find_gcd(values: list[int]) -> int:
    """
    Encontra o maior divisor comum de uma lista de valores.

    Args:
        values: Lista de números inteiros positivos

    Returns:
        GCD dos valores, ou 8 como fallback
    """
    if not values:
        return 8

    from math import gcd
    from functools import reduce

    result = reduce(gcd, values)
    return result if result > 0 else 8
