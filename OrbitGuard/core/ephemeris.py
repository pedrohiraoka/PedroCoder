"""
OrbitGuard - Módulo de Efemérides e Ocultações.

Calcula efemérides precisas de asteroides e cometas usando JPL Horizons,
identifica estrelas de fundo no caminho de ocultação e prioriza eventos
com base em critérios científicos.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass, field

import astropy.units as u
from astropy.coordinates import SkyCoord, Angle
from astropy.time import Time
import pandas as pd

try:
    from astroquery.jplhorizons import Horizons
    from astroquery.gaia import Gaia
except ImportError as e:
    logging.warning(f"astroquery não disponível: {e}")

from .catalog import JPLHorizonsQuery, ExoplanetCatalog
from ..utils.cache import CacheManager
from ..utils.config import Config, API_LIMITS

logger = logging.getLogger(__name__)


@dataclass
class EphemerisData:
    """Dados de efemérides para um pequeno corpo."""

    target_name: str
    epoch: Time
    ra: float  # graus
    dec: float  # graus
    ra_rate: float  # arcsec/hora
    dec_rate: float  # arcsec/hora
    distance: float  # AU
    velocity: float  # km/s
    magnitude: Optional[float] = None
    elongation: Optional[float] = None  # graus
    phase_angle: Optional[float] = None  # graus


@dataclass
class OccultationEvent:
    """Evento de ocultação estelar."""

    star_name: str
    star_coord: SkyCoord
    event_time: Time
    separation_arcsec: float
    target_name: str
    target_mag: Optional[float] = None
    star_mag: Optional[float] = None
    duration_sec: Optional[float] = None
    has_exoplanet: bool = False
    planet_names: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    gaia_source_id: Optional[str] = None


class EphemerisCalculator:
    """
    Calculadora de efemérides para pequenos corpos do Sistema Solar.
    
    Usa JPL Horizons para obter posições precisas de asteroides e cometas
    em qualquer instante de tempo.
    
    Attributes:
        cache_manager: Gerenciador de cache para consultas JPL
        default_step: Passo de tempo padrão para efemérides (minutos)
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        default_step: float = 60.0,
    ):
        """
        Inicializa a calculadora de efemérides.
        
        Args:
            cache_manager: Gerenciador de cache opcional
            default_step: Passo de tempo em minutos para efemérides
        """
        self.cache_manager = cache_manager or CacheManager()
        self.default_step = default_step * u.minute
        self.horizons_query = JPLHorizonsQuery()

    def get_ephemeris(
        self,
        target_name: str,
        obs_time: datetime,
        location: Optional[str] = "@geo",
    ) -> EphemerisData:
        """
        Obtém efemérides para um alvo em um instante específico.
        
        Args:
            target_name: Nome do alvo (ex: "1 Ceres", "2 Pallas")
            obs_time: Tempo de observação
            location: Localização do observador (padrão: geocêntrico)
        
        Returns:
            EphemerisData com posição e parâmetros orbitais
        
        Raises:
            ValueError: Se o alvo não for encontrado
            TimeoutError: Se a consulta JPL timeout
        """
        # Tenta cache primeiro
        cache_key = f"ephemeris:{target_name}:{obs_time.isoformat()}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Cache hit para {cache_key}")
            return EphemerisData(**cached)

        try:
            # Consulta JPL Horizons
            eph = self.horizons_query.get_ephemeris(
                target_name=target_name,
                epochs=obs_time,
                location=location,
            )

            if eph is None or len(eph) == 0:
                raise ValueError(f"Alvo não encontrado: {target_name}")

            row = eph[0]

            # Extrai dados
            data = EphemerisData(
                target_name=target_name,
                epoch=Time(row["datetime_jd"], format="jd"),
                ra=float(row["RA"]),
                dec=float(row["DEC"]),
                ra_rate=float(row.get("RA_rate", 0)),
                dec_rate=float(row.get("DEC_rate", 0)),
                distance=float(row["delta"]),
                velocity=float(row.get("v", 0)),
                magnitude=float(row.get("V", 0)) if "V" in row else None,
                elongation=float(row.get("elong", 0)) if "elong" in row else None,
                phase_angle=float(row.get("phaseangle", 0))
                if "phaseangle" in row
                else None,
            )

            # Salva no cache
            self.cache_manager.set(
                cache_key,
                {
                    "target_name": data.target_name,
                    "epoch": data.epoch.iso,
                    "ra": data.ra,
                    "dec": data.dec,
                    "ra_rate": data.ra_rate,
                    "dec_rate": data.dec_rate,
                    "distance": data.distance,
                    "velocity": data.velocity,
                    "magnitude": data.magnitude,
                    "elongation": data.elongation,
                    "phase_angle": data.phase_angle,
                },
                ttl_hours=24,
            )

            return data

        except Exception as e:
            logger.error(f"Erro ao obter efemérides para {target_name}: {e}")
            raise

    def generate_ephemeris_range(
        self,
        target_name: str,
        start_time: datetime,
        end_time: datetime,
        step_minutes: float = 60.0,
    ) -> List[EphemerisData]:
        """
        Gera efemérides para um intervalo de tempo.
        
        Args:
            target_name: Nome do alvo
            start_time: Tempo inicial
            end_time: Tempo final
            step_minutes: Passo em minutos
        
        Returns:
            Lista de EphemerisData para cada passo
        """
        ephemerides = []
        current_time = start_time

        while current_time <= end_time:
            try:
                eph = self.get_ephemeris(target_name, current_time)
                ephemerides.append(eph)
            except Exception as e:
                logger.warning(
                    f"Falha ao obter efemérides em {current_time}: {e}"
                )

            current_time += timedelta(minutes=step_minutes)

        logger.info(
            f"Geradas {len(ephemerides)} efemérides para {target_name}"
        )
        return ephemerides

    def calculate_closest_approach(
        self,
        target_name: str,
        star_coord: SkyCoord,
        start_time: datetime,
        end_time: datetime,
        step_minutes: float = 10.0,
    ) -> Tuple[datetime, float]:
        """
        Calcula o momento de maior aproximação entre um alvo e uma estrela.
        
        Args:
            target_name: Nome do alvo
            star_coord: Coordenadas da estrela
            start_time: Início da busca
            end_time: Fim da busca
            step_minutes: Passo temporal em minutos
        
        Returns:
            Tupla (tempo_de_máxima_aproximação, separação_mínima_em_arcsec)
        """
        ephemerides = self.generate_ephemeris_range(
            target_name, start_time, end_time, step_minutes
        )

        if not ephemerides:
            raise ValueError("Nenhuma efeméride gerada")

        min_separation = float("inf")
        closest_time = start_time

        for eph in ephemerides:
            target_coord = SkyCoord(
                ra=eph.ra * u.deg,
                dec=eph.dec * u.deg,
            )

            separation = target_coord.separation(star_coord).arcsec

            if separation < min_separation:
                min_separation = separation
                closest_time = eph_epoch_to_datetime(eph.epoch)

        return closest_time, min_separation


