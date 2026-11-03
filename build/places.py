"""
Google ratings for the rated restaurants -- by API, or typed in by hand.

    python build/places.py            # refresh matched.csv from data/ratings.csv

Reads  data/ratings.csv
Writes data/places_cache.json   raw Text Search (New) responses, keyed by query
       data/matched.csv         one row per restaurant, for eyeballing

A row that already has google_rating filled in is never sent to the API -- fill that
column by hand and no key is needed at all. For the rest, places.rating and
places.userRatingCount are Enterprise-SKU fields: 1,000 free calls a month, then roughly
$20 per 1,000. The cache is the only thing standing between a re-run and a bill, so a
query that is already cached is never sent again.
"""
import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RATINGS = ROOT / "data" / "ratings.csv"
CACHE = ROOT / "data" / "places_cache.json"
MATCHED = ROOT / "data" / "matched.csv"
DECISIONS = ROOT / "data" / "review_decisions.csv"

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.rating,places.userRatingCount,places.location"
)
MAX_RESULTS = 3         # the runner-up is what tells you a match went wrong
KEEP_THRESHOLD = 0.85   # below this, a match is excluded until a human looks at it
PAUSE = 0.1             # seconds between live calls
FREE_CALLS = 1000       # Enterprise SKU, per month

COLUMNS = [
    "name", "city", "market", "category", "price_level", "cuisine", "rank", "beli_score",
    "friend_score", "friend_count", "beli_average", "beli_rating_count",
    "google_name", "google_address", "google_rating", "user_ratings_total",
    "match_score", "source", "runner_up", "keep",
]

NO_KEY = """\
GOOGLE_MAPS_API_KEY is not set, so there is no way to call the Places API.

Either fill the google_rating column in data/ratings.csv by hand -- rows that have it
are never sent to the API -- or set up a key:

  1. console.cloud.google.com -> new project
  2. Billing -> link a billing account (a card is required even inside the free tier)
  3. APIs & Services -> Library -> enable "Places API (New)"
  4. Credentials -> Create credentials -> API key
  5. Restrict it to Places API (New). Do not pick an Android or iOS restriction --
     those are rejected for web-service calls and return REQUEST_DENIED.
  6. setx GOOGLE_MAPS_API_KEY "..."   then open a new terminal

"""


def maybe_float(value):
    """Optional numeric column -> float or None. Blanks are normal, not errors."""
    try:
        return float((value or "").strip())
    except (ValueError, AttributeError):
        return None


def read_ratings(path, limit=None):
    """ratings.csv -> list of rows. Only name and beli_score are required."""
    rows, skipped = [], []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for line_no, row in enumerate(csv.DictReader(handle), start=2):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            score = maybe_float(row.get("beli_score"))
            if score is None:
                skipped.append(f"line {line_no}: {name} has no usable beli_score")
                continue
            rows.append({
                "name": name,
                "city": (row.get("city") or "").strip(),
                "category": (row.get("category") or "").strip(),
                "market": (row.get("market") or "").strip(),
                "cuisine": (row.get("cuisine") or "").strip(),
                "price_level": maybe_float(row.get("price_level")),
                "rank": maybe_float(row.get("rank")),
                "beli_score": score,
                "friend_score": maybe_float(row.get("friend_score")),
                "friend_count": maybe_float(row.get("friend_count")),
                "beli_average": maybe_float(row.get("beli_average")),
                "beli_rating_count": maybe_float(row.get("beli_rating_count")),
                "google_rating": maybe_float(row.get("google_rating_manual")),
                "user_ratings_total": maybe_float(row.get("google_reviews_manual")),
            })
    for note in skipped:
        print(f"  dropped  {note}")
    return rows[:limit] if limit else rows


def query_for(row):
    return f"{row['name']}, {row['city']}".strip().strip(",")


def normalize(text):
    text = re.sub(r"\b(the|restaurant|cafe|café|bar|nyc)\b", " ", text.lower())
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def similarity(a, b):
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def display_name(place):
    return (place.get("displayName") or {}).get("text", "")


def search(query, key, session):
    response = session.post(
        ENDPOINT,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
        json={"textQuery": query, "maxResultCount": MAX_RESULTS},
        timeout=20,
    )
    if response.status_code != 200:
        raise SystemExit(
            f"Places API returned {response.status_code} for [{query}]:\n{response.text}"
        )
    return response.json()


