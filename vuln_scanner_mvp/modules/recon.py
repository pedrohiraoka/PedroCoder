"""
Módulo de Reconhecimento (Recon)
Realiza coleta de informações sobre o alvo usando técnicas passivas.
"""

import socket
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    GOOGLESEARCH_AVAILABLE = False

from utils.logger import logger


class ReconModule:
    """
    Módulo de reconhecimento para coleta de informações passivas.
    Baseado nas técnicas descritas em 'Hacking com Kali Linux'.
    """
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.vulnerabilities: List[Dict[str, Any]] = []
        
    def run_all(self, target: str) -> Dict[str, Any]:
        """
        Executa todas as técnicas de reconhecimento.
        
        Args:
            target: IP ou domínio do alvo
            
        Returns:
            Dicionário com todos os resultados
        """
        logger.info(f"Iniciando reconhecimento para: {target}")
        
        self.results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'whois': {},
            'dns': {},
            'geolocation': {},
            'google_hacking': [],
            'subdomains': [],
            'vulnerabilities': []
        }
        
        # Executar módulos de reconhecimento
        self._get_whois(target)
        self._dns_lookup(target)
        self._geolocate_ip(target)
        self._google_hacking(target)
        
        self.results['vulnerabilities'] = self.vulnerabilities
        logger.info(f"Reconhecimento concluído. {len(self.vulnerabilities)} achados.")
        
        return self.results
    
    def _resolve_target(self, target: str) -> Optional[str]:
        """
        Resolve um domínio para IP ou valida um IP.
        
        Args:
            target: Domínio ou IP
            
        Returns:
            IP resolvido ou None se falhar
        """
        try:
            # Verificar se já é um IP
            socket.inet_aton(target)
            return target
        except socket.error:
            # Tentar resolver como domínio
            try:
                ip = socket.gethostbyname(target)
                logger.info(f"Domínio {target} resolvido para IP: {ip}")
                return ip
            except socket.gaierror:
                logger.error(f"Não foi possível resolver: {target}")
                return None
    
    def _get_whois(self, target: str) -> None:
        """
        Consulta informações WHOIS do domínio/IP.
        
        Args:
            target: Domínio ou IP
        """
        if not WHOIS_AVAILABLE:
            logger.warning("Biblioteca 'whois' não disponível. Pulando WHOIS.")
            self.results['whois'] = {'error': 'Biblioteca whois não instalada'}
            return
        
        try:
            logger.info(f"Consultando WHOIS para: {target}")
            w = whois.whois(target)
            
            whois_data = {
                'domain': w.domain_name if hasattr(w, 'domain_name') else 'N/A',
                'registrar': w.registrar if hasattr(w, 'registrar') else 'N/A',
                'creation_date': str(w.creation_date) if hasattr(w, 'creation_date') else 'N/A',
                'expiration_date': str(w.expiration_date) if hasattr(w, 'expiration_date') else 'N/A',
                'updated_date': str(w.updated_date) if hasattr(w, 'updated_date') else 'N/A',
                'name_servers': w.name_servers if hasattr(w, 'name_servers') else [],
                'status': w.status if hasattr(w, 'status') else [],
                'emails': w.emails if hasattr(w, 'emails') else [],
                'org': w.org if hasattr(w, 'org') else 'N/A',
                'country': w.country if hasattr(w, 'country') else 'N/A'
            }
            
            self.results['whois'] = whois_data
            
            # Verificar vulnerabilidade: domínio expirando em breve
            if whois_data['expiration_date'] != 'N/A' and whois_data['expiration_date'] != 'None':
                try:
                    exp_date = whois_data['expiration_date'].split()[0] if ' ' in str(whois_data['expiration_date']) else whois_data['expiration_date']
                    # Análise simples - apenas informativa
                    self.vulnerabilities.append({
                        'id': 'WHOIS-001',
                        'severity': 'LOW',
                        'category': 'Information Disclosure',
                        'title': 'Informações WHOIS Expostas',
                        'description': 'As informações de registro do domínio estão publicamente disponíveis.',
                        'recommendation': 'Considere usar serviço de privacidade de domínio para ocultar dados sensíveis.',
                        'evidence': f"Domínio: {whois_data['domain']}"
                    })
                except Exception:
                    pass
                    
            logger.info("WHOIS consultado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao consultar WHOIS: {str(e)}")
            self.results['whois'] = {'error': str(e)}
    
    def _dns_lookup(self, target: str) -> None:
        """
        Realiza lookup DNS para diversos registros.
        
        Args:
            target: Domínio do alvo
        """
        if not DNS_AVAILABLE:
            logger.warning("Biblioteca 'dnspython' não disponível. Pulando DNS lookup.")
            self.results['dns'] = {'error': 'Biblioteca dnspython não instalada'}
            return
        
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
        dns_data = {}
        
        try:
            logger.info(f"Realizando DNS lookup para: {target}")
            
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(target, record_type)
                    records = [str(rdata) for rdata in answers]
                    dns_data[record_type] = records
                    
                    # Verificar vulnerabilidades específicas
                    if record_type == 'MX' and records:
                        self.vulnerabilities.append({
                            'id': 'DNS-001',
                            'severity': 'INFO',
                            'category': 'Information Disclosure',
                            'title': 'Servidores de Email Identificados',
                            'description': f'Servidores MX encontrados: {", ".join(records)}',
                            'recommendation': 'Verifique se os servidores de email possuem configurações de segurança adequadas (SPF, DKIM, DMARC).',
                            'evidence': f"Registros MX: {records}"
                        })
                    
                    if record_type == 'TXT' and records:
                        # Verificar SPF, DKIM, DMARC
                        has_spf = any('spf' in str(r).lower() for r in records)
                        has_dmarc = any('dmarc' in str(r).lower() for r in records)
                        
                        if not has_spf or not has_dmarc:
                            self.vulnerabilities.append({
                                'id': 'DNS-002',
                                'severity': 'MEDIUM',
                                'category': 'Email Security',
                                'title': 'Configurações de Segurança de Email Incompletas',
                                'description': f'Domínio pode não ter SPF ({\"✓\" if has_spf else \"✗\"}) ou DMARC ({\"✓\" if has_dmarc else \"✗\"}) configurados.',
                                'recommendation': 'Configure registros SPF e DMARC para proteger contra spoofing de email.',
                                'evidence': f"Registros TXT: {records}"
                            })
                            
                except dns.resolver.NoAnswer:
                    dns_data[record_type] = []
                except dns.resolver.NXDOMAIN:
                    dns_data[record_type] = []
                    break
                except Exception:
                    dns_data[record_type] = []
            
            self.results['dns'] = dns_data
            logger.info("DNS lookup concluído")
            
        except Exception as e:
            logger.error(f"Erro no DNS lookup: {str(e)}")
            self.results['dns'] = {'error': str(e)}
    
    def _geolocate_ip(self, target: str) -> None:
        """
        Obtém informações de geolocalização do IP.
        
        Args:
            target: IP ou domínio
        """
        try:
            ip = self._resolve_target(target)
            if not ip:
                self.results['geolocation'] = {'error': 'Não foi possível resolver o target'}
                return
            
            logger.info(f"Obtendo geolocalização para IP: {ip}")
            
            # Usar API pública de geolocalização (ip-api.com - gratuito para uso não comercial)
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            
            if response.status_code == 200:
                geo_data = response.json()
                
                if geo_data.get('status') == 'success':
                    self.results['geolocation'] = {
                        'ip': ip,
                        'country': geo_data.get('country', 'N/A'),
                        'country_code': geo_data.get('countryCode', 'N/A'),
                        'region': geo_data.get('regionName', 'N/A'),
                        'city': geo_data.get('city', 'N/A'),
                        'zip': geo_data.get('zip', 'N/A'),
                        'timezone': geo_data.get('timezone', 'N/A'),
                        'isp': geo_data.get('isp', 'N/A'),
                        'org': geo_data.get('org', 'N/A'),
                        'as': geo_data.get('as', 'N/A'),
                        'query': geo_data.get('query', 'N/A')
                    }
                    
                    # Verificar se é hosting/cloud (potencialmente mais seguro)
                    isp_lower = str(geo_data.get('isp', '')).lower()
                    hosting_keywords = ['amazon', 'google', 'microsoft', 'digitalocean', 'linode', 'cloudflare', 'ovh', 'hetzner']
                    
                    if any(keyword in isp_lower for keyword in hosting_keywords):
                        self.vulnerabilities.append({
                            'id': 'GEO-001',
                            'severity': 'INFO',
                            'category': 'Infrastructure',
                            'title': 'Hospedagem em Nuvem/Hosting Detectada',
                            'description': f'O alvo está hospedado em provedor de cloud/hosting: {geo_data.get("isp", "N/A")}',
                            'recommendation': 'Sistemas em nuvem podem ter configurações de segurança diferentes. Verifique security groups e ACLs.',
                            'evidence': f"ISP: {geo_data.get('isp', 'N/A')}"
                        })
                    
                    logger.info("Geolocalização obtida com sucesso")
                else:
                    self.results['geolocation'] = {'error': 'API retornou status de erro'}
            else:
                self.results['geolocation'] = {'error': f'Status code: {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na geolocalização: {str(e)}")
            self.results['geolocation'] = {'error': str(e)}
        except Exception as e:
            logger.error(f"Erro inesperado na geolocalização: {str(e)}")
            self.results['geolocation'] = {'error': str(e)}
    
    def _google_hacking(self, target: str) -> None:
        """
        Realiza Google Hacking básico (apenas simulação educativa).
        
        Args:
            target: Domínio do alvo
        """
        if not GOOGLESEARCH_AVAILABLE:
            logger.warning("Biblioteca 'googlesearch-python' não disponível. Pulando Google Hacking.")
            self.results['google_hacking'] = {'error': 'Biblioteca googlesearch-python não instalada'}
            return
        
        try:
            logger.info(f"Realizando Google Hacking para: {target}")
            
            # Queries de Google Hacking baseadas em técnicas comuns
            queries = [
                f'site:{target} ext:php',
                f'site:{target} ext:sql',
                f'site:{target} ext:txt',
                f'site:{target} intext:"index of"',
                f'site:{target} inurl:admin',
                f'site:{target} inurl:login',
                f'site:{target} filetype:pdf',
                f'site:{target} intitle:"index of /"',
            ]
            
            results = []
            
            for query in queries[:3]:  # Limitar a 3 queries para não sobrecarregar
                try:
                    query_results = list(search(query, num_results=5, advanced=True))
                    for result in query_results[:2]:  # Max 2 resultados por query
                        results.append({
                            'query': query,
                            'title': getattr(result, 'title', 'N/A'),
                            'url': getattr(result, 'url', 'N/A') if hasattr(result, 'url') else str(result),
                            'description': getattr(result, 'description', 'N/A')
                        })
                        
                        # Identificar possíveis vulnerabilidades
                        if 'index of' in str(result).lower() or 'directory' in str(result).lower():
                            self.vulnerabilities.append({
                                'id': 'GH-001',
                                'severity': 'HIGH',
                                'category': 'Information Disclosure',
                                'title': 'Possível Directory Listing Exposto',
                                'description': f'Listagem de diretório pode estar habilitada no servidor.',
                                'recommendation': 'Desabilite directory listing no servidor web (Apache: Options -Indexes, Nginx: autoindex off).',
                                'evidence': f"Query: {query}, Resultado: {result}"
                            })
                            
                except Exception:
                    continue
            
            self.results['google_hacking'] = results
            logger.info(f"Google Hacking concluído. {len(results)} resultados encontrados.")
            
        except Exception as e:
            logger.error(f"Erro no Google Hacking: {str(e)}")
            self.results['google_hacking'] = {'error': str(e)}
    
    def get_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Retorna lista de vulnerabilidades encontradas."""
        return self.vulnerabilities
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos achados."""
        return {
            'target': self.results.get('target', 'N/A'),
            'timestamp': self.results.get('timestamp', 'N/A'),
            'whois_available': bool(self.results.get('whois', {}) and 'error' not in self.results.get('whois', {})),
            'dns_records_found': len(self.results.get('dns', {})) if isinstance(self.results.get('dns'), dict) else 0,
            'geolocation_available': bool(self.results.get('geolocation', {}) and 'error' not in self.results.get('geolocation', {})),
            'google_results': len(self.results.get('google_hacking', [])) if isinstance(self.results.get('google_hacking'), list) else 0,
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
