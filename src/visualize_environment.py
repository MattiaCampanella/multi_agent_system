"""
Visualizza un ambiente usando pygame.
"""

import pygame
from src.agents.collector_agent import CollectorAgent as _CollectorAgent

# Costanti cella
EMPTY = 0
WALL = 1
WAREHOUSE = 2
ENTRANCE = 3
EXIT = 4

# Colori (R, G, B)
COLOR_MAP = {
    EMPTY:     (255, 255, 255),
    WALL:      ( 64,  64,  64),
    WAREHOUSE: ( 74, 144, 217),
    ENTRANCE:  ( 46, 204, 113),
    EXIT:      (231,  76,  60),
}
COLOR_OBJECT = (255, 165,   0)
COLOR_GRID   = (200, 200, 200)
COLOR_BG     = (240, 240, 240)

AGENT_COLOR_SCOUT     = ( 52, 152, 219)   # blu
AGENT_COLOR_COLLECTOR = (231,  76,  60)   # rosso

LEGEND_ITEMS = [
    (COLOR_MAP[WALL],      "Wall"),
    (COLOR_MAP[WAREHOUSE], "Warehouse"),
    (COLOR_MAP[ENTRANCE],  "Entrance"),
    (COLOR_MAP[EXIT],      "Exit"),
    (COLOR_MAP[EMPTY],        "Corridor"),
    (COLOR_OBJECT,            "Object"),
    (AGENT_COLOR_SCOUT,       "Scout"),
    (AGENT_COLOR_COLLECTOR,   "Collector"),
]

LEGEND_WIDTH = 180
CELL_SIZE    = 28


def visualize(data: dict, agents: list = None, surface: pygame.Surface = None) -> pygame.Surface:
    """
    Disegna l'ambiente (e opzionalmente gli agenti) su una pygame.Surface.
    Se surface è None ne crea una nuova e la restituisce.
    """
    grid       = data["grid"]
    warehouses = data["warehouses"]
    objects    = data.get("objects", [])
    n          = data["metadata"]["grid_size"]

    grid_px  = n * CELL_SIZE
    win_w    = grid_px + LEGEND_WIDTH
    win_h    = grid_px

    if surface is None:
        surface = pygame.Surface((win_w, win_h))

    surface.fill(COLOR_BG)

    # --- frecce direzione entrate/uscite ---
    arrow_map = {}
    for w in warehouses:
        side = w["side"]
        er, ec = w["entrance"]
        xr, xc = w["exit"]
        if side == "top":
            arrow_map[(er, ec)] = "\u25B2"; arrow_map[(xr, xc)] = "\u25BC"
        elif side == "bottom":
            arrow_map[(er, ec)] = "\u25BC"; arrow_map[(xr, xc)] = "\u25B2"
        elif side == "left":
            arrow_map[(er, ec)] = "\u25C0"; arrow_map[(xr, xc)] = "\u25B6"
        else:
            arrow_map[(er, ec)] = "\u25B6"; arrow_map[(xr, xc)] = "\u25C0"

    font_arrow  = pygame.font.SysFont("segoeuisymbol", CELL_SIZE - 6, bold=True)
    font_agent  = pygame.font.SysFont("arial", CELL_SIZE - 10, bold=True)
    font_legend = pygame.font.SysFont("arial", 13)

    # --- celle ---
    for r in range(n):
        for c in range(n):
            val   = grid[r][c]
            color = COLOR_MAP.get(val, COLOR_MAP[EMPTY])
            rect  = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLOR_GRID, rect, 1)

            if (r, c) in arrow_map:
                txt = font_arrow.render(arrow_map[(r, c)], True, (255, 255, 255))
                surface.blit(txt, txt.get_rect(center=rect.center))

    # --- oggetti ---
    for obj in objects:
        obj_r, obj_c = obj
        cx = obj_c * CELL_SIZE + CELL_SIZE // 2
        cy = obj_r * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, COLOR_OBJECT, (cx, cy), CELL_SIZE // 3)

    # --- agenti ---
    for agent in (agents or []):
        ar, ac = agent.position
        color  = AGENT_COLOR_COLLECTOR if isinstance(agent, _CollectorAgent) else AGENT_COLOR_SCOUT
        cx = ac * CELL_SIZE + CELL_SIZE // 2
        cy = ar * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, color, (cx, cy), CELL_SIZE // 2 - 2)
        lbl = font_agent.render(str(agent.id), True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

    # --- legenda ---
    lx = grid_px + 8
    ly = 10
    for color, label in LEGEND_ITEMS:
        pygame.draw.rect(surface, color, (lx, ly, 16, 16))
        pygame.draw.rect(surface, (0, 0, 0), (lx, ly, 16, 16), 1)
        txt = font_legend.render(label, True, (30, 30, 30))
        surface.blit(txt, (lx + 22, ly))
        ly += 24

    return surface

