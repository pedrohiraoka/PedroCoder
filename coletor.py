"""
coletor.py
Módulo responsável por coletar dados brutos de ativos da B3
utilizando as bibliotecas brasa-marketdata e pynvest.
"""

import pandas as pd
from datetime import datetime
import logging
import re

try:
    import brasa
except ImportError:
    logging.error("brasa-marketdata não encontrado. Instale com: pip install brasa-marketdata")
    raise

try:
    from pynvest.scrappers.fundamentus import Fundamentus
    PYNVEST_AVAILABLE = True
except ImportError:
    PYNVEST_AVAILABLE = False
    logging.warning("pynvest não encontrado. Dados fundamentalistas não serão coletados.")


def validar_formato_ticker(ticker: str) -> bool:
    """
    Valida o formato do ticker (4 letras + 1 número ou 5 letras).
    
    Args:
        ticker (str): Ticker a ser validado.
    
    Returns:
        bool: True se formato válido, False caso contrário.
    """
    return bool(re.match(r'^[A-Z]{4}\d{1}$|^[A-Z]{5}$', ticker))


def validar_ticker(ticker: str) -> bool:
    """
    Valida se o ticker existe na base de dados da B3 via brasa.
    
    Args:
        ticker (str): Ticker do ativo.
    
    Returns:
        bool: True se existir, False caso contrário.
    """
    if not validar_formato_ticker(ticker):
        return False
    
    try:
        # Tenta baixar um período mínimo para verificar existência
        df = brasa.download(
            template='b3-cotahist-daily', 
            codes=ticker, 
            start='2023-01-02', 
            end='2023-01-03'
        )
        return not df.empty
    except Exception:
        return False


def coletar_dados_cadastrais(ticker: str) -> dict:
    """
    Coleta dados cadastrais do ativo diretamente da B3 via brasa.
    
    Origem dos dados: B3 (Cadastro Oficial de Negociação)
    
    Args:
        ticker (str): Ticker do ativo.
    
    Returns:
        dict: Dados cadastrais ou dicionário vazio em caso de erro.
    """
    try:
        # Obtém o dataframe de cotações que contém informações cadastrais
        df = brasa.download(template='b3-cotahist-daily', codes=ticker)
        
        if df.empty:
            logging.warning(f"Nenhum dado encontrado para {ticker}")
            return {}
        
        # Extrai informações únicas do cadastro
        # As colunas podem variar conforme versão do brasa
        dados = {}
        
        # Tenta extrair campos comuns de cadastro
        colunas_mapeamento = {
            'codneg': 'codigo_negociacao',
            'nomempres': 'nome_empresa',
            'especificacao': 'especificacao_papel',
            'prazo': 'prazo_dias',
            'moeda': 'moeda_referencia'
        }
        
        for col_origem, col_destino in colunas_mapeamento.items():
            if col_origem in df.columns:
                valor = df[col_origem].iloc[-1]
                if pd.notna(valor):
                    dados[col_destino] = str(valor)
        
        # Adiciona metadata básica
        dados['ticker'] = ticker
        dados['data_primeira_negociacao'] = str(df['data'].min()) if 'data' in df.columns else None
        dados['data_ultima_negociacao'] = str(df['data'].max()) if 'data' in df.columns else None
        
        return dados
    except Exception as e:
        logging.error(f"Erro ao coletar dados cadastrais de {ticker}: {e}")
        return {}


