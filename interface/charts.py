from pathlib import Path

import numpy as np
from ursina import Entity, Mesh, camera, color, destroy, window

from .theme import panel, label, button, SURFACE, MUTED, ACCENT, ACTIVE
from .chart_data import METRICS, series, axis_bounds

COLORS=((106,221,200),(130,166,242),(239,186,113))


def number(value):
    return "0" if value==0 else f"{value:.3g}"


class ScientificCharts:
    """A single readable plot inside the universe, sampled at 1 Hz."""
    def __init__(self,app):
        self.app=app
        self.root=None
        self.metric="Energia"
        self.plot=None
        self.sim=None

    @property
    def visible(self):
        return self.root is not None

    def open(self):
        if self.visible:
            self.close()
            return
        self.app.explorer.controls_enabled=False
        self.root=Entity(parent=camera.ui,z=-4,scale=min(1,window.aspect_ratio/(16/9)))
        Entity(parent=self.root,model="quad",scale=(4,2),color=color.rgba32(0,0,0,160),z=.3,collider="box")
        panel(self.root,size=(1.38,.82),z=.2)
        label("Telemetria",self.root,-.62,.35,1.3)
        self.subtitle=label("",self.root,-.62,.305,.69,MUTED)
        button("Fechar / Esc",self.root,.54,.35,.20,self.close)
        self.tabs={}
        for i,metric in enumerate(METRICS):
            self.tabs[metric]=button(metric,self.root,-.50+i*.25,.235,.23,lambda m=metric:self.set_metric(m))
        self.latest=label("",self.root,-.61,.16,1.25,ACCENT)
        self.unit=label("",self.root,-.61,.115,.63,MUTED)
        self.summary=label("",self.root,-.61,-.335,.66,MUTED)
        self.export_note=label("",self.root,-.61,-.373,.58,MUTED)
        button("Salvar PNG",self.root,.54,-.35,.20,self.export_png)

    def set_metric(self,metric):
        self.metric=metric
        self.update(self.app.sim,self.app.selected,self.app.source)

    def update(self,sim,body,source):
        if not self.visible:
            return
        self.sim,self.body,self.source=sim,body,source
        self.root.scale=min(1,window.aspect_ratio/(16/9))
        self.subtitle.text=("Sistema completo" if self.metric=="Energia" else body.name if body else "Nenhum corpo selecionado")+"  /  atualização ao vivo"
        for metric,tab in self.tabs.items():
            tab.color=ACTIVE if metric==self.metric else SURFACE
        if self.plot:
            destroy(self.plot)
        self.plot=Entity(parent=self.root)
        data,unit=series(sim,self.metric,body,source)
        self.unit.text=unit
        if not data or not any(len(y) for _,_,y in data):
            self.latest.text="—"
            label(unit,self.plot,-.45,-.08,.86,MUTED)
            self.summary.text="Feche a telemetria para selecionar um corpo na cena ou na lista."
            self.export_note.text=""
            return
        values=np.concatenate([y for _,_,y in data])
        ymin,ymax=axis_bounds(values,self.metric=="Energia")
        tmin=min(float(t[0]) for _,t,_ in data)
        tmax=max(float(t[-1]) for _,t,_ in data)
        if tmax==tmin:
            tmax=tmin+max(sim.settings.dt*10,.01)
        left,right,bottom,top=-.52,.60,-.235,.065
        for i in range(5):
            y=bottom+(top-bottom)*i/4
            self.line([(left,y),(right,y)],color.rgb32(35,47,61),1)
            label(number(ymin+(ymax-ymin)*i/4),self.plot,-.62,y+.008,.57,MUTED)
        for i in range(5):
            x=left+(right-left)*i/4
            label(number(tmin+(tmax-tmin)*i/4),self.plot,x-.01,bottom-.025,.57,MUTED)
        label("Tempo simulado / anos",self.plot,.33,bottom-.055,.57,MUTED)
        for i,(name,t,values_) in enumerate(data):
            points=[(left+(float(tx)-tmin)/(tmax-tmin)*(right-left),
                     bottom+(float(y)-ymin)/(ymax-ymin)*(top-bottom)) for tx,y in zip(t,values_)]
            self.line(points,color.rgb32(*COLORS[i]),2)
            if points:
                panel(self.plot,position=points[-1],size=(.006,.006),tint=color.rgb32(*COLORS[i]),z=-.02)
            label(name[:35],self.plot,left+i*.36,.095,.62,color.rgb32(*COLORS[i]))
        self.latest.text=(number(data[0][2][-1]) if len(data)==1 else "  /  ".join(f"{name} {number(y[-1])}" for name,_,y in data))
        if self.metric=="Energia" and unit.startswith("%"):
            drift=float(data[0][2][-1])
            self.latest.text="Variação abaixo de 0,001%" if abs(drift)<.001 else f"Variação {drift:+.3g}%"
        self.summary.text=f"{len(data[0][1])} amostras  ·  mínimo {number(float(np.min(values)))}  ·  máximo {number(float(np.max(values)))}"
        self.export_note.text=(f"Energia total {sim.total_energy:.6g} Msol AU²/ano²  ·  Fusões são inelásticas."
                               if self.metric=="Energia" else "Valores medidos pelo integrador, em unidades físicas.")
        if len(data[0][1])<2:
            self.summary.text="Aguardando evolução: execute a simulação ou avance alguns passos."

    def line(self,points,tint,thickness):
        if len(points)>1:
            Entity(parent=self.plot,model=Mesh(vertices=[(x,y,0) for x,y in points],mode="line",thickness=thickness),color=tint)

    def export_png(self,path=None):
        if self.sim is None:
            return
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        data,unit=series(self.sim,self.metric,self.body,self.source)
        fig=Figure(figsize=(10,5),facecolor="#0c131d",layout="constrained")
        FigureCanvasAgg(fig)
        ax=fig.add_subplot(facecolor="#0c131d")
        for i,(name,t,y) in enumerate(data):
            ax.plot(t,y,label=name,color=np.array(COLORS[i])/255,lw=2)
        ax.set_title(self.metric+" / PROJECT GENESIS",color="#e3ecf4",loc="left",pad=20)
        ax.set_xlabel("Tempo simulado (ano)",color="#8b9eb3")
        ax.set_ylabel(unit,color="#8b9eb3")
        ax.tick_params(colors="#8b9eb3")
        ax.ticklabel_format(axis="both",useOffset=False,scilimits=(-3,4))
        ax.grid(axis="y",color="#23303d",lw=.6)
        for spine in ax.spines.values():
            spine.set_visible(False)
        if data:
            lo,hi=axis_bounds(np.concatenate([y for _,_,y in data]),self.metric=="Energia")
            ax.set_ylim(lo,hi)
            ax.legend(facecolor="#141e2b",edgecolor="none",labelcolor="#e3ecf4")
        target=Path(path or f"exports/telemetria-{self.metric.lower()}.png")
        target.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(target,dpi=160)
        self.export_note.text="Salvo em "+str(target)

    def close(self):
        if self.root:
            destroy(self.root)
        self.root=None
        self.plot=None
        self.app.explorer.controls_enabled=self.app.modal is None
