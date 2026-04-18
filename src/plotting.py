from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from triggers import theta_from_current


def save_comparison_plot(no_trigger: pd.DataFrame, with_trigger: pd.DataFrame, supermag: pd.DataFrame | None, substorms: dict[str, pd.DataFrame] | None, output_path: str | Path, title: str) -> Path:
    output_path = Path(output_path)
    if supermag is None:
        supermag = pd.DataFrame()
    if substorms is None:
        substorms = {}
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(no_trigger.index, no_trigger["I"], label="No Trigger")
    axes[0].plot(with_trigger.index, with_trigger["I"], label="With Trigger")
    if "I_c" in with_trigger.columns:
        axes[0].plot(with_trigger.index, with_trigger["I_c"], linestyle="--", label="I_c")
    axes[0].set_ylabel("I")
    axes[0].set_title(title)
    axes[0].legend(loc="upper left")

    if "I_c" in with_trigger.columns:
        theta = theta_from_current(with_trigger["I"], with_trigger["I_c"])
        axes[1].fill_between(theta.index, 0.0, theta.values, alpha=0.4, label="Theta")
        axes[1].legend(loc="upper left")

    for ts in substorms.get("Newell", pd.DataFrame()).index:
        axes[1].axvline(ts, linestyle="--", c = 'gray', alpha=0.5)
    for ts in substorms.get("Ohtani", pd.DataFrame()).index:
        axes[1].axvline(ts, linestyle=":", c = 'red', alpha=0.5)

    axes[1].set_ylabel("Theta")
    axes[1].set_xlabel("Time")

    ax2 = axes[1].twinx()
    if not supermag.empty and "SML" in supermag.columns:
        ax2.plot(supermag.index, supermag["SML"], c='purple', alpha=0.6)
    ax2.set_ylabel("SML (nT)", color='purple')
    ax2.tick_params(axis='y', color='purple')
    ax2.spines['right'].set_color('purple')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path

def plot_state_variables(with_trigger: pd.DataFrame, output_path: str | Path) -> Path:
    output_path = Path(output_path)

    vars_to_plot = ["I", "V", "I1", "VI", "pres", "Kk", "I2", "Wrc"]

    titles = {
        "I": "Cross-tail Current",
        "V": "Magnetospheric Potential",
        "I1": "Region-1 Current",
        "VI": "Ionospheric Potential",
        "pres": "Plasma Sheet Pressure",
        "Kk": "Plasma Sheet Kinetic Energy",
        "I2": "Region-2 / Ring Current",
        "Wrc": "Ring Current Energy",
    }

    ylabels = {
        "I": "I",
        "V": "V",
        "I1": "I1",
        "VI": "VI",
        "pres": "Pressure",
        "Kk": "Kinetic Energy",
        "I2": "I2",
        "Wrc": "Energy",
    }

    fig, axes = plt.subplots(4, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    time = with_trigger["time"] if "time" in with_trigger.columns else with_trigger.index

    for i, var in enumerate(vars_to_plot):
        ax = axes[i]
        ax.plot(time, with_trigger[var])
        ax.set_title(titles[var])
        ax.set_ylabel(ylabels[var])
        ax.grid(True)

    axes[-1].set_xlabel("Time")
    axes[-2].set_xlabel("Time")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path