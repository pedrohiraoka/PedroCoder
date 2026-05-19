"""Main CLI entry point for FastDL."""

import typer
from rich.console import Console
from pathlib import Path
from typing import Optional

from src.core.downloader import DownloadManager
from src.utils.config import Config

app = typer.Typer(
    name="fastdl",
    help="Acelerador de downloads CLI de alta performance para 2026",
    add_completion=False,
)
console = Console()


@app.command()
def download(
    url: str = typer.Argument(..., help="URL do arquivo para download"),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Nome do arquivo de saída (padrão: nome da URL)"
    ),
    connections: Optional[int] = typer.Option(
        None, "-c", "--connections", help="Número máximo de conexões simultâneas"
    ),
    resume: bool = typer.Option(
        False, "-r", "--resume", help="Retomar download interrompido se disponível"
    ),
    limit_rate: Optional[str] = typer.Option(
        None, "-l", "--limit", help="Limitar velocidade (ex: 10M, 500K)"
    ),
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Modo silencioso (apenas erros)"
    ),
) -> None:
    """Baixa um arquivo usando múltiplas conexões paralelas.
    
    Exemplo:
        fastdl download https://example.com/arquivo.zip -o meu_arquivo.zip
        fastdl dl https://example.com/grande.iso -c 16 --resume
    """
    config = Config.load()
    
    if connections:
        config.max_connections = min(connections, 64)
    
    if limit_rate:
        config.rate_limit = limit_rate
    
    manager = DownloadManager(config=config, quiet=quiet)
    
    try:
        manager.download(url=url, dest_path=output, resume=resume)
    except KeyboardInterrupt:
        console.print("\n[yellow]Download interrompido pelo usuário.[/yellow]")
        console.print("[dim]Estado salvo. Use --resume para continuar.[/dim]")
        raise SystemExit(130)
    except Exception as e:
        console.print(f"\n[red]Erro:[/red] {e}")
        raise SystemExit(1)


@app.command(name="config")
def show_config() -> None:
    """Mostra a configuração atual e localização do arquivo de config."""
    config = Config.load()
    config_path = Config.get_config_path()
    
    console.print(f"[bold]Configuração FastDL[/bold]\n")
    console.print(f"Arquivo de config: [cyan]{config_path}[/cyan]")
    console.print(f"\n[bold]Valores Atuais:[/bold]")
    console.print(f"  Max Conexões: {config.max_connections}")
    console.print(f"  Timeout: {config.timeout}s")
    console.print(f"  Retry Max: {config.max_retries}")
    console.print(f"  Rate Limit: {config.rate_limit or 'Ilimitado'}")
    console.print(f"  Dir Download: {config.download_dir}")


@app.command()
def version() -> None:
    """Mostra a versão do FastDL."""
    console.print("[bold green]FastDL[/bold green] v0.1.0")
    console.print("Python Async Download Accelerator for 2026")


# Alias comum
dl = download

if __name__ == "__main__":
    app()
