import numpy as np
from ursina import Entity, Mesh, color, destroy

VECTOR_COLORS = {"Posição": (106,166,255), "Velocidade": (75,230,190),
                 "Aceleração": (255,194,89), "Força individual": (245,120,190),
                 "Resultante": (184,149,255)}


class VectorRenderer:
    def __init__(self):
        self.enabled = {key: key == "Velocidade" for key in VECTOR_COLORS}
        self.components = False
        self.scale = 1.0
        self.entities = []

    def clear(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()

    def line(self, points, tint, thickness=2):
        self.entities.append(Entity(model=Mesh(vertices=[tuple(p) for p in points],mode="line",thickness=thickness),
                                    color=tint,unlit=True))

    def draw(self, sim, body, source):
        self.clear()
        if body is None:
            return
        individual = np.zeros(3) if source is None else sim.forces_on(body.uid)[next(i for i,b in enumerate(sim.bodies) if b.uid==source.uid)]
        values = {"Posição": body.position, "Velocidade": body.velocity,
                  "Aceleração": body.acceleration,"Força individual": individual,"Resultante": body.force}
        for label, value in values.items():
            norm = np.linalg.norm(value)
            if not self.enabled[label] or norm < 1e-18:
                continue
            start = np.zeros(3) if label == "Posição" else body.position.copy()
            # Position is literal; other vectors use a log display scale only.
            length = norm if label == "Posição" else self.scale * (.3 + .55*np.log1p(norm* (1000 if "Força" in label or label == "Resultante" else 1)))
            direction = value/norm
            end = start+direction*length
            tint = color.rgb32(*VECTOR_COLORS[label])
            self.line([start,end],tint)
            side = np.cross(direction,[0,1,0])
            if np.linalg.norm(side) < 1e-6:
                side = np.cross(direction,[1,0,0])
            side /= np.linalg.norm(side)
            head = min(.15,length*.2)
            self.line([end-direction*head+side*head*.45,end,end-direction*head-side*head*.45],tint)
            if self.components:
                p = start.copy()
                for axis, rgb in enumerate(((246,104,111),(112,219,152),(105,166,255))):
                    q=p.copy(); q[axis]=end[axis]
                    self.line([p,q],color.rgb32(*rgb),1)
                    p=q
