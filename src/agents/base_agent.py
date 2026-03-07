from collections import deque


class BaseAgent:
    
    def __init__(self, id, vis_range, comm_range, init_battery, grid_size=None):
        self.id = id
        self.vis_range = vis_range
        self.comm_range = comm_range
        self.battery = init_battery
        self.local_map = {}
        self.known_objects = set()  # posizioni oggetti rilevati e non ancora raccolti
        self.load = None
        self.position = (0, 0)  # (row, col)
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

    def scout(self, grid: list, objects: list = None) -> None:
        """
        Updates local_map with cells visible from current position.
        If objects is provided, memorizes any object position that falls
        within visual range and has line of sight.
        grid is a 2D list (grid[r][c]).
        objects is a list of (row, col) tuples of object positions.
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

        # Updates known objects if objects are in line of sight
        if objects:
            for obj_pos in objects:
                obj_r, obj_c = obj_pos
                if abs(obj_r - r) <= self.vis_range and abs(obj_c - c) <= self.vis_range:
                    if self._has_line_of_sight((obj_r, obj_c), grid):
                        self.known_objects.add((obj_r, obj_c))

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

    # ------------------------------------------------------------------
    # Communication
    # ------------------------------------------------------------------

    def in_communication_range(self, other: "BaseAgent") -> bool:
        """
        Restituisce True se i raggi di comunicazione dei due agenti si intersecano,
        ovvero se la distanza di Chebyshev tra le loro posizioni è ≤ somma dei raggi.
        """
        r0, c0 = self.position
        r1, c1 = other.position
        distance = max(abs(r0 - r1), abs(c0 - c1))  # distanza di Chebyshev
        return distance <= (self.comm_range + other.comm_range)

    def communicate(self, other: "BaseAgent") -> None:
        """
        Scambia informazioni con un altro agente se i raggi di comunicazione
        si intersecano. Lo scambio è bidirezionale:
        - unione delle mappe locali (local_map)
        - unione degli oggetti rilevati ma non ancora recuperati (known_objects)
        """
        if not self.in_communication_range(other):
            return
        # Unione bidirezionale delle mappe locali
        merged_map = {**other.local_map, **self.local_map}  # self ha priorità
        other.local_map.update(merged_map)
        self.local_map.update(merged_map)
        # Unione bidirezionale degli oggetti noti
        merged_objects = self.known_objects | other.known_objects
        self.known_objects = merged_objects
        other.known_objects = merged_objects


def communicate_all(agents: list) -> None:
    """
    Effettua il passaggio di comunicazione tra tutti gli agenti:
    ogni coppia di agenti entro raggio si scambia mappa e oggetti.
    Da chiamare una volta per tick nel loop di simulazione.
    """
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            agents[i].communicate(agents[j])
