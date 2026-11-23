from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np


def vector(value):
    result = np.array(value, dtype=np.float64, copy=True)
    if result.shape != (3,) or not np.all(np.isfinite(result)):
        raise ValueError("Um vetor deve ter três componentes finitas.")
    return result


@dataclass
class Body:
    name: str
    mass: float
    position: np.ndarray
    velocity: np.ndarray
    visual_radius: float = 0.09
    color: tuple = (0.3, 0.65, 1.0)
    kind: str = "Planeta"
    collision_radius: float = 0.001
    uid: str = field(default_factory=lambda: uuid4().hex)
    acceleration: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self):
        self.name = str(self.name).strip()
        if not self.name:
            raise ValueError("Informe um nome.")
        for label in ("mass", "visual_radius", "collision_radius"):
            value = float(getattr(self, label))
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{label} deve ser positivo e finito.")
            setattr(self, label, value)
        self.position = vector(self.position)
        self.velocity = vector(self.velocity)
        self.acceleration = vector(self.acceleration)
        self.color = tuple(float(c) for c in self.color)
        if len(self.color) != 3 or not all(np.isfinite(c) and 0 <= c <= 1 for c in self.color):
            raise ValueError("Cor RGB deve estar entre 0 e 1.")

    @property
    def force(self):
        return self.mass * self.acceleration
