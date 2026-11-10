"""
The charts.

    python build/chart.py               # the headline scatter
    python build/chart.py --two-panel   # adds a second panel against a Beli score

Reads  data/matched.csv
Writes out/beli_vs_google.png, out/crowd.png, out/coverage.png, out/distribution.png

Every chart shares one frame: a headline that carries the finding, a one-line subtitle
that says what is plotted, the plot, and a footnote. Margins are fixed in inches rather
than left to tight_layout, which is what kept leaving a dead band under the headline.

Google's whole 1-5 scale is always on the axis. The bunching into one narrow band is the
finding, and zooming to the occupied range would hide it.

Design follows the dataviz skill: emphasis form (Beli's teal for the marks that matter,
Beli's grey for the rest), direct labels instead of legend boxes, recessive grid, text in
ink rather than series colour. Teal against that grey separates by dE 31.5 normal-vision
and 28.9 under protanopia, well clear of both floors.
"""
import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import brand

ROOT = Path(__file__).resolve().parent.parent
IMAGE = ROOT / "out" / "beli_vs_google.png"
CROWD = ROOT / "out" / "crowd.png"
COVERAGE = ROOT / "out" / "coverage.png"
DISTRIBUTION = ROOT / "out" / "distribution.png"

SURFACE = brand.SURFACE
INK = brand.INK
INK_2 = brand.INK_2
MUTED = brand.GREY       # Beli's own grey, as the de-emphasis mark
FAINT = brand.MUTED      # chrome text: ticks and footnotes
GRID = brand.GRID
AXIS = brand.AXIS
ACCENT = brand.TEAL      # Beli's logo teal, as the emphasis mark
WASH = brand.WASH        # light teal, for the cluster band

# Sized to stay legible at thumbnail width (~400px), where an image is a third of its
# real size. Point sizes at 100 dpi; margins in inches.
DPI = 100
HEADLINE_PT = 26
SUBTITLE_PT = 15
PANEL_PT = 18
BIG_PT = 38
LABEL_PT = 16
TICK_PT = 14
NOTE_PT = 14
FOOT_PT = 12
WRAP_PER_INCH = 4.4     # bold headline characters per figure inch
MARKER = 58             # small enough that ~120 points stay countable
RING = 1.2              # surface ring, so overlapping points stay countable

EDGE_IN = 0.45          # headline, subtitle and footnote all start here
TOP_IN = 0.32           # above the headline
GAP_IN = 0.30           # between the subtitle and the plot
LEFT_IN = 1.05          # room for tick labels and the y label
RIGHT_IN = 0.35
BOTTOM_IN = 1.25        # tick labels, x label and footnote

plt.rcParams.update(brand.rcparams())


# ---- shared pieces ---------------------------------------------------------------

def pct_label(r2):
    """Compact form for big on-chart numbers. A rounded 0% reads as a broken chart."""
    return "<1%" if r2 < 0.005 else f"{round(r2 * 100)}%"


def pct_words(r2):
    """Sentence form for headlines."""
    return "less than 1%" if r2 < 0.005 else f"{round(r2 * 100)}%"


def frame(figure, headline, subtitle=None, footnote=None, panel_titles=False):
    """Lay out headline, subtitle and footnote, then fit the axes between them.

    Everything is positioned in inches from the figure edges, so the plot starts a fixed
    distance below the last line of text no matter how many lines the headline wraps to.
    """
    w, h = figure.get_size_inches()
    wrapped = textwrap.fill(headline, width=int(w * WRAP_PER_INCH))
    lines = wrapped.count("\n") + 1

    y = h - TOP_IN
    figure.text(EDGE_IN / w, y / h, wrapped, fontsize=HEADLINE_PT, fontweight="bold",
                color=INK, ha="left", va="top", linespacing=1.22)
    y -= lines * HEADLINE_PT * 1.22 / 72
    if subtitle:
        y -= 0.10
        figure.text(EDGE_IN / w, y / h, subtitle, fontsize=SUBTITLE_PT, color=INK_2,
                    ha="left", va="top")
        y -= SUBTITLE_PT * 1.3 / 72
    y -= GAP_IN
    if panel_titles:
        y -= PANEL_PT * 1.6 / 72
    if footnote:
        figure.text(EDGE_IN / w, 0.22 / h, footnote, fontsize=FOOT_PT, color=FAINT,
                    ha="left", va="bottom")
    figure.subplots_adjust(left=LEFT_IN / w, right=1 - RIGHT_IN / w,
                           top=y / h, bottom=(BOTTOM_IN if footnote else BOTTOM_IN - 0.4) / h,
                           wspace=0.10)


