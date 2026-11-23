from dataclasses import replace

import numpy as np
from ursina import Entity, Button, Text, InputField, camera, color, destroy, window

from simulation.body import Body
from simulation.creation import suggested_velocity
from .theme import panel, label, button, SURFACE, MUTED, ACTIVE

BG=color.rgb32(13,22,36)
INK=color.rgb32(216,227,241)
ACCENT=color.rgb32(75,230,190)


class Form:
    def __init__(self, app, title, fields, submit):
        self.app=app
        self.was_playing=app.playing
        app.playing=False
        app.explorer.controls_enabled=False
        self.root=Entity(parent=camera.ui,z=-5)
        self.root.scale=min(1,window.aspect_ratio/(16/9))
        Entity(parent=self.root,model="quad",scale=(4,2),color=color.rgba32(0,0,0,195),z=.2,collider="box")
        panel(self.root,size=(.94,.78),z=.1)
        Text(title,parent=self.root,position=(-.39,.37),scale=1.15,color=INK)
        self.inputs={}
        for i,(key,label,value) in enumerate(fields):
            col,row=i%2,i//2
            x=-.38+col*.40; y=.275-row*.085
            Text(label,parent=self.root,position=(x,y+.026),scale=.63,color=color.rgb32(144,165,188))
            f=InputField(parent=self.root,default_value=str(value),position=(x+.175,y-.012),scale=(.35,.038),
                         color=color.rgb32(25,39,58),text_color=INK,character_limit=70)
            self.inputs[key]=f
            f.text_field.scale*=.7
        values=list(self.inputs.values())
        for a,b in zip(values,values[1:]):
            a.next_field=b
        self.error=Text(" ",parent=self.root,position=(-.38,-.30),scale=.68,color=color.rgb32(255,150,135),wordwrap=65)
        Button("Cancelar",parent=self.root,position=(-.21,-.365),scale=(.32,.045),color=color.rgb32(32,47,66),on_click=self.close)
        Button("Aplicar",parent=self.root,position=(.21,-.365),scale=(.32,.045),color=color.rgb32(29,100,88),on_click=lambda:self.save(submit))

    def save(self, submit):
        try:
            submit({key:f.text.strip() for key,f in self.inputs.items()})
        except (ValueError,OverflowError) as exc:
            self.error.text=str(exc)
            return
        self.close()

    def close(self):
        destroy(self.root)
        self.app.modal=None
        self.app.explorer.controls_enabled=True
        self.app.playing=self.was_playing


def triple(text):
    values=[float(x) for x in text.replace(";",",").split(",")]
    if len(values)!=3:
        raise ValueError("Use três valores separados por vírgulas: x, y, z.")
    return values


