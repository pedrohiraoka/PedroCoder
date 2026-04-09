# 🛰️ OrbitGuard

**Validação de Falsos Positivos em Trânsitos Exoplanetários & Priorização de Ocultações Estelares**

OrbitGuard é uma ferramenta científica desenvolvida em Python que cruza dados de exoplanetas (NASA Exoplanet Archive) com efemérides de pequenos corpos (JPL/MPC) para:
1. **Validar falsos positivos** em curvas de luz de trânsitos causados por asteroides/cometas.
2. **Priorizar eventos de ocultação** de estrelas por asteroides que possuem sistemas planetários confirmados.

---

## 🚀 Funcionalidades Principais

### Módulo 1: Validador de Trânsito (Falsos Positivos)
Identifica se um sinal de trânsito detectado em uma curva de luz pode ser causado pela passagem de um asteroide ou cometa no campo de visão (FOV) do telescópio.

- **Entrada:** Nome do alvo (ex: `TIC 12345678`) ou coordenadas `(RA, Dec)` + tempo de observação.
- **Processamento:**
  - Consulta o *NASA Exoplanet Archive* para confirmar existência de planetas.
  - Recupera posições de asteroides numerados via *JPL Horizons*.
  - Calcula separação angular usando `astropy.coordinates`.
  - Busca curvas de luz no *MAST* via `lightkurve`.
- **Saída:** Status (`GREEN`/`RED`), nome do asteroide, magnitude, separação angular e link para a curva de luz.

### Módulo 2: Priorizador de Ocultação
Gera alvos prioritários para campanhas de observação de ocultações estelares.

- **Entrada:** Nome do asteroide/cometa + intervalo de datas.
- **Processamento:**
  - Gera efemérides precisas do corpo menor.
  - Cruza com catálogo *Gaia DR3* para encontrar estrelas de fundo.
  - Filtra estrelas que possuem exoplanetas confirmados (zona habitável, raio, etc.).
- **Saída:** DataFrame ranqueado por prioridade científica.

### Módulo 3: Caçador de Eventos Cruzados (Batch)
Processamento em lote de múltiplos alvos para detecção de eventos simultâneos.

- **Entrada:** Arquivo CSV com colunas `[ra, dec, obs_time_utc]`.
- **Processamento:** Iteração em chunks com processamento paralelo (`concurrent.futures`).
- **Saída:** Tabela interativa no Streamlit e exportação em CSV.

---

## 🛠️ Stack Tecnológica

| Categoria | Tecnologia |
|-----------|------------|
| **Linguagem** | Python 3.10+ |
| **APIs Astronômicas** | `astroquery` (NASAExoplanetArchive, JPLHorizons, Gaia), `sbpy` |
| **Curvas de Luz** | `lightkurve` (TESS/Kepler/K2) |
| **Cálculo Astrométrico** | `astropy`, `skyfield` (opcional) |
| **Data Processing** | `polars` (performance), `pandas`, `sqlite3` |
| **Interface Web** | `streamlit`, `plotly` |
| **CLI** | `typer` ou `click` |
| **Testes** | `pytest`, `logging`, `typing` |

---

## 📦 Instalação

### Pré-requisitos
- Python 3.10 ou superior.
- Acesso à internet para consultas às APIs (na primeira execução).

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/orbitguard.git
   cd orbitguard
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # ou
   .\venv\Scripts\activate   # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Opcional) Configuração via Conda:**
   Se preferir usar `conda`:
   ```bash
   conda env create -f environment.yml
   conda activate orbitguard
   ```

---

## 💻 Uso

### 1. Interface Web (Streamlit)

A maneira mais completa de interagir com o OrbitGuard é através do dashboard.

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente no seu navegador padrão (geralmente em `http://localhost:8501`).

**Funcionalidades da UI:**
- Aba **Validador de Trânsito**: Insira o nome do alvo ou coordenadas.
- Aba **Ocultações**: Selecione um asteroide e veja estrelas com planetas no caminho.
- Aba **Batch Upload**: Carregue um CSV para processamento em massa.

### 2. Linha de Comando (CLI)

Para automação e scripts rápidos:

```bash
# Validar um alvo específico
python cli.py validate --target "TIC 12345678" --time "2023-10-01T12:00:00"

# Buscar ocultações prioritárias
python cli.py occult --asteroid "Ceres" --start "2023-10-01" --end "2023-10-07"

# Processar arquivo batch
python cli.py batch --input events.csv --output results.csv
```

Use `python cli.py --help` para ver todas as opções disponíveis.

### 3. Uso como Biblioteca Python

Você pode importar os módulos diretamente em seus próprios scripts ou notebooks:

```python
from core.validator import TransitValidator
from core.ephemeris import OccultationPrioritizer
from astropy.time import Time

# Exemplo: Validar trânsito
validator = TransitValidator()
resultado = validator.check_target("TIC 12345678", Time("2023-10-01T12:00:00"))
print(resultado.status)  # GREEN ou RED
print(resultado.asteroids_nearby)
```

---

## 📂 Estrutura do Projeto

