"""
Módulo de Relatórios
Gera relatórios em PDF e CSV com os resultados das varreduras.
Baseado no modelo do livro 'Hacking com Kali Linux'.
"""

import os
import csv
import json
from typing import Dict, List, Any
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

from utils.logger import logger


class ReporterModule:
    """
    Módulo para geração de relatórios de segurança.
    Produz relatórios nos formatos PDF e CSV.
    """
    
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
    def generate_pdf_report(self, scan_results: Dict[str, Any], target: str) -> str:
        """
        Gera relatório em PDF completo.
        
        Args:
            scan_results: Resultados completos do scan
            target: Alvo da varredura
            
        Returns:
            Caminho do arquivo PDF gerado
        """
        if not FPDF_AVAILABLE:
            logger.error("FPDF não disponível. Não foi possível gerar PDF.")
            return ""
        
        try:
            logger.info(f"Gerando relatório PDF para: {target}")
            
            pdf = SecurityReportPDF()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"security_report_{target.replace('.', '_').replace(':', '_')}_{timestamp}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Adicionar conteúdo ao PDF
            self._add_cover_page(pdf, target, scan_results)
            self._add_executive_summary(pdf, scan_results)
            self._add_methodology(pdf)
            self._add_findings(pdf, scan_results)
            self._add_services(pdf, scan_results)
            self._add_recommendations(pdf, scan_results)
            self._add_appendix(pdf, scan_results)
            
            # Salvar PDF
            pdf.output(filepath)
            
            logger.info(f"Relatório PDF gerado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            return ""
    
    def generate_csv_report(self, scan_results: Dict[str, Any], target: str) -> str:
        """
        Gera relatório em CSV com vulnerabilidades.
        
        Args:
            scan_results: Resultados completos do scan
            target: Alvo da varredura
            
        Returns:
            Caminho do arquivo CSV gerado
        """
        try:
            logger.info(f"Gerando relatório CSV para: {target}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vulnerabilities_{target.replace('.', '_').replace(':', '_')}_{timestamp}.csv"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Coletar todas as vulnerabilidades
            all_vulnerabilities = []
            
            for module_name in ['recon', 'scanner', 'exploiter']:
                if module_name in scan_results:
                    vulns = scan_results[module_name].get('vulnerabilities', [])
                    for vuln in vulns:
                        vuln['source_module'] = module_name
                        all_vulnerabilities.append(vuln)
            
            # Escrever CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'Severity', 'Category', 'Title', 'Description', 
                             'Recommendation', 'Evidence', 'Source Module']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for vuln in all_vulnerabilities:
                    writer.writerow({
                        'ID': vuln.get('id', 'N/A'),
                        'Severity': vuln.get('severity', 'N/A'),
                        'Category': vuln.get('category', 'N/A'),
                        'Title': vuln.get('title', 'N/A'),
                        'Description': vuln.get('description', 'N/A'),
                        'Recommendation': vuln.get('recommendation', 'N/A'),
                        'Evidence': vuln.get('evidence', 'N/A'),
                        'Source Module': vuln.get('source_module', 'N/A')
                    })
            
            logger.info(f"Relatório CSV gerado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar CSV: {str(e)}")
            return ""
    
    def generate_json_report(self, scan_results: Dict[str, Any], target: str) -> str:
        """
        Gera relatório em JSON completo.
        
        Args:
            scan_results: Resultados completos do scan
            target: Alvo da varredura
            
        Returns:
            Caminho do arquivo JSON gerado
        """
        try:
            logger.info(f"Gerando relatório JSON para: {target}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scan_results_{target.replace('.', '_').replace(':', '_')}_{timestamp}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            report_data = {
                'report_metadata': {
                    'target': target,
                    'generated_at': datetime.now().isoformat(),
                    'tool': 'VulnScanner MVP',
                    'version': '1.0.0'
                },
                'scan_results': scan_results,
                'summary': self._generate_summary(scan_results)
            }
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(report_data, jsonfile, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Relatório JSON gerado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar JSON: {str(e)}")
            return ""
    
    def _generate_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resumo consolidado dos resultados."""
        total_vulns = 0
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        
        for module_name in ['recon', 'scanner', 'exploiter']:
            if module_name in scan_results:
                vulns = scan_results[module_name].get('vulnerabilities', [])
                total_vulns += len(vulns)
                
                for vuln in vulns:
                    severity = vuln.get('severity', 'INFO')
                    if severity in severity_counts:
                        severity_counts[severity] += 1
        
        return {
            'total_vulnerabilities': total_vulns,
            'by_severity': severity_counts,
            'risk_level': self._calculate_risk_level(severity_counts)
        }
    
    def _calculate_risk_level(self, severity_counts: Dict[str, int]) -> str:
        """Calcula nível de risco baseado nas severidades."""
        if severity_counts['CRITICAL'] > 0:
            return 'CRITICAL'
        elif severity_counts['HIGH'] > 0:
            return 'HIGH'
        elif severity_counts['MEDIUM'] > 0:
            return 'MEDIUM'
        elif severity_counts['LOW'] > 0:
            return 'LOW'
        else:
            return 'INFORMATIONAL'
    
    def _add_cover_page(self, pdf: 'SecurityReportPDF', target: str, scan_results: Dict[str, Any]) -> None:
        """Adiciona página de capa ao PDF."""
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 20, 'Relatório de Segurança', ln=True, align='C')
        
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 15, f'Alvo: {target}', ln=True, align='C')
        
        pdf.set_font('Arial', 'I', 12)
        pdf.cell(0, 10, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', ln=True, align='C')
        
        pdf.cell(0, 10, 'VulnScanner MVP - Ferramenta de Análise de Segurança', ln=True, align='C')
        
        # Informações do scan
        pdf.ln(20)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Informações do Scan:', ln=True)
        
        pdf.set_font('Arial', '', 11)
        summary = self._generate_summary(scan_results)
        pdf.cell(0, 8, f'Total de Vulnerabilidades: {summary["total_vulnerabilities"]}', ln=True)
        pdf.cell(0, 8, f'Nível de Risco: {summary["risk_level"]}', ln=True)
        
        # Aviso legal
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(0, 6, 'Este relatório é confidencial e destinado apenas ao proprietário do sistema testado.\nO uso destas informações deve seguir as diretrizes éticas de segurança.')
    
    def _add_executive_summary(self, pdf: 'SecurityReportPDF', scan_results: Dict[str, Any]) -> None:
        """Adiciona sumário executivo."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '1. Sumário Executivo', ln=True)
        
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, '''
Este relatório apresenta os resultados da análise de segurança realizada no alvo especificado.
A avaliação seguiu metodologias baseadas em práticas de pentest descritas na literatura especializada.

OBJETIVO:
Identificar vulnerabilidades e pontos de melhoria na segurança do sistema analisado.

METODOLOGIA:
- Reconhecimento passivo (WHOIS, DNS, Geolocalização)
- Scanning de portas e serviços
- Verificação de configurações de segurança HTTP
- Detecção de arquivos sensíveis expostos
- Verificação de possíveis vulnerabilidades comuns

VISÃO GERAL DOS ACHADOS:
''')
        
        summary = self._generate_summary(scan_results)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, f'Nível de Risco Geral: {summary["risk_level"]}', ln=True)
        
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f'Total de Vulnerabilidades: {summary["total_vulnerabilities"]}', ln=True)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Distribuição por Severidade:', ln=True)
        
        pdf.set_font('Arial', '', 11)
        for severity, count in summary['by_severity'].items():
            if count > 0:
                pdf.cell(0, 7, f'  • {severity}: {count}', ln=True)
    
    def _add_methodology(self, pdf: 'SecurityReportPDF') -> None:
        """Adiciona seção de metodologia."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '2. Metodologia', ln=True)
        
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, '''
A análise foi conduzida seguindo as fases do ciclo de vida de pentest:

FASE 1 - RECONHECIMENTO:
Coleta de informações públicas sobre o alvo, incluindo:
- Consulta WHOIS para dados de registro
- Lookup DNS para registros públicos
- Geolocalização do IP
- Google Hacking para informações expostas

FASE 2 - SCANNING:
Varredura ativa para identificar serviços e configurações:
- Scan de portas (Nmap)
- Fingerprinting de serviços
- Detecção de tecnologias web
- Verificação de headers de segurança HTTP

FASE 3 - VERIFICAÇÃO DE VULNERABILIDADES:
Análise de possíveis pontos fracos:
- Verificação de arquivos sensíveis expostos
- Detecção de possíveis backdoors
- Verificação de configurações inseguras
- Análise de diretórios expostos

LIMITAÇÕES:
Esta ferramenta realiza verificações passivas e simuladas. Nenhum exploit ativo foi executado.
Os resultados devem ser validados manualmente por profissionais qualificados.''')
    
    def _add_findings(self, pdf: 'SecurityReportPDF', scan_results: Dict[str, Any]) -> None:
        """Adiciona descobertas técnicas."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '3. Descobertas Técnicas', ln=True)
        
        pdf.set_font('Arial', '', 11)
        
        # Coletar todas as vulnerabilidades
        all_vulns = []
        for module_name in ['recon', 'scanner', 'exploiter']:
            if module_name in scan_results:
                vulns = scan_results[module_name].get('vulnerabilities', [])
                all_vulns.extend(vulns)
        
        if not all_vulns:
            pdf.multi_cell(0, 7, '\nNenhuma vulnerabilidade significativa foi encontrada durante a análise.')
            return
        
        # Agrupar por severidade
        by_severity = {}
        for vuln in all_vulns:
            severity = vuln.get('severity', 'INFO')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(vuln)
        
        # Ordenar por severidade (CRITICAL primeiro)
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        
        for severity in severity_order:
            if severity in by_severity and by_severity[severity]:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, f'{severity} ({len(by_severity[severity])})', ln=True)
                
                # Cor baseada na severidade
                if severity == 'CRITICAL':
                    pdf.set_text_color(255, 0, 0)
                elif severity == 'HIGH':
                    pdf.set_text_color(255, 128, 0)
                elif severity == 'MEDIUM':
                    pdf.set_text_color(255, 255, 0)
                else:
                    pdf.set_text_color(0, 0, 0)
                
                for vuln in by_severity[severity][:10]:  # Limitar a 10 por severidade
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, f'[{vuln.get("id", "N/A")}] {vuln.get("title", "Sem título")}', ln=True)
                    
                    pdf.set_font('Arial', '', 10)
                    pdf.multi_cell(0, 6, f'Descrição: {vuln.get("description", "N/A")}')
                    pdf.multi_cell(0, 6, f'Recomendação: {vuln.get("recommendation", "N/A")}')
                    pdf.ln(3)
                
                pdf.set_text_color(0, 0, 0)
                
                if len(by_severity[severity]) > 10:
                    pdf.cell(0, 7, f'... e mais {len(by_severity[severity]) - 10} vulnerabilidades de {severity}. Ver relatório JSON completo.', ln=True)
    
    def _add_services(self, pdf: 'SecurityReportPDF', scan_results: Dict[str, Any]) -> None:
        """Adiciona lista de serviços detectados."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '4. Serviços Detectados', ln=True)
        
        pdf.set_font('Arial', '', 11)
        
        services = []
        if 'scanner' in scan_results:
            services = scan_results['scanner'].get('services', [])
        
        if not services:
            pdf.multi_cell(0, 7, '\nNenhum serviço foi detectado durante o scanning.')
            return
        
        pdf.multi_cell(0, 7, f'Total de serviços detectados: {len(services)}\n')
        
        pdf.set_font('Arial', 'B', 11)
        
        # Cabeçalho da tabela
        pdf.cell(20, 8, 'Porta', 1)
        pdf.cell(25, 8, 'Protocolo', 1)
        pdf.cell(50, 8, 'Serviço', 1)
        pdf.cell(80, 8, 'Versão/Info', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 10)
        
        for service in services[:20]:  # Limitar a 20 serviços
            port = str(service.get('port', 'N/A'))
            protocol = service.get('protocol', 'N/A')
            service_name = service.get('service', 'N/A')
            version = service.get('version', '') or service.get('extra_info', '') or 'N/A'
            
            # Truncar versão se muito longa
            if len(version) > 75:
                version = version[:72] + '...'
            
            pdf.cell(20, 7, port, 1)
            pdf.cell(25, 7, protocol, 1)
            pdf.cell(50, 7, service_name, 1)
            pdf.cell(80, 7, version, 1)
            pdf.ln()
        
        if len(services) > 20:
            pdf.ln(3)
            pdf.cell(0, 7, f'... e mais {len(services) - 20} serviços. Ver relatório JSON completo.', ln=True)
    
    def _add_recommendations(self, pdf: 'SecurityReportPDF', scan_results: Dict[str, Any]) -> None:
        """Adiciona ações recomendadas."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '5. Ações Recomendadas', ln=True)
        
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, '''
Com base nas vulnerabilidades identificadas, recomendamos as seguintes ações prioritárias:

PRIORIDADE ALTA (Imediato):
''')
        
        # Coletar recomendações de vulnerabilidades CRITICAL e HIGH
        high_priority_recs = set()
        
        for module_name in ['recon', 'scanner', 'exploiter']:
            if module_name in scan_results:
                vulns = scan_results[module_name].get('vulnerabilities', [])
                for vuln in vulns:
                    if vuln.get('severity') in ['CRITICAL', 'HIGH']:
                        rec = vuln.get('recommendation', '')
                        if rec:
                            high_priority_recs.add(rec)
        
        pdf.set_font('Arial', '', 10)
        for i, rec in enumerate(list(high_priority_recs)[:5], 1):
            pdf.multi_cell(0, 6, f'{i}. {rec}\n')
        
        if not high_priority_recs:
            pdf.cell(0, 7, 'Nenhuma ação de alta prioridade identificada.', ln=True)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'RECOMENDAÇÕES GERAIS:', ln=True)
        
        pdf.set_font('Arial', '', 10)
        general_recs = [
            'Mantenha todos os sistemas e softwares atualizados com os últimos patches de segurança.',
            'Implemente políticas de senhas fortes e autenticação multifator onde possível.',
            'Configure adequadamente firewalls e grupos de segurança.',
            'Realize auditorias de segurança regularmente.',
            'Monitore logs e implemente sistema de detecção de intrusão.',
            'Treine a equipe em práticas de segurança cibernética.',
            'Desenvolva e teste um plano de resposta a incidentes.'
        ]
        
        for rec in general_recs:
            pdf.multi_cell(0, 6, f'• {rec}')
    
    def _add_appendix(self, pdf: 'SecurityReportPDF', scan_results: Dict[str, Any]) -> None:
        """Adiciona apêndices com informações técnicas."""
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, '6. Apêndices', ln=True)
        
        pdf.set_font('Arial', '', 11)
        
        # Informações de Reconhecimento
        if 'recon' in scan_results:
            recon = scan_results['recon']
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'A. Dados de Reconhecimento', ln=True)
            
            pdf.set_font('Arial', '', 10)
            
            # WHOIS
            whois_data = recon.get('whois', {})
            if whois_data and 'error' not in whois_data:
                pdf.multi_cell(0, 6, '\nInformações WHOIS:')
                pdf.cell(0, 6, f'Domínio: {whois_data.get("domain", "N/A")}', ln=True)
                pdf.cell(0, 6, f'Registrar: {whois_data.get("registrar", "N/A")}', ln=True)
                pdf.cell(0, 6, f'País: {whois_data.get("country", "N/A")}', ln=True)
            
            # DNS
            dns_data = recon.get('dns', {})
            if dns_data and 'error' not in dns_data:
                pdf.multi_cell(0, 6, '\nRegistros DNS encontrados:')
                for record_type, records in dns_data.items():
                    if records:
                        pdf.cell(0, 6, f'{record_type}: {", ".join(str(r) for r in records[:3])}', ln=True)
            
            # Geolocalização
            geo_data = recon.get('geolocation', {})
            if geo_data and 'error' not in geo_data:
                pdf.multi_cell(0, 6, '\nGeolocalização:')
                pdf.cell(0, 6, f'IP: {geo_data.get("ip", "N/A")}', ln=True)
                pdf.cell(0, 6, f'Local: {geo_data.get("city", "")}, {geo_data.get("country", "")}', ln=True)
                pdf.cell(0, 6, f'ISP: {geo_data.get("isp", "N/A")}', ln=True)
        
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(0, 6, '\n--- Fim do Relatório ---\n\nPara informações completas e detalhadas, consulte os arquivos JSON e CSV gerados.')


class SecurityReportPDF(FPDF):
    """Classe personalizada para PDF com cabeçalho e rodapé."""
    
    def header(self):
        """Adiciona cabeçalho em cada página."""
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'VulnScanner MVP - Relatório de Segurança - Gerado em {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(3)
    
    def footer(self):
        """Adiciona rodapé em cada página."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 1, 'C')
