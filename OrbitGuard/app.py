"""
OrbitGuard - Interface Streamlit Principal.

Dashboard interativo para validação de falsos positivos em trânsitos de exoplanetas
e priorização de ocultações estelares por asteroides e cometas.

Usage:
    streamlit run app.py

Features:
    - Validador de Trânsito (Módulo 1)
    - Priorizador de Ocultação (Módulo 2)
    - Processamento Batch (Módulo 3)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import json

from core.validator import TransitValidator, ValidationResult
from core.ephemeris import EphemerisCalculator, OccultationPrioritizer
from core.cross_match import BatchCrossMatcher, CrossMatchResult
from utils.cache import CacheManager
from utils.config import Config, config

# Configuração da página
st.set_page_config(
    page_title="OrbitGuard - Validador de Trânsitos e Ocultações",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicialização do cache
cache_manager = CacheManager()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-green {
        color: #28a745;
        font-weight: bold;
    }
    .status-red {
        color: #dc3545;
        font-weight: bold;
    }
    .status-yellow {
        color: #ffc107;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Inicializa o estado da sessão do Streamlit."""
    if "validation_results" not in st.session_state:
        st.session_state.validation_results = []
    if "occultation_results" not in st.session_state:
        st.session_state.occultation_results = []
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = []
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "validator"


def render_header():
    """Renderiza o cabeçalho principal da aplicação."""
    st.markdown('<h1 class="main-header">🔭 OrbitGuard</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Validador de Falsos Positivos e Priorizador de Ocultações Estelares</p>',
        unsafe_allow_html=True,
    )
    st.divider()


def render_validator_tab():
    """Renderiza a aba do Validador de Trânsito (Módulo 1)."""
    st.header("🔍 Módulo 1: Validador de Trânsito")
    st.markdown(
        "Cruza dados de exoplanetas confirmados com posições de asteroides para identificar "
        "possíveis falsos positivos em observações de trânsito."
    )

    # Colunas para input
    col1, col2 = st.columns([2, 1])

    with col1:
        input_method = st.radio(
            "Método de Entrada:",
            ["Nome do Hospedeiro (ex: TIC, KOI, Kepler)", "Coordenadas (RA, Dec)"],
            horizontal=True,
        )

        if "Nome do Hospedeiro" in input_method:
            hostname = st.text_input(
                "Nome do Hospedeiro:",
                placeholder="Ex: TIC 12345678, KOI-1234, Kepler-186",
                help="Identificador do alvo no NASA Exoplanet Archive",
            )
            ra, dec = None, None
        else:
            col_ra, col_dec = st.columns(2)
            with col_ra:
                ra = st.number_input(
                    "Ascensão Reta (graus):",
                    min_value=0.0,
                    max_value=360.0,
                    value=0.0,
                    step=0.0001,
                )
            with col_dec:
                dec = st.number_input(
                    "Declinação (graus):",
                    min_value=-90.0,
                    max_value=90.0,
                    value=0.0,
                    step=0.0001,
                )
            hostname = None

    with col2:
        obs_date = st.date_input(
            "Data da Observação (UTC):",
            value=datetime.utcnow().date(),
            help="Data e hora da observação do trânsito",
        )
        obs_time = st.time_input(
            "Hora da Observação (UTC):",
            value=datetime.utcnow().time(),
        )
        separation_threshold = st.slider(
            "Limiar de Separação (arcsec):",
            min_value=0.1,
            max_value=10.0,
            value=5.0,
            step=0.1,
            help="Distância angular máxima para considerar cruzamento",
        )

    # Botão de execução
    col_btn1, col_btn2, col_btn3 = st.columns([1, 4, 1])
    with col_btn2:
        run_validation = st.button(
            "🚀 Executar Validação", type="primary", use_container_width=True
        )

    if run_validation:
        try:
            with st.spinner("Consultando NASA Exoplanet Archive e JPL Horizons..."):
                # Combina data e hora
                obs_datetime = datetime.combine(obs_date, obs_time)

                # Inicializa o validador
                validator = TransitValidator(cache_manager=cache_manager)

                # Executa a validação
                if hostname:
                    result = validator.validate_by_hostname(
                        hostname=hostname,
                        obs_time=obs_datetime,
                        separation_threshold_arcsec=separation_threshold,
                    )
                elif ra is not None and dec is not None:
                    result = validator.validate_by_coordinates(
                        ra=ra,
                        dec=dec,
                        obs_time=obs_datetime,
                        separation_threshold_arcsec=separation_threshold,
                    )
                else:
                    st.error("Por favor, forneça um nome de hospedeiro ou coordenadas.")
                    return

                # Armazena o resultado
                st.session_state.validation_results.append(result)

                # Renderiza os resultados
                render_validation_result(result)

        except Exception as e:
            st.error(f"❌ Erro durante a validação: {str(e)}")
            st.exception(e)


