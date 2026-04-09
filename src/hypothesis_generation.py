"""
Módulo de Geração de Hipóteses para o Motor de Hipótese Gerativa.

Gera automaticamente hipóteses plausíveis baseadas em padrões identificados
nos dados durante a análise exploratória.
"""

from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np


class Hypothesis:
    """Classe que representa uma hipótese testável."""
    
    def __init__(self, 
                 hypothesis_text: str,
                 var1: str,
                 var2: str = None,
                 relationship_type: str = "correlation",
                 strength: float = None,
                 evidence: str = None):
        """
        Inicializa uma hipótese.

        Args:
            hypothesis_text: Descrição da hipótese em linguagem natural.
            var1: Primeira variável envolvida.
            var2: Segunda variável envolvida (opcional).
            relationship_type: Tipo de relação ('correlation', 'difference', 'association').
            strength: Medida da força da relação observada.
            evidence: Evidência que motivou a geração da hipótese.
        """
        self.hypothesis_text = hypothesis_text
        self.var1 = var1
        self.var2 = var2
        self.relationship_type = relationship_type
        self.strength = strength
        self.evidence = evidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a hipótese para um dicionário."""
        return {
            'hypothesis': self.hypothesis_text,
            'variable_1': self.var1,
            'variable_2': self.var2,
            'relationship_type': self.relationship_type,
            'observed_strength': self.strength,
            'evidence': self.evidence
        }
    
    def __repr__(self) -> str:
        return f"Hypothesis('{self.hypothesis_text}')"


def generate_correlation_hypotheses(df: pd.DataFrame,
                                   corr_pairs: List[Tuple[str, str, float]],
                                   min_threshold: float = 0.4) -> List[Hypothesis]:
    """
    Gera hipóteses baseadas em correlações entre variáveis numéricas.

    Args:
        df: DataFrame com os dados.
        corr_pairs: Lista de tuplas (var1, var2, correlação).
        min_threshold: Limiar mínimo de correlação para gerar hipótese.

    Returns:
        Lista de objetos Hypothesis.
    """
    hypotheses = []
    
    for var1, var2, corr_value in corr_pairs:
        if abs(corr_value) < min_threshold:
            continue
        
        direction = "positivamente" if corr_value > 0 else "negativamente"
        strength_label = _get_strength_label(abs(corr_value))
        
        hypothesis_text = (
            f"A variável '{var1}' está {direction} correlacionada com '{var2}' "
            f"(correlação = {corr_value:.3f}, força: {strength_label})."
        )
        
        hypothesis = Hypothesis(
            hypothesis_text=hypothesis_text,
            var1=var1,
            var2=var2,
            relationship_type="correlation",
            strength=corr_value,
            evidence=f"Correlação {direction} de {abs(corr_value):.3f} observada nos dados"
        )
        
        hypotheses.append(hypothesis)
    
    return hypotheses


def generate_group_difference_hypotheses(df: pd.DataFrame,
                                        column_types: Dict[str, List[str]],
                                        min_groups: int = 2,
                                        max_groups: int = 5) -> List[Hypothesis]:
    """
    Gera hipóteses baseadas em diferenças entre grupos categóricos.

    Args:
        df: DataFrame com os dados.
        column_types: Dicionário com tipos de colunas.
        min_groups: Número mínimo de categorias para considerar.
        max_groups: Número máximo de categorias para considerar.

    Returns:
        Lista de objetos Hypothesis.
    """
    hypotheses = []
    categorical_cols = column_types.get('categorical_nominal', [])
    numeric_cols = column_types.get('numeric_continuous', [])
    
    for cat_col in categorical_cols:
        if cat_col not in df.columns:
            continue
            
        n_unique = df[cat_col].nunique()
        
        if n_unique < min_groups or n_unique > max_groups:
            continue
        
        for num_col in numeric_cols[:3]:  # Limita a 3 variáveis numéricas
            if num_col not in df.columns:
                continue
            
            # Calcula estatísticas por grupo
            group_stats = df.groupby(cat_col)[num_col].agg(['mean', 'std', 'count'])
            
            # Verifica se há diferença nas médias
            means = group_stats['mean'].dropna()
            
            if len(means) < 2:
                continue
            
            mean_diff = means.max() - means.min()
            overall_std = df[num_col].std()
            
            # Heurística: diferença relativa às médias
            overall_mean = df[num_col].mean()
            if overall_mean != 0:
                relative_diff = mean_diff / abs(overall_mean)
            else:
                relative_diff = mean_diff
            
            if relative_diff > 0.1:  # Pelo menos 10% de diferença relativa
                best_group = means.idxmax()
                worst_group = means.idxmin()
                
                hypothesis_text = (
                    f"Existem diferenças significativas em '{num_col}' entre os grupos de '{cat_col}'. "
                    f"O grupo '{best_group}' apresenta média maior ({means[best_group]:.2f}) "
                    f"que o grupo '{worst_group}' ({means[worst_group]:.2f})."
                )
                
                hypothesis = Hypothesis(
                    hypothesis_text=hypothesis_text,
                    var1=cat_col,
                    var2=num_col,
                    relationship_type="difference",
                    strength=relative_diff,
                    evidence=f"Diferença relativa de {relative_diff:.1%} entre grupos extremos"
                )
                
                hypotheses.append(hypothesis)
    
    return hypotheses


def generate_distribution_hypotheses(df: pd.DataFrame,
                                    column_types: Dict[str, List[str]]) -> List[Hypothesis]:
    """
    Gera hipóteses sobre distribuições e valores atípicos.

    Args:
        df: DataFrame com os dados.
        column_types: Dicionário com tipos de colunas.

    Returns:
        Lista de objetos Hypothesis.
    """
    hypotheses = []
    numeric_cols = column_types.get('numeric_continuous', [])
    
    for col in numeric_cols[:3]:  # Limita a 3 variáveis
        if col not in df.columns:
            continue
        
        # Verifica skewness
        skewness = df[col].skew()
        
        if abs(skewness) > 0.5:
            direction = "à direita" if skewness > 0 else "à esquerda"
            
            hypothesis_text = (
                f"A distribuição de '{col}' é assimétrica {direction} "
                f"(coeficiente de assimetria = {skewness:.3f}), "
                f"sugerindo que valores extremos podem influenciar análises."
            )
            
            hypothesis = Hypothesis(
                hypothesis_text=hypothesis_text,
                var1=col,
                var2=None,
                relationship_type="distribution",
                strength=abs(skewness),
                evidence=f"Assimetria de {skewness:.3f} detectada"
            )
            
            hypotheses.append(hypothesis)
    
    return hypotheses


def generate_categorical_association_hypotheses(df: pd.DataFrame,
                                               column_types: Dict[str, List[str]]) -> List[Hypothesis]:
    """
    Gera hipóteses sobre associações entre variáveis categóricas.

    Args:
        df: DataFrame com os dados.
        column_types: Dicionário com tipos de colunas.

    Returns:
        Lista de objetos Hypothesis.
    """
    hypotheses = []
    categorical_cols = column_types.get('categorical_nominal', [])
    
    # Analisa pares de variáveis categóricas
    for i, cat1 in enumerate(categorical_cols):
        for cat2 in categorical_cols[i+1:]:
            if cat1 not in df.columns or cat2 not in df.columns:
                continue
            
            # Cria tabela de contingência
            contingency = pd.crosstab(df[cat1], df[cat2])
            
            if contingency.shape[0] < 2 or contingency.shape[1] < 2:
                continue
            
            # Verifica se há associação aparente
            row_totals = contingency.sum(axis=1)
            col_totals = contingency.sum(axis=0)
            total = contingency.values.sum()
            
            # Calcula esperado sob independência
            expected = np.outer(row_totals, col_totals) / total
            
            # Compara observado vs esperado
            chi_contrib = ((contingency.values - expected) ** 2 / expected).sum()
            
            if chi_contrib > 10:  # Limiar arbitrário para associação forte
                hypothesis_text = (
                    f"Existe associação entre '{cat1}' e '{cat2}'. "
                    f"A distribuição de '{cat2}' varia significativamente entre as categorias de '{cat1}'."
                )
                
                hypothesis = Hypothesis(
                    hypothesis_text=hypothesis_text,
                    var1=cat1,
                    var2=cat2,
                    relationship_type="association",
                    strength=chi_contrib,
                    evidence=f"Estatística qui-quadrado aproximada = {chi_contrib:.2f}"
                )
                
                hypotheses.append(hypothesis)
    
    return hypotheses


def _get_strength_label(corr_value: float) -> str:
    """Retorna um rótulo descritivo para a força da correlação."""
    if corr_value >= 0.9:
        return "muito forte"
    elif corr_value >= 0.7:
        return "forte"
    elif corr_value >= 0.5:
        return "moderada"
    elif corr_value >= 0.3:
        return "fraca"
    else:
        return "muito fraca"


def generate_hypotheses(df: pd.DataFrame,
                       exploratory_results: Dict[str, Any],
                       max_hypotheses: int = 5) -> List[Hypothesis]:
    """
    Gera hipóteses automáticas baseadas na análise exploratória.

    Args:
        df: DataFrame com os dados.
        exploratory_results: Resultados da análise exploratória.
        max_hypotheses: Número máximo de hipóteses para retornar.

    Returns:
        Lista de objetos Hypothesis ordenados por força da evidência.
    """
    all_hypotheses = []
    
    # Extrai informações necessárias
    column_types = exploratory_results.get('column_types', {})
    corr_pairs = exploratory_results.get('correlations', {}).get('strong_pairs', [])
    
    # Gera diferentes tipos de hipóteses
    corr_hypotheses = generate_correlation_hypotheses(df, corr_pairs)
    all_hypotheses.extend(corr_hypotheses)
    
    group_hypotheses = generate_group_difference_hypotheses(df, column_types)
    all_hypotheses.extend(group_hypotheses)
    
    dist_hypotheses = generate_distribution_hypotheses(df, column_types)
    all_hypotheses.extend(dist_hypotheses)
    
    assoc_hypotheses = generate_categorical_association_hypotheses(df, column_types)
    all_hypotheses.extend(assoc_hypotheses)
    
    # Ordena por força da evidência
    all_hypotheses.sort(key=lambda h: h.strength if h.strength else 0, reverse=True)
    
    # Retorna apenas o número máximo solicitado
    return all_hypotheses[:max_hypotheses]


def format_hypotheses_for_report(hypotheses: List[Hypothesis]) -> str:
    """
    Formata hipóteses para relatório em texto.

    Args:
        hypotheses: Lista de objetos Hypothesis.

    Returns:
        String formatada com as hipóteses.
    """
    if not hypotheses:
        return "Nenhuma hipótese foi gerada com base nos dados fornecidos."
    
    report_lines = [
        "=" * 60,
        "HIPÓTESES GERADAS AUTOMATICAMENTE",
        "=" * 60,
        ""
    ]
    
    for i, hyp in enumerate(hypotheses, 1):
        report_lines.extend([
            f"Hipótese #{i}",
            "-" * 40,
            f"Descrição: {hyp.hypothesis_text}",
            f"Variável 1: {hyp.var1}",
            f"Variável 2: {hyp.var2}",
            f"Tipo de Relação: {hyp.relationship_type}",
            f"Força Observada: {hyp.strength:.3f}" if hyp.strength else "N/A",
            f"Evidência: {hyp.evidence}",
            ""
        ])
    
    return "\n".join(report_lines)
