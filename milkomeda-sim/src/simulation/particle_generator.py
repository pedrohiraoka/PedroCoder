"""
particle_generator.py - Geração de partículas para simulações de galáxias.

Este módulo gera distribuições de partículas realistas para discos, halos
e bulbos galácticos usando perfis de densidade astronômicos.
"""

from typing import Dict, Tuple, Optional
import numpy as np
from astropy import units as u
from src.utils.logger import get_logger
from src.utils.unit_handler import safe_quantity

logger = get_logger(__name__)


def generate_disk(
    n_particles: int,
    mass_total: u.Quantity,
    scale_length: u.Quantity,
    scale_height: u.Quantity,
    seed: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """
    Gera partículas para um disco galáctico exponencial.

    Usa perfil de densidade Σ(r) ∝ exp(-r/Rd) para o plano e
    ρ(z) ∝ sech²(z/2hz) para a altura vertical.

    Args:
        n_particles: Número de partículas a gerar.
        mass_total: Massa total do disco.
        scale_length: Comprimento de escala do disco (Rd).
        scale_height: Altura de escala do disco (hz).
        seed: Seed para reproducibilidade.

    Returns:
        dict: Dicionário com arrays de posição e velocidade.
            - 'position': Array (N, 3) de posições (kpc)
            - 'velocity': Array (N, 3) de velocidades (km/s)
            - 'mass': Array (N,) de massas individuais (Msun)
    """
    if seed is not None:
        np.random.seed(seed)

    # Converter unidades
    M_total = safe_quantity(mass_total, u.Msun).value
    Rd = safe_quantity(scale_length, u.kpc).value
    hz = safe_quantity(scale_height, u.kpc).value

    # Massa por partícula
    m_particle = M_total / n_particles

    # Gerar raios com distribuição exponencial
    # P(r) dr ∝ r * exp(-r/Rd) dr
    u1 = np.random.uniform(0, 1, n_particles)
    u2 = np.random.uniform(0, 1, n_particles)

    # Método de inversão para disco exponencial
    # Usar aproximação: r = -Rd * ln(u1 * u2)
    r = -Rd * np.log(u1 * u2 + 1e-10)
    r = np.clip(r, 0.1, 10 * Rd)  # Limitar raio

    # Ângulos azimutais
    phi = np.random.uniform(0, 2 * np.pi, n_particles)

    # Alturas z com distribuição sech²
    # Usar aproximação gaussiana para simplicidade
    z = np.random.normal(0, hz, n_particles)

    # Converter para coordenadas cartesianas
    x = r * np.cos(phi)
    y = r * np.sin(phi)

    positions = np.column_stack([x, y, z])

    # Velocidades circulares no disco
    # v_circ = sqrt(G * M(<r) / r)
    # Para disco exponencial: v_circ ≈ constante em r >> Rd
    G_val = 4.302e-6  # kpc * (km/s)^2 / Msun

    # Velocidade circular aproximada (curva de rotação plana)
    v_circ = np.sqrt(G_val * M_total / (Rd + r))

    # Componentes de velocidade (movimento circular no plano)
    vx = -v_circ * np.sin(phi)
    vy = v_circ * np.cos(phi)

    # Dispersão de velocidade (dispersão térmica)
    sigma_r = 0.1 * v_circ  # Dispersão radial
    sigma_z = 0.05 * v_circ  # Dispersão vertical

    vx += np.random.normal(0, sigma_r, n_particles)
    vy += np.random.normal(0, sigma_r, n_particles)
    vz = np.random.normal(0, sigma_z, n_particles)

    velocities = np.column_stack([vx, vy, vz])

    # Massas
    masses = np.full(n_particles, m_particle)

    logger.info(
        f"Disco gerado: {n_particles} partículas, M={M_total:.2e} Msun, "
        f"Rd={Rd:.2f} kpc"
    )

    return {
        "position": positions,
        "velocity": velocities,
        "mass": masses,
    }


def generate_halo(
    n_particles: int,
    mass_total: u.Quantity,
    scale_radius: u.Quantity,
    r_min: float = 0.5,
    r_max: float = 100.0,
    seed: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """
    Gera partículas para um halo de matéria escura NFW.

    Usa perfil de densidade ρ(r) ∝ 1/(r/rs * (1 + r/rs)²).

    Args:
        n_particles: Número de partículas.
        mass_total: Massa total do halo.
        scale_radius: Raio de escala do halo (rs).
        r_min: Raio mínimo em unidades de rs.
        r_max: Raio máximo em unidades de rs.
        seed: Seed para reproducibilidade.

    Returns:
        dict: Dicionário com posições, velocidades e massas.
    """
    if seed is not None:
        np.random.seed(seed)

    # Converter unidades
    M_total = safe_quantity(mass_total, u.Msun).value
    rs = safe_quantity(scale_radius, u.kpc).value

    # Massa por partícula
    m_particle = M_total / n_particles

    # Gerar raios com distribuição NFW
    # P(r) dr ∝ r² / (r * (1+r)²) dr = r / (1+r)² dr
    u = np.random.uniform(0, 1, n_particles)

    # Amostrar raio usando método de inversão aproximado
    # Para NFW: r/rs ~ u^(-1/3) para r pequeno, ~u^(-1) para r grande
    x = np.random.power(0.5, n_particles)  # Distribuição aproximada
    x = x * (r_max - r_min) + r_min
    r = rs * x / (1 - x + 1e-10)
    r = np.clip(r, rs * r_min, rs * r_max)

    # Direções aleatórias isotrópicas
    cos_theta = np.random.uniform(-1, 1, n_particles)
    sin_theta = np.sqrt(1 - cos_theta**2)
    phi = np.random.uniform(0, 2 * np.pi, n_particles)

    # Coordenadas cartesianas
    x_pos = r * sin_theta * np.cos(phi)
    y_pos = r * sin_theta * np.sin(phi)
    z_pos = r * cos_theta

    positions = np.column_stack([x_pos, y_pos, z_pos])

    # Velocidades com dispersão isotrópica
    # σ_v ≈ sqrt(G * M / r_virial)
    G_val = 4.302e-6
    r_virial = rs * 10  # Aproximação
    v_dispersion = np.sqrt(G_val * M_total / r_virial)

    vx = np.random.normal(0, v_dispersion, n_particles)
    vy = np.random.normal(0, v_dispersion, n_particles)
    vz = np.random.normal(0, v_dispersion, n_particles)

    velocities = np.column_stack([vx, vy, vz])

    # Massas
    masses = np.full(n_particles, m_particle)

    logger.info(
        f"Halo NFW gerado: {n_particles} partículas, M={M_total:.2e} Msun, "
        f"rs={rs:.2f} kpc"
    )

    return {
        "position": positions,
        "velocity": velocities,
        "mass": masses,
    }


def generate_bulge(
    n_particles: int,
    mass_total: u.Quantity,
    scale_radius: u.Quantity = 1.0 * u.kpc,
    seed: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """
    Gera partículas para um bulbo galáctico (perfil Hernquist).

    Usa perfil de densidade ρ(r) ∝ 1/(r * (1 + r/a)³).

    Args:
        n_particles: Número de partículas.
        mass_total: Massa total do bulbo.
        scale_radius: Raio de escala do bulbo (a).
        seed: Seed para reproducibilidade.

    Returns:
        dict: Dicionário com posições, velocidades e massas.
    """
    if seed is not None:
        np.random.seed(seed)

    # Converter unidades
    M_total = safe_quantity(mass_total, u.Msun).value
    a = safe_quantity(scale_radius, u.kpc).value

    # Massa por partícula
    m_particle = M_total / n_particles

    # Gerar raios com perfil Hernquist
    # P(r) dr ∝ r² / (r * (1+r/a)³) dr
    u = np.random.uniform(0, 1, n_particles)

    # Inversão aproximada para Hernquist
    # r/a = u / (1 - u)
    x = u / (1 - u + 1e-10)
    r = a * np.clip(x, 0.01, 10)

    # Direções isotrópicas
    cos_theta = np.random.uniform(-1, 1, n_particles)
    sin_theta = np.sqrt(1 - cos_theta**2)
    phi = np.random.uniform(0, 2 * np.pi, n_particles)

    # Coordenadas cartesianas
    x_pos = r * sin_theta * np.cos(phi)
    y_pos = r * sin_theta * np.sin(phi)
    z_pos = r * cos_theta

    positions = np.column_stack([x_pos, y_pos, z_pos])

    # Velocidades com dispersão isotrópica
    G_val = 4.302e-6
    v_dispersion = np.sqrt(G_val * M_total / a) * 0.5

    vx = np.random.normal(0, v_dispersion, n_particles)
    vy = np.random.normal(0, v_dispersion, n_particles)
    vz = np.random.normal(0, v_dispersion, n_particles)

    velocities = np.column_stack([vx, vy, vz])

    # Massas
    masses = np.full(n_particles, m_particle)

    logger.info(
        f"Bulbo Hernquist gerado: {n_particles} partículas, "
        f"M={M_total:.2e} Msun, a={a:.2f} kpc"
    )

    return {
        "position": positions,
        "velocity": velocities,
        "mass": masses,
    }


class ParticleGenerator:
    """
    Gerador completo de sistemas de partículas para galáxias.

    Combina disco, halo e bulbo em uma única estrutura de partículas.

    Attributes:
        seed: Seed para randomização.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Inicializa o gerador de partículas.

        Args:
            seed: Seed opcional para reproducibilidade.
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate_galaxy(
        self,
        mass_disk: u.Quantity,
        mass_bulge: u.Quantity,
        mass_halo: u.Quantity,
        scale_length_disk: u.Quantity,
        scale_height_disk: u.Quantity,
        scale_radius_halo: u.Quantity,
        n_particles_disk: int = 5000,
        n_particles_halo: int = 3000,
        n_particles_bulge: int = 2000,
        position_offset: Optional[np.ndarray] = None,
        velocity_offset: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Gera uma galáxia completa com múltiplos componentes.

        Args:
            mass_disk: Massa do disco.
            mass_bulge: Massa do bulbo.
            mass_halo: Massa do halo.
            scale_length_disk: Comprimento de escala do disco.
            scale_height_disk: Altura de escala do disco.
            scale_radius_halo: Raio de escala do halo.
            n_particles_disk: Número de partículas no disco.
            n_particles_halo: Número de partículas no halo.
            n_particles_bulge: Número de partículas no bulbo.
            position_offset: Offset de posição para toda a galáxia.
            velocity_offset: Offset de velocidade para toda a galáxia.

        Returns:
            dict: Sistema completo de partículas.
        """
        logger.info("Gerando galáxia completa...")

        # Gerar componentes
        disk = generate_disk(
            n_particles=n_particles_disk,
            mass_total=mass_disk,
            scale_length=scale_length_disk,
            scale_height=scale_height_disk,
            seed=self.seed,
        )

        halo = generate_halo(
            n_particles=n_particles_halo,
            mass_total=mass_halo,
            scale_radius=scale_radius_halo,
            seed=self.seed,
        )

        bulge = generate_bulge(
            n_particles=n_particles_bulge,
            mass_total=mass_bulge,
            scale_radius=1.0 * u.kpc,
            seed=self.seed,
        )

        # Combinar partículas
        total_particles = n_particles_disk + n_particles_halo + n_particles_bulge

        positions = np.vstack([disk["position"], halo["position"], bulge["position"]])
        velocities = np.vstack([disk["velocity"], halo["velocity"], bulge["velocity"]])
        masses = np.concatenate([disk["mass"], halo["mass"], bulge["mass"]])

        # Aplicar offsets
        if position_offset is not None:
            positions += position_offset
        if velocity_offset is not None:
            velocities += velocity_offset

        # Tipos de partícula (0=disco, 1=halo, 2=bulbo)
        particle_types = np.concatenate(
            [
                np.zeros(n_particles_disk),
                np.ones(n_particles_halo),
                np.full(n_particles_bulge, 2),
            ]
        )

        galaxy = {
            "position": positions,
            "velocity": velocities,
            "mass": masses,
            "type": particle_types,
            "n_total": total_particles,
            "n_disk": n_particles_disk,
            "n_halo": n_particles_halo,
            "n_bulge": n_particles_bulge,
        }

        logger.info(
            f"Galáxia gerada: {total_particles} partículas totais "
            f"(disco={n_particles_disk}, halo={n_particles_halo}, bulbo={n_particles_bulge})"
        )

        return galaxy

    def generate_binary_system(
        self,
        mw_params: Dict,
        m31_params: Dict,
        separation: u.Quantity,
        relative_velocity: u.Quantity,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        Gera um sistema binário de duas galáxias.

        Args:
            mw_params: Parâmetros da Via Láctea.
            m31_params: Parâmetros de Andrômeda.
            separation: Separação inicial entre galáxias.
            relative_velocity: Velocidade relativa inicial.

        Returns:
            tuple: (galaxia_MW, galaxia_M31)
        """
        sep = safe_quantity(separation, u.kpc).value
        vel = safe_quantity(relative_velocity, u.km / u.s).value

        # Via Láctea na origem
        mw = self.generate_galaxy(
            mass_disk=mw_params.get("mass_disk", 6.0e10 * u.Msun),
            mass_bulge=mw_params.get("mass_bulge", 1.0e10 * u.Msun),
            mass_halo=mw_params.get("mass_halo", 1.0e12 * u.Msun),
            scale_length_disk=mw_params.get("scale_length_disk", 3.0 * u.kpc),
            scale_height_disk=mw_params.get("scale_height_disk", 0.3 * u.kpc),
            scale_radius_halo=mw_params.get("scale_radius_halo", 20.0 * u.kpc),
            n_particles_disk=mw_params.get("n_particles_disk", 5000),
            n_particles_halo=mw_params.get("n_particles_halo", 3000),
            n_particles_bulge=mw_params.get("n_particles_bulge", 2000),
        )

        # Andrômeda deslocada
        m31 = self.generate_galaxy(
            mass_disk=m31_params.get("mass_disk", 8.0e10 * u.Msun),
            mass_bulge=m31_params.get("mass_bulge", 3.0e10 * u.Msun),
            mass_halo=m31_params.get("mass_halo", 1.5e12 * u.Msun),
            scale_length_disk=m31_params.get("scale_length_disk", 5.0 * u.kpc),
            scale_height_disk=m31_params.get("scale_height_disk", 0.4 * u.kpc),
            scale_radius_halo=m31_params.get("scale_radius_halo", 25.0 * u.kpc),
            n_particles_disk=m31_params.get("n_particles_disk", 6000),
            n_particles_halo=m31_params.get("n_particles_halo", 4000),
            n_particles_bulge=m31_params.get("n_particles_bulge", 3000),
            position_offset=np.array([sep, 0, 0]),
            velocity_offset=np.array([vel, 0, 0]),
        )

        logger.info(f"Sistema binário gerado: separação={sep} kpc, v_rel={vel} km/s")

        return mw, m31
