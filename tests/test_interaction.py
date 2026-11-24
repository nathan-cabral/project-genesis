import unittest
import numpy as np
from numpy.testing import assert_allclose

from simulation.body import Body
from simulation.creation import ray_plane_intersection,suggested_velocity


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


if __name__=="__main__":
    unittest.main()
