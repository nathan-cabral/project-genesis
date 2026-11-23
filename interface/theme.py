"""Shared visual language for the desktop UI."""
from ursina import Entity, Text, Button, Quad, color

BG = color.rgb32(12, 19, 29)
SURFACE = color.rgb32(20, 30, 43)
HOVER = color.rgb32(31, 47, 62)
INK = color.rgb32(227, 236, 244)
MUTED = color.rgb32(139, 158, 179)
ACCENT = color.rgb32(106, 221, 200)
ACTIVE = color.rgb32(30, 69, 70)


def panel(parent, position=(0, 0), size=(.3, .4), tint=BG, z=.1, collider=None):
    return Entity(parent=parent, model=Quad(radius=.025, aspect=size[0]/size[1]),
                  position=position, scale=size, color=tint, z=z, collider=collider)


def label(text, parent, x, y, scale=.75, tint=INK):
    return Text(text or " ", parent=parent, position=(x, y), scale=scale, color=tint)


def button(text, parent, x, y, width, callback, tint=None, height=.036, text_size=.72):
    return Button(text or " ", parent=parent, position=(x,y), scale=(width,height),
                  radius=.16, color=tint or SURFACE, text_color=INK, text_size=text_size,
                  highlight_text_size=text_size, highlight_color=HOVER,
                  pressed_color=ACTIVE, on_click=callback)
