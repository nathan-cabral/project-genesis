import numpy as np
from PIL import Image
from ursina import Entity, Texture, color, destroy, Mesh
from ursina.shaders import lit_with_shadows_shader
from ursina.shaders import unlit_shader


def surface(body, quality):
    """Deterministic texture: all artwork is generated locally."""
    width, height = (256, 128) if quality == "Alta" else (128, 64)
    y, x = np.mgrid[0:height, 0:width]
    lon, lat = x / width * 2*np.pi, y / height * np.pi
    base = np.array(body.color)
    bands = .78 + .16*np.sin(lat*25 + np.sin(lon*3)*.4)
    if body.name in ("Terra", "Kepler"):
        terrain = np.sin(lon*3+np.sin(lat*5))*np.cos(lat*4) + .4*np.sin(lon*7-lat*6)
        rgb = np.where((terrain > .3)[...,None], np.array([.22,.49,.36]), base)
        clouds = np.maximum(0, np.sin(lon*9 + lat*13 + np.sin(lat*7)) - .65)*.65
        rgb = rgb*bands[...,None] + clouds[...,None]
    elif body.kind=="Estrela":
        heat=.86+.08*np.sin(lon*19+np.sin(lat*23))+.06*np.cos(lon*41-lat*37)
        rgb=base*heat[...,None]
    elif body.name in ("Júpiter","Saturno","Urano","Netuno"):
        grain = np.random.default_rng(42).uniform(-.035,.035,(height,width))
        rgb = base*(bands+grain)[...,None]
    else:
        terrain=.8+.10*np.sin(lon*11+np.cos(lat*9))+.07*np.cos(lat*17-lon*7)
        grain=np.random.default_rng(24).uniform(-.05,.05,(height,width))
        rgb=base*(terrain+grain)[...,None]
    polar = np.maximum(0, np.abs(np.cos(lat))-.94)*5
    if body.kind != "Estrela":
        rgb = rgb*(1-polar[...,None]) + polar[...,None]*.88
    pixels = np.uint8(np.clip(rgb,0,1)*255)
    return Texture(Image.fromarray(pixels),filtering="bilinear")


class PlanetRenderer:
    def __init__(self):
        self.entities = {}
        self.signatures = {}
        self.quality = "Alta"

    def sync(self, bodies, on_select):
        active = {b.uid for b in bodies}
        for uid in list(self.entities):
            if uid not in active:
                destroy(self.entities.pop(uid))
                self.signatures.pop(uid)
        for body in bodies:
            signature = (body.name,body.color,body.visual_radius,body.kind,self.quality)
            if self.signatures.get(body.uid) != signature:
                if body.uid in self.entities:
                    destroy(self.entities[body.uid])
                e = Entity(model="sphere", texture=surface(body,self.quality),
                           scale=body.visual_radius*2, collider="sphere",
                           shader=unlit_shader if body.kind == "Estrela" else lit_with_shadows_shader)
                e.on_click = lambda uid=body.uid: on_select(uid)
                e.body_uid = body.uid
                if body.kind == "Estrela":
                    for mult, alpha in ((1.18,.12),(1.4,.045)):
                        Entity(parent=e,model="sphere",scale=mult,
                               color=color.rgba32(255,173,65,int(alpha*255)), unlit=True,
                               double_sided=True)
                if body.name == "Saturno":
                    points=[]
                    for radius in (.67,.70,.73,.76,.79,.82,.85):
                        ring=[(radius*np.cos(t),0,radius*np.sin(t)) for t in np.linspace(0,2*np.pi,100)]
                        points.extend(zip(ring[:-1],ring[1:]))
                    Entity(parent=e,model=Mesh(vertices=[p for pair in points for p in pair],
                                             triangles=[(i,i+1) for i in range(0,len(points)*2,2)],mode="line",thickness=2),
                           color=color.rgba32(206,185,139,140),rotation_x=22)
                self.entities[body.uid] = e
                self.signatures[body.uid] = signature
            self.entities[body.uid].position = tuple(body.position)

