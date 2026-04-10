"""
Módulo de Scanning
Realiza varredura de portas, fingerprinting de serviços e detecção de tecnologias.
"""

import socket
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

import requests
from bs4 import BeautifulSoup

from utils.logger import logger


class ScannerModule:
    """
    Módulo de scanning para detecção de portas abertas, serviços e vulnerabilidades.
    Baseado nas técnicas descritas em 'Hacking com Kali Linux'.
    """
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.vulnerabilities: List[Dict[str, Any]] = []
        self.services: List[Dict[str, Any]] = []
        
    def run_all(self, target: str, ports: str = "1-1000") -> Dict[str, Any]:
        """
        Executa todas as técnicas de scanning.
        
        Args:
            target: IP ou domínio do alvo
            ports: Range de portas para scan (ex: "1-1000", "80,443,8080")
            
        Returns:
            Dicionário com todos os resultados
        """
        logger.info(f"Iniciando scanning para: {target} (portas: {ports})")
        
        self.results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'ports': {},
            'services': [],
            'http_headers': {},
            'technologies': [],
            'vulnerabilities': []
        }
        
        # Executar módulos de scanning
        self._nmap_scan(target, ports)
        self._http_scan(target)
        self._check_http_headers(target)
        self._detect_directories(target)
        
        self.results['vulnerabilities'] = self.vulnerabilities
        self.results['services'] = self.services
        logger.info(f"Scanning concluído. {len(self.services)} serviços, {len(self.vulnerabilities)} vulnerabilidades.")
        
        return self.results
    
    def _resolve_target(self, target: str) -> Optional[str]:
        """
        Resolve um domínio para IP.
        
        Args:
            target: Domínio ou IP
            
        Returns:
            IP resolvido ou None se falhar
        """
        try:
            socket.inet_aton(target)
            return target
        except socket.error:
            try:
                ip = socket.gethostbyname(target)
                logger.info(f"Domínio {target} resolvido para IP: {ip}")
                return ip
            except socket.gaierror:
                logger.error(f"Não foi possível resolver: {target}")
                return None
    
    def _nmap_scan(self, target: str, ports: str = "1-1000") -> None:
        """
        Realiza scan de portas usando python-nmap.
        
        Args:
            target: IP ou domínio do alvo
            ports: Range de portas
        """
        if not NMAP_AVAILABLE:
            logger.warning("Biblioteca 'python-nmap' não disponível. Pulando Nmap scan.")
            self.results['ports'] = {'error': 'Biblioteca python-nmap não instalada'}
            return
        
        try:
            logger.info(f"Executando Nmap scan em {target} (portas: {ports})")
            
            nm = nmap.PortScanner()
            nm.scan(hosts=target, ports=ports, arguments='-sV -T4')
            
            ports_data = {}
            
            for host in nm.all_hosts():
                ports_data['host'] = host
                ports_data['state'] = nm[host].state()
                ports_data['open_ports'] = []
                
                for proto in nm[host].all_protocols():
                    port_list = nm[host][proto].keys()
                    
                    for port in port_list:
                        port_info = nm[host][proto][port]
                        port_data = {
                            'port': port,
                            'protocol': proto,
                            'state': port_info.get('state', 'unknown'),
                            'service': port_info.get('name', 'unknown'),
                            'version': port_info.get('version', ''),
                            'product': port_info.get('product', ''),
                            'extrainfo': port_info.get('extrainfo', '')
                        }
                        
                        ports_data['open_ports'].append(port_data)
                        
                        # Adicionar à lista de serviços
                        if port_info.get('state') == 'open':
                            self.services.append({
                                'port': port,
                                'protocol': proto,
                                'service': port_info.get('name', 'unknown'),
                                'version': f"{port_info.get('product', '')} {port_info.get('version', '')}".strip(),
                                'extra_info': port_info.get('extrainfo', '')
                            })
                            
                            # Verificar vulnerabilidades baseadas em serviços
                            self._check_service_vulns(port, port_info)
            
            self.results['ports'] = ports_data
            logger.info(f"Nmap scan concluído. {len(ports_data.get('open_ports', []))} portas abertas encontradas.")
            
        except Exception as e:
            logger.error(f"Erro no Nmap scan: {str(e)}")
            self.results['ports'] = {'error': str(e)}
    
    def _check_service_vulns(self, port: int, port_info: Dict) -> None:
        """
        Verifica vulnerabilidades conhecidas baseadas no serviço detectado.
        
        Args:
            port: Número da porta
            port_info: Informações do serviço
        """
        service_name = port_info.get('name', '').lower()
        product = port_info.get('product', '').lower()
        version = port_info.get('version', '')
        
        # Verificar serviços com versões antigas ou inseguras
        if service_name in ['ftp', 'telnet']:
            self.vulnerabilities.append({
                'id': f'SVC-{port:05d}',
                'severity': 'HIGH',
                'category': 'Insecure Service',
                'title': f'Serviço Inseguro Detectado na Porta {port}',
                'description': f'O serviço {service_name.upper()} usa comunicação não criptografada.',
                'recommendation': f'Substitua {service_name.upper()} por uma alternativa segura (ex: SFTP para FTP, SSH para Telnet).',
                'evidence': f"Porta {port}: {service_name} ({product} {version})"
            })
        
        # Verificar MySQL exposto
        if service_name == 'mysql' or 'mysql' in product:
            self.vulnerabilities.append({
                'id': f'SVC-{port:05d}',
                'severity': 'MEDIUM',
                'category': 'Database Exposure',
                'title': 'MySQL Exposto na Rede',
                'description': 'Servidor MySQL está acessível na rede. Verifique se isso é intencional.',
                'recommendation': 'Restrinja o acesso do MySQL apenas a IPs necessários. Use firewall e autenticação forte.',
                'evidence': f"Porta {port}: MySQL ({version})"
            })
        
        # Verificar Redis exposto
        if service_name == 'redis' or 'redis' in product:
            self.vulnerabilities.append({
                'id': f'SVC-{port:05d}',
                'severity': 'HIGH',
                'category': 'Database Exposure',
                'title': 'Redis Exposto na Rede',
                'description': 'Servidor Redis está acessível na rede. Redis frequentemente não tem autenticação por padrão.',
                'recommendation': 'Configure autenticação no Redis e restrinja o acesso via firewall.',
                'evidence': f"Porta {port}: Redis ({version})"
            })
        
        # Verificar SMB/NetBIOS
        if service_name in ['netbios-ssn', 'microsoft-ds', 'smb']:
            self.vulnerabilities.append({
                'id': f'SVC-{port:05d}',
                'severity': 'MEDIUM',
                'category': 'File Sharing',
                'title': 'Compartilhamento de Arquivos Windows Detectado',
                'description': 'Serviços SMB/NetBIOS estão ativos. Podem ser alvo de ataques como EternalBlue.',
                'recommendation': 'Desabilite SMBv1, mantenha o sistema atualizado e restrinja acesso via firewall.',
                'evidence': f"Porta {port}: {service_name} ({version})"
            })
    
    def _http_scan(self, target: str) -> None:
        """
        Realiza scan HTTP para detectar tecnologias e informações.
        
        Args:
            target: IP ou domínio do alvo
        """
        http_ports = [80, 443, 8080, 8443, 8000]
        
        for port in http_ports:
            for protocol in ['http', 'https']:
                if protocol == 'https' and port == 80:
                    continue
                if protocol == 'http' and port == 443:
                    continue
                
                url = f"{protocol}://{target}:{port}" if port not in [80, 443] else f"{protocol}://{target}"
                
                try:
                    logger.info(f"Tentando conexão HTTP em: {url}")
                    response = requests.get(url, timeout=5, verify=False)
                    
                    # Detectar tecnologias
                    technologies = self._detect_technologies(response)
                    
                    if technologies:
                        self.results['technologies'].extend(technologies)
                    
                    # Verificar se é um servidor web válido
                    if response.status_code < 500:
                        self.vulnerabilities.append({
                            'id': f'HTTP-{port:05d}',
                            'severity': 'INFO',
                            'category': 'Web Server',
                            'title': f'Servidor Web Detectado na Porta {port}',
                            'description': f'Servidor {protocol.upper()} respondendo na porta {port}. Status: {response.status_code}',
                            'recommendation': 'Verifique configurações de segurança do servidor web e mantenha-o atualizado.',
                            'evidence': f"URL: {url}, Status: {response.status_code}, Server: {response.headers.get('Server', 'N/A')}"
                        })
                    
                    break  # Se conseguiu conectar, não tentar outros protocolos
                    
                except requests.exceptions.RequestException:
                    continue
                except Exception:
                    continue
    
    def _detect_technologies(self, response: requests.Response) -> List[Dict[str, Any]]:
        """
        Detecta tecnologias usadas no site.
        
        Args:
            response: Resposta HTTP
            
        Returns:
            Lista de tecnologias detectadas
        """
        technologies = []
        headers = response.headers
        body = response.text.lower()
        
        # Detectar pelo header Server
        server = headers.get('Server', '')
        if server:
            technologies.append({
                'name': 'Web Server',
                'value': server,
                'source': 'HTTP Header - Server'
            })
        
        # Detectar X-Powered-By
        powered_by = headers.get('X-Powered-By', '')
        if powered_by:
            technologies.append({
                'name': 'X-Powered-By',
                'value': powered_by,
                'source': 'HTTP Header - X-Powered-By'
            })
            
            # Verificar versões antigas do PHP
            if 'PHP' in powered_by:
                match = re.search(r'PHP/(\d+\.\d+)', powered_by)
                if match:
                    version = float(match.group(1))
                    if version < 7.4:
                        self.vulnerabilities.append({
                            'id': 'TECH-001',
                            'severity': 'HIGH',
                            'category': 'Outdated Software',
                            'title': 'Versão Antiga do PHP Detectada',
                            'description': f'O servidor está usando PHP versão {version}, que pode ter vulnerabilidades conhecidas.',
                            'recommendation': 'Atualize para a versão mais recente do PHP (8.x recomendado).',
                            'evidence': f"X-Powered-By: {powered_by}"
                        })
        
        # Detectar CMS pelo conteúdo
        cms_patterns = {
            'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
            'Joomla': ['joomla', 'components/com_', 'media/jui'],
            'Drupal': ['drupal', 'sites/default/files', 'Drupal.settings'],
            'Magento': ['mage', 'magento', 'varien'],
            'Shopify': ['shopify', 'cdn.shopify'],
            'WooCommerce': ['woocommerce', 'woo-commerce']
        }
        
        for cms, patterns in cms_patterns.items():
            if any(pattern in body for pattern in patterns):
                technologies.append({
                    'name': 'CMS',
                    'value': cms,
                    'source': 'HTML Content Analysis'
                })
                
                # CMS desatualizados podem ser vulneráveis
                self.vulnerabilities.append({
                    'id': 'CMS-001',
                    'severity': 'INFO',
                    'category': 'CMS Detection',
                    'title': f'{cms} Detectado',
                    'description': f'O site parece usar {cms} como sistema de gerenciamento de conteúdo.',
                    'recommendation': f'Mantenha o {cms} e todos os plugins/themes atualizados. Verifique se há patches de segurança pendentes.',
                    'evidence': f"Padrões encontrados no HTML indicando {cms}"
                })
                break
        
        # Detectar frameworks JavaScript
        js_patterns = {
            'React': ['react', 'react-dom'],
            'Angular': ['angular', 'ng-'],
            'Vue.js': ['vue', 'vuejs'],
            'jQuery': ['jquery', 'jquery.']
        }
        
        for framework, patterns in js_patterns.items():
            if any(pattern in body for pattern in patterns):
                technologies.append({
                    'name': 'JavaScript Framework',
                    'value': framework,
                    'source': 'HTML Content Analysis'
                })
        
        return technologies
    
    def _check_http_headers(self, target: str) -> None:
        """
        Verifica cabeçalhos HTTP de segurança.
        
        Args:
            target: IP ou domínio do alvo
        """
        security_headers = {
            'Strict-Transport-Security': 'HSTS não configurado. Dados podem ser transmitidos sem criptografia.',
            'X-Content-Type-Options': 'Cabeçalho ausente. Vulnerável a MIME type sniffing.',
            'X-Frame-Options': 'Cabeçalho ausente. Vulnerável a clickjacking.',
            'X-XSS-Protection': 'Proteção XSS do navegador não está forçada.',
            'Content-Security-Policy': 'CSP não configurado. Maior risco de XSS e injection attacks.',
            'Referrer-Policy': 'Política de referrer não definida. Informações podem vazar via Referer header.',
            'Permissions-Policy': 'Permissões do navegador não estão restritas.'
        }
        
        urls_to_check = [
            f"http://{target}",
            f"https://{target}"
        ]
        
        for url in urls_to_check:
            try:
                logger.info(f"Verificando headers de segurança em: {url}")
                response = requests.get(url, timeout=5, verify=False)
                
                missing_headers = []
                
                for header, description in security_headers.items():
                    if header not in response.headers:
                        missing_headers.append({
                            'header': header,
                            'description': description
                        })
                
                if missing_headers:
                    severity = 'MEDIUM' if len(missing_headers) > 3 else 'LOW'
                    
                    self.vulnerabilities.append({
                        'id': 'HDR-001',
                        'severity': severity,
                        'category': 'HTTP Security Headers',
                        'title': 'Cabeçalhos de Segurança HTTP Ausentes',
                        'description': f'{len(missing_headers)} cabeçalhos de segurança importantes estão faltando.',
                        'recommendation': 'Configure os seguintes cabeçalhos no servidor web:\n' + 
                                         '\n'.join([f"- {h['header']}" for h in missing_headers]),
                        'evidence': f"URL: {url}\nHeaders ausentes: {', '.join([h['header'] for h in missing_headers])}",
                        'details': missing_headers
                    })
                
                self.results['http_headers'] = dict(response.headers)
                break
                
            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                logger.error(f"Erro ao verificar headers em {url}: {str(e)}")
                continue
    
    def _detect_directories(self, target: str) -> None:
        """
        Detecta diretórios expostos usando wordlist básica.
        
        Args:
            target: IP ou domínio do alvo
        """
        # Carregar wordlist
        wordlist_path = None
        possible_paths = [
            '/workspace/vuln_scanner_mvp/wordlists/common_dirs.txt',
            'wordlists/common_dirs.txt',
            '../wordlists/common_dirs.txt'
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    wordlist = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    wordlist_path = path
                    break
            except FileNotFoundError:
                continue
        
        if not wordlist_path:
            # Wordlist fallback embutida
            wordlist = [
                'admin', 'backup', 'config', 'db', 'login', 'phpinfo', 
                'test', 'tmp', 'uploads', '.env', '.git'
            ]
            logger.warning("Wordlist externa não encontrada. Usando lista básica.")
        else:
            logger.info(f"Wordlist carregada de: {wordlist_path}")
        
        urls_to_check = [
            f"http://{target}",
            f"https://{target}"
        ]
        
        found_directories = []
        
        for base_url in urls_to_check:
            try:
                for directory in wordlist[:20]:  # Limitar a 20 para não sobrecarregar
                    url = f"{base_url}/{directory}"
                    
                    try:
                        response = requests.get(url, timeout=3, verify=False)
                        
                        # Verificar se o diretório existe (status 200 ou 301/302)
                        if response.status_code in [200, 301, 302, 403]:
                            # Ignorar páginas de erro genéricas
                            if response.status_code == 200 and len(response.content) > 100:
                                found_directories.append({
                                    'url': url,
                                    'directory': directory,
                                    'status_code': response.status_code,
                                    'size': len(response.content)
                                })
                                
                                # Verificar diretórios sensíveis
                                sensitive_dirs = ['.env', '.git', 'backup', 'config', 'db', 'sql', '.htaccess']
                                if directory in sensitive_dirs or directory.startswith('.'):
                                    self.vulnerabilities.append({
                                        'id': f'DIR-{len(found_directories):03d}',
                                        'severity': 'HIGH' if directory in ['.env', '.git'] else 'MEDIUM',
                                        'category': 'Sensitive Directory Exposure',
                                        'title': f'Diretório/Arquivo Sensível Encontrado: /{directory}',
                                        'description': f'O diretório/arquivo /{directory} está acessível publicamente.',
                                        'recommendation': f'Remova ou proteja o acesso a /{directory}. Configure regras adequadas no servidor web.',
                                        'evidence': f"URL: {url}, Status: {response.status_code}"
                                    })
                                    
                    except requests.exceptions.RequestException:
                        continue
                        
            except Exception as e:
                logger.error(f"Erro ao verificar diretórios em {base_url}: {str(e)}")
                continue
            
            if found_directories:
                break  # Se encontrou em HTTP, não precisa testar HTTPS
        
        if found_directories:
            self.results['directories'] = found_directories
            logger.info(f"{len(found_directories)} diretórios encontrados.")
        else:
            self.results['directories'] = []
    
    def get_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Retorna lista de vulnerabilidades encontradas."""
        return self.vulnerabilities
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Retorna lista de serviços detectados."""
        return self.services
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos achados."""
        ports_data = self.results.get('ports', {})
        open_ports_count = len(ports_data.get('open_ports', [])) if isinstance(ports_data, dict) else 0
        
        return {
            'target': self.results.get('target', 'N/A'),
            'timestamp': self.results.get('timestamp', 'N/A'),
            'open_ports': open_ports_count,
            'services_detected': len(self.services),
            'technologies_found': len(self.results.get('technologies', [])),
            'directories_found': len(self.results.get('directories', [])),
            'total_vulnerabilities': len(self.vulnerabilities),
            'vulnerabilities_by_severity': self._count_by_severity()
        }
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Conta vulnerabilidades por severidade."""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        for vuln in self.vulnerabilities:
            severity = vuln.get('severity', 'INFO')
            if severity in counts:
                counts[severity] += 1
        return counts
