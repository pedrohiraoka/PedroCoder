"""
Crawler - Gerenciamento de filas, HTTP e controle de crawl

Módulo principal que orquestra o crawling de páginas web com
respeito a robots.txt, retries, delays e controle de URLs visitadas.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Set, List, Dict, Any
from urllib.parse import urlparse, urljoin
from collections import deque

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.models import CrawledPage, CrawlerStats, Company
from src.parser import Parser, create_parser_for_domain
from src.utils import (
    RateLimiter, 
    hash_url, 
    get_domain, 
    should_exclude_url,
    format_duration,
    normalize_url
)


logger = logging.getLogger("crawler.main")


class RobotsTxtParser:
    """Parser simples para robots.txt."""
    
    def __init__(self):
        self.allowed_paths: Set[str] = set()
        self.disallowed_paths: Set[str] = set()
        self.crawl_delay: float = 0
        self.sitemaps: List[str] = []
    
    def parse(self, content: str, user_agent: str = "*") -> None:
        """Parseia conteúdo de robots.txt."""
        lines = content.split('\n')
        current_user_agent = None
        matching_rules = False
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if ':' not in line:
                continue
            
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()
            
            if directive == 'user-agent':
                current_user_agent = value.lower()
                matching_rules = current_user_agent == user_agent.lower() or current_user_agent == '*'
            
            if not matching_rules:
                continue
            
            if directive == 'disallow':
                if value:
                    self.disallowed_paths.add(value)
            
            elif directive == 'allow':
                if value:
                    self.allowed_paths.add(value)
            
            elif directive == 'crawl-delay':
                try:
                    self.crawl_delay = float(value)
                except ValueError:
                    pass
            
            elif directive == 'sitemap':
                self.sitemaps.append(value)
    
    def is_allowed(self, path: str) -> bool:
        """Verifica se path é permitido pelo robots.txt."""
        # Paths explícitamente permitidos têm prioridade
        for allowed in self.allowed_paths:
            if path.startswith(allowed):
                return True
        
        # Verifica paths bloqueados
        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return False
        
        # Padrão: permitir
        return True


class CrawlerConfig:
    """Configuração do crawler."""
    
    def __init__(
        self,
        delay: float = 1.5,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = "Mozilla/5.0 (compatible; DataCrawler/1.0)",
        max_pages: int = 100,
        respect_robots_txt: bool = True,
        recursive: bool = False,
        exclude_patterns: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        requests_per_minute: Optional[int] = None
    ):
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.max_pages = max_pages
        self.respect_robots_txt = respect_robots_txt
        self.recursive = recursive
        self.exclude_patterns = exclude_patterns or []
        self.blocked_domains = blocked_domains or []
        self.requests_per_minute = requests_per_minute


class Crawler:
    """
    Crawler web ético e robusto.
    
    Implementa:
    - Respeito a robots.txt
    - Retries com backoff exponencial
    - Rate limiting configurável
    - Controle de URLs visitadas
    - Parsing configurável por domínio
    """
    
    def __init__(
        self,
        config: CrawlerConfig,
        sites_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa crawler.
        
        Args:
            config: Configuração do crawler
            sites_config: Configuração de parsers por site
        """
        self.config = config
        self.sites_config = sites_config or {}
        
        # Estado do crawl
        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque()
        self.robots_cache: Dict[str, RobotsTxtParser] = {}
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            delay=config.delay,
            requests_per_minute=config.requests_per_minute
        )
        
        # Cliente HTTP
        self.client = httpx.Client(
            timeout=httpx.Timeout(config.timeout),
            headers={"User-Agent": config.user_agent},
            follow_redirects=True,
            max_redirects=5
        )
        
        # Estatísticas
        self.stats = CrawlerStats()
        
        logger.info(f"Crawler inicializado com delay={config.delay}s, max_pages={config.max_pages}")
    
    def crawl(
        self,
        seed_urls: List[str],
        parser: Optional[Parser] = None
    ) -> List[CrawledPage]:
        """
        Executa crawl a partir de URLs semente.
        
        Args:
            seed_urls: Lista de URLs iniciais
            parser: Parser opcional (se None, usa configuração por domínio)
        
        Returns:
            Lista de CrawledPage com resultados
        """
        results: List[CrawledPage] = []
        
        # Adiciona URLs iniciais à fila
        for url in seed_urls:
            self.url_queue.append(url)
            logger.info(f"URL semente adicionada: {url}")
        
        logger.info(f"Iniciando crawl com {len(seed_urls)} URL(s) semente")
        start_time = time.time()
        
        pages_crawled = 0
        
        while self.url_queue and pages_crawled < self.config.max_pages:
            url = self.url_queue.popleft()
            
            # Verifica se já visitou
            url_hash = hash_url(url)
            if url_hash in self.visited_urls:
                logger.debug(f"URL já visitada: {url}")
                continue
            
            # Verifica exclusões
            if self._should_skip_url(url):
                continue
            
            # Marca como visitada
            self.visited_urls.add(url_hash)
            pages_crawled += 1
            
            # Faz request
            page_result = self._fetch_page(url, parser)
            results.append(page_result)
            
            # Atualiza estatísticas
            self.stats.adicionar_pagina(page_result)
            
            # Extrai links se recursivo
            if self.config.recursive and page_result.sucesso:
                self._extract_and_queue_links(page_result, url)
            
            # Log de progresso
            if pages_crawled % 10 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    f"Progresso: {pages_crawled}/{self.config.max_pages} páginas, "
                    f"{self.stats.empresas_extraidas} empresas, {format_duration(elapsed)} decorridos"
                )
        
        # Finaliza estatísticas
        self.stats.finalizar()
        
        elapsed_total = time.time() - start_time
        logger.info(
            f"Crawl finalizado: {pages_crawled} páginas, "
            f"{self.stats.urls_sucesso} sucesso, {self.stats.urls_falha} falhas, "
            f"{self.stats.empresas_extraidas} empresas extraídas em {format_duration(elapsed_total)}"
        )
        
        return results
    
    def _should_skip_url(self, url: str) -> bool:
        """Verifica se URL deve ser pulada."""
        domain = get_domain(url)
        parsed = urlparse(url)
        
        # Domínio bloqueado
        for blocked in self.config.blocked_domains:
            if blocked in domain:
                logger.debug(f"Domínio bloqueado: {domain}")
                return True
        
        # Pattern de exclusão
        if should_exclude_url(url, self.config.exclude_patterns):
            logger.debug(f"URL excluída por pattern: {url}")
            return True
        
        # Verifica robots.txt
        if self.config.respect_robots_txt:
            robots = self._get_robots_txt(domain)
            if robots and not robots.is_allowed(parsed.path):
                logger.debug(f"URL bloqueada por robots.txt: {url}")
                return True
        
        return False
    
    def _get_robots_txt(self, domain: str) -> Optional[RobotsTxtParser]:
        """Obtém e cacheia robots.txt do domínio."""
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        try:
            robots_url = f"https://{domain}/robots.txt"
            response = self.client.get(robots_url, timeout=5.0)
            
            if response.status_code == 200:
                parser = RobotsTxtParser()
                parser.parse(response.text, self.config.user_agent)
                self.robots_cache[domain] = parser
                logger.debug(f"robots.txt carregado para {domain}")
                return parser
            else:
                logger.debug(f"robots.txt não encontrado para {domain}")
                return None
                
        except Exception as e:
            logger.debug(f"Erro ao buscar robots.txt de {domain}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)),
        reraise=True
    )
    def _fetch_page(self, url: str, parser: Optional[Parser] = None) -> CrawledPage:
        """
        Faz request HTTP para página.
        
        Args:
            url: URL da página
            parser: Parser opcional
        
        Returns:
            CrawledPage com resultado
        """
        start_time = time.time()
        
        # Rate limiting
        self.rate_limiter.wait()
        
        page = CrawledPage(
            url=url,
            status_code=0,
            html_size=0,
            tempo_processamento=0
        )
        
        try:
            # Faz request
            response = self.client.get(url)
            page.status_code = response.status_code
            page.html_size = len(response.content)
            
            # Trata erros HTTP
            if response.status_code >= 400:
                if response.status_code == 429:
                    # Rate limited - espera mais
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = min(int(retry_after), 300)
                    logger.warning(f"Rate limited ({url}), esperando {wait_time}s")
                    time.sleep(wait_time)
                    raise httpx.HTTPStatusError(f"Rate limited: {response.status_code}", request=response.request, response=response)
                
                page.erros.append(f"HTTP {response.status_code}")
                logger.warning(f"HTTP {response.status_code} para {url}")
                return page
            
            # Parseia conteúdo
            html = response.text
            tempo_parse = time.time()
            
            companies = self._parse_content(html, url, parser)
            page.companies = companies
            
            page.tempo_processamento = time.time() - start_time
            
            logger.info(
                f"Página processada: {url} - {len(companies)} empresas, "
                f"{page.html_size} bytes, {page.tempo_processamento:.2f}s"
            )
            
        except httpx.TimeoutException:
            page.erros.append("Timeout")
            logger.error(f"Timeout ao buscar {url}")
        
        except httpx.HTTPStatusError as e:
            if "Rate limited" not in str(e):
                page.erros.append(f"HTTP Error: {str(e)}")
                logger.error(f"HTTP error em {url}: {e}")
        
        except Exception as e:
            page.erros.append(f"Erro: {str(e)}")
            logger.exception(f"Erro inesperado ao buscar {url}")
        
        return page
    
    def _parse_content(
        self,
        html: str,
        url: str,
        parser: Optional[Parser] = None
    ) -> List[Company]:
        """Parseia conteúdo HTML extraindo empresas."""
        domain = get_domain(url)
        
        # Usa parser fornecido ou cria baseado no domínio
        if parser:
            p = parser
        else:
            p = create_parser_for_domain(domain, self.sites_config)
        
        if not p:
            # Parser genérico básico
            logger.debug(f"Usando parser genérico para {domain}")
            return []
        
        # Executa parsing
        result = p.parse(html, url)
        
        if result.errors:
            logger.warning(f"Erros no parsing de {url}: {result.errors}")
        
        return result.companies
    
    def _extract_and_queue_links(self, page: CrawledPage, base_url: str) -> None:
        """Extrai links da página e adiciona à fila se relevante."""
        # Esta implementação básica não extrai links automaticamente
        # Para crawl recursivo real, seria necessário um parser HTML
        # que extraísse todos os links <a href>
        
        # Implementação simplificada: depende do parser retornar
        # URLs relacionadas nos metadados
        pass
    
    def get_stats(self) -> CrawlerStats:
        """Retorna estatísticas do crawl."""
        return self.stats
    
    def close(self) -> None:
        """Fecha recursos do crawler."""
        self.client.close()
        logger.info("Crawler fechado")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def crawl_site(
    url: str,
    sites_config: Dict[str, Any],
    crawler_config: Optional[CrawlerConfig] = None,
    max_pages: int = 50
) -> List[CrawledPage]:
    """
    Função utilitária para crawl rápido de um site.
    
    Args:
        url: URL inicial
        sites_config: Configuração de parsers
        crawler_config: Configuração opcional do crawler
        max_pages: Máximo de páginas para crawlar
    
    Returns:
        Lista de páginas crawladas
    """
    config = crawler_config or CrawlerConfig(max_pages=max_pages)
    
    with Crawler(config, sites_config) as crawler:
        results = crawler.crawl([url])
    
    return results
