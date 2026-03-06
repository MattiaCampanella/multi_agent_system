class BaseAgent:
    
    def __init__(self, id, vis_range, comm_range, init_battery, position=(0, 0), grid_size=None):
        self.id = id
        self.vis_range = vis_range
        self.comm_range = comm_range
        self.battery = init_battery
        self.local_map = {}
        self.load = None
        self.position = position # (row, col)
        self.grid_size = grid_size  # (rows, cols) — usato per bloccare uscita dalla mappa
    
    DIRECTIONS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1)
    }

    def _has_line_of_sight(self, target: tuple, grid: list) -> bool:
        """
        Bresenham's line: returns True if no wall lies between
        self.position and target (the target wall itself is visible).
        grid is a 2D list (grid[r][c]).
        """
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        r0, c0 = self.position
        r1, c1 = target
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if r0 < r1 else -1
        sc = 1 if c0 < c1 else -1
        err = dr - dc
        r, c = r0, c0

        while True:
            if (r, c) == (r1, c1):
                return True
            # Intermediate cell is a wall then line of sight blocked
            if (r, c) != (r0, c0) and 0 <= r < rows and 0 <= c < cols and grid[r][c] == 1:
                return False
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc

    def scout(self, grid: list) -> None:
        """
        Updates local_map with cells visible from current position.
        grid is a 2D list (grid[r][c]).
        """
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if self.grid_size is None:
            self.grid_size = (rows, cols)
        r, c = self.position
        for dr in range(-self.vis_range, self.vis_range + 1):
            for dc in range(-self.vis_range, self.vis_range + 1):
                tr, tc = r + dr, c + dc
                if 0 <= tr < rows and 0 <= tc < cols:
                    if self._has_line_of_sight((tr, tc), grid):
                        self.local_map[(tr, tc)] = grid[tr][tc]

    def move(self, direction: str) -> None:
        """
        Moves the agent in the specified direction, if valid.
        """
        if direction in self.DIRECTIONS:
            dr, dc = self.DIRECTIONS[direction]
            r, c = self.position
            nr, nc = r + dr, c + dc
            # bounds check
            if self.grid_size is not None:
                rows, cols = self.grid_size
                if not (0 <= nr < rows and 0 <= nc < cols):
                    return
            if self.local_map.get((nr, nc)) != 1:
                if self.battery > 0:
                    self.battery -= 1
                    self.position = (nr, nc)
                