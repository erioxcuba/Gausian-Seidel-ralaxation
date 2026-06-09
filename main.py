import time

import dearpygui.dearpygui as dpg
import numpy as np

from ui.layout          import setup_viewport, VIEWPORT_W, BAR_H
from ui.canvas          import build_canvas, CANVAS_W, CANVAS_H, DRAWLIST
from ui.panels          import build_control_panel
from rendering.renderer import draw_scene
from simulation.solver  import GaussSeidelSolver

# ── Layout geometry constants ──────────────────────────────────────────────────
_MARGIN_X      = 20
_LABEL_H       = 20
_GAP_X         = 30     # horizontal gap between entry and prev matrices
_GAP_Y         = 45     # vertical gap between top row and result row
_TOP_MARGIN    = 12
_BOTTOM_MARGIN = 15


def _compute_layout(rows: int, cols: int):
    # Two matrices side-by-side on top, one centered below
    avail_h_row  = (CANVAS_H - _TOP_MARGIN - 2 * _LABEL_H - _GAP_Y - _BOTTOM_MARGIN) // 2
    avail_w_half = (CANVAS_W - 3 * _MARGIN_X - _GAP_X) // 2
    cs = int(min(avail_h_row / rows, avail_w_half / cols, 45))
    cs = max(cs, 14)

    mat_w       = cols * cs
    total_top_w = 2 * mat_w + _GAP_X
    ox_entry    = (CANVAS_W - total_top_w) // 2
    ox_prev     = ox_entry + mat_w + _GAP_X
    oy_top      = _TOP_MARGIN + _LABEL_H

    ox_result = (CANVAS_W - mat_w) // 2
    oy_result = oy_top + rows * cs + _GAP_Y + _LABEL_H

    return cs, ox_entry, ox_prev, ox_result, oy_top, oy_result


def _hit_cell(mx: float, my: float,
              ox: int, oy: int,
              rows: int, cols: int, cs: int):
    lx, ly = mx - ox, my - oy
    if 0 <= lx < cols * cs and 0 <= ly < rows * cs:
        return int(ly // cs), int(lx // cs)
    return None


# ── Application state ──────────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.solver        = GaussSeidelSolver()
        self.running       = False
        self.step_req      = False
        self.hover_result  = None
        self.hover_entry   = None
        self.hover_prev    = None
        self.edit_cell     = None
        self.last_step_t   = 0.0
        self.steps_per_sec = 5
        self.prev_ax       = 1.0
        self.prev_ay       = 1.0
        self._refresh_layout()

    def _refresh_layout(self):
        cs, ox_e, ox_p, ox_r, oy_t, oy_r = _compute_layout(
            self.solver.rows, self.solver.cols)
        self.cell_size = cs
        self.ox_entry  = ox_e
        self.ox_prev   = ox_p
        self.ox_result = ox_r
        self.oy_top    = oy_t
        self.oy_result = oy_r


# ── Metrics helpers ────────────────────────────────────────────────────────────

def _update_metrics(state: AppState):
    s = state.solver
    dpg.set_value("iter_text", str(s.iteration))
    if s.residuals:
        dpg.set_value("residual_text", f"{s.residuals[-1]:.4e}")
        log_r = [float(np.log10(max(r, 1e-14))) for r in s.residuals[-80:]]
        dpg.set_value("residual_plot", tuple(log_r))
    else:
        dpg.set_value("residual_text", "--")
        dpg.set_value("residual_plot", (0.0,))

    if s.converged:
        status, col = "Converged!", (100, 240, 140)
    elif state.running:
        status, col = "Running...", (220, 200, 80)
    else:
        status, col = "Paused",     (160, 200, 160)
    dpg.set_value("status_text", status)
    dpg.configure_item("status_text", color=col)


def _update_hover_info(state: AppState):
    cell = state.hover_result
    blank_tags = ("formula_line1", "formula_line2", "formula_line3", "formula_line4")
    if cell is None:
        dpg.set_value("hover_cell_text", "--")
        for t in blank_tags: dpg.set_value(t, "")
        return

    i, j = cell
    s = state.solver
    dpg.set_value("hover_cell_text",
                  f"result[{i}, {j}]  =  {s.result[i, j]:.5f}")

    formula, _, _ = s.get_cell_formula(i, j)
    lines = (formula or "").split("\n")
    for k, tag in enumerate(blank_tags):
        dpg.set_value(tag, lines[k] if k < len(lines) else "")


# ── UI construction ────────────────────────────────────────────────────────────

def build_ui(state: AppState):

    def on_spawn():
        state.solver.rows = dpg.get_value("gs_rows")
        state.solver.cols = dpg.get_value("gs_cols")
        state.solver.initialize()
        _set_running(state, False)
        state._refresh_layout()
        _update_metrics(state)

    def on_run():
        if state.solver.converged and not state.running:
            return
        _set_running(state, not state.running)

    def on_reset():
        state.solver.rows = dpg.get_value("gs_rows")
        state.solver.cols = dpg.get_value("gs_cols")
        state.solver.initialize()
        _set_running(state, False)
        state._refresh_layout()
        _update_metrics(state)

    def on_revert():
        state.solver.reset()
        _update_metrics(state)

    def on_edit_confirm():
        if state.edit_cell is not None:
            i, j = state.edit_cell
            state.solver.set_entry_value(i, j, dpg.get_value("edit_value_input"))
        dpg.configure_item("edit_popup", show=False)
        state.edit_cell = None

    def on_edit_cancel():
        dpg.configure_item("edit_popup", show=False)
        state.edit_cell = None

    def on_mouse_move(_, __):
        if not dpg.is_item_hovered("canvas_window"):
            state.hover_result = None
            state.hover_entry  = None
            state.hover_prev   = None
            return
        mx, my = dpg.get_mouse_pos(local=False)
        cy = my - BAR_H
        cx = mx
        r, c, cs = state.solver.rows, state.solver.cols, state.cell_size
        state.hover_result = _hit_cell(cx, cy, state.ox_result, state.oy_result, r, c, cs)
        state.hover_entry  = _hit_cell(cx, cy, state.ox_entry,  state.oy_top,    r, c, cs)
        state.hover_prev   = _hit_cell(cx, cy, state.ox_prev,   state.oy_top,    r, c, cs)

    def on_mouse_click(_, __):
        if not dpg.is_item_hovered("canvas_window"):
            return
        mx, my = dpg.get_mouse_pos(local=False)
        cy = my - BAR_H
        cx = mx
        r, c, cs = state.solver.rows, state.solver.cols, state.cell_size
        cell = _hit_cell(cx, cy, state.ox_entry, state.oy_top, r, c, cs)
        if cell is not None:
            i, j = cell
            state.edit_cell = (i, j)
            kind = "boundary" if state.solver.fixed[i, j] else "interior"
            dpg.set_value("edit_cell_label",
                          f"Edit entry[{i}, {j}]  ({kind})")
            dpg.set_value("edit_value_input", float(state.solver.entry[i, j]))
            dpg.configure_item("edit_popup", show=True)

    def on_key_space(_, __):
        if state.running:
            _set_running(state, False)
        else:
            state.step_req = True

    callbacks = {
        "on_spawn":  on_spawn,
        "on_run":    on_run,
        "on_reset":  on_reset,
        "on_revert": on_revert,
    }

    build_canvas()
    build_control_panel(callbacks)

    with dpg.window(label="Edit Cell", modal=True, tag="edit_popup",
                    show=False, pos=(500, 390), width=280, height=130,
                    no_resize=True, no_close=False):
        dpg.add_text("", tag="edit_cell_label", color=(180, 220, 255))
        dpg.add_input_float(tag="edit_value_input", width=240,
                            step=0.0, format="%.4f")
        with dpg.group(horizontal=True):
            dpg.add_button(label="  OK  ",  width=110, callback=on_edit_confirm)
            dpg.add_button(label="Cancel", width=110, callback=on_edit_cancel)

    with dpg.handler_registry():
        dpg.add_mouse_move_handler(callback=on_mouse_move)
        dpg.add_mouse_click_handler(button=0, callback=on_mouse_click)
        dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=on_key_space)


