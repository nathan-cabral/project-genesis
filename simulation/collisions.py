"""Swept contact geometry and immutable events, independent of graphics."""
from dataclasses import dataclass
import numpy as np


def contact_radius(a,b):
    # Stellar absorption follows the visible surface, by interaction policy.
    # All gravitational forces still use only physical positions and masses.
    def radius(body):
        return max(body.collision_radius,body.visual_radius) if body.kind=="Estrela" else body.collision_radius
    return radius(a)+radius(b)


def swept_contact(start,end,radius):
    """First contact fraction along a relative-motion segment, or None."""
    start=np.asarray(start,dtype=float)
    delta=np.asarray(end,dtype=float)-start
    c=float(start@start-radius**2)
    if c<=0:
        return 0.0
    a=float(delta@delta)
    b=float(start@delta)
    if a<1e-30 or b>=0:
        return None
    discriminant=b*b-a*c
    if discriminant<0:
        return None
    # Stable quadratic root for a nearly grazing initial surface.
    t=c/(-b+np.sqrt(discriminant))
    return float(t) if 0<=t<=1 else None


@dataclass(frozen=True)
class CollisionEvent:
    kind: str
    body_uids: tuple
    names: tuple
    survivor_uid: str
    position: tuple
    size: float
    tint: tuple
    time: float
    star_position: tuple | None = None
    star_radius: float = 0.0
