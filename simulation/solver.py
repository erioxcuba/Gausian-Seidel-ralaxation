import numpy as np


class GaussSeidelSolver:
    def __init__(self):
        self.rows = 6
        self.cols = 6
        self.omega = 1.0
        self.ax = 1.0   # horizontal: dt*diff/(dx^2) = dt*diff*(cols-1)^2
        self.ay = 1.0   # vertical:   dt*diff/(dy^2) = dt*diff*(rows-1)^2
        self.max_iter = 50

        self.entry       = np.zeros((self.rows, self.cols))
        self.result      = np.zeros((self.rows, self.cols))
        self.prev_result = np.zeros((self.rows, self.cols))
        self.fixed       = np.zeros((self.rows, self.cols), dtype=bool)

        self.last_neighbors = np.zeros((self.rows, self.cols, 4))  # T B L R
        self.last_old       = np.zeros((self.rows, self.cols))

        self.iteration = 0
        self.residuals: list = []
        self.converged = False

        self.initialize()

    # ------------------------------------------------------------------ public

    def initialize(self):
        r, c = self.rows, self.cols
        self.entry       = np.zeros((r, c))
        self.result      = np.zeros((r, c))
        self.prev_result = np.zeros((r, c))
        self.fixed       = np.zeros((r, c), dtype=bool)

        self.fixed[0, :]  = True
        self.fixed[-1, :] = True
        self.fixed[:, 0]  = True
        self.fixed[:, -1] = True

        rng = np.random.default_rng()
        self.entry[0, :]  = rng.uniform(0.0, 10.0, c)
        self.entry[-1, :] = rng.uniform(0.0, 10.0, c)
        self.entry[:, 0]  = rng.uniform(0.0, 10.0, r)
        self.entry[:, -1] = rng.uniform(0.0, 10.0, r)
        for i in range(1, r - 1):
            for j in range(1, c - 1):
                self.entry[i, j] = rng.uniform(0.0, 10.0)

        self.result      = self.entry.copy()
        self.prev_result = self.entry.copy()
        self._reset_snapshots()
        self.iteration = 0
        self.residuals = []
        self.converged = False

    def reset(self):
        """Reset result to entry without re-randomizing."""
        self.result      = self.entry.copy()
        self.prev_result = self.entry.copy()
        self._reset_snapshots()
        self.iteration = 0
        self.residuals = []
        self.converged = False

    def set_entry_value(self, i: int, j: int, value: float):
        self.entry[i, j] = float(value)
        self.result[i, j] = float(value)

    def step(self) -> bool:
        """One Gauss-Seidel sweep. Returns False if already finished."""
        if self.converged or self.iteration >= self.max_iter:
            self.converged = True
            return False

        self.prev_result = self.result.copy()
        ax    = self.ax
        ay    = self.ay
        denom = 1.0 + 2.0 * ax + 2.0 * ay

        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                top   = self.result[i - 1, j]
                bot   = self.result[i + 1, j]
                left  = self.result[i, j - 1]
                right = self.result[i, j + 1]
                old   = self.result[i, j]

                self.last_neighbors[i, j] = [top, bot, left, right]
                self.last_old[i, j]       = old

                target = (self.entry[i, j] + ax * (left + right) + ay * (top + bot)) / denom
                new    = self.omega * target + (1.0 - self.omega) * old
                self.result[i, j] = new

        self.result[self.fixed] = self.entry[self.fixed]

        # True equation residual: separate pass with fully-updated grid
        max_res = 0.0
        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                top   = self.result[i - 1, j]
                bot   = self.result[i + 1, j]
                left  = self.result[i, j - 1]
                right = self.result[i, j + 1]
                target = (self.entry[i, j] + ax * (left + right) + ay * (top + bot)) / denom
                r = abs(self.result[i, j] - target)
                if r > max_res:
                    max_res = r

        self.iteration += 1
        self.residuals.append(max_res)
        if max_res < 1e-8:
            self.converged = True
        return True

    def get_cell_formula(self, i: int, j: int):
        """Return (formula_string, nbrs_from_new, nbrs_from_prev) for hover display."""
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return None, [], []

        if self.fixed[i, j]:
            return ("u[%d,%d] = %.4f  (boundary - fixed)" % (i, j, self.entry[i, j]), [], [])

        if self.iteration == 0:
            return ("u[%d,%d] = %.4f  (no iteration yet)" % (i, j, self.result[i, j]), [], [])

        top, bot, left, right = self.last_neighbors[i, j]
        old = self.last_old[i, j]
        ax  = self.ax
        ay  = self.ay
        w   = self.omega
        x0  = self.entry[i, j]
        denom  = 1.0 + 2.0 * ax + 2.0 * ay
        target = (x0 + ax * (left + right) + ay * (top + bot)) / denom
        res    = self.result[i, j]

        # True residual uses current (post-sweep) neighbor values
        live_T = self.result[i - 1, j]
        live_B = self.result[i + 1, j]
        live_L = self.result[i, j - 1]
        live_R = self.result[i, j + 1]
        live_target = (x0 + ax * (live_L + live_R) + ay * (live_T + live_B)) / denom
        resid = abs(res - live_target)

        line1 = ("target = (x0+ax*(L+R)+ay*(T+B)) / (1+2ax+2ay) = %.4f" % target)
        line2 = ("  x0=%.2f ax=%.2f ay=%.2f  T=%.2f B=%.2f L=%.2f R=%.2f"
                 % (x0, ax, ay, top, bot, left, right))
        line3 = ("new = w*target+(1-w)*old = %.3f*%.4f+%.3f*%.4f = %.4f"
                 % (w, target, 1.0 - w, old, res))
        line4 = ("resid = |result-live_target| = %.4e" % resid)

        # T and L were already updated this sweep; B and R came from previous step
        nbrs_new  = [(i - 1, j), (i, j - 1)]
        nbrs_prev = [(i + 1, j), (i, j + 1)]
        return "%s\n%s\n%s\n%s" % (line1, line2, line3, line4), nbrs_new, nbrs_prev

    # ----------------------------------------------------------------- private

    def _reset_snapshots(self):
        r, c = self.rows, self.cols
        self.last_neighbors = np.zeros((r, c, 4))
        self.last_old       = np.zeros((r, c))
