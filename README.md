
# M.A.R.O.N.N.E.
### Multi-Agent Recovery, Organization and Network Navigation Engine

A multi-agent simulation built with Python and Pygame in which heterogeneous agents cooperate to explore a grid environment, collect scattered objects, and deliver them to warehouses.

---

## Overview

The simulation runs on a 2D grid loaded from a JSON layout file. Two types of agents operate concurrently:

- **Scout agents** — explore the map using frontier-based BFS, building a shared knowledge of the environment.
- **Collector agents** — navigate toward known objects, pick them up, and deliver them to the nearest warehouse entrance.

Agents communicate within a configurable range, exchanging local maps and object locations in real time.

---

## Project Structure

```
multi_agent_system/
├── app.py                        # Entry point — configuration, simulation loop
├── requirements.txt
├── layouts/                      # 25x25 grids, 10 objects, 4 warehouses
│   ├── A.json                    # Layout A
│   └── B.json                    # Layout B
└── src/
    ├── visualize_environment.py  # Pygame rendering
    └── agents/
        ├── base_agent.py         # BaseAgent: movement, vision, communication
        ├── scout_agent.py        # ScoutAgent: frontier-based exploration
        └── collector_agent.py    # CollectorAgent: pick-up and delivery
```

---

## Agents

### BaseAgent
Core class shared by all agents. Provides:
- **Line-of-sight** via Bresenham's line algorithm
- **`scout()`** — updates `local_map` and `known_objects` within visual range
- **`move()`** — moves the agent one cell towards given direction, consuming 1 battery unit per step
- **`communicate()`** — bidirectional exchange of `local_map`, `known_objects`, and `known_agents` with any agent within communication range (Chebyshev distance)

### ScoutAgent
Specialised for exploration. Each tick:
1. Updates the local map via `scout()`.
2. Runs a BFS toward the nearest **frontier cell** (a known, passable cell adjacent to an unknown cell), preferring frontiers far from other known agents.

### CollectorAgent
Operates as a finite state machine with four states:

| State | Behaviour |
|---|---|
| `EXPLORING` | BFS toward nearest frontier, like a scout |
| `TARGETING` | BFS toward the closest known object to collect it |
| `DELIVERING` | BFS toward the nearest warehouse entrance |
| `EXITING` | Navigates to the warehouse exit cell after delivery |

---

## Communication

After every simulation step, `communicate_all()` iterates over all agent pairs. Two agents exchange information when their communication ranges overlap (Chebyshev distance ≤ sum of their `comm_range` values). The exchange merges:
- local maps (`local_map`)
- known object positions (`known_objects`), **excluding already-collected ones**
- known agent positions (`known_agents`)

---

## Configuration

All parameters are set at the top of `app.py`:

| Parameter | Default | Description |
|---|---|---|
| `LAYOUT` | `"A"` | Layout file to load (`"A"` or `"B"`) |
| `VIS_RANGE` | `3` | Visual range of each agent (cells) |
| `COMM_RANGE` | `2` | Communication range of each agent (cells) |
| `INIT_BATTERY` | `500` | Starting battery for each agent |
| `NUM_SCOUTS` | `3` | Number of scout agents |
| `NUM_COLLECTORS` | `2` | Number of collector agents |
| `SIM_SPEED` | `10` | Simulation speed (ticks per second) |
| `MAX_TICKS` | `750` | Maximum ticks before the simulation stops |

---

## Layout Format

Layouts are JSON files in `layouts/`. Grid cell values:

| Value | Meaning |
|---|---|
| `0` | Empty / passable |
| `1` | Wall |
| `2` | Warehouse interior |
| `3` | Warehouse entrance |
| `4` | Warehouse exit |

---

## Installation

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
python app.py
```

Press **ESC** or close the window to stop early.

At the end of the simulation a summary is printed to the console:

```
========= SIMULATION SUMMARY =========
ticks:                  700/750
Objects delivered:       10 / 10
Avg. energy consumed:  312.4 / 500
```

---

## Dependencies

| Package | Version |
|---|---|
| `pygame` | ≥ 2.1.0 |
| `numpy` | ≥ 1.24.0 |
| `matplotlib` | ≥ 3.7.0 |
