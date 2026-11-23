import numpy as np

G_ASTRONOMICAL = 4 * np.pi ** 2


def pair_forces(positions, masses, g=G_ASTRONOMICAL, softening=1e-4):
    """F[i,j] acts on i due to j, with Plummer softening (AU)."""
    displacement = positions[None, :, :] - positions[:, None, :]
    distance2 = np.sum(displacement ** 2, axis=2) + softening ** 2
    np.fill_diagonal(distance2, np.inf)
    if np.any(distance2 == 0):
        raise ValueError("Corpos coincidentes exigem suavização positiva ou fusão.")
    return (g * masses[:, None] * masses[None, :] / distance2 ** 1.5)[..., None] * displacement


def accelerations(positions, masses, g=G_ASTRONOMICAL, softening=1e-4):
    return pair_forces(positions, masses, g, softening).sum(axis=1) / masses[:, None]


def energy(positions, velocities, masses, g, softening):
    kinetic = 0.5 * np.sum(masses[:, None] * velocities ** 2)
    i, j = np.triu_indices(len(masses), 1)
    r = np.sqrt(np.sum((positions[j] - positions[i]) ** 2, axis=1) + softening ** 2)
    return float(kinetic - np.sum(g * masses[i] * masses[j] / r))
