import dearpygui.dearpygui as dpg
import numpy as np

_LABEL_OFFSET = 18   # pixels above matrix origin for the label


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
                 label:   str   = "",
                 vmin:    float = None,
                 vmax:    float = None,
                 hi_main: tuple = None,
                 hi_nbrs: set   = None):

    rows, cols = matrix.shape
    if vmin is None: vmin = float(matrix.min())
    if vmax is None: vmax = float(matrix.max())
    if hi_nbrs is None: hi_nbrs = set()

    if label:
        dpg.draw_text([ox, oy - _LABEL_OFFSET], label,
                      color=[200, 220, 255, 255], size=14, parent=drawlist)

    mat_w = cols * cs
    mat_h = rows * cs

    # Background rect
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

            # Highlight border
            bdr_col   = [52, 62, 88, 130]
            bdr_thick = 1
            if hi_main and (i, j) == hi_main:
                bdr_col   = [255, 240, 55, 255]
                bdr_thick = 3
            elif (i, j) in hi_nbrs:
                bdr_col   = [70, 240, 160, 255]
                bdr_thick = 2

            dpg.draw_rectangle([x0, y0], [x1, y1],
                               fill=[0, 0, 0, 0], color=bdr_col,
                               thickness=bdr_thick, parent=drawlist)

            # Value label
            if cs >= 26:
                if cs >= 55:
                    txt = f"{val:.3f}"
                elif cs >= 38:
                    txt = f"{val:.2f}"
                else:
                    txt = f"{val:.1f}"
                brightness = sum(fill[:3])
                txt_col = [240, 240, 240, 230] if brightness < 360 else [18, 18, 18, 220]
                dpg.draw_text([x0 + 3, y0 + cs // 2 - 6],
                              txt, color=txt_col, size=12, parent=drawlist)

            # Boundary marker
            if is_fixed and cs >= 16:
                dpg.draw_text([x0 + 2, y0 + 2], "B",
                              color=[255, 218, 80, 200], size=10, parent=drawlist)

    # Grid lines
    for i in range(rows + 1):
        y = oy + i * cs
        dpg.draw_line([ox, y], [ox + mat_w, y],
                      color=[50, 60, 85, 150], thickness=1, parent=drawlist)
    for j in range(cols + 1):
        x = ox + j * cs
        dpg.draw_line([x, oy], [x, oy + mat_h],
                      color=[50, 60, 85, 150], thickness=1, parent=drawlist)


def draw_scene(drawlist, solver,
               cell_size: int, ox: int, oy_entry: int, oy_result: int,
               hover_result=None, hover_entry=None, neighbors_hl=None):

    if neighbors_hl is None:
        neighbors_hl = set()

    vmin = min(float(solver.entry.min()), float(solver.result.min()))
    vmax = max(float(solver.entry.max()), float(solver.result.max()))
    if vmax <= vmin:
        vmax = vmin + 1.0

    _draw_matrix(drawlist, solver.entry, solver.fixed,
                 ox, oy_entry, cell_size,
                 label="Input Matrix  (click to edit cells)",
                 vmin=vmin, vmax=vmax,
                 hi_main=hover_entry,
                 hi_nbrs=neighbors_hl)

    _draw_matrix(drawlist, solver.result, solver.fixed,
                 ox, oy_result, cell_size,
                 label=f"Result Matrix  (iteration {solver.iteration})",
                 vmin=vmin, vmax=vmax,
                 hi_main=hover_result,
                 hi_nbrs=neighbors_hl)
