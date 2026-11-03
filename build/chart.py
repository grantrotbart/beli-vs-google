"""
The one image.

    python build/chart.py
    python build/chart.py --with-friends    # adds the anchored second panel

Reads  data/matched.csv
Writes out/beli_vs_google.png

One scatter: Google's rating against my own Beli score. Google's whole 1-5 scale is on
the axis on purpose -- the bunching into one narrow band is the finding, and zooming to
the occupied range would hide it.

The friend-score panel is behind a flag. Beli shows that number before you rank, but you
answer in better/worse comparisons rather than typing a score, so it is a real finding
rather than an echo -- it just needs a sentence of mechanism alongside it, which a DM
image cannot carry. Single panel is the default for that reason, not because the second
one is wrong.

Design follows the dataviz skill: emphasis form (one accent hue, the rest in the
de-emphasis gray), single series so no legend, direct labels, recessive grid. Accent
#2a78d6 passes the skill's validator alone; against the gray it separates by CVD dE 15.9
and normal-vision 17.8, clear of both floors. No hover layer -- this is a PNG that has
to survive being looked at once, inside a message.
"""
import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import brand

ROOT = Path(__file__).resolve().parent.parent
IMAGE = ROOT / "out" / "beli_vs_google.png"

SURFACE = brand.SURFACE
INK = brand.INK
INK_2 = brand.INK_2
MUTED = brand.GREY       # Beli's own grey, as the de-emphasis mark
GRID = brand.GRID
AXIS = brand.AXIS
ACCENT = brand.TEAL      # Beli's logo teal, as the emphasis mark
WASH = brand.WASH        # light teal, for the cluster band

# Sized for legibility at DM-preview width (~400px), where this image is a third of its
# real size. Every number below is a point size at 100 dpi.
WIDTH_ONE = 10.2      # the footnote sets this, not the plot
WIDTH_TWO = 12.0
HEIGHT = 7.4
DPI = 100
HEADLINE_PT = 26
WRAP_PER_INCH = 4.6     # bold characters that fit per figure inch at HEADLINE_PT
PANEL_PT = 21
BIG_PT = 40
LABEL_PT = 17
TICK_PT = 15
NOTE_PT = 14
MARKER = 58             # small enough that 114 points stay countable
RING = 1.2              # surface ring, so overlapping points stay countable

plt.rcParams.update(brand.rcparams())


