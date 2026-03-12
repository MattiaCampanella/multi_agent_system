import json
import sys
import pygame
import os
from src.visualize_environment import visualize, CELL_SIZE, LEGEND_WIDTH
from src.agents.scout_agent import ScoutAgent
from src.agents.collector_agent import CollectorAgent
from src.agents.base_agent import communicate_all
from src.agents.hybrid_agent import HybridAgent

# ---- Configurazione ----
CONFIGURATION = "5 hybrids MAP"
LAYOUT = "B"          # "A", "B"
MAP=True
VIS_RANGE   = 3
COMM_RANGE  = 2
INIT_BATTERY = 500
NUM_SCOUTS  = 0
NUM_COLLECTORS = 0
NUM_HYBRIDS = 5
SIM_SPEED   = 10      # ticks per second
MAX_TICKS = 750
FOG_OF_WAR  = True    # nebbia di guerra

config_file = f"layouts\\{LAYOUT}.json"
with open(config_file, "r") as f:
    data = json.load(f)

grid = data["grid"]
n    = data["metadata"]["grid_size"]
warehouses = data["warehouses"]
objects = [tuple(pos) for pos in data.get("objects", [])]

scouts = [
    ScoutAgent(
        id=i,
        vis_range=VIS_RANGE,
        comm_range=COMM_RANGE,
        init_battery=INIT_BATTERY,
    )
    for i in range(NUM_SCOUTS)
]


collectors = [
    CollectorAgent(
        id=NUM_SCOUTS + i,
        vis_range=VIS_RANGE,
        comm_range=COMM_RANGE,
        init_battery=INIT_BATTERY,
    )
    for i in range(NUM_COLLECTORS)
]

hybrids = [
    HybridAgent(
        id=NUM_SCOUTS + NUM_COLLECTORS + i,
        vis_range=VIS_RANGE,
        comm_range=COMM_RANGE,
        init_battery=INIT_BATTERY,
    )
    for i in range(NUM_HYBRIDS)
]

agents = scouts + collectors + hybrids


initial_object_count = len(objects)

# Initial scout to populate local maps and known objects
rows = len(grid)
cols = len(grid[0]) if rows else 0

if MAP:
    # Agenti conoscono la struttura della mappa (muri, magazzini, ingressi, uscite)
    # ma NON le celle vuote (0) e NON gli oggetti
    for agent in agents:
        agent.grid_size = (rows, cols)
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != 0:
                    agent.local_map[(r, c)] = grid[r][c]
        # Collector e Hybrid registrano subito ingressi e uscite
        if hasattr(agent, 'warehouses'):
            for (r, c), cell_val in agent.local_map.items():
                if cell_val == 3 and (r, c) not in agent._known_entrances:
                    agent._known_entrances.add((r, c))
                    agent.warehouses.append({"entrance": (r, c)})
                elif cell_val == 4:
                    agent.known_exits.add((r, c))

# Prima osservazione per registrare oggetti e agenti vicini
for agent in agents:
    agent.scout(grid, objects, agents)


# ---- Pygame ----
pygame.init()
grid_px = n * CELL_SIZE
screen  = pygame.display.set_mode((grid_px + LEGEND_WIDTH, grid_px))
pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}")
clock   = pygame.time.Clock()

# --- Per-step metrics ---
step_objects_found   = []   # cumulative objects picked up at each tick
step_avg_battery_used = []  # avg battery consumed across all agents at each tick

# --- Main loop ---
running = True
paused  = False
ticks = 0
while running and ticks < MAX_TICKS and (objects or any(a.carrying for a in collectors)):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_f:
                FOG_OF_WAR = not FOG_OF_WAR
            elif event.key == pygame.K_SPACE:
                paused = not paused

    if paused:
        pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}  [PAUSA]")
        clock.tick(SIM_SPEED)
        continue
    else:
        pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}")

    # --- Simulation step ---
    for agent in agents:
        agent.step(grid, objects, agents, current_tick=ticks)
        for i in range(len(agents)):
            agent.communicate(agents[i])
    ticks += 1

    # --- Record metrics ---
    step_objects_found.append(initial_object_count - len(objects))
    step_avg_battery_used.append(
        sum(INIT_BATTERY - a.battery for a in agents) / len(agents)
    )

    # --- Visualization ---
    data["objects"] = list(objects)  # Objects is a dinamic set, update data for visualization
    visualize(data, agents=agents, surface=screen, fog_of_war=FOG_OF_WAR)
    pygame.display.flip()
    clock.tick(SIM_SPEED)

pygame.quit()

# --- Save per-step metrics ---
metrics = {
    "configuration": CONFIGURATION,
    "layout": LAYOUT,
    "max_ticks": MAX_TICKS,
    "ticks_run": ticks,
    "initial_objects": initial_object_count,
    "step_objects_found": step_objects_found,
    "step_avg_battery_used": step_avg_battery_used,
}
os.makedirs("results", exist_ok=True)
metrics_file = f"results\\metrics_{CONFIGURATION}-{LAYOUT}.json"
with open(metrics_file, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"\nMetrics saved to '{metrics_file}'")

# --- Summary ---
total_delivered = sum(
    len(a.collected_objects) - (1 if a.carrying else 0)
    for a in collectors
)
avg_energy_consumed = sum(INIT_BATTERY - a.battery for a in agents) / len(agents)

print("\n========= SIMULATION SUMMARY =========")
print(f"Ticks:                   {ticks} / {MAX_TICKS}")
print(f"Objects delivered:        {total_delivered} / {initial_object_count}")
print(f"Avg. energy consumed:   {avg_energy_consumed:.1f} / {INIT_BATTERY}")
print("======================================")

sys.exit()