def style(axis, xlabel, xlim, ylabel=None, xticks=None):
    """Score axes: 0-10 on y with headroom so a 10.0 isn't clipped by the frame."""
    axis.set_xlim(*xlim)
    axis.set_ylim(0, 10.45)
    axis.set_yticks([0, 2, 4, 6, 8, 10])
    if xticks is not None:
        axis.set_xticks(xticks)
    axis.set_xlabel(xlabel, fontsize=LABEL_PT, color=INK_2, labelpad=10)
    if ylabel:
        axis.set_ylabel(ylabel, fontsize=LABEL_PT, color=INK_2, labelpad=10)
    chrome(axis)


def chrome(axis, grid_axis="both"):
    axis.tick_params(labelsize=TICK_PT, colors=FAINT, length=0, pad=8)
    axis.grid(True, axis=grid_axis, color=GRID, linewidth=1, zorder=0)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(AXIS)
        axis.spines[side].set_linewidth(1)


def scatter(axis, x, y, color=ACCENT):
    axis.scatter(x, y, s=MARKER, c=color, edgecolors=SURFACE, linewidths=RING, zorder=3)


def explained(axis, fit, caption):
    """Big number with a caption under it, for telling two panels apart.

    The caption's position is computed from the rendered height of the number, so the
    two can never overlap whatever size the axes ends up."""
    if not fit:
        return
    figure = axis.figure
    axis_h_in = axis.get_position().height * figure.get_size_inches()[1]
    big_h = BIG_PT * 1.05 / 72 / axis_h_in
    top = 0.97
    axis.text(0.04, top, pct_label(fit["r2"]), transform=axis.transAxes,
              fontsize=BIG_PT, fontweight="bold", color=INK, ha="left", va="top")
    axis.text(0.045, top - big_h - 0.02, caption, transform=axis.transAxes,
              fontsize=NOTE_PT, color=INK_2, ha="left", va="top", linespacing=1.3)


def panel_title(axis, text):
    axis.set_title(text, fontsize=PANEL_PT, color=INK, fontweight="bold",
                   pad=12, loc="left")


# ---- the headline scatter --------------------------------------------------------

def google_panel(axis, data, cluster):
    mask = ~np.isnan(data[analyze.CLEAN]) & ~np.isnan(data[analyze.OUTCOME])
    x, y = data[analyze.CLEAN][mask], data[analyze.OUTCOME][mask]
    if cluster:
        g = cluster["google_rating"]
        band = np.isclose(np.round(x, 1), g)
        axis.axvspan(g - 0.07, g + 0.07, color=WASH, zorder=1)
        scatter(axis, x[~band], y[~band], MUTED)
        scatter(axis, x[band], y[band], ACCENT)
    else:
        scatter(axis, x, y)
    style(axis, "Google rating", (1, 5.12), ylabel="My Beli score", xticks=[1, 2, 3, 4, 5])

    if cluster:
        # The label sits in the empty space under the cloud, and an elbow leader runs
        # along y then straight up the band, so it crosses no points on the way.
        text = (f"Google gives these {cluster['count']}\nthe same score.\n"
                f"I rank them {cluster['min']:.1f} to {cluster['max']:.1f}.")
        g = cluster["google_rating"]
        axis.annotate(text, xy=(g, cluster["min"] - 0.25), xytext=(g - 0.22, 2.2),
                      fontsize=NOTE_PT + 1, color=INK, linespacing=1.35,
                      ha="right", va="center",
                      arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1.3,
                                      shrinkA=6, shrinkB=0, relpos=(1.0, 0.5),
                                      connectionstyle="angle,angleA=0,angleB=90,rad=0"))


def second_panel(axis, data, key="beli_average"):
    mask = ~np.isnan(data[key]) & ~np.isnan(data[analyze.OUTCOME])
    x, y = data[key][mask], data[analyze.OUTCOME][mask]
    scatter(axis, x, y)
    if len(x) > 2:
        line = np.poly1d(np.polyfit(x, y, 1))
        span = np.linspace(x.min(), x.max(), 2)
        axis.plot(span, line(span), color=ACCENT, linewidth=2, alpha=0.35, zorder=2)
    xlabel = {"beli_average": "Beli's all-user average",
              "friend_score": "Beli friend score"}[key]
    style(axis, xlabel, (0, 10.2), xticks=[0, 2, 4, 6, 8, 10])


