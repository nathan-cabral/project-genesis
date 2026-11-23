import numpy as np
from ursina import Entity, Mesh, color, destroy


class FieldRenderer:
    """Test acceleration probes; they have no mass and do not affect the system."""
    def __init__(self):
        self.entity=None

    def draw(self,sim,visible):
        if self.entity:
            destroy(self.entity)
            self.entity=None
        if not visible or not sim.bodies:
            return
        p,_,m=sim.arrays()
        points=np.array([(x,0,z) for x in np.linspace(-7,7,13) for z in np.linspace(-7,7,13)])
        d=p[None,:,:]-points[:,None,:]
        r2=(d*d).sum(axis=2)+max(sim.settings.softening,1e-8)**2
        field=(sim.settings.g*m[None,:,None]*d/r2[:,:,None]**1.5).sum(axis=1)
        vertices=[]
        for start,a in zip(points,field):
            norm=np.linalg.norm(a)
            if norm<1e-12:
                continue
            direction=a/norm
            length=min(.5,.14*np.log1p(norm))
            end=start+direction*length
            side=np.cross(direction,[0,1,0]); side/=max(np.linalg.norm(side),1e-12)
            for first,last in ((start,end),(end,end-direction*length*.25+side*length*.12),
                               (end,end-direction*length*.25-side*length*.12)):
                vertices.extend((tuple(first),tuple(last)))
        self.entity=Entity(model=Mesh(vertices=vertices,triangles=[(i,i+1) for i in range(0,len(vertices),2)],
                                      mode="line",thickness=1),color=color.rgba32(92,154,187,110),unlit=True)
