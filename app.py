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
SIM_SPEED   = 5      # ticks per second
MAX_TICKS = 750

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


# Initial scout to populate local maps and known objects
for agent in agents:
    agent.scout(grid, objects)


# ---- Pygame ----
pygame.init()
grid_px = n * CELL_SIZE
screen  = pygame.display.set_mode((grid_px + LEGEND_WIDTH, grid_px))
pygame.display.set_caption(f"M.A.R.O.N.N.E. - Layout {LAYOUT}")
clock   = pygame.time.Clock()

# --- Main loop ---
running = True
ticks = 0
while running and ticks < MAX_TICKS:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # --- Simulation step ---
    for agent in scouts:
        agent.step(grid, objects)
        ticks += 1
    for agent in collectors:
        agent.step(grid, objects)
        ticks += 1
    communicate_all(agents)

    # --- Visualization ---
    data["objects"] = list(objects)  # Objects is a dinamic set, update data for visualization
    visualize(data, agents=agents, surface=screen)
    pygame.display.flip()
    clock.tick(SIM_SPEED)

pygame.quit()
sys.exit()