def _set_running(state: AppState, running: bool):
    state.running = running
    dpg.configure_item("run_btn", label=" Pause " if running else "  Run  ")


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    state = AppState()
    setup_viewport()
    build_ui(state)
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        now = time.perf_counter()

        auto_a = dpg.get_value("gs_a_mode") == "Auto"
        dpg.configure_item("gs_ax",   enabled=not auto_a)
        dpg.configure_item("gs_ay",   enabled=not auto_a)
        dpg.configure_item("gs_dt",   enabled=auto_a)
        dpg.configure_item("gs_diff", enabled=auto_a)
        if auto_a:
            dt   = dpg.get_value("gs_dt")
            diff = dpg.get_value("gs_diff")
            rows = state.solver.rows
            cols = state.solver.cols
            ax   = dt * diff * (cols - 1) ** 2
            ay   = dt * diff * (rows - 1) ** 2
            state.solver.ax = ax
            state.solver.ay = ay
            dpg.set_value("gs_ax", min(ax, 20.0))
            dpg.set_value("gs_ay", min(ay, 20.0))
        else:
            ax = dpg.get_value("gs_ax")
            ay = dpg.get_value("gs_ay")
            if state.solver.rows == state.solver.cols:
                if ax != state.prev_ax:
                    ay = ax
                    dpg.set_value("gs_ay", ay)
                elif ay != state.prev_ay:
                    ax = ay
                    dpg.set_value("gs_ax", ax)
            state.solver.ax = ax
            state.solver.ay = ay
            state.prev_ax   = ax
            state.prev_ay   = ay
        state.solver.omega    = dpg.get_value("gs_omega")
        state.solver.max_iter = dpg.get_value("gs_max_iter")
        state.steps_per_sec   = dpg.get_value("gs_speed")

        do_step = False
        if state.step_req:
            do_step = True
            state.step_req = False
        elif state.running and not state.solver.converged:
            interval = 1.0 / max(state.steps_per_sec, 1)
            if now - state.last_step_t >= interval:
                do_step = True

        if do_step:
            state.solver.step()
            state.last_step_t = now
            _update_metrics(state)
            if state.solver.converged:
                _set_running(state, False)

        _update_hover_info(state)

        nbrs_new_set:  set = set()
        nbrs_prev_set: set = set()
        if state.hover_result:
            _, new_list, prev_list = state.solver.get_cell_formula(*state.hover_result)
            nbrs_new_set  = set(new_list)
            nbrs_prev_set = set(prev_list)

        dpg.delete_item(DRAWLIST, children_only=True)
        draw_scene(
            drawlist     = DRAWLIST,
            solver       = state.solver,
            cell_size    = state.cell_size,
            ox_entry     = state.ox_entry,
            ox_prev      = state.ox_prev,
            ox_result    = state.ox_result,
            oy_top       = state.oy_top,
            oy_result    = state.oy_result,
            hover_result = state.hover_result,
            hover_entry  = state.hover_entry,
            nbrs_new     = nbrs_new_set,
            nbrs_prev    = nbrs_prev_set,
        )

        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
