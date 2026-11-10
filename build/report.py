"""
The report behind the image.

    python build/report.py

Reads  data/matched.csv and the analysis in analyze.py
Writes out/report.html   standalone -- the chart is embedded, so the file travels alone

The charts make the point in a few seconds; this shows the work behind them -- how the
data was collected, what was excluded, the anchoring question, and the one experiment
only Beli can run.
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
# GitHub Pages serves /docs as the site root, so the same file lives there too.
PAGES = ROOT / "docs" / "index.html"

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
    cluster = result["cluster"]
    anchors = result["anchoring"]
    cover = result.get("coverage")
    res = result.get("resolution")
    out = []

    out.append(f"""<header>
<div class="eyebrow">114 restaurants, one Beli list</div>
<h1>Does Beli&rsquo;s data say something Google&rsquo;s doesn&rsquo;t?</h1>
<p class="byline">{AUTHOR} &middot; {result['generated']}</p>
<p class="lede">Beli argues publicly that its ratings are richer and more representative
than Google&rsquo;s or Yelp&rsquo;s. I&rsquo;ve used the app for years, so I pulled the
Google rating for all 114 restaurants on my list and checked the parts of that claim an
outsider can reach. It&rsquo;s one user&rsquo;s data, so it shows a mechanism, not a
measurement.</p>
</header>""")

    out.append(f"""<figure class="figure" style="margin:0">
<img src="{image_uri}" alt="Google rating against my Beli score for 114 restaurants.
The points form a narrow vertical band with no slope.">
</figure>""")

    if google and cluster:
        out.append(f"""<section>
<h2>The headline</h2>
<p class="pull">Google stars explain {headline_pct(google['r2'])} of where a restaurant
lands in my ranking.</p>
<p>n&nbsp;=&nbsp;{google['n']}, Spearman &rho;&nbsp;=&nbsp;{google['spearman']:.2f},
p&nbsp;=&nbsp;{google['p']:.2f}. Not a weak signal. No signal. It stays flat inside every
price band too, so it isn&rsquo;t an artefact of mixing taco stands with tasting
menus.</p>
<p><strong>{cluster['count']} of my restaurants sit at exactly
{cluster['google_rating']:.1f} on Google.</strong> I rank them from {cluster['min']:.1f}
to {cluster['max']:.1f}. {cluster['highest']} is my number one. {cluster['lowest']} is
near the bottom. Google has no way to tell them apart.</p>
</section>""")

    crowd = fits.get("crowd_vs_google")
    if crowd and cluster:
        spread = ""
        if cluster.get("average_min") is not None:
            spread = (f" Inside the {cluster['count']} that Google scores "
                      f"{cluster['google_rating']:.1f}, Beli&rsquo;s users spread them "
                      f"from {cluster['average_min']:.1f} to "
                      f"{cluster['average_max']:.1f}.")
        out.append(f"""<section>
<h2>And it isn&rsquo;t just me</h2>
<p>The obvious objection is that this is one person with odd taste. So here is the same
test with me taken out of it: Google&rsquo;s rating against Beli&rsquo;s all-user
average, on the same restaurants. Both sides are now crowds.</p>
<figure class="figure"><img src="{data_uri(chart.CROWD)}"
alt="Google rating against Beli's all-user average for 113 restaurants, showing no
relationship."></figure>
<p class="pull">Google&rsquo;s rating explains {headline_pct(crowd['r2'])} of the
variance in what Beli&rsquo;s users think.</p>
<p>Spearman &rho;&nbsp;=&nbsp;{crowd['spearman']:.2f}, p&nbsp;=&nbsp;{crowd['p']:.2f}.
Thousands of Beli users on one axis, hundreds of thousands of Google reviewers on the
other, and the two are close to unrelated.{spread}</p>
<p>The clearest case is on the chart. Google puts <strong>Darrell&rsquo;s Dog Gone Good
Diner at 4.4 and Laser Wolf at 4.2</strong>, so by that measure the diner is the better
restaurant. Beli&rsquo;s users have Laser Wolf at 8.9 and Darrell&rsquo;s at 5.5. The
two populations aren&rsquo;t disagreeing at the margin, they&rsquo;re ordering things
differently.</p>
</section>""")

    if cover:
        nyc = [c for c in cover["by_market"] if c["market"] == "NYC"]
        nyc = nyc[0] if nyc else None
        top = cover["top"][0]
        rows = [[c["market"], c["n"], f'{c["median"]:.1f}&times;',
                 f'{c["beli_wins"]}/{c["n"]}'] for c in cover["by_market"]]
        out.append(f"""<section>
