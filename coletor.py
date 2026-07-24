"""
Coletor de Dados Fundamentalistas - Fundamentus

Script utilitário robusto para coletar dados fundamentais brutos de ativos
da bolsa brasileira (B3) do site https://www.fundamentus.com.br

Autor: Engenheiro de Dados Sênior
Data: 2026
"""

import json
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pynvest.scrappers.fundamentus import Fundamentus

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constantes de configuração
DELAY_BETWEEN_REQUESTS = 1.5  # segundos entre requisições para evitar rate limiting
OUTPUT_FILENAME = "dados_fundamentus_brutos.json"


def parse_tickers_input(input_text: str) -> List[str]:
    """
    Processa a entrada de texto do usuário e extrai tickers válidos.
    
    Args:
        input_text: Texto bruto inserido pelo usuário
        
    Returns:
        Lista de tickers padronizados em maiúsculas
    """
    if not input_text.strip():
        return []
    
    # Divide por vírgula e remove espaços em branco
    raw_tickers = [t.strip() for t in input_text.split(',')]
    
    # Filtra tickers vazios e padroniza para maiúsculas
    tickers = []
    for ticker in raw_tickers:
        # Remove caracteres inválidos (mantém apenas letras e números)
        cleaned = re.sub(r'[^A-Za-z0-9]', '', ticker)
        if cleaned:
            tickers.append(cleaned.upper())
    
    # Remove duplicatas mantendo a ordem
    seen = set()
    unique_tickers = []
    for ticker in tickers:
        if ticker not in seen:
            seen.add(ticker)
            unique_tickers.append(ticker)
    
    return unique_tickers


