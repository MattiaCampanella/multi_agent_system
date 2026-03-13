import json
import sys
import os
from src.agents.scout_agent import ScoutAgent
from src.agents.collector_agent import CollectorAgent
from src.agents.base_agent import communicate_all
from src.agents.hybrid_agent import HybridAgent

# ---- Configurazione ----
CONFIGURATION = "1 Hybrid"
LAYOUT = "A"          # "A", "B"
MAP= False
VIS_RANGE   = 3
COMM_RANGE  = 2
INIT_BATTERY = 500
NUM_SCOUTS  = 2
NUM_COLLECTORS = 2
NUM_HYBRIDS = 1
SIM_SPEED   = 10      # ticks per second (local only)
MAX_TICKS = 750
FOG_OF_WAR  = True    # nebbia di guerra (local only)

# ---- Session Target ----
# "local"      — interactive pygame window with real-time visualisation and
#                keyboard controls (ESC / SPACE / F).  Requires a display.
# "background" — headless execution: no window is opened; the simulation runs
#                at full speed and saves metrics to results/.  Ideal for batch
#                runs or automated testing on machines without a display.
# "cloud"      — same as "background" but prints a brief per-tick progress
#                line to stdout, making it easier to monitor long runs in
#                streaming cloud logs (e.g. GitHub Actions, CI pipelines).
SESSION_TARGET = "local"   # "local" | "background" | "cloud"

config_file = os.path.join("layouts", f"{LAYOUT}.json")
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


# --- Per-step metrics ---
step_objects_found   = []   # cumulative objects picked up at each tick
step_avg_battery_used = []  # avg battery consumed across all agents at each tick

# ============================================================
# LOCAL session target — interactive pygame window
# ============================================================
if SESSION_TARGET == "local":
    import pygame
    from src.visualize_environment import visualize, CELL_SIZE, LEGEND_WIDTH

    pygame.init()
    grid_px = n * CELL_SIZE
    screen  = pygame.display.set_mode((grid_px + LEGEND_WIDTH, grid_px))
    pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}")
    clock   = pygame.time.Clock()

    running = True
    paused  = False
    ticks = 0
    while running and ticks < MAX_TICKS and (objects or any(a.carrying for a in (collectors + hybrids))):
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
        data["objects"] = list(objects)  # Objects is a dynamic set, update data for visualization
        visualize(data, agents=agents, surface=screen, fog_of_war=FOG_OF_WAR)
        pygame.display.flip()
        clock.tick(SIM_SPEED)

    pygame.quit()

# ============================================================
# BACKGROUND / CLOUD session targets — headless execution
# ============================================================
else:
    ticks = 0
    while ticks < MAX_TICKS and (objects or any(a.carrying for a in (collectors + hybrids))):
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

        # cloud: emit a brief progress line every 50 ticks so streaming logs
        # show liveness without flooding the output.
        if SESSION_TARGET == "cloud" and ticks % 50 == 0:
            collected = initial_object_count - len(objects)
            print(f"[tick {ticks:4d}] objects collected: {collected}/{initial_object_count}", flush=True)


# --- Save per-step metrics ---
metrics = {
    "configuration": CONFIGURATION + ("MAP" if MAP else ""),
    "layout": LAYOUT,
    "max_ticks": MAX_TICKS,
    "ticks_run": ticks,
    "initial_objects": initial_object_count,
    "step_objects_found": step_objects_found,
    "step_avg_battery_used": step_avg_battery_used,
}
os.makedirs("results", exist_ok=True)
metrics_file = os.path.join("results", f"metrics_{CONFIGURATION}" + (" MAP" if MAP else "") + f"-{LAYOUT}.json")
with open(metrics_file, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"\nMetrics saved to '{metrics_file}'")

# --- Summary ---
# Gli oggetti vengono rimossi dalla lista globale al momento del pickup:
# (initial - rimasti) = raccolti; sottraendo chi sta ancora trasportando si ottengono i consegnati.
total_delivered = (initial_object_count - len(objects)) - sum(
    1 for a in agents if getattr(a, "carrying", False)
)
avg_energy_consumed = sum(INIT_BATTERY - a.battery for a in agents) / len(agents)

print("\n========= SIMULATION SUMMARY =========")
print(f"Ticks:                   {ticks} / {MAX_TICKS}")
print(f"Objects delivered:        {total_delivered} / {initial_object_count}")
print(f"Avg. energy consumed:   {avg_energy_consumed:.1f} / {INIT_BATTERY}")
print("======================================")

sys.exit()
