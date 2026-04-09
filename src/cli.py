"""
CLI - Interface de Linha de Comando

Interface CLI usando Typer para controle do crawler.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List

import typer
import yaml

from src.crawler import Crawler, CrawlerConfig
from src.storage import Storage, StorageFormat, export_companies
from src.utils import setup_logging, format_duration
from src.models import CrawlerStats


# Inicializa app Typer
app = typer.Typer(
    name="crawler",
    help="MVP Crawler/Web Scraper - Extração ética de dados web",
    add_completion=False
)


def load_config(config_path: str) -> dict:
    """Carrega configuração YAML."""
    path = Path(config_path)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


@app.command()
def crawl(
    url: str = typer.Argument(..., help="URL inicial para crawl"),
    config_file: str = typer.Option(
        "config/sites.yaml", 
        "--config", "-c",
        help="Arquivo de configuração YAML"
    ),
    output_dir: str = typer.Option(
        "./output",
        "--output-dir", "-o",
        help="Diretório para arquivos de saída"
    ),
    output_format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Formato de saída: json, csv, sqlite"
    ),
    database: Optional[str] = typer.Option(
        None,
        "--database", "-d",
        help="Banco de dados SQLite para persistência"
    ),
    max_pages: int = typer.Option(
        50,
        "--max-pages", "-m",
        help="Máximo de páginas para crawlar"
    ),
    delay: float = typer.Option(
        1.5,
        "--delay", "-D",
        help="Delay entre requisições (segundos)"
    ),
    timeout: int = typer.Option(
        30,
        "--timeout", "-t",
        help="Timeout da requisição (segundos)"
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Habilitar crawl recursivo"
    ),
    no_robots: bool = typer.Option(
        False,
        "--no-robots",
        help="Ignorar robots.txt"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Log detalhado (DEBUG)"
    ),
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file", "-l",
        help="Arquivo de log"
    )
):
    """
    Executa crawl em uma URL.
    
    Exemplo:
        python main.py crawl https://exemplo.com/empresas
    
    Com opções avançadas:
        python main.py crawl https://exemplo.com --max-pages 100 --delay 2.0 --output csv
    """
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(level=level, log_file=log_file)
    
    logger.info("=" * 60)
    logger.info("MVP Crawler - Iniciando")
    logger.info("=" * 60)
    
    # Carrega configuração
    config_data = load_config(config_file)
    global_config = config_data.get('global', {})
    sites_config = config_data.get('sites', {})
    
    # Merge de configurações CLI e arquivo
    final_delay = delay if delay != 1.5 else global_config.get('delay', delay)
    final_timeout = timeout if timeout != 30 else global_config.get('timeout', timeout)
    final_max_pages = max_pages if max_pages != 50 else global_config.get('max_pages', max_pages)
    respect_robots = not no_robots and global_config.get('respect_robots_txt', True)
    
    # Configuração do crawler
    crawler_config = CrawlerConfig(
        delay=final_delay,
        timeout=final_timeout,
        max_retries=global_config.get('max_retries', 3),
        user_agent=global_config.get('user_agent', "Mozilla/5.0 (compatible; DataCrawler/1.0)"),
        max_pages=final_max_pages,
        respect_robots_txt=respect_robots,
        recursive=recursive,
        exclude_patterns=config_data.get('exclude_patterns', []),
        blocked_domains=config_data.get('blocked_domains', [])
    )
    
    logger.info(f"URL alvo: {url}")
    logger.info(f"Configurações:")
    logger.info(f"  - Delay: {final_delay}s")
    logger.info(f"  - Timeout: {final_timeout}s")
    logger.info(f"  - Max páginas: {final_max_pages}")
    logger.info(f"  - Respeitar robots.txt: {respect_robots}")
    logger.info(f"  - Recursivo: {recursive}")
    
    # Executa crawl
    try:
        with Crawler(crawler_config, sites_config) as crawler:
            results = crawler.crawl([url])
            
            # Extrai companies dos resultados
            all_companies = []
            for page in results:
                all_companies.extend(page.companies)
                if page.company:
                    all_companies.append(page.company)
            
            logger.info(f"\nTotal de empresas extraídas: {len(all_companies)}")
            
            # Exporta dados
            if all_companies:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                
                # Determina formato
                try:
                    fmt = StorageFormat(output_format.lower())
                except ValueError:
                    logger.warning(f"Formato '{output_format}' não reconhecido, usando JSON")
                    fmt = StorageFormat.JSON
                
                # Salva no formato solicitado
                storage = Storage(output_dir)
                filepath = storage.save(all_companies, format=fmt)
                logger.info(f"Dados salvos em: {filepath}")
                
                # Salva banco se especificado
                if database:
                    db_filepath = storage.save(all_companies, format=StorageFormat.SQLITE, filename=database)
                    logger.info(f"Banco de dados salvo em: {db_filepath}")
                
                # Opcional: salva também em JSON para backup
                if fmt != StorageFormat.JSON:
                    json_path = storage.save(all_companies, format=StorageFormat.JSON)
                    logger.debug(f"Backup JSON: {json_path}")
            
            # Estatísticas finais
            stats = crawler.get_stats()
            logger.info("\n" + "=" * 60)
            logger.info("Estatísticas Finais")
            logger.info("=" * 60)
            logger.info(f"Páginas visitadas: {stats.urls_visitadas}")
            logger.info(f"Sucesso: {stats.urls_sucesso}")
            logger.info(f"Falhas: {stats.urls_falha}")
            logger.info(f"Empresas extraídas: {stats.empresas_extraidas}")
            logger.info(f"Tempo total: {format_duration(stats.tempo_total)}")
            logger.info(f"Tempo médio/requisição: {stats.tempo_medio_por_requisicao:.2f}s")
            
            # Retorna código de saída apropriado
            if stats.urls_falha > stats.urls_sucesso:
                logger.warning("Mais falhas que sucessos - verifique logs")
                return 1
            
            return 0
            
    except KeyboardInterrupt:
        logger.error("\nInterrupt pelo usuário")
        return 130
    except Exception as e:
        logger.exception(f"Erro durante crawl: {e}")
        return 1


@app.command()
def validate(
    config_file: str = typer.Argument(
        "config/sites.yaml",
        help="Arquivo de configuração para validar"
    )
):
    """
    Valida arquivo de configuração.
    
    Verifica sintaxe YAML e estrutura esperada.
    """
    logger = setup_logging(level=logging.INFO)
    
    path = Path(config_file)
    if not path.exists():
        logger.error(f"Arquivo não encontrado: {config_file}")
        raise typer.Exit(code=1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            logger.warning("Arquivo vazio ou inválido")
            return
        
        # Valida estrutura básica
        errors = []
        
        if 'global' in config:
            global_cfg = config['global']
            if 'delay' in global_cfg and not isinstance(global_cfg['delay'], (int, float)):
                errors.append("global.delay deve ser numérico")
            if 'timeout' in global_cfg and not isinstance(global_cfg['timeout'], int):
                errors.append("global.timeout deve ser inteiro")
        
        if 'sites' in config:
            sites = config['sites']
            if not isinstance(sites, dict):
                errors.append("sites deve ser um dicionário")
            else:
                for domain, site_config in sites.items():
                    if not isinstance(site_config, dict):
                        errors.append(f"Configuração de '{domain}' deve ser dicionário")
                    elif 'listagem' not in site_config and 'campos' not in site_config:
                        logger.warning(f"Site '{domain}' sem configuração de listagem ou campos")
        
        if errors:
            logger.error("Erros de validação:")
            for error in errors:
                logger.error(f"  - {error}")
            raise typer.Exit(code=1)
        
        logger.info(f"Configuração válida: {config_file}")
        logger.info(f"  - Domínios configurados: {len(config.get('sites', {}))}")
        logger.info(f"  - Domínios bloqueados: {len(config.get('blocked_domains', []))}")
        logger.info(f"  - Padrões de exclusão: {len(config.get('exclude_patterns', []))}")
        
    except yaml.YAMLError as e:
        logger.error(f"Erro de sintaxe YAML: {e}")
        raise typer.Exit(code=1)


@app.command()
def info():
    """
    Mostra informações sobre o crawler.
    """
    logger = setup_logging(level=logging.INFO)
    
    print("""
╔══════════════════════════════════════════════════════════╗
║           MVP Crawler/Web Scraper v1.0.0                 ║
╠══════════════════════════════════════════════════════════╣
║  Ferramenta ética para extração de dados web             ║
║                                                          ║
║  Recursos:                                               ║
║  ✓ Respeito a robots.txt                                 ║
║  ✓ Retries com backoff exponencial                       ║
║  ✓ Rate limiting configurável                            ║
║  ✓ Parsing CSS e XPath                                   ║
║  ✓ Validação Pydantic                                    ║
║  ✓ Export JSON, CSV, SQLite                              ║
║                                                          ║
║  Uso básico:                                             ║
║  python main.py crawl https://exemplo.com                ║
║                                                          ║
║  Documentação completa: README.md                        ║
╚══════════════════════════════════════════════════════════╝
    """)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Mostra versão"
    )
):
    """
    MVP Crawler - CLI principal
    """
    if version:
        print("MVP Crawler v1.0.0")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
