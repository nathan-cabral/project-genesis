"""Scientific series shared by the in-app plot and optional PNG export."""
import numpy as np

METRICS=("Energia","Velocidade","Aceleração","Distância","Posição")


def series(sim,metric,body=None,source=None):
    records=list(sim.history)
    if metric=="Energia":
        baseline=sim.reference_energy
        t=np.array([r["time"] for r in records])
        values=np.array([r["energy"] for r in records])
        if abs(baseline)<1e-25:
            return [("Energia",t,values)],"Msol AU²/ano²"
        return [("Variação",t,(values-baseline)/abs(baseline)*100)],"% da energia de referência"
    if body is None or metric=="Distância" and source is None:
        return [],"Selecione um corpo" if body is None else "Escolha uma fonte no painel do corpo"
    data=[r for r in records if body.uid in r["bodies"] and
          (metric!="Distância" or source.uid in r["bodies"])]
    t=np.array([r["time"] for r in data])
    if not data:
        return [],"Aguardando amostras"
    if metric=="Posição":
        return [(axis,t,np.array([r["bodies"][body.uid][0][i] for r in data])) for i,axis in enumerate("XYZ")],"AU"
    if metric=="Distância":
        values=[np.linalg.norm(r["bodies"][body.uid][0]-r["bodies"][source.uid][0]) for r in data]
        return [(body.name+" → "+source.name,t,np.array(values))],"AU"
    index=1 if metric=="Velocidade" else 2
    return [(body.name,t,np.array([np.linalg.norm(r["bodies"][body.uid][index]) for r in data]))],"AU/ano" if index==1 else "AU/ano²"


def axis_bounds(values,energy=False):
    low,high=float(np.min(values)),float(np.max(values))
    if energy:
        low=min(low,0); high=max(high,0)
    span=max(high-low,.002 if energy else max(abs(low),abs(high))*.06,1e-9)
    center=0 if energy and max(abs(low),abs(high))<.001 else (low+high)/2
    return center-span*.65,center+span*.65
