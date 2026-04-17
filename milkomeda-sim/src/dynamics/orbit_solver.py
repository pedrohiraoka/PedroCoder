"""
orbit_solver.py - Solução de órbitas usando gala para potenciais gravitacionais.

Este módulo implementa a integração orbital da Via Láctea e Andrômeda
usando potenciais analíticos realistas do pacote gala.
"""

from typing import Dict, Tuple, Optional, List
import numpy as np
from astropy import units as u
from astropy.constants import G
import gala.potential as gp
from gala.dynamics import Orbit
from src.utils.logger import get_logger
from src.utils.unit_handler import safe_quantity

logger = get_logger(__name__)


def create_mw_potential(
    mass_disk: u.Quantity = 6.0e10 * u.Msun,
    mass_bulge: u.Quantity = 1.0e10 * u.Msun,
    mass_halo: u.Quantity = 1.0e12 * u.Msun,
    scale_length_disk: u.Quantity = 3.0 * u.kpc,
    scale_height_disk: u.Quantity = 0.3 * u.kpc,
    scale_radius_halo: u.Quantity = 20.0 * u.kpc,
) -> gp.PotentialBase:
    """
    Cria o potencial gravitacional composto da Via Láctea.

    Usa um modelo com disco Miyamoto-Nagai, bulbo Hernquist e halo NFW.

    Args:
        mass_disk: Massa do disco estelar.
        mass_bulge: Massa do bulbo central.
        mass_halo: Massa do halo de matéria escura.
        scale_length_disk: Comprimento de escala do disco.
        scale_height_disk: Altura de escala do disco.
        scale_radius_halo: Raio de escala do halo NFW.

    Returns:
        PotentialBase: Potencial composto da Via Láctea.
    """
    # Converter unidades - gala usa valores numéricos em unidades internas
    def to_gala_units(q, unit):
        return q.to_value(unit)

    # Disco Miyamoto-Nagai (sem units parameter na versão atual do gala)
    disk = gp.MiyamotoNagaiPotential(
        m=to_gala_units(mass_disk, u.Msun),
        a=to_gala_units(scale_length_disk, u.kpc),
        b=to_gala_units(scale_height_disk, u.kpc),
    )

    # Bulbo Hernquist
    bulge = gp.HernquistPotential(
        m=to_gala_units(mass_bulge, u.Msun),
        c=1.0,  # Raio de escala do bulbo em kpc
    )

    # Halo NFW (Navarro-Frenk-White)
    halo = gp.NFWPotential(
        m=to_gala_units(mass_halo, u.Msun),
        r_s=to_gala_units(scale_radius_halo, u.kpc),
    )

    # Potencial composto
    mw_potential = gp.Potential(disk=disk, bulge=bulge, halo=halo)

    logger.info(
        f"Potencial MW criado: M_disk={mass_disk:.2e}, M_bulge={mass_bulge:.2e}, "
        f"M_halo={mass_halo:.2e}"
    )

    return mw_potential


def create_m31_potential(
    mass_disk: u.Quantity = 8.0e10 * u.Msun,
    mass_bulge: u.Quantity = 3.0e10 * u.Msun,
    mass_halo: u.Quantity = 1.5e12 * u.Msun,
    scale_length_disk: u.Quantity = 5.0 * u.kpc,
    scale_height_disk: u.Quantity = 0.4 * u.kpc,
    scale_radius_halo: u.Quantity = 25.0 * u.kpc,
) -> gp.PotentialBase:
    """
    Cria o potencial gravitacional composto de Andrômeda (M31).

    Args:
        mass_disk: Massa do disco estelar.
        mass_bulge: Massa do bulbo central.
        mass_halo: Massa do halo de matéria escura.
        scale_length_disk: Comprimento de escala do disco.
        scale_height_disk: Altura de escala do disco.
        scale_radius_halo: Raio de escala do halo NFW.

    Returns:
        PotentialBase: Potencial composto de Andrômeda.
    """
    # Converter unidades - gala usa valores numéricos em unidades internas
    def to_gala_units(q, unit):
        return q.to_value(unit)

    # Disco Miyamoto-Nagai
    disk = gp.MiyamotoNagaiPotential(
        m=to_gala_units(mass_disk, u.Msun),
        a=to_gala_units(scale_length_disk, u.kpc),
        b=to_gala_units(scale_height_disk, u.kpc),
    )

    # Bulbo Hernquist (mais massivo que MW)
    bulge = gp.HernquistPotential(
        m=to_gala_units(mass_bulge, u.Msun),
        c=1.5,  # Raio de escala do bulbo em kpc
    )

    # Halo NFW
    halo = gp.NFWPotential(
        m=to_gala_units(mass_halo, u.Msun),
        r_s=to_gala_units(scale_radius_halo, u.kpc),
    )

    # Potencial composto
    m31_potential = gp.Potential(disk=disk, bulge=bulge, halo=halo)

    logger.info(
        f"Potencial M31 criado: M_disk={mass_disk:.2e}, M_bulge={mass_bulge:.2e}, "
        f"M_halo={mass_halo:.2e}"
    )

    return m31_potential


