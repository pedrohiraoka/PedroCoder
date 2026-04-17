"""
nbody_integrator.py - Integrador N-corpos simplificado para evolução de galáxias.

Este módulo implementa um integrador leapfrog simplificado para evoluir
sistemas de partículas sob gravidade mútua e potenciais externos.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from astropy import units as u
from pathlib import Path
import json
from src.utils.logger import get_logger
from src.utils.unit_handler import safe_quantity

logger = get_logger(__name__)


class NBodyIntegrator:
    """
    Integrador N-corpos usando método leapfrog.

    Implementa integração symplectic para conservação de energia
    em simulações de longo prazo.

    Attributes:
        G: Constante gravitacional nas unidades apropriadas.
        softening: Parâmetro de suavização para evitar singularidades.
    """

    def __init__(
        self,
        G: float = 4.302e-6,  # kpc * (km/s)^2 / Msun
        softening: float = 0.1,  # kpc
    ):
        """
        Inicializa o integrador N-corpos.

        Args:
            G: Constante gravitacional.
            softening: Parâmetro de suavização (kpc).
        """
        self.G = G
        self.softening = softening

        logger.info(
            f"NBodyIntegrator inicializado: G={G:.2e}, softening={softening} kpc"
        )

    def compute_accelerations(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        external_acceleration: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Computa acelerações gravitacionais entre todas as partículas.

        Usa algoritmo direto O(N²) - adequado para N < 50000.

        Args:
            positions: Array (N, 3) de posições.
            masses: Array (N,) de massas.
            external_acceleration: Aceleração externa opcional (ex: potencial estático).

        Returns:
            np.ndarray: Array (N, 3) de acelerações.
        """
        n_particles = len(positions)
        accelerations = np.zeros_like(positions)

        # Calcular diferenças de posição (matriz N x N x 3)
        # Usando broadcasting para eficiência
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]

        # Distâncias com softening
        r_squared = np.sum(diff**2, axis=2) + self.softening**2
        r = np.sqrt(r_squared)

        # Fator G * m / r³
        # Evitar divisão por zero adicionando epsilon
        r_cubed = r**3 + 1e-10

        # Matriz de fatores
        factors = self.G * masses[np.newaxis, :] / r_cubed

        # Somar contribuições de todas as partículas
        # a_i = sum_j (G * m_j * (r_j - r_i) / |r_j - r_i|³)
        for i in range(n_particles):
            accelerations[i] = -np.sum(factors[:, i][:, np.newaxis] * diff[i, :, :], axis=0)

        # Adicionar aceleração externa se fornecida
        if external_acceleration is not None:
            accelerations += external_acceleration

        return accelerations

    def leapfrog_step(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        dt: float,
        external_acceleration: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executa um passo de integração leapfrog.

        Método symplectic de segunda ordem:
        1. Kick: v(t+dt/2) = v(t) + a(t) * dt/2
        2. Drift: r(t+dt) = r(t) + v(t+dt/2) * dt
        3. Kick: v(t+dt) = v(t+dt/2) + a(t+dt) * dt/2

        Args:
            positions: Posições atuais.
            velocities: Velocidades atuais.
            masses: Massas das partículas.
            dt: Passo de tempo.
            external_acceleration: Aceleração externa.

        Returns:
            tuple: (novas_posicoes, novas_velocidades)
        """
        # Kick inicial (meio passo)
        accels = self.compute_accelerations(positions, masses, external_acceleration)
        velocities_half = velocities + 0.5 * accels * dt

        # Drift (passo completo)
        new_positions = positions + velocities_half * dt

        # Kick final (meio passo)
        new_accels = self.compute_accelerations(new_positions, masses, external_acceleration)
        new_velocities = velocities_half + 0.5 * new_accels * dt

        return new_positions, new_velocities

    def evolve(
        self,
        particles: Dict[str, np.ndarray],
        n_steps: int,
        dt: float,
        snapshot_interval: int = 10,
        output_dir: Optional[Path] = None,
    ) -> List[Dict[str, np.ndarray]]:
        """
        Evolui o sistema de partículas no tempo.

        Args:
            particles: Dicionário com 'position', 'velocity', 'mass'.
            n_steps: Número de passos de integração.
            dt: Passo de tempo (Myr).
            snapshot_interval: Intervalo para salvar snapshots.
            output_dir: Diretório para salvar snapshots.

        Returns:
            list: Lista de snapshots (dicionários de partículas).
        """
        positions = particles["position"].copy()
        velocities = particles["velocity"].copy()
        masses = particles["mass"]

        snapshots = []
        total_mass = np.sum(masses)

        logger.info(
            f"Iniciando evolução: {len(positions)} partículas, "
            f"{n_steps} passos, dt={dt} Myr"
        )

        for step in range(n_steps):
            # Integrar um passo
            positions, velocities = self.leapfrog_step(
                positions, velocities, masses, dt
            )

            # Salvar snapshot se necessário
            if step % snapshot_interval == 0 or step == n_steps - 1:
                snapshot = {
                    "time": step * dt,  # Myr
                    "position": positions.copy(),
                    "velocity": velocities.copy(),
                    "mass": masses.copy(),
                    "type": particles.get("type", np.zeros(len(masses))),
                }
                snapshots.append(snapshot)

                # Salvar em arquivo se diretório fornecido
                if output_dir:
                    self.save_snapshot(snapshot, output_dir, step // snapshot_interval)

                # Log progresso
                if step % (n_steps // 10) == 0:
                    progress = 100 * step / n_steps
                    logger.info(f"Progresso: {progress:.0f}% (t={step*dt:.1f} Myr)")

        logger.info(f"Evolução completa: {len(snapshots)} snapshots salvos")
        return snapshots

    def save_snapshot(
        self,
        snapshot: Dict[str, np.ndarray],
        output_dir: Path,
        index: int,
    ) -> Path:
        """
        Salva um snapshot em formato NumPy (.npz).

        Args:
            snapshot: Dados do snapshot.
            output_dir: Diretório de saída.
            index: Índice do snapshot.

        Returns:
            Path: Caminho do arquivo salvo.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"snapshot_{index:04d}.npz"

        np.savez_compressed(
            filepath,
            time=snapshot["time"],
            position=snapshot["position"],
            velocity=snapshot["velocity"],
            mass=snapshot["mass"],
            type=snapshot.get("type", np.zeros(len(snapshot["mass"]))),
        )

        logger.debug(f"Snapshot salvo: {filepath}")
        return filepath

    def load_snapshot(self, filepath: Path) -> Dict[str, np.ndarray]:
        """
        Carrega um snapshot de arquivo .npz.

        Args:
            filepath: Caminho do arquivo.

        Returns:
            dict: Dados do snapshot.
        """
        data = np.load(filepath)
        return {
            "time": float(data["time"]),
            "position": data["position"],
            "velocity": data["velocity"],
            "mass": data["mass"],
            "type": data.get("type", np.zeros(len(data["mass"]))),
        }

    def combine_systems(
        self,
        system1: Dict[str, np.ndarray],
        system2: Dict[str, np.ndarray],
    ) -> Dict[str, np.ndarray]:
        """
        Combina dois sistemas de partículas em um único.

        Args:
            system1: Primeiro sistema.
            system2: Segundo sistema.

        Returns:
            dict: Sistema combinado.
        """
        combined = {
            "position": np.vstack([system1["position"], system2["position"]]),
            "velocity": np.vstack([system1["velocity"], system2["velocity"]]),
            "mass": np.concatenate([system1["mass"], system2["mass"]]),
            "type": np.concatenate(
                [
                    system1.get("type", np.zeros(len(system1["mass"]))),
                    system2.get("type", np.zeros(len(system2["mass"]))) + 10,
                ]
            ),
        }
        combined["n_total"] = len(combined["mass"])

        logger.info(
            f"Sistemas combinados: {combined['n_total']} partículas totais"
        )

        return combined


def evolve_system(
    mw_particles: Dict[str, np.ndarray],
    m31_particles: Dict[str, np.ndarray],
    orbit_result: Dict[str, np.ndarray],
    n_steps: int = 100,
    dt: float = 100.0,  # Myr
    output_dir: Optional[Path] = None,
) -> List[Dict[str, np.ndarray]]:
    """
    Função utilitária para evoluir o sistema binário MW-M31.

    Args:
        mw_particles: Partículas da Via Láctea.
        m31_particles: Partículas de Andrômeda.
        orbit_result: Resultado da órbita integrada (para movimento do centro de massa).
        n_steps: Número de passos de integração.
        dt: Passo de tempo (Myr).
        output_dir: Diretório para snapshots.

    Returns:
        list: Lista de snapshots da evolução.
    """
    integrator = NBodyIntegrator()

    # Combinar sistemas
    combined = integrator.combine_systems(mw_particles, m31_particles)

    # Evoluir
    snapshots = integrator.evolve(
        particles=combined,
        n_steps=n_steps,
        dt=dt,
        snapshot_interval=max(1, n_steps // 50),  # ~50 snapshots
        output_dir=output_dir,
    )

    return snapshots