<h2>Volume, and where it comes from</h2>
<p>The 10&ndash;100&times; figure holds, but only where Beli has users.</p>
<figure class="figure"><img src="{data_uri(chart.COVERAGE)}"
alt="Beli ratings against Google reviews on log scales. New York points sit above the
parity line, the rest below."></figure>
{table(["market", "n", "median Beli ratings per Google review", "Beli ahead on"], rows)}
<p>In New York, Beli carries a median {nyc['median']:.0f}&times; Google&rsquo;s volume and
leads on {nyc['beli_wins']} of {nyc['n']} restaurants. The widest gap is {top['name']}:
{top['beli']:,.0f} against {top['google']:,.0f}. Outside New York it flips, and in Europe
there&rsquo;s almost nothing. That&rsquo;s a network effect rather than a property of the
platform, and the split seems more useful than a blended number hiding both halves.</p>
</section>""")

    if res:
        g, b = res[analyze.CLEAN], res["beli_average"]
        out.append(f"""<section>
<h2>Resolution</h2>
<p>Volume only matters if it buys discrimination. Of the {res['pairs']:,} pairs among
these restaurants, a score that gives both the same value can&rsquo;t order them.</p>
<figure class="figure"><img src="{data_uri(chart.DISTRIBUTION)}"
alt="Histograms of Google ratings and Beli all-user averages, each drawn across its own
full scale."></figure>
{table(["crowd score", "distinct values", "tied pairs", "share tied",
        "largest group on one value"],
       [[analyze.LABELS[analyze.CLEAN], g["distinct"], f'{g["tied_pairs"]:,}',
         pct(g["tied_share"]), g["biggest_tie"]],
        [analyze.LABELS["beli_average"], b["distinct"], f'{b["tied_pairs"]:,}',
         pct(b["tied_share"]), b["biggest_tie"]]])}
<p>Both are averages over users, so this is like for like. Google leaves
{g["tied_pairs"] / max(b["tied_pairs"], 1):.1f}&times; as many pairs indistinguishable.
Some of that is granularity, since one decimal on a 1&ndash;5 scale gives Google fewer
slots. I don&rsquo;t think that rescues it. A product reading the Google rating
can&rsquo;t rank what the rating doesn&rsquo;t separate.</p>
</section>""")

    if anchors:
        gap_rows = [[analyze.LABELS[key], anchors[key]["n"],
                     f'{anchors[key]["mean"]:+.2f}', f'{anchors[key]["median_abs"]:.2f}',
                     f'{anchors[key]["big"]} ({pct(anchors[key]["big_share"])})',
                     f'{anchors[key]["big_above"]} up / {anchors[key]["big_below"]} down']
                    for key in anchors]
        sig_rows = []
        for key in [analyze.CLEAN] + analyze.ANCHORS:
            fit = fits.get(key)
            if fit:
                sig_rows.append([analyze.LABELS[key], fit["n"], f'{fit["r2"]:.3f}',
                                 pct(fit["r2"], 1), f'{fit["spearman"]:.2f}'])
        out.append(f"""<section>
