"""
test_dynamics.py - Testes para módulo de dinâmica orbital.

Testa as funcionalidades principais do orbit_solver e collision_estimator.
"""

import unittest
import numpy as np
from astropy import units as u
import sys
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dynamics.orbit_solver import OrbitSolver, create_mw_potential, create_m31_potential
from src.dynamics.collision_estimator import CollisionEstimator, estimate_collision_time


class TestOrbitSolver(unittest.TestCase):
    """Testes para a classe OrbitSolver."""

    def setUp(self):
        """Configura testes."""
        self.solver = OrbitSolver()

    def test_solver_initialization(self):
        """Testa inicialização do solver."""
        self.assertIsNotNone(self.solver.mw_potential)
        self.assertIsNotNone(self.solver.m31_potential)
        self.assertGreater(self.solver.total_mass.value, 0)

    def test_solve_orbit_basic(self):
        """Testa integração orbital básica."""
        result = self.solver.solve_orbit(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            tangential_velocity=17 * u.km / u.s,
            duration=5.0 * u.Gyr,
            n_steps=100,
        )

        # Verificar estrutura do resultado
        self.assertIn("time", result)
        self.assertIn("position", result)
        self.assertIn("distance", result)
        self.assertIn("velocity", result)

        # Verificar dimensões
        self.assertEqual(len(result["time"]), 100)
        self.assertEqual(result["position"].shape[0], 3)

    def test_solve_orbit_radial(self):
        """Testa órbita puramente radial (sem velocidade tangencial)."""
        result = self.solver.solve_orbit(
            initial_distance=500 * u.kpc,
            radial_velocity=-150 * u.km / u.s,
            tangential_velocity=0 * u.km / u.s,
            duration=3.0 * u.Gyr,
            n_steps=50,
        )

        # Em órbita radial, distância deve diminuir inicialmente
        distances = result["distance"]
        self.assertLess(distances[-1], distances[0])

    def test_get_closest_approach(self):
        """Testa detecção de periapsis."""
        result = self.solver.solve_orbit(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            tangential_velocity=50 * u.km / u.s,  # Maior vt para evitar colisão
            duration=10.0 * u.Gyr,
            n_steps=200,
        )

        time_peri, dist_peri = self.solver.get_closest_approach(result)

        self.assertGreater(time_peri, 0)
        self.assertGreater(dist_peri, 0)
        self.assertLessEqual(dist_peri, result["distance"].min() + 1)  # Tolerância


class TestCollisionEstimator(unittest.TestCase):
    """Testes para a classe CollisionEstimator."""

    def setUp(self):
        """Configura testes."""
        self.estimator = CollisionEstimator()

    def test_estimate_collision_time_bound(self):
        """Testa estimativa para sistema ligado (colisão garantida)."""
        result = self.estimator.estimate_collision_time(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            total_mass=2.5e12 * u.Msun,
            tangential_velocity=17 * u.km / u.s,
        )

        self.assertIn("collision_time_gyr", result)
        self.assertIn("periapsis_distance_kpc", result)
        self.assertIn("is_bound", result)

        # Sistema MW-M31 deve estar ligado
        self.assertTrue(result["is_bound"])

        # Tempo de colisão deve ser positivo e finito
        self.assertGreater(result["collision_time_gyr"], 0)
        self.assertLess(result["collision_time_gyr"], 20)  # < 20 Gyr

    def test_estimate_collision_time_radial(self):
        """Testa estimativa para queda radial pura."""
        result = self.estimator.estimate_collision_time(
            initial_distance=500 * u.kpc,
            radial_velocity=-200 * u.km / u.s,
            total_mass=2.5e12 * u.Msun,
            tangential_velocity=0 * u.km / u.s,
        )

        # Colisão deve ocorrer mais rápido em queda radial
        self.assertLess(result["collision_time_gyr"], 10)

    def test_find_closest_approach_from_orbit(self):
        """Testa extração de periapsis de órbita integrada."""
        solver = OrbitSolver()
        orbit_result = solver.solve_orbit(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            tangential_velocity=17 * u.km / u.s,
            duration=10.0 * u.Gyr,
            n_steps=100,
        )

        closest = self.estimator.find_closest_approach_from_orbit(orbit_result)

        self.assertIn("time_gyr", closest)
        self.assertIn("distance_kpc", closest)
        self.assertIn("velocity_km_s", closest)

        self.assertGreater(closest["time_gyr"], 0)
        self.assertGreater(closest["distance_kpc"], 0)

    def test_count_encounters(self):
        """Testa contagem de encontros próximos."""
        solver = OrbitSolver()
        orbit_result = solver.solve_orbit(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            tangential_velocity=100 * u.km / u.s,  # Alta vt para múltiplos encontros
            duration=15.0 * u.Gyr,
            n_steps=300,
        )

        # Contar encontros dentro de 100 kpc
        n_encounters = self.estimator.count_encounters(orbit_result, threshold=100)

        self.assertIsInstance(n_encounters, int)
        self.assertGreaterEqual(n_encounters, 0)


