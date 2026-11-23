from .gravity import accelerations


def velocity_verlet(positions, velocities, masses, dt, g, softening):
    """Kick-drift-kick; both force evaluations use the complete N-body state."""
    a0 = accelerations(positions, masses, g, softening)
    next_positions = positions + velocities * dt + 0.5 * a0 * dt ** 2
    a1 = accelerations(next_positions, masses, g, softening)
    next_velocities = velocities + 0.5 * (a0 + a1) * dt
    return next_positions, next_velocities, a1
