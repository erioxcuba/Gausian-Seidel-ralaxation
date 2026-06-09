import dearpygui.dearpygui as dpg
import numpy as np

_LABEL_OFFSET = 18


def _heatmap(v: float, vmin: float, vmax: float, alpha: int = 210) -> list:
    t = 0.5 if vmax <= vmin else (v - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, float(t)))
    if t < 0.5:
        s = t * 2
        r = int(30  + s * 20)
        g = int(60  + s * 110)
        b = int(210 - s * 30)
    else:
        s = (t - 0.5) * 2
        r = int(50  + s * 200)
        g = int(170 - s * 140)
        b = int(180 - s * 160)
    return [r, g, b, alpha]


def _draw_matrix(drawlist: str,
                 matrix: np.ndarray,
                 fixed:  np.ndarray,
                 ox: int, oy: int, cs: int,
                 label:     str   = "",
                 vmin:      float = None,
                 vmax:      float = None,
                 hi_main:   tuple = None,
                 hi_nbrs_a: set   = None,   # green  — from current sweep (T, L)
                 hi_nbrs_b: set   = None):  # orange — from previous step (B, R)

    rows, cols = matrix.shape
    if vmin is None: vmin = float(matrix.min())
    if vmax is None: vmax = float(matrix.max())
    if hi_nbrs_a is None: hi_nbrs_a = set()
    if hi_nbrs_b is None: hi_nbrs_b = set()

    if label:
        dpg.draw_text([ox, oy - _LABEL_OFFSET], label,
                      color=[200, 220, 255, 255], size=14, parent=drawlist)

    mat_w = cols * cs
    mat_h = rows * cs

    dpg.draw_rectangle([ox - 1, oy - 1], [ox + mat_w + 1, oy + mat_h + 1],
                       fill=[14, 18, 30, 255], color=[40, 55, 80, 200],
                       thickness=1, parent=drawlist)

    for i in range(rows):
        for j in range(cols):
            x0 = ox + j * cs
            y0 = oy + i * cs
            x1 = x0 + cs
            y1 = y0 + cs
            val      = float(matrix[i, j])
            is_fixed = bool(fixed[i, j])
            alpha    = 175 if is_fixed else 215
            fill     = _heatmap(val, vmin, vmax, alpha)

            dpg.draw_rectangle([x0, y0], [x1, y1],
                               fill=fill, color=[0, 0, 0, 0], parent=drawlist)

            bdr_col   = [52, 62, 88, 130]
            bdr_thick = 1
            if hi_main and (i, j) == hi_main:
                bdr_col   = [255, 240, 55, 255]    # yellow
                bdr_thick = 3
            elif (i, j) in hi_nbrs_a:
                bdr_col   = [70, 240, 160, 255]    # green
                bdr_thick = 2
            elif (i, j) in hi_nbrs_b:
                bdr_col   = [255, 160, 50, 255]    # orange
                bdr_thick = 2

            dpg.draw_rectangle([x0, y0], [x1, y1],
                               fill=[0, 0, 0, 0], color=bdr_col,
                               thickness=bdr_thick, parent=drawlist)

            if cs >= 22:
                txt = str(int(round(val)))
                brightness = sum(fill[:3])
                txt_col = [240, 240, 240, 230] if brightness < 360 else [18, 18, 18, 220]
                tx = x0 + max(2, (cs - len(txt) * 7) // 2)
                ty = y0 + (cs - 12) // 2
                dpg.draw_text([tx, ty], txt, color=txt_col, size=12, parent=drawlist)

            if is_fixed and cs >= 16:
                dpg.draw_text([x0 + 2, y0 + 2], "B",
                              color=[255, 218, 80, 200], size=10, parent=drawlist)

    for i in range(rows + 1):
        y = oy + i * cs
        dpg.draw_line([ox, y], [ox + mat_w, y],
                      color=[50, 60, 85, 150], thickness=1, parent=drawlist)
    for j in range(cols + 1):
        x = ox + j * cs
        dpg.draw_line([x, oy], [x, oy + mat_h],
                      color=[50, 60, 85, 150], thickness=1, parent=drawlist)


def draw_scene(drawlist, solver,
               cell_size: int,
               ox_entry: int, ox_prev: int, ox_result: int,
               oy_top: int, oy_result: int,
               hover_result=None, hover_entry=None,
               nbrs_new=None, nbrs_prev=None):

    if nbrs_new  is None: nbrs_new  = set()
    if nbrs_prev is None: nbrs_prev = set()

    vmin = min(float(solver.entry.min()),
               float(solver.result.min()),
               float(solver.prev_result.min()))
    vmax = max(float(solver.entry.max()),
               float(solver.result.max()),
               float(solver.prev_result.max()))
    if vmax <= vmin:
        vmax = vmin + 1.0

    # Entry matrix (top-left): x0[i,j] is the only value read from here — yellow on [i,j]
    entry_main = hover_result if hover_result is not None else hover_entry
    _draw_matrix(drawlist, solver.entry, solver.fixed,
                 ox_entry, oy_top, cell_size,
                 label="Entry  (x0)",
                 vmin=vmin, vmax=vmax,
                 hi_main=entry_main)

    # Previous step matrix (top-right): B=[i+1,j] and R=[i,j+1] are read from here — orange
    _draw_matrix(drawlist, solver.prev_result, solver.fixed,
                 ox_prev, oy_top, cell_size,
                 label="Previous step",
                 vmin=vmin, vmax=vmax,
                 hi_nbrs_b=nbrs_prev if hover_result is not None else set())

    # Result matrix (bottom): T=[i-1,j] and L=[i,j-1] already updated this sweep — green;
    # [i,j] itself is the cell being computed — yellow
    _draw_matrix(drawlist, solver.result, solver.fixed,
                 ox_result, oy_result, cell_size,
                 label=f"Result  (iteration {solver.iteration})",
                 vmin=vmin, vmax=vmax,
                 hi_main=hover_result,
                 hi_nbrs_a=nbrs_new if hover_result is not None else set())
