"""Screen ray projected on an explicit horizontal construction plane."""
import numpy as np
from panda3d.core import Point2, Point3
from ursina import Entity, Mesh, camera, application, mouse, window, color, destroy

from simulation.creation import ray_plane_intersection


def screen_position_on_plane(x, y, height=0):
    near,far=Point3(),Point3()
    lens=application.base.cam.node().get_lens()
    if not lens.extrude(Point2(2*x/window.aspect_ratio,2*y),near,far):
        return None
    root=application.base.render
    cam=application.base.cam
    origin=np.array(root.get_relative_point(cam,near))
    end=np.array(root.get_relative_point(cam,far))
    return ray_plane_intersection(origin,end-origin,height)


class PlacementPreview:
    def __init__(self,height=0):
        self.height=height
        self.root=Entity()
        grid=[]
        for value in range(-12,13):
            grid.extend(((value,height,-12),(value,height,12),(-12,height,value),(12,height,value)))
        Entity(parent=self.root,model=Mesh(vertices=grid,triangles=[(i,i+1) for i in range(0,len(grid),2)],mode="line"),
               color=color.rgba32(97,162,170,38))
        circle=[(.18*np.cos(t),0,.18*np.sin(t)) for t in np.linspace(0,2*np.pi,64)]
        self.marker=Entity(parent=self.root,model=Mesh(vertices=circle,mode="line",thickness=2),color=color.rgb32(106,221,200))
        self.dot=Entity(parent=self.marker,model="sphere",scale=.055,color=color.rgb32(180,255,232))
        self.position=None

    def update(self):
        self.position=screen_position_on_plane(mouse.x,mouse.y,self.height)
        if self.position is not None and np.linalg.norm(self.position)<1e4:
            self.marker.enabled=True
            self.marker.position=tuple(self.position)
        else:
            self.position=None
            self.marker.enabled=False

    def close(self):
        destroy(self.root)
