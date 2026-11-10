"""
Look over data/ratings.csv before spending anything on it.

    python build/check.py

Catches the things that are cheap to fix now and expensive to find later: scores bunched
into one end of the scale, duplicate rows, missing cities that will send the Google
lookup to the wrong restaurant, and anything unparseable.

The one that matters most is coverage. Beli's list is sorted, so the natural way to log
is from the top down, which leaves a sample of nothing but restaurants the rater
liked. The whole analysis is about variance in the ranking: no spread
in the scores, nothing to explain, and the chart has nothing to show.
"""
import csv
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import places

DECILES = 10
THIN = 5            # occupied deciles below this means the range is too narrow
TARGET = 100        # the brief's number, and enough for a dense Google cluster


def bar(count, width=28, total=None):
    filled = 0 if not total else round(width * count / total)
    return "#" * filled + "." * (width - filled)


def rank_coverage(rows, list_size=None):
    """Where in the Been list these came from.

    This is the better coverage test. Scores bunch at the top of anyone's list, so a
    score histogram can look thin for innocent reasons; rank says plainly whether the
    whole list was sampled or only the liked end of it."""
    ranks = sorted(r["rank"] for r in rows if r["rank"] is not None)
    if not ranks:
        print("\n  No rank column filled, so I can't tell where in your list these came")
        print("  from. The screenshots show it as '#N on your Been list'.")
        return
    top = list_size or max(ranks)
    segments = 5
    width = max(top / segments, 1)
    print(f"\n  Where these sit in your Been list (#1 to #{top:.0f}"
          f"{'' if list_size else ', as far as you have logged'}):")
    for index in range(segments):
        lo, hi = index * width, (index + 1) * width
        count = sum(1 for r in ranks if lo < r <= hi or (index == 0 and r <= hi))
        print(f"    #{lo + 1:>5.0f}-{hi:<6.0f} {bar(count, total=len(ranks))} {count}")
    if not list_size:
        print(f"\n  Pass --list-size N (your real Been list length) and I can tell you")
        print("  whether that is the whole list or only the top of it.")
    elif max(ranks) < list_size * 0.5:
        print(f"\n  WARNING: nothing logged below #{max(ranks):.0f} of {list_size}. "
              "That is the top half only.")

    # The score is derived from rank, so the two orderings must agree. Where they
    # don't, one of the two numbers was mistyped.
    pairs = [(r["rank"], r["beli_score"], r["name"])
             for r in rows if r["rank"] is not None]
    by_rank = sorted(pairs)
    out_of_order = [(a, b) for a, b in zip(by_rank, by_rank[1:]) if a[1] < b[1]]
    if out_of_order:
        print(f"\n  {len(out_of_order)} place(s) where rank and score disagree. The score "
              "comes from\n  the rank, so one of the two is a typo:")
        for (r1, s1, n1), (r2, s2, n2) in out_of_order[:8]:
            print(f"    #{r1:.0f} {n1} scores {s1}, but #{r2:.0f} {n2} scores {s2}")


