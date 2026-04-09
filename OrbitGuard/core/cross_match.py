"""
OrbitGuard - Módulo de Cross-Match em Batch.

Processa múltiplos alvos simultaneamente para detecção de eventos cruzados
entre trânsitos de exoplanetas e posições de asteroides/cometas.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import pandas as pd

from .validator import TransitValidator, ValidationResult
from .ephemeris import EphemerisCalculator, OccultationPrioritizer
from ..utils.cache import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class CrossMatchResult:
    """Resultado de um cross-match para um único alvo."""

    ra: float
    dec: float
    obs_time: datetime
    status: str  # GREEN, YELLOW, RED
    has_cross_match: bool = False
    separation_arcsec: Optional[float] = None
    asteroid_name: Optional[str] = None
    asteroid_magnitude: Optional[float] = None
    confirmed_planets: List[Dict[str, Any]] = field(default_factory=list)
    lightcurve_available: bool = False
    lightcurve_url: Optional[str] = None
    priority_score: float = 0.0
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável."""
        return {
            "ra": self.ra,
            "dec": self.dec,
            "obs_time": self.obs_time.isoformat() if self.obs_time else None,
            "status": self.status,
            "has_cross_match": self.has_cross_match,
            "separation_arcsec": self.separation_arcsec,
            "asteroid_name": self.asteroid_name,
            "asteroid_magnitude": self.asteroid_magnitude,
            "confirmed_planets": len(self.confirmed_planets),
            "lightcurve_available": self.lightcurve_available,
            "lightcurve_url": self.lightcurve_url,
            "priority_score": self.priority_score,
        }


