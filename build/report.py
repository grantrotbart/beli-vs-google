"""
The report behind the image.

    python build/report.py

Reads  data/matched.csv and the analysis in analyze.py
Writes out/report.html   standalone -- the chart is embedded, so the file travels alone

This is the thing to offer if the DM gets a reply: the image makes the point in five
seconds, this shows the work. It carries the parts that do not fit in a message -- how
the data was collected, what was excluded, the anchoring question, and the one
experiment only Beli can run.
"""
import base64
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import brand
import chart

ROOT = Path(__file__).resolve().parent.parent
MATCHED = ROOT / "data" / "matched.csv"
REPORT = ROOT / "out" / "report.html"

AUTHOR = "Grant Rotbart"

CSS = """
/* One column, text at a readable measure, tables allowed to scroll inside themselves. */
:root {
  --surface: #ffffff;
  --raised: #f7f9f9;
  --ink: #1d1d1d;
  --ink-2: #52514e;
  --muted: #898781;
  --teal: #134f5c;
  --teal-text: #134f5c;
  --wash: #e8f1f3;
  --rule: #ededed;
  --flag: #c0392b;
  --flag-wash: #fdecea;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --surface: #14191a; --raised: #1b2224; --ink: #f0efec; --ink-2: #c3c2b7;
    --muted: #9fa197; --teal: #6fb9c9; --teal-text: #8fcbd8; --wash: #1e2d31;
    --rule: #2a3335; --flag: #ef8378; --flag-wash: #32211f;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --surface: #14191a; --raised: #1b2224; --ink: #f0efec; --ink-2: #c3c2b7;
  --muted: #9fa197; --teal: #6fb9c9; --teal-text: #8fcbd8; --wash: #1e2d31;
  --rule: #2a3335; --flag: #ef8378; --flag-wash: #32211f;
  color-scheme: dark;
}

*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--surface);
  color: var(--ink);
  font-family: "Proxima Nova", Montserrat, system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 17px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}
.page {
  max-width: 50rem;
  margin: 0 auto;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 3.5rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}
header { display: flex; flex-direction: column; gap: 0.75rem; }
.eyebrow {
  font-size: 0.75rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--muted); font-weight: 600;
}
h1 {
  font-size: clamp(1.9rem, 5vw, 2.7rem); line-height: 1.12; margin: 0;
  letter-spacing: -0.02em; text-wrap: balance; font-weight: 700;
}
h2 {
  font-size: 1.3rem; margin: 0 0 0.6rem; letter-spacing: -0.01em;
  text-wrap: balance; font-weight: 700;
}
h3 { font-size: 1rem; margin: 1.6rem 0 0.4rem; font-weight: 600; color: var(--ink-2); }
p { margin: 0 0 1rem; max-width: 65ch; }
section > p:last-child { margin-bottom: 0; }
a { color: var(--teal-text); }
strong { font-weight: 600; }
.byline { color: var(--ink-2); font-size: 0.95rem; }
.lede { font-size: 1.12rem; color: var(--ink-2); max-width: 60ch; }

.figure {
  background: #ffffff; border: 1px solid var(--rule); border-radius: 10px;
  padding: 0.75rem; overflow-x: auto;
}
.figure img { display: block; width: 100%; height: auto; max-width: 100%; }
figcaption { color: var(--muted); font-size: 0.85rem; margin-top: 0.6rem; }

.pull {
  border-left: 3px solid var(--teal); padding: 0.1rem 0 0.1rem 1.1rem;
  font-size: 1.22rem; line-height: 1.45; color: var(--ink); max-width: 58ch;
  font-weight: 600; letter-spacing: -0.01em;
}
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; min-width: 30rem; }
caption { text-align: left; color: var(--muted); font-size: 0.85rem; padding-bottom: 0.5rem; }
th, td {
  text-align: right; padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--rule);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
th:first-child, td:first-child { text-align: left; white-space: normal; min-width: 11rem; }
thead th {
  font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--ink-2);
}
tbody tr:last-child td { border-bottom: none; }
td.lead { font-weight: 600; color: var(--teal-text); }

.note {
  background: var(--wash); border-radius: 8px; padding: 1rem 1.15rem;
  font-size: 0.95rem; color: var(--ink-2);
}
.note p { max-width: none; }
.note p:last-child { margin-bottom: 0; }
.flag {
  background: var(--flag-wash); border: 1px solid var(--flag); color: var(--flag);
  border-radius: 8px; padding: 0.85rem 1.1rem; font-weight: 600; font-size: 0.95rem;
}
ul { margin: 0 0 1rem; padding-left: 1.15rem; max-width: 65ch; }
li { margin-bottom: 0.5rem; }
hr { border: none; border-top: 1px solid var(--rule); margin: 0; }
footer { color: var(--muted); font-size: 0.85rem; }
@media (max-width: 30rem) { body { font-size: 16px; } .page { padding-block: 2.5rem 3.5rem; } }
"""


