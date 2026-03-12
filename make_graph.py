import json
import os
import glob
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "results"


def load_metrics(pattern="*.json") -> list[dict]:
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, pattern)))
    metrics = []
    for f in files:
        with open(f, "r") as fp:
            data = json.load(fp)
            data["_file"] = os.path.basename(f)
            metrics.append(data)
    return metrics


def plot_all(metrics: list[dict]):
    if not metrics:
        print("Nessun file trovato in results/")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("Simulation Metrics", fontsize=14, fontweight="bold")

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for i, m in enumerate(metrics):
        color = colors[i % len(colors)]
        layout = m.get("layout", m["_file"].replace("metrics_", "").replace(".json", ""))
        config = m.get("configuration", "").strip()
        label = f"{config} - {layout}" if config else layout
        ticks = list(range(1, m["ticks_run"] + 1))

        ax1.plot(ticks, m["step_objects_found"], color=color, label=label, linewidth=1.8)
        ax2.plot(ticks, m["step_avg_battery_used"], color=color, label=label, linewidth=1.8)

    # --- Objects found ---
    ax1.set_ylabel("Objects collected (cumulative)")
    ax1.set_ylim(bottom=0)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9, loc="lower right")
    for i, m in enumerate(metrics):
        color = colors[i % len(colors)]
        ax1.axhline(m["initial_objects"], color=color, linestyle="--", alpha=0.4, linewidth=1)

    # --- Battery used ---
    ax2.set_ylabel("Avg. battery consumed")
    ax2.set_xlabel("Tick")
    ax2.set_ylim(bottom=0)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9, loc="upper left")
    max_tick = max(m["ticks_run"] for m in metrics)
    ax2.set_xticks(range(0, max_tick + 1, 10))
    init_battery = metrics[0].get("max_battery", 500)
    ax2.axhline(init_battery, color="gray", linestyle="--", alpha=0.4, linewidth=1, label="Max battery")

    plt.tight_layout()
    out_path = os.path.join(RESULTS_DIR, f"comparison.png")
    plt.savefig(out_path, dpi=150)
    print(f"Grafico salvato in '{out_path}'")
    plt.show()


if __name__ == "__main__":
    metrics = load_metrics()
    plot_all(metrics)
