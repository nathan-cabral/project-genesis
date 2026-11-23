import numpy as np


def fmt(v):
    return "(" + ", ".join(f"{x: .3g}" for x in v) + ")"


def explanation(sim, body, source):
    if body is None:
        return "Selecione um corpo na cena ou na lista."
    s=sim.settings
    lines=[f"CORPO: {body.name}",f"m = {body.mass:.5g} Msol", "",
           f"r = {fmt(body.position)} AU",f"|r| = {np.linalg.norm(body.position):.5g} AU",
           f"v = {fmt(body.velocity)} AU/ano",f"|v| = {np.linalg.norm(body.velocity):.5g}",
           f"a = {fmt(body.acceleration)} AU/ano²",f"|a| = {np.linalg.norm(body.acceleration):.5g}",
           f"F = {fmt(body.force)} Msol AU/ano²",f"|F| = {np.linalg.norm(body.force):.5g}", ""]
    if source is not None:
        d=source.position-body.position
        distance=np.linalg.norm(d)
        f=sim.forces_on(body.uid)[next(i for i,b in enumerate(sim.bodies) if b.uid==source.uid)]
        lines += [f"1. Fonte: {source.name} (m={source.mass:.4g})",f"2. d = r_fonte - r = {fmt(d)} AU",
                  f"3. |d| = {distance:.5g} AU; eps = {s.softening:.3g} AU", "4. F_ij = G m_i m_j d / (|d|²+eps²)^(3/2)",
                  f"G={s.g:.5g}; m_i m_j={body.mass*source.mass:.5g}",
                  f"F_ij = {fmt(f)} Msol AU/ano²", ""]
    lines += ["5. F_res = soma de TODAS as F_ij; a = F_res/m",
              "6. Velocity Verlet (kick-drift-kick):",f"h = {s.dt:.5g} ano",
              "r' = r + v h + a h²/2", "a' = gravidade nas novas posições", "v' = v + (a+a') h/2", "",
              "eps é suavização numérica, não física.","Raios visuais não entram nas forças.",
              "Setas v/a/F: escala logarítmica visual.","Posição: seta desde a origem inercial."]
    return "\n".join(lines)
