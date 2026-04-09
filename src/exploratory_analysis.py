"""
Módulo de Análise Exploratória Inicial (AEI) para o Motor de Hipótese Gerativa.

Realiza análise básica da estrutura dos dados, identifica correlações,
detecta agrupamentos e prepara informações para geração de hipóteses.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats


def get_data_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analisa a estrutura básica dos dados.

    Args:
        df: DataFrame para análise.

    Returns:
        Dicionário com informações sobre estrutura dos dados.
    """
    structure = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 ** 2)
    }
    return structure


def get_descriptive_statistics(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Calcula estatísticas descritivas para colunas numéricas e categóricas.

    Args:
        df: DataFrame para análise.

    Returns:
        Dicionário com estatísticas descritivas separadas por tipo.
    """
    numeric_stats = df.describe(include=[np.number])
    categorical_stats = df.describe(include=['object', 'category', 'bool'])
    
    return {
        'numeric': numeric_stats,
        'categorical': categorical_stats
    }


def identify_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classifica colunas por tipo de dado e uso potencial.

    Args:
        df: DataFrame para análise.

    Returns:
        Dicionário com listas de colunas classificadas.
    """
    column_types = {
        'numeric_continuous': [],
        'numeric_discrete': [],
        'categorical_nominal': [],
        'categorical_ordinal': [],
        'datetime': [],
        'text': [],
        'identifier': []
    }
    
    for col in df.columns:
        dtype = df[col].dtype
        
        if np.issubdtype(dtype, np.datetime64):
            column_types['datetime'].append(col)
        elif np.issubdtype(dtype, np.number):
            unique_values = df[col].nunique()
            total_values = len(df)
            
            # Heurística: se tem poucos valores únicos, é discreto
            if unique_values < 10 or unique_values < total_values * 0.05:
                column_types['numeric_discrete'].append(col)
            else:
                column_types['numeric_continuous'].append(col)
        elif dtype == 'object' or str(dtype) == 'category':
            unique_ratio = df[col].nunique() / len(df)
            
            # Heurística: se tem muitos valores únicos, pode ser texto ou identificador
            if unique_ratio > 0.9:
                column_types['identifier'].append(col)
            elif unique_ratio < 0.1:
                column_types['categorical_nominal'].append(col)
            else:
                column_types['text'].append(col)
    
    return column_types


def calculate_correlations(df: pd.DataFrame, 
                          method: str = 'pearson') -> pd.DataFrame:
    """
    Calcula matriz de correlação para variáveis numéricas.

    Args:
        df: DataFrame para análise.
        method: Método de correlação ('pearson', 'spearman', 'kendall').

    Returns:
        Matriz de correlação como DataFrame.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return pd.DataFrame()
    
    return numeric_df.corr(method=method)


def find_strong_correlations(df: pd.DataFrame, 
                            threshold: float = 0.6) -> List[Tuple[str, str, float]]:
    """
    Identifica pares de variáveis com correlação forte.

    Args:
        df: DataFrame para análise.
        threshold: Limiar mínimo para considerar correlação forte.

    Returns:
        Lista de tuplas (var1, var2, correlação) ordenadas por magnitude.
    """
    corr_matrix = calculate_correlations(df)
    
    if corr_matrix.empty:
        return []
    
    strong_corrs = []
    columns = corr_matrix.columns
    
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            var1 = columns[i]
            var2 = columns[j]
            corr_value = corr_matrix.loc[var1, var2]
            
            if abs(corr_value) >= threshold:
                strong_corrs.append((var1, var2, corr_value))
    
    # Ordena por magnitude da correlação
    strong_corrs.sort(key=lambda x: abs(x[2]), reverse=True)
    
    return strong_corrs


def analyze_categorical_relationships(df: pd.DataFrame, 
                                     target_col: str = None) -> Dict[str, Any]:
    """
    Analisa relações entre variáveis categóricas e outras variáveis.

    Args:
        df: DataFrame para análise.
        target_col: Coluna alvo opcional para focar a análise.

    Returns:
        Dicionário com análises de relações categóricas.
    """
    column_types = identify_column_types(df)
    results = {}
    
    categorical_cols = column_types['categorical_nominal']
    
    if target_col and target_col in categorical_cols:
        categorical_cols = [target_col]
    
    for cat_col in categorical_cols:
        if cat_col not in df.columns:
            continue
            
        results[cat_col] = {
            'unique_values': df[cat_col].nunique(),
            'value_counts': df[cat_col].value_counts().head(10).to_dict(),
            'relationships_with_numeric': {}
        }
        
        # Analisa relação com variáveis numéricas
        for num_col in column_types['numeric_continuous'][:5]:  # Limita a 5
            if num_col not in df.columns:
                continue
            
            group_stats = df.groupby(cat_col)[num_col].agg(['mean', 'std', 'count'])
            results[cat_col]['relationships_with_numeric'][num_col] = group_stats.to_dict()
    
    return results


def detect_outliers(df: pd.DataFrame, 
                   method: str = 'iqr', 
                   threshold: float = 1.5) -> Dict[str, List[int]]:
    """
    Detecta outliers em variáveis numéricas.

    Args:
        df: DataFrame para análise.
        method: Método de detecção ('iqr', 'zscore').
        threshold: Limiar para detecção.

    Returns:
        Dicionário com índices de outliers por coluna.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    outliers = {}
    
    for col in numeric_df.columns:
        if method == 'iqr':
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outlier_mask = (numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(numeric_df[col].dropna()))
            outlier_mask = z_scores > threshold
            # Mapeia de volta para índices originais
            valid_indices = numeric_df[col].dropna().index
            outlier_indices = valid_indices[z_scores > threshold]
            outliers[col] = outlier_indices.tolist()
            continue
        else:
            raise ValueError(f"Método não suportado: {method}")
        
        outliers[col] = numeric_df[outlier_mask].index.tolist()
    
    return outliers


def perform_exploratory_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Realiza uma análise exploratória completa nos dados.

    Args:
        df: DataFrame para análise.

    Returns:
        Dicionário com todos os resultados da análise exploratória.
    """
    results = {
        'structure': get_data_structure(df),
        'descriptive_stats': get_descriptive_statistics(df),
        'column_types': identify_column_types(df),
        'correlations': {
            'matrix': calculate_correlations(df),
            'strong_pairs': find_strong_correlations(df)
        },
        'categorical_analysis': analyze_categorical_relationships(df),
        'outliers': detect_outliers(df)
    }
    
    return results
