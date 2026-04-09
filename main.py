"""
Main - Ponto de entrada da aplicação

Executa o crawler via CLI ou como script direto.
"""

import sys
from src.cli import app


def main():
    """Ponto de entrada principal."""
    try:
        app()
    except KeyboardInterrupt:
        print("\nInterrupto pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
