"""
The whole thing, in one command.

    python build/run.py              # data/ratings.csv -> out/beli_vs_google.png
    python build/run.py --limit 3    # first three rows only, for a cheap live test
    python build/run.py --no-fetch   # analysis and chart from the cache alone

Paste ratings into data/ratings.csv, run this, and out/ holds the image and every
number the writeup needs.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import chart
import places
import report


def main(args):
    print("1/4  Google ratings")
    pull = places.build(
        places.RATINGS, limit=args.limit, fetch=args.fetch)
    if not pull["kept"]:
        raise SystemExit(
            "\nNothing is marked keep = 1, so there is nothing to plot. Open "
            "data/matched.csv, check the matches, and set keep to 1 on the good ones.")

    print("\n2/4  the numbers")
    result = analyze.compute()
    print(f"  {analyze.headline(result)}")
    stats_path = analyze.write_stats(result)

    print("\n3/4  the image")
    data = analyze.load()
    image = chart.draw(result, data, with_second=args.with_second, second_key=args.second)
    chart.coverage_chart(data)
    chart.distribution_chart(data)

    print("\n4/4  the report")
    report_path = report.build(result)

    print(f"\n  {image.relative_to(chart.ROOT)}")
    print(f"  {report_path.relative_to(chart.ROOT)}")
    print(f"  {stats_path.relative_to(chart.ROOT)}")
    if pull["flagged"]:
        print(f"\n  {pull['flagged']} match(es) still excluded. They are listed above and "
              "in data/matched.csv.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ratings.csv -> the finished image.")
    parser.add_argument("--limit", type=int, help="first N rows only")
    parser.add_argument("--no-fetch", dest="fetch", action="store_false",
                        help="never call the API; use what is cached")
    parser.add_argument("--two-panel", dest="with_second", action="store_true",
                        help="add a second panel comparing a Beli score against mine")
    parser.add_argument("--second", default="beli_average",
                        choices=["beli_average", "friend_score"],
                        help="which Beli score the second panel plots")
    sys.exit(main(parser.parse_args()))
