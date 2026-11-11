# Beli vs Google -- the numbers

Generated 2026-11-11 from 117 kept rows. Google ratings via: api, manual.

## Headline

> Google stars explain less than 1% of the variance in how I actually rank restaurants (n=117).

## 1. Volume: does Beli actually carry more ratings?

Tested per market, because the blended number is misleading both ways.

| market        | n  | median Beli ratings per Google review | Beli ahead on |
|---------------|----|---------------------------------------|---------------|
| NYC           | 46 | 12.3x                                 | 45/46         |
| Other US      | 13 | 1.9x                                  | 8/13          |
| South Florida | 31 | 0.3x                                  | 10/31         |
| North Florida | 15 | 0.3x                                  | 3/15          |
| Europe        | 9  | 0.0x                                  | 0/9           |

Too few restaurants to break out: Central Florida (2).

The widest gaps, all of them in New York:

| restaurant            | ratio | Beli ratings | Google reviews |
|-----------------------|-------|--------------|----------------|
| The Lions Bar & Grill | 91x   | 17,766       | 196            |
| Win Son Bakery        | 52x   | 25,085       | 486            |
| OPTO                  | 47x   | 10,666       | 225            |
| Son del North         | 39x   | 22,997       | 591            |
| Laser Wolf            | 37x   | 44,512       | 1,210          |

So the 10-100x figure holds where Beli has density and inverts where it does not. That is the shape of a network effect rather than a property of the platform, and the per-market split is the useful version of the claim.

## 2. Resolution: can the number tell two restaurants apart?

Across 116 restaurants there are 6,670 possible pairs. A score that gives two restaurants the same value cannot order them.

| crowd score                       | possible values | values used | tied pairs | share tied | largest group on one value |
|-----------------------------------|-----------------|-------------|------------|------------|----------------------------|
| Google rating                     | 41              | 12          | 826        | 12.4%      | 22                         |
| Beli all-user average             | 101             | 29          | 309        | 4.6%       | 13                         |
| Beli average on Google's 1-5 grid | 41              | 14          | 730        | 10.9%      | 21                         |

Both are averages over users, so this is like for like. Google leaves 2.7x as many pairs indistinguishable, and its largest collision puts **22 restaurants on one number**.

**Most of that is granularity.** Google publishes one decimal on 1-5 (41 possible values); Beli one decimal on 0-10 (101). Mapping Beli's averages linearly onto Google's grid (1 + 0.4 x score, re-rounded) leaves 730 tied pairs, so on equal slots Google ties 1.1x as many, not 2.7x. The practical point stands -- a product consuming the Google rating cannot rank what it does not separate -- but the advantage is mostly the published scale, not the users behind it.

## 3. Consequence: Google's number predicts nothing about my order

Google's rating is not on screen while I rank, and nothing in the ranking flow refers to it.

The different scales do not matter here: R2 and Spearman are both scale-invariant, so doubling every Google rating to put it on a 0-10 basis would leave these numbers untouched. Only the slope is in mixed units -- Beli points per Google star.

| comparison                               | n   | R2    | variance explained | Spearman rho | Spearman p |
|------------------------------------------|-----|-------|--------------------|--------------|------------|
| Google rating -> my ranking              | 117 | 0.000 | 0.0%               | 0.022        | 0.81       |
| Google rating -> Beli's all-user average | 116 | 0.024 | 2.4%               | 0.127        | 0.17       |

The second row is the one with no n=1 in it. Both sides are averages over users, my own rating is one of thousands inside the Beli figure, and nothing either platform shows me affects it.


### Is it just cheap versus expensive?

The obvious objection to a null result: a taco stand and a tasting menu are not the same judgement, so maybe Google tracks my ranking *within* a price band and only looks flat across all of them. It does not.

| price band | n  | R2    | variance explained | Spearman rho |
|------------|----|-------|--------------------|--------------|
| $          | 24 | 0.026 | 2.6%               | -0.004       |
| $$         | 56 | 0.000 | 0.0%               | 0.008        |
| $$$        | 28 | 0.003 | 0.3%               | -0.064       |

And holding price fixed: price alone explains 9.8% of my ranking; price plus Google explains 9.9%. **Google adds +0.1 percentage points** (n=113).

So the null is not a mixing artifact. Google's rating is uninformative about my ordering inside each price band and across all of them.

The price bracket alone explains 9.8% of where a restaurant lands in my list. **The price bracket is a better guide to my ranking than the Google rating is.**

## Shown to me before I rank

Both of these are on screen before I rank a place, so they are context rather than predictions. The pairwise mechanic limits how far that can go -- the score is a rank position, not a number I type -- but it does not rule out a tilt on close calls, so the gap table below is the check.

