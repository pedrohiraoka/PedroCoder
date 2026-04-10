"""
VulnScanner MVP - Aplicação de Segurança Digital
Dashboard interativo para análise de vulnerabilidades em aplicações web.

Baseado nas técnicas de pentest descritas no livro 'Hacking com Kali Linux'.

AVISO: Esta ferramenta é apenas para fins educacionais e testes autorizados.
"""

import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Adicionar caminho do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos
from modules.recon import ReconModule
from modules.scanner import ScannerModule
from modules.exploiter import ExploiterModule
from modules.reporter import ReporterModule
from utils.legal import get_legal_warning, get_ethical_guidelines
from utils.logger import logger

# Configuração da página
st.set_page_config(
    page_title="VulnScanner MVP",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .danger-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .severity-critical { color: #dc3545; font-weight: bold; }
    .severity-high { color: #fd7e14; font-weight: bold; }
    .severity-medium { color: #ffc107; font-weight: bold; }
    .severity-low { color: #17a2b8; font-weight: bold; }
    .severity-info { color: #6c757d; }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Inicializa variáveis de sessão."""
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = {}
    if 'scan_completed' not in st.session_state:
        st.session_state.scan_completed = False
    if 'target' not in st.session_state:
        st.session_state.target = ""


def show_header():
    """Exibe cabeçalho da aplicação."""
    st.markdown('<h1 class="main-header">🛡️ VulnScanner MVP</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ferramenta de Análise de Segurança Digital<br>Baseada em técnicas de Pentest</p>', unsafe_allow_html=True)
    st.divider()


def show_legal_warning():
    """Exibe aviso legal e termo de concordância."""
    st.markdown("### ⚠️ Aviso Legal Importante")
    
    with st.expander("Leia os Termos de Uso e Diretrizes Éticas", expanded=True):
        st.markdown(get_legal_warning())
        st.info(get_ethical_guidelines())
    
    return st.checkbox("✅ Li e concordo com os termos. Tenho autorização para testar o alvo especificado.")


def show_input_section():
    """Exibe seção de entrada do usuário."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        target = st.text_input(
            "🎯 Alvo (IP ou Domínio)",
            placeholder="ex: example.com ou 192.168.1.1",
            help="Digite o IP ou domínio do sistema que deseja analisar (apenas sistemas autorizados)"
        )
    
    with col2:
        port_range = st.selectbox(
            "Range de Portas",
            ["1-1000", "1-100", "Common (1-100)", "80,443,8080", "All (1-65535)"],
            index=0,
            help="Selecione o range de portas para scanning"
        )
    
    with col3:
        scan_depth = st.selectbox(
            "Profundidade",
            ["Rápido", "Normal", "Completo"],
            index=1,
            help="Selecione a profundidade da análise"
        )
    
    return target, port_range, scan_depth


def run_scan(target: str, port_range: str, scan_depth: str, progress_bar):
    """
    Executa todos os módulos de scan.
    
    Args:
        target: IP ou domínio do alvo
        port_range: Range de portas
        scan_depth: Profundidade do scan
        progress_bar: Barra de progresso do Streamlit
        
    Returns:
        Dicionário com resultados completos
    """
    results = {}
    total_steps = 4
    
    try:
        # Módulo de Reconhecimento
        progress_bar.progress(1/total_steps, text="🔍 Executando Reconhecimento...")
        logger.info(f"Iniciando módulo de reconhecimento para {target}")
        
        recon = ReconModule()
        results['recon'] = recon.run_all(target)
        
        # Módulo de Scanning
        progress_bar.progress(2/total_steps, text="📡 Executando Scanning de Portas...")
        logger.info(f"Iniciando módulo de scanner para {target}")
        
        scanner = ScannerModule()
        results['scanner'] = scanner.run_all(target, ports=port_range)
        
        # Módulo de Exploração (Simulada)
        progress_bar.progress(3/total_steps, text="🔬 Verificando Vulnerabilidades...")
        logger.info(f"Iniciando módulo de exploração simulada para {target}")
        
        exploiter = ExploiterModule()
        results['exploiter'] = exploiter.run_all(target)
        
        # Completar
        progress_bar.progress(4/total_steps, text="✅ Scan Completo!")
        
        logger.info(f"Scan completo para {target}. Total de vulnerabilidades: {sum(len(r.get('vulnerabilities', [])) for r in results.values())}")
        
        return results
        
    except Exception as e:
        logger.error(f"Erro durante o scan: {str(e)}")
        st.error(f"Erro durante a varredura: {str(e)}")
        return None


def display_executive_summary(results: Dict[str, Any]):
    """Exibe resumo executivo com métricas e gráficos."""
    st.markdown("### 📊 Resumo Executivo")
    
    # Coletar todas as vulnerabilidades
    all_vulns = []
    for module_name in ['recon', 'scanner', 'exploiter']:
        if module_name in results:
            vulns = results[module_name].get('vulnerabilities', [])
            all_vulns.extend(vulns)
    
    # Contar por severidade
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
    for vuln in all_vulns:
        severity = vuln.get('severity', 'INFO')
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Calcular nível de risco
    if severity_counts['CRITICAL'] > 0:
        risk_level = 'CRITICO'
        risk_color = '🔴'
    elif severity_counts['HIGH'] > 0:
        risk_level = 'ALTO'
        risk_color = '🟠'
    elif severity_counts['MEDIUM'] > 0:
        risk_level = 'MEDIO'
        risk_color = '🟡'
    elif severity_counts['LOW'] > 0:
        risk_level = 'BAIXO'
        risk_color = '🔵'
    else:
        risk_level = 'INFORMATIVO'
        risk_color = '⚪'
    
    # Métricas em cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🔴 Críticas", severity_counts['CRITICAL'])
    with col2:
        st.metric("🟠 Altas", severity_counts['HIGH'])
    with col3:
        st.metric("🟡 Médias", severity_counts['MEDIUM'])
    with col4:
        st.metric("🔵 Baixas", severity_counts['LOW'])
    with col5:
        st.metric("⚪ Info", severity_counts['INFO'])
    
    st.divider()
    
    # Gráfico de severidade
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if all_vulns:
            # Preparar dados para gráfico
            severity_data = {k: v for k, v in severity_counts.items() if v > 0}
            
            if severity_data:
                st.markdown("#### Distribuição de Vulnerabilidades por Severidade")
                
                # Gráfico de barras simples usando Streamlit
                chart_data = {
                    'Severidade': list(severity_data.keys()),
                    'Quantidade': list(severity_data.values())
                }
                st.bar_chart(chart_data, x='Severidade', y='Quantidade')
    
    with col2:
        st.markdown("#### Nível de Risco")
        st.markdown(f"<h1 style='text-align: center;'>{risk_color} {risk_level}</h1>", unsafe_allow_html=True)
        
        total_vulns = len(all_vulns)
        st.markdown(f"""
        **Total de Achados:** {total_vulns}
        
        **Status:** {'⚠️ Atenção necessária' if severity_counts['CRITICAL'] + severity_counts['HIGH'] > 0 else '✅ Sem críticas'}
        """)
    
    return severity_counts, risk_level


def display_findings(results: Dict[str, Any]):
    """Exibe lista detalhada de vulnerabilidades encontradas."""
    st.markdown("### 🔍 Descobertas Detalhadas")
    
    # Coletar todas as vulnerabilidades
    all_vulns = []
    for module_name in ['recon', 'scanner', 'exploiter']:
        if module_name in results:
            vulns = results[module_name].get('vulnerabilities', [])
            for vuln in vulns:
                vuln['module'] = module_name
                all_vulns.append(vuln)
    
    if not all_vulns:
        st.info("Nenhuma vulnerabilidade foi encontrada durante a análise.")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filter_severity = st.multiselect(
            "Filtrar por Severidade",
            ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'],
            default=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        )
    with col2:
        filter_module = st.multiselect(
            "Filtrar por Módulo",
            ['recon', 'scanner', 'exploiter'],
            default=['recon', 'scanner', 'exploiter']
        )
    
    # Filtrar vulnerabilidades
    filtered_vulns = [
        v for v in all_vulns 
        if v.get('severity') in filter_severity and v.get('module') in filter_module
    ]
    
    if not filtered_vulns:
        st.warning("Nenhuma vulnerabilidade corresponde aos filtros selecionados.")
        return
    
    # Exibir vulnerabilidades agrupadas por severidade
    severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
    
    for severity in severity_order:
        severity_vulns = [v for v in filtered_vulns if v.get('severity') == severity]
        
        if severity_vulns:
            # Cor do cabeçalho baseada na severidade
            if severity == 'CRITICAL':
                color = '#dc3545'
            elif severity == 'HIGH':
                color = '#fd7e14'
            elif severity == 'MEDIUM':
                color = '#ffc107'
            elif severity == 'LOW':
                color = '#17a2b8'
            else:
                color = '#6c757d'
            
            st.markdown(f"""
            <div style="background-color: {color}; color: white; padding: 0.5rem; border-radius: 5px; margin: 1rem 0;">
                <strong>{severity}</strong> ({len(severity_vulns)} achados)
            </div>
            """, unsafe_allow_html=True)
            
            for vuln in severity_vulns:
                with st.expander(f"[{vuln.get('id', 'N/A')}] {vuln.get('title', 'Sem título')}", expanded=False):
                    st.markdown(f"**Categoria:** {vuln.get('category', 'N/A')}")
                    st.markdown(f"**Descrição:** {vuln.get('description', 'N/A')}")
                    st.markdown(f"**Recomendação:** {vuln.get('recommendation', 'N/A')}")
                    st.code(vuln.get('evidence', 'N/A'), language='text')
                    
                    if 'note' in vuln:
                        st.info(f"ℹ️ {vuln['note']}")


def display_services(results: Dict[str, Any]):
    """Exibe tabela de serviços detectados."""
    st.markdown("### 🖥️ Serviços Detectados")
    
    services = []
    if 'scanner' in results:
        services = results['scanner'].get('services', [])
    
    if not services:
        st.info("Nenhum serviço foi detectado durante o scanning.")
        return
    
    # Criar tabela
    table_data = []
    for service in services:
        table_data.append({
            'Porta': service.get('port', 'N/A'),
            'Protocolo': service.get('protocol', 'N/A'),
            'Serviço': service.get('service', 'N/A'),
            'Versão': service.get('version', '') or service.get('extra_info', '') or 'N/A'
        })
    
    st.table(table_data[:50])  # Limitar a 50 serviços
    
    if len(services) > 50:
        st.info(f"... e mais {len(services) - 50} serviços. Consulte o relatório completo.")


def display_recon_info(results: Dict[str, Any]):
    """Exibe informações de reconhecimento."""
    st.markdown("### 🔎 Informações de Reconhecimento")
    
    if 'recon' not in results:
        st.info("Dados de reconhecimento não disponíveis.")
        return
    
    recon = results['recon']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # WHOIS
        st.markdown("#### 📋 Dados WHOIS")
        whois_data = recon.get('whois', {})
        
        if whois_data and 'error' not in whois_data:
            st.json({
                'Domínio': whois_data.get('domain', 'N/A'),
                'Registrar': whois_data.get('registrar', 'N/A'),
                'Organização': whois_data.get('org', 'N/A'),
                'País': whois_data.get('country', 'N/A'),
                'Data de Criação': str(whois_data.get('creation_date', 'N/A'))[:10],
                'Data de Expiração': str(whois_data.get('expiration_date', 'N/A'))[:10]
            })
        else:
            st.warning("Dados WHOIS não disponíveis.")
    
    with col2:
        # Geolocalização
        st.markdown("#### 🌍 Geolocalização")
        geo_data = recon.get('geolocation', {})
        
        if geo_data and 'error' not in geo_data:
            st.json({
                'IP': geo_data.get('ip', 'N/A'),
                'País': geo_data.get('country', 'N/A'),
                'Região': geo_data.get('region', 'N/A'),
                'Cidade': geo_data.get('city', 'N/A'),
                'ISP': geo_data.get('isp', 'N/A'),
                'Timezone': geo_data.get('timezone', 'N/A')
            })
        else:
            st.warning("Dados de geolocalização não disponíveis.")
    
    # DNS
    st.markdown("#### 📡 Registros DNS")
    dns_data = recon.get('dns', {})
    
    if dns_data and 'error' not in dns_data:
        dns_table = []
        for record_type, records in dns_data.items():
            if records:
                dns_table.append({
                    'Tipo': record_type,
                    'Registros': ', '.join(str(r) for r in records[:5])
                })
        
        if dns_table:
            st.table(dns_table)
        else:
            st.info("Nenhum registro DNS encontrado.")
    else:
        st.warning("Dados DNS não disponíveis.")


def export_reports(results: Dict[str, Any], target: str):
    """Exibe opções de exportação de relatórios."""
    st.markdown("### 📥 Exportar Relatório")
    
    reporter = ReporterModule()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Gerar PDF", use_container_width=True):
            with st.spinner("Gerando relatório PDF..."):
                pdf_path = reporter.generate_pdf_report(results, target)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime='application/pdf'
                        )
                else:
                    st.error("Erro ao gerar PDF. Verifique se a biblioteca fpdf está instalada.")
    
    with col2:
        if st.button("📊 Gerar CSV", use_container_width=True):
            with st.spinner("Gerando relatório CSV..."):
                csv_path = reporter.generate_csv_report(results, target)
                if csv_path and os.path.exists(csv_path):
                    with open(csv_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=f.read(),
                            file_name=os.path.basename(csv_path),
                            mime='text/csv'
                        )
                else:
                    st.error("Erro ao gerar CSV.")
    
    with col3:
        if st.button("📋 Gerar JSON", use_container_width=True):
            with st.spinner("Gerando relatório JSON..."):
                json_path = reporter.generate_json_report(results, target)
                if json_path and os.path.exists(json_path):
                    with open(json_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=f.read(),
                            file_name=os.path.basename(json_path),
                            mime='application/json'
                        )
                else:
                    st.error("Erro ao gerar JSON.")


def main():
    """Função principal da aplicação."""
    initialize_session_state()
    show_header()
    
    # Mostrar aviso legal
    agreed = show_legal_warning()
    
    if not agreed:
        st.warning("⚠️ Você precisa concordar com os termos para usar esta ferramenta.")
        st.stop()
    
    st.success("✅ Termos aceitos. Você pode prosseguir com a análise.")
    st.divider()
    
    # Seção de entrada
    target, port_range, scan_depth = show_input_section()
    
    # Botão de iniciar scan
    col1, col2 = st.columns([1, 4])
    with col1:
        start_scan = st.button("🚀 Iniciar Varredura", type="primary", use_container_width=True)
    
    # Executar scan
    if start_scan and target:
        if not target.strip():
            st.error("Por favor, digite um IP ou domínio válido.")
        else:
            target = target.strip()
            logger.info(f"Iniciando scan para: {target}")
            
            # Barra de progresso
            progress_bar = st.progress(0, text="Iniciando varredura...")
            
            # Executar scan
            results = run_scan(target, port_range, scan_depth, progress_bar)
            
            if results:
                st.session_state.scan_results = results
                st.session_state.scan_completed = True
                st.session_state.target = target
                
                st.success(f"✅ Varredura concluída para {target}!")
                
                # Exibir resultados
                display_executive_summary(results)
                st.divider()
                
                display_findings(results)
                st.divider()
                
                display_services(results)
                st.divider()
                
                display_recon_info(results)
                st.divider()
                
                export_reports(results, target)
    
    elif start_scan and not target:
        st.error("Por favor, digite um IP ou domínio para iniciar a varredura.")
    
    # Rodapé
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🛡️ VulnScanner MVP - Ferramenta Educacional de Segurança</p>
        <p>Use apenas em sistemas autorizados. Os desenvolvedores não se responsabilizam por uso indevido.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
