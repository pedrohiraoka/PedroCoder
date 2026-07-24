#!/usr/bin/env python3
"""
Aplicação CLI para Acompanhamento de Carteira de Investimentos B3.

Gerencia ações e FIIs da bolsa brasileira com:
- Coleta de dados oficiais (brasa-marketdata, pynvest)
- Cálculos financeiros automáticos
- Exportação para JSON
- Interface rica com rich
"""

import argparse
import logging
import sys
from typing import Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importações condicionais para rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from portfolio_manager import PortfolioManager
from exporter import Exporter


def get_console() -> Optional[Console]:
    """Retorna uma instância do Console rich se disponível."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_table(console: Console, title: str, columns: list, data: list) -> None:
    """
    Imprime uma tabela formatada usando rich.
    
    Args:
        console: Instância do Console rich.
        title: Título da tabela.
        columns: Lista de tuplas (nome, justificativa).
        data: Lista de listas com os dados.
    """
    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
    
    for col_name, justify in columns:
        table.add_column(col_name, justify=justify)
    
    for row in data:
        table.add_row(*[str(cell) for cell in row])
    
    console.print(table)


def print_panel(console: Console, content: str, title: str = "") -> None:
    """Imprime um painel formatado."""
    console.print(Panel(content, title=title, border_style="green"))


def cmd_add_asset(args, portfolio: PortfolioManager) -> int:
    """Comando para adicionar ativo."""
    success = portfolio.add_asset(
        ticker=args.ticker,
        quantity=args.quantity,
        average_price=args.price,
        asset_type=args.type
    )
    
    if success:
        print(f"✓ Ativo {args.ticker.upper()} adicionado/atualizado com sucesso!")
        return 0
    else:
        print(f"✗ Erro ao adicionar ativo {args.ticker.upper()}")
        return 1


def cmd_remove_asset(args, portfolio: PortfolioManager) -> int:
    """Comando para remover ativo."""
    success = portfolio.remove_asset(args.ticker)
    
    if success:
        print(f"✓ Ativo {args.ticker.upper()} removido com sucesso!")
        return 0
    else:
        print(f"✗ Ativo {args.ticker.upper()} não encontrado ou erro na remoção")
        return 1


def cmd_list_assets(args, portfolio: PortfolioManager) -> int:
    """Comando para listar ativos."""
    assets = portfolio.get_all_assets()
    
    if not assets:
        print("Nenhum ativo cadastrado na carteira.")
        return 0
    
    console = get_console()
    
    if console and RICH_AVAILABLE:
        columns = [
            ("Ticker", "left"),
            ("Tipo", "center"),
            ("Qtd", "right"),
            ("Preço Médio", "right"),
            ("Criado Em", "left")
        ]
        
        data = [
            [
                a['ticker'],
                a['asset_type'],
                a['quantity'],
                f"R$ {a['average_price']:.2f}",
                a['created_at'][:10]
            ]
            for a in assets
        ]
        
        print_table(console, "Carteira de Ativos", columns, data)
    else:
        # Fallback sem rich
        print(f"{'Ticker':<10} {'Tipo':<6} {'Qtd':>8} {'Preço Médio':>15} {'Criado Em'}")
        print("-" * 60)
        for a in assets:
            print(
                f"{a['ticker']:<10} {a['asset_type']:<6} {a['quantity']:>8} "
                f"R$ {a['average_price']:>12.2f} {a['created_at'][:10]}"
            )
    
    return 0


def cmd_show_portfolio(args, portfolio: PortfolioManager) -> int:
    """Comando para mostrar resumo da carteira com métricas."""
    console = get_console()
    
    metrics = portfolio.calculate_portfolio_metrics()
    summary = portfolio.get_portfolio_summary()
    
    if not metrics:
        print("Carteira vazia. Adicione ativos primeiro.")
        return 0
    
    if console and RICH_AVAILABLE:
        # Tabela de ativos com métricas
        columns = [
            ("Ticker", "left"),
            ("Qtd", "right"),
            ("Preço Médio", "right"),
            ("Atual", "right"),
            ("Investido", "right"),
            ("Mercado", "right"),
            ("L/P", "right"),
            ("L/P %", "right"),
            ("DY on Cost", "right")
        ]
        
        data = []
        for m in metrics:
            lp_pct_str = f"{m['profit_loss_pct']:+.2f}%"
            dy_str = f"{m['dividend_yield_on_cost']:.2f}%"
            
            current_price_str = f"R$ {m['current_price']:.2f}" if m['current_price'] else "N/A"
            
            data.append([
                m['ticker'],
                m['quantity'],
                f"R$ {m['average_price']:.2f}",
                current_price_str,
                f"R$ {m['invested_value']:.2f}",
                f"R$ {m['market_value']:.2f}",
                f"R$ {m['profit_loss']:.2f}",
                lp_pct_str,
                dy_str
            ])
        
        print_table(console, "Resumo da Carteira", columns, data)
        
        # Painel de resumo financeiro
        summary_text = f"""
