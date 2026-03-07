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

    def step(self, grid: list, objects: list = None) -> None:
        """
        Un tick di esplorazione frontier-based:
        1. scout() — aggiorna local_map e known_objects.
        2. BFS verso la frontiera più vicina.
        3. Muove di un passo in quella direzione.
        """
        self.scout(grid, objects)
        direction = self._bfs_to_nearest_frontier()
        if direction is not None:
            self.move(direction)
