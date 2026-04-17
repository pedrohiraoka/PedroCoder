"""
config.py - Constantes físicas, defaults astronômicos e caminhos para Milkomeda.

Este módulo contém todas as constantes físicas, parâmetros padrão baseados em
literatura astronômica (Gaia DR3), e configurações de caminhos para o simulador.
"""

import os
from pathlib import Path
from astropy import units as u
from astropy.constants import G

# =============================================================================
# CAMINHOS DO PROJETO
# =============================================================================
PROJECT_ROOT = Path(__file__).parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SNAPSHOTS_DIR = OUTPUTS_DIR / "snapshots"
FRAMES_DIR = OUTPUTS_DIR / "frames"

# Garantir que diretórios existam
for directory in [OUTPUTS_DIR, SNAPSHOTS_DIR, FRAMES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CONSTANTES FÍSICAS (via astropy.constants)
# =============================================================================
G_CONST = G  # Constante gravitacional
C_LIGHT = 299792.458 * u.km / u.s  # Velocidade da luz

# =============================================================================
# PARÂMETROS PADRÃO DA VIA LÁCTEA (MW)
# Baseados em modelos recentes (McMillan 2017, Gravity Collaboration 2019)
# =============================================================================
MW_DEFAULTS = {
    "mass_disk": 6.0e10 * u.Msun,      # Massa do disco estelar
    "mass_bulge": 1.0e10 * u.Msun,     # Massa do bulbo
    "mass_halo": 1.0e12 * u.Msun,      # Massa do halo de matéria escura
    "scale_length_disk": 3.0 * u.kpc,  # Comprimento de escala do disco
    "scale_height_disk": 0.3 * u.kpc,  # Altura de escala do disco
    "scale_radius_halo": 20.0 * u.kpc, # Raio de escala do halo (NFW)
    "n_particles_disk": 5000,          # Número de partículas no disco
    "n_particles_halo": 3000,          # Número de partículas no halo
    "n_particles_bulge": 2000,         # Número de partículas no bulbo
}

# =============================================================================
# PARÂMETROS PADRÃO DE ANDRÔMEDA (M31)
# Baseados em modelos de Chemin et al. (2009), Geehan et al. (2006)
# =============================================================================
M31_DEFAULTS = {
    "mass_disk": 8.0e10 * u.Msun,
    "mass_bulge": 3.0e10 * u.Msun,
    "mass_halo": 1.5e12 * u.Msun,
    "scale_length_disk": 5.0 * u.kpc,
    "scale_height_disk": 0.4 * u.kpc,
    "scale_radius_halo": 25.0 * u.kpc,
    "n_particles_disk": 6000,
    "n_particles_halo": 4000,
    "n_particles_bulge": 3000,
}

# =============================================================================
# PARÂMETROS ORBITAIS INICIAIS (Gaia DR3 + HST)
# Distância ~765 kpc, velocidade radial ~110 km/s (aproximação)
# =============================================================================
ORBIT_DEFAULTS = {
    "initial_distance": 765 * u.kpc,
    "radial_velocity": -110 * u.km / u.s,  # Negativo = aproximação
    "tangential_velocity": 17 * u.km / u.s,
    "simulation_duration": 10.0 * u.Gyr,
    "n_snapshots": 50,
}

# =============================================================================
# PARÂMETROS DE RENDERIZAÇÃO
# =============================================================================
RENDER_DEFAULTS = {
    "fps": 30,
    "resolution": (1280, 720),
    "dpi": 100,
    "colormap_stars": "inferno",
    "colormap_gas": "viridis",
    "video_codec": "h264",
    "video_bitrate": "2M",
}

# =============================================================================
# CONFIGURAÇÕES DE INTEGRAÇÃO NUMÉRICA
# =============================================================================
INTEGRATION_DEFAULTS = {
    "method": "DOPRI854",  # Runge-Kutta de alta ordem (gala)
    "dt": 10.0 * u.Myr,    # Passo de tempo inicial
    "rtol": 1e-9,          # Tolerância relativa
    "atol": 1e-9,          # Tolerância absoluta
}

# =============================================================================
# METADADOS DA SIMULAÇÃO
# =============================================================================
SIMULATION_METADATA = {
    "name": "Milkomeda",
    "version": "1.0.0",
    "description": "Simulador de Fusão Via Láctea & Andrômeda",
    "author": "Astro Physics Team",
    "license": "MIT",
}

# =============================================================================
# MAPEAMENTO DE UNIDADES PARA EXPORTAÇÃO
# =============================================================================
UNIT_CONVERSIONS = {
    "length": u.kpc,
    "velocity": u.km / u.s,
    "mass": u.Msun,
    "time": u.Gyr,
    "angle": u.deg,
}


def get_default_config() -> dict:
    """
    Retorna um dicionário com toda a configuração padrão do simulador.

    Returns:
        dict: Configuração completa com todos os parâmetros padrão.
    """
    return {
        "mw": MW_DEFAULTS.copy(),
        "m31": M31_DEFAULTS.copy(),
        "orbit": ORBIT_DEFAULTS.copy(),
        "render": RENDER_DEFAULTS.copy(),
        "integration": INTEGRATION_DEFAULTS.copy(),
        "metadata": SIMULATION_METADATA.copy(),
        "paths": {
            "outputs": str(OUTPUTS_DIR),
            "snapshots": str(SNAPSHOTS_DIR),
            "frames": str(FRAMES_DIR),
        },
    }