def render_validation_result(result: ValidationResult):
    """Renderiza os resultados da validação de trânsito."""
    st.subheader("📊 Resultados da Validação")

    # Status card
    status_color = {
        "GREEN": "status-green",
        "RED": "status-red",
        "YELLOW": "status-yellow",
    }.get(result.status, "")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Status",
            value=result.status,
            delta=None,
        )
    with col2:
        st.metric(
            label="Planetas Confirmados",
            value=len(result.confirmed_planets) if result.confirmed_planets else 0,
        )
    with col3:
        st.metric(
            label="Asteroides Próximos",
            value=len(result.asteroids) if result.asteroids else 0,
        )

    # Detalhes do alerta
    if result.status == "RED":
        st.warning(
            f"⚠️ **ALERTA**: Possível falso positivo detectado! "
            f"Asteroide {result.asteroids[0]['name']} está a "
            f"{result.asteroids[0]['separation_arcsec']:.2f} arcsec do alvo."
        )

    # Tabela de planetas
    if result.confirmed_planets:
        st.markdown("### 🪐 Planetas Confirmados")
        planets_df = pd.DataFrame(result.confirmed_planets)
        st.dataframe(
            planets_df,
            use_container_width=True,
            hide_index=True,
        )

    # Tabela de asteroides
    if result.asteroids:
        st.markdown("### ☄️ Asteroides no Campo de Visão")
        asteroids_df = pd.DataFrame(result.asteroids)
        st.dataframe(
            asteroids_df,
            use_container_width=True,
            hide_index=True,
        )

        # Gráfico de separação
        if len(result.asteroids) > 1:
            fig = px.scatter(
                asteroids_df,
                x="name",
                y="separation_arcsec",
                size="magnitude",
                color="magnitude",
                labels={
                    "name": "Asteroide",
                    "separation_arcsec": "Separação (arcsec)",
                    "magnitude": "Magnitude",
                },
                title="Separação Angular dos Asteroides",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Curva de luz
    if result.lightcurve_available:
        st.markdown("### 📈 Curva de Luz Disponível")
        if result.lightcurve_url:
            st.link_button(
                "🔗 Acessar Curva de Luz no MAST",
                result.lightcurve_url,
            )
    else:
        st.info("ℹ️ Curva de luz não disponível para este alvo.")

    # JSON export
    with st.expander("📄 Exportar Resultado (JSON)"):
        st.json(result.to_dict())


def render_occultation_tab():
    """Renderiza a aba do Priorizador de Ocultação (Módulo 2)."""
    st.header("🌟 Módulo 2: Priorizador de Ocultação")
    st.markdown(
        "Identifica estrelas de fundo no caminho de ocultação de asteroides/cometas "
        "e prioriza aquelas com exoplanetas confirmados."
    )

    # Input do alvo
    col1, col2 = st.columns([2, 1])

    with col1:
        target_name = st.text_input(
            "Nome do Alvo (Asteroide/Cometa):",
            placeholder="Ex: 1 Ceres, 2 Pallas, 1P/Halley",
            help="Designação do pequeno corpo no JPL Horizons",
        )

    with col2:
        date_range = st.date_input(
            "Intervalo de Datas (UTC):",
            value=[datetime.utcnow().date(), datetime.utcnow().date() + timedelta(days=30)],
            help="Período para buscar eventos de ocultação",
        )

    # Parâmetros avançados
    with st.expander("⚙️ Parâmetros Avançados"):
        col_mag, col_dist = st.columns(2)
        with col_mag:
            max_mag = st.slider(
                "Magnitude Máxima da Estrela:",
                min_value=8.0,
                max_value=20.0,
                value=15.0,
                step=0.5,
            )
        with col_dist:
            max_distance = st.slider(
                "Distância Máxima do Caminho (arcsec):",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1,
            )

    # Botão de execução
    run_occultation = st.button("🔭 Buscar Ocultações", type="primary")

    if run_occultation:
        if not target_name:
            st.error("Por favor, forneça o nome do alvo.")
            return

        try:
            with st.spinner(
                f"Calculando efemérides para {target_name} e cruzando com catálogos..."
            ):
                # Inicializa o priorizador
                prioritizer = OccultationPrioritizer(cache_manager=cache_manager)

                # Executa a busca
                results = prioritizer.find_occultations(
                    target_name=target_name,
                    date_start=date_range[0],
                    date_end=date_range[1],
                    max_magnitude=max_mag,
                    max_separation_arcsec=max_distance,
                )

                # Armazena os resultados
                st.session_state.occultation_results = results

                # Renderiza os resultados
                render_occultation_results(results)

        except Exception as e:
            st.error(f"❌ Erro durante a busca de ocultações: {str(e)}")
            st.exception(e)


def render_occultation_results(results: list[Dict[str, Any]]):
    """Renderiza os resultados da busca de ocultações."""
    st.subheader("📋 Eventos de Ocultação Encontrados")

    if not results:
        st.info("ℹ️ Nenhum evento de ocultação encontrado para os parâmetros fornecidos.")
        return

    # Métricas resumidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Eventos", len(results))
    with col2:
        stars_with_planets = sum(1 for r in results if r.get("has_exoplanet", False))
        st.metric("Estrelas com Exoplanetas", stars_with_planets)
    with col3:
        avg_priority = sum(r.get("priority_score", 0) for r in results) / len(results)
        st.metric("Prioridade Média", f"{avg_priority:.2f}")

    # Tabela de resultados
    st.markdown("### 📊 Tabela de Eventos")
    results_df = pd.DataFrame(results)

    # Ordena por prioridade
    if "priority_score" in results_df.columns:
        results_df = results_df.sort_values("priority_score", ascending=False)

    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
    )

    # Gráfico de prioridades
    if "priority_score" in results_df.columns and len(results_df) > 1:
        fig = px.bar(
            results_df.head(20),
            x="star_name",
            y="priority_score",
            color="has_exoplanet",
            labels={
                "star_name": "Estrela",
                "priority_score": "Score de Prioridade",
                "has_exoplanet": "Tem Exoplaneta",
            },
            title="Top 20 Eventos por Prioridade",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Exportação
    with st.expander("💾 Exportar Resultados"):
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Baixar como CSV",
            data=csv,
            file_name=f"occultation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        json_str = json.dumps(results, indent=2)
        st.download_button(
            label="📥 Baixar como JSON",
            data=json_str,
            file_name=f"occultation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


def render_batch_tab():
    """Renderiza a aba de Processamento Batch (Módulo 3)."""
    st.header("📦 Módulo 3: Processamento Batch")
    st.markdown(
        "Processa múltiplos alvos simultaneamente a partir de um arquivo CSV "
        "para detecção de eventos cruzados em larga escala."
    )

    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "📁 Upload de Arquivo CSV",
        type=["csv"],
        help="CSV deve conter colunas: ra, dec, obs_time_utc (ou hostname)",
    )

    # Ou input manual
    st.markdown("**Ou insira dados manualmente:**")
    batch_data = st.text_area(
        "Dados CSV (ra, dec, obs_time_utc):",
        placeholder="ra,dec,obs_time_utc\n180.123,-45.678,2024-01-15T10:30:00\n...",
        height=150,
    )

    # Parâmetros de processamento
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.slider(
            "Tamanho do Chunk:",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="Número de linhas processadas por vez",
        )
    with col2:
        max_workers = st.slider(
            "Workers Paralelos:",
            min_value=1,
            max_value=8,
            value=4,
            step=1,
        )

    # Botão de execução
    run_batch = st.button("🚀 Processar Batch", type="primary")

    if run_batch:
        # Determina a fonte de dados
        data_source = None
        if uploaded_file:
            try:
                data_source = pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"Erro ao ler arquivo CSV: {str(e)}")
                return
        elif batch_data:
            try:
                from io import StringIO

                data_source = pd.read_csv(StringIO(batch_data))
            except Exception as e:
                st.error(f"Erro ao parsear dados CSV: {str(e)}")
                return
        else:
            st.warning("Por favor, faça upload de um CSV ou insira dados manualmente.")
            return

        # Valida colunas necessárias
        required_cols = {"ra", "dec", "obs_time_utc"}
        if not required_cols.issubset(data_source.columns):
            st.error(
                f"CSV deve conter as colunas: {', '.join(required_cols)}. "
                f"Colunas encontradas: {', '.join(data_source.columns)}"
            )
            return

        try:
            with st.spinner(f"Processando {len(data_source)} alvos..."):
                # Barra de progresso
                progress_bar = st.progress(0)

                # Inicializa o processador batch
                batch_matcher = BatchCrossMatcher(
                    cache_manager=cache_manager, max_workers=max_workers
                )

                # Processa em chunks
                all_results = []
                total_chunks = (len(data_source) // chunk_size) + 1

                for i in range(0, len(data_source), chunk_size):
                    chunk = data_source.iloc[i : i + chunk_size]
                    chunk_results = batch_matcher.process_chunk(chunk)
                    all_results.extend(chunk_results)

                    # Atualiza progresso
                    current_chunk = (i // chunk_size) + 1
                    progress_bar.progress(min(current_chunk / total_chunks, 1.0))

                # Armazena resultados
                st.session_state.batch_results = all_results

                # Renderiza resultados
                render_batch_results(all_results)

        except Exception as e:
            st.error(f"❌ Erro durante processamento batch: {str(e)}")
            st.exception(e)


def render_batch_results(results: list[CrossMatchResult]):
    """Renderiza os resultados do processamento batch."""
    st.subheader("📊 Resultados do Processamento Batch")

    if not results:
        st.info("ℹ️ Nenhum evento cruzado encontrado.")
        return

    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Processado", len(results))
    with col2:
        events_found = sum(1 for r in results if r.has_cross_match)
        st.metric("Eventos Cruzados", events_found)
    with col3:
        red_alerts = sum(1 for r in results if r.status == "RED")
        st.metric("Alertas Vermelhos", red_alerts)

    # Tabela de resultados
    st.markdown("### 📋 Tabela de Eventos Cruzados")

    # Converte para DataFrame
    results_data = [r.to_dict() for r in results]
    results_df = pd.DataFrame(results_data)

    # Filtra apenas eventos com cross-match
    if "has_cross_match" in results_df.columns:
        filtered_df = results_df[results_df["has_cross_match"]]
    else:
        filtered_df = results_df

    if len(filtered_df) > 0:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
        )

        # Gráfico de distribuição
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            if "status" in filtered_df.columns:
                fig = px.pie(
                    filtered_df,
                    names="status",
                    title="Distribuição de Status",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            if "separation_arcsec" in filtered_df.columns:
                fig = px.histogram(
                    filtered_df,
                    x="separation_arcsec",
                    nbins=20,
                    title="Distribuição de Separação Angular",
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum evento cruzado detectado nos dados processados.")

    # Exportação
    with st.expander("💾 Exportar Resultados Batch"):
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Baixar como CSV",
            data=csv,
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def render_about_tab():
    """Renderiza a aba Sobre."""
    st.header("ℹ️ Sobre o OrbitGuard")

    st.markdown(
        """
        ### 🔭 OrbitGuard - Validador de Falsos Positivos e Priorizador de Ocultações

        O **OrbitGuard** é uma ferramenta científica desenvolvida para auxiliar astrônomos
        na validação de sinais de trânsito de exoplanetas e na identificação de oportunidades
        de ocultação estelar por pequenos corpos do Sistema Solar.

        #### Funcionalidades Principais:

        1. **Validador de Trânsito (Módulo 1)**
           - Cruza dados do NASA Exoplanet Archive com efemérides do JPL Horizons
           - Identifica asteroides que podem causar falsos positivos em observações de trânsito
           - Fornece alertas em tempo real com status GREEN/YELLOW/RED

        2. **Priorizador de Ocultação (Módulo 2)**
           - Calcula efemérides precisas de asteroides e cometas
           - Identifica estrelas de fundo no caminho de ocultação (catálogo Gaia DR3)
           - Prioriza eventos envolvendo estrelas com exoplanetas confirmados

        3. **Processamento Batch (Módulo 3)**
           - Processa centenas de alvos simultaneamente
           - Suporte a arquivos CSV e entrada manual de dados
           - Exportação de resultados em CSV e JSON

        #### Stack Tecnológico:

        - **Python 3.10+** com tipagem rigorosa
        - **astroquery** para APIs astronômicas (NASA, JPL, Gaia)
        - **lightkurve** para curvas de luz TESS/Kepler
        - **sbpy** + **astropy** para cálculos de efemérides
        - **polars/pandas** para processamento de dados
        - **streamlit** + **plotly** para visualização interativa

        #### Limitações Conhecidas:

        - Precisão posicional limitada a ~1.5 arcsec para asteroides numerados
        - Dependência de conectividade para consultas em tempo real
        - Cache local pode ocupar espaço significativo para grandes volumes de dados

        #### Créditos:

        Dados fornecidos por:
        - NASA Exoplanet Archive
        - JPL Horizons System
        - ESA Gaia Mission
        - MAST Archive (Lightkurve)
        """
    )

    # Links úteis
    st.markdown(
        """
        ### 🔗 Links Úteis

        - [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
        - [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/)
        - [ESA Gaia](https://www.cosmos.esa.int/web/gaia)
        - [MAST Archive](https://mast.stsci.edu/)
        - [GitHub do OrbitGuard](https://github.com/orbitguard)
        """
    )


def main():
    """Função principal da aplicação Streamlit."""
    # Inicializa estado da sessão
    initialize_session_state()

    # Renderiza cabeçalho
    render_header()

    # Navegação por abas
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🔍 Validador de Trânsito",
            "🌟 Ocultações",
            "📦 Processamento Batch",
            "ℹ️ Sobre",
        ]
    )

    with tab1:
        render_validator_tab()

    with tab2:
        render_occultation_tab()

    with tab3:
        render_batch_tab()

    with tab4:
        render_about_tab()

    # Footer
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            OrbitGuard v0.1.0 | Desenvolvido para a comunidade astronômica | 
            Dados sujeitos aos termos das APIs originais
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
