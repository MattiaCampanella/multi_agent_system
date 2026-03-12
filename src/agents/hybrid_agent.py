from src.agents.collector_agent import CollectorAgent
from collections import deque

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

class HybridAgent(CollectorAgent):

    #------------------------------------------------------------------
    # Navigation (override)
    #------------------------------------------------------------------
    def _bfs_to_nearest_frontier(self) -> str | None:
        """
        BFS da self.position attraverso celle note e percorribili.
        Raccoglie tutte le celle di frontiera raggiungibili con il relativo
        punteggio (distanza BFS), le ordina per punteggio crescente e
        restituisce la direzione del primo passo verso quella con punteggio
        minore. Restituisce None se nessuna frontiera è raggiungibile.
        """
        if self.grid_size is None:
            return None
        rows, cols = self.grid_size

        # (cella, prima_direzione_presa, distanza)
        queue: deque = deque()
        queue.append((self.position, None, 0))
        visited: set = {self.position}

        # Lista di tutte le frontiere trovate: (distanza, prima_direzione)
        frontier_candidates: list = []

        while queue:
            (r, c), first_dir, dist = queue.popleft()

            # Verifica se questa cella è una frontiera (non per la posizione iniziale)
            if (r, c) != self.position:
                for dr, dc in self.DIRECTIONS.values():
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in self.local_map and 0 <= nr < rows and 0 <= nc < cols:
                        # Calcola la distanza minima dagli altri agenti noti
                        if self.known_agents:
                            min_agent_dist = min(
                                abs(r - ar) + abs(c - ac)
                                for (ar, ac), _ in self.known_agents.values()
                            )
                        else:
                            min_agent_dist = 0
                        # Frontiere lontane dagli altri agenti ottengono score minore (preferite)
                        score = dist - min_agent_dist
                        frontier_candidates.append((score, first_dir))
                        break # basta trovare una cella adiacente incognita per essere frontiera

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
                queue.append(((nr, nc), step, dist + 1))

        if not frontier_candidates:
            return None  # nessuna frontiera raggiungibile

        # Ordina per punteggio (distanza) crescente e scegli quella con punteggio minore
        frontier_candidates.sort(key=lambda x: x[0])
        best_score, best_dir = frontier_candidates[0]
        return best_dir

    def step(self, grid: list, objects: list = None, agents: list = None, current_tick: int = 0) -> None:
        """
        Un tick del collector:
        - EXPLORING: esplora le frontiere con BFS; se scopre 10 oggetti (e c'è
          almeno un warehouse noto) passa a TARGETING.
        - TARGETING: naviga verso l'oggetto bersaglio con BFS.
        """
        self.scout(grid, objects, agents, current_tick=current_tick)

        if self.state == EXPLORING:
            if len(self.known_objects) + len(self.collected_objects) >= 9 and self.warehouses and not self.carrying:
                self.state = TARGETING
                self.target = self._closest_known_object()
                return
            direction = self._bfs_to_nearest_frontier()
            if direction is not None:
                self.move(direction)
            else:
                self.state = TARGETING

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
