#!/usr/bin/env python3
"""
main.py - Entry point CLI para o Simulador Milkomeda.

Este módulo fornece a interface de linha de comando para executar
simulações completas da fusão entre Via Láctea e Andrômeda.

Exemplos de uso:
    # Executar com parâmetros padrão
    python main.py --run

    # Personalizar distância inicial e duração
    python main.py --distance 800kpc --duration 12Gyr --run

    # Apenas calcular órbita sem simulação N-corpos
    python main.py --orbit-only --distance 765kpc

    # Gerar vídeo em alta resolução
    python main.py --run --resolution 1920x1080 --fps 60
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import numpy as np
from astropy import units as u

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_default_config, PROJECT_ROOT
from src.utils.logger import setup_logger, get_logger
from src.dynamics.orbit_solver import OrbitSolver
from src.dynamics.collision_estimator import CollisionEstimator
from src.simulation.particle_generator import ParticleGenerator
from src.simulation.nbody_integrator import NBodyIntegrator, evolve_system
from src.rendering.frame_renderer import FrameRenderer
from src.rendering.video_compiler import VideoCompiler


def parse_arguments() -> argparse.Namespace:
    """
    Parseia argumentos da linha de comando.

    Returns:
        Namespace: Argumentos parseados.
    """
    parser = argparse.ArgumentParser(
        prog="milkomeda",
        description="Simulador de Fusão Via Láctea & Andrômeda (Milkomeda)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --run
      Executa simulação completa com parâmetros padrão

  %(prog)s --distance 800kpc --velocity -120km/s --run
      Personaliza distância e velocidade inicial

  %(prog)s --orbit-only --duration 15Gyr
      Apenas calcula órbita, sem simulação N-corpos

  %(prog)s --run --n-particles 20000 --output_dir ./minha_simulacao
      Simulação com mais partículas e diretório personalizado
        """,
    )

    # Parâmetros orbitais
    orbital_group = parser.add_argument_group("Parâmetros Orbitais")
    orbital_group.add_argument(
        "--distance", "-d",
        type=str,
        default="765kpc",
        help="Distância inicial MW-M31 (ex: 765kpc, 800kpc). Default: 765kpc"
    )
    orbital_group.add_argument(
        "--velocity", "-v",
        type=str,
        default="-110km/s",
        help="Velocidade radial (ex: -110km/s, -120km/s). Default: -110km/s"
    )
    orbital_group.add_argument(
        "--tangential-velocity",
        type=str,
        default="17km/s",
        help="Velocidade tangencial. Default: 17km/s"
    )
    orbital_group.add_argument(
        "--duration", "-t",
        type=str,
        default="10Gyr",
        help="Duração da simulação. Default: 10Gyr"
    )

    # Parâmetros de simulação
    sim_group = parser.add_argument_group("Parâmetros de Simulação")
    sim_group.add_argument(
        "--n-particles", "-n",
        type=int,
        default=10000,
        help="Número total de partículas por galáxia. Default: 10000"
    )
    sim_group.add_argument(
        "--n-steps",
        type=int,
        default=100,
        help="Número de passos de integração. Default: 100"
    )
    sim_group.add_argument(
        "--dt",
        type=float,
        default=100.0,
        help="Passo de tempo em Myr. Default: 100"
    )
    sim_group.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed aleatória para reproducibilidade"
    )

    # Parâmetros de renderização
    render_group = parser.add_argument_group("Renderização")
    render_group.add_argument(
        "--resolution", "-r",
        type=str,
        default="1280x720",
        help="Resolução do vídeo (ex: 1280x720, 1920x1080). Default: 1280x720"
    )
    render_group.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames por segundo. Default: 30"
    )
    render_group.add_argument(
        "--render-mode",
        type=str,
        choices=["2d", "3d", "density"],
        default="2d",
        help="Modo de renderização. Default: 2d"
    )
    render_group.add_argument(
        "--no-video",
        action="store_true",
        help="Não compilar vídeo, apenas salvar frames"
    )

    # Opções de execução
    exec_group = parser.add_argument_group("Execução")
    exec_group.add_argument(
        "--run",
        action="store_true",
        help="Executar simulação completa"
    )
    exec_group.add_argument(
        "--orbit-only",
        action="store_true",
        help="Apenas calcular órbita, sem simulação N-corpos"
    )
    exec_group.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Diretório de saída. Default: ./outputs"
    )
    exec_group.add_argument(
        "--verbose",
        action="store_true",
        help="Habilitar logs detalhados (DEBUG)"
    )
    exec_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suprimir logs (apenas WARNING+)"
    )
    exec_group.add_argument(
        "--report",
        action="store_true",
        help="Gerar relatório científico em JSON"
    )

    return parser.parse_args()


