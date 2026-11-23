import time as clock
import numpy as np
from ursina import Entity, camera, color, destroy, window

from simulation.scenarios import SCENARIOS
from visualization.vector_renderer import VECTOR_COLORS
from .educational_mode import explanation
from .theme import panel, label, button, BG, SURFACE, INK, MUTED, ACCENT, ACTIVE


class HUD:
    def __init__(self,app):
        self.app=app
        self.root=Entity(parent=camera.ui)
        label("GENESIS",self.root,-.84,.46,1.3)
        label("Seu laboratório orbital",self.root,-.84,.415,.65,MUTED)
        self.status=label("",self.root,-.10,.451,.68,ACCENT)
        button("Telemetria  / G",self.root,.53,.44,.22,app.open_charts)
        button("Ajustes",self.root,.75,.44,.17,app.open_settings)
        self.left=Entity(parent=self.root,x=-.715)
        self.right=Entity(parent=self.root,x=.705)
        panel(self.left,size=(.275,.75))
        panel(self.right,size=(.30,.75))
        label("EXPLORAR",self.left,-.113,.34,.58,MUTED)
        self.tab="Corpos"
        self.tabs={name:button(name,self.left,-.065+i*.13,.286,.12,lambda n=name:self.show_tab(n))
                   for i,name in enumerate(("Corpos","Cenários"))}
        self.body_root=Entity(parent=self.left)
        self.scenarios=Entity(parent=self.left,enabled=False)
        label("Seu universo",self.body_root,-.11,.235,.85)
        self.body_page=0; self.body_buttons=[]; self.body_rows=[]
        self.rebuild_bodies()
        notes=("Dez corpos para explorar","Um experimento essencial","Órbitas em torno do baricentro","Uma passagem próxima",
               "Quando a órbita não se sustenta","Uma trajetória aberta","Encontro inelástico")
        for i,(name,note) in enumerate(zip(SCENARIOS,notes)):
            button(name,self.scenarios,0,.211-i*.067,.245,lambda n=name:app.load_scenario(n),height=.038,text_size=.67)
            label(note,self.scenarios,-.112,.185-i*.067,.51,MUTED)
        button("+ Adicionar corpo",self.left,0,-.325,.24,app.create_body,tint=ACTIVE,height=.043,text_size=.77)
        label("INSPECIONAR",self.right,-.125,.34,.58,MUTED)
        self.title=label("Visão geral",self.right,-.125,.295,1.05)
        self.subtitle=label("",self.right,-.125,.25,.62,MUTED)
        self.cards=[]
        for i in range(2):
            x=-.066+i*.135
            panel(self.right,position=(x,.167),size=(.124,.095),tint=SURFACE)
            value=label("",self.right,x-.05,.184,.83)
            caption=label("",self.right,x-.05,.145,.55,MUTED)
            self.cards.append((value,caption))
        self.info=label("",self.right,-.125,.097,.65,MUTED)
        self.selection_actions=Entity(parent=self.right)
        button("Focar",self.selection_actions,-.087,-.035,.08,app.focus,text_size=.63)
        button("Seguir",self.selection_actions,0,-.035,.08,app.follow,text_size=.63)
        button("Geral",self.selection_actions,.087,-.035,.08,app.explorer.overview,text_size=.63)
        button("Editar",self.selection_actions,-.067,-.079,.124,app.edit_body)
        button("Remover",self.selection_actions,.067,-.079,.124,app.remove_body)
        self.selection_hint=label("Clique em um planeta\nou escolha um corpo na lista.",self.right,-.125,-.028,.73)
        label("VETORES",self.right,-.125,-.146,.58,MUTED)
        self.component_button=button("XYZ",self.right,.09,-.146,.065,self.toggle_components,height=.025,text_size=.58)
        self.vector_buttons={}
        for i,(name,rgb) in enumerate(VECTOR_COLORS.items()):
            short={"Força individual":"Força fonte","Aceleração":"Aceleração"}.get(name,name)
            b=button(short,self.right,-.067+(i%2)*.134,-.192-(i//2)*.040,.125,
                     lambda n=name:self.toggle_vector(n),height=.032,text_size=.60)
            b.text_color=color.rgb32(*rgb)
            b.highlight_text_color=b.text_color
            self.vector_buttons[name]=b
        self.source_button=button("Fonte",self.right,.067,-.272,.125,app.cycle_source,height=.032,text_size=.57)
        button("Modo Professor  / P",self.right,0,-.331,.26,self.toggle_professor,tint=ACTIVE,height=.043)
        self.bottom=Entity(parent=self.root,y=-.435)
        panel(self.bottom,size=(1.69,.078))
        self.play_button=button("Pausar",self.bottom,-.745,0,.14,app.toggle_play,tint=ACTIVE,height=.04)
        button("Passo",self.bottom,-.60,0,.12,app.single_step)
        button("Reiniciar",self.bottom,-.463,0,.14,app.reset)
        button("−",self.bottom,-.35,0,.055,lambda:app.change_speed(-1))
        self.rate=label("",self.bottom,-.30,.011,.67)
        button("+",self.bottom,-.17,0,.055,lambda:app.change_speed(1))
        self.trails_button=button("Trilhas",self.bottom,-.06,0,.13,app.toggle_trails)
        self.field_button=button("Campo",self.bottom,.085,0,.13,app.toggle_field)
        button("Limpar",self.bottom,.23,0,.13,app.clear_trails)
        button("Prever",self.bottom,.37,0,.13,app.predict)
        self.clock=label("",self.bottom,.48,.016,.61,ACCENT)
        label("Arraste com botão direito para orbitar  ·  Roda para zoom  ·  Espaço para pausar",self.root,-.50,-.365,.58,MUTED)
        self.message=label("",self.root,-.49,.355,.61,MUTED)
        self.message.wordwrap=64
        self.professor=Entity(parent=self.root,x=.46,enabled=False,z=-2)
        panel(self.professor,size=(.78,.77),collider="box")
        label("Modo Professor",self.professor,-.35,.335,1.05)
        self.lesson=label("",self.professor,-.35,.28,.70)
        button("Alternar fonte",self.professor,-.21,-.335,.25,app.cycle_source)
        button("Fechar / P",self.professor,.245,.335,.20,self.toggle_professor)
        for i,(name,rgb) in enumerate(VECTOR_COLORS.items()):
            label(name,self.professor,-.35+(i%3)*.24,-.24-(i//3)*.027,.52,color.rgb32(*rgb))
        self.update()

    def show_tab(self,name):
        self.tab=name
        self.body_root.enabled=name=="Corpos"
        self.scenarios.enabled=name=="Cenários"
        for key,b in self.tabs.items():
            b.color=ACTIVE if key==name else SURFACE

    def rebuild_bodies(self):
        for e in self.body_buttons:
            destroy(e)
        self.body_buttons=[]; self.body_rows=[]
        bodies=self.app.sim.bodies
        pages=max(1,(len(bodies)+8)//9)
        self.body_page%=pages
        for i,b in enumerate(bodies[self.body_page*9:(self.body_page+1)*9]):
            row=button(b.name[:22],self.body_root,0,.187-i*.044,.245,lambda uid=b.uid:self.app.select(uid),height=.036)
            Entity(parent=row,model="quad",position=(-.435,0,-.02),scale=(.026,.32),color=color.rgb(*b.color))
            self.body_buttons.append(row)
            self.body_rows.append((b.uid,row))
        if not bodies:
            self.body_buttons.append(label("Seu universo está vazio.\nAdicione o primeiro corpo.",self.body_root,-.11,.17,.70,MUTED))
        self.body_buttons.append(button(f"Página {self.body_page+1} de {pages}  ›",self.body_root,0,-.255,.245,self.next_page,height=.029,text_size=.59))

    def next_page(self):
        self.body_page+=1
        self.rebuild_bodies()

    def toggle_vector(self,name):
        self.app.vectors.enabled[name]=not self.app.vectors.enabled[name]

    def toggle_components(self):
        self.app.vectors.components=not self.app.vectors.components

    def toggle_professor(self):
        self.professor.enabled=not self.professor.enabled
        self.right.enabled=not self.professor.enabled

    def update(self):
        app=self.app; sim=app.sim; b=app.selected; source=app.source
        self.root.scale=min(1,window.aspect_ratio/(16/9))
        self.show_tab(self.tab)
        self.status.text=("Em movimento" if app.playing else "Pausado")+f"  /  {len(sim.bodies)} corpos"
        self.selection_actions.enabled=b is not None
        self.selection_hint.enabled=b is None
        if b:
            self.title.text=b.name[:23]
            self.subtitle.text=b.kind+"  /  propriedades físicas"
            self.cards[0][0].text=f"{np.linalg.norm(b.velocity):.3g}"
            self.cards[0][1].text="Velocidade / AU/ano"
            self.cards[1][0].text=f"{np.linalg.norm(b.position):.3g}"
            self.cards[1][1].text="Distância origem / AU"
            self.info.text=(f"Massa   {b.mass:.3g} Msol\nAceleração   {np.linalg.norm(b.acceleration):.3g} AU/ano²\n"
                            f"Força   {np.linalg.norm(b.force):.3g} Msol AU/ano²")
        else:
            self.title.text="Seu sistema"
            self.subtitle.text=app.scenario_name
            self.cards[0][0].text=str(len(sim.bodies)); self.cards[0][1].text="Corpos celestes"
            self.cards[1][0].text=f"{sim.time:.2f}"; self.cards[1][1].text="Anos simulados"
            self.info.text=f"Energia   {sim.total_energy:.4g} Msol AU²/ano²\n|Momento|   {np.linalg.norm(sim.momentum):.2g} Msol AU/ano\nFusões   {sim.merge_count}"
        for uid,row in self.body_rows:
            row.color=ACTIVE if uid==app.selected_uid else BG
        for name,btn in self.vector_buttons.items():
            btn.color=ACTIVE if app.vectors.enabled[name] else SURFACE
        self.component_button.color=ACTIVE if app.vectors.components else SURFACE
        self.source_button.text=(source.name[:15] if source else "Escolher fonte")
        self.play_button.text="Pausar" if app.playing else "Executar"
        self.rate.text=f"{app.speed:g} ano/s"
        self.trails_button.color=ACTIVE if app.orbits.visible else SURFACE
        self.field_button.color=ACTIVE if app.field_visible else SURFACE
        self.clock.text=f"{sim.time:.3f} ano simulado\n{clock.perf_counter()-app.real_start:.0f}s de execução"
        if self.professor.enabled:
            self.lesson.text=explanation(sim,b,source)