def style(axis, xlabel, xlim):
    axis.set_xlim(*xlim)
    axis.set_ylim(0, 10)
    axis.set_xlabel(xlabel, fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.tick_params(labelsize=TICK_PT, colors=MUTED, length=0, pad=8)
    axis.grid(True, color=GRID, linewidth=1, zorder=0)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(AXIS)
        axis.spines[side].set_linewidth(1)


def scatter(axis, x, y, color=ACCENT):
    axis.scatter(x, y, s=MARKER, c=color, edgecolors=SURFACE, linewidths=RING, zorder=3)


def pct_label(r2):
    """A rounded 0% reads as a broken chart, so say what is actually meant."""
    return "<1%" if r2 < 0.005 else f"{round(r2 * 100)}%"


def explained(axis, fit, color=ACCENT):
    """Direct label instead of a legend -- the number has to survive the thumbnail."""
    if not fit:
        return
    axis.text(0.04, 0.95, pct_label(fit["r2"]), transform=axis.transAxes,
              fontsize=BIG_PT, fontweight="bold", color=color, ha="left", va="top")
    axis.text(0.04, 0.845, "of the variance\nin my ranking", transform=axis.transAxes,
              fontsize=NOTE_PT, color=INK_2, ha="left", va="top", linespacing=1.35)


def google_panel(axis, data, fit, cluster, title_pad=16):
    mask = ~np.isnan(data[analyze.CLEAN]) & ~np.isnan(data[analyze.OUTCOME])
    x, y = data[analyze.CLEAN][mask], data[analyze.OUTCOME][mask]
    if cluster:
        band = np.isclose(np.round(x, 1), cluster["google_rating"])
        axis.axvspan(cluster["google_rating"] - 0.07, cluster["google_rating"] + 0.07,
                     color=WASH, zorder=1)
        scatter(axis, x[~band], y[~band], MUTED)
        scatter(axis, x[band], y[band], ACCENT)
    else:
        scatter(axis, x, y)
    style(axis, "Google rating", (1, 5))
    axis.set_xticks([1, 2, 3, 4, 5])
    axis.set_ylabel("My Beli score", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.set_title("What Google stars know", fontsize=PANEL_PT, color=INK,
                   fontweight="bold", pad=title_pad, loc="left")
    explained(axis, fit)
    if cluster:
        axis.annotate(
            f"Google gives these {cluster['count']} the same score.\n"
            f"I rank them {cluster['min']:.1f} to {cluster['max']:.1f}.",
            xy=(cluster["google_rating"] - 0.09, 2.6),
            xytext=(0.17, 0.22), textcoords=axis.transAxes,
            fontsize=NOTE_PT + 1, color=INK, linespacing=1.4, va="top",
            arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1.5, shrinkA=8))


def second_panel(axis, data, fit, key="beli_average", title_pad=40):
    """Behind a flag: true, but it needs the mechanism note to be read correctly."""
    mask = ~np.isnan(data[key]) & ~np.isnan(data[analyze.OUTCOME])
    x, y = data[key][mask], data[analyze.OUTCOME][mask]
    scatter(axis, x, y)
    if len(x) > 2:
        line = np.poly1d(np.polyfit(x, y, 1))
        span = np.linspace(x.min(), x.max(), 2)
        axis.plot(span, line(span), color=ACCENT, linewidth=2, alpha=0.35, zorder=2)
    titles = {"beli_average": ("Beli's all-user average", "What Beli's users know"),
              "friend_score": ("Beli friend score", "What my friends know")}
    xlabel, title = titles[key]
    style(axis, xlabel, (0, 10))
    axis.set_title(title, fontsize=PANEL_PT, color=INK,
                   fontweight="bold", pad=title_pad, loc="left")
    axis.text(0, 1.015, "I rank by comparison, not by typing a score",
              transform=axis.transAxes, fontsize=NOTE_PT, color=INK_2, va="bottom")
    explained(axis, fit)


def draw(result, data, path=IMAGE, with_second=False, second_key="beli_average"):
    fit = result["fits"].get(analyze.CLEAN)
    second_fit = result["fits"].get(second_key)
    with_second = with_second and second_fit is not None

    width = WIDTH_TWO if with_second else WIDTH_ONE
    figure, axes = plt.subplots(1, 2 if with_second else 1, figsize=(width, HEIGHT),
                                dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes)

    # Titles align across panels, with room under the right one for its mechanism note.
    google_panel(axes[0], data, fit, result["cluster"], title_pad=40 if with_second else 16)
    if with_second:
        second_panel(axes[1], data, second_fit, second_key)

    if not fit:
        headline = "Not enough data yet."
    elif with_second:
        other = ("Beli's own users explain" if second_key == "beli_average"
                 else "My friends explain")
        headline = (f"Google stars explain {pct_label(fit['r2'])} of how I rank "
                    f"restaurants. {other} {pct_label(second_fit['r2'])}.")
    else:
        headline = (f"Google stars explain {pct_label(fit['r2'])} of how I rank "
                    f"restaurants.")
    wrapped = textwrap.fill(headline, width=int(width * WRAP_PER_INCH))
    figure.suptitle(wrapped, fontsize=HEADLINE_PT, fontweight="bold", color=INK,
                    x=0.045, y=0.98, ha="left", va="top", linespacing=1.3)
    top = 0.86 if wrapped.count("\n") else 0.90

    note = f"n = {fit['n']} restaurants  ·  " if fit else ""
    figure.text(0.045, 0.045,
                note + "one user's own ratings, so this is a mechanism, not a measurement",
                fontsize=NOTE_PT, color=MUTED, ha="left")

    figure.tight_layout(rect=(0.03, 0.07, 0.99, top), w_pad=4.0)
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw the scatter.")
    parser.add_argument("--two-panel", dest="with_second", action="store_true",
                        help="add a second panel comparing a Beli score against mine")
    parser.add_argument("--second", default="beli_average",
                        choices=["beli_average", "friend_score"],
                        help="which Beli score the second panel plots")
    parser.add_argument("--out", type=Path, default=IMAGE)
    args = parser.parse_args()
    print(f"wrote {draw(analyze.compute(), analyze.load(), args.out, args.with_second, args.second)}")
