"""
Aplicação CLI para acompanhamento de carteira de investimentos.

Esta é a interface principal do sistema, fornecendo comandos interativos
para gerenciar uma carteira de ações e fundos imobiliários (FIIs) do
mercado brasileiro, com foco em histórico de dividendos.

Uso:
    python main.py

Comandos disponíveis:
    1. Adicionar Ativo
    2. Remover Ativo
    3. Atualizar Dados (buscar cotações e dividendos)
    4. Visualizar Resumo
    5. Exportar JSON
    6. Listar Ativos
    7. Sair
"""

import sys
from datetime import datetime

from portfolio_manager import PortfolioManager
from calculator import consolidar_carteira, formatar_moeda, formatar_percentual
from exporter import gerar_exportacao_json
import data_fetcher


def exibir_menu() -> None:
    """Exibe o menu principal da aplicação."""
    print("\n" + "=" * 60)
    print("📊 ACOMPANHAMENTO DE CARTEIRA DE INVESTIMENTOS")
    print("=" * 60)
    print("1. ➕ Adicionar Ativo")
    print("2. 🗑️  Remover Ativo")
    print("3. 🔄 Atualizar Dados (cotações e dividendos)")
    print("4. 📈 Visualizar Resumo")
    print("5. 💾 Exportar JSON")
    print("6. 📋 Listar Ativos")
    print("7. 🚪 Sair")
    print("=" * 60)


def adicionar_ativo(pm: PortfolioManager) -> None:
    """
    Interativo para adicionar um novo ativo à carteira.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- ADICIONAR ATIVO ---")
    
    ticker = input("Digite o ticker do ativo (ex: PETR4, HGLG11): ").strip()
    if not ticker:
        print("[ERRO] Ticker não pode ser vazio.")
        return
    
    # Determinar tipo automaticamente
    tipo_detectado = data_fetcher.determinar_tipo_ativo(ticker)
    print(f"Tipo detectado: {tipo_detectado}")
    
    tipo_input = input(f"Confirme o tipo [{tipo_detectado}] ou digite ACAO/FII: ").strip().upper()
    if tipo_input:
        tipo = tipo_input
    else:
        tipo = tipo_detectado
    
    if tipo not in ["ACAO", "FII"]:
        print("[ERRO] Tipo inválido. Use ACAO ou FII.")
        return
    
    try:
        quantidade = float(input("Digite a quantidade: ").strip())
        preco_medio = float(input("Digite o preço médio de compra (R$): ").strip())
        
        if pm.adicionar_ativo(ticker, tipo, quantidade, preco_medio):
            print(f"[SUCESSO] Ativo {ticker} adicionado/atualizado na carteira.")
        else:
            print("[ERRO] Falha ao adicionar ativo.")
            
    except ValueError:
        print("[ERRO] Quantidade e preço médio devem ser números válidos.")


def remover_ativo(pm: PortfolioManager) -> None:
    """
    Interativo para remover um ativo da carteira.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- REMOVER ATIVO ---")
    
    ticker = input("Digite o ticker do ativo a remover: ").strip()
    if not ticker:
        print("[ERRO] Ticker não pode ser vazio.")
        return
    
    if pm.remover_ativo(ticker):
        print(f"[SUCESSO] Ativo {ticker.upper()} removido da carteira.")
    else:
        print(f"[ERRO] Ativo {ticker.upper()} não encontrado.")


def atualizar_dados(pm: PortfolioManager) -> None:
    """
    Atualiza cotações e dividendos de todos os ativos da carteira.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- ATUALIZANDO DADOS ---")
    
    ativos = pm.listar_ativos()
    if not ativos:
        print("[INFO] Carteira vazia. Adicione ativos primeiro.")
        return
    
    print(f"Atualizando {len(ativos)} ativo(s)...")
    print("-" * 40)
    
    for i, ativo in enumerate(ativos, 1):
        print(f"[{i}/{len(ativos)}] Buscando dados para {ativo.ticker}...", end=" ")
        
        # Buscar cotação
        cotacao = data_fetcher.obter_cotacao_atual(ativo.ticker)
        
        # Buscar dividendos
        proventos = data_fetcher.obter_historico_dividendos(ativo.ticker)
        
        if cotacao:
            print(f"Cotação: R$ {cotacao:.2f}", end="")
        else:
            print("Cotação: N/A", end="")
        
        if proventos:
            print(f" | Proventos (12m): {len(proventos)}", end="")
        else:
            print(" | Proventos: N/A", end="")
        
        print()
    
    print("-" * 40)
    print("[INFO] Atualização concluída!")


def visualizar_resumo(pm: PortfolioManager) -> None:
    """
    Exibe um resumo formatado da carteira no terminal.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- RESUMO DA CARTEIRA ---")
    
    carteira = pm.obter_carteira()
    ativos = pm.listar_ativos()
    
    if not ativos:
        print("[INFO] Carteira vazia. Adicione ativos primeiro.")
        return
    
    print("Atualizando dados dos ativos...")
    ativos_consolidados, resumo = consolidar_carteira(carteira)
    
    # Exibir cabeçalho da tabela
    print("\n" + "-" * 100)
    print(f"{'TICKER':<8} {'TIPO':<6} {'QTD':>10} {'PM':>12} {'ATUAL':>12} {'VALOR MERC':>14} {'L/P %':>10} {'YoC':>8} {'DY':>8}")
    print("-" * 100)
    
    # Exibir cada ativo
    for ativo in ativos_consolidados:
        ticker = ativo.ticker
        tipo = ativo.tipo.value[:4]  # ACAO ou FII
        qtd = f"{ativo.quantidade:.0f}"
        pm_str = formatar_moeda(ativo.preco_medio)
        atual = formatar_moeda(ativo.preco_atual)
        valor_merc = formatar_moeda(ativo.valor_mercado)
        lp_pct = formatar_percentual(ativo.lucro_prejuizo_percentual)
        yoc = f"{ativo.yield_on_cost:.2f}%" if ativo.yield_on_cost else "N/A"
        dy = f"{ativo.dividend_yield:.2f}%" if ativo.dividend_yield else "N/A"
        
        # Indicador de erro
        indicador = ""
        if ativo.erro_cotacao:
            indicador = " ⚠️"
        
        print(f"{ticker:<8} {tipo:<6} {qtd:>10} {pm_str:>12} {atual:>12} {valor_merc:>14} {lp_pct:>10} {yoc:>8} {dy:>8}{indicador}")
    
    print("-" * 100)
    
    # Exibir resumo geral
    print("\n📊 RESUMO GERAL:")
    print(f"   Valor Total Investido: {formatar_moeda(resumo.valor_total_investido)}")
    print(f"   Valor Total de Mercado: {formatar_moeda(resumo.valor_total_mercado)}")
    print(f"   Lucro/Prejuízo: {formatar_moeda(resumo.lucro_prejuizo_total)} ({formatar_percentual(resumo.lucro_prejuizo_percentual)})")
    print(f"   Proventos (últimos 12 meses): {formatar_moeda(resumo.total_proventos_12m)}")
    print(f"   Yield on Cost da Carteira: {formatar_percentual(resumo.yield_on_cost_carteira)}")
    print(f"   Dividend Yield da Carteira: {formatar_percentual(resumo.dividend_yield_carteira)}")
    print(f"   Quantidade de Ativos: {resumo.quantidade_ativos}")
    print(f"   Data da Atualização: {resumo.data_atualizacao}")


