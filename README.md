# Beli vs Google

Beli's pitch is that its ratings are more representative of what people actually think
than Google's or Yelp's. This tests the parts of that claim one user's data can reach:
**114 restaurants I've ranked on Beli, against the same restaurants' Google ratings.**

Three findings, in the order the report makes them:

1. **Volume.** In New York, Beli carries a median of **12.3x** Google's rating count and
   leads on 45 of 46 restaurants. Outside New York that inverts. The per-market split is
   the honest version of the 10-100x claim.
2. **Resolution.** Google's rating puts **22 of these restaurants on the same number** --
   my #1 and my #104 among them. It leaves 2.7x as many pairs indistinguishable as
   Beli's all-user average does.
3. **Consequence.** A restaurant's Google rating explains **less than 1%** of where it
   lands in my ranking (n=114, Spearman 0.02, p=0.91), and the null holds inside every
   price band.

One user's data, so it is a mechanism rather than a measurement. `out/report.html` is the
write-up; `out/stats.md` has every figure including the ones that cut against the thesis.

---

Does Beli's data say something Google's stars don't? One chart, built from my own
ratings. `BRIEF.md` is the full argument; this file is just how to run it.

## The two-minute version

1. Put your ratings in `data/ratings.csv`
2. `python build/check.py` — looks the file over before you spend anything on it
3. `python build/run.py`
4. `out/beli_vs_google.png` is the image for the DM, `out/report.html` is the report to
   offer if it gets a reply, and `out/stats.md` is every number behind both

### Log across your whole list, not down from the top

Beli sorts your list, so logging from the top and stopping when you get bored leaves you
with only restaurants you liked. The analysis explains variance in your ranking — with
no spread in the scores there's nothing to explain and the chart has nothing to show.
Take from the top, the middle and the bottom. `check.py` warns you if the range is thin.


## What goes in ratings.csv

```csv
name,city,beli_score,beli_average,friend_score,google_rating,user_ratings_total,note
Lilia,Brooklyn NY,9.4,8.2,9.0,,,
```

Only `name` and `beli_score` are required. Everything else can be blank, and a blank is
treated as "not available" rather than zero — restaurants none of your friends have
rated just drop out of the friend-score panel, they don't poison it.

| column | what it is |
|---|---|
| `name`, `city` | `city` disambiguates the Google lookup. Worth filling in. |
| `beli_score` | your own 0–10 score. The thing being explained. |
| `rec_score` | Beli's predicted score. **Shown before you rank** — see below. |
| `friend_score` | Beli's friend-weighted score. **Shown before you rank.** |
| `beli_average` | Beli's average across all users. **Shown before you rank.** |
| `google_rating_manual` | **fill this in and no API call is made for that row.** Leave it empty and the API supplies the rating, which lands in `data/matched.csv`, not here. |
| `google_reviews_manual` | Same idea for the Google review count. Optional. |
| `note` | free text, ignored |

### Why three of those columns need a sentence of context

Beli shows the rec score, the friend score and the all-user average on screen *before*
you rank a place. That would be fatal if you then typed a score — you'd just be echoing
the number. **You don't.** Ranking is a sequence of better / worse / too tough
comparisons against restaurants you've already ranked, and the 0–10 is derived from
where you land in your own list. A number on screen can't be copied into an answer that
isn't a number.

What it could still do is tilt close comparisons, and a sorted insertion is exactly the
structure where a small consistent tilt compounds over the ~log2(n) comparisons it takes
to place one restaurant. So `stats.md` reports these columns with the mechanism stated,
and adds a gap table: how far your score lands from each number you were shown, and how
many disagreements exceed 2 points in each direction. Large gaps both ways are the
evidence that the ordering is yours.

Google's rating isn't in the ranking flow at all, which is why it carries the headline.

## Google ratings: by hand, or by API

Both work, and they mix freely — a row with `google_rating` filled in is never sent to
the API, so you can type in the ones you care about and let the API do the rest.

**By API.** Needs `GOOGLE_MAPS_API_KEY` set. At ~100 restaurants this is free:
`rating` and `userRatingCount` are Enterprise-SKU fields with 1,000 free calls a month,
and every response is cached in `data/places_cache.json`, so a re-run costs nothing.
Setup, in order:

1. `console.cloud.google.com` → new project
2. Billing → link a billing account (a card is required even inside the free tier)
3. APIs & Services → Library → enable **Places API (New)** — the new one, not legacy
4. Credentials → Create credentials → API key
5. Restrict it to Places API (New). Not an Android or iOS restriction — those are
   rejected for web-service calls and come back `REQUEST_DENIED`.
6. Budget alert at $5, as a backstop
7. `setx GOOGLE_MAPS_API_KEY "..."` then open a new terminal

**By hand.** Fill `google_rating` and skip all of the above. No key, no billing account.

## The eyeball step

Restaurant names collide, and a bad match quietly poisons the chart. So after the pull,
`data/matched.csv` has a `keep` column: `1` where the name matched closely, `0` where it
didn't. Anything at `0` is excluded until you look at it. The run prints each one with
the runner-up Google result so you can tell what happened.

Set `keep` to `1` on the ones that are actually right. **Your edits survive a re-run** —
rows merge on name + city.

## Flags

| flag | what it does |
|---|---|
| `--limit N` | first N rows only — use this for your first live call |
| `--no-fetch` | never call the API; work from what's cached |
| `--with-friends` | add the friend-score panel, and put both numbers in the headline |

A sensible first live run, once the key exists:

```bash
python build/run.py --limit 3
```

Three calls, three cached responses. Check the ratings against Google Maps in a browser,
then run the whole thing.

## What the analysis actually does

Every regression explains the same thing — **your own Beli score**:

- the clean fit: your score on Google's rating, which is the headline
- the fits on what Beli showed you first, with the mechanism note that makes them
  readable, plus the gap table that checks them
- spread and entropy for each measure over its own native scale (Google 1–5, Beli 0–10).
  **Read the caveat under that table before quoting it:** a rank-derived score spreads
  across its scale partly by construction, so the comparison is about the two
  instruments, not about two populations of people.
- the most crowded Google rating, and how far apart you rank those same restaurants

`out/stats.md` ends with the caveats that belong in the writeup.

## Files

### Which file holds what

`data/ratings.csv` is **input only** — what you typed in. The Google ratings are never
written back here; they are fetched into `data/places_cache.json` and joined into
`data/matched.csv`, which is the file the analysis actually reads. So an empty
`google_rating_manual` column in ratings.csv is correct and expected.

```
data/ratings.csv          the only file you edit
data/matched.csv          generated: your rows + the Google data. The analysis reads this.
data/places_cache.json    raw API responses. Deleting it means paying again.
build/brand.py            Beli's colours and type, in one place
build/places.py           the pull
build/analyze.py          the numbers
build/chart.py            the image
build/report.py           the standalone HTML report
build/run.py              all of it
assets/fonts/             Montserrat, bundled so the charts don't depend on the system
out/                      the deliverables
```

## Brand

Colours are sampled from Beli's own assets, not guessed: the logo is `#134F5C` on
white, the app greys sit near `#9FA197`, and the site sets Proxima Nova. `build/brand.py`
holds all of it and documents the two places the brand had to bend to stay readable —
the teal is used as an emphasis mark rather than a categorical slot, and Proxima Nova
can't be redistributed so Montserrat stands in. The report asks for Proxima Nova first,
so anyone who has it licensed sees the real face.