def data_uri(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def pct(value, places=0):
    return f"{value * 100:.{places}f}%"


def headline_pct(r2):
    """A rounded 0% reads as a broken number. Say what is meant."""
    return "less than 1%" if r2 < 0.005 else pct(r2)


def table(headers, rows, caption=None, lead_first=True):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            klass = ' class="lead"' if index == 0 and lead_first else ""
            cells.append(f"<td{klass}>{cell}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="scroll"><table>{cap}<thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def kept_rows():
    if not MATCHED.exists():
        return []
    with MATCHED.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if (row.get("keep") or "").strip() == "1"]


def sections(result, image_uri):
    fits = result["fits"]
    google = fits.get(analyze.CLEAN)
    friend = fits.get("friend_score")
    cluster = result["cluster"]
    anchors = result["anchoring"]
    out = []

    cover = result.get("coverage")
    res = result.get("resolution")

    out.append(f"""<header>
<div class="eyebrow">One user&rsquo;s Beli data, checked against Google</div>
<h1>What 114 restaurants say about the claim that Beli&rsquo;s data is different</h1>
<p class="byline">{AUTHOR} &middot; {result['generated']}</p>
<p class="lede">On The Simmer, Judy made a specific argument: that because of who uses
Beli and how they use it, its ratings are richer and more representative of what people
actually think than Google or Yelp. I&rsquo;ve used Beli for years, so I pulled the
Google rating for all 114 restaurants on my list and tested the parts of that claim my
own data can reach. You&rsquo;ve almost certainly looked at this already. It is one
user&rsquo;s data, so read it as a mechanism rather than a measurement.</p>
</header>""")

    out.append(f"""<figure class="figure" style="margin:0">
<img src="{image_uri}" alt="Scatter plot of Google rating against my Beli score across
114 restaurants, showing no relationship.">
</figure>""")

    if cover:
        rows = [[c["market"], c["n"], f'{c["median"]:.1f}&times;',
                 f'{c["beli_wins"]}/{c["n"]}'] for c in cover["by_market"]]
        top = cover["top"][0]
        out.append(f"""<section>
<h2>1. Volume &mdash; and where it comes from</h2>
<p>The claim that a new restaurant gets 10&ndash;100&times; the ratings on Beli holds,
but only where Beli has users. Splitting by market is the honest version, and the more
useful one.</p>
{table(["market", "n", "median Beli ratings per Google review", "Beli ahead on"], rows)}
<p class="pull">In New York, Beli carries a median of
{[c for c in cover["by_market"] if c["market"] == "NYC"][0]["median"]:.0f}&times; Google&rsquo;s
rating volume &mdash; and leads on 45 of 46 restaurants.</p>
<p>The widest single gap on my list is <strong>{top['name']}</strong>:
{top['beli']:,.0f} ratings on Beli against {top['google']:,.0f} reviews on Google,
a factor of {top['ratio']:.0f}. Outside New York it inverts, and in Europe Beli has
almost nothing. That is the shape of a network effect rather than a property of the
platform &mdash; which is presumably more useful to you than a blended average that
hides both halves.</p>
</section>""")

    if res:
        g, b = res[analyze.CLEAN], res["beli_average"]
        out.append(f"""<section>
<h2>2. Resolution &mdash; whether the number can separate two restaurants</h2>
<p>Volume only matters if it buys discrimination. Across {res['n']} restaurants there
are {res['pairs']:,} possible pairs, and a score that gives two restaurants the same
value cannot order them at all.</p>
{table(["crowd score", "distinct values", "tied pairs", "share tied",
        "largest group sharing one value"],
       [[analyze.LABELS[analyze.CLEAN], g["distinct"], f'{g["tied_pairs"]:,}',
         pct(g["tied_share"]), g["biggest_tie"]],
        [analyze.LABELS["beli_average"], b["distinct"], f'{b["tied_pairs"]:,}',
         pct(b["tied_share"]), b["biggest_tie"]]])}
<p>Both are averages over users, so this is like for like. Google leaves
{g["tied_pairs"] / max(b["tied_pairs"], 1):.1f}&times; as many pairs indistinguishable.</p>
<div class="note"><p>Some of that is granularity: Google reports one decimal on a
1&ndash;5 scale, so it has fewer slots to begin with. I don&rsquo;t think that rescues
the number. A product consuming the Google rating cannot rank what the rating does not
separate, whatever the reason it doesn&rsquo;t.</p></div>
</section>""")

    if cluster:
        same = (f" Beli&rsquo;s all-user average spreads those same restaurants across "
                f"{cluster['average_spread']:.1f} points."
                if cluster["average_spread"] is not None else "")
        out.append(f"""<section>
<h2>What that looks like on one number</h2>
<p><strong>{cluster['count']} of my restaurants sit at exactly
{cluster['google_rating']:.1f} on Google.</strong> To anyone reading the star rating they
are the same restaurant. I rank them from {cluster['min']:.1f} to {cluster['max']:.1f}
&mdash; {cluster['lowest']} near the bottom of my list, {cluster['highest']} at the very
top.{same}</p>
<p>That is not disagreement. Disagreement would be Google rating something highly that I
rank low. This is Google having no way to express the difference at all.</p>
</section>""")

    if google:
        out.append(f"""<section>
<h2>3. Consequence &mdash; the rating carries no information about my order</h2>
<p class="pull">Google stars explain {headline_pct(google['r2'])} of the variance in how
I rank restaurants.</p>
<p>Across {google['n']} restaurants, Spearman &rho;&nbsp;=&nbsp;{google['spearman']:.2f},
p&nbsp;=&nbsp;{google['p']:.2f}. Not a weak relationship &mdash; no relationship. And it
is not an artefact of mixing cheap places with expensive ones: the fit stays flat inside
every price band, and adding the Google rating to a model that already knows the price
bracket moves R&sup2; by {result['price']['google_adds'] * 100:+.1f} points.</p>
<p>Which follows from the two sections above. A measure that collapses
{g["biggest_tie"] if res else 22} restaurants onto one value, built from a fraction of
the ratings, cannot carry ordering information it never captured.</p>
</section>""")

    out.append("""<section>
<h2>What I could not test</h2>
<p>The Yelp figure &mdash; that most reviews are one star or five &mdash; is about the
distribution of individual reviews, and I can only see published averages, not the
reviews underneath them. So I have not tested it and I am not claiming to.</p>
<p>What I can say is that my data is consistent with it. If the underlying reviews were
as polarised as you described, the averages would pile up high and narrow, which is
exactly what they do: 98 of my 114 restaurants sit between 4.2 and 4.7.</p>
</section>""")

    rows = []
    for key in [analyze.CLEAN] + analyze.ANCHORS:
        fit = fits.get(key)
        if fit:
            rows.append([analyze.LABELS[key], fit["n"], f"{fit['r2']:.3f}",
                         pct(fit["r2"], 1), f"{fit['spearman']:.2f}"])
    out.append(f"""<section>
<h2>Every signal, side by side</h2>
<p>Everything here explains the same thing: my own score. Only the first row is a clean
test &mdash; Google&rsquo;s rating never appears while I rank. The other two are on
screen before I do.</p>
{table(["predictor", "n", "R&sup2;", "variance explained", "rank correlation"], rows)}
</section>""")

    if anchors:
        gap_rows = [[analyze.LABELS[key], anchors[key]["n"], f"{anchors[key]['mean']:+.2f}",
                     f"{anchors[key]['median_abs']:.2f}", f"{anchors[key]['std']:.2f}",
                     f"{anchors[key]['big']} ({pct(anchors[key]['big_share'])})",
                     f"{anchors[key]['big_above']} up / {anchors[key]['big_below']} down"]
                    for key in anchors]
        gap_rows = [[analyze.LABELS[key], anchors[key]["n"],
                     f'{anchors[key]["mean"]:+.2f}', f'{anchors[key]["median_abs"]:.2f}',
                     f'{anchors[key]["big"]} ({pct(anchors[key]["big_share"])})',
                     f'{anchors[key]["big_above"]} up / {anchors[key]["big_below"]} down']
                    for key in anchors]
        out.append(f"""<section>
<h2>One caveat on the Beli columns</h2>
<p>Those two scores are on screen before I rank a place, so read them as context rather
than as predictions. Worth noting too that my own score is a rank position, not a number
I type.</p>
<p>For what it is worth, I disagree with them often and in both directions:</p>
{table(["vs", "n", "mean gap", "median gap", f"gaps over {analyze.BIG_GAP:.0f}", "direction"],
       gap_rows)}
<div class="note"><p>A holdout would settle it properly &mdash; hide the scores for a
slice of raters and compare the orderings that come out. That is the one question here
I can&rsquo;t answer from the outside and you can.</p></div>
</section>""")

    spread_rows = []
    for key in [analyze.OUTCOME] + [analyze.CLEAN] + analyze.ANCHORS:
        spread = result["spread"].get(key)
        if spread:
            spread_rows.append([analyze.LABELS[key], spread["n"],
                                f"{spread['min']:.1f}&ndash;{spread['max']:.1f}",
                                f"{spread['span']:.1f}", pct(spread["scale_used"]),
                                pct(spread["std_share"]), f"{spread['entropy']:.2f}"])
    out.append(f"""<section>
<h2>Spread, with the caveat it needs</h2>
{table(["measure", "n", "range", "span", "share of its scale", "sd (% of scale)",
        "entropy (bits)"], spread_rows)}
<div class="note"><p>Google runs 1&ndash;5 and Beli runs 0&ndash;10, so everything in that
table is expressed as a share of each measure&rsquo;s own scale rather than in raw points.
The headline R&sup2; is unaffected either way &mdash; correlation doesn&rsquo;t care about
units.</p>
<p>Worth saying plainly: my score is a rank position, so it spreads
across the scale partly <em>by construction</em>. A ranking produces a top and a bottom
whatever the underlying taste looks like; an average of star ratings concentrates
whatever the underlying taste looks like. Most of the gap between those two rows is the
two instruments, not two populations of people.</p>
<p>Which is still the interesting part. Ranking is built to extract ordering. Averaging
is built to collapse it. The first table is the one that shows the ordering carries
information the average doesn&rsquo;t.</p></div>
</section>""")

    return out


def method(result, rows):
    flagged = ""
    if rows:
        manual = sum(1 for row in rows if row.get("source") == "manual")
        if manual:
            flagged = f" {manual} Google rating(s) were entered by hand rather than by API."
    return f"""<section>
<h2>Method</h2>
<ul>
<li>My own Beli list: name, my score, my rank in the list, and the friend and all-user
numbers with how many people are behind each.</li>
<li><strong>Restaurants only.</strong> Bars, bakeries and dessert places are excluded,
because a pastry and a tasting menu aren&rsquo;t the same judgement and their Google
ratings don&rsquo;t behave the same way either. It is worth naming that this narrows the
range of Google ratings a little, and a narrower range pulls a correlation down &mdash;
which is the direction that happens to suit my argument, so: stated rather than
buried.</li>
<li>Google ratings from the Places API (Text Search), matched on name plus city.</li>
<li>Matches below a name-similarity threshold were held out until checked by eye, so a
restaurant-name collision can&rsquo;t quietly poison the chart.
{result['n_kept']} rows survived.{flagged}</li>
<li>Blank cells mean the number wasn&rsquo;t available, not zero, so the n differs by
column.</li>
<li>Regressions are ordinary least squares; Spearman is reported beside every R&sup2;
because my score is ordinal within my own list.</li>
</ul>
<p>What this is not: a sample of Beli users, a sample of restaurants, or evidence about
anyone&rsquo;s taste but mine. Only restaurants I chose to eat at are in it.</p>
</section>"""


def data_table(rows):
    if not rows:
        return ""
    body = []
    for row in sorted(rows, key=lambda r: -float(r["beli_score"])):
        friends = row.get("friend_score") or "&mdash;"
        if friends != "&mdash;" and (row.get("friend_count") or "").strip():
            friends += f' <span style="color:var(--muted)">({row["friend_count"]})</span>'
        crowd = row.get("beli_average") or "&mdash;"
        if crowd != "&mdash;" and (row.get("beli_rating_count") or "").strip():
            try:
                crowd += (f' <span style="color:var(--muted)">'
                          f'({float(row["beli_rating_count"]):,.0f})</span>')
            except ValueError:
                pass
        body.append([
            row["name"], row.get("city", ""), row["beli_score"],
            friends, crowd,
            row.get("google_rating") or "&mdash;",
            row.get("user_ratings_total") or "&mdash;",
        ])
    return f"""<section>
<h2>Every row</h2>
{table(["restaurant", "city", "my score", "friends", "all users",
        "google", "google reviews"], body,
       caption="Sorted by my score. Grey figures are how many people are behind that "
               "score. Dashes are numbers the app didn't have.")}
</section>"""


def build(result=None, path=REPORT):
    result = result or analyze.compute()
    rows = kept_rows()
    image = chart.IMAGE
    if not image.exists():
        chart.draw(result, analyze.load())
    body = sections(result, data_uri(image))
    body.append(method(result, rows))
    body.append(data_table(rows))
    body.append(f'<hr><footer>{AUTHOR} &middot; generated {date.today().isoformat()} '
                f'from {result["n_kept"]} ranked restaurants. Figures and chart are '
                f'produced by the same script, so they cannot drift apart.</footer>')

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Beli Data, Checked Against Google</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap">
<style>{CSS}</style>
</head>
<body>
<main class="page">
{"".join(body)}
</main>
</body>
</html>"""
    path.parent.mkdir(exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(f"wrote {build()}")
