"""
Parser - Extração e parsing de conteúdo HTML

Módulo responsável por extrair dados estruturados de páginas HTML
usando seletores CSS ou XPath configuráveis.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from parsel import Selector

from src.models import Company, Contact, Service, Price
from src.utils import normalize_email, normalize_phone, parse_price


logger = logging.getLogger("crawler.parser")


class ParseResult:
    """Resultado do parsing de uma página."""
    
    def __init__(self):
        self.companies: List[Company] = []
        self.next_page_url: Optional[str] = None
        self.errors: List[str] = []
        self.items_found: int = 0
    
    def add_error(self, error: str) -> None:
        """Adiciona erro ao resultado."""
        self.errors.append(error)
        logger.warning(f"Parse error: {error}")
    
    @property
    def success(self) -> bool:
        """Indica se parsing foi bem-sucedido."""
        return len(self.errors) == 0 and len(self.companies) > 0


class Parser:
    """
    Parser para extração de dados de páginas HTML.
    
    Suporta seletores CSS e XPath, com configuração flexível
    por domínio ou template.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa parser com configuração.
        
        Args:
            config: Dicionário de configuração com seletores
        """
        self.config = config
        self.use_xpath = config.get('use_xpath', False)
        self.listagem_config = config.get('listagem', {})
        self.campos_config = config.get('campos', {})
        self.servicos_config = config.get('servicos', {})
        self.precos_config = config.get('precos', {})
    
    def parse(self, html: str, base_url: str) -> ParseResult:
        """
        Parseia HTML e extrai dados estruturados.
        
        Args:
            html: Conteúdo HTML da página
            base_url: URL base para links relativos
        
        Returns:
            ParseResult com empresas extraídas
        """
        result = ParseResult()
        
        try:
            # Inicializa parsers
            soup = BeautifulSoup(html, 'lxml')
            selector = Selector(text=html)
            
            # Extrai lista de empresas (listagem)
            companies = self._extract_companies_list(soup, selector, base_url)
            
            if companies:
                result.companies = companies
                result.items_found = len(companies)
                logger.info(f"Extraídas {len(companies)} empresas da listagem")
            else:
                # Tenta extrair empresa única (página de detalhe)
                company = self._extract_single_company(soup, selector, base_url)
                if company:
                    result.companies = [company]
                    result.items_found = 1
                    logger.info("Extraída empresa única da página")
            
            # Extrai link de próxima página (paginação)
            result.next_page_url = self._extract_pagination(soup, selector, base_url)
            
        except Exception as e:
            result.add_error(f"Erro no parsing: {str(e)}")
            logger.exception("Erro durante parsing do HTML")
        
        return result
    
    def _extract_companies_list(
        self, 
        soup: BeautifulSoup, 
        selector: Selector, 
        base_url: str
    ) -> List[Company]:
        """Extrai lista de empresas de uma página de listagem."""
        companies = []
        
        container_selector = self.listagem_config.get('container')
        if not container_selector:
            logger.debug("Nenhum container de listagem configurado")
            return companies
        
        # Seleciona containers
        if self.use_xpath:
            containers = selector.xpath(container_selector).getall()
            container_elements = [Selector(text=c) for c in containers] if containers else []
        else:
            container_elements = soup.select(container_selector)
        
        logger.debug(f"Encontrados {len(container_elements)} containers")
        
        # Extrai cada empresa
        for i, container in enumerate(container_elements):
            try:
                company = self._extract_company_from_container(
                    container, base_url, f"item_{i}"
                )
                if company and company.nome:
                    companies.append(company)
            except Exception as e:
                logger.warning(f"Erro ao extrair item {i}: {e}")
                continue
        
        return companies
    
    def _extract_single_company(
        self,
        soup: BeautifulSoup,
        selector: Selector,
        base_url: str
    ) -> Optional[Company]:
        """Extrai empresa única de página de detalhe."""
        try:
            company = self._extract_company_from_container(selector, base_url, "detail")
            return company if company and company.nome else None
        except Exception as e:
            logger.warning(f"Erro ao extrair empresa única: {e}")
            return None
    
    def _extract_company_from_container(
        self,
        container: Any,
        base_url: str,
        index: str
    ) -> Optional[Company]:
        """
        Extrai dados de empresa de um container.
        
        Args:
            container: Elemento container (Soup element ou Selector)
            base_url: URL base
            index: Identificador do item
        
        Returns:
            Company ou None
        """
        try:
            # Extrai campos básicos
            campos_data = self._extract_fields(container, self.campos_config, base_url)
            
            if not campos_data.get('nome'):
                return None
            
            # Cria contato
            contato = Contact(
                email=normalize_email(campos_data.get('email')),
                telefone=normalize_phone(campos_data.get('telefone')) if campos_data.get('telefone') else None,
                website=campos_data.get('website'),
                endereco=campos_data.get('endereco')
            )
            
            # Extrai serviços
            servicos = self._extract_services(container, base_url)
            
            # Extrai preços gerais
            precos = self._extract_prices(container, base_url)
            
            company = Company(
                nome=campos_data.get('nome', ''),
                descricao=campos_data.get('descricao'),
                contato=contato if any([contato.email, contato.telefone, contato.website]) else None,
                servicos=servicos,
                precos=precos,
                categoria=campos_data.get('categoria'),
                url_origem=base_url,
                metadata={'index': index}
            )
            
            return company
            
        except Exception as e:
            logger.debug(f"Erro ao extrair container {index}: {e}")
            return None
    
    def _extract_fields(
        self,
        container: Any,
        config: Dict[str, str],
        base_url: str
    ) -> Dict[str, Any]:
        """
        Extrai múltiplos campos de um container.
        
        Args:
            container: Elemento container
            config: Configuração dos campos
            base_url: URL base
        
        Returns:
            Dicionário com valores dos campos
        """
        data = {}
        
        for field_name, selector in config.items():
            value = self._extract_field_value(container, selector, base_url)
            if value:
                data[field_name] = value
        
        return data
    
    def _extract_field_value(
        self,
        container: Any,
        selector: str,
        base_url: str
    ) -> Optional[Any]:
        """
        Extrai valor de um campo específico.
        
        Suporta:
        - Seletor CSS: "h2.title::text"
        - Seletor CSS com atributo: "a.link@href"
        - XPath: ".//h2[@class='title']/text()"
        
        Args:
            container: Elemento container
            selector: Seletor CSS ou XPath
            base_url: URL base para normalização
        
        Returns:
            Valor extraído ou None
        """
        try:
            if not selector:
                return None
            
            # Detecta se é XPath
            is_xpath = self.use_xpath or selector.startswith(('//', './/'))
            
            # Verifica se precisa de atributo
            attr_name = None
            if '@' in selector and not is_xpath:
                parts = selector.split('@')
                selector = parts[0]
                attr_name = parts[1] if len(parts) > 1 else None
            
            # Verifica se é seletor de texto (::text)
            is_text_selector = selector.endswith('::text')
            if is_text_selector:
                selector = selector[:-6]  # Remove ::text
            
            if is_xpath:
                # Usa parsel para XPath
                if isinstance(container, Selector):
                    result = container.xpath(selector).get()
                else:
                    # Converte Soup element para Selector
                    selector_obj = Selector(text=str(container))
                    result = selector_obj.xpath(selector).get()
            else:
                # Usa BeautifulSoup para CSS
                if isinstance(container, Tag):
                    element = container.select_one(selector)
                else:
                    css_result = container.css(selector).get()
                    if css_result:
                        element = Selector(text=css_result)
                    else:
                        element = None
                
                if element is None:
                    return None
                
                # Verifica se precisa de atributo
                if attr_name:
                    if isinstance(element, Tag):
                        result = element.get(attr_name)
                    else:
                        result = element.attrib.get(attr_name)
                elif is_text_selector:
                    # Apenas texto
                    if isinstance(element, Tag):
                        result = element.get_text(strip=True)
                    else:
                        result = element.get()
                else:
                    # Texto por padrão
                    if isinstance(element, Tag):
                        result = element.get_text(strip=True)
                    else:
                        result = element.get()
            
            # Limpa e normaliza
            if result:
                result = ' '.join(result.split()).strip()
                
                # Normaliza URLs
                if attr_name == 'href' or 'url' in selector.lower():
                    result = urljoin(base_url, result)
                
                return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair campo '{selector}': {e}")
            return None
    
    def _extract_services(
        self,
        container: Any,
        base_url: str
    ) -> List[Service]:
        """Extrai lista de serviços."""
        services = []
        
        if not self.servicos_config:
            return services
        
        container_selector = self.servicos_config.get('container')
        campos_config = self.servicos_config.get('campos', {})
        
        if not container_selector:
            return services
        
        # Seleciona containers de serviço
        if self.use_xpath:
            items = container.xpath(container_selector).getall()
            service_containers = [Selector(text=i) for i in items] if items else []
        else:
            if isinstance(container, Tag):
                service_containers = container.select(container_selector)
            else:
                service_containers = container.css(container_selector).getall()
                service_containers = [Selector(text=s) for s in service_containers]
        
        for i, svc_container in enumerate(service_containers):
            try:
                campos = self._extract_fields(svc_container, campos_config, base_url)
                
                if not campos.get('nome'):
                    continue
                
                # Parse preço se existir
                preco = None
                if campos.get('preco'):
                    valor = parse_price(campos['preco'])
                    if valor:
                        preco = Price(valor=valor, formato_original=campos['preco'])
                
                service = Service(
                    nome=campos['nome'],
                    descricao=campos.get('descricao'),
                    preco=preco,
                    categoria=campos.get('categoria')
                )
                services.append(service)
                
            except Exception as e:
                logger.debug(f"Erro ao extrair serviço {i}: {e}")
                continue
        
        return services
    
    def _extract_prices(
        self,
        container: Any,
        base_url: str
    ) -> List[Price]:
        """Extrai lista de preços gerais."""
        prices = []
        
        if not self.precos_config:
            return prices
        
        container_selector = self.precos_config.get('container')
        campos_config = self.precos_config.get('campos', {})
        
        if not container_selector:
            return prices
        
        # Seleciona containers de preço
        if self.use_xpath:
            items = container.xpath(container_selector).getall()
            price_containers = [Selector(text=i) for i in items] if items else []
        else:
            if isinstance(container, Tag):
                price_containers = container.select(container_selector)
            else:
                price_containers = container.css(container_selector).getall()
                price_containers = [Selector(text=p) for p in price_containers]
        
        for i, price_container in enumerate(price_containers):
            try:
                campos = self._extract_fields(price_container, campos_config, base_url)
                
                valor_str = campos.get('valor') or campos.get('preco')
                if not valor_str:
                    continue
                
                valor = parse_price(valor_str)
                if not valor:
                    continue
                
                price = Price(
                    valor=valor,
                    moeda=campos.get('moeda', 'BRL'),
                    formato_original=valor_str,
                    tipo=campos.get('plano') or campos.get('tipo')
                )
                prices.append(price)
                
            except Exception as e:
                logger.debug(f"Erro ao extrair preço {i}: {e}")
                continue
        
        return prices
    
    def _extract_pagination(
        self,
        soup: BeautifulSoup,
        selector: Selector,
        base_url: str
    ) -> Optional[str]:
        """Extrai URL da próxima página."""
        pagination_selector = self.listagem_config.get('pagination')
        
        if not pagination_selector:
            return None
        
        try:
            if self.use_xpath or pagination_selector.startswith('//'):
                # XPath
                next_url = selector.xpath(pagination_selector).get()
            else:
                # CSS
                if pagination_selector.endswith('@href'):
                    element = soup.select_one(pagination_selector.split('@')[0])
                    next_url = element.get('href') if element else None
                else:
                    element = soup.select_one(pagination_selector)
                    next_url = element.get('href') if element else None
            
            if next_url:
                next_url = urljoin(base_url, next_url.strip())
                logger.debug(f"Próxima página encontrada: {next_url}")
                return next_url
            
        except Exception as e:
            logger.debug(f"Erro ao extrair paginação: {e}")
        
        return None


def create_parser_for_domain(domain: str, sites_config: Dict[str, Any]) -> Optional[Parser]:
    """
    Factory function para criar parser baseado no domínio.
    
    Args:
        domain: Domínio do site
        sites_config: Configuração completa de sites
    
    Returns:
        Parser configurado ou None se domínio não configurado
    """
    # Normaliza domínio
    domain = domain.lower().replace('www.', '')
    
    # Busca configuração específica
    site_config = sites_config.get(domain)
    
    if not site_config:
        # Tenta match parcial
        for key, config in sites_config.items():
            if key in domain or domain in key:
                site_config = config
                break
    
    if not site_config:
        logger.warning(f"Nenhuma configuração encontrada para domínio: {domain}")
        return None
    
    return Parser(site_config)
