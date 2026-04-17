"""
frame_renderer.py - Renderização de frames para simulações do Milkomeda.

Este módulo gera visualizações 2D e 3D dos snapshots da simulação,
produzindo imagens PNG adequadas para compilação em vídeo.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from astropy import units as u
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Circle
from src.utils.logger import get_logger
from src.utils.unit_handler import safe_quantity

logger = get_logger(__name__)


def render_frame_2d(
    snapshot: Dict[str, np.ndarray],
    output_path: Path,
    time_gyr: float = 0.0,
    distance_kpc: float = 765.0,
    figsize: Tuple[int, int] = (12, 8),
    dpi: int = 100,
    colormap: str = "inferno",
    limit: float = 500.0,
) -> Path:
    """
    Renderiza um frame 2D de densidade estelar.

    Args:
        snapshot: Dados do snapshot com 'position', 'mass', 'type'.
        output_path: Caminho para salvar a imagem.
        time_gyr: Tempo atual da simulação (Gyr).
        distance_kpc: Distância entre galáxias (kpc).
        figsize: Tamanho da figura (polegadas).
        dpi: Resolução da imagem.
        colormap: Colormap do matplotlib.
        limit: Limite do eixo (kpc).

    Returns:
        Path: Caminho da imagem salva.
    """
    positions = snapshot.get("position", np.zeros((0, 3)))
    masses = snapshot.get("mass", np.ones(len(positions)))
    types = snapshot.get("type", np.zeros(len(positions)))

    # Criar figura
    fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)

    # Projeção XY (vista de topo)
    x = positions[:, 0]
    y = positions[:, 1]

    # Separar por tipo (MW vs M31)
    mw_mask = types < 10
    m31_mask = types >= 10

    # Plot MW (azul)
    if np.any(mw_mask):
        ax.scatter(
            x[mw_mask], y[mw_mask],
            s=0.5, c='steelblue', alpha=0.6,
            label='Via Láctea', rasterized=True
        )

    # Plot M31 (vermelho)
    if np.any(m31_mask):
        ax.scatter(
            x[m31_mask], y[m31_mask],
            s=0.5, c='crimson', alpha=0.6,
            label='Andrômeda', rasterized=True
        )

    # Configurar eixos
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect('equal')
    ax.set_xlabel('X (kpc)', fontsize=12)
    ax.set_ylabel('Y (kpc)', fontsize=12)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Título com informações temporais
    ax.set_title(
        f'Milkomeda Simulation | t = {time_gyr:.2f} Gyr | d = {distance_kpc:.0f} kpc',
        fontsize=14, fontweight='bold'
    )

    # Salvar
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='black')
    plt.close(fig)

    logger.debug(f"Frame 2D salvo: {output_path}")
    return output_path


def render_frame_3d(
    snapshot: Dict[str, np.ndarray],
    output_path: Path,
    time_gyr: float = 0.0,
    distance_kpc: float = 765.0,
    figsize: Tuple[int, int] = (10, 8),
    dpi: int = 100,
    elevation: float = 30.0,
    azimuth: float = 45.0,
) -> Path:
    """
    Renderiza um frame 3D mostrando distribuição espacial.

    Args:
        snapshot: Dados do snapshot.
        output_path: Caminho para salvar a imagem.
        time_gyr: Tempo atual (Gyr).
        distance_kpc: Distância entre galáxias (kpc).
        figsize: Tamanho da figura.
        dpi: Resolução.
        elevation: Elevação da câmera (graus).
        azimuth: Azimute da câmera (graus).

    Returns:
        Path: Caminho da imagem salva.
    """
    positions = snapshot.get("position", np.zeros((0, 3)))
    types = snapshot.get("type", np.zeros(len(positions)))

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')

    # Separar componentes
    mw_mask = types < 10
    m31_mask = types >= 10

    # Plot MW
    if np.any(mw_mask):
        ax.scatter(
            positions[mw_mask, 0],
            positions[mw_mask, 1],
            positions[mw_mask, 2],
            s=1, c='steelblue', alpha=0.5,
            label='Via Láctea'
        )

    # Plot M31
    if np.any(m31_mask):
        ax.scatter(
            positions[m31_mask, 0],
            positions[m31_mask, 1],
            positions[m31_mask, 2],
            s=1, c='crimson', alpha=0.5,
            label='Andrômeda'
        )

    # Configurar eixos
    limit = 500
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xlabel('X (kpc)')
    ax.set_ylabel('Y (kpc)')
    ax.set_zlabel('Z (kpc)')
    ax.legend()

    # Ângulos da câmera
    ax.view_init(elev=elevation, azim=azimuth)

    # Título
    ax.set_title(f't = {time_gyr:.2f} Gyr | d = {distance_kpc:.0f} kpc')

    # Salvar
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='black')
    plt.close(fig)

    logger.debug(f"Frame 3D salvo: {output_path}")
    return output_path


def render_density_map(
    snapshot: Dict[str, np.ndarray],
    output_path: Path,
    time_gyr: float = 0.0,
    distance_kpc: float = 765.0,
    figsize: Tuple[int, int] = (10, 8),
    dpi: int = 100,
    colormap: str = "magma",
    n_bins: int = 200,
    limit: float = 400.0,
) -> Path:
    """
    Renderiza um mapa de densidade 2D usando histograma.

    Args:
        snapshot: Dados do snapshot.
        output_path: Caminho para salvar.
        time_gyr: Tempo (Gyr).
        distance_kpc: Distância (kpc).
        figsize: Tamanho da figura.
        dpi: Resolução.
        colormap: Colormap.
        n_bins: Número de bins no histograma.
        limit: Limite do eixo.

    Returns:
        Path: Caminho da imagem.
    """
    positions = snapshot.get("position", np.zeros((0, 3)))

    fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)

    # Histograma 2D
    x = positions[:, 0]
    y = positions[:, 1]

    h = ax.hist2d(
        x, y,
        bins=n_bins,
        range=[[-limit, limit], [-limit, limit]],
        cmap=colormap,
        norm=LogNorm(vmin=1, vmax=1e5),
        rasterized=True
    )

    # Colorbar
    cbar = plt.colorbar(h[3], ax=ax)
    cbar.set_label('Densidade (partículas/kpc²)', fontsize=10)

    # Configurar
    ax.set_xlabel('X (kpc)')
    ax.set_ylabel('Y (kpc)')
    ax.set_aspect('equal')
    ax.set_title(
        f'Densidade Estelar | t = {time_gyr:.2f} Gyr | d = {distance_kpc:.0f} kpc',
        fontsize=12
    )

    # Salvar
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    logger.debug(f"Mapa de densidade salvo: {output_path}")
    return output_path


class FrameRenderer:
    """
    Renderizador completo de frames para animações.

    Gerencia a renderização de múltiplos frames com configurações
    consistentes e metadados.

    Attributes:
        output_dir: Diretório para salvar frames.
        config: Configurações de renderização.
    """

    def __init__(
        self,
        output_dir: Path,
        figsize: Tuple[int, int] = (12, 8),
        dpi: int = 100,
        colormap: str = "inferno",
    ):
        """
        Inicializa o renderizador.

        Args:
            output_dir: Diretório de saída.
            figsize: Tamanho da figura.
            dpi: Resolução.
            colormap: Colormap padrão.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.figsize = figsize
        self.dpi = dpi
        self.colormap = colormap

        logger.info(
            f"FrameRenderer inicializado: output={output_dir}, "
            f"figsize={figsize}, dpi={dpi}"
        )

    def render_all_frames(
        self,
        snapshots: List[Dict[str, np.ndarray]],
        orbit_distances: Optional[np.ndarray] = None,
        mode: str = "2d",
    ) -> List[Path]:
        """
        Renderiza todos os frames de uma sequência.

        Args:
            snapshots: Lista de snapshots.
            orbit_distances: Array de distâncias orbitais (opcional).
            mode: Modo de renderização ('2d', '3d', 'density').

        Returns:
            list: Lista de caminhos das imagens.
        """
        frame_paths = []
        n_snapshots = len(snapshots)

        logger.info(f"Renderizando {n_snapshots} frames no modo '{mode}'...")

        for i, snapshot in enumerate(snapshots):
            time_gyr = snapshot.get("time", 0.0) / 1000.0  # Myr -> Gyr

            # Obter distância se disponível
            if orbit_distances is not None and i < len(orbit_distances):
                distance = orbit_distances[i]
            else:
                # Calcular distância aproximada entre centros
                positions = snapshot.get("position", np.zeros((0, 3)))
                types = snapshot.get("type", np.zeros(len(positions)))

                mw_mask = types < 10
                m31_mask = types >= 10

                if np.any(mw_mask) and np.any(m31_mask):
                    center_mw = np.mean(positions[mw_mask], axis=0)
                    center_m31 = np.mean(positions[m31_mask], axis=0)
                    distance = np.linalg.norm(center_mw - center_m31)
                else:
                    distance = 765.0

            # Nome do arquivo
            filename = f"frame_{i:04d}.png"
            filepath = self.output_dir / filename

            # Renderizar baseado no modo
            if mode == "3d":
                render_frame_3d(
                    snapshot=snapshot,
                    output_path=filepath,
                    time_gyr=time_gyr,
                    distance_kpc=distance,
                    figsize=self.figsize,
                    dpi=self.dpi,
                )
            elif mode == "density":
                render_density_map(
                    snapshot=snapshot,
                    output_path=filepath,
                    time_gyr=time_gyr,
                    distance_kpc=distance,
                    figsize=self.figsize,
                    dpi=self.dpi,
                    colormap=self.colormap,
                )
            else:  # mode == "2d"
                render_frame_2d(
                    snapshot=snapshot,
                    output_path=filepath,
                    time_gyr=time_gyr,
                    distance_kpc=distance,
                    figsize=self.figsize,
                    dpi=self.dpi,
                    colormap=self.colormap,
                )

            frame_paths.append(filepath)

            # Progresso
            if (i + 1) % 10 == 0 or i == n_snapshots - 1:
                progress = 100 * (i + 1) / n_snapshots
                logger.info(f"Renderização: {progress:.0f}% ({i+1}/{n_snapshots})")

        logger.info(f"{len(frame_paths)} frames renderizados com sucesso")
        return frame_paths

    def render_orbit_overlay(
        self,
        snapshots: List[Dict[str, np.ndarray]],
        orbit_result: Dict[str, np.ndarray],
        output_dir: Optional[Path] = None,
    ) -> List[Path]:
        """
        Renderiza frames com sobreposição da órbita calculada.

        Args:
            snapshots: Snapshots da simulação.
            orbit_result: Resultado da integração orbital.
            output_dir: Diretório de saída (usa default se None).

        Returns:
            list: Caminhos das imagens.
        """
        if output_dir is None:
            output_dir = self.output_dir / "orbit_overlay"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        orbit_positions = orbit_result.get("position", np.zeros((3, 0)))
        orbit_times = orbit_result.get("time", np.array([]))

        frame_paths = []

        for i, snapshot in enumerate(snapshots):
            time_gyr = snapshot.get("time", 0.0) / 1000.0

            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            # Plot partículas
            positions = snapshot.get("position", np.zeros((0, 3)))
            types = snapshot.get("type", np.zeros(len(positions)))

            mw_mask = types < 10
            m31_mask = types >= 10

            if np.any(mw_mask):
                ax.scatter(positions[mw_mask, 0], positions[mw_mask, 1],
                          s=0.5, c='steelblue', alpha=0.5)
            if np.any(m31_mask):
                ax.scatter(positions[m31_mask, 0], positions[m31_mask, 1],
                          s=0.5, c='crimson', alpha=0.5)

            # Plot órbita
            if len(orbit_positions.shape) > 1 and orbit_positions.shape[0] >= 2:
                # Encontrar posição atual na órbita
                if len(orbit_times) > 0:
                    idx = np.argmin(np.abs(orbit_times - time_gyr))
                    current_pos = orbit_positions[:, idx]

                    # Plot trajetória até agora
                    ax.plot(orbit_positions[0, :idx+1], orbit_positions[1, :idx+1],
                           'g-', linewidth=2, alpha=0.7, label='Órbita')

                    # Marcar posição atual
                    ax.scatter(current_pos[0], current_pos[1],
                              s=100, c='lime', marker='*', zorder=5)

            ax.set_xlabel('X (kpc)')
            ax.set_ylabel('Y (kpc)')
            ax.set_aspect('equal')
            ax.set_title(f't = {time_gyr:.2f} Gyr')
            ax.legend()

            filepath = output_dir / f"orbit_{i:04d}.png"
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight', facecolor='black')
            plt.close(fig)

            frame_paths.append(filepath)

        logger.info(f"{len(frame_paths)} frames com órbita renderizados")
        return frame_paths
