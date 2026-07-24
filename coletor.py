#!/usr/bin/env python3
"""
Coletor de Dados Brutos de Ativos da B3 (FIIs e Ações)

Este script coleta dados fundamentais e de mercado de ativos listados na B3
usando fontes 100% gratuitas (pynvest/Fundamentus e brasa-marketdata).

Os dados são exportados em um arquivo JSON estruturado para consumo por IA externa.

Autor: Engenheiro de Software Sênior - Especialista em Python
Data: 2026
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Any

import pandas as pd

try:
    from pynvest.scrappers.fundamentus import Fundamentus
    PYNVEST_AVAILABLE = True
except ImportError:
    PYNVEST_AVAILABLE = False
    print("Aviso: pynvest não disponível. Dados do Fundamentus não serão coletados.")

try:
    import brasa
    BRASA_AVAILABLE = True
except ImportError:
    BRASA_AVAILABLE = False
    print("Aviso: brasa-marketdata não disponível. Dados B3 não serão coletados.")


def parse_tickers_input(input_text: str) -> list[str]:
    """
    Processa a entrada de texto do usuário e retorna uma lista de tickers.
    
    Args:
        input_text: String contendo tickers separados por vírgula.
        
    Returns:
        Lista de tickers padronizados (maiúsculas, sem espaços).
    """
    if not input_text.strip():
        return []
    
    tickers = [
        ticker.strip().upper() 
        for ticker in input_text.split(',') 
        if ticker.strip()
    ]
    return tickers


def collect_fundamentus_data(ticker: str, fundamentus: Fundamentus) -> dict[str, Any]:
    """
    Coleta dados fundamentais de um ativo via scraping do Fundamentus (pynvest).
    
    Fonte: https://www.fundamentus.com.br
    
    Args:
        ticker: Símbolo do ativo (ex: PETR4, HGLG11).
        fundamentus: Instância da classe Fundamentus do pynvest.
        
    Returns:
        Dicionário com os dados fundamentais do ativo.
        
    Raises:
        Exception: Caso ocorra erro na coleta (timeout, dado indisponível, etc.).
    """
    df = fundamentus.coleta_indicadores_de_ativo(ticker)
    
    if df is None or (hasattr(df, 'empty') and df.empty):
        raise ValueError(f"Nenhum dado encontrado para {ticker} no Fundamentus")
    
    # Converte DataFrame para dicionário, tratando valores únicos
    data_dict = {}
    for col in df.columns:
        val = df[col].iloc[0] if len(df) > 0 else None
        data_dict[col] = val
    
    return data_dict


def collect_brasa_data(ticker: str) -> dict[str, Any]:
    """
    Tenta coletar dados de mercado via brasa-marketdata (dados oficiais B3/CVM).
    
    Nota: brasa-marketdata requer download prévio dos dados. Se os dados não
    estiverem em cache, esta função retorná um dicionário vazio ou com erro.
    
    Fontes:
    - b3-company-info: Informações cadastrais das empresas
    - b3-company-details: Detalhes adicionais das empresas
    
    Args:
        ticker: Símbolo do ativo (ex: PETR4, HGLG11).
        
    Returns:
        Dicionário com dados de mercado ou mensagem de indisponibilidade.
    """
    result = {"fonte": "brasa-marketdata", "dados": {}}
    
    # Tenta obter informações da empresa
    try:
        df_info = brasa.get_marketdata('b3-company-info')
        if df_info is not None and not df_info.empty:
            # Filtra pelo ticker
            mask = df_info['cd_cvm'].astype(str).str.contains(ticker.replace('3', '').replace('4', '').replace('11', ''), na=False)
            if mask.any():
                row = df_info[mask].iloc[0]
                result["dados"]["company_info"] = row.to_dict()
    except Exception:
        pass  # Silenciosamente ignora se brasa falhar
    
    return result


def process_single_ticker(ticker: str, fundamentus: Fundamentus | None) -> dict[str, Any]:
    """
    Processa um único ticker, coletando dados de todas as fontes disponíveis.
    
    Args:
        ticker: Símbolo do ativo.
        fundamentus: Instância do Fundamentus ou None se indisponível.
        
    Returns:
        Dicionário estruturado com todos os dados coletados ou erro.
    """
    result: dict[str, Any] = {
        "ticker": ticker,
        "timestamp_coleta": datetime.now(timezone(timedelta(hours=-3))).isoformat(),
        "dados": {},
        "erros": []
    }
    
    # Coleta dados do Fundamentus (fonte primária)
    if fundamentus is not None:
        try:
            fundamentus_data = collect_fundamentus_data(ticker, fundamentus)
            result["dados"]["fundamentus"] = fundamentus_data
            result["dados"]["fundamentus"]["fonte_url"] = "https://www.fundamentus.com.br"
        except Exception as e:
            error_msg = f"Fundamentus: {str(e)}"
            result["erros"].append(error_msg)
    
    # Coleta dados do brasa-marketdata (fonte secundária)
    if BRASA_AVAILABLE:
        try:
            brasa_data = collect_brasa_data(ticker)
            if brasa_data.get("dados"):
                result["dados"]["brasa"] = brasa_data["dados"]
        except Exception as e:
            error_msg = f"Brasa: {str(e)}"
            result["erros"].append(error_msg)
    
    # Marca como sucesso se pelo menos uma fonte funcionou
    if result["dados"] and not all(len(v) == 0 for v in result["dados"].values()):
        result["sucesso"] = True
    else:
        result["sucesso"] = False
        if not result["erros"]:
            result["erros"].append("Nenhuma fonte de dados retornou informações")
    
    return result


def collect_all_tickers(tickers: list[str]) -> dict[str, Any]:
    """
    Coleta dados de múltiplos tickers com tratamento robusto de erros.
    
    Args:
        tickers: Lista de símbolos de ativos.
        
    Returns:
        Dicionário completo com metadados e dados de todos os tickers.
    """
    inicio_coleta = datetime.now(timezone(timedelta(hours=-3)))
    
    resultado_geral: dict[str, Any] = {
        "metadados": {
            "data_hora_inicio": inicio_coleta.isoformat(),
            "total_tickers_solicitados": len(tickers),
            "tickers_processados": [],
            "tickers_sucesso": [],
            "tickers_falha": [],
            "fontes_utilizadas": []
        },
        "ativos": {}
    }
    
    # Registra fontes disponíveis
    if PYNVEST_AVAILABLE:
        resultado_geral["metadados"]["fontes_utilizadas"].append(
            "pynvest (Fundamentus scraping)"
        )
    if BRASA_AVAILABLE:
        resultado_geral["metadados"]["fontes_utilizadas"].append(
            "brasa-marketdata (B3/CVM)"
        )
    
    # Inicializa coletor do Fundamentus
    fundamentus = Fundamentus() if PYNVEST_AVAILABLE else None
    
    # Processa cada ticker individualmente com try/except
    for ticker in tickers:
        resultado_geral["metadados"]["tickers_processados"].append(ticker)
        
        try:
            dados_ticker = process_single_ticker(ticker, fundamentus)
            resultado_geral["ativos"][ticker] = dados_ticker
            
            if dados_ticker.get("sucesso", False):
                resultado_geral["metadados"]["tickers_sucesso"].append(ticker)
            else:
                resultado_geral["metadados"]["tickers_falha"].append(ticker)
                
        except Exception as e:
            # Captura qualquer erro inesperado para não crashar o script
            resultado_geral["ativos"][ticker] = {
                "ticker": ticker,
                "timestamp_coleta": datetime.now(timezone(timedelta(hours=-3))).isoformat(),
                "dados": {},
                "erros": [f"Erro crítico: {str(e)}"],
                "sucesso": False
            }
            resultado_geral["metadados"]["tickers_falha"].append(ticker)
    
    # Finaliza metadados
    fim_coleta = datetime.now(timezone(timedelta(hours=-3)))
    resultado_geral["metadados"]["data_hora_fim"] = fim_coleta.isoformat()
    resultado_geral["metadados"]["duracao_segundos"] = (fim_coleta - inicio_coleta).total_seconds()
    
    return resultado_geral


def save_to_json(data: dict[str, Any], filename: str = "dados_brutos_carteira.json") -> str:
    """
    Salva os dados coletados em um arquivo JSON formatado.
    
    Args:
        data: Dicionário com os dados coletados.
        filename: Nome do arquivo de saída.
        
    Returns:
        Caminho completo do arquivo salvo.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename


