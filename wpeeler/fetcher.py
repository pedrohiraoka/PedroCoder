"""
WPeeler - Web Design DNA Extractor

Módulo de fetch: download de HTML e extração de CSS.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Headers realistas para evitar bloqueios
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class FetchError(Exception):
    """Erro ao buscar conteúdo da URL."""

    pass


class CSSFetchError(Exception):
    """Erro ao buscar arquivo CSS externo."""

    pass


def fetch_url(url: str, timeout: int = 10) -> dict[str, Any]:
    """
    Faz download do HTML de uma URL e extrai informações básicas.

    Args:
        url: URL para fetch
        timeout: Timeout em segundos para a requisição

    Returns:
        Dict com:
            - url_original: URL fornecida
            - final_url: URL após redirects
            - html: Conteúdo HTML bruto
            - css_sources: Dict {url_css: conteudo_css}
            - inline_styles: Lista de blocos <style> inline

    Raises:
        FetchError: Se houver erro na requisição HTTP
    """
    logger.info(f"Fetching URL: {url}")

    try:
        response = requests.get(
            url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to fetch {url}: {e}")

    # Detecta encoding
    if response.encoding is None or response.encoding == "ISO-8859-1":
        response.encoding = response.apparent_encoding

    html_content = response.text
    final_url = response.url

    logger.info(f"Successfully fetched {final_url} ({len(html_content)} bytes)")

    # Parseia HTML para extrair referências CSS
    soup = BeautifulSoup(html_content, "html.parser")

    # Extrai inline styles
    inline_styles: list[str] = []
    for style_tag in soup.find_all("style"):
        if style_tag.string:
            inline_styles.append(style_tag.string)
        elif style_tag.contents:
            # Concatena todos os Text nodes dentro de <style>
            style_content = "".join(str(c) for c in style_tag.contents if isinstance(c, str))
            if style_content.strip():
                inline_styles.append(style_content)

    logger.info(f"Found {len(inline_styles)} inline <style> blocks")

    # Extrai links para CSS externos
    css_links: list[str] = []
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            # Resolve URL relativa
            absolute_url = urljoin(final_url, href)
            css_links.append(absolute_url)

    logger.info(f"Found {len(css_links)} external CSS links")

    # Baixa CSS externos
    css_sources: dict[str, str] = {}
    for css_url in css_links:
        try:
            css_content = fetch_css_file(css_url, timeout=timeout)
            css_sources[css_url] = css_content
            logger.debug(f"Fetched CSS from {css_url} ({len(css_content)} bytes)")
        except CSSFetchError as e:
            logger.warning(f"Failed to fetch CSS from {css_url}: {e}")
            continue

    # Adiciona inline styles com URL especial
    for i, inline_css in enumerate(inline_styles):
        inline_key = f"inline_{i}"
        css_sources[inline_key] = inline_css

    return {
        "url_original": url,
        "final_url": final_url,
        "html": html_content,
        "css_sources": css_sources,
    }


def fetch_css_file(url: str, timeout: int = 10) -> str:
    """
    Baixa um arquivo CSS de uma URL.

    Args:
        url: URL do arquivo CSS
        timeout: Timeout em segundos

    Returns:
        Conteúdo do CSS como string

    Raises:
        CSSFetchError: Se houver erro no fetch
    """
    try:
        response = requests.get(
            url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise CSSFetchError(f"Failed to fetch CSS from {url}: {e}")

    # Detecta encoding
    if response.encoding is None or response.encoding == "ISO-8859-1":
        response.encoding = response.apparent_encoding

    return response.text


def resolve_css_imports(
    css_content: str, base_url: str, timeout: int = 5
) -> tuple[str, dict[str, str]]:
    """
    Resolve @import statements em um CSS.

    Args:
        css_content: Conteúdo CSS original
        base_url: URL base para resolver imports relativos
        timeout: Timeout para fetch de imports

    Returns:
        Tuple (css_com_imports_resolvidos, dict_de_imports_baixados)
    """
    import re

    imported_css: dict[str, str] = {}

    # Pattern para @import
    import_pattern = re.compile(
        r'@import\s+(?:url\(["\']?([^"\')]+)["\']?\)|["\']([^"\']+)["\'])\s*;?',
        re.IGNORECASE,
    )

    def replace_import(match: re.Match) -> str:
        import_url = match.group(1) or match.group(2)
        if not import_url:
            return match.group(0)

        # Resolve URL relativa
        absolute_url = urljoin(base_url, import_url)

        try:
            if absolute_url not in imported_css:
                css = fetch_css_file(absolute_url, timeout=timeout)
                imported_css[absolute_url] = css
                # Recursivamente resolve imports no CSS baixado
                resolved, nested = resolve_css_imports(css, absolute_url, timeout)
                imported_css.update(nested)
                return resolved
            else:
                return imported_css[absolute_url]
        except CSSFetchError as e:
            logger.warning(f"Failed to resolve @import {absolute_url}: {e}")
            return ""  # Remove o @import falho

    resolved_css = import_pattern.sub(replace_import, css_content)
    return resolved_css, imported_css
