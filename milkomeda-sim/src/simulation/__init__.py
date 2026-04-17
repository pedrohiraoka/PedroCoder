"""
src/simulation/__init__.py - Módulo de simulação N-corpos do Milkomeda.
"""

from .particle_generator import ParticleGenerator, generate_disk, generate_halo, generate_bulge
from .nbody_integrator import NBodyIntegrator, evolve_system

__all__ = [
    "ParticleGenerator",
    "generate_disk",
    "generate_halo",
    "generate_bulge",
    "NBodyIntegrator",
    "evolve_system",
]
