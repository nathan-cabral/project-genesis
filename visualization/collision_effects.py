"""Bounded, procedural collision VFX. Fragments carry no simulated mass."""
import numpy as np
from ursina import Entity, Mesh, color, destroy
from ursina.shaders import unlit_shader


class Burst:
    def __init__(self,event,quality):
        self.event=event
        self.age=0.0
        self.absorbing=event.kind=="absorption"
        self.lifetime=1.05 if self.absorbing else 1.8
        self.root=Entity(position=event.position)
        self.rng=np.random.default_rng()
        self.count=18 if quality=="Baixa" else 38
        self.size=max(.12,min(event.size,.55))
        directions=self.rng.normal(size=(self.count,3))
        directions/=np.linalg.norm(directions,axis=1)[:,None]
        self.velocities=directions*self.rng.uniform(.5,2.3,(self.count,1))*self.size*3
        self.offsets=self.rng.uniform(.015,.035,self.count)*self.size/.15
        self.offsets*=.22 if self.absorbing else .65
        self.seeds=directions*self.size*.12
        self.mesh=Mesh(vertices=[(0,0,0)]*(self.count*4),
                       triangles=[tuple(i*4+j for j in face) for i in range(self.count)
                                  for face in ((0,1,2),(0,3,1),(0,2,3),(1,3,2))],static=False)
        self.shards=Entity(parent=self.root,model=self.mesh,shader=unlit_shader,double_sided=True)
        self.flash=Entity(parent=self.root,model="sphere",scale=self.size*2,
                          color=color.rgba32(255,223,156,220),shader=unlit_shader)
        ring=[(np.cos(t),0,np.sin(t)) for t in np.linspace(0,2*np.pi,80)]
        self.wave=Entity(parent=self.root,model=Mesh(vertices=ring,mode="line",thickness=2),
                         color=color.rgba32(255,180,92,190),shader=unlit_shader)
        if self.absorbing:
            self.center=np.asarray(event.star_position)-np.asarray(event.position)
            self.seeds=self.rng.normal(size=(self.count,3))*self.size*.27
        self.update(0)

    def update(self,dt):
        self.age+=dt
        progress=min(1,self.age/self.lifetime)
        fade=(1-progress)**1.4
        if self.absorbing:
            centers=self.seeds*(1-progress)+self.center*progress
            swirl=np.column_stack((np.sin(progress*9+np.arange(self.count)),np.cos(progress*9+np.arange(self.count)),np.zeros(self.count)))
            centers+=swirl*self.size*.22*np.sin(progress*np.pi)
        else:
            centers=self.seeds+self.velocities*(1-np.exp(-self.age*1.5))/1.5
        tetra=np.array([[1,1,1],[-1,-1,1],[-1,1,-1],[1,-1,-1]],dtype=float)
        vertices=(centers[:,None,:]+tetra[None,:,:]*self.offsets[:,None,None]*(1-progress*.65)).reshape(-1,3)
        self.mesh.vertices=[tuple(p) for p in vertices]
        self.mesh.colors=[color.rgba32(255,int(160-90*progress),int(70-35*progress),int(255*fade)) for _ in vertices]
        self.mesh.generate()
        self.flash.scale=self.size*(3+progress*5)
        self.flash.color=color.rgba32(255,209,134,int(190*max(0,1-progress*4)))
        self.wave.scale=self.size*(1+progress*(2 if self.absorbing else 6))
        self.wave.color=color.rgba32(255,168,74,int(160*fade))
        return self.age<self.lifetime

    def close(self):
        destroy(self.root)


class CollisionEffects:
    MAX_BURSTS=12

    def __init__(self):
        self.bursts=[]

    def emit(self,event,quality="Alta"):
        while len(self.bursts)>=self.MAX_BURSTS:
            self.bursts.pop(0).close()
        self.bursts.append(Burst(event,quality))

    def update(self,dt):
        for burst in self.bursts[:]:
            if not burst.update(dt):
                burst.close()
                self.bursts.remove(burst)

    def clear(self):
        for burst in self.bursts:
            burst.close()
        self.bursts.clear()