def draw(result, data, path=IMAGE, with_second=False, second_key="beli_average"):
    fit = result["fits"].get(analyze.CLEAN)
    second_fit = result["fits"].get(second_key)
    with_second = with_second and second_fit is not None
    cluster = result["cluster"]

    width, height = (12.0, 7.4) if with_second else (10.2, 7.2)
    figure, axes = plt.subplots(1, 2 if with_second else 1, figsize=(width, height),
                                dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes)

    google_panel(axes[0], data, cluster)
    if with_second:
        second_panel(axes[1], data, second_key)

    if not fit:
        headline = "Not enough data yet."
    elif with_second:
        other = ("Beli's own users explain" if second_key == "beli_average"
                 else "My friends explain")
        headline = (f"Google stars explain {pct_words(fit['r2'])} of how I rank "
                    f"restaurants. {other} {pct_words(second_fit['r2'])}.")
    else:
        headline = (f"Google stars explain {pct_words(fit['r2'])} of how I rank "
                    f"restaurants.")
    n = fit["n"] if fit else 0
    against = ("their Google ratings and Beli's all-user average" if with_second
               else "the same restaurants' Google ratings")
    frame(figure, headline,
          subtitle=f"{n} restaurants on my Beli list, against {against}.",
          panel_titles=with_second)

    if with_second:
        titles = {"beli_average": "What Beli's users know",
                  "friend_score": "What my friends know"}
        panel_title(axes[0], "What Google stars know")
        panel_title(axes[1], titles[second_key])
        explained(axes[0], fit, "of the variance\nin my ranking")
        explained(axes[1], second_fit, "of the variance\nin my ranking")

    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


# ---- crowd against crowd ---------------------------------------------------------

def crowd_chart(result, data, path=CROWD):
    """Google's crowd against Beli's crowd on the same restaurants.

    The same null as the personal chart, with no n=1 to argue about. Two named points
    carry the inversion, because a cloud with no slope is easy to nod past and a pair of
    restaurants is not."""
    fit = result["fits"].get("crowd_vs_google")
    mask = ~np.isnan(data[analyze.CLEAN]) & ~np.isnan(data["beli_average"])
    x, y = data[analyze.CLEAN][mask], data["beli_average"][mask]
    names = [n for n, keep in zip(data["names"], mask) if keep]

    figure, axis = plt.subplots(figsize=(10.2, 7.2), dpi=DPI)
    scatter(axis, x, y, ACCENT)
    style(axis, "Google rating", (1, 5.12), ylabel="Beli's all-user average",
          xticks=[1, 2, 3, 4, 5])

    # Google puts these two in one order, Beli's users in the other.
    callouts = {"Laser Wolf": (-0.45, 0.62),
                "Darrell's Dog Gone Good Diner": (-0.45, -0.85)}
    for label, (dx, dy) in callouts.items():
        if label not in names:
            continue
        i = names.index(label)
        axis.annotate(f"{label}\nGoogle {x[i]:.1f}  ·  Beli users {y[i]:.1f}",
                      xy=(x[i], y[i]), xytext=(x[i] + dx, y[i] + dy),
                      fontsize=NOTE_PT, color=INK, ha="right", va="center",
                      linespacing=1.3,
                      arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1.2,
                                      shrinkA=4, shrinkB=5))

    headline = (f"Google's rating explains {pct_words(fit['r2'])} of what Beli's users "
                f"think" if fit else "Google against Beli's users")
    frame(figure, headline,
          subtitle=f"Google rating against Beli's all-user average, "
                   f"{int(mask.sum())} restaurants.",
          footnote="Both axes are averages over many users, so my own taste isn't "
                   "driving this one.")
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


# ---- volume ----------------------------------------------------------------------

