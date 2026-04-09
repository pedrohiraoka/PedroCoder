"""
OrbitGuard - Interface de Linha de Comando (CLI).

Interface CLI para validação de trânsitos e priorização de ocultações
usando Typer.

Usage:
    # Validar um trânsito por hostname
    python cli.py validate --hostname "TIC 12345678" --obs-time "2024-01-15T10:30:00"
    
    # Validar por coordenadas
    python cli.py validate --ra 180.123 --dec -45.678 --obs-time "2024-01-15T10:30:00"
    
    # Buscar ocultações
    python cli.py occult --target "1 Ceres" --start-date "2024-01-01" --end-date "2024-02-01"
    
    # Processamento batch
    python cli.py batch --input targets.csv --output results.csv
"""

import typer
from datetime import datetime
from typing import Optional, List
import json
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.validator import TransitValidator, ValidationResult
from core.ephemeris import EphemerisCalculator, OccultationPrioritizer
from core.cross_match import BatchCrossMatcher
from utils.cache import CacheManager
from utils.config import Config

app = typer.Typer(
    name="orbitguard",
    help="OrbitGuard CLI - Validador de Falsos Positivos e Priorizador de Ocultações",
    add_completion=True,
)

cache_manager = CacheManager()


def parse_datetime(dt_str: str) -> datetime:
    """Parse string de datetime em vários formatos."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Formato de data inválido: {dt_str}. Use YYYY-MM-DDTHH:MM:SS ou similar."
    )


@app.command("validate")
def validate_transit(
    hostname: Optional[str] = typer.Option(
        None, "--hostname", "-n", help="Nome do hospedeiro (ex: TIC 12345678)"
    ),
    ra: Optional[float] = typer.Option(
        None, "--ra", "-r", help="Ascensão Reta em graus"
    ),
    dec: Optional[float] = typer.Option(
        None, "--dec", "-d", help="Declinação em graus"
    ),
    obs_time: str = typer.Option(
        ..., "--obs-time", "-t", help="Tempo de observação (UTC) no formato ISO"
    ),
    separation_threshold: float = typer.Option(
        5.0, "--threshold", "-s", help="Limiar de separação em arcsec (padrão: 5.0)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Arquivo de saída JSON (opcional)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo detalhado"),
):
    """
    Valida um trânsito de exoplaneta cruzando com dados de asteroides.
    
    Pode usar hostname (recomendado) ou coordenadas (ra, dec).
    """
    try:
        obs_datetime = parse_datetime(obs_time)
        
        if verbose:
            typer.echo(f"🔍 Iniciando validação para {obs_datetime}...")
        
        validator = TransitValidator(cache_manager=cache_manager)
        
        if hostname:
            if verbose:
                typer.echo(f"📍 Buscando alvo: {hostname}")
            result = validator.validate_by_hostname(
                hostname=hostname,
                obs_time=obs_datetime,
                separation_threshold_arcsec=separation_threshold,
            )
        elif ra is not None and dec is not None:
            if verbose:
                typer.echo(f"📍 Coordenadas: RA={ra}, Dec={dec}")
            result = validator.validate_by_coordinates(
                ra=ra,
                dec=dec,
                obs_time=obs_datetime,
                separation_threshold_arcsec=separation_threshold,
            )
        else:
            typer.echo("❌ Erro: Forneça --hostname OU --ra e --dec")
            raise typer.Exit(code=1)
        
        # Exibe resultados
        display_validation_result(result, verbose=verbose)
        
        # Salva em arquivo se especificado
        if output_file:
            with open(output_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            typer.echo(f"💾 Resultados salvos em: {output_file}")
        
    except Exception as e:
        typer.echo(f"❌ Erro: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)


def display_validation_result(result: ValidationResult, verbose: bool = False):
    """Exibe resultados da validação no terminal."""
    # Status com cores
    status_colors = {
        "GREEN": "✅",
        "YELLOW": "⚠️",
        "RED": "❌",
    }
    status_icon = status_colors.get(result.status, "•")
    
    typer.echo("\n" + "=" * 60)
    typer.echo(f"{status_icon} STATUS: {result.status}")
    typer.echo("=" * 60)
    
    if result.confirmed_planets:
        typer.echo(f"\n🪐 Planetas Confirmados: {len(result.confirmed_planets)}")
        for planet in result.confirmed_planets[:5]:  # Mostra até 5
            planet_name = planet.get('pl_name', 'N/A')
            typer.echo(f"   • {planet_name}")
    
    if result.asteroids:
        typer.echo(f"\n☄️ Asteroides Próximos: {len(result.asteroids)}")
        for ast in result.asteroids[:5]:  # Mostra até 5
            typer.echo(
                f"   • {ast['name']}: {ast['separation_arcsec']:.2f} arcsec, "
                f"mag {ast['magnitude']:.1f}"
            )
    
    if result.lightcurve_available:
        typer.echo(f"\n📈 Curva de luz disponível: {result.lightcurve_url}")
    
    if verbose and result.raw_data:
        typer.echo("\n📄 Dados brutos (JSON):")
        typer.echo(json.dumps(result.to_dict(), indent=2))


@app.command("occult")
def find_occultations(
    target: str = typer.Option(
        ..., "--target", "-t", help="Nome do alvo (asteroide/cometa)"
    ),
    start_date: str = typer.Option(
        ..., "--start-date", "-s", help="Data inicial (YYYY-MM-DD)"
    ),
    end_date: str = typer.Option(
        ..., "--end-date", "-e", help="Data final (YYYY-MM-DD)"
    ),
    max_magnitude: float = typer.Option(
        15.0, "--max-mag", "-m", help="Magnitude máxima da estrela (padrão: 15.0)"
    ),
    max_separation: float = typer.Option(
        1.0, "--max-sep", "-x", help="Separação máxima em arcsec (padrão: 1.0)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Arquivo de saída CSV/JSON"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo detalhado"),
):
    """
    Busca eventos de ocultação estelar por um asteroide ou cometa.
    
    Identifica estrelas no caminho da ocultação e prioriza aquelas
    com exoplanetas confirmados.
    """
    try:
        date_start = parse_datetime(start_date).date()
        date_end = parse_datetime(end_date).date()
        
        if verbose:
            typer.echo(f"🔭 Buscando ocultações para {target}...")
            typer.echo(f"📅 Período: {date_start} a {date_end}")
        
        prioritizer = OccultationPrioritizer(cache_manager=cache_manager)
        
        results = prioritizer.find_occultations(
            target_name=target,
            date_start=date_start,
            date_end=date_end,
            max_magnitude=max_magnitude,
            max_separation_arcsec=max_separation,
        )
        
        # Exibe resultados
        typer.echo("\n" + "=" * 60)
        typer.echo(f"📋 Eventos de Ocultação Encontrados: {len(results)}")
        typer.echo("=" * 60)
        
        if results:
            # Ordena por prioridade
            sorted_results = sorted(
                results, key=lambda x: x.get("priority_score", 0), reverse=True
            )
            
            for i, event in enumerate(sorted_results[:10], 1):  # Top 10
                star_name = event.get("star_name", "N/A")
                priority = event.get("priority_score", 0)
                has_planet = "🪐" if event.get("has_exoplanet") else ""
                typer.echo(
                    f"{i:2d}. {star_name} {has_planet} (Score: {priority:.2f})"
                )
                
                if verbose:
                    date = event.get("event_date", "N/A")
                    sep = event.get("separation_arcsec", 0)
                    typer.echo(f"    Data: {date}, Sep: {sep:.3f} arcsec")
        else:
            typer.echo("ℹ️ Nenhum evento encontrado.")
        
        # Salva em arquivo
        if output_file:
            suffix = output_file.suffix.lower()
            if suffix == ".json":
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
            elif suffix == ".csv":
                import pandas as pd
                df = pd.DataFrame(results)
                df.to_csv(output_file, index=False)
            else:
                # Default JSON
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
            
            typer.echo(f"💾 Resultados salvos em: {output_file}")
        
    except Exception as e:
        typer.echo(f"❌ Erro: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)


@app.command("batch")
def process_batch(
    input_file: Path = typer.Option(
        ..., "--input", "-i", help="Arquivo CSV de entrada"
    ),
    output_file: Path = typer.Option(
        ..., "--output", "-o", help="Arquivo CSV de saída"
    ),
    chunk_size: int = typer.Option(
        50, "--chunk-size", "-c", help="Tamanho do chunk (padrão: 50)"
    ),
    max_workers: int = typer.Option(
        4, "--workers", "-w", help="Número de workers paralelos (padrão: 4)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo detalhado"),
):
    """
    Processa múltiplos alvos em batch a partir de um arquivo CSV.
    
    O CSV deve conter colunas: ra, dec, obs_time_utc
    """
    try:
        if not input_file.exists():
            typer.echo(f"❌ Arquivo não encontrado: {input_file}")
            raise typer.Exit(code=1)
        
        import pandas as pd
        
        if verbose:
            typer.echo(f"📁 Lendo arquivo: {input_file}")
        
        df = pd.read_csv(input_file)
        
        required_cols = {"ra", "dec", "obs_time_utc"}
        if not required_cols.issubset(df.columns):
            typer.echo(
                f"❌ Colunas necessárias: {required_cols}\n"
                f"Colunas encontradas: {df.columns.tolist()}"
            )
            raise typer.Exit(code=1)
        
        if verbose:
            typer.echo(f"📊 Processando {len(df)} alvos...")
        
        batch_matcher = BatchCrossMatcher(
            cache_manager=cache_manager,
            max_workers=max_workers,
        )
        
        all_results = []
        total_chunks = (len(df) // chunk_size) + 1
        
        with typer.progress_bar(
            length=total_chunks, label="Processando chunks"
        ) as progress:
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                chunk_results = batch_matcher.process_chunk(chunk)
                all_results.extend(chunk_results)
                progress.update(1)
        
        # Converte para DataFrame
        results_data = [r.to_dict() for r in all_results]
        results_df = pd.DataFrame(results_data)
        
        # Salva resultados
        results_df.to_csv(output_file, index=False)
        
        # Estatísticas
        total = len(results_df)
        cross_matches = results_df["has_cross_match"].sum() if "has_cross_match" in results_df.columns else 0
        red_alerts = (results_df["status"] == "RED").sum() if "status" in results_df.columns else 0
        
        typer.echo("\n" + "=" * 60)
        typer.echo("📊 Resumo do Processamento Batch")
        typer.echo("=" * 60)
        typer.echo(f"Total processado: {total}")
        typer.echo(f"Eventos cruzados: {cross_matches}")
        typer.echo(f"Alertas vermelhos: {red_alerts}")
        typer.echo(f"💾 Resultados salvos em: {output_file}")
        
    except Exception as e:
        typer.echo(f"❌ Erro: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)


@app.command("info")
def show_info():
    """Exibe informações sobre o OrbitGuard e status do cache."""
    typer.echo("\n" + "=" * 60)
    typer.echo("🔭 OrbitGuard - Informações")
    typer.echo("=" * 60)
    
    typer.echo(f"\nVersão: 1.0.0")
    typer.echo(f"Cache path: {config.cache_db_path.parent}")
    
    # Stats do cache
    cache_stats = cache_manager.get_stats()
    typer.echo(f"\n📦 Estatísticas do Cache:")
    typer.echo(f"   Tamanho: {cache_stats.get('size_mb', 0):.2f} MB")
    typer.echo(f"   Entradas: {cache_stats.get('entries', 0)}")
    
    typer.echo(f"\n⚙️ Limites de API:")
    typer.echo(f"   JPL Horizons: {config.JPL_HORIZONS_RATE_LIMIT} req/min")
    typer.echo(f"   Exoplanet Archive: {config.EXOPLANET_ARCHIVE_RATE_LIMIT} req/min")
    typer.echo(f"   Gaia: {config.GAIA_RATE_LIMIT} req/min")
    
    typer.echo("\n📚 Documentação: https://github.com/orbitguard/docs")


@app.command("clear-cache")
def clear_cache(
    force: bool = typer.Option(False, "--force", "-f", help="Confirma sem perguntar"),
):
    """Limpa todo o cache local."""
    if not force:
        confirm = typer.confirm("Tem certeza que deseja limpar todo o cache?")
        if not confirm:
            raise typer.Abort()
    
    cache_manager.clear()
    typer.echo("✅ Cache limpo com sucesso!")


@app.callback()
def main_callback():
    """OrbitGuard CLI - Ferramenta de validação de trânsitos e ocultações."""
    pass


if __name__ == "__main__":
    app()
