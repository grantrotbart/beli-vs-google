# Beli vs Google

### **[Read the report →](https://grantrotbart.github.io/beli-vs-google/)**

Beli's pitch is that its ratings are more representative of what people actually think
than Google's or Yelp's. This tests the parts of that claim one user's data can reach:
**114 restaurants ranked on Beli, against the same restaurants' Google ratings.**

Three findings, in the order the report makes them:

1. **Volume.** In New York, Beli carries a median of **12.3x** Google's rating count and
   leads on 45 of 46 restaurants. Outside New York that inverts. The per-market split is
   the honest version of the 10-100x claim.
2. **Resolution.** Google's rating puts **22 of these restaurants on the same number**,
   spanning rank #1 to rank #104. It leaves 2.7x as many pairs indistinguishable as
   Beli's all-user average does.
3. **Consequence.** A restaurant's Google rating explains **less than 1%** of where it
   lands in the ranking (n=114, Spearman 0.02, p=0.91), and the null holds inside every
   price band. Run crowd against crowd instead of against one person, Google explains
   **1.2%** of Beli's all-user average.

One user's list, so this is a mechanism rather than a measurement. The
[report](https://grantrotbart.github.io/beli-vs-google/) is the write-up (`out/report.html`
in the repo). `out/stats.md` has every figure, including the ones that cut against the
thesis.

## The data

`data/ratings.csv` is the hand-collected input: one row per restaurant, read off the app.

| column | what it is |
|---|---|
| `name`, `city` | `city` disambiguates the Google lookup |
| `market`, `category`, `cuisine`, `price_level` | grouping fields, read off the listing |
| `rank` | position in the Been list, 1 is best |
| `beli_score` | the personal 0-10 score, which is derived from `rank` |
| `friend_score`, `friend_count` | Beli's friend-weighted score and how many friends |
| `beli_average`, `beli_rating_count` | Beli's all-user average and how many users |
| `google_rating_manual` | optional override. Filled in, the row is never sent to the API |
| `google_reviews_manual` | same idea for the review count |

Only `name` and `beli_score` are required. Blank means unavailable, not zero, so a
restaurant none of the user's friends have rated drops out of the friend-score
comparison without distorting it.

Google ratings are never written back into that file. They are fetched into
`data/places_cache.json` and joined into `data/matched.csv`, which is what the analysis
reads. The raw cache stays local rather than in the repo, since Google's terms don't
allow republishing Places responses. `matched.csv` carries the fields the analysis uses.

## Method notes

**Sampling.** Beli sorts the Been list by score, so taking the top N would truncate the
range and leave nothing to explain. These 114 are the full list, evenly spread from rank
1 to rank 114, scores 3.7 to 10.0.

**Three Beli scores are shown before ranking.** The rec score, friend score and all-user
average appear on screen before a restaurant is placed. That would be fatal if the score
were typed, but it isn't: ranking is a sequence of better / worse / too tough
comparisons against already-ranked restaurants, and the 0-10 falls out of the resulting
position. `stats.md` reports those columns with a gap table measuring how far the final
placement lands from each number shown, and how many disagreements exceed two points in
each direction. Large gaps in both directions are the evidence against anchoring.

Google's rating appears nowhere in the ranking flow, which is why it carries the
headline.

**Matching.** Google results below a name-similarity threshold are held out until
checked by hand, so a restaurant-name collision cannot quietly poison the chart.
Decisions persist in `data/review_decisions.csv` and survive regenerating `matched.csv`.

**Restaurants only.** Bars, bakeries and dessert places are excluded. That narrows the
Google range slightly, and a narrower range pulls correlations down, which happens to
favour the thesis. The per-price-band table in `stats.md` shows the null holds anyway.

## Reproducing it

```bash
python build/check.py --list-size 114
```

```bash
python build/run.py
```

`check.py` validates the input: score coverage, rank coverage, duplicates, missing
cities, and whether rank order and score order agree. `run.py` fetches, analyses, draws
and writes the report.

| flag | what it does |
|---|---|
| `--limit N` | first N rows only, for a cheap first live call |
| `--no-fetch` | never call the API; work from the cache |
| `--two-panel` | add a second panel comparing a Beli score against the personal one |
| `--second` | which Beli score that panel plots |

### The Google API

Needs `GOOGLE_MAPS_API_KEY`. At this volume it is free: `rating` and `userRatingCount`
are Enterprise-SKU fields with 1,000 free calls a month, and every response is cached,
so re-runs cost nothing.

1. `console.cloud.google.com` → new project
2. Billing → link a billing account (a card is required even inside the free tier)
3. APIs & Services → Library → enable **Places API (New)**, not the legacy Places API
4. Credentials → Create credentials → API key
5. Restrict it to Places API (New). Android and iOS restrictions are rejected for
   web-service calls and return `REQUEST_DENIED`
6. A budget alert, as a backstop
7. `setx GOOGLE_MAPS_API_KEY "..."`, then open a new terminal

Filling `google_rating_manual` instead skips all of that.

## Files

```
data/ratings.csv            hand-collected input
data/matched.csv            generated: input joined to the Google data
data/places_cache.json      raw API responses (local only, not committed)
data/review_decisions.csv   match confirmations, kept out of the generated file
build/brand.py              colours and type
build/places.py             the Google pull and the matcher
build/analyze.py            the statistics
build/chart.py              the four charts
build/report.py             the standalone HTML report
build/check.py              input validation
build/run.py                all of it
assets/fonts/               Montserrat, bundled so charts don't depend on the system
out/                        charts, report, stats
docs/                       the report again, for GitHub Pages
```

## Brand

Colours are sampled from Beli's own assets rather than guessed: the logo is `#134F5C` on
white, the app greys sit near `#9FA197`, and the site sets Proxima Nova. `build/brand.py`
holds all of it and documents the two places the brand had to bend to stay readable. The
teal is used as an emphasis mark rather than a categorical slot, since it fails the
lightness and chroma gates as a standalone series colour. Proxima Nova can't be
redistributed, so Montserrat stands in; the report asks for Proxima Nova first, so
anyone with it licensed sees the real face.
