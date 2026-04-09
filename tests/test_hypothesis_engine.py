"""
Testes unitários para o Motor de Hipótese Gerativa.

Cobre as funções críticas de:
- Ingestão de dados
- Análise exploratória
- Geração de hipóteses
- Sugestão de testes estatísticos
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import sys

# Adiciona o caminho do src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_ingestion import (
    load_csv, 
    load_json, 
    fetch_from_api,
    load_data
)
from src.exploratory_analysis import (
    get_data_structure,
    identify_column_types,
    calculate_correlations,
    find_strong_correlations,
    perform_exploratory_analysis
)
from src.hypothesis_generation import (
    Hypothesis,
    generate_correlation_hypotheses,
    generate_group_difference_hypotheses,
    generate_hypotheses,
    format_hypotheses_for_report
)
from src.test_suggestion import (
    StatisticalTest,
    SamplingPlan,
    SuccessMetrics,
    HypothesisTestPlan,
    calculate_sample_size,
    select_test_for_hypothesis,
    create_sampling_plan,
    create_success_metrics,
    generate_test_plan
)
from src.main import HypothesisEngine


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_dataframe():
    """Cria um DataFrame de exemplo para testes."""
    np.random.seed(42)
    n = 100
    
    df = pd.DataFrame({
        'idade': np.random.normal(35, 10, n).clip(18, 70).astype(int),
        'renda': np.random.exponential(5000, n).astype(int),
        'anos_estudo': np.random.normal(12, 3, n).clip(5, 20).astype(int),
        'genero': np.random.choice(['Masculino', 'Feminino'], n),
        'regiao': np.random.choice(['Norte', 'Sul', 'Leste', 'Oeste'], n),
        'satisfacao': np.random.randint(1, 6, n)
    })
    
    # Adiciona correlação artificial entre renda e anos_estudo
    df['renda'] = df['renda'] + df['anos_estudo'] * 300
    
    return df


@pytest.fixture
def sample_csv_file(tmp_path, sample_dataframe):
    """Cria um arquivo CSV temporário para testes."""
    csv_path = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_json_file(tmp_path, sample_dataframe):
    """Cria um arquivo JSON temporário para testes."""
    json_path = tmp_path / "test_data.json"
    sample_dataframe.to_dict(orient='records')
    with open(json_path, 'w') as f:
        json.dump(sample_dataframe.to_dict(orient='records'), f)
    return str(json_path)


# =============================================================================
# TESTES DE INGESTÃO DE DADOS
# =============================================================================

class TestDataIngestion:
    """Testes para o módulo de ingestão de dados."""
    
    def test_load_csv(self, sample_csv_file, sample_dataframe):
        """Testa carregamento de CSV."""
        df = load_csv(sample_csv_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_dataframe)
        assert list(df.columns) == list(sample_dataframe.columns)
    
    def test_load_json(self, sample_json_file, sample_dataframe):
        """Testa carregamento de JSON."""
        df = load_json(sample_json_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_dataframe)
    
    def test_load_data_auto_csv(self, sample_csv_file):
        """Testa detecção automática de tipo para CSV."""
        df = load_data(sample_csv_file, source_type='auto')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_fetch_from_api_invalid_url(self):
        """Testa tratamento de erro para URL inválida."""
        with pytest.raises(Exception):
            fetch_from_api("http://url-invalida-exemplo.com/api")


# =============================================================================
# TESTES DE ANÁLISE EXPLORATÓRIA
# =============================================================================

class TestExploratoryAnalysis:
    """Testes para o módulo de análise exploratória."""
    
    def test_get_data_structure(self, sample_dataframe):
        """Testa obtenção da estrutura dos dados."""
        structure = get_data_structure(sample_dataframe)
        
        assert 'shape' in structure
        assert 'columns' in structure
        assert 'dtypes' in structure
        assert 'missing_values' in structure
        
        assert structure['shape'][0] == 100
        assert len(structure['columns']) == 6
    
    def test_identify_column_types(self, sample_dataframe):
        """Testa identificação de tipos de colunas."""
        column_types = identify_column_types(sample_dataframe)
        
        assert 'numeric_continuous' in column_types
        assert 'categorical_nominal' in column_types
        
        # Verifica se colunas foram classificadas
        all_columns = []
        for col_list in column_types.values():
            all_columns.extend(col_list)
        
        assert len(all_columns) == len(sample_dataframe.columns)
    
    def test_calculate_correlations(self, sample_dataframe):
        """Testa cálculo de matriz de correlação."""
        corr_matrix = calculate_correlations(sample_dataframe)
        
        assert isinstance(corr_matrix, pd.DataFrame)
        
        # Verifica se é uma matriz quadrada
        numeric_cols = sample_dataframe.select_dtypes(include=[np.number]).columns
        assert corr_matrix.shape[0] == corr_matrix.shape[1]
        assert corr_matrix.shape[0] == len(numeric_cols)
        
        # Diagonal deve ser 1
        for col in corr_matrix.columns:
            assert corr_matrix.loc[col, col] == 1.0
    
    def test_find_strong_correlations(self, sample_dataframe):
        """Testa identificação de correlações fortes."""
        strong_corrs = find_strong_correlations(sample_dataframe, threshold=0.3)
        
        assert isinstance(strong_corrs, list)
        
        # Cada item deve ser uma tupla (var1, var2, correlation)
        for corr in strong_corrs:
            assert len(corr) == 3
            assert isinstance(corr[0], str)
            assert isinstance(corr[1], str)
            assert isinstance(corr[2], float)
            assert abs(corr[2]) >= 0.3
    
    def test_perform_exploratory_analysis(self, sample_dataframe):
        """Testa análise exploratória completa."""
        results = perform_exploratory_analysis(sample_dataframe)
        
        assert 'structure' in results
        assert 'descriptive_stats' in results
        assert 'column_types' in results
        assert 'correlations' in results
        assert 'outliers' in results


# =============================================================================
# TESTES DE GERAÇÃO DE HIPÓTESES
# =============================================================================

class TestHypothesisGeneration:
    """Testes para o módulo de geração de hipóteses."""
    
    def test_hypothesis_class(self):
        """Testa classe Hypothesis."""
        hyp = Hypothesis(
            hypothesis_text="Teste de hipótese",
            var1="var1",
            var2="var2",
            relationship_type="correlation",
            strength=0.75,
            evidence="Correlação observada"
        )
        
        assert hyp.hypothesis_text == "Teste de hipótese"
        assert hyp.var1 == "var1"
        assert hyp.var2 == "var2"
        assert hyp.strength == 0.75
        
        # Testa conversão para dict
        hyp_dict = hyp.to_dict()
        assert 'hypothesis' in hyp_dict
        assert 'variable_1' in hyp_dict
    
    def test_generate_correlation_hypotheses(self, sample_dataframe):
        """Testa geração de hipóteses de correlação."""
        # Primeiro obtém pares de correlação
        corr_pairs = find_strong_correlations(sample_dataframe, threshold=0.1)
        
        hypotheses = generate_correlation_hypotheses(
            sample_dataframe, 
            corr_pairs,
            min_threshold=0.1
        )
        
        assert isinstance(hypotheses, list)
        
        for hyp in hypotheses:
            assert isinstance(hyp, Hypothesis)
            assert 'correlacionada' in hyp.hypothesis_text
    
    def test_generate_group_difference_hypotheses(self, sample_dataframe):
        """Testa geração de hipóteses de diferença entre grupos."""
        column_types = identify_column_types(sample_dataframe)
        
        hypotheses = generate_group_difference_hypotheses(
            sample_dataframe,
            column_types
        )
        
        assert isinstance(hypotheses, list)
        
        for hyp in hypotheses:
            assert isinstance(hyp, Hypothesis)
            assert hyp.relationship_type == 'difference'
    
    def test_generate_hypotheses(self, sample_dataframe):
        """Testa geração geral de hipóteses."""
        exploratory_results = perform_exploratory_analysis(sample_dataframe)
        
        hypotheses = generate_hypotheses(
            sample_dataframe,
            exploratory_results,
            max_hypotheses=5
        )
        
        assert isinstance(hypotheses, list)
        assert len(hypotheses) <= 5
        
        # Verifica se estão ordenadas por força
        if len(hypotheses) > 1:
            for i in range(len(hypotheses) - 1):
                h1_strength = hypotheses[i].strength or 0
                h2_strength = hypotheses[i + 1].strength or 0
                assert h1_strength >= h2_strength
    
    def test_format_hypotheses_for_report(self):
        """Testa formatação de relatório de hipóteses."""
        hypotheses = [
            Hypothesis("Hipótese 1", "var1", "var2", "correlation", 0.8, "Evidência 1"),
            Hypothesis("Hipótese 2", "var3", "var4", "difference", 0.6, "Evidência 2")
        ]
        
        report = format_hypotheses_for_report(hypotheses)
        
        assert isinstance(report, str)
        assert "Hipótese #1" in report
        assert "Hipótese #2" in report
        assert "Hipótese 1" in report
    
    def test_format_hypotheses_empty_list(self):
        """Testa formatação com lista vazia."""
        report = format_hypotheses_for_report([])
        assert "Nenhuma hipótese" in report


# =============================================================================
# TESTES DE SUGESTÃO DE TESTES ESTATÍSTICOS
# =============================================================================

class TestTestSuggestion:
    """Testes para o módulo de sugestão de testes."""
    
    def test_statistical_test_class(self):
        """Testa classe StatisticalTest."""
        test = StatisticalTest(
            name="Teste Exemplo",
            description="Descrição do teste",
            use_case="Caso de uso",
            assumptions=["Assunção 1", "Assunção 2"],
            implementation_hint="codigo.exemplo()"
        )
        
        assert test.name == "Teste Exemplo"
        assert len(test.assumptions) == 2
        
        # Testa conversão para dict
        test_dict = test.to_dict()
        assert 'name' in test_dict
        assert 'assumptions' in test_dict
    
    def test_sampling_plan_class(self):
        """Testa classe SamplingPlan."""
        plan = SamplingPlan(
            method="Aleatória Simples",
            description="Descrição",
            recommended_sample_size=100,
            justification="Justificativa"
        )
        
        assert plan.recommended_sample_size == 100
    
    def test_success_metrics_class(self):
        """Testa classe SuccessMetrics."""
        metrics = SuccessMetrics(
            primary_metric="p-valor",
            threshold="< 0.05",
            interpretation="Significância estatística",
            secondary_metrics=["IC 95%", "Power"]
        )
        
        assert len(metrics.secondary_metrics) == 2
    
    def test_calculate_sample_size(self):
        """Testa cálculo de tamanho de amostra."""
        # Teste para dois grupos
        n_two_group = calculate_sample_size(effect_size=0.5, test_type='two_group')
        assert n_two_group > 0
        
        # Teste para correlação
        n_corr = calculate_sample_size(effect_size=0.5, test_type='correlation')
        assert n_corr > 0
        
        # Tamanhos maiores para efeitos menores
        n_small_effect = calculate_sample_size(effect_size=0.3, test_type='two_group')
        n_large_effect = calculate_sample_size(effect_size=0.8, test_type='two_group')
        assert n_small_effect > n_large_effect
    
    def test_select_test_for_hypothesis(self):
        """Testa seleção de teste baseado no tipo de hipótese."""
        # Teste para correlação
        test = select_test_for_hypothesis(
            hypothesis_type='correlation',
            var1_type='continuous',
            var2_type='continuous'
        )
        assert isinstance(test, StatisticalTest)
        assert 'correlação' in test.name.lower() or 'Correlação' in test.name
        
        # Teste para associação
        test = select_test_for_hypothesis(
            hypothesis_type='association',
            var1_type='categorical',
            var2_type='categorical'
        )
        assert 'Qui-Quadrado' in test.name or 'qui-quadrado' in test.name.lower()
    
    def test_create_sampling_plan(self):
        """Testa criação de plano de amostragem."""
        plan = create_sampling_plan(
            df_size=1000,
            hypothesis_type='difference',
            n_groups=2
        )
        
        assert isinstance(plan, SamplingPlan)
        assert plan.recommended_sample_size > 0
        assert 'Estratificada' in plan.method
    
    def test_create_success_metrics(self):
        """Testa criação de métricas de sucesso."""
        metrics = create_success_metrics(
            hypothesis_type='correlation',
            test_name='Spearman'
        )
        
        assert isinstance(metrics, SuccessMetrics)
        assert 'correlação' in metrics.primary_metric.lower() or 'r' in metrics.primary_metric.lower()
    
    def test_generate_test_plan(self, sample_dataframe):
        """Testa geração de plano de teste completo."""
        hypothesis = Hypothesis(
            "Hipótese de teste",
            "idade",
            "renda",
            "correlation",
            0.5,
            "Correlação observada"
        )
        
        column_types = identify_column_types(sample_dataframe)
        
        plan = generate_test_plan(hypothesis, sample_dataframe, column_types)
        
        assert isinstance(plan, HypothesisTestPlan)
        assert plan.hypothesis == "Hipótese de teste"
        assert isinstance(plan.test, StatisticalTest)
        assert isinstance(plan.sampling_plan, SamplingPlan)
        assert isinstance(plan.success_metrics, SuccessMetrics)


# =============================================================================
# TESTES DO MOTOR PRINCIPAL
# =============================================================================

class TestHypothesisEngine:
    """Testes para a classe HypothesisEngine."""
    
    def test_engine_initialization(self):
        """Testa inicialização do motor."""
        engine = HypothesisEngine(random_seed=42)
        
        assert engine.data is None
        assert engine.exploratory_results is None
        assert engine.hypotheses == []
        assert engine.test_plans == []
    
    def test_engine_load_dataframe(self, sample_dataframe):
        """Testa carregamento de DataFrame no motor."""
        engine = HypothesisEngine()
        result = engine.load_dataframe(sample_dataframe)
        
        assert result is engine  # Testa encadeamento
        assert engine.data is not None
        assert len(engine.data) == len(sample_dataframe)
    
    def test_engine_run_exploratory_analysis(self, sample_dataframe):
        """Testa execução de análise exploratória no motor."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        result = engine.run_exploratory_analysis()
        
        assert result is engine  # Testa encadeamento
        assert engine.exploratory_results is not None
        assert 'structure' in engine.exploratory_results
    
    def test_engine_generate_hypotheses(self, sample_dataframe):
        """Testa geração de hipóteses no motor."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_exploratory_analysis()
        result = engine.generate_hypotheses(max_hypotheses=3)
        
        assert result is engine  # Testa encadeamento
        assert len(engine.hypotheses) <= 3
    
    def test_engine_generate_test_plans(self, sample_dataframe):
        """Testa geração de planos de teste no motor."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_exploratory_analysis()
        engine.generate_hypotheses(max_hypotheses=3)
        result = engine.generate_test_plans()
        
        assert result is engine  # Testa encadeamento
        assert len(engine.test_plans) == len(engine.hypotheses)
    
    def test_engine_run_full_pipeline(self, sample_dataframe):
        """Testa execução do pipeline completo."""
        engine = HypothesisEngine()
        result = engine.load_dataframe(sample_dataframe).run_full_pipeline(
            max_hypotheses=5, 
            verbose=False
        )
        
        assert result is engine
        assert engine.exploratory_results is not None
        assert len(engine.hypotheses) > 0
        assert len(engine.test_plans) == len(engine.hypotheses)
    
    def test_engine_get_summary(self, sample_dataframe):
        """Testa obtenção de resumo."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_full_pipeline(max_hypotheses=3, verbose=False)
        
        summary = engine.get_summary()
        
        assert isinstance(summary, dict)
        assert 'data_shape' in summary
        assert 'n_hypotheses' in summary
        assert 'hypotheses' in summary
        assert 'test_plans' in summary
    
    def test_engine_generate_report_text(self, sample_dataframe):
        """Testa geração de relatório em texto."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_full_pipeline(max_hypotheses=3, verbose=False)
        
        report = engine.generate_report(output_format='text')
        
        assert isinstance(report, str)
        assert "RELATÓRIO" in report
        assert "HIPÓTESES" in report
    
    def test_engine_generate_report_json(self, sample_dataframe):
        """Testa geração de relatório em JSON."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_full_pipeline(max_hypotheses=3, verbose=False)
        
        report = engine.generate_report(output_format='json')
        
        assert isinstance(report, str)
        
        # Verifica se é JSON válido
        report_dict = json.loads(report)
        assert isinstance(report_dict, dict)
    
    def test_engine_error_without_data(self):
        """Testa erro ao executar sem dados."""
        engine = HypothesisEngine()
        
        with pytest.raises(ValueError, match="Nenhum dado carregado"):
            engine.run_exploratory_analysis()
    
    def test_engine_error_without_exploratory_analysis(self, sample_dataframe):
        """Testa erro ao gerar hipóteses sem análise exploratória."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        
        with pytest.raises(ValueError, match="Execute a análise exploratória"):
            engine.generate_hypotheses()
    
    def test_engine_reproducibility(self, sample_dataframe):
        """Testa reprodutibilidade dos resultados."""
        engine1 = HypothesisEngine(random_seed=42)
        engine1.load_dataframe(sample_dataframe)
        engine1.run_full_pipeline(max_hypotheses=5, verbose=False)
        
        engine2 = HypothesisEngine(random_seed=42)
        engine2.load_dataframe(sample_dataframe)
        engine2.run_full_pipeline(max_hypotheses=5, verbose=False)
        
        # Mesma seed deve produzir mesmos resultados
        assert len(engine1.hypotheses) == len(engine2.hypotheses)
        
        if len(engine1.hypotheses) > 0:
            assert engine1.hypotheses[0].hypothesis_text == engine2.hypotheses[0].hypothesis_text


