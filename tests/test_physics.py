import unittest

import numpy as np
from numpy.testing import assert_allclose

from simulation.body import Body, vector
from simulation.gravity import accelerations, pair_forces
from simulation.physics import Settings, Simulation
from simulation.scenarios import binary, solar


class PhysicsTests(unittest.TestCase):
    def test_vectors_and_distance(self):
        self.assertEqual(np.linalg.norm(vector([3,4,0])), 5)
        for invalid in ([1,2], [1,np.nan,3]):
            with self.assertRaises(ValueError):
                vector(invalid)

    def test_newton_and_inverse_square(self):
        masses = np.array([2., 3.])
        positions = np.array([[0.,0,0], [2.,0,0]])
        f = pair_forces(positions, masses, g=1, softening=0)
        assert_allclose(f[0,1], [1.5,0,0])
        assert_allclose(f[0,1], -f[1,0])
        positions[1,0] = 4
        assert_allclose(pair_forces(positions,masses,1,0)[0,1], f[0,1]/4)

    def test_vector_sum_and_acceleration(self):
        p = np.array([[0.,0,0], [1.,0,0], [0.,2,0]])
        m = np.array([2.,3.,4.])
        assert_allclose(pair_forces(p,m,1,0).sum(axis=1)[0], [6,2,0])
        assert_allclose(accelerations(p,m,1,0)[0], [3,1,0])
        m[0] = 200
        assert_allclose(accelerations(p,m,1,0)[0], [3,1,0])

    def test_uniform_motion(self):
        sim = Simulation([Body("A", 1, [1,2,3], [2,-3,4])], Settings(dt=.01))
        for _ in range(100):
            sim.step()
        assert_allclose(sim.bodies[0].position, [3,-1,7], atol=1e-12)
        assert_allclose(sim.bodies[0].velocity, [2,-3,4])

    def test_merger_conserves_mass_and_momentum(self):
        sim = Simulation([Body("A",2,[0,0,0],[1,2,3],collision_radius=.2),
                          Body("B",3,[.1,0,0],[-2,1,0],collision_radius=.2)])
        initial = sim.momentum.copy()
        sim.merge_collisions()
        self.assertEqual(len(sim.bodies), 1)
        self.assertEqual(sim.bodies[0].mass, 5)
        assert_allclose(sim.momentum, initial)
        assert_allclose(sim.bodies[0].position, [.06,0,0])

    def test_collision_scenario_merges_in_motion(self):
        from simulation.scenarios import approach
        sim=Simulation(approach(True),Settings(collisions=True))
        initial=sim.momentum.copy()
        for _ in range(6000):
            sim.step()
            if len(sim.bodies)==1:
                break
        self.assertEqual(len(sim.bodies),1)
        self.assertAlmostEqual(sim.bodies[0].mass,.04)
        assert_allclose(sim.momentum,initial,atol=1e-12)

    def test_binary_energy_and_momentum(self):
        sim = Simulation(binary())
        initial = sim.total_energy
        for _ in range(4000):
            sim.step()
        self.assertLess(abs((sim.total_energy-initial)/initial), 1e-8)
        assert_allclose(sim.momentum, [0,0,0], atol=1e-12)

    def test_softening_handles_coincident_bodies(self):
        p = np.zeros((2,3))
        assert_allclose(accelerations(p,np.ones(2),1,.01), 0)
        with self.assertRaises(ValueError):
            accelerations(p,np.ones(2),1,0)

    def test_verlet_constant_acceleration_position(self):
        from simulation.integrator import velocity_verlet
        p = np.array([[0.,0,0],[1.,0,0]])
        v = np.zeros((2,3))
        np_, nv, na = velocity_verlet(p,v,np.ones(2),.01,1,0)
        assert_allclose(np_[0], [.00005,0,0])
        assert_allclose(nv[0], .5*(np.array([1,0,0])+na[0])*.01)

    def test_demo_stays_finite(self):
        sim = Simulation(solar())
        self.assertEqual(len(sim.bodies), 10)
        e = sim.total_energy
        for _ in range(2000):
            sim.step()
        self.assertTrue(np.isfinite(sim.total_energy))
        self.assertLess(abs((sim.total_energy-e)/e), 1e-4)

    def test_invalid_add_is_atomic(self):
        sim=Simulation([Body("A",1,[0,0,0],[0,0,0])],Settings(softening=0))
        with self.assertRaises(ValueError):
            sim.add(Body("B",1,[0,0,0],[0,0,0]))
        self.assertEqual(len(sim.bodies),1)

    def test_invalid_body_and_settings(self):
        for mass in (0,-1,np.inf,np.nan):
            with self.assertRaises(ValueError):
                Body("A",mass,[0,0,0],[0,0,0])
        for dt in (0,-.1,np.nan):
            with self.assertRaises(ValueError):
                Settings(dt=dt).validate()

    def test_fixed_step_converges_quadratically(self):
        results=[]
        for dt in (.01,.005,.000625):
            sim=Simulation(binary(),Settings(dt=dt))
            for _ in range(round(.5/dt)):
                sim.step()
            results.append(sim.bodies[0].position.copy())
        coarse=np.linalg.norm(results[0]-results[2])
        fine=np.linalg.norm(results[1]-results[2])
        self.assertGreater(coarse/fine,3.8)

    def test_trails_bounded_and_restart_after_edit(self):
        sim=Simulation(binary(),Settings(trail_length=10))
        for _ in range(150):
            sim.step()
        self.assertEqual(len(sim.trails[sim.bodies[0].uid]),10)
        sim.refresh_after_edit()
        for body in sim.bodies:
            self.assertEqual(len(sim.trails[body.uid]),1)
            assert_allclose(sim.trails[body.uid][0],body.position)


if __name__ == "__main__":
    unittest.main()