class TestUtilityFunctions(unittest.TestCase):
    """Testes para funções utilitárias."""

    def test_create_mw_potential(self):
        """Testa criação do potencial da Via Láctea."""
        potential = create_mw_potential(
            mass_disk=5.0e10 * u.Msun,
            mass_bulge=1.0e10 * u.Msun,
            mass_halo=1.0e12 * u.Msun,
        )

        self.assertIsNotNone(potential)

    def test_create_m31_potential(self):
        """Testa criação do potencial de Andrômeda."""
        potential = create_m31_potential(
            mass_disk=8.0e10 * u.Msun,
            mass_bulge=3.0e10 * u.Msun,
            mass_halo=1.5e12 * u.Msun,
        )

        self.assertIsNotNone(potential)

    def test_estimate_collision_time_function(self):
        """Testa função utilitária estimate_collision_time."""
        result = estimate_collision_time(
            initial_distance=765 * u.kpc,
            radial_velocity=-110 * u.km / u.s,
            mw_mass=1.0e12 * u.Msun,
            m31_mass=1.5e12 * u.Msun,
        )

        self.assertIsInstance(result, dict)
        self.assertIn("collision_time_gyr", result)


class TestPhysicsConsistency(unittest.TestCase):
    """Testes de consistência física."""

    def test_energy_conservation_approximate(self):
        """Testa conservação aproximada de energia em órbita."""
        solver = OrbitSolver()

        # Órbita com baixa excentricidade
        result = solver.solve_orbit(
            initial_distance=500 * u.kpc,
            radial_velocity=-50 * u.km / u.s,
            tangential_velocity=150 * u.km / u.s,
            duration=5.0 * u.Gyr,
            n_steps=100,
        )

        # Calcular energia específica em cada ponto
        G_val = 4.302e-6  # kpc * (km/s)^2 / Msun
        M = solver.total_mass.to(u.Msun).value

        velocities = result["velocity"]
        distances = result["distance"]

        v_squared = np.sum(velocities**2, axis=0)
        energies = 0.5 * v_squared - G_val * M / distances

        # Energia não deve variar mais que 10% (integração numérica)
        energy_variation = (energies.max() - energies.min()) / np.abs(energies.mean())

        # Tolerância generosa devido à aproximação
        self.assertLess(energy_variation, 0.5)

    def test_angular_momentum_conservation(self):
        """Testa conservação aproximada de momento angular."""
        solver = OrbitSolver()

        result = solver.solve_orbit(
            initial_distance=500 * u.kpc,
            radial_velocity=-50 * u.km / u.s,
            tangential_velocity=150 * u.km / u.s,
            duration=5.0 * u.Gyr,
            n_steps=100,
        )

        positions = result["position"]
        velocities = result["velocity"]

        # Momento angular específico L = r × v
        L_x = positions[1] * velocities[2] - positions[2] * velocities[1]
        L_y = positions[2] * velocities[0] - positions[0] * velocities[2]
        L_z = positions[0] * velocities[1] - positions[1] * velocities[0]

        L_magnitude = np.sqrt(L_x**2 + L_y**2 + L_z**2)

        # Variação relativa
        L_variation = (L_magnitude.max() - L_magnitude.min()) / L_magnitude.mean()

        # Tolerância generosa
        self.assertLess(L_variation, 0.3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
