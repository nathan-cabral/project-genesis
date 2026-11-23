"""Exercise our application objects and capture our renderer (no OS input automation)."""
from pathlib import Path


def verify_application(lab, app):
    from panda3d.core import Filename
    from ursina import invoke, application
    import numpy as np

    output=Path("exports")
    output.mkdir(exist_ok=True)

    def capture(name):
        app.graphicsEngine.renderFrame()
        app.graphicsEngine.renderFrame()
        app.win.saveScreenshot(Filename.fromOsSpecific(str((output/name).resolve())))
        from PIL import Image
        assert Image.open(output/name).convert("RGB").getextrema()[0][1]>10, "Captura sem renderização"

    def overview():
        lab.playing=False
        capture("01-universo.png")
        lab.create_body()
        assert lab.modal is not None

    def editor():
        capture("02-editor.png")
        lab.modal.close()
        lab.playing=True
        lab.create_body()
        lab.modal.inputs["name"].text="Rascunho cancelado"
        lab.modal.begin_pick()
        lab.modal.input("escape")
        assert not lab.modal.picking
        assert lab.modal.inputs["name"].text=="Rascunho cancelado"
        lab.modal.close()
        assert lab.playing and len(lab.sim.bodies)==10
        lab.playing=False
        lab.create_body()
        from visualization.placement import screen_position_on_plane
        from panda3d.core import Point2,Point3
        from ursina import window
        target=np.array([2.4,0,1.7])
        projected=Point2()
        assert app.camLens.project(app.cam.get_relative_point(app.render,Point3(*target)),projected)
        hit=screen_position_on_plane(projected.x*window.aspect_ratio/2,projected.y/2)
        np.testing.assert_allclose(hit,target,atol=1e-4)
        lab.modal.begin_pick()
        assert lab.modal.picking and not lab.playing
        assert len(lab.sim.bodies)==10
        lab.modal.preview.marker.position=tuple(target)
        capture("05-posicionamento.png")
        lab.modal.finish_pick(hit)
        np.testing.assert_allclose(lab.modal.position(),target,atol=1e-4)
        lab.modal.inputs["name"].text="Teste de criação"
        lab.modal.confirm.on_click()
        assert len(lab.sim.bodies)==11
        assert lab.selected.name=="Teste de criação"
        lab.edit_body()
        lab.modal.inputs["mass"].text="0.000012"
        lab.modal.toggle_advanced()
        capture("06-avancado.png")
        lab.modal.confirm.on_click()
        assert lab.selected.mass==.000012
        lab.open_settings()
        lab.modal.inputs["dt"].text="0.0003"
        next(c for c in lab.modal.root.children if getattr(c,"text",None)=="Aplicar").on_click()
        assert lab.sim.settings.dt==.0003
        lab.remove_body()
        assert len(lab.sim.bodies)==10
        lab.select(lab.sim.bodies[3].uid)
        for name in lab.vectors.enabled:
            lab.vectors.enabled[name]=True
        lab.vectors.components=True
        lab.hud.toggle_professor()
        lab.hud.update()
        lab.toggle_field()
        assert lab.field.entity is not None
        assert all(len(segment)==2 for segment in lab.field.entity.model.triangles)

    def teacher():
        capture("03-professor.png")
        lab.hud.toggle_professor()
        for scenario in __import__("simulation.scenarios",fromlist=["SCENARIOS"]).SCENARIOS:
            lab.load_scenario(scenario)
            for _ in range(100):
                lab.sim.step()
            assert np.isfinite(lab.sim.total_energy)
        lab.load_scenario("Estrelas binárias")
        lab.select(lab.sim.bodies[1].uid)
        for _ in range(1000):
            lab.sim.step()
        lab.predict()
        assert lab.orbits.prediction is not None
        lab.open_charts()
        for metric in ("Velocidade","Aceleração","Distância","Posição","Energia"):
            lab.charts.set_metric(metric)
        capture("04-telemetria.png")
        lab.charts.export_png(output/"04-graficos.png")
        lab.charts.close()
        lab.load_scenario("Sistema Genesis")
        print("GENESIS VERIFY: posicionamento na cena, criação, edição, ajustes, 7 cenários e telemetria integrada OK",flush=True)

    def collision_visuals():
        from simulation.body import Body
        from simulation.physics import Simulation,Settings
        from ursina import camera
        lab.effects.clear()
        lab.sim=Simulation([Body("A",1,[-.08,0,0],[0,0,0],.12,collision_radius=.1),
                            Body("B",1,[.08,0,0],[0,0,0],.12,collision_radius=.1)],Settings(g=1e-8))
        lab.sim.step()
        assert len(lab.sim.collision_events)==1
        event=lab.sim.collision_events[0]
        lab.consume_collision_events()
        assert len(lab.effects.bursts)==1
        lab.effects.update(.35)
        lab.explorer.position=(0,0,0)
        lab.explorer.rotation=(22,-18,0)
        lab.explorer.target_z=-3
        camera.z=-3
        lab.planets.sync(lab.sim.bodies,lab.select)
        lab.hud.update()
        capture("07-explosao.png")
        lab.effects.update(3)
        assert not lab.effects.bursts
        for _ in range(14):
            lab.effects.emit(event,"Baixa")
        assert len(lab.effects.bursts)==lab.effects.MAX_BURSTS
        lab.effects.clear()
        sun=Body("Sol",1,[0,0,0],[0,0,0],.28,(1,.66,.22),"Estrela",.00465)
        visitor=Body("Impactante",1e-6,[-1,0,0],[4000,0,0],.06)
        lab.sim=Simulation([visitor,sun],Settings(g=1e-8,dt=.001,collisions=False))
        lab.sim.step()
        assert len(lab.sim.bodies)==1 and lab.sim.bodies[0].uid==sun.uid
        lab.consume_collision_events()
        assert lab.effects.bursts[0].absorbing
        lab.effects.update(.12)
        lab.planets.sync(lab.sim.bodies,lab.select)
        lab.hud.update()
        capture("08-absorcao-solar.png")
        lab.effects.update(3)
        assert not lab.effects.bursts
        lab.load_scenario("Sistema Genesis")
        assert not lab.effects.bursts and not lab.sim.collision_events
        print("GENESIS VERIFY: explosão, destroços, absorção solar, limites e limpeza de efeitos OK",flush=True)

    invoke(overview,delay=2.5)
    invoke(editor,delay=3.3)
    invoke(teacher,delay=4.8)
    invoke(collision_visuals,delay=6.5)
    invoke(application.quit,delay=10)
