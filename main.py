#!/usr/bin/env python3
"""
main.py
Interface de Linha de Comando (CLI) para coleta e exportação de dados brutos da B3.

Este script orquestra a coleta de dados de múltiplos ativos e exporta
para um arquivo JSON estruturado para consumo por IA externa.

Uso:
    python main.py
    
O script solicitará os tickers via input e gerará o arquivo 'dados_brutos_carteira.json'.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from coletor import (
    validar_ticker,
    coletar_todos_dados_ativo,
    PYNVEST_AVAILABLE
)


def configurar_logging():
    """Configura o sistema de logging para exibir informações durante a execução."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def parse_input_tickers(input_text: str) -> list:
    """
    Processa o input do usuário e retorna lista de tickers válidos.
    
    - Remove espaços em branco
    - Converte para maiúsculas
    - Remove entradas vazias
    - Mantém ordem original
    
    Args:
        input_text (str): Texto bruto do input do usuário.
    
    Returns:
        list: Lista de tickers processados.
    """
    if not input_text.strip():
        return []
    
    # Separa por vírgula, limpa espaços e converte para maiúsculas
    tickers = [t.strip().upper() for t in input_text.split(',')]
    
    # Remove entradas vazias que possam ter sido criadas por vírgulas extras
    tickers = [t for t in tickers if t]
    
    return tickers


def validar_tickers(tickers: list) -> tuple:
    """
    Valida cada ticker contra a base de dados.
    
    Args:
        tickers (list): Lista de tickers para validar.
    
    Returns:
        tuple: (lista_validos, lista_invalidos)
    """
    validos = []
    invalidos = []
    
    logging.info("Validando tickers na base de dados...")
    
    for ticker in tickers:
        if validar_ticker(ticker):
            validos.append(ticker)
            logging.info(f"  ✓ {ticker} - Válido")
        else:
            invalidos.append(ticker)
            logging.warning(f"  ✗ {ticker} - Inválido ou não encontrado")
    
    return validos, invalidos


def coletar_dados_carteira(tickers: list) -> dict:
    """
    Coleta dados de todos os tickers válidos da carteira.
    
    Args:
        tickers (list): Lista de tickers válidos.
    
    Returns:
        dict: Dicionário com dados de todos os ativos.
    """
    ativos = {}
    total = len(tickers)
    
    for i, ticker in enumerate(tickers, 1):
        logging.info(f"[{i}/{total}] Processando {ticker}...")
        try:
            dados = coletar_todos_dados_ativo(ticker)
            ativos[ticker] = dados
        except Exception as e:
            logging.error(f"Erro crítico ao processar {ticker}: {e}")
            # Continua para o próximo ticker mesmo em caso de erro
            ativos[ticker] = {
                'dados_cadastrais': {},
                'historico_cotacoes': [],
                'indicadores_fundamentalistas': {'erro': str(e)},
                'proventos_historicos': []
            }
    
    return ativos


def criar_estrutura_saida(ativos: dict, tickers_originais: list, tickers_invalidos: list) -> dict:
    """
    Cria a estrutura final do JSON conforme especificação.
    
    Estrutura hierárquica otimizada para parsing por LLMs:
    - metadata: Informações sobre a geração do arquivo
    - ativos: Dados organizados por ticker
    - resumo_validacao: Informações sobre tickers inválidos
    
    Args:
        ativos (dict): Dicionário com dados dos ativos.
        tickers_originais (list): Lista original de tickers solicitados.
        tickers_invalidos (list): Lista de tickers que não foram encontrados.
    
    Returns:
        dict: Estrutura completa pronta para exportação JSON.
    """
    fontes_dados = ["B3 (via brasa-marketdata)"]
    if PYNVEST_AVAILABLE:
        fontes_dados.append("Fundamentus (via pynvest)")
    else:
        fontes_dados.append("Fundamentus (via pynvest) - NÃO DISPONÍVEL")
    
    saida = {
        "metadata": {
            "gerado_em": datetime.now().isoformat(),
            "fonte_dados": fontes_dados,
            "tickers_solicitados": tickers_originais,
            "tickers_validos": list(ativos.keys()),
            "tickers_invalidos": tickers_invalidos,
            "versao_script": "1.0.0",
            "observacoes": [
                "dados_cadastrais: Origem B3 - Cadastro oficial de negociação",
                "historico_cotacoes: Origem B3 - Sistema COTAHIST (dados diários)",
                "indicadores_fundamentalistas: Origem Fundamentus - Indicadores calculados",
                "proventos_historicos: Origem B3 - Eventos corporativos",
                "Campos null/None indicam dados indisponíveis na fonte original"
            ]
        },
        "ativos": ativos,
        "resumo_validacao": {
            "total_solicitados": len(tickers_originais),
            "total_validos": len(ativos),
            "total_invalidos": len(tickers_invalidos),
            "invalidos_detalhes": tickers_invalidos
        }
    }
    
    return saida


def exportar_json(dados: dict, nome_arquivo: str = "dados_brutos_carteira.json"):
    """
    Exporta os dados para arquivo JSON formatado.
    
    Args:
        dados (dict): Dados a serem exportados.
        nome_arquivo (str): Nome do arquivo de saída.
    
    Returns:
        str: Caminho completo do arquivo gerado.
    """
    caminho = Path(nome_arquivo)
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
    
    logging.info(f"Arquivo exportado com sucesso: {caminho.absolute()}")
    return str(caminho.absolute())


def main():
    """Função principal que executa o fluxo completo da CLI."""
    configurar_logging()
    
    print("=" * 60)
    print("COLETOR DE DADOS BRUTOS - B3")
    print("=" * 60)
    print()
    
    if not PYNVEST_AVAILABLE:
        print("⚠️  AVISO: pynvest não instalado. Dados fundamentalistas não serão coletados.")
        print("   Instale com: pip install pynvest")
        print()
    
    # Solicita input do usuário
    print("Digite os tickers separados por vírgula (ex: PETR4, VALE3, HGLG11):")
    input_text = input("> ").strip()
    
    # Processa input
    tickers_originais = parse_input_tickers(input_text)
    
    if not tickers_originais:
        logging.error("Nenhum ticker válido fornecido. Encerrando.")
        return
    
    logging.info(f"Tickers recebidos: {tickers_originais}")
    
    # Valida tickers
    tickers_validos, tickers_invalidos = validar_tickers(tickers_originais)
    
    if not tickers_validos:
        logging.error("Nenhum ticker válido encontrado. Encerrando.")
        return
    
    logging.info(f"Tickers válidos: {len(tickers_validos)}")
    if tickers_invalidos:
        logging.warning(f"Tickers ignorados: {tickers_invalidos}")
    
    print()
    print("-" * 60)
    print("INICIANDO COLETA DE DADOS")
    print("-" * 60)
    
    # Coleta dados
    ativos = coletar_dados_carteira(tickers_validos)
    
    print()
    print("-" * 60)
    print("GERANDO ARQUIVO DE SAÍDA")
    print("-" * 60)
    
    # Cria estrutura de saída
    dados_saida = criar_estrutura_saida(ativos, tickers_originais, tickers_invalidos)
    
    # Exporta JSON
    caminho_arquivo = exportar_json(dados_saida)
    
    print()
    print("=" * 60)
    print("COLETA CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"Arquivo gerado: {caminho_arquivo}")
    print(f"Total de ativos processados: {len(ativos)}")
    if tickers_invalidos:
        print(f"Tickers ignorados (inválidos): {len(tickers_invalidos)}")
    print()


if __name__ == "__main__":
    main()
