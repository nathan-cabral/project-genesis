import numpy as np
from ursina import EditorCamera, Vec3, lerp, time


class ExplorerCamera(EditorCamera):
    def __init__(self):
        super().__init__(rotation=(32,-22,0), zoom_speed=1.2, pan_speed=(3,3))
        self.follow_uid=None
        self.controls_enabled=True
        self.overview()

    def input(self,key):
        if self.controls_enabled:
            super().input(key)

    def update(self):
        if self.controls_enabled:
            super().update()

    def overview(self):
        self.follow_uid=None
        self.position=(0,0,0)
        self.rotation=(32,-22,0)
        self.target_z=-23

    def focus(self, body, follow=False):
        self.position=Vec3(*body.position)
        self.target_z=-max(1.8,body.visual_radius*12)
        self.follow_uid=body.uid if follow else None

    def track(self, bodies):
        target=next((b for b in bodies if b.uid==self.follow_uid),None)
        if target is not None:
            self.position=lerp(self.position,Vec3(*target.position),min(1,time.dt*8))
