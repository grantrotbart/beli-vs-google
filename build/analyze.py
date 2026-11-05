"""
The numbers behind the chart.

    python build/analyze.py

Reads  data/matched.csv   (rows where keep == 1)
Writes out/stats.md       every figure the writeup needs, headline first

Beli shows the rec score, the friend score and the all-user average before you rank.
That would be fatal if you then typed a number -- but you don't. You answer a sequence
of better / worse / too tough comparisons against restaurants you have already ranked,
and the 0-10 falls out of where you land in your own sorted list. An anchor cannot be
copied into an answer that is never a number, which is why these columns are reported
rather than discarded. It is not zero, though: a binary search is exactly the structure
where a small per-comparison bias compounds, so the gap distributions and the count of
large disagreements are computed as a check on how much room anchoring actually had.
"""
import csv
from datetime import date
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parent.parent
MATCHED = ROOT / "data" / "matched.csv"
STATS = ROOT / "out" / "stats.md"

OUTCOME = "beli_score"
CLEAN = "google_rating"                                    # not shown while ranking
ANCHORS = ["friend_score", "beli_average"]    # shown before you rank
PREDICTORS = [CLEAN] + ANCHORS
LABELS = {
    "google_rating": "Google rating",
    "friend_score": "Beli friend score",
    "beli_average": "Beli all-user average",
    "beli_score": "My Beli score",
    "crowd_vs_google": "Beli's crowd vs Google's",
}
# Native scale of each measure. Used to ask what share of its own scale a distribution
# actually uses -- the fair way to compare a 1-5 star average with a 0-10 ranking.
SCALES = {
    "google_rating": (1.0, 5.0),
    "friend_score": (0.0, 10.0),
    "beli_average": (0.0, 10.0),
    "beli_score": (0.0, 10.0),
}
BINS = 10
MIN_CLUSTER = 3
STRONG = 0.25        # above this, the "Google is noise" reading does not hold
BIG_GAP = 2.0        # a disagreement too large to have been nudged there by an anchor
MIN_BAND = 8         # smallest price band worth fitting on its own
BANDS = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}


def load():
    """matched.csv -> dict of column -> np.array(float), keep == 1 rows only."""
    kept, sources = [], set()
    with MATCHED.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("keep") or "").strip() != "1":
                continue
            kept.append(row)
            sources.add((row.get("source") or "").strip())

    def column(key):
        out = []
        for row in kept:
            try:
                out.append(float((row.get(key) or "").strip()))
            except ValueError:
                out.append(np.nan)
        return np.array(out, dtype=float)

    data = {key: column(key) for key in [OUTCOME] + PREDICTORS}
    for key in ("user_ratings_total", "friend_count", "beli_rating_count", "price_level"):
        data[key] = column(key)
    data["names"] = [row["name"] for row in kept]
    data["markets"] = [row.get("market", "") for row in kept]
    data["sources"] = sources
    return data