class BodyEditor:
    PRESETS={"Planeta":(3e-6,.09,.001),"Estrela":(1,.24,.00465),
             "Lua":(3.7e-8,.03,.000012),"Asteroide":(1e-10,.023,.000003)}
    PALETTE=((.28,.68,.96),(.40,.81,.67),(.95,.62,.35),(.74,.60,.95),(.92,.79,.53),(.77,.82,.88))

    def __init__(self,app,body=None):
        self.app=app; self.original=body
        self.body=body or Body(f"Planeta {len(app.sim.bodies)+1}",3e-6,[2.7,0,0],[0,0,0])
        self.was_playing=app.playing
        self.hud_visible=app.hud.root.enabled
        app.playing=False
        app.accumulator=0
        app.explorer.controls_enabled=False
        self.kind=self.body.kind
        self.motion="Manual" if body else "Orbitar"
        self.picking=False
        self.preview=None
        self.root=Entity(parent=camera.ui,z=-5)
        self.root.scale=min(1,window.aspect_ratio/(16/9))
        Entity(parent=self.root,model="quad",scale=(4,2),color=color.rgba32(0,0,0,175),z=.3,collider="box")
        panel(self.root,size=(1.04,.84),z=.2)
        label("Editar corpo" if body else "Um novo mundo",self.root,-.46,.36,1.25)
        label("Escolha o visual, encontre um lugar e explore.",self.root,-.46,.31,.68,MUTED)
        self.basic=Entity(parent=self.root)
        self.advanced=Entity(parent=self.root,enabled=False)
        self.inputs={}
        self.type_buttons={}
        for i,kind in enumerate(self.PRESETS):
            self.type_buttons[kind]=button(kind,self.basic,-.345+i*.23,.235,.215,lambda k=kind:self.set_kind(k))
        label("Nome",self.basic,-.45,.18,.68,MUTED)
        self.field("name",self.body.name,self.basic,-.15,.13,.60)
        label("Cor",self.basic,-.45,.082,.68,MUTED)
        self.swatches=[]
        for i,tint in enumerate(self.PALETTE):
            self.swatches.append(button(" ",self.basic,-.425+i*.061,.026,.043,
                                        lambda c=tint:self.set_color(c),color.rgb(*tint),height=.035))
        self.color_note=label("",self.basic,.04,.039,.65,MUTED)
        label("Onde colocar?",self.basic,-.45,-.026,.8)
        button("Escolher na cena",self.basic,.305,-.022,.29,self.begin_pick,tint=ACTIVE)
        for i,axis in enumerate("xyz"):
            x=-.45+i*.31
            label(axis.upper()+"  / AU",self.basic,x,-.084,.60,MUTED)
            self.field(axis,f"{self.body.position[i]:.7g}",self.basic,x+.14,-.129,.28)
        label("Movimento inicial",self.basic,-.45,-.18,.68,MUTED)
        self.motion_buttons={}
        for i,mode in enumerate(("Orbitar","Parado","Escape")):
            self.motion_buttons[mode]=button(mode,self.basic,-.30+i*.31,-.226,.29,lambda m=mode:self.set_motion(m))
        self.motion_note=label("",self.basic,-.45,-.266,.60,MUTED)
        fields=[("mass","Massa / Msol",self.body.mass),("radius","Tamanho visual",self.body.visual_radius),
                ("velocity","Velocidade XYZ / AU por ano",", ".join(f"{v:.8g}" for v in self.body.velocity)),
                ("collision","Raio de colisão / AU",self.body.collision_radius),
                ("color","Cor RGB / 0 a 1",", ".join(str(c) for c in self.body.color))]
        for i,(key,title,value) in enumerate(fields):
            x=-.45+(i%2)*.48; y=.205-(i//2)*.125
            label(title,self.advanced,x,y,.68,MUTED)
            self.field(key,value,self.advanced,x+.215,y-.048,.43)
        self.velocity_seed=self.inputs["velocity"].text
        label("Velocidade digitada substitui a sugestão de órbita.\nMassa e tamanho visual são independentes.",self.advanced,-.45,-.21,.67,MUTED)
        self.advanced_button=button("Avançado",self.root,-.365,-.355,.18,self.toggle_advanced)
        button("Cancelar",self.root,.09,-.355,.20,self.close)
        self.confirm=button("Salvar" if body else "Criar planeta",self.root,.345,-.355,.25,self.save,tint=ACTIVE)
        self.error=label(" ",self.root,-.45,-.303,.64,color.rgb32(255,157,139))
        self.error.wordwrap=78
        for keys in (("name","x","y","z"),("mass","radius","velocity","collision","color")):
            for a,b in zip(keys,keys[1:]):
                self.inputs[a].next_field=self.inputs[b]
        self.refresh_choices()

    def field(self,key,value,parent,x,y,width):
        f=InputField(parent=parent,default_value=str(value),position=(x,y),scale=(width,.042),
                     color=SURFACE,text_color=INK,character_limit=70)
        f.text_field.scale*=.64
        self.inputs[key]=f
        return f

    def refresh_choices(self):
        for kind,b in self.type_buttons.items():
            b.color=ACTIVE if kind==self.kind else SURFACE
        for mode,b in self.motion_buttons.items():
            b.color=ACTIVE if mode==self.motion else SURFACE
        self.confirm.text="Salvar alterações" if self.original else "Criar "+self.kind.lower()
        self.color_note.text="Paleta pronta ou RGB em Avançado"
        self.motion_note.text={"Orbitar":"Sugestão circular em torno do corpo mais massivo. Não garante estabilidade.",
                               "Escape":"Velocidade sugerida: 1,6 × circular. Interações podem alterar a trajetória.",
                               "Parado":"Velocidade inicial zero no referencial do sistema.",
                               "Manual":"Velocidade personalizada. Ajuste em Avançado."}[self.motion]

    def set_kind(self,kind):
        self.kind=kind
        mass,radius,collision=self.PRESETS[kind]
        for key,value in (("mass",mass),("radius",radius),("collision",collision)):
            self.inputs[key].text=str(value)
        if not self.original:
            self.inputs["name"].text=f"{kind} {len(self.app.sim.bodies)+1}"
        self.refresh_choices()

    def set_color(self,tint):
        self.inputs["color"].text=", ".join(str(c) for c in tint)
        for c,b in zip(self.PALETTE,self.swatches):
            b.scale_y=.044 if c==tint else .035

    def position(self):
        p=np.array([float(self.inputs[a].text) for a in "xyz"])
        if not np.all(np.isfinite(p)):
            raise ValueError("Informe coordenadas finitas.")
        return p

    def set_motion(self,mode):
        self.motion=mode
        self.velocity_seed=self.inputs["velocity"].text
        self.refresh_choices()

    def toggle_advanced(self):
        if not self.advanced.enabled and self.motion!="Manual" and self.inputs["velocity"].text==self.velocity_seed:
            try:
                if self.motion=="Parado":
                    velocity=np.zeros(3)
                else:
                    s=self.app.sim.settings
                    velocity=suggested_velocity(self.position(),float(self.inputs["mass"].text),
                        [b for b in self.app.sim.bodies if b.uid!=self.body.uid],s.g,s.softening,1.6 if self.motion=="Escape" else 1)
                self.inputs["velocity"].text=", ".join(f"{v:.8g}" for v in velocity)
                self.velocity_seed=self.inputs["velocity"].text
            except ValueError:
                self.error.text="Revise a posição e a massa para calcular uma sugestão de velocidade."
        self.advanced.enabled=not self.advanced.enabled
        self.basic.enabled=not self.advanced.enabled
        self.advanced_button.text="Voltar" if self.advanced.enabled else "Avançado"
        # Do not leave a hidden text field focused.
        for f in self.inputs.values():
            f.active=False

    def begin_pick(self):
        from visualization.placement import PlacementPreview
        try:
            height=float(self.inputs["y"].text)
            if not np.isfinite(height):
                raise ValueError("Altura inválida")
        except ValueError:
            self.error.text="Informe uma altura Y válida para escolher o plano na cena."
            return
        for f in self.inputs.values():
            f.active=False
        self.picking=True
        self.root.enabled=False
        self.app.hud.root.enabled=False
        self.app.explorer.controls_enabled=True
        self.preview=PlacementPreview(height)
        self.pick_ui=Entity(parent=camera.ui,z=-6,scale=min(1,window.aspect_ratio/(16/9)))
        panel(self.pick_ui,position=(0,-.38),size=(1.15,.14),collider="box")
        label("Clique no universo para posicionar",self.pick_ui,-.53,-.33,.88)
        self.pick_hint=label(f"Plano XZ  /  altura Y = {height:g} AU  /  botão direito para orbitar",self.pick_ui,-.53,-.37,.66,MUTED)
        button("Voltar / Esc",self.pick_ui,.43,-.405,.20,self.cancel_pick)

    def update(self):
        self.root.scale=min(1,window.aspect_ratio/(16/9))
        if self.picking:
            self.pick_ui.scale=self.root.scale
            self.preview.update()
            p=self.preview.position
            self.pick_hint.text=(f"X {p[0]:.2f}   Y {p[1]:.2f}   Z {p[2]:.2f} AU  ·  plano XZ"
                                 if p is not None else "Gire a câmera para olhar o plano orbital.")

    def finish_pick(self,position):
        # Preview never commits a body: confirmation remains in the editor.
        for axis,value in zip("xyz",position):
            self.inputs[axis].text=f"{value:.8g}"
        self.cancel_pick()

    def cancel_pick(self):
        if not self.picking:
            return
        self.preview.close()
        destroy(self.pick_ui)
        self.preview=None
        self.picking=False
        self.root.enabled=True
        self.app.hud.root.enabled=self.hud_visible
        self.app.explorer.controls_enabled=False

    def input(self,key):
        from ursina import mouse
        if not self.picking:
            if key=="escape":
                self.close()
            return
        if key=="escape":
            self.cancel_pick()
        elif key=="left mouse down":
            if mouse.hovered_entity and mouse.hovered_entity.has_ancestor(camera.ui):
                return
            self.preview.update()
            if self.preview.position is not None:
                self.finish_pick(self.preview.position)

    def save(self):
        try:
            p=self.position(); mass=float(self.inputs["mass"].text)
            manual=self.motion=="Manual" or self.inputs["velocity"].text!=self.velocity_seed
            sources=[b for b in self.app.sim.bodies if b.uid!=self.body.uid]
            if manual:
                velocity=triple(self.inputs["velocity"].text)
            elif self.motion=="Parado":
                velocity=np.zeros(3)
            else:
                s=self.app.sim.settings
                velocity=suggested_velocity(p,mass,sources,s.g,s.softening,1.6 if self.motion=="Escape" else 1)
            fresh=Body(self.inputs["name"].text,mass,p,velocity,float(self.inputs["radius"].text),
                       tuple(triple(self.inputs["color"].text)),self.kind,float(self.inputs["collision"].text),uid=self.body.uid)
            if self.original:
                candidate=[fresh if b.uid==fresh.uid else b for b in self.app.sim.bodies]
                self.app.sim.validate_bodies(candidate)
                self.app.sim.bodies=candidate
                self.app.sim.rebaseline()
            else:
                self.app.sim.add(fresh)
        except (ValueError,OverflowError) as exc:
            message=str(exc)
            if "could not convert" in message:
                message="Revise os números. Use ponto decimal e vírgulas entre as componentes."
            for key,title in (("mass","Massa"),("visual_radius","Tamanho visual"),("collision_radius","Raio de colisão")):
                message=message.replace(key,title)
            self.error.text=message
            return
        self.app.selected_uid=fresh.uid
        if not self.app.source:
            self.app.cycle_source()
        self.app.orbits.clear_prediction()
        self.app.hud.rebuild_bodies()
        self.close()

    def close(self):
        if self.picking:
            self.cancel_pick()
        destroy(self.root)
        self.app.modal=None
        self.app.hud.root.enabled=self.hud_visible
        self.app.explorer.controls_enabled=True
        self.app.playing=self.was_playing
        self.app.accumulator=0


def body_form(app,body=None):
    return BodyEditor(app,body)


def settings_form(app):
    s=app.sim.settings
    fields=[("g","G (AU³ / Msol ano²)",s.g),("dt","PASSO FIXO (ano)",s.dt),
            ("eps","SUAVIZAÇÃO NUMÉRICA (AU)",s.softening),("trails","HISTÓRICO (10 a 5000 pontos)",s.trail_length),
            ("limit","LIMITE DE CORPOS (2 a 512)",s.max_bodies),("vectors","ESCALA VISUAL DAS SETAS",app.vectors.scale),
            ("quality","QUALIDADE: Alta / Baixa",app.planets.quality),("collisions","FUSÃO EXPERIMENTAL: sim / não","sim" if s.collisions else "não")]
    def submit(data):
        new=replace(s,g=float(data["g"]),dt=float(data["dt"]),softening=float(data["eps"]),
                    trail_length=int(data["trails"]),max_bodies=int(data["limit"]))
        new.validate()
        if new.max_bodies<len(app.sim.bodies):
            raise ValueError("Limite menor que a quantidade atual de corpos.")
        scale=float(data["vectors"])
        if not np.isfinite(scale) or not .01<=scale<=20:
            raise ValueError("Escala das setas: 0.01 a 20.")
        if data["quality"] not in ("Alta","Baixa") or data["collisions"].lower() not in ("sim","não","nao"):
            raise ValueError("Qualidade: Alta/Baixa; fusão: sim/não.")
        new.collisions=data["collisions"].lower()=="sim"
        app.sim.validate_bodies(app.sim.bodies,new)
        app.sim.settings=new
        app.sim.rebaseline()
        app.vectors.scale=scale
        app.planets.quality=data["quality"]
        app.orbits.clear_prediction()
        app.accumulator=0
    return Form(app,"PARÂMETROS DO LABORATÓRIO",fields,submit)
