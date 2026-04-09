"""DataHarvest Streamlit - MVP: Pesquisa e download em lote de arquivos."""

import subprocess
import os
import shlex
import time
from datetime import datetime

import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

st.set_page_config(page_title="DataHarvest", page_icon="📥", layout="wide")

EXTENSIONS = {
    'PDF': '.pdf', 'DOC': '.doc', 'DOCX': '.docx', 'XLS': '.xls',
    'XLSX': '.xlsx', 'PPT': '.ppt', 'PPTX': '.pptx', 'TXT': '.txt',
    'PNG': '.png', 'JPG': '.jpg', 'ZIP': '.zip'
}


def check_wget_installed():
    """Verifica se wget está instalado."""
    try:
        return subprocess.run(["wget", "--version"], capture_output=True, timeout=5).returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def search_files(query, file_types, max_results):
    """Pesquisa arquivos no DuckDuckGo."""
    if not file_types:
        return []
    
    filetype_query = " OR ".join([f"filetype:{ft.lower()}" for ft in file_types])
    full_query = f"{query} ({filetype_query})"
    valid_exts = [EXTENSIONS[ft] for ft in file_types if ft in EXTENSIONS]
    
    results = []
    try:
        with DDGS() as ddgs:
            for result in ddgs.text(full_query, max_results=max_results):
                url = result.get('href', '')
                url_lower = url.lower()
                
                for ext in valid_exts:
                    if url_lower.endswith(ext):
                        filename = os.path.basename(url.split('?')[0]) or f"arquivo_{len(results)+1}{ext}"
                        results.append({
                            "Nome do Arquivo": filename,
                            "URL": url,
                            "Tipo": ext[1:].upper(),
                            "status": "🔍 Detectado"
                        })
                        break
    except RatelimitException:
        st.warning("Serviço temporariamente indisponível. Tente novamente.")
    except Exception as e:
        st.error(f"Erro na busca: {e}")
    
    return results


def download_files(df, download_dir, log_container):
    """Baixa arquivos selecionados com wget."""
    os.makedirs(download_dir, exist_ok=True)
    selected = df[df['Baixar?'] == True]
    
    if selected.empty:
        log_container.write("⚠️ Nenhum arquivo selecionado.")
        return df
    
    log_container.write(f"📁 Pasta: {download_dir} | 📦 Arquivos: {len(selected)}")
    log_container.write("-" * 50)
    
    for idx in selected.index:
        url, filename = df.loc[idx, 'URL'], df.loc[idx, 'Nome do Arquivo']
        df.loc[idx, 'status'] = "⏳ Baixando..."
        log_container.write(f"\n📥 {filename}")
        
        cmd = f"wget -P {shlex.quote(download_dir)} -nc -c --show-progress {shlex.quote(url)}"
        
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output = []
            for line in process.stdout:
                if line.strip():
                    output.append(line.strip())
                    if len(output) > 5:
                        output = output[-5:]
            
            process.wait(timeout=300)
            df.loc[idx, 'status'] = "✅ Concluído" if process.returncode == 0 else "❌ Erro"
            log_container.success(f"   ✅ {filename}") if process.returncode == 0 else log_container.error(f"   ❌ {filename}")
        except Exception as e:
            df.loc[idx, 'status'] = "❌ Erro"
            log_container.error(f"   ❌ {str(e)}")
        
        time.sleep(0.5)
    
    log_container.write("-" * 50)
    log_container.write("🎉 Download finalizado!")
    return df


def init_state():
    """Inicializa session_state."""
    if 'df_results' not in st.session_state:
        st.session_state.df_results = pd.DataFrame(columns=['Nome do Arquivo', 'URL', 'Tipo', 'status', 'Baixar?'])


def render_sidebar():
    """Renderiza sidebar."""
    st.sidebar.header("⚙️ Configurações")
    st.sidebar.text_input("Termo de Busca", placeholder="Ex: relatório 2024 pdf", key="search_term")
    st.sidebar.multiselect("Tipos de Arquivo", options=list(EXTENSIONS.keys()), default=['PDF'], key="file_types")
    st.sidebar.slider("Nº de Links", min_value=10, max_value=200, value=50, step=10, key="max_results")
    st.sidebar.text_input("Pasta de Download", value="./downloads", key="download_dir")
    return st.sidebar.button("🔍 Buscar", type="primary", use_container_width=True)


def render_results(status_placeholder):
    """Renderiza tabela de resultados."""
    status_placeholder.success(f"✅ {len(st.session_state.df_results)} arquivo(s) encontrado(s)!")
    st.dataframe(st.session_state.df_results, use_container_width=True, hide_index=True, column_config={
        "URL": st.column_config.LinkColumn(width="large"),
        "Baixar?": st.column_config.CheckboxColumn(width="small")
    })


def execute_downloads():
    """Executa downloads."""
    download_dir = st.session_state.get('download_dir', './downloads')
    
    if not check_wget_installed():
        st.error("❌ wget não encontrado! Instale: `sudo apt install wget` (Linux) ou `brew install wget` (macOS)")
        st.stop()
    
    log_container = st.empty()
    st.session_state.last_log = f"Iniciando: {datetime.now().strftime('%H:%M:%S')}\n"
    log_container.markdown(f"```{st.session_state.last_log}```")
    
    st.session_state.df_results = download_files(st.session_state.df_results, download_dir, log_container)
    st.success("Downloads concluídos!")


def main():
    """Função principal."""
    init_state()
    
    st.title("📥 DataHarvest")
    st.markdown("Pesquise e baixe arquivos da web de forma simples.")
    status_placeholder = st.empty()
    
    if st.session_state.df_results.empty:
        status_placeholder.info("👈 Configure sua busca na sidebar e clique em 'Buscar'.")
    
    if render_sidebar():
        query = st.session_state.get('search_term', '').strip()
        file_types = st.session_state.get('file_types', [])
        max_results = st.session_state.get('max_results', 50)
        
        if not query:
            status_placeholder.warning("⚠️ Informe um termo de busca.")
        elif not file_types:
            status_placeholder.warning("⚠️ Selecione pelo menos um tipo de arquivo.")
        else:
            status_placeholder.info("🔍 Buscando...")
            results = search_files(query, file_types, max_results)
            
            if results:
                df = pd.DataFrame(results)
                df['Baixar?'] = False
                st.session_state.df_results = df[['Nome do Arquivo', 'URL', 'Tipo', 'status', 'Baixar?']]
                st.rerun()
            else:
                status_placeholder.warning("⚠️ Nenhum arquivo encontrado.")
    
    if not st.session_state.df_results.empty:
        render_results(status_placeholder)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Marcar Todos", use_container_width=True):
                st.session_state.df_results['Baixar?'] = True
                st.rerun()
        with col2:
            if st.button("❌ Desmarcar Todos", use_container_width=True):
                st.session_state.df_results['Baixar?'] = False
                st.rerun()
        
        st.markdown("---")
        if st.button("🚀 Baixar Selecionados", type="primary", use_container_width=True):
            execute_downloads()
        
        with st.expander("📜 Console de Log"):
            if st.session_state.get('last_log'):
                st.code(st.session_state.last_log)


if __name__ == "__main__":
    main()
