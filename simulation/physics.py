from collections import deque
from dataclasses import dataclass

import numpy as np

from .body import Body
from .gravity import G_ASTRONOMICAL, accelerations, energy, pair_forces
from .integrator import velocity_verlet


@dataclass
class Settings:
    g: float = G_ASTRONOMICAL
    dt: float = 0.0005
    softening: float = 0.0001
    collisions: bool = False
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
        if self.settings.collisions:
            self.merge_collisions()
        p, v, m = self.arrays()
        p, v, a = velocity_verlet(p, v, m, self.settings.dt,
                                   self.settings.g, self.settings.softening)
        if not all(np.all(np.isfinite(x)) for x in (p, v, a)):
            raise FloatingPointError("Estado não finito. Reduza o passo e reinicie o cenário.")
        for body, pos, vel, acc in zip(self.bodies, p, v, a):
            body.position, body.velocity, body.acceleration = pos, vel, acc
        self.time += self.settings.dt
        self.steps += 1
        if self.settings.collisions:
            self.merge_collisions()
        if self.steps % 10 == 0:
            self.record()

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

    def merge_collisions(self):
        # Repeat after a merge: the new volume can overlap another body.
        while True:
            pair = next(((i, j) for i, a in enumerate(self.bodies)
                         for j, b in enumerate(self.bodies) if j > i
                         and np.linalg.norm(a.position - b.position) <= a.collision_radius + b.collision_radius), None)
            if pair is None:
                return
            i, j = pair
            a, b = self.bodies[i], self.bodies[j]
            mass = a.mass + b.mass
            merged = Body(a.name + " + " + b.name, mass,
                          (a.mass * a.position + b.mass * b.position) / mass,
                          (a.mass * a.velocity + b.mass * b.velocity) / mass,
                          (a.visual_radius ** 3 + b.visual_radius ** 3) ** (1/3),
                          tuple((a.mass * np.array(a.color) + b.mass * np.array(b.color)) / mass),
                          "Estrela" if "Estrela" in (a.kind, b.kind) else a.kind,
                          (a.collision_radius ** 3 + b.collision_radius ** 3) ** (1/3), uid=a.uid)
            self.bodies[i] = merged
            del self.bodies[j]
            self.merge_count += 1
            self.refresh()
