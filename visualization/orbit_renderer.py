import numpy as np
from ursina import Entity, Mesh, color, destroy

from simulation.integrator import velocity_verlet


class OrbitRenderer:
    def __init__(self):
        self.entities = []
        self.visible = True
        self.prediction = None

    def redraw(self, sim):
        for e in self.entities:
            destroy(e)
        self.entities=[]
        if not self.visible:
            return
        for b in sim.bodies:
            points=sim.trails[b.uid]
            if len(points)>1:
                self.entities.append(Entity(model=Mesh(vertices=[tuple(p) for p in points],mode="line",thickness=1),
                                            color=color.rgba32(*(int(c*255) for c in b.color),150),unlit=True))

    def clear_prediction(self):
        if self.prediction is not None:
            destroy(self.prediction)
            self.prediction=None

    def predict(self, sim):
        self.clear_prediction()
        if len(sim.bodies) != 2:
            raise ValueError("Previsão disponível apenas para cenários com exatamente dois corpos.")
        p,v,m=sim.arrays()
        period=np.sqrt(np.linalg.norm(p[1]-p[0])**3/(m.sum()) * 4*np.pi**2/sim.settings.g)
        dt=min(sim.settings.dt,period/2500)
        paths=[[],[]]
        for i in range(2500):
            p,v,_=velocity_verlet(p,v,m,dt,sim.settings.g,sim.settings.softening)
            if i%5==0:
                for j in range(2):
                    paths[j].append(tuple(p[j]))
        segments=[]
        for path in paths:
            for a,b in zip(path[::2],path[1::2]):
                segments.extend((a,b))
        self.prediction=Entity(model=Mesh(vertices=segments,triangles=[(i,i+1) for i in range(0,len(segments),2)],mode="line",thickness=1),
                               color=color.rgba32(124,218,255,130),unlit=True)