class OccultationPrioritizer:
    """
    Priorizador de eventos de ocultação estelar.
    
    Identifica estrelas no caminho de asteroides/cometas e as ranqueia
    por prioridade científica baseado em:
    - Presença de exoplanetas confirmados
    - Magnitude da estrela
    - Duração estimada da ocultação
    - Separação angular mínima
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        exoplanet_catalog: Optional[ExoplanetCatalog] = None,
    ):
        """
        Inicializa o priorizador.
        
        Args:
            cache_manager: Gerenciador de cache
            exoplanet_catalog: Catálogo de exoplanetas para cruzamento
        """
        self.cache_manager = cache_manager or CacheManager()
        self.exoplanet_catalog = exoplanet_catalog or ExoplanetCatalog()
        self.ephemeris_calc = EphemerisCalculator(cache_manager=self.cache_manager)

    def find_occultations(
        self,
        target_name: str,
        date_start: date,
        date_end: date,
        max_magnitude: float = 15.0,
        max_separation_arcsec: float = 1.0,
        search_radius_deg: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Busca eventos de ocultação para um alvo em um período.
        
        Args:
            target_name: Nome do alvo (asteroide/cometa)
            date_start: Data inicial
            date_end: Data final
            max_magnitude: Magnitude máxima das estrelas a considerar
            max_separation_arcsec: Separação máxima para considerar ocultação
            search_radius_deg: Raio de busca em graus ao redor do caminho
        
        Returns:
            Lista de dicionários com eventos de ocultação ranqueados
        """
        logger.info(
            f"Buscando ocultações para {target_name} de {date_start} a {date_end}"
        )

        # Gera efemérides ao longo do período
        start_dt = datetime.combine(date_start, datetime.min.time())
        end_dt = datetime.combine(date_end, datetime.max.time())

        try:
            ephemerides = self.ephemeris_calc.generate_ephemeris_range(
                target_name, start_dt, end_dt, step_minutes=30
            )
        except Exception as e:
            logger.error(f"Erro ao gerar efemérides: {e}")
            return []

        if not ephemerides:
            return []

        # Para cada ponto da efeméride, busca estrelas próximas
        events = []
        checked_stars = set()

        for eph in ephemerides:
            target_coord = SkyCoord(ra=eph.ra * u.deg, dec=eph.dec * u.deg)

            # Busca estrelas no catálogo Gaia
            stars = self._query_gaia_stars(
                target_coord,
                radius_deg=search_radius_deg,
                max_magnitude=max_magnitude,
            )

            for star in stars:
                star_id = star.get("source_id")
                if star_id in checked_stars:
                    continue
                checked_stars.add(star_id)

                star_coord = SkyCoord(
                    ra=star["ra"] * u.deg,
                    dec=star["dec"] * u.deg,
                )

                # Calcula separação
                separation = target_coord.separation(star_coord).arcsec

                if separation <= max_separation_arcsec:
                    # Potencial evento de ocultação
                    event = self._create_occultation_event(
                        star=star,
                        star_coord=star_coord,
                        target_name=target_name,
                        event_time=eph.epoch,
                        separation_arcsec=separation,
                        target_mag=eph.magnitude,
                    )

                    if event:
                        events.append(event.to_dict())

        # Ordena por prioridade
        events.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        logger.info(f"Encontrados {len(events)} eventos de ocultação")
        return events

    def _query_gaia_stars(
        self,
        center_coord: SkyCoord,
        radius_deg: float,
        max_magnitude: float,
    ) -> List[Dict[str, Any]]:
        """
        Consulta o catálogo Gaia DR3 para estrelas em uma região.
        
        Args:
            center_coord: Coordenadas do centro da busca
            radius_deg: Raio da busca em graus
            max_magnitude: Limite de magnitude
        
        Returns:
            Lista de dicionários com dados das estrelas
        """
        try:
            # Query no Gaia
            query = f"""
                SELECT TOP 1000
                    source_id,
                    ra,
                    dec,
                    phot_g_mean_mag as g_mag,
                    phot_bp_mean_mag as bp_mag,
                    phot_rp_mean_mag as rp_mag
                FROM gaiadr3.gaia_source
                WHERE CONTAINS(
                    POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {center_coord.ra.deg}, {center_coord.dec.deg}, {radius_deg})
                ) = 1
                AND phot_g_mean_mag <= {max_magnitude}
                AND phot_g_mean_mag IS NOT NULL
            """

            result = Gaia.query_job(query)
            table = result.to_table()

            stars = []
            for row in table:
                stars.append(
                    {
                        "source_id": str(row["source_id"]),
                        "ra": float(row["ra"]),
                        "dec": float(row["dec"]),
                        "g_mag": float(row["g_mag"]) if row["g_mag"] else None,
                        "bp_mag": float(row["bp_mag"]) if row["bp_mag"] else None,
                        "rp_mag": float(row["rp_mag"]) if row["rp_mag"] else None,
                    }
                )

            return stars

        except Exception as e:
            logger.warning(f"Erro na consulta Gaia: {e}")
            return []

    def _create_occultation_event(
        self,
        star: Dict[str, Any],
        star_coord: SkyCoord,
        target_name: str,
        event_time: Time,
        separation_arcsec: float,
        target_mag: Optional[float] = None,
    ) -> Optional[OccultationEvent]:
        """
        Cria um evento de ocultação com cálculo de prioridade.
        
        Args:
            star: Dados da estrela
            star_coord: Coordenadas da estrela
            target_name: Nome do alvo
            event_time: Tempo do evento
            separation_arcsec: Separação angular
            target_mag: Magnitude do alvo
        
        Returns:
            OccultationEvent ou None se falhar
        """
        try:
            # Verifica se a estrela tem exoplanetas
            has_exoplanet = False
            planet_names = []

            # Busca exoplanetas próximos às coordenadas da estrela
            planets = self.exoplanet_catalog.find_nearby_planets(
                ra=star["ra"],
                dec=star["dec"],
                radius_arcsec=5.0,  # 5 arcsec de raio
            )

            if planets:
                has_exoplanet = True
                planet_names = [p.get("pl_name", "") for p in planets]

            # Calcula score de prioridade
            priority_score = self._calculate_priority_score(
                star_mag=star.get("g_mag"),
                has_exoplanet=has_exoplanet,
                separation_arcsec=separation_arcsec,
                num_planets=len(planet_names),
            )

            event = OccultationEvent(
                star_name=f"Gaia DR3 {star['source_id']}",
                star_coord=star_coord,
                event_time=event_time,
                separation_arcsec=separation_arcsec,
                target_name=target_name,
                target_mag=target_mag,
                star_mag=star.get("g_mag"),
                has_exoplanet=has_exoplanet,
                planet_names=planet_names,
                priority_score=priority_score,
                gaia_source_id=star["source_id"],
            )

            return event

        except Exception as e:
            logger.error(f"Erro ao criar evento de ocultação: {e}")
            return None

    def _calculate_priority_score(
        self,
        star_mag: Optional[float],
        has_exoplanet: bool,
        separation_arcsec: float,
        num_planets: int,
    ) -> float:
        """
        Calcula score de prioridade para um evento de ocultação.
        
        Critérios:
        - Estrelas com exoplanetas: +50 pontos base
        - Planetas na zona habitável: +20 pontos adicionais
        - Magnitude mais brilhante: +10 pontos
        - Separação menor: +20 pontos
        
        Args:
            star_mag: Magnitude G da estrela
            has_exoplanet: True se tem exoplaneta confirmado
            separation_arcsec: Separação angular em arcsec
            num_planets: Número de planetas confirmados
        
        Returns:
            Score de prioridade (0-100)
        """
        score = 0.0

        # Base por ter exoplaneta
        if has_exoplanet:
            score += 50.0
            # Bônus por múltiplos planetas
            score += min(num_planets * 5, 20)

        # Magnitude (estrelas mais brilhantes são mais fáceis de observar)
        if star_mag is not None:
            mag_score = max(0, (18 - star_mag) / 1.8)  # 0-10 pontos
            score += mag_score

        # Separação (menor é melhor)
        sep_score = max(0, (1.0 - separation_arcsec) * 20)
        score += sep_score

        return min(score, 100.0)


def eph_epoch_to_datetime(epoch: Time) -> datetime:
    """Converte astropy Time para datetime Python."""
    return epoch.to_datetime()


# Exportações públicas
__all__ = [
    "EphemerisCalculator",
    "OccultationPrioritizer",
    "EphemerisData",
    "OccultationEvent",
    "eph_epoch_to_datetime",
]