| shown before ranking  | n   | R2    | variance explained | Spearman rho | Spearman p |
|-----------------------|-----|-------|--------------------|--------------|------------|
| Beli friend score     | 66  | 0.137 | 13.7%              | 0.306        | 0.013      |
| Beli all-user average | 116 | 0.244 | 24.4%              | 0.504        | 8.3e-09    |

## How far I land from the number I was shown

Each check is set against a rater who copied the shown order exactly. My score is a rank position stretched across the scale, so some gap appears even for that copier; the column says how much.

| vs                    | n   | mean gap | median gap size | gaps over 2 | direction     | copier's gaps over 2 | pairs in opposite order | biggest |
|-----------------------|-----|----------|-----------------|-------------|---------------|----------------------|-------------------------|---------|
| Beli friend score     | 66  | +0.21    | 0.90            | 11 (16.7%)  | 7 up / 4 down | 3                    | 723 of 1,886 (38.3%)    | 5.2     |
| Beli all-user average | 116 | +0.28    | 0.90            | 10 (8.6%)   | 5 up / 5 down | 1                    | 1,788 of 5,903 (30.3%)  | 3.9     |

The mean gap is identical for the copier by construction -- it depends on which scores exist, not on which restaurant gets which -- so it is reported but is not evidence either way.

A copier would put 0% of pairs in opposite order and two unrelated orderings about 50%. The large gaps beyond the copier's and the share of reversed pairs show the ordering is not an echo. They cannot prove the tilt on close calls is zero, and the agreement that remains could be anchoring or shared taste. Only a holdout separates those, and only Beli can run one.

## How many people are behind those numbers

Friend counts: median **1**, max 8. 51 restaurant(s) have no friend rating at all, 25 rest on a **single friend**, and 27 have three or more.

A friend score drawn from one friend is one person's opinion wearing a crowd's name. Where that is most of the sample, the friend-score correlation is really a correlation with a handful of individuals, and the writeup should say so rather than call it a social signal.

Beli rating counts: median **2,222**, from 7 to 135,883. 39 restaurant(s) have fewer than 500 ratings. At the thinnest, my own rating is about 14.3% of that average.

## Spread

| measure               | n   | min  | max   | range | share of its scale | std (raw) | std (% of scale) | entropy (bits) |
|-----------------------|-----|------|-------|-------|--------------------|-----------|------------------|----------------|
| My Beli score         | 117 | 3.70 | 10.00 | 6.30  | 63.0%              | 1.35      | 13.5%            | 1.96           |
| Google rating         | 117 | 3.90 | 5.00  | 1.10  | 27.5%              | 0.23      | 5.6%             | 1.22           |
| Beli friend score     | 66  | 2.60 | 10.00 | 7.40  | 74.0%              | 1.51      | 15.1%            | 2.13           |
| Beli all-user average | 116 | 5.50 | 9.30  | 3.80  | 38.0%              | 0.67      | 6.7%             | 1.50           |

Google runs 1-5 and Beli runs 0-10, so **the raw std column is not comparable across rows** -- it is there for reference only. Compare the two percentage columns instead. Entropy is over 10 bins spanning each measure's own native scale, so each bin is a tenth of its own range and the figures line up.

**Read this table carefully before quoting it.** My Beli score is derived from rank position in my own list, so it spreads across the scale partly *by construction* -- a rank-derived number is close to uniform whatever the underlying taste looks like, while an average of star ratings concentrates whatever the underlying taste looks like. Most of the gap between those two rows is the two instruments, not two populations.

That is the honest version of the claim, and it is still the interesting one: ranking is built to extract ordering, averaging is built to discard it. The finding is about instrument design. It is not evidence that Beli users are more discerning, and should not be written as though it were.

## The tightest Google cluster

22 restaurants all sit at **4.5 on Google**. I rank them from **6.7 to 10.0** -- a spread of 3.3 points: Tropical Acres Steakhouse at the bottom, Rolo's at the top.

Beli's all-user average spreads those same restaurants across 2.3 points.

## Review count vs disagreement

Spearman rho = 0.053 (p = 0.57, n = 117) between a restaurant's Google review count and how far my rating sits from what its Google rating predicts. Negative means Google agrees with me more where it has more reviews.

## Caveats that belong in the writeup

- One user's ratings. This is a mechanism, not a measurement.
- **My score is a rank position, not a judgement typed on a 0-10 scale.** It is ordinal within my own list. That is why Spearman is reported beside every R2, and why the spread comparison above is about instruments rather than people.
- **The rec score, friend score and all-user average are on screen before I rank.** The pairwise mechanic means they cannot be copied into the answer, but they could still tilt close comparisons. The gap table is the check; a holdout is the only real test.
- Google's rating is not shown in the ranking flow, but I am not blind to it in life -- I may have seen a place's stars before choosing to eat there.
- Only restaurants I chose to visit, so the sample is selected on expected enjoyment.