def extract_fundamental_data(ticker: str, fundamentus: Fundamentus) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Extrai dados fundamentalistas de um único ticker usando pynvest.
    
    Args:
        ticker: Ticker do ativo (ex: PETR4, HGLG11)
        fundamentus: Instância da classe Fundamentus
        
    Returns:
        Tupla contendo:
        - Dicionário com dados fundamentalistas ou None em caso de erro
        - Mensagem de erro ou None se sucesso
    """
    try:
        # Coleta dados do Fundamentus via pynvest
        df = fundamentus.coleta_indicadores_de_ativo(ticker, parse_dtypes=True)
        
        if df.empty:
            return None, "Dados vazios retornados pelo Fundamentus"
        
        # Converte DataFrame para dicionário
        data = df.iloc[0].to_dict()
        
        # Determina se é Ação ou FII e extrai metadados apropriados
        is_fii = 'fii' in data or 'nome_fii' in data
        
        # Extrai nome da empresa/FII
        if is_fii:
            nome_empresa = data.get('nome_fii', f"FII {ticker}")
            setor = data.get('segmento', 'Fundos Imobiliários')
            tipo_ativo = 'FII'
        else:
            nome_empresa = data.get('nome_empresa', f"Ação {ticker}")
            setor = data.get('nome_setor', 'Não informado')
            tipo_ativo = 'Ação'
        
        # Mapeia dados fundamentalistas para formato padronizado
        dados_fundamentalistas = {}
        
        # Cotação atual
        cotacao = data.get('vlr_cot')
        dados_fundamentalistas['cotacao'] = float(cotacao) if pd.notna(cotacao) else None
        
        # P/L (Preço sobre Lucro)
        pl = data.get('vlr_ind_p_sobre_l')
        dados_fundamentalistas['pl'] = float(pl) if pd.notna(pl) else None
        
        # P/VP (Preço sobre Valor Patrimonial)
        pvp = data.get('vlr_ind_p_sobre_vp') if not is_fii else data.get('vlr_p_sobre_vp')
        dados_fundamentalistas['pvp'] = float(pvp) if pd.notna(pvp) else None
        
        # PSR (Preço sobre Receita Líquida)
        psr = data.get('vlr_ind_psr')
        dados_fundamentalistas['psr'] = float(psr) if pd.notna(psr) else None
        
        # Dividend Yield
        dy = data.get('vlr_ind_div_yield') if not is_fii else data.get('vlr_div_yield')
        dados_fundamentalistas['dividend_yield'] = float(dy) if pd.notna(dy) else None
        
        # P/Ativo
        p_ativo = data.get('vlr_ind_p_sobre_ativ')
        dados_fundamentalistas['p_ativo'] = float(p_ativo) if pd.notna(p_ativo) else None
        
        # P/Capital de Giro
        p_cap_giro = data.get('vlr_ind_p_sobre_cap_giro')
        dados_fundamentalistas['p_cap_giro'] = float(p_cap_giro) if pd.notna(p_cap_giro) else None
        
        # P/EBIT
        p_ebit = data.get('vlr_ind_p_sobre_ebit')
        dados_fundamentalistas['p_ebit'] = float(p_ebit) if pd.notna(p_ebit) else None
        
        # P/Ativo Circulante Líquido
        p_acl = data.get('vlr_ind_p_sobre_ativ_circ_liq')
        dados_fundamentalistas['p_ativo_circ_liq'] = float(p_acl) if pd.notna(p_acl) else None
        
        # EV/EBIT
        ev_ebit = data.get('vlr_ind_ev_sobre_ebit')
        dados_fundamentalistas['ev_ebit'] = float(ev_ebit) if pd.notna(ev_ebit) else None
        
        # EV/EBITDA
        ev_ebitda = data.get('vlr_ind_ev_sobre_ebitda')
        dados_fundamentalistas['ev_ebitda'] = float(ev_ebitda) if pd.notna(ev_ebitda) else None
        
        # Margem EBIT
        margem_ebit = data.get('vlr_ind_margem_ebit')
        dados_fundamentalistas['margem_ebit'] = float(margem_ebit) if pd.notna(margem_ebit) else None
        
        # Margem Líquida
        margem_liquida = data.get('vlr_ind_margem_liq')
        dados_fundamentalistas['margem_liquida'] = float(margem_liquida) if pd.notna(margem_liquida) else None
        
        # Liquidez Corrente
        liq_corrente = data.get('vlr_liquidez_corr')
        dados_fundamentalistas['liquidez_corrente'] = float(liq_corrente) if pd.notna(liq_corrente) else None
        
        # ROE (Return on Equity)
        roe = data.get('vlr_ind_roe')
        dados_fundamentalistas['roe'] = float(roe) if pd.notna(roe) else None
        
        # ROA (Return on Assets)
        roa = data.get('vlr_ind_ebit_sobre_ativo')
        dados_fundamentalistas['roa'] = float(roa) if pd.notna(roa) else None
        
        # Dívida Líquida / EBITDA (calculado manualmente se necessário)
        div_liquida = data.get('vlr_divida_liq')
        ebitda = data.get('vlr_ebit_ult_12m')  # Aproximação
        if pd.notna(div_liquida) and pd.notna(ebitda) and ebitda != 0:
            dados_fundamentalistas['divida_liquida_ebitda'] = float(div_liquida) / float(ebitda)
        else:
            dados_fundamentalistas['divida_liquida_ebitda'] = None
        
        # Dívida Líquida / PL
        patrim_liq = data.get('vlr_patrim_liq')
        if pd.notna(div_liquida) and pd.notna(patrim_liq) and patrim_liq != 0:
            dados_fundamentalistas['divida_liquida_pl'] = float(div_liquida) / float(patrim_liq)
        else:
            dados_fundamentalistas['divida_liquida_pl'] = None
        
        # Monta estrutura de dados do ativo
        ativo_data = {
            'nome_empresa': nome_empresa,
            'setor': setor,
            'tipo_ativo': tipo_ativo,
            'dados_fundamentalistas': dados_fundamentalistas,
            'status': 'sucesso'
        }
        
        return ativo_data, None
        
    except TypeError as e:
        # Erro específico quando ticker não é encontrado
        error_msg = str(e)
        if "Não foram encontradas informações financeiras" in error_msg:
            return None, "Ticker não encontrado no Fundamentus"
        return None, f"Erro de processamento: {error_msg}"
        
    except Exception as e:
        logger.error(f"Erro ao processar ticker {ticker}: {str(e)}")
        return None, f"Falha na conexão ou processamento: {str(e)}"


def collect_all_tickers(tickers: List[str]) -> Dict[str, Any]:
    """
    Coleta dados fundamentalistas para todos os tickers fornecidos.
    
    Args:
        tickers: Lista de tickers para processar
        
    Returns:
        Dicionário com estrutura completa de dados para exportação JSON
    """
    # Inicializa instância do Fundamentus
    fundamentus = Fundamentus()
    
    # Estruturas de resultado
    ativos = {}
    tickers_sucesso = []
    tickers_erro = []
    
    logger.info(f"Iniciando coleta de {len(tickers)} ticker(s)...")
    
    for i, ticker in enumerate(tickers, 1):
        logger.info(f"[{i}/{len(tickers)}] Processando {ticker}...")
        
        dados, erro = extract_fundamental_data(ticker, fundamentus)
        
        if dados:
            ativos[ticker] = dados
            tickers_sucesso.append(ticker)
            logger.info(f"  ✓ {ticker} processado com sucesso")
        else:
            ativos[ticker] = {
                'status': 'erro',
                'mensagem': erro
            }
            tickers_erro.append(ticker)
            logger.warning(f"  ✗ {ticker}: {erro}")
        
        # Delay entre requisições para evitar rate limiting
        if i < len(tickers):
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Monta estrutura final do JSON
    resultado = {
        'metadata': {
            'gerado_em': datetime.now(timezone(timedelta(hours=-3))).isoformat(),
            'fonte_dados': 'Fundamentus (via pynvest)',
            'tickers_solicitados': tickers,
            'tickers_processados_com_sucesso': tickers_sucesso,
            'tickers_com_erro': tickers_erro,
            'total_tickers': len(tickers),
            'sucessos': len(tickers_sucesso),
            'erros': len(tickers_erro)
        },
        'ativos': ativos
    }
    
    return resultado


def save_to_json(data: Dict[str, Any], filename: str = OUTPUT_FILENAME) -> str:
    """
    Salva os dados coletados em arquivo JSON.
    
    Args:
        data: Dicionário com dados estruturados
        filename: Nome do arquivo de saída
        
    Returns:
        Caminho completo do arquivo salvo
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Dados salvos em: {filename}")
    return filename


