"""Geometry and physically meaningful defaults for interactive creation."""
import numpy as np


def ray_plane_intersection(origin, direction, height=0):
    origin=np.asarray(origin,dtype=float)
    direction=np.asarray(direction,dtype=float)
    if abs(direction[1])<1e-8:
        return None
    t=(height-origin[1])/direction[1]
    if t<=0:
        return None
    return origin+t*direction


def suggested_velocity(position, mass, bodies, g, softening=0, factor=1):
    if not bodies:
        return np.zeros(3)
    primary=max(bodies,key=lambda b:b.mass)
    delta=np.asarray(position)-primary.position
    radius=np.linalg.norm(delta)
    tangent=np.cross(delta,[0,1,0])
    if np.linalg.norm(tangent)<1e-9:
        tangent=np.cross(delta,[0,0,1])
    if radius<1e-8:
        raise ValueError("Escolha uma posição afastada do corpo central.")
    speed=np.sqrt(g*(primary.mass+mass)*radius**2/(radius**2+softening**2)**1.5)
    return primary.velocity+tangent/np.linalg.norm(tangent)*speed*factor