class BatchCrossMatcher:
    """
    Processador de cross-match em batch para múltiplos alvos.
    
    Usa processamento paralelo para validar centenas de alvos
    simultaneamente, aplicando a lógica dos módulos de validação
    e efemérides.
    
    Attributes:
        cache_manager: Gerenciador de cache compartilhado
        max_workers: Número máximo de workers paralelos
        validator: Instância do validador de trânsitos
        ephemeris_calc: Calculadora de efemérides
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        max_workers: int = 4,
        separation_threshold: float = 5.0,
    ):
        """
        Inicializa o processador batch.
        
        Args:
            cache_manager: Gerenciador de cache
            max_workers: Número de threads paralelas
            separation_threshold: Limiar de separação em arcsec
        """
        self.cache_manager = cache_manager or CacheManager()
        self.max_workers = max_workers
        self.separation_threshold = separation_threshold
        
        self.validator = TransitValidator(cache_manager=self.cache_manager)
        self.ephemeris_calc = EphemerisCalculator(cache_manager=self.cache_manager)

    def process_chunk(
        self,
        chunk_df: pd.DataFrame,
    ) -> List[CrossMatchResult]:
        """
        Processa um chunk de dados em paralelo.
        
        Args:
            chunk_df: DataFrame com colunas [ra, dec, obs_time_utc]
        
        Returns:
            Lista de CrossMatchResult para cada alvo processado
        """
        results = []
        
        # Prepara tarefas
        tasks = []
        for idx, row in chunk_df.iterrows():
            try:
                ra = float(row["ra"])
                dec = float(row["dec"])
                obs_time = parse_obs_time(row["obs_time_utc"])
                
                tasks.append((ra, dec, obs_time))
            except Exception as e:
                logger.warning(f"Linha {idx} inválida: {e}")
                # Cria resultado de erro
                results.append(CrossMatchResult(
                    ra=float(row.get("ra", 0)),
                    dec=float(row.get("dec", 0)),
                    obs_time=datetime.now(),
                    status="ERROR",
                    raw_data={"error": str(e)},
                ))
        
        # Processa em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._process_single, *task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Erro ao processar tarefa {task}: {e}")
                    ra, dec, obs_time = task
                    results.append(CrossMatchResult(
                        ra=ra,
                        dec=dec,
                        obs_time=obs_time,
                        status="ERROR",
                        raw_data={"error": str(e)},
                    ))
        
        logger.info(f"Processadas {len(results)} entradas no chunk")
        return results

    def _process_single(
        self,
        ra: float,
        dec: float,
        obs_time: datetime,
    ) -> CrossMatchResult:
        """
        Processa um único alvo.
        
        Args:
            ra: Ascensão reta em graus
            dec: Declinação em graus
            obs_time: Tempo de observação
        
        Returns:
            CrossMatchResult com os dados do cruzamento
        """
        try:
            # Executa validação
            validation = self.validator.validate_by_coordinates(
                ra=ra,
                dec=dec,
                obs_time=obs_time,
                separation_threshold_arcsec=self.separation_threshold,
            )
            
            # Determina se há cross-match
            has_cross_match = (
                validation.status == "RED" or 
                (validation.asteroids and len(validation.asteroids) > 0)
            )
            
            # Extrai dados do asteroide mais próximo
            asteroid_name = None
            asteroid_mag = None
            separation = None
            
            if validation.asteroids and len(validation.asteroids) > 0:
                closest = validation.asteroids[0]
                asteroid_name = closest.get("name")
                asteroid_mag = closest.get("magnitude")
                separation = closest.get("separation_arcsec")
            
            # Calcula score de prioridade
            priority_score = self._calculate_priority_score(
                status=validation.status,
                num_asteroids=len(validation.asteroids) if validation.asteroids else 0,
                num_planets=len(validation.confirmed_planets) if validation.confirmed_planets else 0,
                separation=separation,
            )
            
            result = CrossMatchResult(
                ra=ra,
                dec=dec,
                obs_time=obs_time,
                status=validation.status,
                has_cross_match=has_cross_match,
                separation_arcsec=separation,
                asteroid_name=asteroid_name,
                asteroid_magnitude=asteroid_mag,
                confirmed_planets=validation.confirmed_planets or [],
                lightcurve_available=validation.lightcurve_available,
                lightcurve_url=validation.lightcurve_url,
                priority_score=priority_score,
                raw_data=validation.to_dict(),
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento single ({ra}, {dec}): {e}")
            raise

    def _calculate_priority_score(
        self,
        status: str,
        num_asteroids: int,
        num_planets: int,
        separation: Optional[float],
    ) -> float:
        """
        Calcula score de prioridade para um evento cruzado.
        
        Critérios:
        - Status RED: +50 pontos
        - Status YELLOW: +25 pontos
        - Múltiplos asteroides: +5 por asteroide (max 20)
        - Planetas confirmados: +10 por planeta (max 30)
        - Separação muito pequena (<1 arcsec): +20 pontos
        
        Args:
            status: Status da validação
            num_asteroids: Número de asteroides detectados
            num_planets: Número de planetas confirmados
            separation: Separação angular em arcsec
        
        Returns:
            Score de prioridade (0-100)
        """
        score = 0.0
        
        # Status base
        if status == "RED":
            score += 50.0
        elif status == "YELLOW":
            score += 25.0
        
        # Múltiplos asteroides
        score += min(num_asteroids * 5, 20)
        
        # Planetas confirmados
        score += min(num_planets * 10, 30)
        
        # Separação crítica
        if separation is not None and separation < 1.0:
            score += 20.0
        
        return min(score, 100.0)

    def process_file(
        self,
        input_path: str,
        output_path: str,
        chunk_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Processa um arquivo CSV completo.
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída
            chunk_size: Tamanho de cada chunk
        
        Returns:
            Dicionário com estatísticas do processamento
        """
        # Lê o arquivo
        df = pd.read_csv(input_path)
        
        # Valida colunas
        required_cols = {"ra", "dec", "obs_time_utc"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Colunas necessárias: {required_cols}")
        
        all_results = []
        total_chunks = (len(df) // chunk_size) + 1
        
        logger.info(f"Processando {len(df)} alvos em {total_chunks} chunks")
        
        # Processa em chunks
        for i in range(0, len(df), chunk_size):
            chunk_df = df.iloc[i : i + chunk_size]
            chunk_results = self.process_chunk(chunk_df)
            all_results.extend(chunk_results)
            
            logger.info(f"Chunk {i//chunk_size + 1}/{total_chunks} completo")
        
        # Salva resultados
        results_data = [r.to_dict() for r in all_results]
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(output_path, index=False)
        
        # Estatísticas
        stats = {
            "total_processed": len(all_results),
            "cross_matches": sum(1 for r in all_results if r.has_cross_match),
            "red_alerts": sum(1 for r in all_results if r.status == "RED"),
            "yellow_alerts": sum(1 for r in all_results if r.status == "YELLOW"),
            "green_clear": sum(1 for r in all_results if r.status == "GREEN"),
            "errors": sum(1 for r in all_results if r.status == "ERROR"),
            "output_file": output_path,
        }
        
        logger.info(f"Processamento completo: {stats}")
        return stats


def parse_obs_time(time_value: Any) -> datetime:
    """
    Parse de tempo de observação em vários formatos.
    
    Args:
        time_value: Valor do tempo (string, timestamp, etc)
    
    Returns:
        datetime em UTC
    
    Raises:
        ValueError: Se o formato não for reconhecido
    """
    if isinstance(time_value, datetime):
        return time_value
    
    if isinstance(time_value, str):
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_value, fmt)
            except ValueError:
                continue
        
        # Tenta ISO format com timezone
        try:
            # Remove timezone info se presente
            clean_time = time_value.replace("Z", "").replace("+00:00", "")
            return datetime.fromisoformat(clean_time)
        except ValueError:
            pass
    
    # Tenta converter de timestamp
    try:
        return datetime.fromtimestamp(float(time_value))
    except (ValueError, TypeError, OSError):
        pass
    
    raise ValueError(
        f"Formato de tempo não reconhecido: {time_value}. "
        "Use ISO format (YYYY-MM-DDTHH:MM:SS)"
    )


# Exportações públicas
__all__ = [
    "BatchCrossMatcher",
    "CrossMatchResult",
    "parse_obs_time",
]
