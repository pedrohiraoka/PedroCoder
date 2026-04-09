# Motor de Hipótese Gerativa e Testes Automatizados

Um MVP (Produto Viável Mínimo) que serve como um "Motor de Hipótese Gerativa". O sistema recebe um conjunto de dados e gera automaticamente hipóteses plausíveis baseadas em relações estatísticas ou padrões identificados nos dados. Em seguida, sugere testes estatísticos apropriados, planos de amostragem e métricas de sucesso para validar ou refutar cada hipótese gerada.

## Funcionalidades

- **Ingestão de Dados**: Leitura de CSV, JSON e APIs públicas (IBGE, Câmara dos Deputados)
- **Análise Exploratória Inicial (AEI)**: Estrutura dos dados, correlações, outliers
- **Geração Automática de Hipóteses**: 3-5 hipóteses plausíveis baseadas em padrões estatísticos
- **Sugestão de Testes Estatísticos**: Teste-t, ANOVA, Qui-quadrado, Spearman, etc.
- **Planos de Amostragem**: Cálculo de tamanho de amostra e métodos recomendados
- **Métricas de Sucesso**: Critérios claros para validação das hipóteses
- **Relatórios**: Saída em texto ou JSON

## Instalação

```bash
pip install -r requirements.txt
```

## Uso Básico

### Pipeline Completo com Dados Sintéticos

```python
from src.main import HypothesisEngine
import pandas as pd
import numpy as np

# Criar dados de exemplo
np.random.seed(42)
data = pd.DataFrame({
    'idade': np.random.normal(35, 10, 200),
    'renda': np.random.exponential(5000, 200),
    'anos_estudo': np.random.normal(12, 3, 200),
    'genero': np.random.choice(['M', 'F'], 200)
})

# Executar pipeline completo
engine = HypothesisEngine(random_seed=42)
engine.load_dataframe(data)
engine.run_full_pipeline(max_hypotheses=5)

# Gerar relatório
report = engine.generate_report(output_format='text')
print(report)

# Salvar em JSON
engine.save_report('relatorio.json', output_format='json')
```

### Carregar Dados de API Pública

```python
from src.main import HypothesisEngine

# Dados da Câmara dos Deputados
engine = HypothesisEngine()
engine.load_data_from_api('camara', deputados_limit=100)
engine.run_full_pipeline()
print(engine.generate_report())
```

### Carregar Arquivo Local

```python
from src.main import HypothesisEngine

engine = HypothesisEngine()
engine.load_data_from_file('meus_dados.csv', source_type='csv')
engine.run_full_pipeline()
```

## Estrutura do Projeto

```
/workspace
├── src/
│   ├── __init__.py           # Pacote principal
│   ├── data_ingestion.py     # Ingestão de dados (CSV, JSON, APIs)
│   ├── exploratory_analysis.py # Análise exploratória
│   ├── hypothesis_generation.py # Geração de hipóteses
│   ├── test_suggestion.py    # Sugestão de testes estatísticos
│   └── main.py               # Motor principal (HypothesisEngine)
├── tests/
│   └── test_hypothesis_engine.py # Testes unitários
├── data/                     # Diretório para dados locais
├── requirements.txt          # Dependências
└── README.md                 # Este arquivo
```

## Executar Testes

```bash
pytest tests/test_hypothesis_engine.py -v
```

## Critérios de Aceitação Atendidos

- ✅ Conecta com fontes de dados públicas (APIs IBGE, Câmara)
- ✅ Lê e realiza AEI básica nos dados
- ✅ Gera automaticamente 3-5 hipóteses plausíveis
- ✅ Associa teste estatístico, plano de amostragem e métrica a cada hipótese
- ✅ Produz relatório legível (texto/JSON)
- ✅ Inclui 37 testes unitários cobrindo lógica central
- ✅ Código versionado em Git com estrutura clara

## Exemplo de Hipótese Gerada

```
Hipótese #1
----------------------------------------
Descrição: A variável 'renda' está positivamente correlacionada 
           com 'anos_estudo' (correlação = 0.623, força: moderada).
Variável 1: renda
Variável 2: anos_estudo
Tipo de Relação: correlation
Força Observada: 0.623

TESTE SUGERIDO:
  Nome: Teste de Correlação de Spearman
  Pressupostos: Variáveis ordinais, relação monotônica
  
PLANO DE AMOSTRAGEM:
  Método: Amostragem Aleatória Simples
  Tamanho Recomendado: 64
  
MÉTRICAS DE SUCESSO:
  Métrica Primária: Coeficiente de correlação (r)
  Limiar: |r| > 0.5 para efeito moderado
```

## Licença

MIT License