def best_match(name, payload):
    """Highest-similarity place, plus the runner-up so a wrong match is visible."""
    scored = sorted(
        ((similarity(name, display_name(place)), place) for place in payload.get("places") or []),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not scored:
        return None, 0.0, ""
    runner_up = display_name(scored[1][1]) if len(scored) > 1 else ""
    return scored[0][1], scored[0][0], runner_up


def held_keeps():
    """Every match you have judged by hand, so a re-run never asks twice.

    Kept in review_decisions.csv rather than only in matched.csv, because matched.csv is
    regenerated and deleting it used to throw the decisions away with it. matched.csv
    still wins where both have an opinion -- that is where you just edited."""
    held = {}
    for path in (DECISIONS, MATCHED):
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if (row.get("keep") or "").strip() in ("0", "1"):
                    held[(row["name"], row["city"])] = int(row["keep"])
    return held


def save_decisions(matched, defaults):
    """Persist only the rows where a human overrode the automatic call."""
    overrides = [row for row in matched
                 if int(row["keep"]) != defaults.get((row["name"], row["city"]), 1)]
    with DECISIONS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "city", "keep"])
        writer.writeheader()
        for row in overrides:
            writer.writerow({k: row[k] for k in ("name", "city", "keep")})
    return len(overrides)


def blank_row(row, **extra):
    base = {column: "" for column in COLUMNS}
    base.update({"name": row["name"], "city": row["city"], "market": row["market"],
                 "category": row["category"],
                 "cuisine": row["cuisine"], "beli_score": row["beli_score"]})
    for key in ("price_level", "rank", "friend_score", "friend_count",
                "beli_average", "beli_rating_count"):
        base[key] = row[key] if row[key] is not None else ""
    base.update(extra)
    return base


def build(ratings_path=RATINGS, limit=None, fetch=True):
    rows = read_ratings(ratings_path, limit)
    if not rows:
        raise SystemExit(f"{ratings_path} has no usable rows yet. Add your ratings first.")

    cache_path = CACHE
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    held = held_keeps()

    by_hand = [row for row in rows if row["google_rating"] is not None]
    needed = [row for row in rows
              if row["google_rating"] is None and query_for(row) not in cache]
    if needed and fetch:
        print(f"  {len(needed)} row(s) need a live call "
              f"({len(by_hand)} already filled in by hand, {FREE_CALLS}/month are free)")

    key = None if not fetch else os.environ.get("GOOGLE_MAPS_API_KEY")
    session = requests.Session() if fetch else None

    billed, matched, uncached, defaults = 0, [], 0, {}
    for row in rows:
        # A hand-filled google_rating wins outright and costs nothing.
        if row["google_rating"] is not None:
            matched.append(blank_row(
                row,
                google_name=row["name"],
                google_rating=row["google_rating"],
                user_ratings_total=(row["user_ratings_total"]
                                    if row["user_ratings_total"] is not None else ""),
                match_score=1.0,
                source="manual",
                keep=held.get((row["name"], row["city"]), 1),
            ))
            defaults[(row["name"], row["city"])] = 1
            continue

        query = query_for(row)
        payload = cache.get(query)
        if payload is None:
            if not fetch:
                uncached += 1
                continue
            else:
                if not key:
                    raise SystemExit(NO_KEY)
                payload = cache[query] = search(query, key, session)
                billed += 1
                cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
                print(f"  fetched  {query}  ({billed} billed)")
                time.sleep(PAUSE)

        place, score, runner_up = best_match(row["name"], payload)
        rating = place.get("rating") if place else None
        default = 1 if (place is not None and score >= KEEP_THRESHOLD and rating is not None) else 0
        matched.append(blank_row(
            row,
            google_name=display_name(place) if place else "",
            google_address=place.get("formattedAddress", "") if place else "",
            google_rating=rating if rating is not None else "",
            user_ratings_total=place.get("userRatingCount", "") if place else "",
            match_score=round(score, 3),
            source="api",
            runner_up=runner_up,
            keep=held.get((row["name"], row["city"]), default),
        ))
        defaults[(row["name"], row["city"])] = default

    with MATCHED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(matched)
    kept_by_hand = save_decisions(matched, defaults)

    flagged = [row for row in matched if not row["keep"]]
    tail = f", {uncached} skipped as uncached" if uncached else ""
    print(f"\n  {len(matched)} matched, {billed} billed call(s){tail}")
    if flagged:
        print(f"  {len(flagged)} need your eye -- open data/matched.csv and set keep to 1 "
              "where the match is right:")
        for row in flagged:
            runner = f"  runner-up: {row['runner_up']}" if row["runner_up"] else ""
            print(f"    {row['name']} ({row['city']})  ->  "
                  f"{row['google_name'] or '(no result)'}  [{row['match_score']}]{runner}")
    return {
        "matched": len(matched),
        "billed": billed,
        "flagged": len(flagged),
        "kept": len(matched) - len(flagged),
        "by_hand": len(by_hand),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull Google ratings for the rated restaurants.")
    parser.add_argument("--limit", type=int, help="first N rows only")
    parser.add_argument("--no-fetch", dest="fetch", action="store_false", help="cache only")
    args = parser.parse_args()
    build(RATINGS, args.limit, args.fetch)
