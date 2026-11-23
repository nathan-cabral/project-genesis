import unittest
import numpy as np
from numpy.testing import assert_allclose

from simulation.body import Body
from simulation.creation import ray_plane_intersection,suggested_velocity
from simulation.physics import Simulation,Settings
from interface.chart_data import series,axis_bounds


class CreationTests(unittest.TestCase):
    def test_ray_hits_explicit_height(self):
        assert_allclose(ray_plane_intersection([1,10,2],[.5,-1,1],2),[5,2,10])

    def test_parallel_and_behind_camera_are_rejected(self):
        self.assertIsNone(ray_plane_intersection([0,2,0],[1,0,0]))
        self.assertIsNone(ray_plane_intersection([0,2,0],[1,1,0]))

    def test_suggested_velocity_is_tangent_and_softened(self):
        source=Body("A",2,[0,0,0],[1,2,3])
        velocity=suggested_velocity([3,0,0],.1,[source],4,.2)
        relative=velocity-source.velocity
        self.assertAlmostEqual(np.dot(relative,[3,0,0]),0)
        self.assertAlmostEqual(np.linalg.norm(relative)**2,4*2.1*9/(9+.04)**1.5)

    def test_empty_and_polar_systems(self):
        assert_allclose(suggested_velocity([0,1,0],1,[],1),0)
        b=Body("A",1,[0,0,0],[0,0,0])
        self.assertTrue(np.all(np.isfinite(suggested_velocity([0,2,0],1,[b],1))))
        with self.assertRaises(ValueError):
            suggested_velocity([0,0,0],1,[b],1)


class ChartTests(unittest.TestCase):
    def setUp(self):
        self.b=Body("A",1,[0,0,0],[2,0,0])
        self.sim=Simulation([self.b],Settings(dt=.001))
        for _ in range(30):
            self.sim.step()

    def test_velocity_values_are_measured_not_normalized(self):
        data,unit=series(self.sim,"Velocidade",self.b)
        assert_allclose(data[0][2],2)
        self.assertEqual(unit,"AU/ano")

    def test_energy_relative_error(self):
        data,unit=series(self.sim,"Energia")
        assert_allclose(data[0][2],0)
        self.assertIn("%",unit)

    def test_zero_reference_and_missing_selection(self):
        empty=Simulation()
        data,unit=series(empty,"Energia")
        self.assertNotIn("%",unit)
        self.assertTrue(np.all(np.isfinite(data[0][2])))
        self.assertEqual(series(self.sim,"Distância",self.b)[0],[])
        self.assertEqual(series(self.sim,"Posição")[0],[])

    def test_xyz_preserves_components(self):
        data,_=series(self.sim,"Posição",self.b)
        self.assertEqual([name for name,_,_ in data],list("XYZ"))
        self.assertAlmostEqual(data[0][2][-1],.06)
        assert_allclose(data[1][2],0)

    def test_constant_series_gets_readable_axis(self):
        low,high=axis_bounds([100,100.00000001])
        self.assertGreater(high-low,5)


if __name__=="__main__":
    unittest.main()
