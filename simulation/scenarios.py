import numpy as np

from .body import Body
from .gravity import G_ASTRONOMICAL as G


def centered(bodies):
    mass = sum(b.mass for b in bodies)
    p = sum(b.mass * b.position for b in bodies) / mass
    v = sum(b.mass * b.velocity for b in bodies) / mass
    for b in bodies:
        b.position -= p
        b.velocity -= v
    return bodies


def star():
    return Body("Helios", 1, [0, 0, 0], [0, 0, 0], .24, (1, .66, .22), "Estrela", .00465)


def planet(name, radius, mass, size, tint, phase=0, inclination=0):
    speed = np.sqrt(G * (1 + mass) / radius)
    c, s = np.cos(phase), np.sin(phase)
    return Body(name, mass, [radius*c, radius*s*np.sin(inclination), radius*s*np.cos(inclination)],
                [-speed*s, speed*c*np.sin(inclination), speed*c*np.cos(inclination)], size, tint)


def solar():
    # Demonstrative architecture, not Solar System ephemerides.
    specs = [
        ("Mercúrio", .70, 1.66e-7, .047, (.65,.57,.48)),
        ("Vênus", 1.05, 2.45e-6, .074, (.95,.65,.33)),
        ("Terra", 1.55, 3.0e-6, .085, (.23,.64,.96)),
        ("Marte", 2.15, 3.2e-7, .061, (.90,.32,.20)),
        ("Júpiter", 3.4, 9.55e-4, .19, (.77,.61,.44)),
        ("Saturno", 4.9, 2.86e-4, .16, (.87,.77,.53)),
        ("Urano", 6.6, 4.37e-5, .12, (.36,.82,.84)),
        ("Netuno", 8.4, 5.15e-5, .115, (.29,.42,.96)),
    ]
    bodies = [star()] + [planet(*spec, phase=i*.78, inclination=(i%3-1)*.035)
                         for i, spec in enumerate(specs)]
    earth = bodies[3]
    # A stable illustrative moon inside Earth's Hill sphere (~0.0155 AU).
    offset = .009
    bodies.append(Body("Lua", 3.69e-8, earth.position + [offset,0,0],
                       earth.velocity + [0,0,np.sqrt(G * earth.mass / offset)], .026,
                       (.78,.82,.88), "Lua", .0000116))
    return centered(bodies)


def binary():
    return [Body("Aster A", .5, [-.6,0,0], [0,0,-np.sqrt(G/4.8)], .18, (1,.7,.3), "Estrela"),
            Body("Aster B", .5, [.6,0,0], [0,0,np.sqrt(G/4.8)], .15, (.4,.7,1), "Estrela")]


def orbit(factor=1):
    bodies = [star(), planet("Kepler", 1.6, 3e-6, .09, (.3,.8,.9))]
    bodies[1].velocity *= factor
    return centered(bodies)


def approach(merge=False):
    r = .11 if merge else .015
    return [Body("Viajante A", .02, [-1,0,0], [.2,0,0 if merge else .3], .13, (.3,.8,1), collision_radius=r),
            Body("Viajante B", .02, [1,0,0], [-.2,0,0 if merge else -.3], .13, (1,.5,.3), collision_radius=r)]


SCENARIOS = {
    "Sistema Genesis": solar,
    "Órbita circular": orbit,
    "Estrelas binárias": binary,
    "Encontro gravitacional": approach,
    "Velocidade insuficiente": lambda: orbit(.65),
    "Velocidade de escape": lambda: orbit(1.6),
    "Colisão e fusão": lambda: approach(True),
}
