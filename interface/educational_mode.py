import numpy as np


def fmt(v):
    return "(" + ", ".join(f"{x:.3g}" for x in v) + ")"


def explanation(sim, body, source, vector_name="Velocidade"):
    if body is None:
        return "Selecione um corpo na cena\nou na lista à esquerda."
    if vector_name=="Força individual":
        if source is None:
            return "É preciso outro corpo para\nmostrar a força de uma fonte."
        index=next(i for i,b in enumerate(sim.bodies) if b.uid==source.uid)
        value=sim.forces_on(body.uid)[index]
        unit="Msol AU/ano²"
        meaning=f"Atração exercida por uma fonte.\nFonte: {source.name[:28]}"
    else:
        value,unit,meaning={
            "Posição": (body.position,"AU","Localiza o corpo em relação\nà origem do sistema."),
            "Velocidade": (body.velocity,"AU/ano","Indica para onde e com que\nrapidez o corpo se move."),
            "Aceleração": (body.acceleration,"AU/ano²","Indica como a velocidade\nmuda ao longo do tempo."),
            "Resultante": (body.force,"Msol AU/ano²","É a soma das forças que\natuam sobre o corpo."),
        }[vector_name]
    return (f"{meaning}\n\nComponentes (X, Y, Z) · {unit}\n{fmt(value)}\n\n"
            f"Módulo: {np.linalg.norm(value):.3g} {unit}")
