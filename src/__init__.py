"""
Módulo __init__ para o pacote src do Motor de Hipótese Gerativa.
"""

from .data_ingestion import (
    load_csv,
    load_json,
    fetch_from_api,
    fetch_ibge_indicadores,
    fetch_camara_deputados,
    load_data
)

from .exploratory_analysis import (
    get_data_structure,
    get_descriptive_statistics,
    identify_column_types,
    calculate_correlations,
    find_strong_correlations,
    analyze_categorical_relationships,
    detect_outliers,
    perform_exploratory_analysis
)

from .hypothesis_generation import (
    Hypothesis,
    generate_correlation_hypotheses,
    generate_group_difference_hypotheses,
    generate_distribution_hypotheses,
    generate_categorical_association_hypotheses,
    generate_hypotheses,
    format_hypotheses_for_report
)

from .test_suggestion import (
    StatisticalTest,
    SamplingPlan,
    SuccessMetrics,
    HypothesisTestPlan,
    TEST_CATALOG,
    calculate_sample_size,
    select_test_for_hypothesis,
    create_sampling_plan,
    create_success_metrics,
    generate_test_plan,
    format_test_plans_for_report
)

from .main import HypothesisEngine, main

__version__ = '0.1.0'
__author__ = 'Motor de Hipótese Gerativa Team'

__all__ = [
    # Data Ingestion
    'load_csv',
    'load_json',
    'fetch_from_api',
    'fetch_ibge_indicadores',
    'fetch_camara_deputados',
    'load_data',
    
    # Exploratory Analysis
    'get_data_structure',
    'get_descriptive_statistics',
    'identify_column_types',
    'calculate_correlations',
    'find_strong_correlations',
    'analyze_categorical_relationships',
    'detect_outliers',
    'perform_exploratory_analysis',
    
    # Hypothesis Generation
    'Hypothesis',
    'generate_correlation_hypotheses',
    'generate_group_difference_hypotheses',
    'generate_distribution_hypotheses',
    'generate_categorical_association_hypotheses',
    'generate_hypotheses',
    'format_hypotheses_for_report',
    
    # Test Suggestion
    'StatisticalTest',
    'SamplingPlan',
    'SuccessMetrics',
    'HypothesisTestPlan',
    'TEST_CATALOG',
    'calculate_sample_size',
    'select_test_for_hypothesis',
    'create_sampling_plan',
    'create_success_metrics',
    'generate_test_plan',
    'format_test_plans_for_report',
    
    # Main Engine
    'HypothesisEngine',
    'main'
]