# =============================================================================
# TESTES DE INTEGRAÇÃO
# =============================================================================

class TestIntegration:
    """Testes de integração do sistema completo."""
    
    def test_full_workflow_with_synthetic_data(self):
        """Testa fluxo completo com dados sintéticos."""
        np.random.seed(42)
        n = 150
        
        data = pd.DataFrame({
            'tempo_estudo': np.random.uniform(1, 10, n),
            'nota': np.random.uniform(5, 10, n),
            'frequencia': np.random.uniform(0.5, 1.0, n),
            'curso': np.random.choice(['A', 'B', 'C'], n),
            'turno': np.random.choice(['Manhã', 'Tarde', 'Noite'], n)
        })
        
        # Adiciona correlação positiva entre tempo_estudo e nota
        data['nota'] = data['nota'] + data['tempo_estudo'] * 0.5
        
        engine = HypothesisEngine(random_seed=42)
        engine.load_dataframe(data)
        engine.run_full_pipeline(max_hypotheses=5, verbose=False)
        
        # Verifica critérios de aceitação
        assert engine.data is not None
        assert engine.exploratory_results is not None
        assert len(engine.hypotheses) >= 1
        assert len(engine.hypotheses) <= 5
        assert len(engine.test_plans) == len(engine.hypotheses)
        
        # Verifica qualidade das hipóteses
        for hyp in engine.hypotheses:
            assert hyp.hypothesis_text is not None
            assert len(hyp.hypothesis_text) > 10
        
        # Verifica qualidade dos planos de teste
        for plan in engine.test_plans:
            assert plan.test.name is not None
            assert plan.sampling_plan.recommended_sample_size > 0
            assert plan.success_metrics.primary_metric is not None
    
    def test_save_and_load_report(self, sample_dataframe, tmp_path):
        """Testa salvar e carregar relatório."""
        engine = HypothesisEngine()
        engine.load_dataframe(sample_dataframe)
        engine.run_full_pipeline(max_hypotheses=3, verbose=False)
        
        # Salva relatório JSON
        json_path = tmp_path / "relatorio.json"
        engine.save_report(str(json_path), output_format='json')
        
        # Verifica se arquivo foi criado
        assert json_path.exists()
        
        # Carrega e verifica conteúdo
        with open(json_path, 'r') as f:
            report_data = json.load(f)
        
        assert 'n_hypotheses' in report_data
        assert report_data['n_hypotheses'] == len(engine.hypotheses)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
