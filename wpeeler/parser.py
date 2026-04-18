"""
WPeeler - Web Design DNA Extractor

Módulo de parser: análise de CSS usando tinycss2.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import tinycss2

logger = logging.getLogger(__name__)


@dataclass
class CSSDeclaration:
    """Representa uma declaração CSS individual."""

    property_name: str
    value: str
    selector: Optional[str] = None
    rule_type: str = "style"  # style, @media, @keyframes, etc.
    importance: bool = False


@dataclass
class CSSRule:
    """Representa uma regra CSS completa."""

    selector: str
    declarations: list[CSSDeclaration] = field(default_factory=list)
    at_rule: Optional[str] = None  # Para @media, @keyframes, etc.
    condition: Optional[str] = None  # Condição do @media, nome do @keyframes


@dataclass
class ParsedCSS:
    """Resultado do parsing de CSS."""

    rules: list[CSSRule] = field(default_factory=list)
    declarations: list[CSSDeclaration] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    keyframes: dict[str, list[CSSRule]] = field(default_factory=dict)
    media_queries: dict[str, list[CSSRule]] = field(default_factory=dict)


def parse_css(css_content: str, source_url: str = "unknown") -> ParsedCSS:
    """
    Parseia conteúdo CSS usando tinycss2.

    Args:
        css_content: String com o conteúdo CSS
        source_url: URL ou identificador da fonte do CSS

    Returns:
        ParsedCSS com regras, declarações e metadados
    """
    logger.debug(f"Parsing CSS from {source_url} ({len(css_content)} bytes)")

    parsed = ParsedCSS()

    try:
        rules = tinycss2.parse_stylesheet(
            css_content, skip_whitespace=True, skip_comments=True
        )
    except Exception as e:
        logger.warning(f"Error parsing CSS from {source_url}: {e}")
        return parsed

    for rule in rules:
        if rule.type == "error":
            continue

        if rule.type == "at-rule":
            _process_at_rule(rule, parsed)
        elif rule.type == "qualified-rule":
            _process_qualified_rule(rule, parsed)

    logger.debug(
        f"Parsed {len(parsed.rules)} rules, "
        f"{len(parsed.declarations)} declarations from {source_url}"
    )

    return parsed


def _process_at_rule(rule: Any, parsed: ParsedCSS) -> None:
    """Processa uma @-rule (media, keyframes, import, etc.)."""
    at_keyword = rule.at_keyword.lower()

    if at_keyword == "media":
        # Extrai condição do media query
        prelude = tinycss2.serialize(rule.prelude).strip()
        parsed.media_queries[prelude] = []

        if rule.content is not None:
            content_rules = tinycss2.parse_rule_list(
                rule.content, skip_whitespace=True, skip_comments=True
            )
            for inner_rule in content_rules:
                if inner_rule.type == "qualified-rule":
                    qualified = _parse_qualified_rule(inner_rule)
                    if qualified:
                        qualified.at_rule = "@media"
                        qualified.condition = prelude
                        parsed.rules.append(qualified)
                        parsed.media_queries[prelude].append(qualified)

    elif at_keyword == "keyframes" or at_keyword == "-webkit-keyframes":
        # Extrai nome dos keyframes
        prelude = tinycss2.serialize(rule.prelude).strip()
        parsed.keyframes[prelude] = []

        if rule.content is not None:
            content_rules = tinycss2.parse_rule_list(
                rule.content, skip_whitespace=True, skip_comments=True
            )
            for inner_rule in content_rules:
                if inner_rule.type == "qualified-rule":
                    qualified = _parse_qualified_rule(inner_rule)
                    if qualified:
                        qualified.at_rule = "@keyframes"
                        qualified.condition = prelude
                        parsed.keyframes[prelude].append(qualified)

    elif at_keyword == "import":
        # @import já foi resolvido no fetcher, ignoramos
        pass

    elif at_keyword in ("page", "font-face", "supports", "charset"):
        # Outros at-rules não processados neste MVP
        pass


def _process_qualified_rule(rule: Any, parsed: ParsedCSS) -> None:
    """Processa uma qualified-rule (seletor + declarações)."""
    qualified = _parse_qualified_rule(rule)
    if qualified:
        parsed.rules.append(qualified)


def _parse_qualified_rule(rule: Any) -> Optional[CSSRule]:
    """Parseia uma qualified-rule em CSSRule."""
    try:
        selector = tinycss2.serialize(rule.prelude).strip()
        if not selector:
            return None
    except Exception:
        return None

    declarations: list[CSSDeclaration] = []

    if rule.content is not None:
        decl_list = tinycss2.parse_declaration_list(
            rule.content, skip_whitespace=True, skip_comments=True
        )

        for item in decl_list:
            if item.type == "declaration":
                try:
                    prop_name = item.name.lower()
                    value = tinycss2.serialize(item.value).strip()
                    importance = item.important

                    decl = CSSDeclaration(
                        property_name=prop_name,
                        value=value,
                        selector=selector,
                        importance=importance,
                    )
                    declarations.append(decl)
                except Exception:
                    continue

    return CSSRule(selector=selector, declarations=declarations)


def extract_all_declarations(css_sources: dict[str, str]) -> list[CSSDeclaration]:
    """
    Extrai todas as declarações de múltiplas fontes CSS.

    Args:
        css_sources: Dict {url: css_content}

    Returns:
        Lista plana de todas as CSSDeclaration
    """
    all_declarations: list[CSSDeclaration] = []

    for source_url, css_content in css_sources.items():
        parsed = parse_css(css_content, source_url)
        
        # Extrai declarações das regras (onde estão realmente armazenadas)
        for rule in parsed.rules:
            all_declarations.extend(rule.declarations)
        
        # Extrai variáveis CSS (:root)
        for rule in parsed.rules:
            if ":root" in rule.selector:
                for decl in rule.declarations:
                    if decl.property_name.startswith("--"):
                        parsed.variables[decl.property_name] = decl.value

    return all_declarations


def normalize_value(value: str) -> str:
    """
    Normaliza um valor CSS removendo espaços extras e padronizando formato.

    Args:
        value: Valor CSS bruto

    Returns:
        Valor normalizado
    """
    # Remove múltiplos espaços
    normalized = re.sub(r"\s+", " ", value.strip())

    # Remove espaços dentro de funções (rgb, calc, etc.)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    normalized = re.sub(r"\s*,\s*", ",", normalized)

    return normalized
