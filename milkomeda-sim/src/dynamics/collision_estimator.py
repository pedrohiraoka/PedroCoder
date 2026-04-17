"""
collision_estimator.py - Estimativa de tempo de colisão e parâmetros de encontro.

Este módulo calcula o tempo estimado até a colisão entre Via Láctea e Andrômeda,
além de determinar parâmetros como periapsis, velocidade de impacto e número
de encontros previstos.
"""

from typing import Dict, Tuple, Optional
import numpy as np
from astropy import units as u
from src.utils.logger import get_logger
from src.utils.unit_handler import safe_quantity, format_quantity

logger = get_logger(__name__)


class CollisionEstimator:
    """
    Estimador de parâmetros de colisão para sistemas de galáxias binárias.

    Calcula tempo de colisão, distância de periapsis, e outras métricas
    relevantes para a fusão MW-M31.

    Attributes:
        collision_threshold: Distância mínima para considerar "colisão" (kpc).
        merger_threshold: Distância para considerar "fusão completa" (kpc).
    """

    def __init__(
        self,
        collision_threshold: float = 50.0,  # kpc
        merger_threshold: float = 10.0,  # kpc
    ):
        """
        Inicializa o estimador de colisão.

        Args:
            collision_threshold: Distância para definir primeiro encontro (kpc).
            merger_threshold: Distância para definir fusão completa (kpc).
        """
        self.collision_threshold = collision_threshold
        self.merger_threshold = merger_threshold

        logger.info(
            f"CollisionEstimator inicializado: collision={collision_threshold} kpc, "
            f"merger={merger_threshold} kpc"
        )

    def estimate_collision_time(
        self,
        initial_distance: u.Quantity,
        radial_velocity: u.Quantity,
        total_mass: u.Quantity,
        tangential_velocity: Optional[u.Quantity] = None,
    ) -> Dict[str, float]:
        """
        Estima o tempo até a colisão usando aproximação Kepleriana.

        Args:
            initial_distance: Distância inicial entre galáxias.
            radial_velocity: Velocidade radial atual.
            total_mass: Massa total do sistema.
            tangential_velocity: Velocidade tangencial (opcional).

        Returns:
            dict: Dicionário com estimativas de tempo e parâmetros de colisão.
                - 'collision_time_gyr': Tempo até primeira colisão (Gyr)
                - 'merger_time_gyr': Tempo até fusão completa (Gyr)
                - 'periapsis_distance_kpc': Distância de periapsis (kpc)
                - 'impact_velocity_km_s': Velocidade de impacto (km/s)
                - 'eccentricity': Excentricidade orbital
                - 'semi_major_axis_kpc': Semi-eixo maior (kpc)
        """
        # Converter unidades
        r0 = safe_quantity(initial_distance, u.kpc).value
        vr0 = safe_quantity(radial_velocity, u.km / u.s).value
        M = safe_quantity(total_mass, u.Msun).value

        if tangential_velocity is not None:
            vt0 = safe_quantity(tangential_velocity, u.km / u.s).value
        else:
            vt0 = 0.0

        # Constante gravitacional em unidades apropriadas
        G_val = 4.302e-6  # kpc * (km/s)^2 / Msun

        # Energia específica (por unidade de massa reduzida)
        v_squared = vr0**2 + vt0**2
        energy = 0.5 * v_squared - G_val * M / r0

        # Momento angular específico
        L = r0 * vt0

        # Parâmetros orbitais
        if energy < 0:
            # Órbita elíptica
            semi_major_axis = -G_val * M / (2 * energy)
            eccentricity = np.sqrt(1 + 2 * energy * L**2 / (G_val * M) ** 2)
            period = 2 * np.pi * np.sqrt(semi_major_axis**3 / (G_val * M))
        else:
            # Órbita parabólica ou hiperbólica (não há colisão garantida)
            semi_major_axis = np.inf
            eccentricity = np.sqrt(1 + 2 * energy * L**2 / (G_val * M) ** 2)
            period = np.inf

        # Periapsis (distância de maior aproximação)
        if eccentricity < 1:
            periapsis = semi_major_axis * (1 - eccentricity)
        else:
            periapsis = L**2 / (G_val * M * (1 + eccentricity))

        # Estimar tempo até colisão
        # Para órbita radial (vt0 ≈ 0), usar fórmula de queda livre
        if vt0 < 1:  # Quase radial
            # Tempo de queda livre aproximado
            collision_time = np.pi / 2 * np.sqrt(r0**3 / (2 * G_val * M))
            collision_time = collision_time / 1000  # Converter para Gyr
        else:
            # Usar fração do período orbital
            # Aproximação: tempo até periapsis é fração do período
            if energy < 0 and period < np.inf:
                # Fração baseada na anomalia excêntrica
                # Simplificação: assumir ~1/4 do período para colisão
                collision_time = period * 0.25 / 1000  # Gyr
            else:
                # Estimativa linear (fallback)
                collision_time = r0 / abs(vr0) if vr0 < 0 else np.inf
                collision_time = collision_time * 0.9778 / 1000  # Converter para Gyr

        # Tempo até fusão completa (após múltiplos encontros)
        # Empiricamente ~2-3 vezes o tempo da primeira colisão
        merger_time = collision_time * 2.5 if collision_time < np.inf else np.inf

        # Velocidade de impacto (na distância de colisão)
        # Conservação de energia: v_impact^2 = v_0^2 + 2GM(1/r_coll - 1/r_0)
        r_coll = self.collision_threshold
        impact_velocity = np.sqrt(
            v_squared + 2 * G_val * M * (1 / r_coll - 1 / r0)
        )

        result = {
            "collision_time_gyr": collision_time,
            "merger_time_gyr": merger_time,
            "periapsis_distance_kpc": periapsis,
            "impact_velocity_km_s": impact_velocity,
            "eccentricity": eccentricity,
            "semi_major_axis_kpc": semi_major_axis if np.isfinite(semi_major_axis) else np.nan,
            "orbital_period_gyr": period / 1000 if np.isfinite(period) else np.nan,
            "is_bound": energy < 0,
        }

        logger.info(
            f"Colisão estimada em {collision_time:.2f} Gyr, "
            f"periapsis: {periapsis:.2f} kpc, "
            f"excentricidade: {eccentricity:.3f}"
        )

        return result

    def find_closest_approach_from_orbit(
        self,
        orbit_result: Dict[str, np.ndarray],
    ) -> Dict[str, float]:
        """
        Encontra o ponto de maior aproximação a partir de uma órbita integrada.

        Args:
            orbit_result: Resultado da integração orbital (de OrbitSolver).

        Returns:
            dict: Informações sobre o encontro mais próximo.
                - 'time_gyr': Tempo do periapsis (Gyr)
                - 'distance_kpc': Distância do periapsis (kpc)
                - 'velocity_km_s': Velocidade no periapsis (km/s)
                - 'index': Índice do array onde ocorre
        """
        distances = orbit_result.get("distance", [])
        times = orbit_result.get("time", [])
        velocities = orbit_result.get("velocity", [])

        if len(distances) == 0:
            logger.warning("Orbit result está vazio")
            return {
                "time_gyr": np.nan,
                "distance_kpc": np.nan,
                "velocity_km_s": np.nan,
                "index": -1,
            }

        # Encontrar mínimo
        min_idx = np.argmin(distances)

        # Calcular magnitude da velocidade no periapsis
        if len(velocities.shape) > 1:
            velocity_magnitude = np.sqrt(np.sum(velocities**2, axis=0))[min_idx]
        else:
            velocity_magnitude = np.abs(velocities[min_idx])

        result = {
            "time_gyr": times[min_idx],
            "distance_kpc": distances[min_idx],
            "velocity_km_s": velocity_magnitude,
            "index": int(min_idx),
        }

        logger.info(
            f"Periapsis encontrado: t={result['time_gyr']:.3f} Gyr, "
            f"d={result['distance_kpc']:.2f} kpc"
        )

        return result

    def count_encounters(
        self,
        orbit_result: Dict[str, np.ndarray],
        threshold: Optional[float] = None,
    ) -> int:
        """
        Conta o número de encontros próximos na órbita.

        Args:
            orbit_result: Resultado da integração orbital.
            threshold: Distância limite para contar como encontro (kpc).

        Returns:
            int: Número de encontros detectados.
        """
        if threshold is None:
            threshold = self.collision_threshold

        distances = orbit_result.get("distance", [])

        if len(distances) == 0:
            return 0

        # Contar cruzamentos do threshold (encontros)
        below_threshold = distances < threshold

        # Contar transições de False->True (início de encontro)
        encounters = 0
        for i in range(1, len(below_threshold)):
            if below_threshold[i] and not below_threshold[i - 1]:
                encounters += 1

        logger.info(f"Detectados {encounters} encontros dentro de {threshold} kpc")
        return encounters

    def generate_collision_report(
        self,
        orbit_result: Dict[str, np.ndarray],
        analytic_estimate: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Gera um relatório textual sobre a colisão prevista.

        Args:
            orbit_result: Resultado da integração orbital.
            analytic_estimate: Estimativa analítica opcional.

        Returns:
            str: Relatório formatado.
        """
        # Dados da órbita integrada
        closest = self.find_closest_approach_from_orbit(orbit_result)
        encounters = self.count_encounters(orbit_result)

        # Construir relatório
        report_lines = [
            "=" * 60,
            "RELATÓRIO DE COLISÃO: VIA LÁCTEA & ANDRÔMEDA",
            "=" * 60,
            "",
            "PARÂMETROS DO ENCONTRO:",
            f"  • Tempo até primeira colisão: {closest['time_gyr']:.2f} Gyr",
            f"  • Distância de periapsis: {closest['distance_kpc']:.2f} kpc",
            f"  • Velocidade no periapsis: {closest['velocity_km_s']:.1f} km/s",
            f"  • Número de encontros previstos: {encounters}",
            "",
        ]

        if analytic_estimate:
            report_lines.extend(
                [
                    "ESTIMATIVA ANALÍTICA:",
                    f"  • Excentricidade orbital: {analytic_estimate.get('eccentricity', np.nan):.3f}",
                    f"  • Semi-eixo maior: {analytic_estimate.get('semi_major_axis_kpc', np.nan):.1f} kpc",
                    f"  • Período orbital: {analytic_estimate.get('orbital_period_gyr', np.nan):.2f} Gyr",
                    f"  • Sistema ligado: {'Sim' if analytic_estimate.get('is_bound', False) else 'Não'}",
                    "",
                ]
            )

        report_lines.extend(
            [
                "CRONOLOGIA PREVISTA:",
                f"  1. Primeira aproximação máxima: ~{closest['time_gyr']:.1f} Gyr",
                f"  2. Fusão completa (Milkomeda): ~{closest['time_gyr'] * 2.5:.1f} Gyr",
                "  3. Relaxamento para galáxia elíptica: ~10 Gyr",
                "",
                "=" * 60,
            ]
        )

        report = "\n".join(report_lines)
        logger.info("Relatório de colisão gerado")

        return report


def estimate_collision_time(
    initial_distance: u.Quantity = 765 * u.kpc,
    radial_velocity: u.Quantity = -110 * u.km / u.s,
    mw_mass: u.Quantity = 1.0e12 * u.Msun,
    m31_mass: u.Quantity = 1.5e12 * u.Msun,
    tangential_velocity: Optional[u.Quantity] = None,
) -> Dict[str, float]:
    """
    Função utilitária para estimativa rápida de tempo de colisão.

    Args:
        initial_distance: Distância inicial.
        radial_velocity: Velocidade radial.
        mw_mass: Massa da Via Láctea.
        m31_mass: Massa de Andrômeda.
        tangential_velocity: Velocidade tangencial.

    Returns:
        dict: Resultados da estimativa.
    """
    estimator = CollisionEstimator()
    total_mass = safe_quantity(mw_mass, u.Msun) + safe_quantity(m31_mass, u.Msun)

    return estimator.estimate_collision_time(
        initial_distance=initial_distance,
        radial_velocity=radial_velocity,
        total_mass=total_mass,
        tangential_velocity=tangential_velocity,
    )