def parse_quantity(value_str: str, default_unit: u.Unit) -> u.Quantity:
    """
    Parseia string de quantidade física.

    Args:
        value_str: String no formato "valor unidade" ou apenas "valor".
        default_unit: Unidade padrão.

    Returns:
        Quantity: Valor parseado.
    """
    parts = value_str.strip().replace(" ", "")

    # Tentar extrair número e unidade
    import re
    match = re.match(r"^(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)(.*)$", parts, re.IGNORECASE)

    if match:
        value = float(match.group(1))
        unit_str = match.group(2)

        if unit_str:
            try:
                unit = u.Unit(unit_str)
            except ValueError:
                unit = default_unit
        else:
            unit = default_unit

        return value * unit
    else:
        return float(parts) * default_unit


def run_orbit_calculation(args: argparse.Namespace, config: dict) -> dict:
    """
    Executa cálculo orbital.

    Args:
        args: Argumentos da CLI.
        config: Configuração.

    Returns:
        dict: Resultado da órbita.
    """
    logger = get_logger("milkomeda.orbit")
    logger.info("Calculando órbita MW-M31...")

    # Parsear entradas
    distance = parse_quantity(args.distance, u.kpc)
    velocity = parse_quantity(args.velocity, u.km/u.s)
    tangential_vel = parse_quantity(args.tangential_velocity, u.km/u.s)
    duration = parse_quantity(args.duration, u.Gyr)

    logger.info(f"Distância inicial: {distance}")
    logger.info(f"Velocidade radial: {velocity}")
    logger.info(f"Velocidade tangencial: {tangential_vel}")

    # Criar solver e integrar
    solver = OrbitSolver()

    orbit_result = solver.solve_orbit(
        initial_distance=distance,
        radial_velocity=velocity,
        tangential_velocity=tangential_vel,
        duration=duration,
        n_steps=args.n_steps * 10,  # Mais passos para órbita suave
    )

    # Estimar colisão
    estimator = CollisionEstimator()
    closest = estimator.find_closest_approach_from_orbit(orbit_result)

    logger.info(
        f"Periapsis: t={closest['time_gyr']:.2f} Gyr, "
        f"d={closest['distance_kpc']:.1f} kpc"
    )

    return {
        "orbit": orbit_result,
        "closest_approach": closest,
        "params": {
            "distance": str(distance),
            "velocity": str(velocity),
            "tangential_velocity": str(tangential_vel),
            "duration": str(duration),
        },
    }