class OrbitSolver:
    """
    Solver para integração orbital de sistemas binários de galáxias.

    Integra as órbitas da Via Láctea e Andrômeda considerando seus
    potenciais gravitacionais combinados.

    Attributes:
        mw_potential: Potencial da Via Láctea.
        m31_potential: Potencial de Andrômeda.
        total_potential: Potencial combinado do sistema.
    """

    def __init__(
        self,
        mw_potential: Optional[gp.PotentialBase] = None,
        m31_potential: Optional[gp.PotentialBase] = None,
        **potential_kwargs,
    ):
        """
        Inicializa o solver orbital.

        Args:
            mw_potential: Potencial da Via Láctea (cria default se None).
            m31_potential: Potencial de Andrômeda (cria default se None).
            **potential_kwargs: Parâmetros para criar potenciais default.
        """
        self.mw_potential = mw_potential or create_mw_potential(**potential_kwargs)
        self.m31_potential = m31_potential or create_m31_potential(**potential_kwargs)

        # Para órbita relativa, usamos o potencial combinado
        # Na aproximação de massa pontual efetiva
        self.total_mass = self._estimate_total_mass()

        logger.info(f"OrbitSolver inicializado. Massa total: {self.total_mass:.2e}")

    def _estimate_total_mass(self) -> u.Quantity:
        """
        Estima a massa total do sistema para o problema de dois corpos.

        Returns:
            Quantity: Massa total estimada.
        """
        # Aproximação: soma das massas dos halos (dominantes)
        mw_halo_mass = 1.0e12 * u.Msun
        m31_halo_mass = 1.5e12 * u.Msun
        return mw_halo_mass + m31_halo_mass

    def solve_orbit(
        self,
        initial_distance: u.Quantity = 765 * u.kpc,
        radial_velocity: u.Quantity = -110 * u.km / u.s,
        tangential_velocity: u.Quantity = 17 * u.km / u.s,
        duration: u.Quantity = 10.0 * u.Gyr,
        n_steps: int = 1000,
        method: str = "DOPRI854",
    ) -> Dict[str, np.ndarray]:
        """
        Integra a órbita relativa entre MW e M31.

        Args:
            initial_distance: Distância inicial entre as galáxias.
            radial_velocity: Velocidade radial (negativa = aproximação).
            tangential_velocity: Velocidade tangencial.
            duration: Duração total da simulação.
            n_steps: Número de passos de integração.
            method: Método de integração (DOPRI854, Leapfrog, etc.).

        Returns:
            dict: Dicionário com arrays de tempo, posição, velocidade e distância.
                - 'time': Array de tempos (Gyr)
                - 'position': Array de posições 3D (kpc)
                - 'velocity': Array de velocidades 3D (km/s)
                - 'distance': Distância entre galáxias (kpc)
                - 'radial_velocity': Velocidade radial (km/s)
        """
        # Converter unidades
        r0 = safe_quantity(initial_distance, u.kpc).to(u.kpc).value
        vr0 = safe_quantity(radial_velocity, u.km / u.s).to(u.km / u.s).value
        vt0 = safe_quantity(tangential_velocity, u.km / u.s).to(u.km / u.s).value
        t_max = safe_quantity(duration, u.Gyr).to(u.Gyr).value

        # Configurar condições iniciais no frame do centro de massa
        # Posição inicial: M31 em (r0, 0, 0) relativo à MW na origem
        # Velocidade: componente radial (-vr) e tangencial (vt)
        pos0 = np.array([r0, 0, 0])  # kpc
        vel0 = np.array([vr0, vt0, 0])  # km/s

        # Criar órbita inicial do gala
        w0 = np.hstack([pos0, vel0])

        # Unidades do gala
        units = gp.UnitSystem(u.kpc, u.Myr, u.Msun, u.radian)

        # Potencial efetivo para problema de dois corpos
        # Usamos um potencial Kepleriano com massa total reduzida
        effective_potential = gp.KeplerPotential(m=self.total_mass.to(u.Msun).value)

        # Integrador
        integrator_class = getattr(gp.integrate, method, gp.integrate.DOPRI854Integrator)
        integrator = integrator_class(effective_potential, units=units)

        # Tempos de integração
        time_array = np.linspace(0, t_max * 1000, n_steps)  # Convert Gyr to Myr

        try:
            # Integrar órbita
            orbit = integrator.run(w0, dt=time_array)

            # Extrair resultados
            positions = orbit.pos.T.value  # kpc
            velocities = orbit.vel.T.value  # kpc/Myr -> converter para km/s
            velocities = velocities * 0.9778  # kpc/Myr -> km/s

            # Calcular distância
            distances = np.sqrt(np.sum(positions**2, axis=0))

            # Calcular velocidade radial
            radial_velocities = np.sum(positions * velocities, axis=0) / (distances + 1e-10)

            result = {
                "time": time_array / 1000.0,  # Converter Myr para Gyr
                "position": positions,
                "velocity": velocities,
                "distance": distances,
                "radial_velocity": radial_velocities,
                "orbit": orbit,
            }

            logger.info(
                f"Órbita integrada: {n_steps} passos, "
                f"distância final: {distances[-1]:.2f} kpc"
            )

            return result

        except Exception as e:
            logger.error(f"Erro na integração orbital: {e}")
            # Fallback: solução analítica aproximada
            return self._analytic_approximation(
                r0, vr0, vt0, t_max, n_steps
            )

    def _analytic_approximation(
        self,
        r0: float,
        vr0: float,
        vt0: float,
        t_max: float,
        n_steps: int,
    ) -> Dict[str, np.ndarray]:
        """
        Fornece uma aproximação analítica caso a integração falhe.

        Usa equações de movimento Kepleriano simplificadas.

        Args:
            r0: Distância inicial (kpc).
            vr0: Velocidade radial inicial (km/s).
            vt0: Velocidade tangencial inicial (km/s).
            t_max: Tempo máximo (Gyr).
            n_steps: Número de passos.

        Returns:
            dict: Resultados aproximados.
        """
        logger.warning("Usando aproximação analítica para órbita")

        # Constantes
        G_val = G.to_value(u.kpc * u.km**2 / u.s**2 / u.Msun)
        M = self.total_mass.to(u.Msun).value

        # Aceleração inicial (aproximação)
        a0 = -G_val * M / (r0**2)

        # Arrays de tempo
        time_array = np.linspace(0, t_max, n_steps)

        # Aproximação de movimento uniformemente acelerado (válido para curto prazo)
        # Para longo prazo, usar equações Keplerianas completas
        distances = r0 + vr0 * time_array * 1000 + 0.5 * a0 * (time_array * 1000) ** 2
        distances = np.maximum(distances, 0.1)  # Evitar distâncias negativas

        # Conservação de momento angular para velocidade tangencial
        L = r0 * vt0
        vt = L / (distances + 1e-10)

        # Velocidade radial aproximada
        vr = vr0 + a0 * time_array * 1000

        # Posições (assumindo movimento no plano xy)
        angles = np.cumsum(vt / (distances + 1e-10)) * 0.001  # Aproximação
        positions = np.zeros((3, n_steps))
        positions[0] = distances * np.cos(angles)
        positions[1] = distances * np.sin(angles)

        velocities = np.zeros((3, n_steps))
        velocities[0] = vr * np.cos(angles) - vt * np.sin(angles)
        velocities[1] = vr * np.sin(angles) + vt * np.cos(angles)

        return {
            "time": time_array,
            "position": positions,
            "velocity": velocities,
            "distance": distances,
            "radial_velocity": vr,
            "orbit": None,
        }

    def get_closest_approach(
        self, orbit_result: Dict[str, np.ndarray]
    ) -> Tuple[float, float]:
        """
        Encontra o ponto de maior aproximação na órbita.

        Args:
            orbit_result: Resultado da integração orbital.

        Returns:
            tuple: (tempo de periapsis em Gyr, distância de periapsis em kpc).
        """
        distances = orbit_result["distance"]
        times = orbit_result["time"]

        min_idx = np.argmin(distances)
        return times[min_idx], distances[min_idx]
