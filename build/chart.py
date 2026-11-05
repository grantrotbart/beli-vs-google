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


def explained(axis, fit, color=ACCENT, caption="of the variance\nin my ranking"):
    """Direct label instead of a legend -- the number has to survive the thumbnail."""
    if not fit:
        return
    axis.text(0.04, 0.95, pct_label(fit["r2"]), transform=axis.transAxes,
              fontsize=BIG_PT, fontweight="bold", color=color, ha="left", va="top")
    axis.text(0.04, 0.845, caption, transform=axis.transAxes,
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


COVERAGE = ROOT / "out" / "coverage.png"
DISTRIBUTION = ROOT / "out" / "distribution.png"


def coverage_chart(data, path=COVERAGE):
    """Beli ratings against Google reviews, log-log, parity line through the middle.

    Above the line means Beli carries more. The New York points sit well above it and
    almost everything else sits below, which is the whole finding in one picture."""
    beli, goog = data["beli_rating_count"], data["user_ratings_total"]
    mask = ~np.isnan(beli) & ~np.isnan(goog) & (goog > 0) & (beli > 0)
    x, y = goog[mask], beli[mask]
    nyc = np.array([m == "NYC" for m, keep in zip(data["markets"], mask) if keep])

    figure, axis = plt.subplots(figsize=(8.6, 6.4), dpi=DPI)
    lim = [min(x.min(), y.min()) * 0.6, max(x.max(), y.max()) * 1.8]
    axis.plot(lim, lim, color=AXIS, linewidth=1.5, zorder=1)
    axis.text(lim[1] * 0.42, lim[1] * 0.60, "same number of ratings",
              fontsize=NOTE_PT - 1, color=MUTED, rotation=38, ha="center", va="center")
    scatter(axis, x[~nyc], y[~nyc], MUTED)
    scatter(axis, x[nyc], y[nyc], ACCENT)

    axis.set_xscale("log"); axis.set_yscale("log")
    axis.set_xlim(*lim); axis.set_ylim(*lim)
    axis.set_xlabel("Google reviews", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.set_ylabel("Beli ratings", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.tick_params(labelsize=TICK_PT, colors=MUTED, length=0, pad=8)
    axis.grid(True, color=GRID, linewidth=1, zorder=0)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(AXIS); axis.spines[side].set_linewidth(1)

    axis.text(0.03, 0.96, "New York", transform=axis.transAxes, fontsize=NOTE_PT + 3,
              color=ACCENT, fontweight="bold", va="top")
    axis.text(0.03, 0.90, "everywhere else", transform=axis.transAxes,
              fontsize=NOTE_PT + 3, color=MUTED, fontweight="bold", va="top")
    figure.suptitle("Beli has more ratings than Google — in New York",
                    fontsize=HEADLINE_PT - 4, fontweight="bold", color=INK,
                    x=0.045, y=0.97, ha="left", va="top")
    figure.tight_layout(rect=(0.02, 0.02, 0.99, 0.90))
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


def distribution_chart(data, path=DISTRIBUTION):
    """The two crowd scores as histograms on their own scales.

    Google's 114 restaurants fall into 12 values; Beli's average spreads them wider."""
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), dpi=DPI, sharey=True)
    for axis, key, lo, hi, step, title in (
            (axes[0], analyze.CLEAN, 1.0, 5.0, 0.1, "Google rating"),
            (axes[1], "beli_average", 0.0, 10.0, 0.1, "Beli's all-user average")):
        v = data[key][~np.isnan(data[key])]
        axis.hist(v, bins=np.arange(lo, hi + step, step), color=ACCENT, zorder=3)
        axis.set_xlim(lo, hi)
        axis.set_xlabel(f"{title}  ({len(set(v))} distinct values)",
                        fontsize=LABEL_PT - 2, color=INK_2, labelpad=10)
        axis.tick_params(labelsize=TICK_PT - 1, colors=MUTED, length=0, pad=6)
        axis.grid(True, axis="y", color=GRID, linewidth=1, zorder=0)
        axis.set_axisbelow(True)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            axis.spines[side].set_color(AXIS); axis.spines[side].set_linewidth(1)
    axes[0].set_ylabel("restaurants", fontsize=LABEL_PT - 2, color=INK_2, labelpad=10)
    figure.suptitle("Same 114 restaurants, each scale drawn in full",
                    fontsize=HEADLINE_PT - 4, fontweight="bold", color=INK,
                    x=0.035, y=0.97, ha="left", va="top")
    figure.tight_layout(rect=(0.01, 0.02, 0.99, 0.86), w_pad=3.0)
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


CROWD = ROOT / "out" / "crowd.png"


def crowd_chart(result, data, path=CROWD):
    """Google's crowd against Beli's crowd on the same restaurants.

    The same null as the personal chart, but with no n=1 to argue about: both axes are
    averages over thousands of people. Two named points carry the inversion, because a
    cloud with no slope is easy to nod past and a pair of restaurants is not."""
    fit = result["fits"].get("crowd_vs_google")
    mask = ~np.isnan(data[analyze.CLEAN]) & ~np.isnan(data["beli_average"])
    x, y = data[analyze.CLEAN][mask], data["beli_average"][mask]
    names = [n for n, keep in zip(data["names"], mask) if keep]

    figure, axis = plt.subplots(figsize=(9.6, 7.0), dpi=DPI)
    scatter(axis, x, y, ACCENT)
    style(axis, "Google rating", (1, 5))
    axis.set_xticks([1, 2, 3, 4, 5])
    axis.set_ylabel("Beli's all-user average", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.set_title("Two crowds, the same 113 restaurants", fontsize=PANEL_PT, color=INK,
                   fontweight="bold", pad=16, loc="left")
    if fit:
        explained(axis, fit, caption="of the variance in\nwhat Beli's users think")

    # Name the inversion: Google puts these in one order, Beli's users the other.
    want = {"Laser Wolf": (-0.42, 0.55), "Darrell's Dog Gone Good Diner": (-0.52, -0.75)}
    for label, (dx, dy) in want.items():
        for i, name in enumerate(names):
            if name == label:
                axis.annotate(
                    label, xy=(x[i], y[i]), xytext=(x[i] + dx, y[i] + dy),
                    fontsize=NOTE_PT, color=INK, ha="right",
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1.2,
                                    shrinkA=4, shrinkB=5))
                break

    headline = "Google and Beli's users barely agree on anything"
    figure.suptitle(headline, fontsize=HEADLINE_PT - 2, fontweight="bold", color=INK,
                    x=0.045, y=0.97, ha="left", va="top")
    figure.text(0.045, 0.045,
                "n = 113 restaurants  ·  both axes are averages over users, not one person",
                fontsize=NOTE_PT, color=MUTED, ha="left")
    figure.tight_layout(rect=(0.03, 0.07, 0.99, 0.90))
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path