def run_nbody_simulation(
    args: argparse.Namespace,
    config: dict,
    orbit_result: dict,
) -> list:
    """
    Executa simulação N-corpos.

    Args:
        args: Argumentos da CLI.
        config: Configuração.
        orbit_result: Resultado orbital.

    Returns:
        list: Snapshots da simulação.
    """
    logger = get_logger("milkomeda.nbody")
    logger.info("Iniciando simulação N-corpos...")

    # Determinar número de partículas por componente
    n_total = args.n_particles
    n_disk = int(n_total * 0.5)
    n_halo = int(n_total * 0.35)
    n_bulge = int(n_total * 0.15)

    # Gerador de partículas
    generator = ParticleGenerator(seed=args.seed)

    # Parâmetros das galáxias
    mw_params = {
        "mass_disk": 6.0e10 * u.Msun,
        "mass_bulge": 1.0e10 * u.Msun,
        "mass_halo": 1.0e12 * u.Msun,
        "scale_length_disk": 3.0 * u.kpc,
        "scale_height_disk": 0.3 * u.kpc,
        "scale_radius_halo": 20.0 * u.kpc,
        "n_particles_disk": n_disk,
        "n_particles_halo": n_halo,
        "n_particles_bulge": n_bulge,
    }

    m31_params = {
        "mass_disk": 8.0e10 * u.Msun,
        "mass_bulge": 3.0e10 * u.Msun,
        "mass_halo": 1.5e12 * u.Msun,
        "scale_length_disk": 5.0 * u.kpc,
        "scale_height_disk": 0.4 * u.kpc,
        "scale_radius_halo": 25.0 * u.kpc,
        "n_particles_disk": n_disk,
        "n_particles_halo": n_halo,
        "n_particles_bulge": n_bulge,
    }

    # Gerar sistema binário
    distance = parse_quantity(args.distance, u.kpc)
    velocity = parse_quantity(args.velocity, u.km/u.s)

    mw, m31 = generator.generate_binary_system(
        mw_params=mw_params,
        m31_params=m31_params,
        separation=distance,
        relative_velocity=velocity,
    )

    logger.info(f"Sistema gerado: MW={mw['n_total']} part., M31={m31['n_total']} part.")

    # Diretório de snapshots
    output_dir = Path(args.output_dir) if args.output_dir else config["paths"]["snapshots"]

    # Evoluir sistema
    integrator = NBodyIntegrator()
    combined = integrator.combine_systems(mw, m31)

    snapshots = integrator.evolve(
        particles=combined,
        n_steps=args.n_steps,
        dt=args.dt,
        snapshot_interval=max(1, args.n_steps // 50),
        output_dir=output_dir,
    )

    logger.info(f"Simulação completa: {len(snapshots)} snapshots")
    return snapshots


def run_rendering(
    args: argparse.Namespace,
    config: dict,
    snapshots: list,
    orbit_result: dict,
) -> list:
    """
    Renderiza frames e compila vídeo.

    Args:
        args: Argumentos da CLI.
        config: Configuração.
        snapshots: Snapshots da simulação.
        orbit_result: Resultado orbital.

    Returns:
        list: Caminhos dos frames.
    """
    logger = get_logger("milkomeda.render")

    # Parsear resolução
    res_parts = args.resolution.split("x")
    resolution = (int(res_parts[0]), int(res_parts[1]))

    # Diretório de frames
    frames_dir = Path(args.output_dir) / "frames" if args.output_dir else config["paths"]["frames"]

    # Renderizador
    renderer = FrameRenderer(
        output_dir=frames_dir,
        figsize=(resolution[0] // 100, resolution[1] // 100),
        dpi=100,
    )

    # Obter distâncias da órbita
    orbit_distances = orbit_result.get("orbit", {}).get("distance", None)

    # Renderizar frames
    frame_paths = renderer.render_all_frames(
        snapshots=snapshots,
        orbit_distances=orbit_distances,
        mode=args.render_mode,
    )

    # Compilar vídeo se solicitado
    if not args.no_video:
        output_dir = Path(args.output_dir) if args.output_dir else config["paths"]["outputs"]
        video_path = output_dir / "milkomeda_simulation.mp4"

        compiler = VideoCompiler(
            fps=args.fps,
            resolution=resolution,
        )

        try:
            compiler.compile_frames(
                frame_paths=frame_paths,
                output_path=video_path,
                cleanup=False,  # Manter frames
            )
            logger.info(f"Vídeo compilado: {video_path}")
        except Exception as e:
            logger.error(f"Falha na compilação do vídeo: {e}")
            logger.info("Frames PNG disponíveis em: {}".format(frames_dir))

    return frame_paths


def generate_report(
    args: argparse.Namespace,
    config: dict,
    orbit_data: dict,
    n_snapshots: int,
) -> Path:
    """
    Gera relatório científico em JSON.

    Args:
        args: Argumentos da CLI.
        config: Configuração.
        orbit_data: Dados orbitais.
        n_snapshots: Número de snapshots.

    Returns:
        Path: Caminho do relatório.
    """
    output_dir = Path(args.output_dir) if args.output_dir else config["paths"]["outputs"]
    report_path = output_dir / "simulation_report.json"

    closest = orbit_data.get("closest_approach", {})

    report = {
        "metadata": {
            "simulation": "Milkomeda",
            "version": config["metadata"]["version"],
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(sys.argv),
        },
        "initial_conditions": orbit_data.get("params", {}),
        "collision_parameters": {
            "time_to_collision_gyr": closest.get("time_gyr", None),
            "periapsis_distance_kpc": closest.get("distance_kpc", None),
            "periapsis_velocity_km_s": closest.get("velocity_km_s", None),
        },
        "simulation_stats": {
            "n_snapshots": n_snapshots,
            "n_steps": args.n_steps,
            "dt_myr": args.dt,
            "total_time_myr": args.n_steps * args.dt,
        },
        "rendering": {
            "mode": args.render_mode,
            "resolution": args.resolution,
            "fps": args.fps,
        },
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger = get_logger("milkomeda.report")
    logger.info(f"Relatório salvo: {report_path}")

    return report_path


def main():
    """
    Função principal do simulador Milkomeda.
    """
    # Parsear argumentos
    args = parse_arguments()

    # Carregar configuração
    config = get_default_config()

    # Configurar logging
    if args.quiet:
        log_level = 30  # WARNING
    elif args.verbose:
        log_level = 10  # DEBUG
    else:
        log_level = 20  # INFO

    logger = setup_logger("milkomeda", level=log_level)

    logger.info("=" * 60)
    logger.info("MILKOMEDA - Simulador de Fusão Galáctica")
    logger.info("=" * 60)

    # Validar argumentos
    if not args.run and not args.orbit_only:
        logger.info("Use --run para executar simulação ou --orbit-only para apenas órbita")
        logger.info("Use --help para ver todas as opções")
        return 0

    # Calcular órbita
    orbit_data = run_orbit_calculation(args, config)

    if args.orbit_only:
        # Apenas mostrar resultado orbital
        closest = orbit_data["closest_approach"]
        print("\n" + "=" * 50)
        print("RESULTADO ORBITAL")
        print("=" * 50)
        print(f"Tempo até colisão: {closest['time_gyr']:.2f} Gyr")
        print(f"Distância de periapsis: {closest['distance_kpc']:.1f} kpc")
        print(f"Velocidade no periapsis: {closest['velocity_km_s']:.1f} km/s")
        print("=" * 50 + "\n")

        if args.report:
            generate_report(args, config, orbit_data, 0)

        return 0

    # Executar simulação N-corpos
    snapshots = run_nbody_simulation(args, config, orbit_data["orbit"])

    # Renderizar
    frame_paths = run_rendering(args, config, snapshots, orbit_data["orbit"])

    # Gerar relatório
    if args.report:
        generate_report(args, config, orbit_data, len(snapshots))

    # Resumo final
    logger.info("=" * 60)
    logger.info("SIMULAÇÃO COMPLETA")
    logger.info(f"  • Snapshots: {len(snapshots)}")
    logger.info(f"  • Frames renderizados: {len(frame_paths)}")
    logger.info(f"  • Colisão prevista em: {orbit_data['closest_approach']['time_gyr']:.2f} Gyr")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