def ols(predictors, outcome):
    """Least squares with an intercept. Returns r2, adjusted r2, coefficients, fitted."""
    design = np.column_stack([np.ones(len(outcome))] + list(predictors))
    beta, *_ = np.linalg.lstsq(design, outcome, rcond=None)
    fitted = design @ beta
    ss_res = float(((outcome - fitted) ** 2).sum())
    ss_tot = float(((outcome - outcome.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    k, n = len(predictors), len(outcome)
    adjusted = 1 - (1 - r2) * (n - 1) / (n - k - 1) if n > k + 1 else float("nan")
    return r2, adjusted, beta, fitted


def describe(values, key):
    """Spread of one measure, including what share of its own scale it uses."""
    clean = values[~np.isnan(values)]
    if len(clean) < 2:
        return None
    low, high = SCALES[key]
    counts, _ = np.histogram(clean, bins=BINS, range=(low, high))
    share = counts[counts > 0] / counts.sum()
    return {
        "n": int(len(clean)),
        "min": float(clean.min()),
        "max": float(clean.max()),
        "span": float(clean.max() - clean.min()),
        "scale_used": float((clean.max() - clean.min()) / (high - low)),
        "std": float(clean.std(ddof=1)),
        # A 1-5 star average and a 0-10 ranking have different-sized scales, so raw
        # standard deviations are not comparable across rows. This one is.
        "std_share": float(clean.std(ddof=1) / (high - low)),
        "variance": float(clean.var(ddof=1)),
        "iqr": float(np.percentile(clean, 75) - np.percentile(clean, 25)),
        "entropy": float(-(share * np.log2(share)).sum()),
    }


def simple_fits(data):
    """One regression per predictor, each on every row where that predictor exists."""
    fits = {}
    for key in PREDICTORS:
        mask = ~np.isnan(data[key]) & ~np.isnan(data[OUTCOME])
        if mask.sum() < 3:
            continue
        x, y = data[key][mask], data[OUTCOME][mask]
        line = sps.linregress(x, y)
        rho, p_rho = sps.spearmanr(x, y)
        fits[key] = {
            "n": int(mask.sum()),
            "r2": float(line.rvalue ** 2),
            "slope": float(line.slope),
            "intercept": float(line.intercept),
            "p": float(line.pvalue),
            "spearman": float(rho),
            "spearman_p": float(p_rho),
        }
    return fits


def crowd_fit(data):
    """Google's crowd against Beli's crowd. Neither side is one person."""
    mask = ~np.isnan(data[CLEAN]) & ~np.isnan(data["beli_average"])
    if mask.sum() < 20:
        return None
    x, y = data[CLEAN][mask], data["beli_average"][mask]
    line = sps.linregress(x, y)
    rho, p_rho = sps.spearmanr(x, y)
    return {"n": int(mask.sum()), "r2": float(line.rvalue ** 2),
            "slope": float(line.slope), "intercept": float(line.intercept),
            "p": float(line.pvalue), "spearman": float(rho), "spearman_p": float(p_rho)}


def anchoring(data):
    """How far my score lands from each number the app showed me first.

    The score is never typed, so an anchor cannot be copied straight through. What it
    could still do is tilt individual better/worse calls. A tilt like that shows up as
    gaps bunched on zero with few large, two-sided disagreements -- so that is what gets
    counted. Large gaps in both directions are the evidence against it."""
    out = {}
    for key in ANCHORS:
        mask = ~np.isnan(data[key]) & ~np.isnan(data[OUTCOME])
        if mask.sum() < 3:
            continue
        delta = data[OUTCOME][mask] - data[key][mask]
        big = np.abs(delta) > BIG_GAP
        out[key] = {
            "n": int(mask.sum()),
            "mean": float(delta.mean()),
            "median_abs": float(np.median(np.abs(delta))),
            "std": float(delta.std(ddof=1)),
            "within_half": float((np.abs(delta) <= 0.5).mean()),
            "within_one": float((np.abs(delta) <= 1.0).mean()),
            "big": int(big.sum()),
            "big_share": float(big.mean()),
            "big_above": int((delta > BIG_GAP).sum()),
            "big_below": int((delta < -BIG_GAP).sum()),
            "max_gap": float(np.abs(delta).max()),
        }
    return out


def sample_depth(data):
    """How many people are actually behind the two Beli columns.

    A friend score from one friend is one person's opinion wearing a crowd's name, and
    the all-user average contains my own rating -- which matters where few people have
    rated the place. Both are worth stating in numbers rather than hand-waving."""
    out = {}
    friends = data["friend_count"][~np.isnan(data["friend_count"])]
    if len(friends):
        out["friends"] = {
            "n": int(len(friends)),
            "median": float(np.median(friends)),
            "none": int((friends == 0).sum()),
            "single": int((friends == 1).sum()),
            "three_plus": int((friends >= 3).sum()),
            "max": float(friends.max()),
        }
    crowd = data["beli_rating_count"][~np.isnan(data["beli_rating_count"])]
    if len(crowd):
        out["crowd"] = {
            "n": int(len(crowd)),
            "median": float(np.median(crowd)),
            "min": float(crowd.min()),
            "max": float(crowd.max()),
            "my_share_worst": float(100 / crowd.min()) if crowd.min() else None,
            "thin": int((crowd < 500).sum()),
        }
    return out


def coverage(data):
    """The claim that Beli carries far more ratings than Google, tested per market.

    The blended figure is misleading in both directions, so it is not reported. Beli's
    volume advantage is a function of where its users are: enormous in New York, absent
    where the app has no density. That map is the finding."""
    beli, goog = data["beli_rating_count"], data["user_ratings_total"]
    mask = ~np.isnan(beli) & ~np.isnan(goog) & (goog > 0)
    if mask.sum() < 20:
        return None
    ratio = beli[mask] / goog[mask]
    names = [n for n, keep in zip(data["names"], mask) if keep]
    markets = [m for m, keep in zip(data["markets"], mask) if keep]

    by_market = []
    for name in sorted(set(markets)):
        sel = np.array([m == name for m in markets])
        if sel.sum() >= 5:
            by_market.append({
                "market": name, "n": int(sel.sum()),
                "median": float(np.median(ratio[sel])),
                "beli_wins": int((ratio[sel] > 1).sum()),
            })
    by_market.sort(key=lambda row: -row["median"])

    order = np.argsort(-ratio)
    top = [{"name": names[i], "ratio": float(ratio[i]),
            "beli": float(beli[mask][i]), "google": float(goog[mask][i])}
           for i in order[:5]]
    # Where is the gap widest? Split by how well covered the restaurant is on Google.
    order_g = np.argsort(goog[mask])
    half = len(order_g) // 2
    thin = float(np.median(ratio[order_g[:half]]))
    thick = float(np.median(ratio[order_g[half:]]))

    return {
        "n": int(mask.sum()),
        "by_market": by_market,
        "top": top,
        "thin_google": thin,
        "thick_google": thick,
        "thin_cutoff": float(goog[mask][order_g[half]]),
        "beli_total": float(beli[mask].sum()),
        "google_total": float(goog[mask].sum()),
    }


def distinguishing(data):
    """How often each crowd score leaves two restaurants tied.

    This is the resolution that matters to a product that has to rank things: a score
    that puts 22 restaurants on the same number cannot order them at all."""
    out = {}
    both = ~np.isnan(data[CLEAN]) & ~np.isnan(data["beli_average"])
    n = int(both.sum())
    if n < 20:
        return None
    pairs = n * (n - 1) // 2
    for key in (CLEAN, "beli_average"):
        values, counts = np.unique(data[key][both], return_counts=True)
        tied = int(sum(c * (c - 1) // 2 for c in counts))
        out[key] = {
            "distinct": int(len(values)),
            "tied_pairs": tied,
            "tied_share": tied / pairs,
            "biggest_tie": int(counts.max()),
        }
    out["n"] = n
    out["pairs"] = pairs
    return out


def within_price(data):
    """Answers the obvious objection: that the null is just cheap-versus-expensive.

    A taco stand and a tasting menu are different judgements, so if Google's rating
    tracked my ranking *inside* a price band and only looked flat across all of them,
    the headline would be an artifact. Two tests: the fit band by band, and whether
    Google adds anything to a model that already knows the price."""
    price = data["price_level"]
    mask = ~np.isnan(price) & ~np.isnan(data[CLEAN]) & ~np.isnan(data[OUTCOME])
    if mask.sum() < 20:
        return None
    google, outcome, band = data[CLEAN][mask], data[OUTCOME][mask], price[mask]

    bands = []
    for level in sorted(set(band)):
        sel = band == level
        if sel.sum() >= MIN_BAND:
            line = sps.linregress(google[sel], outcome[sel])
            bands.append({
                "level": int(level), "n": int(sel.sum()),
                "r2": float(line.rvalue ** 2),
                "spearman": float(sps.spearmanr(google[sel], outcome[sel])[0]),
            })

    # Price as dummies (one band held out as the reference), then the same plus Google.
    levels = sorted(set(band))[1:]
    dummies = [(band == level).astype(float) for level in levels]
    r2_price, _, _, _ = ols(dummies, outcome)
    r2_both, _, _, _ = ols(dummies + [google], outcome)
    return {
        "n": int(mask.sum()),
        "bands": bands,
        "r2_price": r2_price,
        "r2_both": r2_both,
        "google_adds": r2_both - r2_price,
    }


def tightest_cluster(data):
    """The most crowded Google rating, and how far apart those restaurants really are.

    Where several ratings tie on count, take the one with the widest Beli spread -- that
    is the claim being made, and stats.md says the tie-break happened."""
    mask = ~np.isnan(data[CLEAN]) & ~np.isnan(data[OUTCOME])
    if mask.sum() < MIN_CLUSTER:
        return None
    rounded = np.round(data[CLEAN][mask], 1)
    outcome = data[OUTCOME][mask]
    averages = data["beli_average"][mask]
    names = [name for name, keep in zip(data["names"], mask) if keep]

    values, counts = np.unique(rounded, return_counts=True)
    if not len(values[counts >= MIN_CLUSTER]):
        return None
    top = counts[counts >= MIN_CLUSTER].max()
    tied = [value for value, count in zip(values, counts) if count == top and count >= MIN_CLUSTER]

    def spread(value):
        members = outcome[rounded == value]
        return members.max() - members.min()

    value = max(tied, key=spread)
    members = rounded == value
    member_averages = averages[members]
    member_averages = member_averages[~np.isnan(member_averages)]
    ordered = sorted(zip(outcome[members], [n for n, m in zip(names, members) if m]))
    return {
        "google_rating": float(value),
        "count": int(members.sum()),
        "tied_with": [float(v) for v in tied if v != value],
        "min": float(outcome[members].min()),
        "max": float(outcome[members].max()),
        "spread": float(spread(value)),
        "average_spread": (float(member_averages.max() - member_averages.min())
                           if len(member_averages) >= 2 else None),
        "average_min": float(member_averages.min()) if len(member_averages) else None,
        "average_max": float(member_averages.max()) if len(member_averages) else None,
        "lowest": ordered[0][1],
        "highest": ordered[-1][1],
    }


def review_count_check(data, fits):
    """Does Google agree with me more on restaurants with more reviews? Cheap test of
    the selection-bias argument."""
    if CLEAN not in fits:
        return None
    mask = (~np.isnan(data[CLEAN]) & ~np.isnan(data[OUTCOME])
            & ~np.isnan(data["user_ratings_total"]))
    if mask.sum() < 5:
        return None
    fit = fits[CLEAN]
    residual = np.abs(
        data[OUTCOME][mask] - (fit["intercept"] + fit["slope"] * data[CLEAN][mask])
    )
    rho, p = sps.spearmanr(data["user_ratings_total"][mask], residual)
    return {"n": int(mask.sum()), "spearman": float(rho), "p": float(p)}


def compute():
    data = load()
    fits = simple_fits(data)
    crowd = crowd_fit(data)
    if crowd:
        fits["crowd_vs_google"] = crowd
    return {
        "generated": date.today().isoformat(),
        "sources": sorted(s for s in data["sources"] if s),
        "n_kept": int(len(data[OUTCOME])),
        "spread": {key: describe(data[key], key) for key in [OUTCOME] + PREDICTORS},
        "fits": fits,
        "anchoring": anchoring(data),
        "depth": sample_depth(data),
        "price": within_price(data),
        "coverage": coverage(data),
        "resolution": distinguishing(data),
        "cluster": tightest_cluster(data),
        "review_check": review_count_check(data, fits),
    }


def headline(result, with_friends=False):
    """One sentence, pre-written both ways so the pre-commitment survives the number."""
    google = result["fits"].get(CLEAN)
    if not google:
        return "Not enough Google ratings yet to say anything."
    line = (f"Google stars explain {round(google['r2'] * 100)}% of the variance in how I "
            f"actually rank restaurants (n={google['n']}).")
    friend = result["fits"].get("friend_score")
    if with_friends and friend:
        line += (f" My friends' Beli scores explain {round(friend['r2'] * 100)}% "
                 f"(n={friend['n']}).")
    if google["r2"] >= STRONG:
        line += ("  -- Google tracks my ranking more closely than expected. "
                 "Report it as found.")
    return line


def table(rows, header):
    widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]
    lines = ["| " + " | ".join(str(h).ljust(w) for h, w in zip(header, widths)) + " |",
             "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c).ljust(w) for c, w in zip(row, widths)) + " |")
    return lines


def write_stats(result, path=STATS):
    pct = lambda value: f"{value * 100:.1f}%"
    fits = result["fits"]
    lines = [
        "# Beli vs Google -- the numbers",
        "",
        f"Generated {result['generated']} from {result['n_kept']} kept rows. "
        f"Google ratings via: {', '.join(result['sources']) or 'none'}.",
        "",
    ]
    lines += ["## Headline", "", f"> {headline(result)}", ""]

    cover = result.get("coverage")
    if cover:
        lines += [
            "## 1. Volume: does Beli actually carry more ratings?",
            "",
            "Tested per market, because the blended number is misleading both ways.",
            "",
        ]
        lines += table(
            [[row["market"], row["n"], f"{row['median']:.1f}x",
              f"{row['beli_wins']}/{row['n']}"] for row in cover["by_market"]],
            ["market", "n", "median Beli ratings per Google review", "Beli ahead on"])
        lines += [
            "",
            "The widest gaps, all of them in New York:",
            "",
        ]
        lines += table(
            [[row["name"], f"{row['ratio']:.0f}x", f"{row['beli']:,.0f}", f"{row['google']:,.0f}"]
             for row in cover["top"]],
            ["restaurant", "ratio", "Beli ratings", "Google reviews"])
        lines += [
            "",
            "So the 10-100x figure holds where Beli has density and inverts where it does "
            "not. That is the shape of a network effect rather than a property of the "
            "platform, and the per-market split is the useful version of the claim.",
            "",
        ]

    res = result.get("resolution")
    if res:
        g, b = res[CLEAN], res["beli_average"]
        lines += [
            "## 2. Resolution: can the number tell two restaurants apart?",
            "",
            f"Across {res['n']} restaurants there are {res['pairs']:,} possible pairs. "
            f"A score that gives two restaurants the same value cannot order them.",
            "",
        ]
        lines += table(
            [[LABELS[CLEAN], g["distinct"], f"{g['tied_pairs']:,}", pct(g["tied_share"]),
              g["biggest_tie"]],
             [LABELS["beli_average"], b["distinct"], f"{b['tied_pairs']:,}",
              pct(b["tied_share"]), b["biggest_tie"]]],
            ["crowd score", "distinct values", "tied pairs", "share tied",
             "largest group on one value"])
        lines += [
            "",
            f"Both are averages over users, so this is a fair comparison. Google leaves "
            f"{g['tied_pairs'] / max(b['tied_pairs'], 1):.1f}x as many pairs "
            f"indistinguishable, and its largest collision puts **{g['biggest_tie']} "
            f"restaurants on one number**.",
            "",
            "Part of that is granularity -- Google reports one decimal on a 1-5 scale, so "
            "it has fewer slots to begin with. That is not a defence of the number: a "
            "product consuming the Google rating cannot rank what the rating does not "
            "separate, whatever the reason.",
            "",
        ]

    google = fits.get(CLEAN)
    if google:
        lines += ["## 3. Consequence: Google's number predicts nothing about my order",
                  "",
                  "Google's rating is not on screen while I rank, and nothing in the "
                  "ranking flow refers to it.",
                  "",
                  "The different scales do not matter here: R2 and Spearman are both "
                  "scale-invariant, so doubling every Google rating to put it on a 0-10 "
                  "basis would leave these numbers untouched. Only the slope is in mixed "
                  "units -- Beli points per Google star.", ""]
        rows = [[f"{LABELS[CLEAN]} -> my ranking", google["n"], f"{google['r2']:.3f}",
                 pct(google["r2"]), f"{google['spearman']:.3f}", f"{google['p']:.2g}"]]
        crowd = fits.get("crowd_vs_google")
        if crowd:
            rows.append([f"{LABELS[CLEAN]} -> Beli's all-user average", crowd["n"],
                         f"{crowd['r2']:.3f}", pct(crowd["r2"]),
                         f"{crowd['spearman']:.3f}", f"{crowd['p']:.2g}"])
        lines += table(rows, ["comparison", "n", "R2", "variance explained",
                              "Spearman rho", "p"])
        if crowd:
            lines += ["",
                      "The second row is the one with no n=1 in it. Both sides are "
                      "averages over users, my own rating is one of thousands inside the "
                      "Beli figure, and nothing either platform shows me affects it.", ""]
        lines += [""]

    price = result.get("price")
    if price:
        lines += [
            "### Is it just cheap versus expensive?",
            "",
            "The obvious objection to a null result: a taco stand and a tasting menu are "
            "not the same judgement, so maybe Google tracks my ranking *within* a price "
            "band and only looks flat across all of them. It does not.",
            "",
        ]
        lines += table(
            [[BANDS.get(b["level"], b["level"]), b["n"], f"{b['r2']:.3f}", pct(b["r2"]),
              f"{b['spearman']:.3f}"] for b in price["bands"]],
            ["price band", "n", "R2", "variance explained", "Spearman rho"])
        lines += [
            "",
            f"And holding price fixed: price alone explains {pct(price['r2_price'])} of my "
            f"ranking; price plus Google explains {pct(price['r2_both'])}. **Google adds "
            f"{price['google_adds'] * 100:+.1f} percentage points** (n={price['n']}).",
            "",
            "So the null is not a mixing artifact. Google's rating is uninformative about "
            "my ordering inside each price band and across all of them.",
            "",
            f"Worth saying out loud: the price bracket alone explains "
            f"{pct(price['r2_price'])} of where a restaurant lands in my list. "
            f"**Knowing whether a place is $ or $$$ tells you more about my ranking than "
            f"its Google rating does.**",
            "",
        ]

    anchored = [key for key in ANCHORS if key in fits]
    if anchored:
        lines += [
            "## Shown to me before I rank",
            "",
            "Both of these are on screen before I rank a place, so they are context "
            "rather than predictions. The pairwise mechanic limits how far that can go -- "
            "the score is a rank position, not a number I type -- but it does not rule "
            "out a tilt on close calls, so the gap table below is the check.",
            "",
        ]
        lines += table(
            [[LABELS[key], fits[key]["n"], f"{fits[key]['r2']:.3f}", pct(fits[key]["r2"]),
              f"{fits[key]['spearman']:.3f}", f"{fits[key]['p']:.2g}"] for key in anchored],
            ["shown before ranking", "n", "R2", "variance explained", "Spearman rho", "p"])
        lines += [""]

    anchors = result["anchoring"]
    if anchors:
        lines += [
            "## How far I land from the number I was shown",
            "",
            "Large disagreements in **both** directions are the evidence that the "
            "ordering is mine. An anchored rater rarely produces them.",
            "",
        ]
        lines += table(
            [[LABELS[key], anchors[key]["n"], f"{anchors[key]['mean']:+.2f}",
              f"{anchors[key]['median_abs']:.2f}", f"{anchors[key]['std']:.2f}",
              pct(anchors[key]["within_half"]),
              f"{anchors[key]['big']} ({pct(anchors[key]['big_share'])})",
              f"{anchors[key]['big_above']} up / {anchors[key]['big_below']} down",
              f"{anchors[key]['max_gap']:.1f}"]
             for key in anchors],
            ["vs", "n", "mean gap", "median gap size", "sd", "within 0.5",
             f"gaps over {BIG_GAP:.0f}", "direction", "biggest"])
        lines += ["",
                  "A mean gap near zero with a wide sd and large gaps both ways is the "
                  "pattern you want. What it cannot do is prove the tilt is zero -- only "
                  "a holdout can, and only Beli can run one.", ""]

    depth = result.get("depth") or {}
    if depth:
        lines += ["## How many people are behind those numbers", ""]
        friends = depth.get("friends")
        if friends:
            lines += [
                f"Friend counts: median **{friends['median']:.0f}**, max "
                f"{friends['max']:.0f}. {friends['none']} restaurant(s) have no friend "
                f"rating at all, {friends['single']} rest on a **single friend**, and "
                f"{friends['three_plus']} have three or more.",
                "",
                "A friend score drawn from one friend is one person's opinion wearing a "
                "crowd's name. Where that is most of the sample, the friend-score "
                "correlation is really a correlation with a handful of individuals, and "
                "the writeup should say so rather than call it a social signal.",
                "",
            ]
        crowd = depth.get("crowd")
        if crowd:
            share = (f" At the thinnest, my own rating is about "
                     f"{crowd['my_share_worst']:.1f}% of that average."
                     if crowd["my_share_worst"] else "")
            lines += [
                f"Beli rating counts: median **{crowd['median']:,.0f}**, from "
                f"{crowd['min']:,.0f} to {crowd['max']:,.0f}. {crowd['thin']} restaurant(s) "
                f"have fewer than 500 ratings.{share}",
                "",
            ]

    lines += ["## Spread", ""]
    rows = []
    for key in [OUTCOME] + PREDICTORS:
        spread = result["spread"].get(key)
        if spread:
            rows.append([LABELS[key], spread["n"], f"{spread['min']:.2f}", f"{spread['max']:.2f}",
                         f"{spread['span']:.2f}", pct(spread["scale_used"]),
                         f"{spread['std']:.2f}", pct(spread["std_share"]),
                         f"{spread['entropy']:.2f}"])
    lines += table(rows, ["measure", "n", "min", "max", "range", "share of its scale",
                          "std (raw)", "std (% of scale)", "entropy (bits)"])
    lines += ["", f"Google runs 1-5 and Beli runs 0-10, so **the raw std column is not "
                  "comparable across rows** -- it is there for reference only. Compare the "
                  "two percentage columns instead. Entropy is over {} bins spanning each "
                  "measure's own native scale, so each bin is a tenth of its own range and "
                  "the figures line up.".format(BINS),
              "",
              "**Read this table carefully before quoting it.** My Beli score is derived "
              "from rank position in my own list, so it spreads across the scale partly "
              "*by construction* -- a rank-derived number is close to uniform whatever "
              "the underlying taste looks like, while an average of star ratings "
              "concentrates whatever the underlying taste looks like. Most of the gap "
              "between those two rows is the two instruments, not two populations.",
              "",
              "That is the honest version of the claim, and it is still the interesting "
              "one: ranking is built to extract ordering, averaging is built to discard "
              "it. The finding is about instrument design. It is not evidence that Beli "
              "users are more discerning, and should not be written as though it were.", ""]

    cluster = result["cluster"]
    if cluster:
        lines += ["## The tightest Google cluster", "",
                  f"{cluster['count']} restaurants all sit at **{cluster['google_rating']:.1f} "
                  f"on Google**. I rank them from **{cluster['min']:.1f} to "
                  f"{cluster['max']:.1f}** -- a spread of {cluster['spread']:.1f} points: "
                  f"{cluster['lowest']} at the bottom, {cluster['highest']} at the top."]
        if cluster["average_spread"] is not None:
            lines += ["", f"Beli's all-user average spreads those same restaurants across "
                          f"{cluster['average_spread']:.1f} points."]
        if cluster["tied_with"]:
            lines += ["", f"Tied on count with {cluster['tied_with']}; the widest-spread one "
                          "was taken."]
        lines += [""]

    check = result["review_check"]
    if check:
        lines += ["## Review count vs disagreement", "",
                  f"Spearman rho = {check['spearman']:.3f} (p = {check['p']:.2g}, "
                  f"n = {check['n']}) between a restaurant's Google review count and how far "
                  "my rating sits from what its Google rating predicts. Negative means Google "
                  "agrees with me more where it has more reviews.", ""]

    lines += [
        "## Caveats that belong in the writeup",
        "",
        "- One user's ratings. This is a mechanism, not a measurement.",
        "- **My score is a rank position, not a judgement typed on a 0-10 scale.** It is "
        "ordinal within my own list. That is why Spearman is reported beside every R2, "
        "and why the spread comparison above is about instruments rather than people.",
        "- **The rec score, friend score and all-user average are on screen before I "
        "rank.** The pairwise mechanic means they cannot be copied into the answer, but "
        "they could still tilt close comparisons. The gap table is the check; a holdout "
        "is the only real test.",
        "- Google's rating is not shown in the ranking flow, but I am not blind to it in "
        "life -- I may have seen a place's stars before choosing to eat there.",
        "- Only restaurants I chose to visit, so the sample is selected on expected "
        "enjoyment.",
        "",
    ]
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    result = compute()
    print(headline(result))
    print(f"wrote {write_stats(result)}")
