"""Data-free explanatory figure: three observation-equivalent worlds and Settle's horizon.
    python paper/figures_static.py   -> paper/figures/fig_worlds.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

P = Path(__file__).resolve().parent
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"


def main():
    fig, ax = plt.subplots(figsize=(7.4, 2.6), dpi=300)
    worlds = [("lost reply", 0.4, "committed, reply lost"), ("never arrived", None, "never executed"),
              ("late commit", 12.0, "executes after the\nclient gave up")]
    deadline, delta, lag = 4.0, 20.0, 1.0
    for i, (name, commit, hidden) in enumerate(worlds):
        y = len(worlds) - 1 - i
        ax.plot([0, 26], [y, y], color=GRID, linewidth=1, zorder=0)
        ax.plot(0, y, "o", color=INK2, markersize=5, zorder=3)
        ax.annotate("", xy=(deadline, y), xytext=(0, y),
                    arrowprops=dict(arrowstyle="-", color=INK2, linewidth=2), zorder=2)
        ax.plot(deadline, y, "x", color=ORANGE, markersize=7, markeredgewidth=2, zorder=3)
        if commit is not None:
            ax.plot(commit, y, "s", color=BLUE, markersize=6, zorder=4)
        ax.text(-0.6, y, name, ha="right", va="center", fontsize=7.5, color=INK)
        ax.text(26.3, y, hidden, ha="left", va="center", fontsize=6.5, color=MUTED)
    ax.axvspan(0, deadline, color="#f0efec", zorder=-1)
    ax.text(deadline / 2, 2.55, "what the agent sees:\nthe same timeout", ha="center", va="bottom", fontsize=6.5,
            color=INK2)
    ax.axvline(delta + lag, color=BLUE, linewidth=1.2, linestyle=(0, (3, 2)))
    ax.text(delta + lag + 0.3, 2.55, "Settle's horizon  t + Δ + λ:\ncount effects by tag;\nre-issue if 0, compensate if > 1",
            ha="left", va="bottom", fontsize=6.5, color=BLUE)
    ax.plot([], [], "o", color=INK2, label="dispatch")
    ax.plot([], [], "x", color=ORANGE, markeredgewidth=2, label="tool deadline (timeout)")
    ax.plot([], [], "s", color=BLUE, label="effect created (hidden)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.36), ncol=3, fontsize=6.5, frameon=False)
    ax.set_xlim(-0.5, 26)
    ax.set_ylim(-0.6, 3.4)
    ax.set_yticks([])
    ax.set_xticks([0, 4, 12, 21])
    ax.set_xticklabels(["0", "4 s", "12 s", "21 s"], fontsize=7, color=INK2)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    fig.tight_layout()
    fig.subplots_adjust(left=0.15, right=0.74, bottom=0.25)
    (P / "figures").mkdir(exist_ok=True)
    fig.savefig(P / "figures" / "fig_worlds.png")


if __name__ == "__main__":
    main()
