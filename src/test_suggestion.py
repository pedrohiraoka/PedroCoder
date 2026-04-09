"""
Módulo de Sugestão de Testes Estatísticos para o Motor de Hipótese Gerativa.

Para cada hipótese gerada, sugere testes estatísticos apropriados,
planos de amostragem e métricas de sucesso.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class StatisticalTest:
    """Classe que representa um teste estatístico sugerido."""
    
    name: str
    description: str
    use_case: str
    assumptions: List[str]
    implementation_hint: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'use_case': self.use_case,
            'assumptions': self.assumptions,
            'implementation_hint': self.implementation_hint
        }


@dataclass
class SamplingPlan:
    """Classe que representa um plano de amostragem."""
    
    method: str
    description: str
    recommended_sample_size: int
    justification: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method,
            'description': self.description,
            'recommended_sample_size': self.recommended_sample_size,
            'justification': self.justification
        }


@dataclass
class SuccessMetrics:
    """Classe que representa métricas de sucesso para avaliação."""
    
    primary_metric: str
    threshold: str
    interpretation: str
    secondary_metrics: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_metric': self.primary_metric,
            'threshold': self.threshold,
            'interpretation': self.interpretation,
            'secondary_metrics': self.secondary_metrics or []
        }


@dataclass
class HypothesisTestPlan:
    """Classe que representa o plano completo de teste para uma hipótese."""
    
    hypothesis: str
    test: StatisticalTest
    sampling_plan: SamplingPlan
    success_metrics: SuccessMetrics
    additional_recommendations: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hypothesis': self.hypothesis,
            'test': self.test.to_dict(),
            'sampling_plan': self.sampling_plan.to_dict(),
            'success_metrics': self.success_metrics.to_dict(),
            'additional_recommendations': self.additional_recommendations or []
        }


# Catálogo de testes estatísticos
TEST_CATALOG = {
    'pearson_correlation': StatisticalTest(
        name="Teste de Correlação de Pearson",
        description="Mede a correlação linear entre duas variáveis contínuas.",
        use_case="Duas variáveis contínuas, relação linear esperada.",
        assumptions=[
            "Variáveis são contínuas e normalmente distribuídas",
            "Relação linear entre as variáveis",
            "Homocedasticidade (variância constante)",
            "Ausência de outliers significativos"
        ],
        implementation_hint="scipy.stats.pearsonr(x, y)"
    ),
    
    'spearman_correlation': StatisticalTest(
        name="Teste de Correlação de Spearman",
        description="Mede a correlação monotônica entre duas variáveis (não-paramétrico).",
        use_case="Variáveis ordinais ou contínuas não-normais, relação monotônica.",
        assumptions=[
            "Variáveis são pelo menos ordinais",
            "Relação monotônica entre as variáveis",
            "Não assume normalidade"
        ],
        implementation_hint="scipy.stats.spearmanr(x, y)"
    ),
    
    't_test_independent': StatisticalTest(
        name="Teste-t de Student para Amostras Independentes",
        description="Compara as médias de dois grupos independentes.",
        use_case="Comparar média de variável contínua entre dois grupos categóricos.",
        assumptions=[
            "Variável dependente é contínua e normalmente distribuída",
            "Grupos são independentes",
            "Homogeneidade de variâncias (teste de Levene)",
            "Ausência de outliers significativos"
        ],
        implementation_hint="scipy.stats.ttest_ind(group1, group2, equal_var=True/False)"
    ),
    
    't_test_paired': StatisticalTest(
        name="Teste-t de Student para Amostras Pareadas",
        description="Compara as médias de duas medições no mesmo grupo.",
        use_case="Medições antes/depois no mesmo grupo ou pares relacionados.",
        assumptions=[
            "Diferenças entre pares são normalmente distribuídas",
            "Variável dependente é contínua",
            "Observações são pareadas"
        ],
        implementation_hint="scipy.stats.ttest_rel(before, after)"
    ),
    
    'anova_oneway': StatisticalTest(
        name="ANOVA de Uma Via",
        description="Compara as médias de três ou mais grupos independentes.",
        use_case="Variável contínua com fator categórico de 3+ níveis.",
        assumptions=[
            "Variável dependente é contínua e normalmente distribuída",
            "Grupos são independentes",
            "Homogeneidade de variâncias",
            "Independência das observações"
        ],
        implementation_hint="scipy.stats.f_oneway(group1, group2, group3, ...)"
    ),
    
    'chi_square': StatisticalTest(
        name="Teste Qui-Quadrado de Independência",
        description="Testa associação entre duas variáveis categóricas.",
        use_case="Duas variáveis categóricas, tabela de contingência.",
        assumptions=[
            "Variáveis são categóricas",
            "Observações são independentes",
            "Frequências esperadas > 5 em pelo menos 80% das células"
        ],
        implementation_hint="scipy.stats.chi2_contingency(contingency_table)"
    ),
    
    'mann_whitney': StatisticalTest(
        name="Teste U de Mann-Whitney",
        description="Teste não-paramétrico para comparar dois grupos independentes.",
        use_case="Variável ordinal ou contínua não-normal, dois grupos.",
        assumptions=[
            "Variável é pelo menos ordinal",
            "Grupos são independentes",
            "Distribuições têm forma similar",
            "Não assume normalidade"
        ],
        implementation_hint="scipy.stats.mannwhitneyu(group1, group2, alternative='two-sided')"
    ),
    
    'kruskal_wallis': StatisticalTest(
        name="Teste de Kruskal-Wallis",
        description="Teste não-paramétrico para comparar três ou mais grupos.",
        use_case="Variável ordinal ou contínua não-normal, 3+ grupos.",
        assumptions=[
            "Variável é pelo menos ordinal",
            "Grupos são independentes",
            "Não assume normalidade"
        ],
        implementation_hint="scipy.stats.kruskal(group1, group2, group3, ...)"
    ),
    
    'linear_regression': StatisticalTest(
        name="Regressão Linear Simples",
        description="Modela relação linear entre variável preditora e resposta.",
        use_case="Prever variável contínua baseada em outra variável contínua.",
        assumptions=[
            "Relação linear entre X e Y",
            "Resíduos normalmente distribuídos",
            "Homocedasticidade dos resíduos",
            "Independência dos resíduos"
        ],
        implementation_hint="statsmodels.api.OLS(y, X).fit() ou sklearn.linear_model.LinearRegression()"
    )
}


def calculate_sample_size(effect_size: float = 0.5, 
                         alpha: float = 0.05, 
                         power: float = 0.8,
                         test_type: str = 'two_group') -> int:
    """
    Calcula tamanho de amostra recomendado usando fórmula simplificada.

    Args:
        effect_size: Tamanho do efeito esperado (Cohen's d).
        alpha: Nível de significância.
        power: Poder estatístico desejado.
        test_type: Tipo de teste ('two_group', 'correlation', 'anova').

    Returns:
        Tamanho de amostra recomendado por grupo.
    """
    # Valores z padrão
    z_alpha = 1.96  # Para alpha = 0.05 (two-tailed)
    z_beta = 0.84   # Para power = 0.80
    
    # Fórmulas simplificadas baseadas em aproximações
    if test_type == 'two_group':
        # n = 2 * ((z_alpha + z_beta) / effect_size)^2
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    elif test_type == 'correlation':
        # Fórmula para correlação
        # Transformação de Fisher
        n = ((z_alpha + z_beta) / (0.5 * np.log((1 + effect_size) / (1 - effect_size)))) ** 2 + 3
    elif test_type == 'anova':
        # Aproximação para ANOVA
        k = 3  # Número de grupos assumido
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2 * k
    else:
        n = 30  # Default
    
    return max(int(np.ceil(n)), 5)  # Mínimo de 5 observações


def select_test_for_hypothesis(hypothesis_type: str,
                               var1_type: str,
                               var2_type: Optional[str] = None,
                               n_groups: int = None) -> StatisticalTest:
    """
    Seleciona o teste estatístico apropriado baseado no tipo de hipótese.

    Args:
        hypothesis_type: Tipo de hipótese ('correlation', 'difference', 'association').
        var1_type: Tipo da primeira variável ('continuous', 'categorical', 'ordinal').
        var2_type: Tipo da segunda variável (opcional).
        n_groups: Número de grupos (para testes de diferença).

    Returns:
        Objeto StatisticalTest recomendado.
    """
    # Mapa de seleção de testes
    if hypothesis_type == 'correlation':
        if var1_type == 'continuous' and var2_type == 'continuous':
            # Verifica se deve usar Spearman (mais robusto)
            return TEST_CATALOG['spearman_correlation']
    
    elif hypothesis_type == 'difference':
        if n_groups == 2:
            if var2_type == 'continuous':
                return TEST_CATALOG['mann_whitney']  # Não-paramétrico por padrão
        elif n_groups and n_groups > 2:
            if var2_type == 'continuous':
                return TEST_CATALOG['kruskal_wallis']  # Não-paramétrico por padrão
    
    elif hypothesis_type == 'association':
        if var1_type == 'categorical' and var2_type == 'categorical':
            return TEST_CATALOG['chi_square']
    
    # Default: retorna Spearman como opção mais geral
    return TEST_CATALOG['spearman_correlation']


def create_sampling_plan(df_size: int,
                        hypothesis_type: str,
                        n_groups: int = None) -> SamplingPlan:
    """
    Cria um plano de amostragem recomendado.

    Args:
        df_size: Tamanho total da população disponível.
        hypothesis_type: Tipo de hipótese sendo testada.
        n_groups: Número de grupos (se aplicável).

    Returns:
        Objeto SamplingPlan com recomendações.
    """
    # Determina método de amostragem
    if n_groups and n_groups > 1:
        method = "Amostragem Estratificada"
        description = (
            f"Divida a população em {n_groups} estratos (grupos) e "
            f"amarre proporcionalmente de cada estrato para garantir representatividade."
        )
        test_type = 'anova' if n_groups > 2 else 'two_group'
    else:
        method = "Amostragem Aleatória Simples"
        description = (
            "Selecione observações aleatoriamente da população com igual probabilidade. "
            "Use randomização verdadeira para evitar viés de seleção."
        )
        test_type = 'correlation'
    
    # Calcula tamanho recomendado
    sample_size = calculate_sample_size(effect_size=0.5, power=0.8, test_type=test_type)
    
    # Ajusta se população for menor que amostra recomendada
    if df_size < sample_size:
        justification = (
            f"Tamanho da população ({df_size}) é menor que o recomendado. "
            f"Considere usar toda a população ou buscar dados adicionais."
        )
        sample_size = df_size
    else:
        justification = (
            f"Baseado em poder estatístico de 80%, alpha de 5%, e tamanho de efeito médio (d=0.5). "
            f"Para detectar efeitos menores, aumente o tamanho da amostra."
        )
    
    return SamplingPlan(
        method=method,
        description=description,
        recommended_sample_size=sample_size,
        justification=justification
    )


def create_success_metrics(hypothesis_type: str,
                          test_name: str) -> SuccessMetrics:
    """
    Cria métricas de sucesso para avaliar resultados do teste.

    Args:
        hypothesis_type: Tipo de hipótese.
        test_name: Nome do teste estatístico.

    Returns:
        Objeto SuccessMetrics com critérios de avaliação.
    """
    metrics_map = {
        'correlation': SuccessMetrics(
            primary_metric="Coeficiente de correlação (r)",
            threshold="|r| > 0.5 para efeito moderado",
            interpretation=(
                "r > 0: correlação positiva; r < 0: correlação negativa. "
                "|r| > 0.7: forte; |r| > 0.5: moderada; |r| > 0.3: fraca."
            ),
            secondary_metrics=["p-valor < 0.05", "Intervalo de confiança de 95%"]
        ),
        'difference': SuccessMetrics(
            primary_metric="Diferença de médias padronizada (Cohen's d)",
            threshold="d > 0.5 para efeito moderado",
            interpretation=(
                "d > 0: grupo 1 tem média maior; d < 0: grupo 2 tem média maior. "
                "d > 0.8: efeito grande; d > 0.5: moderado; d > 0.2: pequeno."
            ),
            secondary_metrics=["p-valor < 0.05", "Intervalo de confiança de 95%", "Potência estatística > 0.8"]
        ),
        'association': SuccessMetrics(
            primary_metric="Estatística Qui-Quadrado e p-valor",
            threshold="p < 0.05 para rejeitar independência",
            interpretation=(
                "p < 0.05: evidência de associação entre variáveis. "
                "Considere calcular V de Cramer para força da associação."
            ),
            secondary_metrics=["V de Cramer > 0.3 para associação moderada", "Resíduos padronizados"]
        ),
        'distribution': SuccessMetrics(
            primary_metric="Coeficiente de assimetria (skewness)",
            threshold="|skewness| > 0.5 indica assimetria moderada",
            interpretation=(
                "skewness > 0: assimetria à direita; skewness < 0: assimetria à esquerda. "
                "|skewness| > 1: assimetria forte."
            ),
            secondary_metrics=["Teste de normalidade (Shapiro-Wilk)", "Kurtose"]
        )
    }
    
    return metrics_map.get(hypothesis_type, metrics_map['correlation'])


def generate_test_plan(hypothesis: Any,
                      df: Any,
                      column_types: Dict[str, List[str]]) -> HypothesisTestPlan:
    """
    Gera um plano completo de teste para uma hipótese.

    Args:
        hypothesis: Objeto Hypothesis para o qual gerar o plano.
        df: DataFrame com os dados (para determinar tamanhos).
        column_types: Dicionário com tipos de colunas.

    Returns:
        Objeto HypothesisTestPlan com todas as recomendações.
    """
    # Determina tipos de variáveis
    var1 = hypothesis.var1
    var2 = hypothesis.var2
    
    # Classifica tipos
    def get_var_type(var_name):
        if not var_name:
            return None
        if var_name in column_types.get('numeric_continuous', []):
            return 'continuous'
        elif var_name in column_types.get('numeric_discrete', []):
            return 'ordinal'
        elif var_name in column_types.get('categorical_nominal', []):
            return 'categorical'
        else:
            return 'unknown'
    
    var1_type = get_var_type(var1)
    var2_type = get_var_type(var2)
    
    # Determina número de grupos se aplicável
    n_groups = None
    if var1_type == 'categorical' and var1 in df.columns:
        n_groups = df[var1].nunique()
    elif var2_type == 'categorical' and var2 in df.columns:
        n_groups = df[var2].nunique()
    
    # Seleciona teste
    test = select_test_for_hypothesis(
        hypothesis.relationship_type,
        var1_type or 'continuous',
        var2_type,
        n_groups
    )
    
    # Cria plano de amostragem
    sampling_plan = create_sampling_plan(
        len(df),
        hypothesis.relationship_type,
        n_groups
    )
    
    # Cria métricas de sucesso
    success_metrics = create_success_metrics(
        hypothesis.relationship_type,
        test.name
    )
    
    # Recomendações adicionais
    recommendations = [
        "Verifique os pressupostos do teste antes de aplicar.",
        "Considere correções para múltiplas comparações se testar várias hipóteses.",
        "Documente qualquer exclusão de dados ou tratamento de outliers.",
        "Reporte intervalos de confiança junto com estimativas pontuais."
    ]
    
    if hypothesis.relationship_type == 'difference' and n_groups and n_groups > 2:
        recommendations.append(
            "Se ANOVA/Kruskal-Wallis for significativo, realize testes post-hoc "
            "(ex: Tukey HSD ou Dunn's test) para identificar quais grupos diferem."
        )
    
    return HypothesisTestPlan(
        hypothesis=hypothesis.hypothesis_text,
        test=test,
        sampling_plan=sampling_plan,
        success_metrics=success_metrics,
        additional_recommendations=recommendations
    )


def format_test_plans_for_report(test_plans: List[HypothesisTestPlan]) -> str:
    """
    Formata planos de teste para relatório em texto.

    Args:
        test_plans: Lista de objetos HypothesisTestPlan.

    Returns:
        String formatada com os planos de teste.
    """
    if not test_plans:
        return "Nenhum plano de teste foi gerado."
    
    report_lines = [
        "=" * 60,
        "PLANOS DE TESTE ESTATÍSTICO SUGERIDOS",
        "=" * 60,
        ""
    ]
    
    for i, plan in enumerate(test_plans, 1):
        report_lines.extend([
            f"Plano de Teste #{i}",
            "-" * 40,
            f"Hipótese: {plan.hypothesis}",
            "",
            "TESTE SUGERIDO:",
            f"  Nome: {plan.test.name}",
            f"  Descrição: {plan.test.description}",
            f"  Caso de Uso: {plan.test.use_case}",
            f"  Pressupostos:",
        ])
        
        for assumption in plan.test.assumptions:
            report_lines.append(f"    - {assumption}")
        
        report_lines.append(f"  Implementação: {plan.test.implementation_hint}")
        report_lines.append("")
        
        report_lines.append("PLANO DE AMOSTRAGEM:")
        report_lines.append(f"  Método: {plan.sampling_plan.method}")
        report_lines.append(f"  Descrição: {plan.sampling_plan.description}")
        report_lines.append(f"  Tamanho Recomendado: {plan.sampling_plan.recommended_sample_size}")
        report_lines.append(f"  Justificativa: {plan.sampling_plan.justification}")
        report_lines.append("")
        
        report_lines.append("MÉTRICAS DE SUCESSO:")
        report_lines.append(f"  Métrica Primária: {plan.success_metrics.primary_metric}")
        report_lines.append(f"  Limiar: {plan.success_metrics.threshold}")
        report_lines.append(f"  Interpretação: {plan.success_metrics.interpretation}")
        
        if plan.success_metrics.secondary_metrics:
            report_lines.append("  Métricas Secundárias:")
            for metric in plan.success_metrics.secondary_metrics:
                report_lines.append(f"    - {metric}")
        
        report_lines.append("")
        
        if plan.additional_recommendations:
            report_lines.append("RECOMENDAÇÕES ADICIONAIS:")
            for rec in plan.additional_recommendations:
                report_lines.append(f"  - {rec}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("")
    
    return "\n".join(report_lines)
