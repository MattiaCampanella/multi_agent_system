import json
import sys
import pygame
from src.visualize_environment import visualize, CELL_SIZE, LEGEND_WIDTH
from src.agents.base_agent import BaseAgent

# ---- Configurazione ----
LAYOUT = "A"          # "A", "B"
VIS_RANGE   = 2
COMM_RANGE  = 1
INIT_BATTERY = 500
NUM_AGENTS  = 5
SIM_SPEED   = 10      # ticks per second

config_file = f"layouts\\{LAYOUT}.json"
with open(config_file, "r") as f:
    data = json.load(f)

grid = data["grid"]
n    = data["metadata"]["grid_size"]

# ---- Spawn agenti sulle prime NUM_AGENTS celle libere ----
spawn_positions = []
for r in range(n):
    for c in range(n):
        if grid[r][c] == 0:
            spawn_positions.append((r, c))
        if len(spawn_positions) == NUM_AGENTS:
            break
    if len(spawn_positions) == NUM_AGENTS:
        break

agents = [
    BaseAgent(
        id=i,
        vis_range=VIS_RANGE,
        comm_range=COMM_RANGE,
        init_battery=INIT_BATTERY,
        position=spawn_positions[i],
    )
    for i in range(NUM_AGENTS)
]

# scout iniziale
for agent in agents:
    agent.scout(grid)


# ---- Pygame ----
pygame.init()
grid_px = n * CELL_SIZE
screen  = pygame.display.set_mode((grid_px + LEGEND_WIDTH, grid_px))
pygame.display.set_caption(f"MARNE — Layout {LAYOUT}")
clock   = pygame.time.Clock()

# Movimento agente 0 con frecce / WASD
KEY_DIR = {
    pygame.K_UP:    "up",    pygame.K_w: "up",
    pygame.K_DOWN:  "down",  pygame.K_s: "down",
    pygame.K_LEFT:  "left",  pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
}

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            
            direction = KEY_DIR.get(event.key)
            if direction:
                agents[0].move(direction)
                agents[0].scout(grid)

    visualize(data, agents=agents, surface=screen)
    pygame.display.flip()
    clock.tick(SIM_SPEED)

pygame.quit()
sys.exit()
