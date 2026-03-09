import json
import sys
import pygame
from src.visualize_environment import visualize, CELL_SIZE, LEGEND_WIDTH
from src.agents.scout_agent import ScoutAgent
from src.agents.collector_agent import CollectorAgent
from src.agents.base_agent import communicate_all
    
# ---- Configurazione ----
LAYOUT = "A"          # "A", "B"
VIS_RANGE   = 3
COMM_RANGE  = 2
INIT_BATTERY = 500
NUM_SCOUTS  = 3
NUM_COLLECTORS = 2
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

agents = scouts + collectors


initial_object_count = len(objects)

# Initial scout to populate local maps and known objects
for agent in agents:
    agent.scout(grid, objects, agents)


# ---- Pygame ----
pygame.init()
grid_px = n * CELL_SIZE
screen  = pygame.display.set_mode((grid_px + LEGEND_WIDTH, grid_px))
pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}")
clock   = pygame.time.Clock()

# --- Main loop ---
running = True
paused  = False
ticks = 0
steps = 0
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
    for agent in scouts:
        agent.step(grid, objects, agents, current_tick=ticks)
        ticks += 1
    for agent in collectors:
        agent.step(grid, objects, agents, current_tick=ticks)
        ticks += 1
    communicate_all(agents)
    steps += 1

    # --- Visualization ---
    data["objects"] = list(objects)  # Objects is a dinamic set, update data for visualization
    visualize(data, agents=agents, surface=screen, fog_of_war=FOG_OF_WAR)
    pygame.display.flip()
    clock.tick(SIM_SPEED)

pygame.quit()

# --- Summary ---
total_delivered = sum(
    len(a.collected_objects) - (1 if a.carrying else 0)
    for a in collectors
)
avg_energy_consumed = sum(INIT_BATTERY - a.battery for a in agents) / len(agents)

print("\n========= SIMULATION SUMMARY =========")
print(f"Ticks:                   {ticks} / {MAX_TICKS}")
print(f"Steps per agent:         {steps} / {MAX_TICKS // len(agents)}")
print(f"Objects delivered:        {total_delivered} / {initial_object_count}")
print(f"Avg. energy consumed:   {avg_energy_consumed:.1f} / {INIT_BATTERY}")
print("======================================")

sys.exit()
