from collections import deque
from dataclasses import dataclass

import numpy as np

from .body import Body
from .gravity import G_ASTRONOMICAL, accelerations, energy, pair_forces
from .integrator import velocity_verlet
from .collisions import CollisionEvent


@dataclass
class Settings:
    g: float = G_ASTRONOMICAL
    dt: float = 0.0005
    softening: float = 0.0001
    collisions: bool = True
    max_bodies: int = 128
    trail_length: int = 900

    def validate(self):
        if not np.isfinite(self.g) or self.g <= 0:
            raise ValueError("G deve ser positivo e finito.")
        if not np.isfinite(self.dt) or not 1e-6 <= self.dt <= 0.02:
            raise ValueError("Passo deve estar entre 0.000001 e 0.02 ano.")
        if not np.isfinite(self.softening) or self.softening < 0:
            raise ValueError("Suavização deve ser finita e não negativa.")
        if not 2 <= self.max_bodies <= 512 or not 10 <= self.trail_length <= 5000:
            raise ValueError("Limite: 2–512 corpos; histórico: 10–5000 pontos.")


class Simulation:
    def __init__(self, bodies=(), settings=None):
        self.settings = settings or Settings()
        self.settings.validate()
        self.bodies = list(bodies)
        self.time = 0.0
        self.trails = {}
        self.history = deque(maxlen=4000)
        self.revision = 0
        self.steps = 0
        self.merge_count = 0
        self.collision_events = deque(maxlen=256)
        self.refresh()
        self.reference_energy = self.total_energy
        self.record()

    def arrays(self):
        return (np.array([b.position for b in self.bodies]).reshape(-1, 3),
                np.array([b.velocity for b in self.bodies]).reshape(-1, 3),
                np.array([b.mass for b in self.bodies]))

    def refresh(self):
        self.settings.validate()
        if len(self.bodies) > self.settings.max_bodies:
            raise ValueError("Limite de corpos excedido.")
        p, _, m = self.arrays()
        if len(m):
            for b, a in zip(self.bodies, accelerations(p, m, self.settings.g, self.settings.softening)):
                b.acceleration = a
        for b in self.bodies:
            old = self.trails.get(b.uid, ())
            self.trails[b.uid] = deque(old, maxlen=self.settings.trail_length)
        self.trails = {b.uid: self.trails[b.uid] for b in self.bodies}
        self.revision += 1

    @property
    def total_energy(self):
        p, v, m = self.arrays()
        return energy(p, v, m, self.settings.g, self.settings.softening)

    @property
    def momentum(self):
        _, v, m = self.arrays()
        return np.sum(v * m[:, None], axis=0)

    def step(self):
        if not self.bodies:
            return
        self.merge_collisions(force_planets=False)
        remaining=self.settings.dt
        while remaining>0:
            p,v,m=self.arrays()
            # Search before evaluating forces at the destination: a fast body
            # may cross a star and leave it again within a single fixed step.
            a0=accelerations(p,m,self.settings.g,self.settings.softening)
            destination=p+v*remaining+.5*a0*remaining**2
            hit=self.first_contact(p,destination)
            duration=remaining if hit is None else remaining*hit[0]
            if duration>0:
                next_p,next_v,next_a=velocity_verlet(p,v,m,duration,self.settings.g,self.settings.softening)
                self.set_state(next_p,next_v,next_a)
            remaining=max(0,remaining-duration)
            if hit is None:
                break
            self.merge_pair(hit[1],hit[2],self.time+self.settings.dt-remaining)
            # Each contact reduces N, so even zero-time contact chains finish.
        self.time += self.settings.dt
        self.steps += 1
        self.merge_collisions(force_planets=False)
        if self.steps % 10 == 0:
            self.record()

    def set_state(self,p,v,a):
        if not all(np.all(np.isfinite(x)) for x in (p,v,a)):
            raise FloatingPointError("Estado não finito. Reduza o passo e reinicie o cenário.")
        for body,pos,vel,acc in zip(self.bodies,p,v,a):
            body.position,body.velocity,body.acceleration=pos,vel,acc

    def first_contact(self,start,end,force_planets=False):
        i,j=np.triu_indices(len(self.bodies),1)
        if not len(i):
            return None
        stars=np.array([b.kind=="Estrela" for b in self.bodies])
        radii=np.array([max(b.visual_radius,b.collision_radius) if star else b.collision_radius
                        for b,star in zip(self.bodies,stars)])
        allowed=np.ones(len(i),dtype=bool) if force_planets or self.settings.collisions else stars[i]|stars[j]
        relative=start[j]-start[i]
        delta=(end[j]-end[i])-relative
        a=np.sum(delta*delta,axis=1)
        b=np.sum(relative*delta,axis=1)
        c=np.sum(relative*relative,axis=1)-(radii[i]+radii[j])**2
        disc=b*b-a*c
        t=np.full(len(i),np.inf)
        t[allowed & (c<=0)]=0
        moving=allowed & (c>0) & (a>1e-30) & (b<0) & (disc>=0)
        t[moving]=c[moving]/(-b[moving]+np.sqrt(disc[moving]))
        t[(t<0)|(t>1)]=np.inf
        index=int(np.argmin(t))
        return (float(t[index]),int(i[index]),int(j[index])) if np.isfinite(t[index]) else None

    def record(self):
        for b in self.bodies:
            self.trails[b.uid].append(b.position.copy())
        self.history.append({"time": self.time, "energy": self.total_energy,
                             "bodies": {b.uid: (b.position.copy(), b.velocity.copy(), b.acceleration.copy())
                                        for b in self.bodies}})

    def rebaseline(self):
        """User interventions start a new diagnostic interval."""
        self.refresh()
        self.reference_energy = self.total_energy
        self.history.clear()
        self.clear_trails()
        self.record()

    def clear_trails(self):
        for trail in self.trails.values():
            trail.clear()

    def add(self, body):
        if len(self.bodies) >= self.settings.max_bodies:
            raise ValueError("Limite de corpos atingido.")
        self.validate_bodies(self.bodies+[body])
        self.bodies.append(body)
        self.rebaseline()

    def validate_bodies(self, bodies, settings=None):
        s=settings or self.settings
        s.validate()
        if len({b.uid for b in bodies})!=len(bodies):
            raise ValueError("Identificadores de corpos devem ser únicos.")
        p=np.array([b.position for b in bodies]).reshape(-1,3)
        m=np.array([b.mass for b in bodies])
        if len(m):
            accelerations(p,m,s.g,s.softening)

    def remove(self, uid):
        self.bodies = [b for b in self.bodies if b.uid != uid]
        self.rebaseline()

    def forces_on(self, uid):
        p, _, m = self.arrays()
        idx = next(i for i, b in enumerate(self.bodies) if b.uid == uid)
        return pair_forces(p, m, self.settings.g, self.settings.softening)[idx]

    def merge_collisions(self,force_planets=True):
        # Repeat after a merge: the new volume can overlap another body.
        while True:
            p,_,_=self.arrays()
            hit=self.first_contact(p,p,force_planets)
            if hit is None:
                return
            self.merge_pair(hit[1],hit[2],event_time=self.time)

    def merge_pair(self,i,j,event_time):
        a,b=self.bodies[i],self.bodies[j]
        stars=[body for body in (a,b) if body.kind=="Estrela"]
        star=max(stars,key=lambda body:body.mass) if stars else None
        survivor=star or a
        mass=a.mass+b.mass
        position=(a.mass*a.position+b.mass*b.position)/mass
        if star:
            other=b if star.uid==a.uid else a
            direction=other.position-star.position
            distance=np.linalg.norm(direction)
            direction=direction/distance if distance>1e-12 else np.array([1.,0,0])
            effect_position=star.position+direction*star.visual_radius
        else:
            effect_position=position
        merged = Body(star.name if star else a.name + " + " + b.name, mass,position,
                      (a.mass * a.velocity + b.mass * b.velocity) / mass,
                      (a.visual_radius ** 3 + b.visual_radius ** 3) ** (1/3),
                      star.color if star else tuple((a.mass * np.array(a.color) + b.mass * np.array(b.color)) / mass),
                      "Estrela" if star else a.kind,
                      (a.collision_radius ** 3 + b.collision_radius ** 3) ** (1/3), uid=survivor.uid)
        self.collision_events.append(CollisionEvent(
            "absorption" if star else "impact",(a.uid,b.uid),(a.name,b.name),survivor.uid,
            tuple(effect_position),other.visual_radius if star else max(a.visual_radius,b.visual_radius),survivor.color,event_time,
            tuple(position) if star else None,star.visual_radius if star else 0))
        self.bodies[i]=merged
        del self.bodies[j]
        self.merge_count+=1
        self.refresh()
