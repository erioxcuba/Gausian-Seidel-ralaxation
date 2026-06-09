import dearpygui.dearpygui as dpg
from .layout import VIEWPORT_W, VIEWPORT_H, BAR_H
from .canvas import CANVAS_W

PANEL_X  = CANVAS_W + 4
PANEL_W  = VIEWPORT_W - CANVAS_W - 8
INPUT_W  = 210


def build_control_panel(callbacks: dict):

    with dpg.theme() as _theme:
        with dpg.theme_component(dpg.mvSliderFloat):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,          [38, 58, 92, 210])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,   [52, 74, 112, 230])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,       [100, 160, 240, 255])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [140, 200, 255, 255])
        with dpg.theme_component(dpg.mvSliderInt):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,          [38, 58, 92, 210])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,   [52, 74, 112, 230])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,       [100, 160, 240, 255])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [140, 200, 255, 255])
        with dpg.theme_component(dpg.mvInputFloat):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,         [38, 58, 92, 210])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,  [52, 74, 112, 230])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,   [64, 90, 132, 255])
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        [50, 80, 130, 220])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [70, 110, 170, 240])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  [90, 140, 200, 255])
    dpg.bind_theme(_theme)

    with dpg.window(label="Controls", tag="panel_window",
                    pos=(PANEL_X, BAR_H), width=PANEL_W, height=VIEWPORT_H - BAR_H,
                    no_resize=True, no_move=True, no_close=True, no_scrollbar=False):

        dpg.add_text("Gauss-Seidel Relaxation", color=(200, 220, 255))
        dpg.add_separator()

        # Grid
        with dpg.collapsing_header(label="Grid", default_open=True):
            dpg.add_slider_int(label="Rows",    tag="gs_rows",
                               default_value=6, min_value=2, max_value=15, width=INPUT_W)
            dpg.add_slider_int(label="Columns", tag="gs_cols",
                               default_value=6, min_value=2, max_value=15, width=INPUT_W)
            dpg.add_spacer(height=5)
            dpg.add_button(label="Spawn + Randomize", tag="spawn_btn",
                           width=INPUT_W, callback=callbacks.get("on_spawn"))
            dpg.add_text("Rebuilds grid and fills with random values", color=(130, 130, 155))
            dpg.add_spacer(height=8)

        # Relaxation
        with dpg.collapsing_header(label="Relaxation", default_open=True):
            dpg.add_slider_float(label="ax (horiz)", tag="gs_ax",
                                 default_value=1.0, min_value=0.0, max_value=20.0,
                                 format="%.3f", width=INPUT_W)
            dpg.add_slider_float(label="ay (vert)",  tag="gs_ay",
                                 default_value=1.0, min_value=0.0, max_value=20.0,
                                 format="%.3f", width=INPUT_W)
            dpg.add_text("target = (x0+ax*(L+R)+ay*(T+B)) / (1+2ax+2ay)", color=(130, 130, 155))
            dpg.add_spacer(height=4)
            dpg.add_radio_button(items=["Manual", "Auto"],
                                 tag="gs_a_mode", default_value="Manual",
                                 horizontal=True)
            dpg.add_spacer(height=4)
            dpg.add_slider_float(label="dt",   tag="gs_dt",
                                 default_value=0.1, min_value=0.001, max_value=1.0,
                                 format="%.4f", width=INPUT_W)
            dpg.add_slider_float(label="diff", tag="gs_diff",
                                 default_value=0.5, min_value=0.0, max_value=5.0,
                                 format="%.3f", width=INPUT_W)
            dpg.add_text("Auto: ax = dt*diff*(cols-1)^2", color=(130, 130, 155))
            dpg.add_text("      ay = dt*diff*(rows-1)^2", color=(130, 130, 155))
            dpg.add_spacer(height=4)
            dpg.add_slider_float(label="Factor (w)", tag="gs_omega",
                                 default_value=1.0, min_value=0.1, max_value=2.0,
                                 format="%.3f", width=INPUT_W)
            dpg.add_text("w<1 under-relax   w=1 GS   w>1 SOR on target", color=(130, 130, 155))
            dpg.add_slider_int(label="Max Iterations", tag="gs_max_iter",
                               default_value=50, min_value=1, max_value=500, width=INPUT_W)
            dpg.add_slider_int(label="Steps / sec", tag="gs_speed",
                               default_value=5, min_value=1, max_value=60, width=INPUT_W)
            dpg.add_spacer(height=8)

        # Control
        with dpg.collapsing_header(label="Control", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="  Run  ", tag="run_btn",
                               width=INPUT_W // 2, callback=callbacks.get("on_run"))
                dpg.add_button(label="Reset->Random", tag="reset_btn",
                               width=INPUT_W // 2, callback=callbacks.get("on_reset"))
            dpg.add_spacer(height=4)
            dpg.add_button(label="Revert Result to Entry", tag="revert_btn",
                           width=INPUT_W, callback=callbacks.get("on_revert"))
            dpg.add_spacer(height=4)
            dpg.add_text("Space = step / pause", color=(110, 110, 130))
            dpg.add_text("Click entry cell to edit its value", color=(110, 110, 130))
            dpg.add_spacer(height=8)

        # Metrics
        with dpg.collapsing_header(label="Metrics", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text("Iteration:",    color=(180, 180, 200))
                dpg.add_text("--", tag="iter_text", color=(220, 200, 160))
            with dpg.group(horizontal=True):
                dpg.add_text("Max Residual:", color=(180, 180, 200))
                dpg.add_text("--", tag="residual_text", color=(220, 200, 160))
            with dpg.group(horizontal=True):
                dpg.add_text("Status:",       color=(180, 180, 200))
                dpg.add_text("Paused", tag="status_text", color=(160, 200, 160))
            dpg.add_spacer(height=6)
            dpg.add_text("Residual History  (log10 scale)", color=(180, 180, 200))
            dpg.add_simple_plot(tag="residual_plot",
                                width=PANEL_W - 30, height=75,
                                default_value=(0.0,), histogram=False)
            dpg.add_spacer(height=8)

        # Hover Formula
        with dpg.collapsing_header(label="Hover Formula  (result matrix)", default_open=True):
            dpg.add_text("Hovered cell", color=(180, 180, 200))
            dpg.add_text("--", tag="hover_cell_text", color=(220, 200, 160))
            dpg.add_separator()
            dpg.add_text("", tag="formula_line1", color=(140, 230, 170), wrap=PANEL_W - 20)
            dpg.add_text("", tag="formula_line2", color=(140, 230, 170), wrap=PANEL_W - 20)
            dpg.add_text("", tag="formula_line3", color=(140, 230, 170), wrap=PANEL_W - 20)
            dpg.add_text("", tag="formula_line4", color=(180, 240, 200), wrap=PANEL_W - 20)
            dpg.add_spacer(height=8)

        dpg.add_separator()
        dpg.add_text("B      = boundary cell (fixed)", color=(130, 130, 155))
        dpg.add_text("Yellow = cell being computed / x0 source", color=(130, 130, 155))
        dpg.add_text("Green  = T and L  (from current sweep)", color=(130, 130, 155))
        dpg.add_text("Orange = B and R  (from previous step)", color=(130, 130, 155))
        dpg.add_spacer(height=12)