def main(path=places.RATINGS, list_size=None):
    if not path.exists():
        raise SystemExit(f"{path} does not exist yet.")

    rows, bad = [], []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in ("name", "beli_score") if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"ratings.csv is missing required column(s): {missing}. "
                             "Keep the header row from the template.")
        for line_no, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            score = places.maybe_float(row.get("beli_score"))
            if score is None:
                bad.append(f"line {line_no}: {name} -- beli_score is blank or not a number")
                continue
            if not 0 <= score <= 10:
                bad.append(f"line {line_no}: {name} -- beli_score {score} is outside 0-10")
                continue
            rows.append({**row, "name": name, "beli_score": score,
                         "city": (row.get("city") or "").strip(),
                         "rank": places.maybe_float(row.get("rank"))})

    print(f"\n  {len(rows)} usable row(s) in {path.name}")
    if bad:
        print(f"\n  {len(bad)} row(s) could not be read:")
        for note in bad:
            print(f"    {note}")
    if not rows:
        raise SystemExit("\n  Nothing to check yet. Add some ratings and run this again.")

    scores = [r["beli_score"] for r in rows]
    low, high = min(scores), max(scores)
    buckets = Counter(min(int(s // 1), 9) for s in scores)
    occupied = len(buckets)

    print(f"\n  Your scores: {low:.1f} to {high:.1f}")
    for decile in range(DECILES):
        count = buckets.get(decile, 0)
        flag = "  <- empty" if not count else ""
        print(f"    {decile}-{decile + 1:<3} {bar(count, total=max(buckets.values()))} "
              f"{count}{flag}")

    if occupied < THIN:
        print(f"\n  WARNING: your scores only occupy {occupied} of 10 bands.")
        print("  The analysis explains variance in your ranking, so it needs the range.")
        print("  Beli's list is sorted -- go back and pull from the middle and the")
        print("  bottom too, not just the top.")
    else:
        print(f"\n  Coverage looks fine: {occupied} of 10 bands occupied.")

    rank_coverage(rows, list_size)

    seen = Counter((r["name"].lower(), r["city"].lower()) for r in rows)
    dupes = [k for k, n in seen.items() if n > 1]
    if dupes:
        print(f"\n  {len(dupes)} duplicate row(s) -- the same restaurant twice:")
        for name, city in dupes[:10]:
            print(f"    {name} ({city or 'no city'})")

    nocity = [r["name"] for r in rows if not r["city"]]
    if nocity:
        print(f"\n  {len(nocity)} row(s) have no city. Google will guess, and may guess a")
        print("  different restaurant with the same name:")
        for name in nocity[:10]:
            print(f"    {name}")
        if len(nocity) > 10:
            print(f"    ... and {len(nocity) - 10} more")

    optional = {"friend_score": 0, "friend_count": 0,
                "beli_average": 0, "beli_rating_count": 0, "google_rating_manual": 0}
    for row in rows:
        for key in optional:
            if places.maybe_float(row.get(key)) is not None:
                optional[key] += 1
    print("\n  Optional columns filled:")
    for key, count in optional.items():
        print(f"    {key:<18} {count}/{len(rows)}")

    # A row is covered if it was typed in by hand or is already in the cache.
    cache = {}
    if places.CACHE.exists():
        import json
        cache = json.loads(places.CACHE.read_text(encoding="utf-8"))
    needs_api = sum(
        1 for r in rows
        if places.maybe_float(r.get("google_rating_manual")) is None
        and places.query_for({"name": r["name"], "city": r["city"]}) not in cache
    )
    cached = len(rows) - needs_api - sum(
        1 for r in rows if places.maybe_float(r.get("google_rating_manual")) is not None)
    key_set = bool(os.environ.get("GOOGLE_MAPS_API_KEY"))
    if cached:
        print(f"\n  {cached} row(s) already cached -- those cost nothing to reuse.")
    print(f"  {needs_api} row(s) would need a live lookup. "
          f"API key is {'set' if key_set else 'NOT set'}.")
    if needs_api and not key_set:
        print("  Either set GOOGLE_MAPS_API_KEY, or fill the google_rating column by hand.")
    elif needs_api:
        print(f"  {places.FREE_CALLS} calls a month are free, so this costs nothing.")
        print("  Try 'python build/run.py --limit 3' first.")

    if len(rows) < TARGET:
        print(f"\n  {TARGET - len(rows)} more to reach {TARGET}, which is the number the "
              f"brief settled on.")
    print()
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Look over data/ratings.csv.")
    parser.add_argument("--list-size", type=int,
                        help="how many spots are on your Been list in total, so coverage "
                             "is measured against the real list rather than what you "
                             "have logged so far")
    sys.exit(main(list_size=parser.parse_args().list_size))
