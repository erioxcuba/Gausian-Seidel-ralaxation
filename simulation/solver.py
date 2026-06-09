import numpy as np


class GaussSeidelSolver:
    def __init__(self):
        self.rows     = 6
        self.cols     = 6
        self.omega    = 1.0
        self.max_iter = 50

        self.entry  = np.zeros((self.rows, self.cols))
        self.result = np.zeros((self.rows, self.cols))
        self.fixed  = np.zeros((self.rows, self.cols), dtype=bool)

        # Snapshot of inputs used at the last update of each interior cell
        self.last_neighbors = np.zeros((self.rows, self.cols, 4))  # T B L R
        self.last_old       = np.zeros((self.rows, self.cols))

        self.iteration = 0
        self.residuals: list = []
        self.converged = False

        self.initialize()

    # ------------------------------------------------------------------ public

    def initialize(self):
        r, c = self.rows, self.cols
        self.entry  = np.zeros((r, c))
        self.result = np.zeros((r, c))
        self.fixed  = np.zeros((r, c), dtype=bool)

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

        self.result = self.entry.copy()
        self._reset_snapshots()
        self.iteration = 0
        self.residuals = []
        self.converged = False

    def reset(self):
        """Reset result to entry without re-randomizing."""
        self.result = self.entry.copy()
        self._reset_snapshots()
        self.iteration = 0
        self.residuals = []
        self.converged = False

    def set_entry_value(self, i: int, j: int, value: float):
        self.entry[i, j] = float(value)
        self.result[i, j] = float(value)

    def step(self) -> bool:
        """Perform one Gauss-Seidel sweep. Returns False if already finished."""
        if self.converged or self.iteration >= self.max_iter:
            self.converged = True
            return False

        max_res = 0.0
        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                top   = self.result[i - 1, j]
                bot   = self.result[i + 1, j]
                left  = self.result[i, j - 1]
                right = self.result[i, j + 1]
                old   = self.result[i, j]

                self.last_neighbors[i, j] = [top, bot, left, right]
                self.last_old[i, j]       = old

                new = (self.omega * (top + bot + left + right) / 4.0
                       + (1.0 - self.omega) * old)
                self.result[i, j] = new
                diff = abs(new - old)
                if diff > max_res:
                    max_res = diff

        # Boundary cells stay fixed
        self.result[self.fixed] = self.entry[self.fixed]

        self.iteration += 1
        self.residuals.append(max_res)
        if max_res < 1e-8:
            self.converged = True
        return True

    def get_cell_formula(self, i: int, j: int):
        """Return (formula_string, neighbor_index_list) for hover display."""
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            return None, []

        if self.fixed[i, j]:
            return ("u[%d,%d] = %.4f  (boundary - fixed)" % (i, j, self.entry[i, j]), [])

        if self.iteration == 0:
            return ("u[%d,%d] = %.4f  (no iteration yet)" % (i, j, self.result[i, j]), [])

        top, bot, left, right = self.last_neighbors[i, j]
        old = self.last_old[i, j]
        w   = self.omega
        avg = (top + bot + left + right) / 4.0
        res = self.result[i, j]

        line1 = "u[%d,%d] = w*(T+B+L+R)/4 + (1-w)*u_old" % (i, j)
        line2 = ("= %.3f*(%.3f+%.3f+%.3f+%.3f)/4 + %.3f*%.3f"
                 % (w, top, bot, left, right, 1 - w, old))
        line3 = "= %.3f*%.4f + %.4f" % (w, avg, (1 - w) * old)
        line4 = "=> %.5f" % res

        neighbors = [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]
        return "%s\n%s\n%s\n%s" % (line1, line2, line3, line4), neighbors

    # ----------------------------------------------------------------- private

    def _reset_snapshots(self):
        r, c = self.rows, self.cols
        self.last_neighbors = np.zeros((r, c, 4))
        self.last_old       = np.zeros((r, c))
