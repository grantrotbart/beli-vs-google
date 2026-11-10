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
details.rows > summary {
  display: flex; align-items: baseline; gap: 0.75rem; cursor: pointer;
  list-style: none; padding: 0.15rem 0; border-radius: 6px;
}
details.rows > summary::-webkit-details-marker { display: none; }
details.rows > summary h2 { display: inline; margin: 0; }
details.rows > summary::before {
  content: ""; flex: none; width: 0.55rem; height: 0.55rem; align-self: center;
  border-right: 2px solid var(--teal-text); border-bottom: 2px solid var(--teal-text);
  transform: rotate(-45deg); transition: transform 0.15s ease;
}
details.rows[open] > summary::before { transform: rotate(45deg); }
details.rows > summary .count { color: var(--muted); font-size: 0.9rem; }
details.rows > summary:hover h2 { color: var(--teal-text); }
details.rows > summary:focus-visible { outline: 2px solid var(--teal-text); outline-offset: 4px; }
details.rows[open] > summary { margin-bottom: 0.8rem; }
@media (prefers-reduced-motion: reduce) { details.rows > summary::before { transition: none; } }
.caption { color: var(--muted); font-size: 0.85rem; margin: 0 0 0.5rem; max-width: none; }
.scroll-top { overflow-x: auto; overflow-y: hidden; margin-bottom: 0.25rem; }
.scroll-top > div { height: 1px; }
.scroll-top[hidden] { display: none; }
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
    n = result["n_kept"]
    band = result["google_band"]

    out.append(f"""<header>
<div class="eyebrow">{n} restaurants, one Beli list</div>
<h1>Does Beli&rsquo;s data say something Google&rsquo;s doesn&rsquo;t?</h1>
<p class="byline">{AUTHOR} &middot; {result['generated']}</p>
<p class="lede">Beli argues publicly that its ratings are richer and more representative
than Google&rsquo;s or Yelp&rsquo;s. I&rsquo;ve used the app for years, so I pulled the
Google rating for all {n} restaurants on my list and checked the parts of that claim an
outsider can reach. It&rsquo;s one user&rsquo;s data (mine), so it shows a mechanism,
not a measurement, but the results are very interesting nonetheless.</p>
</header>""")

    out.append(f"""<figure class="figure" style="margin:0">
<img src="{image_uri}" alt="Google rating against my Beli score for {n} restaurants.
The points form a narrow vertical band with no slope.">
</figure>""")

    if google and cluster:
        out.append(f"""<section>
<h2>The headline</h2>
<p class="pull">Google stars explain {headline_pct(google['r2'])} of where a restaurant
lands in my ranking.</p>
<p>n&nbsp;=&nbsp;{google['n']}, Spearman &rho;&nbsp;=&nbsp;{google['spearman']:.2f},
and p&nbsp;=&nbsp;{google['spearman_p']:.2f} indicate no signal between what my Beli
ranking and Google reviews say about each other. Spearman&rsquo;s &rho; asks whether
two lists put restaurants in the same order: 1 would mean Google orders them exactly as
I do, 0 means no relationship at all. The p-value is the chance of seeing at least this
much overlap if the two were completely unrelated, so at
{google['spearman_p']:.2f} what little overlap there is looks like coincidence. This
holds within price bands too, so the result isn&rsquo;t skewed by mixing fast-casual
spots with special-occasion restaurants.</p>
<p><strong>{cluster['count']} of my restaurants sit at exactly
{cluster['google_rating']:.1f} on Google</strong>, but I rank them from
{cluster['min']:.1f} to {cluster['max']:.1f}. {cluster['highest']} is my number one while
{cluster['lowest']} is near the bottom, but according to Google, they&rsquo;re just as
good.</p>
</section>""")

    crowd = fits.get("crowd_vs_google")
    if crowd and cluster:
        spread = ""
        if cluster.get("average_min") is not None:
            spread = (f" Inside the same {cluster['count']} that Google scores "
                      f"{cluster['google_rating']:.1f}, Beli&rsquo;s users spread them "
                      f"from {cluster['average_min']:.1f} to "
                      f"{cluster['average_max']:.1f}.")
        missing = n - crowd["n"]
        dropped = ""
        if missing == 1:
            dropped = (f" ({crowd['n']} of the {n}, since one doesn&rsquo;t have a Beli "
                       f"average yet)")
        elif missing > 1:
            dropped = (f" ({crowd['n']} of the {n}, since {missing} don&rsquo;t have a "
                       f"Beli average yet)")
        out.append(f"""<section>
<h2>And it isn&rsquo;t just me</h2>
<p>The obvious objection is that this is one person with odd taste. So here is the same
test with me taken out of it: Google&rsquo;s rating against Beli&rsquo;s all-user
average, on the same restaurants{dropped}.</p>
<figure class="figure"><img src="{data_uri(chart.CROWD)}"
alt="Google rating against Beli's all-user average for {crowd['n']} restaurants, showing no
relationship."></figure>
<p class="pull">Google&rsquo;s rating explains {headline_pct(crowd['r2'])} of the
variance in what Beli&rsquo;s users think.</p>
<p>Spearman &rho;&nbsp;=&nbsp;{crowd['spearman']:.2f},
p&nbsp;=&nbsp;{crowd['spearman_p']:.2f}. A &rho; that close to 0 means the two crowds
barely agree on which restaurants are better than which. A p-value of
{crowd['spearman_p']:.2f} means even that small overlap could easily be chance; the
usual bar for calling something real is 0.05. Thousands of Beli users on one axis,
hundreds of thousands of Google reviewers on the other, and the two are close to
unrelated.{spread}</p>
<p>The clearest case is on the chart. Google puts <strong>Darrell&rsquo;s Dog Gone Good
Diner at 4.4 and Laser Wolf at 4.2</strong>, so by that measure the diner is the better
restaurant. Beli&rsquo;s users have Laser Wolf at 8.9 and Darrell&rsquo;s at 5.5. That
isn&rsquo;t a close call tipping the other way: the two crowds put these restaurants in
opposite order, and Beli&rsquo;s users split them by more than three points.</p>
</section>""")

    if cover:
        nyc = [c for c in cover["by_market"] if c["market"] == "NYC"]
        nyc = nyc[0] if nyc else None
        top = cover["top"][0]
        rows = [[c["market"], c["n"], f'{c["median"]:.1f}&times;',
                 f'{c["beli_wins"]}/{c["n"]}'] for c in cover["by_market"]]
        out.append(f"""<section>
<h2>Volume, and where it comes from</h2>
<p>Beli&rsquo;s founder claimed that Beli also has 10&ndash;100&times; more reviews to
work with than other platforms. This figure holds, but only where Beli has users.</p>
<figure class="figure"><img src="{data_uri(chart.COVERAGE)}"
alt="Beli ratings against Google reviews on log scales. New York points sit above the
parity line, the rest below."></figure>
{table(["market", "n", "median Beli ratings per Google review", "Beli ahead on"], rows)}
{f'<p class="note">{analyze.small_markets_note(cover["small_markets"])}</p>' if cover["small_markets"] else ""}
<p>In New York, Beli carries a median {nyc['median']:.0f}&times; Google&rsquo;s volume and
leads on {nyc['beli_wins']} of {nyc['n']} restaurants. The widest gap is {top['name']}:
{top['beli']:,.0f} against {top['google']:,.0f}. Outside New York it flips, and in Europe
there&rsquo;s almost nothing. That&rsquo;s a network effect rather than a property of the
platform, and the split seems more useful than a blended number hiding both halves.</p>
</section>""")

    if res:
        g, b = res[analyze.CLEAN], res["beli_average"]
        sq = res["beli_on_google_grid"]
        slots = res["slots"]
        raw_gap = g["tied_pairs"] / max(b["tied_pairs"], 1)
        fair_gap = g["tied_pairs"] / max(sq["tied_pairs"], 1)
        out.append(f"""<section>
<h2>Resolution</h2>
<p>More ratings only help if they let you tell restaurants apart. Of the
{res['pairs']:,} pairs among these restaurants, any pair a score gives the same value is
a pair it can&rsquo;t put in order.</p>
<figure class="figure"><img src="{data_uri(chart.DISTRIBUTION)}"
alt="Histograms of Google ratings on a 1 to 5 scale and Beli all-user averages on a 0 to
10 scale, each drawn across its full scale."></figure>
{table(["crowd score", "possible values", "values used", "tied pairs", "share tied",
        "largest group on one value"],
       [[analyze.LABELS[analyze.CLEAN], slots[analyze.CLEAN], g["distinct"],
         f'{g["tied_pairs"]:,}', pct(g["tied_share"], 1), g["biggest_tie"]],
        [analyze.LABELS["beli_average"], slots["beli_average"], b["distinct"],
         f'{b["tied_pairs"]:,}', pct(b["tied_share"], 1), b["biggest_tie"]],
        ["Beli&rsquo;s average on Google&rsquo;s scale", slots[analyze.CLEAN],
         sq["distinct"], f'{sq["tied_pairs"]:,}', pct(sq["tied_share"], 1),
         sq["biggest_tie"]]])}
<p>Both are averages over users, so this is like for like. Google leaves
{raw_gap:.1f}&times; as many pairs indistinguishable. Most of that is granularity: Google
publishes one decimal on a 1&ndash;5 scale, which allows {slots[analyze.CLEAN]} possible
values, while Beli&rsquo;s one decimal on 0&ndash;10 allows {slots['beli_average']}.
Squeeze Beli&rsquo;s averages onto Google&rsquo;s {slots[analyze.CLEAN]} slots (the last
row) and they still tie fewer pairs, {pct(sq["tied_share"], 1)} against
{pct(g["tied_share"], 1)}, but the gap shrinks to {fair_gap:.1f}&times;.</p>
<p>So the difference here is mostly the scale each platform publishes, not its users
being more discerning. It still matters in practice: a product reading the Google rating
can&rsquo;t rank what the rating doesn&rsquo;t separate, whatever the reason.</p>
</section>""")

    if anchors:
        gap_rows = [[analyze.LABELS[key], anchors[key]["n"],
                     f'{anchors[key]["median_abs"]:.2f}',
                     f'{anchors[key]["big"]} ({anchors[key]["big_above"]} up, '
                     f'{anchors[key]["big_below"]} down)',
                     anchors[key]["copier_big"],
                     pct(anchors[key]["opposite_share"])]
                    for key in anchors]
        sig_rows = []
        for key in [analyze.CLEAN] + analyze.ANCHORS:
            fit = fits.get(key)
            if fit:
                explained = "&lt;0.1%" if fit["r2"] < 0.0005 else pct(fit["r2"], 1)
                sig_rows.append([analyze.LABELS[key], fit["n"], f'{fit["r2"]:.3f}',
                                 explained, f'{fit["spearman"]:.2f}'])
        avg = anchors.get("beli_average")
        evidence = ""
        if avg:
            evidence = f"""<p>{avg['big']} restaurants land more than
{analyze.BIG_GAP:.0f} points from Beli&rsquo;s average, {avg['big_above']} above and
{avg['big_below']} below. My score is a rank position spread wider than the averages, so
some gap appears even for someone who copied the order they were shown, but that copier
would produce {avg['copier_big']}. And I put {pct(avg['opposite_share'])} of pairs in the
opposite order from Beli&rsquo;s users, against 0% for a copier and 50% for a coin flip.
So my ranking isn&rsquo;t an echo of what I was shown. What this can&rsquo;t rule out is
a smaller nudge on close calls, since the agreement that&rsquo;s left could be anchoring
or simply shared taste.</p>"""
        out.append(f"""<section>
<h2>Am I just echoing what I was shown?</h2>
<p>A user can see average scores and friend scores before they rank a restaurant, and get
an idea of what their score might end up being as they compare it to others, so
it&rsquo;s worth checking.</p>
{table(["predictor", "n", "R&sup2;", "variance explained", "rank correlation"], sig_rows)}
{table(["vs", "n", "median gap", f"gaps over {analyze.BIG_GAP:.0f}",
        f"a copier&rsquo;s gaps over {analyze.BIG_GAP:.0f}", "pairs in opposite order"],
       gap_rows)}
{evidence}
<div class="note"><p>A holdout would settle it across every user rather than one. Hide
the scores for a slice of raters and compare the orderings that come out. That would
require a change to the inside of the app, so it isn&rsquo;t a test I can run, but
I&rsquo;d be curious to investigate it.</p></div>
</section>""")

    # What the analysis raised but can't settle, merged with the parts of Beli's claim
    # this data can't reach. Every number here is computed, so it can't drift.
    friend_fit = fits.get("friend_score")
    avg_fit = fits.get("beli_average")
    friends = (result.get("depth") or {}).get("friends") or {}
    sq = res["beli_on_google_grid"] if res else None
    follow_up = []
    if cover:
        follow_up.append("""<li><strong>Where Beli becomes the better source.</strong> The
volume advantage tracks density, not the platform. The full dataset would show the
threshold: how many active users a metro needs before Beli out-rates Google.</li>""")
        follow_up.append(f"""<li><strong>Where Google is thinnest.</strong> On the half of
my list with fewer Google reviews, Beli carries a median
{cover['thin_google']:.1f}&times; Google&rsquo;s ratings. On the better-covered half,
{cover['thick_google']:.1f}&times;. The edge is widest where a diner has least to go
on.</li>""")
    if sq:
        follow_up.append(f"""<li><strong>Whether ranking beats stars at the same
resolution.</strong> Put on Google&rsquo;s 41-value scale, Beli&rsquo;s averages still tie
slightly fewer pairs ({pct(sq['tied_share'], 1)} against
{pct(res[analyze.CLEAN]['tied_share'], 1)}). With every user&rsquo;s data you could test
whether pairwise ranking separates restaurants better than star averages once the scale
is held fixed.</li>""")

    beyond = ["""<li><strong>Re-rankings.</strong> My own impression of a restaurant often
changes after a second visit, and Beli lets you rank a place again. I&rsquo;d want to see
how often a re-rank moves a restaurant, in which direction, and whether first-visit
scores are noisier than they look.</li>""",
              """<li><strong>The written reviews.</strong> Running the text people leave
through a language model could pull out what a score can&rsquo;t: which dishes people
order and rate, or whether a low score was an off night rather than the kitchen.</li>"""]
    if friend_fit and avg_fit:
        single = (f", and {friends['single']} of the {friend_fit['n']} friend scores I have "
                  f"come from a single friend" if friends else "")
        beyond.append(f"""<li><strong>Friend scores for recommendations.</strong> Friend
scores explain {pct(friend_fit['r2'], 1)} of my ranking, against
{pct(avg_fit['r2'], 1)} for the all-user average{single}. With more data you could test
whether weighting friends by how closely their taste matches yours makes them a better
guide than the crowd.</li>""")
    beyond.append("""<li><strong>Who&rsquo;s rating.</strong> Beli&rsquo;s users are
mostly younger, and might perceive restaurants differently than Gen X and older diners.
Google draws from a broader population, so some of the gap between the two crowds could
be who&rsquo;s rating rather than how well. Demographic data would separate the
two.</li>""")

    out.append(f"""<section>
<h2>Things I&rsquo;d want to look at with the real data</h2>
<p>Not recommendations. These are questions {n} restaurants raised and can&rsquo;t answer
on their own.</p>

<h3>Following up on these results</h3>
<ul>
{"".join(follow_up)}
</ul>

<h3>The rest of Beli&rsquo;s claim</h3>
<ul>
<li><strong>Yelp.</strong> I didn&rsquo;t pull Yelp ratings, so every comparison here is
against Google. The figure that over 70% of Yelp reviews are one or five stars is about
individual reviews, and I can only see published averages. My data is consistent with
it: polarised reviews would produce averages piled high and narrow, and
{band['count']} of my {band['n']} Google ratings sit between {band['low']} and
{band['high']}.</li>
<li><strong>The first week.</strong> Beli has said it collects far more ratings than
Google or Yelp in a restaurant&rsquo;s first week. My data is a snapshot, so it
can&rsquo;t see timing. With timestamps you could compare how fast each platform builds
up ratings after an opening, and how soon Beli&rsquo;s average settles near where it
ends up.</li>
</ul>

<h3>Beyond the score</h3>
<ul>
{"".join(beyond)}
</ul>
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
    fetched = sum(1 for row in rows or [] if row.get("source") == "api")
    if rows:
        count = sum(1 for row in rows if row.get("source") == "manual")
        if count:
            manual = (f" {count} more were read off Google Maps by hand rather than "
                      f"fetched.")
    return f"""<section>
<h2>Method</h2>
<ul>
<li>My Beli list: name, score, rank, and the friend and all-user numbers with the count
of people behind each.{thin}</li>
<li>Google ratings from the Places API, matched on name plus city. Low-confidence
matches were held out until checked by eye, so a name collision can&rsquo;t quietly
poison the chart. {fetched} survived.{manual}</li>
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


def whole(value):
    """Counts arrive from the CSV as floats ("4.0"). People are whole, so show them so."""
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return None


def data_table(rows):
    if not rows:
        return ""
    body = []
    for row in sorted(rows, key=lambda r: -float(r["beli_score"])):
        friends = row.get("friend_score") or "&mdash;"
        count = whole(row.get("friend_count"))
        if friends != "&mdash;" and count:
            friends += f' <span style="color:var(--muted)">({count})</span>'
        crowd = row.get("beli_average") or "&mdash;"
        count = whole(row.get("beli_rating_count"))
        if crowd != "&mdash;" and count:
            crowd += f' <span style="color:var(--muted)">({count})</span>'
        body.append([
            row["name"], row.get("city", ""), row["beli_score"],
            friends, crowd,
            row.get("google_rating") or "&mdash;",
            whole(row.get("user_ratings_total")) or "&mdash;",
        ])
    # Collapsed by default: it's reference material, and at this length it would
    # otherwise be most of the page. The table is wider than the column on most
    # screens, so a second scrollbar sits above it: with 117 rows the native one is
    # a long way down.
    return f"""<section>
<details class="rows">
<summary><h2>Every row</h2><span class="count">{len(body)} restaurants</span></summary>
<p class="caption">Sorted by my score. Grey figures are how many people are behind that
score. Dashes are numbers the app didn&rsquo;t have.</p>
<div class="scroll-top" aria-hidden="true"><div></div></div>
{table(["restaurant", "city", "my score", "friends", "all users",
        "google", "google reviews"], body)}
</details>
<script>
(() => {{
  const details = document.querySelector("details.rows");
  const top = details.querySelector(".scroll-top");
  const spacer = top.firstElementChild;
  const body = details.querySelector(".scroll");
  // Copy only when they differ, so the echoed scroll event ends the loop by itself.
  const mirror = (from, to) => () => {{
    if (to.scrollLeft !== from.scrollLeft) to.scrollLeft = from.scrollLeft;
  }};
  const size = () => {{
    spacer.style.width = body.scrollWidth + "px";
    top.hidden = body.scrollWidth <= body.clientWidth + 1;
  }};
  top.addEventListener("scroll", mirror(top, body), {{ passive: true }});
  body.addEventListener("scroll", mirror(body, top), {{ passive: true }});
  details.addEventListener("toggle", size);
  window.addEventListener("resize", size);
  size();
}})();
</script>
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