def coverage_chart(data, path=COVERAGE):
    """Beli ratings against Google reviews, log-log, with a parity line.

    Above the line means Beli carries more. The New York points sit well above it."""
    beli, goog = data["beli_rating_count"], data["user_ratings_total"]
    mask = ~np.isnan(beli) & ~np.isnan(goog) & (goog > 0) & (beli > 0)
    x, y = goog[mask], beli[mask]
    nyc = np.array([m == "NYC" for m, keep in zip(data["markets"], mask) if keep])
    nyc_median = float(np.median(y[nyc] / x[nyc])) if nyc.any() else None

    figure, axis = plt.subplots(figsize=(9.6, 7.4), dpi=DPI)
    lim = [min(x.min(), y.min()) * 0.6, max(x.max(), y.max()) * 1.8]
    axis.plot(lim, lim, color=AXIS, linewidth=1.5, zorder=1)
    scatter(axis, x[~nyc], y[~nyc], MUTED)
    scatter(axis, x[nyc], y[nyc], ACCENT)
    axis.set_xscale("log"); axis.set_yscale("log")
    axis.set_xlim(*lim); axis.set_ylim(*lim)
    axis.set_xlabel("Google reviews", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    axis.set_ylabel("Beli ratings", fontsize=LABEL_PT, color=INK_2, labelpad=10)
    chrome(axis)
    axis.minorticks_off()
    ticks = [10 ** k for k in range(1, 6) if lim[0] <= 10 ** k <= lim[1]]
    names = {10: "10", 100: "100", 1000: "1k", 10000: "10k", 100000: "100k"}
    axis.set_xticks(ticks, [names[t] for t in ticks])
    axis.set_yticks(ticks, [names[t] for t in ticks])

    # Direct labels: a coloured dot beside ink text, so identity isn't colour alone.
    handles = [Line2D([], [], marker="o", linestyle="", markersize=9,
                      markerfacecolor=c, markeredgecolor=SURFACE, label=t)
               for c, t in ((ACCENT, "New York"), (MUTED, "Everywhere else"))]
    legend = axis.legend(handles=handles, loc="upper left", frameon=False,
                         fontsize=NOTE_PT + 1, handletextpad=0.4, borderaxespad=0.6,
                         labelspacing=0.6)
    for text in legend.get_texts():
        text.set_color(INK)

    headline = (f"In New York, Beli has {nyc_median:.0f}x Google's ratings"
                if nyc_median else "Beli ratings against Google reviews")
    frame(figure, headline,
          subtitle="One point per restaurant. Above the line, Beli has more ratings.",
          footnote="Median ratio per restaurant. Florida and Europe sit mostly below "
                   "the line.")

    # The parity label has to be placed after layout, because its angle depends on the
    # final shape of the axes.
    p0 = axis.transData.transform((lim[0], lim[0]))
    p1 = axis.transData.transform((lim[1], lim[1]))
    angle = np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))
    at = lim[0] * 2.2
    axis.text(at, at * 1.25, "equal on both", fontsize=NOTE_PT - 1, color=FAINT,
              rotation=angle, rotation_mode="anchor", ha="left", va="bottom")

    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


# ---- resolution ------------------------------------------------------------------

def distribution_chart(data, path=DISTRIBUTION):
    """The two crowd scores as histograms, each across its own full scale.

    Google's average can't fall below one star, so its axis starts at 1; a Beli score
    can go to 0. Each panel says how many values its scale allows, because most of the
    difference in ties comes from that, not from the users."""
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 5.8), dpi=DPI, sharey=True)
    panels = (
        (axes[0], analyze.CLEAN, 1.0, 5.0, "Google: 1 to 5 stars", [1, 2, 3, 4, 5]),
        (axes[1], "beli_average", 0.0, 10.0, "Beli: 0 to 10", [0, 2, 4, 6, 8, 10]),
    )
    used = {}
    for axis, key, lo, hi, title, ticks in panels:
        v = np.round(data[key][~np.isnan(data[key])], 1)
        used[key] = len(np.unique(v))
        possible = int(round((hi - lo) * 10)) + 1
        # One bar per possible value, centred on it, so no rating sits on a bin edge.
        edges = np.arange(lo - 0.05, hi + 0.1, 0.1)
        axis.hist(v, bins=edges, color=ACCENT, zorder=3)
        axis.set_xlim(lo - 0.05, hi + 0.05)
        axis.set_xticks(ticks)
        axis.set_xlabel(f"one decimal  ·  {possible} possible values, {used[key]} used",
                        fontsize=LABEL_PT - 2, color=INK_2, labelpad=10)
        chrome(axis, grid_axis="y")
        panel_title(axis, title)
    axes[0].set_ylabel("restaurants", fontsize=LABEL_PT - 1, color=INK_2, labelpad=10)

    beli = data["beli_average"][~np.isnan(data["beli_average"])]
    squeezed = len(np.unique(np.round(1 + 0.4 * beli, 1)))
    n = int((~np.isnan(data[analyze.CLEAN])).sum())
    frame(figure,
          f"Google packs {n} restaurants into {used[analyze.CLEAN]} values",
          subtitle="Each platform's average across its full scale. A Google average "
                   "can't fall below 1 star.",
          footnote=f"Mostly granularity: squeezed onto Google's 41 slots, Beli's averages "
                   f"would use {squeezed} values.",
          panel_titles=True)
    figure.subplots_adjust(wspace=0.08)
    figure.savefig(path, dpi=DPI, facecolor=SURFACE)
    plt.close(figure)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw the charts.")
    parser.add_argument("--two-panel", dest="with_second", action="store_true",
                        help="add a second panel comparing a Beli score against mine")
    parser.add_argument("--second", default="beli_average",
                        choices=["beli_average", "friend_score"],
                        help="which Beli score the second panel plots")
    parser.add_argument("--out", type=Path, default=IMAGE)
    args = parser.parse_args()
    print(f"wrote {draw(analyze.compute(), analyze.load(), args.out, args.with_second, args.second)}")
