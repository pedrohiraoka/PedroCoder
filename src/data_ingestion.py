"""
Módulo de ingestão de dados para o Motor de Hipótese Gerativa.

Suporta leitura de:
- Arquivos CSV locais
- Arquivos JSON locais
- APIs públicas (ex: IBGE, Câmara dos Deputados)
"""

import json
from typing import Optional, Union
import pandas as pd
import requests


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Carrega um arquivo CSV em um DataFrame pandas.

    Args:
        file_path: Caminho para o arquivo CSV.

    Returns:
        DataFrame com os dados carregados.

    Raises:
        FileNotFoundError: Se o arquivo não for encontrado.
        pd.errors.EmptyDataError: Se o arquivo estiver vazio.
    """
    return pd.read_csv(file_path)


def load_json(file_path: str) -> pd.DataFrame:
    """
    Carrega um arquivo JSON em um DataFrame pandas.

    Args:
        file_path: Caminho para o arquivo JSON.

    Returns:
        DataFrame com os dados carregados.

    Raises:
        FileNotFoundError: Se o arquivo não for encontrado.
        ValueError: Se o JSON não puder ser convertido em DataFrame.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        return pd.DataFrame.from_dict(data, orient='index')
    else:
        raise ValueError("Formato JSON não suportado para conversão em DataFrame")


def fetch_from_api(url: str, params: Optional[dict] = None, 
                   headers: Optional[dict] = None) -> pd.DataFrame:
    """
    Busca dados de uma API pública e retorna como DataFrame.

    Args:
        url: URL da API.
        params: Parâmetros opcionais para a requisição.
        headers: Headers opcionais para a requisição.

    Returns:
        DataFrame com os dados retornados pela API.

    Raises:
        requests.RequestException: Se houver erro na requisição HTTP.
        ValueError: Se a resposta não puder ser convertida em DataFrame.
    """
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Resposta da API não é um JSON válido: {e}")
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        # Tenta encontrar uma chave que contenha os dados principais
        for key in ['data', 'results', 'dados', 'registros']:
            if key in data and isinstance(data[key], list):
                return pd.DataFrame(data[key])
        return pd.DataFrame.from_dict(data, orient='index')
    else:
        raise ValueError("Formato de resposta da API não suportado")


def fetch_ibge_indicadores(indicador: str = "72", periodo: str = "2020") -> pd.DataFrame:
    """
    Busca indicadores do IBGE via API.
    
    Args:
        indicador: Código do indicador (ex: 72 = Taxa de desocupação).
        periodo: Período da consulta (ex: "2020", "2019|2020").
    
    Returns:
        DataFrame com os dados do IBGE.
    
    Example:
        >>> df = fetch_ibge_indicadores("72", "2020")
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/indicadores/{indicador}/periodos/{periodo}"
    params = {
        'localidades': 'br',
        'classificacoes': 'sexo'
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # Processa a estrutura complexa do IBGE
    flattened_data = []
    for item in data:
        if 'series' in item:
            for serie in item['series']:
                for ponto in serie.get('series', []):
                    flattened_data.append({
                        'indicador': item.get('nome', ''),
                        'periodo': ponto.get('periodo', ''),
                        'valor': ponto.get('valor', '')
                    })
    
    return pd.DataFrame(flattened_data)


def fetch_camara_deputados(deputados_limit: int = 50) -> pd.DataFrame:
    """
    Busca dados de deputados da Câmara dos Deputados via API.
    
    Args:
        deputados_limit: Número máximo de deputados para retornar.
    
    Returns:
        DataFrame com dados dos deputados.
    
    Example:
        >>> df = fetch_camara_deputados(50)
    """
    url = "https://www.camara.leg.br/api-deputados/Deputados"
    params = {'itens': deputados_limit}
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    deputies_data = []
    for deputy in data.get('dados', []):
        deputies_data.append({
            'id': deputy.get('id'),
            'nome': deputy.get('nome'),
            'sigla_partido': deputy.get('siglaPartido'),
            'sigla_uf': deputy.get('siglaUF'),
            'genero': deputy.get('sexo'),
            'data_falecimento': deputy.get('dataFalecimento'),
            'email': deputy.get('email')
        })
    
    return pd.DataFrame(deputies_data)


def load_data(source: str, source_type: str = 'auto', **kwargs) -> pd.DataFrame:
    """
    Função genérica para carregar dados de várias fontes.
    
    Args:
        source: Caminho do arquivo ou URL.
        source_type: Tipo de fonte ('csv', 'json', 'api', 'auto').
        **kwargs: Argumentos adicionais para funções específicas.
    
    Returns:
        DataFrame com os dados carregados.
    
    Example:
        >>> df = load_data('dados.csv')
        >>> df = load_data('https://api.exemplo.com/dados', source_type='api')
    """
    if source_type == 'auto':
        if source.startswith('http'):
            source_type = 'api'
        elif source.endswith('.csv'):
            source_type = 'csv'
        elif source.endswith('.json'):
            source_type = 'json'
        else:
            raise ValueError("Não foi possível determinar o tipo de fonte automaticamente")
    
    if source_type == 'csv':
        return load_csv(source)
    elif source_type == 'json':
        return load_json(source)
    elif source_type == 'api':
        return fetch_from_api(source, **kwargs)
    else:
        raise ValueError(f"Tipo de fonte não suportado: {source_type}")
