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
_GAP_Y         = 50
_TOP_MARGIN    = 12
_BOTTOM_MARGIN = 15


def _compute_layout(rows: int, cols: int):
    avail_h = (CANVAS_H - _TOP_MARGIN - 2 * _LABEL_H - _GAP_Y - _BOTTOM_MARGIN) // 2
    avail_w = CANVAS_W - 2 * _MARGIN_X
    cs      = int(min(avail_h / rows, avail_w / cols, 80))
    cs      = max(cs, 14)
    mat_w   = cols * cs
    ox      = (CANVAS_W - mat_w) // 2
    oy_e    = _TOP_MARGIN + _LABEL_H
    oy_r    = oy_e + rows * cs + _GAP_Y + _LABEL_H
    return cs, ox, oy_e, oy_r


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
        self.hover_result  = None   # (r, c) or None
        self.hover_entry   = None   # (r, c) or None
        self.edit_cell     = None   # (r, c) pending popup edit
        self.last_step_t   = 0.0
        self.steps_per_sec = 5
        self._refresh_layout()

    def _refresh_layout(self):
        cs, ox, oy_e, oy_r = _compute_layout(self.solver.rows, self.solver.cols)
        self.cell_size = cs
        self.ox        = ox
        self.oy_entry  = oy_e
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
        dpg.set_value("residual_text", "—")
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
        dpg.set_value("hover_cell_text", "—")
        for t in blank_tags: dpg.set_value(t, "")
        return

    i, j = cell
    s = state.solver
    dpg.set_value("hover_cell_text",
                  f"result[{i}, {j}]  =  {s.result[i, j]:.5f}")

    formula, _ = s.get_cell_formula(i, j)
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
            return
        mx, my = dpg.get_mouse_pos(local=False)
        cy = my - BAR_H       # canvas-local y (canvas window has no title bar)
        cx = mx               # canvas window starts at x=0
        r, c, cs = state.solver.rows, state.solver.cols, state.cell_size
        state.hover_result = _hit_cell(cx, cy, state.ox, state.oy_result, r, c, cs)
        state.hover_entry  = _hit_cell(cx, cy, state.ox, state.oy_entry,  r, c, cs)

    def on_mouse_click(_, __):
        if not dpg.is_item_hovered("canvas_window"):
            return
        mx, my = dpg.get_mouse_pos(local=False)
        cy = my - BAR_H
        cx = mx
        r, c, cs = state.solver.rows, state.solver.cols, state.cell_size
        cell = _hit_cell(cx, cy, state.ox, state.oy_entry, r, c, cs)
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

    # Edit-cell popup
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

        # Sync parameters that can change without a Spawn
        state.solver.omega    = dpg.get_value("gs_omega")
        state.solver.max_iter = dpg.get_value("gs_max_iter")
        state.steps_per_sec   = dpg.get_value("gs_speed")

        # Decide whether to step
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

        # Hover formula
        _update_hover_info(state)

        # Resolve neighbor highlight for current hover
        nbrs: set = set()
        if state.hover_result:
            _, nbr_list = state.solver.get_cell_formula(*state.hover_result)
            nbrs = set(nbr_list)

        # Redraw canvas
        dpg.delete_item(DRAWLIST, children_only=True)
        draw_scene(
            drawlist     = DRAWLIST,
            solver       = state.solver,
            cell_size    = state.cell_size,
            ox           = state.ox,
            oy_entry     = state.oy_entry,
            oy_result    = state.oy_result,
            hover_result = state.hover_result,
            hover_entry  = state.hover_entry,
            neighbors_hl = nbrs,
        )

        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