```text
OrbitGuard/
├── app.py                      # Interface Streamlit principal (Dashboard Web)
├── cli.py                      # Interface de Linha de Comando (Typer CLI)
├── core/                       # Módulos principais do sistema
│   ├── __init__.py            # Exportações do pacote core
│   ├── catalog.py             # Wrapper para APIs (NASA Exoplanet Archive, Lightkurve, JPL Horizons)
│   ├── validator.py           # Módulo 1: Validador de Trânsito (Falsos Positivos)
│   ├── ephemeris.py           # Módulo 2: Cálculo de Efemérides e Ocultações
│   └── cross_match.py         # Módulo 3: Processamento Batch e Detecção de Eventos Cruzados
├── utils/                      # Utilitários e configurações
│   ├── __init__.py            # Exportações do pacote utils
│   ├── cache.py               # Gerenciamento de Cache Local (SQLite/Parquet)
│   └── config.py              # Constantes, Limites de API, Paths
├── tests/                      # Testes Unitários e de Integração
│   ├── __init__.py
│   └── test_core.py           # Testes dos módulos principais
├── notebooks/                  # Prototipagem e Validação de APIs
│   └── __init__.py
├── orbitguard_cache/           # Diretório de Cache (gerado automaticamente)
│   └── catalog_cache.db       # Banco de dados SQLite de cache
├── requirements.txt            # Dependências Python
├── README.md                   # Este arquivo
└── .gitignore                  # Arquivos ignorados pelo Git
```

### Descrição dos Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Dashboard interativo Streamlit com 3 abas (Validador, Ocultações, Batch) |
| `cli.py` | CLI completa com comandos `validate`, `occult`, `batch`, `info`, `clear-cache` |
| `core/catalog.py` | Classes `ExoplanetCatalog`, `LightCurveSearch`, `JPLHorizonsQuery` |
| `core/validator.py` | Classe `TransitValidator` e `ValidationResult` para validação de trânsitos |
| `core/ephemeris.py` | Classes `EphemerisCalculator` e `OccultationPrioritizer` |
| `core/cross_match.py` | Classe `BatchCrossMatcher` para processamento paralelo em lote |
| `utils/cache.py` | Sistema de cache inteligente com TTL e persistência SQLite |
| `utils/config.py` | Configurações globais, limites de API e constantes |

---

## ⚙️ Configuração e Cache

O OrbitGuard implementa um sistema de cache inteligente para reduzir chamadas às APIs e respeitar limites de taxa.

- **Local do Cache:** `./orbitguard_cache/`
- **Formato:** SQLite para metadados e Parquet para catálogos massivos.
- **Validade:** O cache de efemérides expira após 24h por padrão (configurável em `utils/config.py`).

Para limpar o cache manualmente:
```bash
rm -rf orbitguard_cache/*
```

---

## 🧪 Testes

Execute a suíte de testes para verificar a integridade da instalação:

```bash
pytest tests/ -v
```

Os testes cobrem:
- Parsing de coordenadas e tempos.
- Mock de respostas de API (para não depender de conexão durante testes locais).
- Lógica de cruzamento angular.

---

## 📝 Exemplos de Casos de Uso

### Cenário 1: Astrônomo Amateur validando um alerta de trânsito
Você recebeu um alerta de que a estrela `HD 12345` mostrou um mergulho incomum na curva de luz do TESS. Antes de anunciar como candidato a exoplaneta, você quer descartar um asteroide.

1. Abra o OrbitGuard (`streamlit run app.py`).
2. Na aba "Validador", digite `HD 12345`.
3. O sistema retorna: **"ALERTA: Asteroide (4) Vesta passou a 2.3 arcsec do alvo no momento do evento."**
4. Conclusão: O sinal é provavelmente um falso positivo.

### Cenário 2: Planejamento de Campanha de Ocultação
Um observatório quer apontar telescópios para capturar a ocultação de uma estrela por um asteroide, mas quer priorizar estrelas que tenham planetas conhecidos (para tentar detectar atmosferas ou anéis extras).

1. Use a CLI: `python cli.py occult --asteroid "Pallas" --start "2023-11-01" --end "2023-11-30"`
2. O sistema gera uma lista de 50 estrelas no caminho.
3. Filtra e destaca 3 estrelas que possuem exoplanetas na Zona Habitável.
4. Exporte a lista para o planejador de observação.

---

## ⚠️ Limitações Conhecidas

1. **Precisão Posicional:** A precisão depende da qualidade das efemérides do JPL. Para asteroides não numerados, a incerteza pode ser > 1.5 arcsec.
2. **Limites de API:** O NASA Exoplanet Archive e o JPL Horizons possuem limites de requisição. O OrbitGuard implementa *rate limiting*, mas uso intensivo pode causar delays.
3. **Dados de Curva de Luz:** Nem todos os alvos do Exoplanet Archive têm curvas de luz disponíveis no MAST (depende da missão: TESS, Kepler, K2).
4. **Offline:** O modo offline funciona apenas para dados previamente cacheados. Efemérides novas requerem conexão.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir *Issues* ou enviar *Pull Requests*.

1. Faça um Fork do projeto.
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`).
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`).
4. Push para a branch (`git push origin feature/AmazingFeature`).
5. Abra um Pull Request.

Por favor, certifique-se de que seus testes passam (`pytest`) e siga o estilo de código PEP 8.

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- Dados fornecidos pelo **NASA Exoplanet Archive**, parte do Exoplanet Exploration Program.
- Efemérides fornecidas pelo **JPL Horizons System**.
- Curvas de luz fornecidas pelo **MAST Archive** (Space Telescope Science Institute).
- Catálogo estelar **Gaia DR3** (ESA).

---

## 📞 Contato

Desenvolvido por [Seu Nome/Organização].
Dúvidas? Abra uma issue ou envie um email para [seu-email@exemplo.com].
