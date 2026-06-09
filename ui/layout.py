import dearpygui.dearpygui as dpg

VIEWPORT_W = 1380
VIEWPORT_H = 920
BAR_H      = 20


def setup_viewport(title: str = "Gauss-Seidel Relaxation"):
    dpg.create_context()
    dpg.create_viewport(title=title,
                        width=VIEWPORT_W, height=VIEWPORT_H,
                        x_pos=60, y_pos=40,
                        resizable=False)
    dpg.setup_dearpygui()
