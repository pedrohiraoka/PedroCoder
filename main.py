#!/usr/bin/env python3
"""
TechDetector - MVP de Detecção de Tecnologias Web

Este módulo fornece uma classe para detectar tecnologias utilizadas por um site,
analisando headers HTTP e conteúdo HTML da página.

Autor: TechDetector MVP
Versão: 1.0.0
"""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class TechDetector:
    """
    Classe principal para detecção de tecnologias web.
    
    Esta classe realiza requisições HTTP para uma URL fornecida e analisa
    os headers da resposta e o conteúdo HTML para identificar tecnologias
    como servidores web, CMS, frameworks, bibliotecas JavaScript, etc.
    
    Attributes:
        url (str): A URL do site a ser analisado.
        signatures (List[Dict]): Lista de assinaturas para detecção de tecnologias.
        detected_technologies (List[Dict]): Lista de tecnologias detectadas.
    """

    def __init__(self):
        """Inicializa o TechDetector com a base de assinaturas de detecção."""
        self.url: str = ""
        self.signatures: List[Dict[str, Any]] = self._build_signatures()
        self.detected_technologies: List[Dict[str, str]] = []

    def _build_signatures(self) -> List[Dict[str, Any]]:
        """
        Constrói a base de assinaturas para detecção de tecnologias.
        
        Returns:
            List[Dict]: Lista de dicionários contendo padrões de detecção.
        """
        signatures = [
            # ==================== SERVIDORES WEB ====================
            {
                "header_key": "Server",
                "pattern": r"Apache(?:/(\d+\.\d+\.\d+))?",
                "technology": "Apache",
                "type": "header"
            },
            {
                "header_key": "Server",
                "pattern": r"nginx(?:/(\d+\.\d+\.\d+))?",
                "technology": "nginx",
                "type": "header"
            },
            {
                "header_key": "Server",
                "pattern": r"Microsoft-IIS(?:/(\d+\.\d+))?",
                "technology": "Microsoft-IIS",
                "type": "header"
            },
            {
                "header_key": "Server",
                "pattern": r"LiteSpeed",
                "technology": "LiteSpeed",
                "type": "header"
            },
            {
                "header_key": "Server",
                "pattern": r"Caddy",
                "technology": "Caddy",
                "type": "header"
            },
            
            # ==================== CMS ====================
            {
                "header_key": "X-Powered-By",
                "pattern": r"WordPress",
                "technology": "WordPress",
                "type": "header"
            },
            {
                "html_pattern": r'<meta[^>]*generator[^>]*wordpress',
                "technology": "WordPress",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'/wp-content/',
                "technology": "WordPress",
                "type": "html"
            },
            {
                "html_pattern": r'/wp-includes/',
                "technology": "WordPress",
                "type": "html"
            },
            {
                "header_key": "X-Generator",
                "pattern": r"Drupal",
                "technology": "Drupal",
                "type": "header"
            },
            {
                "html_pattern": r'<meta[^>]*generator[^>]*drupal',
                "technology": "Drupal",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "X-Generator",
                "pattern": r"Joomla",
                "technology": "Joomla",
                "type": "header"
            },
            {
                "html_pattern": r'<meta[^>]*generator[^>]*joomla',
                "technology": "Joomla",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "X-Ghost",
                "pattern": r".*",
                "technology": "Ghost",
                "type": "header"
            },
            {
                "html_pattern": r'<meta[^>]*generator[^>]*ghost',
                "technology": "Ghost",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"Magento",
                "technology": "Magento",
                "type": "header"
            },
            {
                "html_pattern": r'magento',
                "technology": "Magento",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "X-Served-By",
                "pattern": r"Shopify",
                "technology": "Shopify",
                "type": "header"
            },
            {
                "html_pattern": r'shopify-cdn',
                "technology": "Shopify",
                "type": "html",
                "flags": re.IGNORECASE
            },
            
            # ==================== FRAMEWORKS BACKEND ====================
            {
                "header_key": "X-Powered-By",
                "pattern": r"Django",
                "technology": "Django",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"Flask",
                "technology": "Flask",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"Laravel",
                "technology": "Laravel",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"Ruby on Rails",
                "technology": "Ruby on Rails",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"Express",
                "technology": "Express",
                "type": "header"
            },
            {
                "header_key": "X-AspNet-Version",
                "pattern": r".*",
                "technology": "ASP.NET",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"ASP\.NET",
                "technology": "ASP.NET",
                "type": "header"
            },
            {
                "header_key": "X-Powered-By",
                "pattern": r"PHP(?:/(\d+\.\d+))?",
                "technology": "PHP",
                "type": "header"
            },
            
            # ==================== FRAMEWORKS FRONTEND ====================
            {
                "html_pattern": r'react(?:\.development|\.production)?\.js',
                "technology": "React",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'data-reactroot',
                "technology": "React",
                "type": "html"
            },
            {
                "html_pattern": r'<[^>]+react-root',
                "technology": "React",
                "type": "html"
            },
            {
                "html_pattern": r'vue(?:\.js)?(?:\?v=[\d.]+)?',
                "technology": "Vue.js",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'\bvue\b.*constructor',
                "technology": "Vue.js",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'ng-version=["\']',
                "technology": "Angular",
                "type": "html"
            },
            {
                "html_pattern": r'angular(?:\.min)?\.js',
                "technology": "Angular",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'<[^>]+ng-',
                "technology": "Angular",
                "type": "html"
            },
            {
                "html_pattern": r'svelte(?:\.min)?\.js',
                "technology": "Svelte",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'<!-- start:svelte -->',
                "technology": "Svelte",
                "type": "html"
            },
            
            # ==================== BIBLIOTECAS JAVASCRIPT ====================
            {
                "html_pattern": r'jquery(?:\-[\d.]+)?(?:\.min)?\.js',
                "technology": "jQuery",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'code\.jquery\.com/jquery',
                "technology": "jQuery",
                "type": "html"
            },
            {
                "html_pattern": r'lodash(?:\.min)?\.js',
                "technology": "Lodash",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'moment(?:\.min)?\.js',
                "technology": "Moment.js",
                "type": "html",
                "flags": re.IGNORECASE
            },
            
            # ==================== FRAMEWORKS CSS ====================
            {
                "html_pattern": r'bootstrap(?:\.min)?\.css',
                "technology": "Bootstrap",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'cdn\.jsdelivr\.net/npm/bootstrap',
                "technology": "Bootstrap",
                "type": "html"
            },
            {
                "html_pattern": r'class="[^"]*btn btn-',
                "technology": "Bootstrap",
                "type": "html"
            },
            {
                "html_pattern": r'tailwind(?:\.min)?\.css',
                "technology": "Tailwind",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'cdn\.jsdelivr\.net/npm/tailwindcss',
                "technology": "Tailwind",
                "type": "html"
            },
            {
                "html_pattern": r'class="[^"]*tw-',
                "technology": "Tailwind",
                "type": "html"
            },
            {
                "html_pattern": r'bulma(?:\.min)?\.css',
                "technology": "Bulma",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'cdn\.jsdelivr\.net/npm/bulma',
                "technology": "Bulma",
                "type": "html"
            },
            {
                "html_pattern": r'foundation(?:\.min)?\.css',
                "technology": "Foundation",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'cdn\.jsdelivr\.net/npm/foundation-sites',
                "technology": "Foundation",
                "type": "html"
            },
            
            # ==================== PLATAFORMAS DE E-COMMERCE ====================
            {
                "html_pattern": r'woocommerce',
                "technology": "WooCommerce",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'/wp-content/plugins/woocommerce/',
                "technology": "WooCommerce",
                "type": "html"
            },
            {
                "header_key": "X-Served-By",
                "pattern": r"BigCommerce",
                "technology": "BigCommerce",
                "type": "header"
            },
            {
                "html_pattern": r'bigcommerce',
                "technology": "BigCommerce",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "X-Wix-Renderer-Server",
                "pattern": r".*",
                "technology": "Wix",
                "type": "header"
            },
            {
                "html_pattern": r'wix\.com',
                "technology": "Wix",
                "type": "html",
                "flags": re.IGNORECASE
            },
            
            # ==================== CDNs E SERVIÇOS DE SEGURANÇA ====================
            {
                "header_key": "Server",
                "pattern": r"cloudflare",
                "technology": "Cloudflare",
                "type": "header",
                "flags": re.IGNORECASE
            },
            {
                "header_key": "CF-RAY",
                "pattern": r".*",
                "technology": "Cloudflare",
                "type": "header"
            },
            {
                "html_pattern": r'cdn\.jsdelivr\.net',
                "technology": "jsDelivr",
                "type": "html"
            },
            {
                "html_pattern": r'maxcdn\.com',
                "technology": "MaxCDN",
                "type": "html",
                "flags": re.IGNORECASE
            },
            
            # ==================== ANÁLISES E MONITORAMENTO ====================
            {
                "html_pattern": r'googletagmanager\.com/gtag/js',
                "technology": "Google Tag Manager",
                "type": "html"
            },
            {
                "html_pattern": r'google-analytics\.com/analytics\.js',
                "technology": "Google Analytics",
                "type": "html"
            },
            {
                "html_pattern": r'www\.google-analytics\.com',
                "technology": "Google Analytics",
                "type": "html"
            },
            {
                "html_pattern": r'gtag\(["\']config["\'], ["\']GA-',
                "technology": "Google Analytics",
                "type": "html"
            },
            {
                "html_pattern": r'hotjar\.com',
                "technology": "Hotjar",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'static\.hotjar\.com',
                "technology": "Hotjar",
                "type": "html"
            },
            {
                "html_pattern": r'matomo\.org',
                "technology": "Matomo",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'piwik\.js',
                "technology": "Matomo",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'/matomo/',
                "technology": "Matomo",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'newrelic\.com',
                "technology": "New Relic",
                "type": "html",
                "flags": re.IGNORECASE
            },
            {
                "html_pattern": r'js-agent\.newrelic\.com',
                "technology": "New Relic",
                "type": "html"
            },
        ]
        return signatures

    def fetch_data(self, url: str) -> tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        Faz uma requisição HTTP GET para a URL fornecida e retorna headers e HTML.
        
        Args:
            url (str): A URL do site a ser analisado.
            
        Returns:
            tuple: Uma tupla contendo (headers, html_content).
                   Retorna (None, None) em caso de erro.
                   
        Raises:
            ValueError: Se a URL for inválida ou malformada.
            requests.RequestException: Em caso de falha na conexão.
        """
        # Validar URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"URL inválida ou malformada: {url}")
        
        # Garantir que a URL tenha o esquema http ou https
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError(f"Esquema de URL não suportado: {parsed_url.scheme}. Use http ou https.")
        
        try:
            # Realizar requisição HTTP com timeout
            response = requests.get(
                url,
                timeout=10,  # Timeout de 10 segundos
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                verify=True  # Verificar certificado SSL
            )
            
            # Verificar se a resposta foi bem-sucedida
            response.raise_for_status()
            
            headers = dict(response.headers)
            html_content = response.text
            
            return headers, html_content
            
        except requests.exceptions.SSLError as e:
            print(f"Erro SSL: {e}")
            print("Dica: Em ambientes de desenvolvimento, você pode precisar configurar certificados SSL.")
            return None, None
        except requests.exceptions.Timeout:
            print("Erro: Tempo limite excedido ao conectar ao servidor.")
            return None, None
        except requests.exceptions.ConnectionError:
            print("Erro: Falha na conexão com o servidor.")
            return None, None
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP: {e}")
            return None, None
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}")
            return None, None

    def analyze_headers(self, headers: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Analisa os headers HTTP em busca de assinaturas de tecnologias conhecidas.
        
        Args:
            headers (Dict): Dicionário contendo os headers da resposta HTTP.
            
        Returns:
            List[Dict]: Lista de tecnologias detectadas nos headers.
        """
        detected = []
        
        # Normalizar chaves dos headers (tornar case-insensitive)
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        
        for signature in self.signatures:
            if signature.get("type") != "header":
                continue
                
            header_key = signature.get("header_key", "").lower()
            pattern = signature.get("pattern", "")
            technology = signature.get("technology", "")
            flags = signature.get("flags", 0)
            
            # Verificar se o header existe
            if header_key in normalized_headers:
                header_value = normalized_headers[header_key]
                
                # Tentar encontrar o padrão no valor do header
                if re.search(pattern, header_value, flags):
                    detected.append({
                        "technology": technology,
                        "source": "header",
                        "details": f"Detectado no header '{header_key}': {header_value[:50]}"
                    })
        
        return detected

    def analyze_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        Analisa o conteúdo HTML em busca de assinaturas de tecnologias conhecidas.
        
        Args:
            html_content (str): Conteúdo HTML da página.
            
        Returns:
            List[Dict]: Lista de tecnologias detectadas no HTML.
        """
        detected = []
        
        # Usar BeautifulSoup para parsing do HTML (embora usemos regex principalmente)
        soup = BeautifulSoup(html_content, 'lxml')
        
        for signature in self.signatures:
            if signature.get("type") != "html":
                continue
                
            pattern = signature.get("html_pattern", "")
            technology = signature.get("technology", "")
            flags = signature.get("flags", 0)
            
            # Buscar o padrão no conteúdo HTML completo
            if re.search(pattern, html_content, flags):
                detected.append({
                    "technology": technology,
                    "source": "html",
                    "details": f"Detectado no conteúdo HTML"
                })
        
        return detected

    def detect_technologies(self, url: str) -> List[Dict[str, str]]:
        """
        Coordena a análise completa e retorna as tecnologias detectadas.
        
        Este método é o ponto principal da classe. Ele:
        1. Faz a requisição HTTP para a URL
        2. Analisa os headers da resposta
        3. Analisa o conteúdo HTML
        4. Consolida os resultados removendo duplicatas
        
        Args:
            url (str): A URL do site a ser analisado.
            
        Returns:
            List[Dict]: Lista consolidada de tecnologias detectadas.
        """
        self.url = url
        self.detected_technologies = []
        
        print(f"\nAnalisando: {url}")
        print("-" * 50)
        
        # Fazer a requisição e obter dados
        headers, html_content = self.fetch_data(url)
        
        if headers is None or html_content is None:
            print("Não foi possível obter dados da URL fornecida.")
            return []
        
        # Analisar headers
        print("Analisando headers HTTP...")
        header_detections = self.analyze_headers(headers)
        self.detected_technologies.extend(header_detections)
        
        # Analisar HTML
        print("Analisando conteúdo HTML...")
        html_detections = self.analyze_html(html_content)
        self.detected_technologies.extend(html_detections)
        
        # Remover duplicatas (manter apenas uma entrada por tecnologia)
        seen_technologies = set()
        unique_detections = []
        
        for detection in self.detected_technologies:
            tech_name = detection["technology"]
            if tech_name not in seen_technologies:
                seen_technologies.add(tech_name)
                unique_detections.append(detection)
        
        self.detected_technologies = unique_detections
        
        return self.detected_technologies

    def print_report(self) -> None:
        """
        Imprime um relatório formatado das tecnologias detectadas.
        """
        print("\n" + "=" * 60)
        print("RELATÓRIO DE DETECÇÃO DE TECNOLOGIAS")
        print("=" * 60)
        print(f"\nURL Analisada: {self.url}")
        print("-" * 60)
        
        if not self.detected_technologies:
            print("\nNenhuma tecnologia foi detectada.")
        else:
            print(f"\nTecnologias Detectadas ({len(self.detected_technologies)}):\n")
            
            # Agrupar por tipo de tecnologia para melhor organização
            categories = {
                "Servidores Web": [],
                "CMS": [],
                "Frameworks Backend": [],
                "Frameworks Frontend": [],
                "Bibliotecas JavaScript": [],
                "Frameworks CSS": [],
                "E-commerce": [],
                "CDNs e Segurança": [],
                "Análises e Monitoramento": []
            }
            
            # Mapeamento simples de tecnologias para categorias
            tech_category_map = {
                "Apache": "Servidores Web",
                "nginx": "Servidores Web",
                "Microsoft-IIS": "Servidores Web",
                "LiteSpeed": "Servidores Web",
                "Caddy": "Servidores Web",
                "WordPress": "CMS",
                "Drupal": "CMS",
                "Joomla": "CMS",
                "Ghost": "CMS",
                "Magento": "CMS",
                "Shopify": "CMS",
                "Django": "Frameworks Backend",
                "Flask": "Frameworks Backend",
                "Laravel": "Frameworks Backend",
                "Ruby on Rails": "Frameworks Backend",
                "Express": "Frameworks Backend",
                "ASP.NET": "Frameworks Backend",
                "PHP": "Frameworks Backend",
                "React": "Frameworks Frontend",
                "Vue.js": "Frameworks Frontend",
                "Angular": "Frameworks Frontend",
                "Svelte": "Frameworks Frontend",
                "jQuery": "Bibliotecas JavaScript",
                "Lodash": "Bibliotecas JavaScript",
                "Moment.js": "Bibliotecas JavaScript",
                "Bootstrap": "Frameworks CSS",
                "Tailwind": "Frameworks CSS",
                "Bulma": "Frameworks CSS",
                "Foundation": "Frameworks CSS",
                "WooCommerce": "E-commerce",
                "BigCommerce": "E-commerce",
                "Wix": "E-commerce",
                "Cloudflare": "CDNs e Segurança",
                "jsDelivr": "CDNs e Segurança",
                "MaxCDN": "CDNs e Segurança",
                "Google Analytics": "Análises e Monitoramento",
                "Google Tag Manager": "Análises e Monitoramento",
                "Hotjar": "Análises e Monitoramento",
                "Matomo": "Análises e Monitoramento",
                "New Relic": "Análises e Monitoramento",
            }
            
            # Categorizar tecnologias detectadas
            for tech in self.detected_technologies:
                tech_name = tech["technology"]
                category = tech_category_map.get(tech_name, "Outros")
                categories[category].append(tech)
            
            # Imprimir por categoria
            for category, techs in categories.items():
                if techs:
                    print(f"\n{category}:")
                    for tech in techs:
                        print(f"  ✓ {tech['technology']}")
                        print(f"    Fonte: {tech['source']}")
        
        print("\n" + "=" * 60)


def main():
    """
    Função principal que executa o TechDetector.
    
    Solicita ao usuário uma URL, realiza a análise e exibe o relatório.
    """
    print("=" * 60)
    print("TechDetector - MVP de Detecção de Tecnologias Web")
    print("=" * 60)
    print("\nEste programa analisa um site e identifica as tecnologias utilizadas.")
    print("Exemplo: https://exemplo.com\n")
    
    try:
        # Solicitar URL ao usuário
        url = input("Digite a URL a ser analisada: ").strip()
        
        if not url:
            print("Erro: URL não pode estar vazia.")
            return
        
        # Criar instância do detector
        detector = TechDetector()
        
        # Realizar detecção
        detector.detect_technologies(url)
        
        # Imprimir relatório
        detector.print_report()
        
    except ValueError as e:
        print(f"\nErro de validação: {e}")
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {e}")


if __name__ == "__main__":
    main()
