from collections import deque
from src.agents.base_agent import BaseAgent


class ScoutAgent(BaseAgent):
    """
    Agente specializzato nell'esplorazione dell'ambiente tramite
    frontier-based exploration (BFS verso la cella di frontiera più vicina).
    Rileva oggetti nel raggio visivo e li memorizza in known_objects.
    """

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------
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
                                for ar, ac in self.known_agents.values()
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

    def step(self, grid: list, objects: list = None, other_agents: dict = None) -> None:
        """
        Un tick di esplorazione frontier-based:
        1. scout() — aggiorna local_map e known_objects.
        2. BFS verso la frontiera più vicina.
        3. Muove di un passo in quella direzione.
        """
        self.scout(grid, objects, other_agents)
        direction = self._bfs_to_nearest_frontier()
        if direction is not None:
            self.move(direction)