<h2>Am I just echoing what I was shown?</h2>
<p>Beli&rsquo;s own scores do track my ranking, and they&rsquo;re on screen before I rank,
so it&rsquo;s the first thing worth checking.</p>
{table(["predictor", "n", "R&sup2;", "variance explained", "rank correlation"], sig_rows)}
<p>The gaps say no.</p>
{table(["vs", "n", "mean gap", "median gap", f"gaps over {analyze.BIG_GAP:.0f}",
        "direction"], gap_rows)}
<p>Mean gap near zero, and the big disagreements run both ways in roughly equal measure.
An echo doesn&rsquo;t look like that.</p>
<div class="note"><p>A holdout would settle it across every user rather than one. Hide
the scores for a slice of raters and compare the orderings that come out. That version
needs the inside of the app, so it isn&rsquo;t a test I can run.</p></div>
</section>""")

    out.append("""<section>
<h2>What I couldn&rsquo;t test</h2>
<p>The Yelp figure, that most reviews are one star or five, is about individual reviews.
I can only see published averages. So I haven&rsquo;t tested it and I&rsquo;m not
claiming to.</p>
<p>My data is consistent with it. Polarised reviews would produce averages piled high and
narrow, and 98 of my 114 sit between 4.2 and 4.7.</p>
</section>""")

    if cover:
        out.append(f"""<section>
<h2>Three things worth looking at with the real data</h2>
<p>Not recommendations. These are the questions 114 restaurants raised and 114
restaurants can&rsquo;t answer.</p>

<h3>Where the data is already the better source</h3>
<p>The advantage tracks density, not the platform. The full dataset would show the
threshold: how many active users a metro needs before Beli becomes the better-covered
source. That line is worth knowing before deciding where anything ships.</p>

<h3>Resolution may be the harder thing to copy</h3>
<p>More ratings is a lead a competitor can close. Separating restaurants that Google puts
on the same number comes from the ranking mechanic, not from scale. Anyone who needs an
order rather than a filter can&rsquo;t get that from a star average at any volume.</p>

<h3>The edge is widest where Google is weakest</h3>
<p>Split my list by Google coverage: on the thinner half Beli carries a median
{cover['thin_google']:.1f}&times; Google&rsquo;s ratings, on the better-covered half
{cover['thick_google']:.1f}&times;. The differentiation concentrates in places Google
barely describes, which is also where a diner has least to go on.</p>
</section>""")

    return out


def method(result, rows):
    depth = result.get("depth") or {}
    friends = depth.get("friends") or {}
    thin = (f" Friend counts are small: median {friends['median']:.0f}, and "
            f"{friends['none']} restaurants have none. Read that row as a handful of "
            f"individuals rather than a crowd."
            if friends else "")
    manual = ""
    if rows:
        count = sum(1 for row in rows if row.get("source") == "manual")
        if count:
            manual = f" {count} Google ratings were typed in by hand rather than fetched."
    return f"""<section>
<h2>Method</h2>
<ul>
<li>My Beli list: name, score, rank, and the friend and all-user numbers with the count
of people behind each.{thin}</li>
<li>Google ratings from the Places API, matched on name plus city. Low-confidence
matches were held out until checked by eye, so a name collision can&rsquo;t quietly
poison the chart. 114 survived.{manual}</li>
<li>Restaurants only. Bars, bakeries and dessert places are out, since a pastry and a
tasting menu aren&rsquo;t the same judgement. That narrows the Google range slightly,
and a narrower range pulls correlations down, which happens to favour my argument.
Stating it rather than burying it.</li>
<li>My score is a rank position, not a number I type, so it&rsquo;s ordinal within my
own list. That&rsquo;s why Spearman sits beside every R&sup2;.</li>
<li>Blank cells mean unavailable, not zero, so n differs by column.</li>
</ul>
<p>What this isn&rsquo;t: a sample of Beli users, a sample of restaurants, or evidence
about anyone&rsquo;s taste but mine. Only places I chose to eat at are in it.</p>
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
    PAGES.parent.mkdir(exist_ok=True)
    PAGES.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(f"wrote {build()}")