def coletar_historico_precos(ticker: str, start_date: str = None, end_date: str = None) -> list:
    """
    Coleta histórico de preços diários do ativo via brasa-marketdata.
    
    Origem dos dados: B3 (Sistema de Negociação - COTAHIST)
    
    Campos retornados (quando disponíveis):
    - data: Data do pregão
    - codigo_negociacao: Ticker do ativo
    - abertura: Preço de abertura
    - maxima: Preço máximo
    - minima: Preço mínimo
    - fechamento: Preço de fechamento
    - volume: Volume financeiro negociado
    
    Args:
        ticker (str): Ticker do ativo.
        start_date (str, optional): Data inicial YYYY-MM-DD.
        end_date (str, optional): Data final YYYY-MM-DD.
    
    Returns:
        list: Lista de dicionários com dados históricos diários.
    """
    try:
        df = brasa.download(
            template='b3-cotahist-daily', 
            codes=ticker, 
            start=start_date, 
            end=end_date
        )
        
        if df.empty:
            logging.warning(f"Nenhum dado histórico encontrado para {ticker}")
            return []
        
        # Converte DataFrame para lista de dicionários
        historico = []
        for _, row in df.iterrows():
            registro = {}
            for col in df.columns:
                valor = row[col]
                
                # Trata valores nulos
                if pd.isna(valor):
                    registro[col] = None
                # Trata datas
                elif isinstance(valor, (pd.Timestamp, datetime)):
                    registro[col] = valor.strftime('%Y-%m-%d')
                # Trata tipos numéricos
                elif isinstance(valor, (int, float)):
                    registro[col] = float(valor) if not pd.isna(valor) else None
                else:
                    registro[col] = str(valor)
            
            historico.append(registro)
        
        return historico
    except Exception as e:
        logging.error(f"Erro ao coletar histórico de preços de {ticker}: {e}")
        return []