def exportar_json(pm: PortfolioManager) -> None:
    """
    Exporta todos os dados da carteira para um arquivo JSON.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- EXPORTAR JSON ---")
    
    carteira = pm.obter_carteira()
    ativos = pm.listar_ativos()
    
    if not ativos:
        print("[INFO] Carteira vazia. Nada para exportar.")
        return
    
    print("Consolidando dados...")
    ativos_consolidados, resumo = consolidar_carteira(carteira)
    
    nome_arquivo = input("Nome do arquivo de saída [carteira_consolidada.json]: ").strip()
    if not nome_arquivo:
        nome_arquivo = "carteira_consolidada.json"
    
    if not nome_arquivo.endswith(".json"):
        nome_arquivo += ".json"
    
    if gerar_exportacao_json(ativos_consolidados, resumo, nome_arquivo):
        print(f"[SUCESSO] Arquivo exportado: {nome_arquivo}")
    else:
        print("[ERRO] Falha ao exportar arquivo.")


def listar_ativos(pm: PortfolioManager) -> None:
    """
    Lista todos os ativos cadastrados na carteira.

    Args:
        pm: Instância do PortfolioManager.
    """
    print("\n--- LISTA DE ATIVOS ---")
    
    ativos = pm.listar_ativos()
    
    if not ativos:
        print("[INFO] Carteira vazia.")
        return
    
    print(f"Total de ativos: {len(ativos)}\n")
    
    for ativo in ativos:
        print(f"  • {ativo.ticker} ({ativo.tipo.value})")
        print(f"    Quantidade: {ativo.quantidade:.2f} | Preço Médio: R$ {ativo.preco_medio:.2f}")
        print(f"    Valor Investido: R$ {ativo.valor_investido:.2f}")
        print(f"    Proventos Recebidos: R$ {ativo.total_proventos_recebidos():.2f}")
        print()


def validar_ticker() -> None:
    """
    Função utilitária para validar um ticker específico.
    """
    print("\n--- VALIDAR TICKER ---")
    ticker = input("Digite o ticker para validar: ").strip()
    
    if not ticker:
        print("[ERRO] Ticker não pode ser vazio.")
        return
    
    print(f"Validando {ticker}...")
    
    valido = data_fetcher.validar_ticker(ticker)
    if valido:
        print(f"[OK] {ticker} é um ticker válido.")
        
        # Mostrar informações adicionais
        info = data_fetcher.obter_informacoes_ativo(ticker)
        if info:
            print(f"  Nome: {info.get('nome', 'N/A')}")
            print(f"  Tipo: {info.get('tipo', 'N/A')}")
    else:
        print(f"[ERRO] {ticker} não foi encontrado ou está indisponível.")


def main() -> None:
    """Função principal que executa o loop da aplicação CLI."""
    print("\n🎯 Bem-vindo ao Acompanhamento de Carteira de Investimentos!")
    print("   Focado em Ações e FIIs do mercado brasileiro (B3)")
    print("   Dados fornecidos por yfinance\n")
    
    # Inicializar gerenciador de carteira
    pm = PortfolioManager()
    
    while True:
        exibir_menu()
        
        opcao = input("\nEscolha uma opção [1-7]: ").strip()
        
        if opcao == "1":
            adicionar_ativo(pm)
        elif opcao == "2":
            remover_ativo(pm)
        elif opcao == "3":
            atualizar_dados(pm)
        elif opcao == "4":
            visualizar_resumo(pm)
        elif opcao == "5":
            exportar_json(pm)
        elif opcao == "6":
            listar_ativos(pm)
        elif opcao == "7":
            print("\n👋 Obrigado por usar o sistema! Até logo.\n")
            break
        else:
            print("\n[ERRO] Opção inválida. Por favor, escolha uma opção de 1 a 7.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Aplicação interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro inesperado: {e}")
        print("Por favor, verifique os logs e tente novamente.")
        sys.exit(1)
