import time as clock

import numpy as np
from ursina import (Ursina, Entity, Text, Mesh, AmbientLight, PointLight, Vec3,
                    application, camera, color, destroy, time, window, invoke)

from simulation.physics import Simulation
from simulation.scenarios import SCENARIOS
from interface.hud import HUD
from interface.body_editor import body_form, settings_form
from .camera import ExplorerCamera
from .planet_renderer import PlanetRenderer
from .orbit_renderer import OrbitRenderer
from .vector_renderer import VectorRenderer
from .field_renderer import FieldRenderer
from .collision_effects import CollisionEffects


class Genesis(Entity):
    SPEEDS=(.01,.03,.075,.15,.3,.75,1.5,3.0)

    def __init__(self):
        super().__init__()
        self.sim=Simulation(SCENARIOS["Sistema Genesis"]())
        self.scenario_name="Sistema Genesis"
        self.selected_uid=None
        self.source_uid=None
        self.playing=True
        self.speed_index=3
        self.accumulator=0.0
        self.visual_clock=0
        self.real_start=clock.perf_counter()
        self.modal=None
        self.last_revision=self.sim.revision
        self.planets=PlanetRenderer()
        self.effects=CollisionEffects()
        self.orbits=OrbitRenderer()
        self.vectors=VectorRenderer()
        self.field=FieldRenderer()
        self.field_visible=False
        self.field_clock=0
        self.explorer=ExplorerCamera()
        self.guides=[]
        self.make_space()
        self.hud=HUD(self)
        self.planets.sync(self.sim.bodies,self.select)
        self.splash=Entity(parent=camera.ui,z=-10)
        Entity(parent=self.splash,model="quad",scale=(4,2),color=color.rgb32(5,10,20),z=.1)
        Text("PROJECT  GENESIS",parent=self.splash,origin=(0,0),y=.03,scale=2,color=color.rgb32(221,239,255))
        Text("UM UNIVERSO GOVERNADO POR VETORES",parent=self.splash,origin=(0,0),y=-.065,scale=.65,color=color.rgb32(75,230,190))
        invoke(self.end_splash,delay=1.4)

    @property
    def speed(self):
        return self.SPEEDS[self.speed_index]

    @property
    def selected(self):
        return next((b for b in self.sim.bodies if b.uid==self.selected_uid),None)

    @property
    def source(self):
        return next((b for b in self.sim.bodies if b.uid==self.source_uid and b.uid!=self.selected_uid),None)

    def end_splash(self):
        for child in self.splash.children:
            child.fade_out(duration=.6)
        destroy(self.splash,delay=.65)

    def make_space(self):
        rng=np.random.default_rng(7)
        points=rng.normal(size=(1600,3)); points/=np.linalg.norm(points,axis=1)[:,None]; points*=180
        Entity(model=Mesh(vertices=[tuple(p) for p in points],mode="point",thickness=1.4,static=True),
               color=color.rgb32(165,186,218),unlit=True)
        AmbientLight(color=color.rgb32(88,101,126))
        self.sunlight=PointLight(color=color.rgb32(255,230,195))
        self.selection_ring=Entity(model=Mesh(vertices=[(np.cos(t),0,np.sin(t)) for t in np.linspace(0,2*np.pi,80)],
                                              mode="line",thickness=2),color=color.rgb32(75,230,190),enabled=False)
        self.make_guides()

    def make_guides(self):
        for e in self.guides:
            destroy(e)
        self.guides=[]
        if self.scenario_name=="Sistema Genesis":
            for radius in (.70,1.05,1.55,2.15,3.4,4.9,6.6,8.4):
                points=[(radius*np.cos(t),0,radius*np.sin(t)) for t in np.linspace(0,2*np.pi,180)]
                self.guides.append(Entity(model=Mesh(vertices=points,mode="line",thickness=1),color=color.rgba32(90,128,165,40)))

    def notify(self,text):
        self.hud.message.text=text

    def select(self,uid):
        if self.modal:
            return
        self.selected_uid=uid
        if not self.source:
            self.cycle_source()

    def cycle_source(self):
        options=[b for b in self.sim.bodies if b.uid!=self.selected_uid]
        if not options:
            self.source_uid=None
            return
        index=next((i for i,b in enumerate(options) if b.uid==self.source_uid),-1)
        self.source_uid=options[(index+1)%len(options)].uid

    def load_scenario(self,name):
        if self.modal:
            return
        self.scenario_name=name
        self.sim=Simulation(SCENARIOS[name]())
        self.effects.clear()
        self.accumulator=0
        self.selected_uid=None; self.source_uid=None
        self.explorer.overview()
        self.orbits.clear_prediction()
        self.make_guides()
        self.hud.rebuild_bodies()
        self.notify("Cenário carregado: "+name)

    def reset(self):
        self.load_scenario(self.scenario_name)

    def toggle_play(self):
        self.playing=not self.playing

    def change_speed(self,delta):
        self.speed_index=max(0,min(len(self.SPEEDS)-1,self.speed_index+delta))

    def focus(self):
        if self.selected:
            self.explorer.focus(self.selected)

    def follow(self):
        if self.selected:
            self.explorer.focus(self.selected,True)

    def create_body(self):
        if not self.modal:
            self.modal=body_form(self)

    def edit_body(self):
        if self.selected and not self.modal:
            self.modal=body_form(self,self.selected)

    def open_settings(self):
        if not self.modal:
            self.modal=settings_form(self)

    def remove_body(self):
        if self.selected:
            self.sim.remove(self.selected_uid)
            self.selected_uid=None
            self.orbits.clear_prediction()
            self.hud.rebuild_bodies()

    def toggle_trails(self):
        self.orbits.visible=not self.orbits.visible
        for e in self.guides:
            e.enabled=self.orbits.visible

    def toggle_field(self):
        self.field_visible=not self.field_visible
        self.field.draw(self.sim,self.field_visible)

    def clear_trails(self):
        self.sim.clear_trails()

    def predict(self):
        try:
            if self.orbits.prediction:
                self.orbits.clear_prediction()
                return
            self.orbits.predict(self.sim)
            self.notify("Tracejado: previsão numérica de 2 corpos a partir deste instante, sem fusões.")
        except ValueError as exc:
            self.notify(str(exc))

    def input(self,key):
        if self.modal:
            if hasattr(self.modal,"input"):
                self.modal.input(key)
            elif key=="escape":
                self.modal.close()
            return
        actions={"space":self.toggle_play,"r":self.reset,"f":self.focus,
                 "t":self.follow,"home":self.explorer.overview,"p":self.hud.toggle_professor,
                 "b":self.toggle_field,"insert":self.create_body,"delete":self.remove_body,
                 "+":lambda:self.change_speed(1),"-":lambda:self.change_speed(-1)}
        if key in actions:
            actions[key]()
        elif key=="h":
            self.hud.root.enabled=not self.hud.root.enabled
        elif key=="escape":
            self.selected_uid=None

    def update(self):
        elapsed=min(time.dt,.1)
        if self.playing and not self.modal:
            self.accumulator+=elapsed*self.speed
            steps=0
            try:
                while self.accumulator>=self.sim.settings.dt and steps<200:
                    self.sim.step()
                    self.accumulator-=self.sim.settings.dt
                    steps+=1
                if steps==200:
                    self.accumulator=min(self.accumulator,self.sim.settings.dt)
                    self.notify("Limite de processamento: tempo simulado avança mais devagar que a taxa solicitada.")
            except (ValueError,FloatingPointError) as exc:
                self.playing=False
                self.notify(str(exc))
        self.consume_collision_events()
        self.effects.update(elapsed)
        if self.modal and hasattr(self.modal,"update"):
            self.modal.update()
        if not self.modal:
            self.explorer.track(self.sim.bodies)
        self.planets.sync(self.sim.bodies,self.select)
        stars=[b for b in self.sim.bodies if b.kind=="Estrela"]
        if stars:
            self.sunlight.position=tuple(stars[0].position)
        self.selection_ring.enabled=self.selected is not None
        if self.selected:
            self.selection_ring.position=tuple(self.selected.position)
            self.selection_ring.scale=self.selected.visual_radius*1.65
        self.visual_clock+=elapsed
        self.field_clock+=elapsed
        if self.field_visible and self.field_clock>=.5:
            self.field_clock=0
            self.field.draw(self.sim,True)
        if self.visual_clock>=.1:
            self.visual_clock=0
            self.orbits.redraw(self.sim)
            self.vectors.draw(self.sim,self.selected,self.source)
            if self.last_revision!=self.sim.revision:
                self.hud.rebuild_bodies()
                self.last_revision=self.sim.revision
            self.hud.update()

    def consume_collision_events(self):
        changed=False
        events=list(self.sim.collision_events)
        self.sim.collision_events.clear()
        for index,event in enumerate(events):
            if index>=len(events)-self.effects.MAX_BURSTS:
                self.effects.emit(event,self.planets.quality)
            if self.selected_uid in event.body_uids:
                self.selected_uid=event.survivor_uid
            if self.explorer.follow_uid in event.body_uids:
                self.explorer.follow_uid=event.survivor_uid
            if self.source_uid in event.body_uids:
                self.source_uid=event.survivor_uid
            self.notify(("Absorção estelar: " if event.kind=="absorption" else "Impacto: ")+" + ".join(event.names))
            changed=True
        if changed:
            self.orbits.clear_prediction()
            self.orbits.redraw(self.sim)
            self.field.draw(self.sim,self.field_visible)
            self.vectors.clear()
            if not self.source:
                self.cycle_source()
            self.hud.rebuild_bodies()


def run(smoke_seconds=0, verify=False):
    app=Ursina(title="PROJECT GENESIS | Laboratório gravitacional",borderless=False,
               fullscreen=False,size=(1440,810),vsync=True,development_mode=False,
               icon=str(application.package_folder/"textures"/"ursina.ico"))
    window.color=color.rgb32(4,8,16)
    window.exit_button.visible=False
    window.fps_counter.enabled=False
    camera.clip_plane_far=500
    camera.fov=55
    lab=Genesis()
    if verify:
        from diagnostics import verify_application
        verify_application(lab,app)
    if smoke_seconds:
        invoke(application.quit,delay=smoke_seconds)
    app.run()