Total Investido:      R$ {summary['total_invested']:,.2f}
Valor de Mercado:     R$ {summary['total_market_value']:,.2f}
Lucro/Prejuízo:       R$ {summary['total_profit_loss']:,.2f} ({summary['total_profit_loss_pct']:+.2f}%)
Total Proventos:      R$ {summary['total_dividends_received']:,.2f}
Ativos:               {summary['assets_count']}
        """
        
        print_panel(console, summary_text, "Resumo Financeiro")
    else:
        # Fallback sem rich
        print(f"\n{'Ticker':<10} {'Qtd':>6} {'P.Médio':>10} {'Atual':>10} {'Investido':>12} {'Mercado':>12} {'L/P':>12} {'L/P%':>10}")
        print("-" * 95)
        for m in metrics:
            current_price_str = f"{m['current_price']:.2f}" if m['current_price'] else "N/A"
            print(
                f"{m['ticker']:<10} {m['quantity']:>6} {m['average_price']:>10.2f} "
                f"{current_price_str:>10} {m['invested_value']:>12.2f} {m['market_value']:>12.2f} "
                f"{m['profit_loss']:>12.2f} {m['profit_loss_pct']:>+10.2f}%"
            )
        
        print("\n=== RESUMO FINANCEIRO ===")
        print(f"Total Investido:     R$ {summary['total_invested']:,.2f}")
        print(f"Valor de Mercado:    R$ {summary['total_market_value']:,.2f}")
        print(f"Lucro/Prejuízo:      R$ {summary['total_profit_loss']:,.2f} ({summary['total_profit_loss_pct']:+.2f}%)")
        print(f"Total Proventos:     R$ {summary['total_dividends_received']:,.2f}")
        print(f"Ativos:              {summary['assets_count']}")
    
    return 0


def cmd_add_dividend(args, portfolio: PortfolioManager) -> int:
    """Comando para registrar provento."""
    success = portfolio.register_dividend(
        ticker=args.ticker,
        date=args.date,
        value_per_share=args.value,
        record_type=args.type
    )
    
    if success:
        print(f"✓ Provento registrado: {args.ticker.upper()} - R$ {args.value:.2f}/cota em {args.date}")
        return 0
    else:
        print(f"✗ Erro ao registrar provento para {args.ticker.upper()}")
        return 1


def cmd_dividend_history(args, portfolio: PortfolioManager) -> int:
    """Comando para mostrar histórico de proventos."""
    dividends = portfolio.get_dividend_history(args.ticker if args.ticker else None)
    
    if not dividends:
        print("Nenhum provento registrado.")
        return 0
    
    console = get_console()
    
    if console and RICH_AVAILABLE:
        columns = [
            ("Data", "left"),
            ("Ticker", "left"),
            ("Tipo", "center"),
            ("Valor/Cota", "right"),
            ("Total", "right")
        ]
        
        data = [
            [
                d['date'],
                d['ticker'],
                d['record_type'],
                f"R$ {d['value_per_share']:.2f}",
                f"R$ {d['total_value']:.2f}"
            ]
            for d in dividends
        ]
        
        print_table(console, "Histórico de Proventos", columns, data)
    else:
        print(f"\n{'Data':<12} {'Ticker':<10} {'Tipo':<12} {'Valor/Cota':>12} {'Total':>12}")
        print("-" * 65)
        for d in dividends:
            print(
                f"{d['date']:<12} {d['ticker']:<10} {d['record_type']:<12} "
                f"R$ {d['value_per_share']:>9.2f} R$ {d['total_value']:>9.2f}"
            )
    
    return 0


def cmd_export(args, portfolio: PortfolioManager) -> int:
    """Comando para exportar carteira para JSON."""
    exporter = Exporter(portfolio)
    
    try:
        output_file = exporter.export_to_json(
            output_path=args.output,
            include_raw_data=args.raw
        )
        print(f"✓ Dados exportados com sucesso para: {output_file}")
        return 0
    except Exception as e:
        print(f"✗ Erro ao exportar: {str(e)}")
        return 1


def main() -> int:
    """
    Função principal da CLI.
    
    Returns:
        Código de retorno (0 para sucesso, diferente de 0 para erro).
    """
    parser = argparse.ArgumentParser(
        description="Acompanhamento de Carteira de Investimentos B3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s add PETR4 --quantity 100 --price 35.50 --type ACAO
  %(prog)s add HGLG11 --quantity 50 --price 105.00 --type FII
  %(prog)s list
  %(prog)s show
  %(prog)s dividend PETR4 --date 2024-01-15 --value 0.85
  %(prog)s history
  %(prog)s export --output minha_carteira.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando: add (adicionar ativo)
    parser_add = subparsers.add_parser('add', help='Adicionar/atualizar ativo na carteira')
    parser_add.add_argument('ticker', type=str, help='Ticker do ativo (ex: PETR4, HGLG11)')
    parser_add.add_argument('--quantity', '-q', type=int, required=True, help='Quantidade de cotas/ações')
    parser_add.add_argument('--price', '-p', type=float, required=True, help='Preço médio de compra')
    parser_add.add_argument(
        '--type', '-t', 
        type=str, 
        choices=['ACAO', 'FII'], 
        default='ACAO',
        help='Tipo de ativo (padrão: ACAO)'
    )
    
    # Comando: remove (remover ativo)
    parser_remove = subparsers.add_parser('remove', help='Remover ativo da carteira')
    parser_remove.add_argument('ticker', type=str, help='Ticker do ativo')
    
    # Comando: list (listar ativos)
    subparsers.add_parser('list', help='Listar todos os ativos cadastrados')
    
    # Comando: show (mostrar resumo com métricas)
    subparsers.add_parser('show', help='Mostrar resumo da carteira com métricas calculadas')
    
    # Comando: dividend (registrar provento)
    parser_div = subparsers.add_parser('dividend', help='Registrar provento recebido')
    parser_div.add_argument('ticker', type=str, help='Ticker do ativo')
    parser_div.add_argument('--date', '-d', type=str, required=True, help='Data do provento (YYYY-MM-DD)')
    parser_div.add_argument('--value', '-v', type=float, required=True, help='Valor por cota/ação')
    parser_div.add_argument(
        '--type', '-t',
        type=str,
        choices=['DIVIDENDO', 'JCP'],
        default='DIVIDENDO',
        help='Tipo de provento (padrão: DIVIDENDO)'
    )
    
    # Comando: history (histórico de proventos)
    parser_hist = subparsers.add_parser('history', help='Mostrar histórico de proventos')
    parser_hist.add_argument('--ticker', type=str, help='Filtrar por ticker específico')
    
    # Comando: export (exportar para JSON)
    parser_export = subparsers.add_parser('export', help='Exportar carteira para JSON')
    parser_export.add_argument(
        '--output', '-o',
        type=str,
        default='investimentos_export.json',
        help='Arquivo de saída (padrão: investimentos_export.json)'
    )
    parser_export.add_argument(
        '--raw',
        action='store_true',
        help='Incluir dados brutos na exportação'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Inicializa o gerenciador de carteira
    portfolio = PortfolioManager()
    
    # Mapeia comandos para funções
    commands = {
        'add': cmd_add_asset,
        'remove': cmd_remove_asset,
        'list': cmd_list_assets,
        'show': cmd_show_portfolio,
        'dividend': cmd_add_dividend,
        'history': cmd_dividend_history,
        'export': cmd_export
    }
    
    if args.command in commands:
        return commands[args.command](args, portfolio)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