def main() -> None:
    """
    Função principal do script de coleta de dados.
    
    Fluxo:
    1. Solicita lista de tickers ao usuário
    2. Processa e valida entrada
    3. Coleta dados de cada ativo
    4. Exporta resultados para JSON
    """
    print("=" * 70)
    print("COLETOR DE DADOS BRUTOS DE ATIVOS DA B3 (FIIs e Ações)")
    print("=" * 70)
    print()
    
    # Exibe fontes disponíveis
    print("Fontes de dados disponíveis:")
    if PYNVEST_AVAILABLE:
        print("  ✓ pynvest (Fundamentus scraping)")
    else:
        print("  ✗ pynvest (indisponível)")
    
    if BRASA_AVAILABLE:
        print("  ✓ brasa-marketdata (B3/CVM)")
    else:
        print("  ✗ brasa-marketdata (indisponível)")
    
    print()
    print("-" * 70)
    
    # Solicita entrada do usuário
    input_text = input("\nDigite os tickers separados por vírgula (ex: PETR4, HGLG11): ")
    
    # Processa entrada
    tickers = parse_tickers_input(input_text)
    
    if not tickers:
        print("\nErro: Nenhum ticker válido fornecido.")
        sys.exit(1)
    
    print(f"\nProcessando {len(tickers)} ticker(s): {', '.join(tickers)}")
    print("-" * 70)
    
    # Coleta dados
    try:
        dados_completos = collect_all_tickers(tickers)
    except Exception as e:
        print(f"\nErro crítico durante coleta: {str(e)}")
        sys.exit(1)
    
    # Salva resultados
    try:
        arquivo_saida = save_to_json(dados_completos)
        print(f"\n✓ Dados salvos em: {arquivo_saida}")
    except Exception as e:
        print(f"\nErro ao salvar arquivo JSON: {str(e)}")
        sys.exit(1)
    
    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO DA COLETA")
    print("=" * 70)
    print(f"Total solicitados: {dados_completos['metadados']['total_tickers_solicitados']}")
    print(f"Sucesso: {len(dados_completos['metadados']['tickers_sucesso'])}")
    print(f"Falha: {len(dados_completos['metadados']['tickers_falha'])}")
    print(f"Duração: {dados_completos['metadados']['duracao_segundos']:.2f} segundos")
    
    if dados_completos['metadados']['tickers_falha']:
        print(f"\nTickers com falha: {', '.join(dados_completos['metadados']['tickers_falha'])}")
    
    print("\n" + "=" * 70)
    print("Processo concluído!")
    print("=" * 70)


if __name__ == "__main__":
    main()
