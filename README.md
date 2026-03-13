
# M.A.R.O.N.N.E.
### Multi-Agent Recovery, Organization and Network Navigation Engine

A multi-agent simulation built with Python and Pygame in which heterogeneous agents cooperate to explore a grid environment, collect scattered objects, and deliver them to warehouses.

---

## Overview

The simulation runs on a 2D grid loaded from a JSON layout file. Three types of agents operate concurrently:

- **Scout agents** — explore the map using frontier-based BFS, building a shared knowledge of the environment.
- **Collector agents** — navigate toward known objects, pick them up, and deliver them to the nearest warehouse entrance.
- **Hybrid agents** — combine exploration and collection in a single agent, switching roles dynamically.

Agents communicate within a configurable range, exchanging local maps and object locations in real time.

At the end of each run, per-step metrics are saved to `results/` as a JSON file and can be plotted with `make_graph.py`.

---

## Project Structure

```
multi_agent_system/
├── app.py                        # Entry point — configuration, simulation loop
├── make_graph.py                 # Plots per-step metrics from results/
├── requirements.txt              # Full dependencies (simulation + graph)
├── graph_requirements.txt        # Minimal dependencies (graph only, no pygame)
├── layouts/                      # 25x25 grids, 10 objects, 4 warehouses
│   ├── A.json                    # Layout A
│   └── B.json                    # Layout B
├── results/                      # Auto-created — metrics JSON files + comparison.png
└── src/
    ├── visualize_environment.py  # Pygame rendering
    └── agents/
        ├── base_agent.py         # BaseAgent: movement, vision, communication
        ├── scout_agent.py        # ScoutAgent: frontier-based exploration
        ├── collector_agent.py    # CollectorAgent: pick-up and delivery
        └── hybrid_agent.py       # HybridAgent: combined scout + collector
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

### HybridAgent
Combines the behaviour of both `ScoutAgent` and `CollectorAgent`. Explores the map autonomously but switches to collection mode when objects are known, then returns to exploration once the delivery is complete.

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
| `CONFIGURATION` | `"2 S + 2 C + 1 H"` | Human-readable label saved in metrics and shown in graph legends |
| `LAYOUT` | `"B"` | Layout file to load (`"A"` or `"B"`) |
| `VIS_RANGE` | `3` | Visual range of each agent (cells) |
| `COMM_RANGE` | `2` | Communication range of each agent (cells) |
| `INIT_BATTERY` | `500` | Starting battery for each agent |
| `NUM_SCOUTS` | `2` | Number of scout agents |
| `NUM_COLLECTORS` | `2` | Number of collector agents |
| `NUM_HYBRIDS` | `1` | Number of hybrid agents |
| `SIM_SPEED` | `10` | Simulation speed (ticks per second, `local` only) |
| `MAX_TICKS` | `750` | Maximum ticks before the simulation stops |
| `FOG_OF_WAR` | `True` | Whether agents only see their explored area (toggle with **F**, `local` only) |
| `SESSION_TARGET` | `"local"` | Execution mode — see [Session Targets](#session-targets) |

---

## Session Targets

`SESSION_TARGET` controls how the simulation is executed.  All three modes
run the **same agent logic** (Scout, Collector, Hybrid) and save identical
metrics JSON files to `results/`.

| Value | Requires display? | Description |
|---|---|---|
| `"local"` | **Yes** | Opens a pygame window with real-time visualisation.  Keyboard shortcuts (ESC / SPACE / F) are active.  Useful for interactive exploration and debugging. |
| `"background"` | No | Headless execution — no window is opened.  The simulation runs at full CPU speed and exits silently after saving metrics.  Ideal for automated batch runs, CI pipelines, or any machine without a display. |
| `"cloud"` | No | Same headless execution as `"background"`, but prints a brief progress line to stdout every 50 ticks so that streaming logs (e.g. GitHub Actions, cloud run logs) stay alive and show liveness. |

### Choosing a session target

```python
# app.py — top of the file
SESSION_TARGET = "local"       # interactive window
# SESSION_TARGET = "background"  # headless, silent
# SESSION_TARGET = "cloud"       # headless, with progress output
```

> **Note** — `SIM_SPEED` and `FOG_OF_WAR` are only meaningful in `"local"`
> mode.  In `"background"` and `"cloud"` mode the simulation runs as fast as
> possible and there is no visual layer to render fog of war.

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

## Metrics & Graphs

At the end of each simulation run, a JSON file is saved to `results/`:

```
results/metrics_<CONFIGURATION>-<LAYOUT>.json
```

The file contains:

```json
{
  "configuration": "No Hybrids 5 Agents",
  "layout": "B",
  "ticks_run": 312,
  "initial_objects": 10,
  "step_objects_found": [0, 0, 1, 1, 2, "..."],
  "step_avg_battery_used": [1.0, 2.0, 3.4, "..."]
}
```

To generate a comparison graph from all saved runs:

```bash
python make_graph.py
```

This reads every `*.json` file in `results/`, overlays them in a dual-panel chart (objects collected + average battery consumed over time), and saves the output as `results/comparison.png`.

Legend labels follow this logic:
- If `CONFIGURATION` is set: **`<configuration> - <layout>`** (e.g. `2 S + 2 C + 1 H - B`)
- If `CONFIGURATION` is empty: just the **layout name**

---

## Installation

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# Install all dependencies (simulation + graph)
pip install -r requirements.txt
```

> **`requirements.txt`** includes `pygame`, `numpy`, and `matplotlib` — everything needed to run both the simulation and the graph tool.
---

## Usage

```bash
python app.py
```

### Local mode (default)

| Key | Action |
|---|---|
| **ESC** | Stop the simulation |
| **SPACE** | Pause / resume |
| **F** | Toggle fog of war |

### Background / Cloud mode

Set `SESSION_TARGET = "background"` or `SESSION_TARGET = "cloud"` at the top of `app.py`.
No pygame window is opened; the simulation runs at full speed.

```bash
python app.py        # SESSION_TARGET = "background" or "cloud" set in app.py
```

At the end of every run (all modes) a summary is printed to the console:

```
========= SIMULATION SUMMARY =========
Ticks:                   312 / 750
Objects delivered:        10 / 10
Avg. energy consumed:   287.4 / 500
======================================

Metrics saved to 'results/metrics_2 S + 2 C + 1 H-B.json'
```

---

## Dependencies

| Package | Used by | Version |
|---|---|---|
| `pygame` | `app.py` | ≥ 2.1.0 |
| `numpy` | `app.py`, `make_graph.py` | ≥ 1.24.0 |
| `matplotlib` | `make_graph.py` | ≥ 3.7.0 |
