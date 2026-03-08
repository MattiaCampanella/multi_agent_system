from collections import deque
from src.agents.base_agent import BaseAgent

# Costanti cella
EMPTY = 0
WALL = 1
WAREHOUSE = 2
ENTRANCE = 3
EXIT = 4

# Stati del CollectorAgent
EXPLORING  = "exploring"
TARGETING  = "targeting"
DELIVERING = "delivering"
EXITING    = "exiting"


class CollectorAgent(BaseAgent):
    def __init__(self, id, vis_range, comm_range, init_battery, grid_size=None):
        super().__init__(id=id, vis_range=vis_range, comm_range=comm_range,
                         init_battery=init_battery, grid_size=grid_size)
        self.carrying = False
        self.target = None                    # Posizione oggetto da raccogliere
        self.warehouses = []                  # Warehouse scoperti (lista di dict {"entrance": (r,c)})
        self._known_entrances: set = set()    # Set ausiliario per evitare duplicati
        self.known_exits: set = set()         # Uscite warehouse scoperte
        self.state = EXPLORING

    # ------------------------------------------------------------------
    # Scout (override)
    # ------------------------------------------------------------------
    def scout(self, grid: list, objects: list = None, agents: list = None, current_tick: int = 0) -> None:
        """
        Estende BaseAgent.scout(): dopo aver aggiornato local_map e known_objects,
        individua le celle ENTRANCE (3) visibili e le aggiunge a self.warehouses.
        """
        super().scout(grid, objects, agents, current_tick=current_tick)

        for (r, c), cell_val in self.local_map.items():
            if cell_val == ENTRANCE and (r, c) not in self._known_entrances:
                self._known_entrances.add((r, c))
                self.warehouses.append({"entrance": (r, c)})
            elif cell_val == EXIT:
                self.known_exits.add((r, c))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _bfs_to_nearest_frontier(self) -> str | None:
        """
        BFS da self.position attraverso celle note e percorribili.
        Restituisce la direzione del primo passo verso la cella di frontiera
        più vicina (cella nota e percorribile che confina con almeno una cella
        incognita nei limiti della mappa), oppure None se non raggiungibile.
        """
        if self.grid_size is None:
            return None
        rows, cols = self.grid_size

        queue: deque = deque()
        queue.append((self.position, None))   # (cella, prima_direzione_presa)
        visited: set = {self.position}

        while queue:
            (r, c), first_dir = queue.popleft()

            # Verifica se questa cella è una frontiera (non per la posizione iniziale)
            if (r, c) != self.position:
                for dr, dc in self.DIRECTIONS.values():
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in self.local_map and 0 <= nr < rows and 0 <= nc < cols:
                        return first_dir  # trovata frontiera più vicina

            # Espandi vicini attraverso celle note e percorribili
            for direction, (dr, dc) in self.DIRECTIONS.items():
                nr, nc = r + dr, c + dc
                if (nr, nc) in visited:
                    continue
                cell_val = self.local_map.get((nr, nc))
                if cell_val is None or cell_val == 1:
                    continue  # muro o incognita: non si può transitare
                visited.add((nr, nc))
                step = first_dir if first_dir is not None else direction
                queue.append(((nr, nc), step))

        return None  # nessuna frontiera raggiungibile
                
    def _bfs_to_position(self, goal: tuple) -> str | None:
        """
        BFS da self.position verso goal attraverso celle note e percorribili.
        Restituisce la direzione del primo passo, oppure None se irraggiungibile.
        """
        if goal is None:
            return None

        queue: deque = deque()
        queue.append((self.position, None))
        visited: set = {self.position}

        while queue:
            (r, c), first_dir = queue.popleft()

            if (r, c) == goal:
                return first_dir

            for direction, (dr, dc) in self.DIRECTIONS.items():
                nr, nc = r + dr, c + dc
                if (nr, nc) in visited:
                    continue
                cell_val = self.local_map.get((nr, nc))
                if cell_val is None or cell_val == 1:
                    continue
                visited.add((nr, nc))
                step = first_dir if first_dir is not None else direction
                queue.append(((nr, nc), step))

        return None

    def _closest_known_object(self) -> tuple | None:
        """
        Restituisce l'oggetto in known_objects più vicino (distanza di Manhattan).
        """
        if not self.known_objects:
            return None
        r, c = self.position
        return min(self.known_objects, key=lambda pos: abs(pos[0] - r) + abs(pos[1] - c))

    def _closest_warehouse_entrance(self) -> tuple | None:
        """
        Restituisce la cella entrance del warehouse più vicino (distanza di Manhattan).
        """
        if not self.warehouses:
            return None
        r, c = self.position
        return min(
            (tuple(w["entrance"]) for w in self.warehouses),
            key=lambda pos: abs(pos[0] - r) + abs(pos[1] - c),
        )

    def _closest_exit(self) -> tuple | None:
        """
        Restituisce la cella EXIT più vicina (distanza di Manhattan).
        """
        if not self.known_exits:
            return None
        r, c = self.position
        return min(self.known_exits, key=lambda pos: abs(pos[0] - r) + abs(pos[1] - c))

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------
    def step(self, grid: list, objects: list = None, agents: list = None, current_tick: int = 0) -> None:
        """
        Un tick del collector:
        - EXPLORING: esplora le frontiere con BFS; se scopre un oggetto (e c'è
          almeno un warehouse noto) passa a TARGETING.
        - TARGETING: naviga verso l'oggetto bersaglio con BFS.
        """
        self.scout(grid, objects, agents, current_tick=current_tick)

        if self.state == EXPLORING:
            if self.known_objects and self.warehouses and not self.carrying:
                self.state = TARGETING
                self.target = self._closest_known_object()
                return
            direction = self._bfs_to_nearest_frontier()
            if direction is not None:
                self.move(direction)

        elif self.state == TARGETING:
            # Se il target non è più nella lista degli oggetti (raccolto da altri),
            # torna a esplorare per sceglierne uno nuovo
            if objects is not None and self.target not in objects:
                self.known_objects.discard(self.target)
                self.target = self._closest_known_object()
                if self.target is None:
                    self.state = EXPLORING
                    return

            # Siamo sull'oggetto: raccoglilo e punta all'entrance più vicina
            if self.position == self.target:
                if objects is not None:
                    try:
                        objects.remove(self.target)
                    except ValueError:
                        pass
                self.known_objects.discard(self.target)
                self.collected_objects.add(self.target)
                self.carrying = True
                self.target = self._closest_warehouse_entrance()
                self.state = DELIVERING
                return

            direction = self._bfs_to_position(self.target)
            if direction is not None:
                self.move(direction)

        elif self.state == DELIVERING:
            # Naviga verso l'entrance; quando ci arriva consegna e punta all'uscita
            if self.position == self.target:
                self.carrying = False
                exit_pos = self._closest_exit()
                self.target = exit_pos
                self.state = EXITING
                return
            direction = self._bfs_to_position(self.target)
            if direction is not None:
                self.move(direction)

        elif self.state == EXITING:
            # Naviga verso la cella EXIT; quando ci arriva sceglie il prossimo stato
            if self.position == self.target:
                if self.known_objects:
                    self.state = TARGETING
                    self.target = self._closest_known_object()
                else:
                    self.state = EXPLORING
                    self.target = None
                return
            direction = self._bfs_to_position(self.target)
            if direction is not None:
                self.move(direction)


