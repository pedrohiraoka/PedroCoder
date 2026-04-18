#!/usr/bin/env python3
"""
WPeeler - Web Design DNA Extractor

CLI entrypoint para análise de DNA visual de websites.

Uso:
    python main.py https://exemplo.com
    python main.py https://exemplo.com --output resultado.json --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Importações relativas ajustadas para execução direta
try:
    from .fetcher import FetchError, fetch_url
    from .analyzer import analyze_css
    from .output import (
        create_site_visual_dna,
        format_report,
        print_summary,
        save_json,
    )
    from .utils import extract_domain
except ImportError:
    from fetcher import FetchError, fetch_url
    from analyzer import analyze_css
    from output import (
        create_site_visual_dna,
        format_report,
        print_summary,
        save_json,
    )
    from utils import extract_domain


def setup_logging(verbose: bool = False) -> None:
    """
    Configura logging para a aplicação.

    Args:
        verbose: Se True, habilita logs DEBUG
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_url(url: str) -> str:
    """
    Valida e normaliza uma URL.

    Args:
        url: URL fornecida pelo usuário

    Returns:
        URL normalizada com scheme

    Raises:
        ValueError: Se a URL for inválida
    """
    from urllib.parse import urlparse

    url = url.strip()

    # Adiciona scheme se ausente
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"URL inválida: {url}")

    return url


def run_analysis(url: str, output_path: Path | None = None) -> int:
    """
    Executa o fluxo completo de análise.

    Args:
        url: URL do site para analisar
        output_path: Caminho opcional para salvar JSON

    Returns:
        Código de saída (0 para sucesso, 1 para erro)
    """
    logger = logging.getLogger(__name__)

    try:
        # Step 1: Fetch HTML e CSS
        logger.info(f"Iniciando análise de {url}")
        print(f"\n🔍 Buscando conteúdo de {url}...")

        fetched_data = fetch_url(url, timeout=15)

        if not fetched_data["css_sources"]:
            logger.warning("Nenhum CSS encontrado no site")
            print("\n⚠️  Aviso: Nenhum CSS foi encontrado neste site.")
            print("   A análise será limitada.")

        # Step 2: Analisar CSS
        print("📊 Analisando padrões visuais...")
        analysis_result = analyze_css(fetched_data["css_sources"])

        # Step 3: Criar modelo validado
        dna = create_site_visual_dna(fetched_data["final_url"], analysis_result)

        # Step 4: Exibir relatório
        format_report(dna)
        print_summary(dna)

        # Step 5: Salvar JSON
        save_json(dna, output_path)

        logger.info(f"Análise concluída com sucesso para {url}")
        return 0

    except FetchError as e:
        logging.error(f"Erro ao buscar URL: {e}")
        print(f"\n❌ Erro ao buscar {url}: {e}")
        print("   Verifique se a URL está correta e acessível.")
        return 1

    except Exception as e:
        logging.exception(f"Erro inesperado: {e}")
        print(f"\n❌ Erro inesperado: {e}")
        print("   Consulte o log para mais detalhes.")
        return 1


def main() -> int:
    """
    Ponto de entrada principal da CLI.

    Returns:
        Código de saída (0 para sucesso, 1 para erro)
    """
    parser = argparse.ArgumentParser(
        prog="wpeeler",
        description="WPeeler - Web Design DNA Extractor\n\n"
        "Extrai automaticamente a 'Alma Matemática' (DNA visual) de um site, "
        "retornando padrões tipográficos, escala de espaçamentos, paleta de cores "
        "e tempos de animação.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s https://stripe.com
  %(prog)s https://vercel.com --output vercel-dna.json
  %(prog)s https://example.com --verbose
        """,
    )

    parser.add_argument(
        "url",
        type=str,
        help="URL do site para análise (ex: https://stripe.com)",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Caminho para salvar o JSON (padrão: wpeeler_<domain>_<timestamp>.json)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Habilitar logs detalhados",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Validate URL
    try:
        url = validate_url(args.url)
    except ValueError as e:
        print(f"❌ {e}")
        return 1

    # Prepare output path
    output_path = Path(args.output) if args.output else None

    # Run analysis
    return run_analysis(url, output_path)


if __name__ == "__main__":
    sys.exit(main())