def coletar_indicadores_fundamentalistas(ticker: str) -> dict:
    """
    Coleta indicadores fundamentalistas via pynvest (Fonte: Fundamentus).
    
    Origem dos dados: Fundamentus.com.br (via scraping pynvest)
    
    Indicadores coletados (quando disponíveis):
    - p_l: Preço/Lucro
    - p_vp: Preço/Valor Patrimonial
    - psr: Price/Sales Ratio
    - dy: Dividend Yield
    - p_ativo: Preço/Ativo Total
    - p_cap_giro: Preço/Capital de Giro
    - p_ebit: Preço/EBIT
    - p_ativo_circ_liq: Preço/Ativo Circulante Líquido
    - ev_ebit: Enterprise Value/EBIT
    - margem_bruta: Margem Bruta
    - margem_ebit: Margem EBIT
    - margem_liquida: Margem Líquida
    - liq_corrente: Liquidez Corrente
    - roe: Return on Equity
    - roa: Return on Assets
    - div_bruta_patrimonio: Dívida Bruta/Patrimônio
    - crescimento_receita_5anos: Crescimento de Receita (5 anos)
    
    Args:
        ticker (str): Ticker do ativo.
    
    Returns:
        dict: Indicadores fundamentalistas ou dicionário vazio em caso de erro.
    """
    if not PYNVEST_AVAILABLE:
        logging.warning(f"pynvest indisponível. Indicadores de {ticker} não coletados.")
        return {"status": "indisponivel", "motivo": "pynvest não instalado"}
    
    try:
        # Instancia o coletor do Fundamentus
        fund = Fundamentus()
        
        # Coleta dados como DataFrame
        df = fund.coleta_indicadores_de_ativo(ticker)
        
        if df.empty:
            logging.warning(f"Nenhum indicador encontrado para {ticker} no Fundamentus")
            return {"status": "nao_encontrado", "ticker": ticker}
        
        # Converte primeira linha para dict
        row = df.iloc[0].to_dict()
        
        # Mapeamento de colunas do pynvest para nomes descritivos em português
        indicadores_map = {
            'vlr_ind_p_sobre_l': 'preco_lucro',
            'vlr_ind_p_sobre_vp': 'preco_valor_patrimonial',
            'vlr_ind_psr': 'preco_vendas',
            'vlr_ind_div_yield': 'dividend_yield',
            'vlr_ind_p_sobre_ativ': 'preco_ativo_total',
            'vlr_ind_p_sobre_cap_giro': 'preco_capital_giro',
            'vlr_ind_p_sobre_ebit': 'preco_ebit',
            'vlr_ind_p_sobre_ativ_circ_liq': 'preco_ativo_circulante_liquido',
            'vlr_ind_ev_sobre_ebitda': 'enterprise_value_ebitda',
            'vlr_ind_ev_sobre_ebit': 'enterprise_value_ebit',
            'marg_bruta': 'margem_bruta',
            'marg_ebit': 'margem_ebit',
            'marg_liq': 'margem_liquida',
            'liq_corr': 'liquidez_corrente',
            'roe': 'retorno_patrimonio',
            'roa': 'retorno_ativos',
            'div_brut_patrim': 'divida_bruta_patrimonio',
            'cres_rec_5a': 'crescimento_receita_5_anos'
        }
        
        indicadores = {}
        indicadores['ticker'] = ticker
        indicadores['data_coleta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        indicadores['fonte'] = 'Fundamentus via pynvest'
        
        for col_pynvest, nome_descritivo in indicadores_map.items():
            try:
                if col_pynvest in row:
                    valor = row[col_pynvest]
                    if pd.notna(valor):
                        # Remove % se presente e converte para float
                        if isinstance(valor, str):
                            valor = valor.replace('%', '').replace(',', '.')
                        try:
                            valor_float = float(valor)
                            # Se for percentual (dividend yield), divide por 100
                            if 'yield' in nome_descritivo or 'margem' in nome_descritivo:
                                if valor_float > 1:
                                    valor_float = valor_float / 100
                            indicadores[nome_descritivo] = round(valor_float, 4)
                        except (ValueError, TypeError):
                            indicadores[nome_descritivo] = str(valor)
                    else:
                        indicadores[nome_descritivo] = None
                else:
                    indicadores[nome_descritivo] = None
            except Exception:
                indicadores[nome_descritivo] = None
        
        return indicadores
    except Exception as e:
        logging.error(f"Erro ao coletar indicadores de {ticker} via pynvest: {e}")
        return {"status": "erro", "mensagem": str(e)}


def coletar_proventos_historicos(ticker: str) -> list:
    """
    Coleta histórico de proventos (dividendos, JCP, bonificações) via brasa.
    
    Origem dos dados: B3 (Eventos Corporativos)
    
    Tipos de proventos:
    - DIVIDENDO: Distribuição de lucros
    - JUROS_CAPITAL_PROPRIO: JCP
    - BONIFICACAO: Bonificação em ações
    - SUBSCRICAO: Direito de subscrição
    
    Args:
        ticker (str): Ticker do ativo.
    
    Returns:
        list: Lista de dicionários com eventos de proventos.
    """
    try:
        # Tenta usar template de eventos corporativos
        # O nome do template pode variar conforme versão do brasa
        templates_possiveis = ['b3-stock-events', 'b3-corporate-events', 'b3-dividends']
        
        for template in templates_possiveis:
            try:
                df = brasa.download(template=template, codes=ticker)
                if not df.empty:
                    proventos = []
                    for _, row in df.iterrows():
                        evento = {}
                        for col in df.columns:
                            valor = row[col]
                            if pd.isna(valor):
                                evento[col] = None
                            elif isinstance(valor, (pd.Timestamp, datetime)):
                                evento[col] = valor.strftime('%Y-%m-%d')
                            elif isinstance(valor, (int, float)):
                                evento[col] = float(valor) if not pd.isna(valor) else None
                            else:
                                evento[col] = str(valor)
                        proventos.append(evento)
                    return proventos
            except Exception:
                continue
        
        # Se nenhum template funcionar, retorna lista vazia
        logging.info(f"Nenhum provento encontrado ou template indisponível para {ticker}")
        return []
    except Exception as e:
        logging.error(f"Erro ao coletar proventos de {ticker}: {e}")
        return []


def coletar_todos_dados_ativo(ticker: str) -> dict:
    """
    Coleta todos os dados disponíveis para um único ativo.
    
    Args:
        ticker (str): Ticker do ativo.
    
    Returns:
        dict: Dicionário com todas as categorias de dados do ativo.
    """
    logging.info(f"Coletando dados para {ticker}...")
    
    dados_ativo = {
        'dados_cadastrais': {},
        'historico_cotacoes': [],
        'indicadores_fundamentalistas': {},
        'proventos_historicos': []
    }
    
    # Coleta dados cadastrais
    dados_ativo['dados_cadastrais'] = coletar_dados_cadastrais(ticker)
    
    # Coleta histórico de preços
    dados_ativo['historico_cotacoes'] = coletar_historico_precos(ticker)
    
    # Coleta indicadores fundamentalistas
    dados_ativo['indicadores_fundamentalistas'] = coletar_indicadores_fundamentalistas(ticker)
    
    # Coleta proventos
    dados_ativo['proventos_historicos'] = coletar_proventos_historicos(ticker)
    
    return dados_ativo
