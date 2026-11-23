import unittest
import numpy as np
from numpy.testing import assert_allclose

from simulation.body import Body
from simulation.physics import Simulation,Settings
from simulation.collisions import swept_contact


def star():
    return Body("Sol",1,[0,0,0],[0,0,0],.24,(1,.7,.2),"Estrela",.00465)


class CollisionTests(unittest.TestCase):
    def test_swept_contact_crossing_grazing_and_stationary(self):
        self.assertAlmostEqual(swept_contact([-2,0,0],[2,0,0],.5),.375)
        self.assertIsNone(swept_contact([-2,1,0],[2,1,0],.5))
        self.assertIsNone(swept_contact([-2,0,0],[-3,0,0],.5))
        self.assertIsNone(swept_contact([2,0,0],[2,0,0],.5))
        self.assertEqual(swept_contact([0,0,0],[0,0,0],.5),0)

    def test_fast_planet_cannot_pass_through_sun(self):
        sun=star()
        planet=Body("Viajante",.001,[-1,0,0],[4000,0,0])
        sim=Simulation([sun,planet],Settings(g=1e-12,dt=.001,collisions=False))
        initial=sim.momentum.copy()
        sim.step()
        self.assertEqual(len(sim.bodies),1)
        self.assertEqual(sim.bodies[0].uid,sun.uid)
        self.assertEqual(sim.bodies[0].name,"Sol")
        self.assertAlmostEqual(sim.bodies[0].mass,1.001)
        assert_allclose(sim.momentum,initial,atol=1e-11)
        self.assertEqual(sim.collision_events[0].kind,"absorption")
        self.assertGreater(sim.collision_events[0].time,0)
        self.assertLess(sim.collision_events[0].time,sim.time)
        for _ in range(100):
            sim.step()
        self.assertEqual(len(sim.bodies),1)
        self.assertEqual(len(sim.collision_events),1)

    def test_star_identity_survives_either_order(self):
        sun=star()
        planet=Body("Planeta",.01,[.15,0,0],[0,0,0])
        sim=Simulation([planet,sun])
        sim.step()
        self.assertEqual(sim.bodies[0].uid,sun.uid)
        self.assertEqual(sim.bodies[0].color,sun.color)
        self.assertEqual(sim.collision_events[0].survivor_uid,sun.uid)

    def test_near_miss_does_not_absorb(self):
        sim=Simulation([star(),Body("Rasante",.001,[-1,.3,0],[4000,0,0])],
                       Settings(g=1e-12,dt=.001))
        sim.step()
        self.assertEqual(len(sim.bodies),2)
        self.assertFalse(sim.collision_events)

    def test_fast_planets_collide_between_steps(self):
        a=Body("A",2,[-1,0,0],[2000,0,0],collision_radius=.1)
        b=Body("B",3,[1,0,0],[-2000,0,0],collision_radius=.1)
        sim=Simulation([a,b],Settings(g=1e-12,dt=.001))
        initial=sim.momentum.copy()
        sim.step()
        self.assertEqual(len(sim.bodies),1)
        self.assertEqual(sim.bodies[0].mass,5)
        assert_allclose(sim.momentum,initial,atol=1e-9)
        self.assertEqual(sim.collision_events[0].kind,"impact")
        self.assertAlmostEqual(sim.time,.001)

    def test_planet_collisions_can_be_disabled(self):
        sim=Simulation([Body("A",1,[0,0,0],[0,0,0],collision_radius=.1),
                        Body("B",1,[.1,0,0],[0,0,0],collision_radius=.1)],
                       Settings(g=1e-12,collisions=False))
        sim.step()
        self.assertEqual(len(sim.bodies),2)
        self.assertFalse(sim.collision_events)

    def test_visible_stellar_surface_absorbs_before_physical_radius(self):
        sim=Simulation([star(),Body("A",1e-6,[.2,0,0],[0,0,0])])
        sim.step()
        self.assertEqual(len(sim.bodies),1)

    def test_contact_before_singularity_with_zero_softening(self):
        sim=Simulation([star(),Body("A",1e-6,[-1,0,0],[1000,0,0])],
                       Settings(g=1e-12,dt=.001,softening=0))
        sim.step()
        self.assertEqual(len(sim.bodies),1)
        self.assertTrue(np.isfinite(sim.total_energy))

    def test_chain_contacts_and_events(self):
        bodies=[Body(str(i),1,[i*.05,0,0],[i,0,0],collision_radius=.1) for i in range(3)]
        sim=Simulation(bodies,Settings(g=1e-12))
        sim.step()
        self.assertEqual(len(sim.bodies),1)
        self.assertEqual(sim.bodies[0].mass,3)
        assert_allclose(sim.momentum,[3,0,0])
        self.assertEqual(len(sim.collision_events),2)


if __name__=="__main__":
    unittest.main()
