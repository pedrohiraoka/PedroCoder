"""
Módulo principal do Motor de Hipótese Gerativa.

Integra todos os componentes do sistema:
- Ingestão de dados
- Análise exploratória
- Geração de hipóteses
- Sugestão de testes estatísticos
- Geração de relatórios
"""

import json
from typing import Dict, Any, Optional
import pandas as pd

from .data_ingestion import load_data, fetch_camara_deputados, fetch_ibge_indicadores
from .exploratory_analysis import perform_exploratory_analysis
from .hypothesis_generation import generate_hypotheses, format_hypotheses_for_report, Hypothesis
from .test_suggestion import (
    generate_test_plan, 
    format_test_plans_for_report, 
    HypothesisTestPlan
)


class HypothesisEngine:
    """
    Classe principal do Motor de Hipótese Gerativa.
    
    Orquestra todo o fluxo de análise, desde a ingestão de dados
    até a geração do relatório final com hipóteses e planos de teste.
    """
    
    def __init__(self, random_seed: int = 42):
        """
        Inicializa o motor de hipóteses.
        
        Args:
            random_seed: Semente para reprodutibilidade dos resultados.
        """
        import numpy as np
        np.random.seed(random_seed)
        self.random_seed = random_seed
        
        self.data: Optional[pd.DataFrame] = None
        self.exploratory_results: Optional[Dict[str, Any]] = None
        self.hypotheses: list[Hypothesis] = []
        self.test_plans: list[HypothesisTestPlan] = []
    
    def load_data_from_file(self, file_path: str, source_type: str = 'auto') -> 'HypothesisEngine':
        """
        Carrega dados de um arquivo local.
        
        Args:
            file_path: Caminho para o arquivo de dados.
            source_type: Tipo de arquivo ('csv', 'json', 'auto').
        
        Returns:
            Self para encadeamento de métodos.
        """
        self.data = load_data(file_path, source_type=source_type)
        return self
    
    def load_data_from_api(self, api_name: str, **kwargs) -> 'HypothesisEngine':
        """
        Carrega dados de uma API pública.
        
        Args:
            api_name: Nome da API ('camara', 'ibge').
            **kwargs: Argumentos específicos para cada API.
        
        Returns:
            Self para encadeamento de métodos.
        
        Example:
            >>> engine = HypothesisEngine()
            >>> engine.load_data_from_api('camara', deputados_limit=100)
        """
        if api_name == 'camara':
            self.data = fetch_camara_deputados(kwargs.get('deputados_limit', 50))
        elif api_name == 'ibge':
            self.data = fetch_ibge_indicadores(
                kwargs.get('indicador', '72'),
                kwargs.get('periodo', '2020')
            )
        else:
            raise ValueError(f"API não suportada: {api_name}")
        
        return self
    
    def load_dataframe(self, df: pd.DataFrame) -> 'HypothesisEngine':
        """
        Carrega dados diretamente de um DataFrame pandas.
        
        Args:
            df: DataFrame com os dados.
        
        Returns:
            Self para encadeamento de métodos.
        """
        self.data = df
        return self
    
    def run_exploratory_analysis(self) -> 'HypothesisEngine':
        """
        Executa análise exploratória nos dados carregados.
        
        Returns:
            Self para encadeamento de métodos.
        
        Raises:
            ValueError: Se não houver dados carregados.
        """
        if self.data is None:
            raise ValueError("Nenhum dado carregado. Use load_data_* primeiro.")
        
        self.exploratory_results = perform_exploratory_analysis(self.data)
        return self
    
    def generate_hypotheses(self, max_hypotheses: int = 5) -> 'HypothesisEngine':
        """
        Gera hipóteses automáticas baseadas na análise exploratória.
        
        Args:
            max_hypotheses: Número máximo de hipóteses para gerar.
        
        Returns:
            Self para encadeamento de métodos.
        
        Raises:
            ValueError: Se a análise exploratória não tiver sido executada.
        """
        if self.exploratory_results is None:
            raise ValueError("Execute a análise exploratória primeiro.")
        
        self.hypotheses = generate_hypotheses(
            self.data,
            self.exploratory_results,
            max_hypotheses=max_hypotheses
        )
        
        return self
    
    def generate_test_plans(self) -> 'HypothesisEngine':
        """
        Gera planos de teste estatístico para cada hipótese.
        
        Returns:
            Self para encadeamento de métodos.
        
        Raises:
            ValueError: Se não houver hipóteses geradas.
        """
        if not self.hypotheses:
            raise ValueError("Gere hipóteses primeiro.")
        
        column_types = self.exploratory_results.get('column_types', {})
        
        self.test_plans = [
            generate_test_plan(hypothesis, self.data, column_types)
            for hypothesis in self.hypotheses
        ]
        
        return self
    
    def run_full_pipeline(self, 
                         max_hypotheses: int = 5,
                         verbose: bool = True) -> 'HypothesisEngine':
        """
        Executa todo o pipeline de análise em uma única chamada.
        
        Args:
            max_hypotheses: Número máximo de hipóteses para gerar.
            verbose: Se True, imprime informações de progresso.
        
        Returns:
            Self para encadeamento de métodos.
        """
        if verbose:
            print("Executando Análise Exploratória...")
        self.run_exploratory_analysis()
        
        if verbose:
            print(f"Gerando até {max_hypotheses} hipóteses...")
        self.generate_hypotheses(max_hypotheses=max_hypotheses)
        
        if verbose:
            print(f"Geração de Planos de Teste...")
        self.generate_test_plans()
        
        if verbose:
            print("Pipeline concluído!")
        
        return self
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo estruturado dos resultados.
        
        Returns:
            Dicionário com resumo completo da análise.
        """
        return {
            'data_shape': self.data.shape if self.data is not None else None,
            'n_columns': len(self.data.columns) if self.data is not None else 0,
            'n_hypotheses': len(self.hypotheses),
            'hypotheses': [h.to_dict() for h in self.hypotheses],
            'test_plans': [tp.to_dict() for tp in self.test_plans]
        }
    
    def generate_report(self, output_format: str = 'text') -> str:
        """
        Gera relatório completo com hipóteses e planos de teste.
        
        Args:
            output_format: Formato do relatório ('text', 'json').
        
        Returns:
            String com o relatório formatado.
        """
        if output_format == 'json':
            return json.dumps(self.get_summary(), indent=2, ensure_ascii=False)
        
        # Formato texto
        report_lines = [
            "=" * 80,
            "RELATÓRIO DO MOTOR DE HIPÓTESE GERATIVA",
            "=" * 80,
            "",
            f"Data de geração: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Tamanho dos dados: {self.data.shape if self.data is not None else 'N/A'}",
            f"Número de colunas: {len(self.data.columns) if self.data is not None else 0}",
            f"Número de hipóteses geradas: {len(self.hypotheses)}",
            "",
            "=" * 80,
            "RESUMO DA ANÁLISE EXPLORATÓRIA",
            "=" * 80,
            ""
        ]
        
        if self.exploratory_results:
            structure = self.exploratory_results.get('structure', {})
            report_lines.extend([
                f"Observações: {structure.get('shape', (0, 0))[0]}",
                f"Variáveis: {structure.get('shape', (0, 0))[1]}",
                f"Linhas duplicadas: {structure.get('duplicate_rows', 0)}",
                "",
                "Tipos de variáveis:",
            ])
            
            column_types = self.exploratory_results.get('column_types', {})
            for type_name, columns in column_types.items():
                if columns:
                    report_lines.append(f"  - {type_name}: {len(columns)} variáveis")
            
            strong_corrs = self.exploratory_results.get('correlations', {}).get('strong_pairs', [])
            if strong_corrs:
                report_lines.extend([
                    "",
                    f"Correlações fortes encontradas: {len(strong_corrs)}",
                ])
        
        report_lines.append("")
        
        # Adiciona hipóteses
        report_lines.append(format_hypotheses_for_report(self.hypotheses))
        report_lines.append("")
        
        # Adiciona planos de teste
        report_lines.append(format_test_plans_for_report(self.test_plans))
        
        return "\n".join(report_lines)
    
    def save_report(self, file_path: str, output_format: str = 'text') -> None:
        """
        Salva o relatório em um arquivo.
        
        Args:
            file_path: Caminho para o arquivo de saída.
            output_format: Formato do relatório ('text', 'json').
        """
        report = self.generate_report(output_format=output_format)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Relatório salvo em: {file_path}")


def main():
    """
    Função principal para demonstração do uso do Motor de Hipótese Gerativa.
    """
    import numpy as np
    
    # Define seed para reprodutibilidade
    np.random.seed(42)
    
    print("=" * 80)
    print("MOTOR DE HIPÓTESE GERATIVA - DEMONSTRAÇÃO")
    print("=" * 80)
    print()
    
    # Cria dados sintéticos para demonstração
    n_samples = 200
    
    data = pd.DataFrame({
        'idade': np.random.normal(35, 10, n_samples).clip(18, 70).astype(int),
        'renda': np.random.exponential(5000, n_samples).astype(int),
        'anos_estudo': np.random.normal(12, 3, n_samples).clip(5, 20).astype(int),
        'horas_trabalho': np.random.normal(40, 10, n_samples).clip(20, 60).astype(int),
        'satisfacao': np.random.randint(1, 6, n_samples),
        'genero': np.random.choice(['Masculino', 'Feminino'], n_samples),
        'regiao': np.random.choice(['Norte', 'Sul', 'Leste', 'Oeste'], n_samples),
        'nivel_educacao': np.random.choice(['Fundamental', 'Médio', 'Superior'], n_samples)
    })
    
    # Adiciona algumas correlações artificiais
    data['renda'] = data['renda'] + data['anos_estudo'] * 500 + np.random.normal(0, 500, n_samples)
    data['satisfacao'] = data['satisfacao'] + (data['horas_trabalho'] < 35).astype(int)
    
    print("Dados sintéticos criados:")
    print(data.head())
    print()
    
    # Inicializa o motor
    engine = HypothesisEngine(random_seed=42)
    
    # Executa pipeline completo
    engine.load_dataframe(data)
    engine.run_full_pipeline(max_hypotheses=5, verbose=True)
    
    print()
    print("=" * 80)
    print("RELATÓRIO COMPLETO")
    print("=" * 80)
    print()
    
    # Gera e imprime relatório
    report = engine.generate_report(output_format='text')
    print(report)
    
    # Salva relatório em JSON
    engine.save_report('relatorio_hipoteses.json', output_format='json')
    
    return engine


if __name__ == '__main__':
    main()
