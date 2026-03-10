from src.agents.collector_agent import CollectorAgent

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