def main():
    """Função principal da aplicação CLI."""
    print("=" * 70)
    print("COLETOR DE DADOS FUNDAMENTALISTAS - FUNDAMENTUS")
    print("=" * 70)
    print()
    
    # Solicita input do usuário
    user_input = input("Digite os tickers separados por vírgula (ex: PETR4, VALE3, HGLG11): ")
    print()
    
    # Processa entrada
    tickers = parse_tickers_input(user_input)
    
    if not tickers:
        logger.error("Nenhum ticker válido fornecido.")
        print("Erro: Por favor, insira pelo menos um ticker válido.")
        return
    
    print(f"Tickers identificados: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} ativo(s)")
    print()
    
    # Coleta dados
    resultado = collect_all_tickers(tickers)
    
    # Salva em JSON
    save_to_json(resultado)
    
    # Resumo final
    print()
    print("=" * 70)
    print("RESUMO DA COLETA")
    print("=" * 70)
    print(f"Tickers solicitados: {resultado['metadata']['total_tickers']}")
    print(f"Sucessos: {resultado['metadata']['sucessos']}")
    print(f"Erros: {resultado['metadata']['erros']}")
    print(f"Arquivo gerado: {OUTPUT_FILENAME}")
    print("=" * 70)


if __name__ == "__main__":
    main()
