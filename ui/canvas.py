import dearpygui.dearpygui as dpg
from .layout import VIEWPORT_H, BAR_H

CANVAS_W  = 860
CANVAS_H  = VIEWPORT_H - BAR_H        # 900
DRAWLIST  = "main_drawlist"
_BG_COLOR = [18, 24, 38, 255]


def build_canvas():
    with dpg.window(label="Simulation", tag="canvas_window",
                    pos=(0, BAR_H), width=CANVAS_W, height=CANVAS_H,
                    no_resize=True, no_move=True, no_close=True,
                    no_title_bar=True, no_scrollbar=True):
        dpg.add_drawlist(tag=DRAWLIST, width=CANVAS_W, height=CANVAS_H)
