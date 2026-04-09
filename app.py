"""
DataHarvest Streamlit - MVP
Aplicação web local para pesquisa e download em lote de arquivos.
"""

import subprocess
import os
import shlex
import time
from datetime import datetime

import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException


# ============================================================================
# CONFIGURAÇÃO INICIAL DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="DataHarvest Streamlit",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização customizada
st.markdown("""
<style>
    .stDataFrame { font-size: 14px; }
    .status-detectado { color: #1f77b4; }
    .status-baixando { color: #ff7f0e; }
    .status-concluido { color: #2ca02c; }
    .status-erro { color: #d62728; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNÇÕES DE BACKEND
# ============================================================================

def check_wget_installed() -> bool:
    """
    Verifica se o wget está instalado no sistema.
    
    Returns:
        bool: True se wget estiver disponível, False caso contrário.
    """
    try:
        result = subprocess.run(
            ["wget", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def search_duckduckgo_files(query: str, file_types: list, max_results: int) -> list:
    """
    Pesquisa arquivos específicos usando DuckDuckGo Search.
    
    Args:
        query: Termo de busca principal.
        file_types: Lista de extensões de arquivo para filtrar.
        max_results: Número máximo de resultados para retornar.
    
    Returns:
        list: Lista de dicionários com informações dos arquivos encontrados.
    """
    if not file_types:
        return []
    
    # Monta a query com filetype filters
    filetype_query = " OR ".join([f"filetype:{ft.lower()}" for ft in file_types])
    full_query = f"{query} ({filetype_query})"
    
    # Mapeamento de extensões
    extension_map = {
        'PDF': '.pdf', 'DOC': '.doc', 'DOCX': '.docx',
        'XLS': '.xls', 'XLSX': '.xlsx', 'PPT': '.ppt',
        'PPTX': '.pptx', 'TXT': '.txt', 'PNG': '.png',
        'JPG': '.jpg', 'ZIP': '.zip'
    }
    
    valid_extensions = [extension_map[ft] for ft in file_types if ft in extension_map]
    
    results = []
    
    try:
        with DDGS() as ddgs:
            # Busca resultados
            search_results = list(ddgs.text(full_query, max_results=max_results))
            
            for result in search_results:
                url = result.get('href', '')
                title = result.get('title', 'Sem título')
                
                # Filtro crítico: verifica se URL termina com extensão válida
                url_lower = url.lower()
                file_type = None
                
                for ext in valid_extensions:
                    if url_lower.endswith(ext):
                        file_type = ext.upper().replace('.', '')
                        break
                
                if file_type and url:
                    # Extrai nome do arquivo da URL
                    filename = os.path.basename(url.split('?')[0])
                    if not filename:
                        filename = f"arquivo_{len(results) + 1}.{file_type.lower()}"
                    
                    results.append({
                        "filename": filename,
                        "url": url,
                        "type": file_type,
                        "status": "🔍 Detectado"
                    })
                    
    except RatelimitException:
        st.warning("Serviço temporariamente indisponível. Tente novamente em alguns instantes.")
    except Exception as e:
        st.error(f"Erro na busca: {str(e)}")
    
    return results


def download_selected_files(df: pd.DataFrame, download_dir: str, log_container) -> pd.DataFrame:
    """
    Baixa arquivos selecionados usando wget.
    
    Args:
        df: DataFrame contendo os resultados da busca.
        download_dir: Diretório de destino para downloads.
        log_container: Container Streamlit para logs em tempo real.
    
    Returns:
        pd.DataFrame: DataFrame atualizado com status dos downloads.
    """
    # Garante que o diretório existe
    os.makedirs(download_dir, exist_ok=True)
    
    # Filtra arquivos selecionados
    selected_mask = df['Baixar?'] == True
    selected_indices = df[selected_mask].index.tolist()
    
    if not selected_indices:
        log_container.write("⚠️ Nenhum arquivo selecionado para download.")
        return df
    
    log_container.write(f"📁 Pasta de download: {download_dir}")
    log_container.write(f"📦 Total de arquivos para baixar: {len(selected_indices)}")
    log_container.write("-" * 50)
    
    for idx in selected_indices:
        url = df.loc[idx, 'URL']
        filename = df.loc[idx, 'Nome do Arquivo']
        
        # Atualiza status para "baixando"
        df.loc[idx, 'status'] = "⏳ Baixando..."
        
        log_container.write(f"\n📥 Iniciando: {filename}")
        log_container.write(f"   URL: {url}")
        
        # Monta comando wget com segurança (shlex.quote previne injeção)
        safe_url = shlex.quote(url)
        safe_dir = shlex.quote(download_dir)
        cmd = f"wget -P {safe_dir} -nc -c --show-progress {safe_url}"
        
        try:
            # Executa wget capturando saída
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            for line in process.stdout:
                if line.strip():
                    output_lines.append(line.strip())
                    # Mostra apenas últimas linhas para não sobrecarregar
                    if len(output_lines) > 5:
                        output_lines = output_lines[-5:]
            
            process.wait(timeout=300)  # Timeout de 5 minutos por arquivo
            
            if process.returncode == 0:
                df.loc[idx, 'status'] = "✅ Concluído"
                log_container.success(f"   ✅ Download concluído: {filename}")
            else:
                df.loc[idx, 'status'] = "❌ Erro"
                log_container.error(f"   ❌ Erro no download (código {process.returncode}): {filename}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            df.loc[idx, 'status'] = "❌ Erro"
            log_container.error(f"   ❌ Timeout no download: {filename}")
        except Exception as e:
            df.loc[idx, 'status'] = "❌ Erro"
            log_container.error(f"   ❌ Erro inesperado: {str(e)}")
        
        # Pequena pausa entre downloads
        time.sleep(0.5)
    
    log_container.write("-" * 50)
    log_container.write("🎉 Processo de download finalizado!")
    
    return df


# ============================================================================
# INTERFACE DO USUÁRIO (UI)
# ============================================================================

def render_sidebar():
    """Renderiza a sidebar com configurações de busca."""
    st.sidebar.header("⚙️ Configurações da Busca")
    
    search_term = st.sidebar.text_input(
        "Termo de Busca",
        placeholder="Ex: relatório financeiro 2024 pdf",
        key="search_term"
    )
    
    file_types = st.sidebar.multiselect(
        "Tipos de Arquivo",
        options=['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 'TXT', 'PNG', 'JPG', 'ZIP'],
        default=['PDF'],
        key="file_types"
    )
    
    max_results = st.sidebar.slider(
        "Nº de Links para Analisar",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        key="max_results"
    )
    
    download_dir = st.sidebar.text_input(
        "Pasta de Download",
        value="./downloads",
        key="download_dir"
    )
    
    search_button = st.sidebar.button("🔍 Buscar e Preparar Downloads", type="primary", use_container_width=True)
    
    return search_button


def render_main_area():
    """Renderiza a área principal com resultados e ações."""
    st.title("📥 DataHarvest Streamlit")
    st.markdown("Pesquise e baixe arquivos específicos da web de forma segura e organizada.")
    
    # Placeholder para mensagens de status
    status_placeholder = st.empty()
    
    # Inicializa session_state se necessário
    if 'df_results' not in st.session_state:
        st.session_state.df_results = pd.DataFrame(columns=[
            'Nome do Arquivo', 'URL', 'Tipo', 'status', 'Baixar?'
        ])
        status_placeholder.info("👈 Use a sidebar para configurar sua busca e clique em 'Buscar e Preparar Downloads'.")
    
    # Exibe DataFrame se houver resultados
    if not st.session_state.df_results.empty:
        display_results_table(status_placeholder)
        
        # Botões de ação em lote
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Marcar Todos", use_container_width=True):
                st.session_state.df_results['Baixar?'] = True
                st.rerun()
        
        with col2:
            if st.button("❌ Desmarcar Todos", use_container_width=True):
                st.session_state.df_results['Baixar?'] = False
                st.rerun()
        
        # Botão de download em lote
        st.markdown("---")
        if st.button("🚀 Baixar Selecionados (Wget)", type="primary", use_container_width=True):
            execute_downloads()
        
        # Console de Log
        st.markdown("---")
        with st.expander("📜 Console de Log", expanded=False):
            if 'download_log' not in st.session_state:
                st.session_state.download_log = ""
            log_container = st.container()
            st.session_state.log_container = log_container
            if st.session_state.get('last_log', ''):
                log_container.markdown(f"```\n{st.session_state.last_log}\n```")
    
    return status_placeholder


def display_results_table(status_placeholder):
    """Exibe a tabela de resultados."""
    status_placeholder.success(f"✅ {len(st.session_state.df_results)} arquivo(s) encontrado(s)!")
    
    df = st.session_state.df_results.copy()
    
    # Configura display do DataFrame
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nome do Arquivo": st.column_config.TextColumn(width="medium"),
            "URL": st.column_config.LinkColumn(width="large"),
            "Tipo": st.column_config.TextColumn(width="small"),
            "status": st.column_config.TextColumn(width="small"),
            "Baixar?": st.column_config.CheckboxColumn(width="small")
        }
    )


def execute_downloads():
    """Executa o download dos arquivos selecionados."""
    download_dir = st.session_state.get('download_dir', './downloads')
    
    # Verifica wget antes de iniciar
    if not check_wget_installed():
        st.error("""
        ### ❌ wget não encontrado!
        
        Para usar esta funcionalidade, instale o wget no seu sistema:
        
        **Linux (Debian/Ubuntu):**
        ```bash
        sudo apt-get install wget
        ```
        
        **Linux (RedHat/CentOS):**
        ```bash
        sudo yum install wget
        ```
        
        **macOS (com Homebrew):**
        ```bash
        brew install wget
        ```
        
        **Windows:**
        - Baixe em: https://eternallybored.org/misc/wget/
        - Ou use Chocolatey: `choco install wget`
        """)
        st.stop()
    
    # Cria container para logs
    log_container = st.empty()
    st.session_state.log_container = log_container
    
    # Inicializa log
    st.session_state.last_log = f"Iniciando downloads em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    log_container.markdown(f"```\n{st.session_state.last_log}```")
    
    # Executa downloads
    st.session_state.df_results = download_selected_files(
        st.session_state.df_results,
        download_dir,
        log_container
    )
    
    # Atualiza log final
    st.session_state.last_log += "\nProcesso finalizado!"
    log_container.markdown(f"```\n{st.session_state.last_log}```")
    
    st.success("Downloads concluídos! Verifique o console de log para detalhes.")


# ============================================================================
# LÓGICA PRINCIPAL
# ============================================================================

def main():
    """Função principal que controla o fluxo da aplicação."""
    
    # Renderiza sidebar e obtém ação do usuário
    search_clicked = render_sidebar()
    
    # Renderiza área principal
    status_placeholder = render_main_area()
    
    # Processa busca se botão foi clicado
    if search_clicked:
        search_term = st.session_state.get('search_term', '')
        file_types = st.session_state.get('file_types', [])
        max_results = st.session_state.get('max_results', 50)
        download_dir = st.session_state.get('download_dir', './downloads')
        
        if not search_term.strip():
            status_placeholder.warning("⚠️ Por favor, informe um termo de busca.")
            return
        
        if not file_types:
            status_placeholder.warning("⚠️ Selecione pelo menos um tipo de arquivo.")
            return
        
        status_placeholder.info("🔍 Buscando arquivos... Aguarde.")
        
        # Executa busca
        results = search_duckduckgo_files(search_term, file_types, max_results)
        
        if results:
            # Cria DataFrame com resultados
            df = pd.DataFrame(results)
            df.rename(columns={'filename': 'Nome do Arquivo'}, inplace=True)
            df['Baixar?'] = False  # Coluna de checkbox
            
            # Reordena colunas
            df = df[['Nome do Arquivo', 'URL', 'Tipo', 'status', 'Baixar?']]
            
            st.session_state.df_results = df
            status_placeholder.success(f"✅ {len(results)} arquivo(s) encontrado(s)!")
            st.rerun()
        else:
            status_placeholder.warning("⚠️ Nenhum arquivo encontrado para os critérios informados.")
            st.session_state.df_results = pd.DataFrame(columns=[
                'Nome do Arquivo', 'URL', 'Tipo', 'status', 'Baixar?'
            ])


if __name__ == "__main__":
    main()
