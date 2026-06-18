# QA Checklist

Run this before delivering a deep report or public-facing Cost-Xray copy.

## Data Integrity

- [ ] Retail price and currency are present.
- [ ] Category is present and maps to a baseline or a custom service framework.
- [ ] Each cost line has amount, percent, source, and confidence.
- [ ] Cost percentages are roughly 95%-105% total, or the deviation note explains why.
- [ ] Amounts sum close to the retail price after rounding.
- [ ] Gross margin, net profit, tax, channel markup, and brand premium are not mixed together.

## Evidence Quality

- [ ] At least one S/A/B source supports the most important claim when possible.
- [ ] Every high-impact number appears in `evidence/evidence-ledger.md`.
- [ ] Low-confidence items are labeled as estimates or assumptions.
- [ ] Sources are current enough for the product and category.
- [ ] Conflicting evidence is acknowledged instead of silently cherry-picked.

## Report Quality

- [ ] The opening verdict is clear but not defamatory.
- [ ] The top 3 cost buckets are easy to understand.
- [ ] The report explains who receives the money, not only percentages.
- [ ] Alternatives are comparable in use case and price band.
- [ ] Disclaimer is present.

## Public Platform Safety

- [ ] No "必买/别买/唯一/最强" absolute claims.
- [ ] No fake official cost claim.
- [ ] No personal attack on brand, founder, users, creators, or sales staff.
- [ ] No investment advice such as "买入/卖出/目标价".
- [ ] "智商税" is used only when the analysis strongly supports it; otherwise use "高溢价/偏贵/不适合某些人".

## Delivery Gate

- **FAIL**: missing price, missing breakdown, impossible percentages, no source labels, or public copy based on unvalidated data.
- **WARN**: limited sources, old sources, high share of confidence 1-2, competitor data missing.
- **PASS**: data consistent, evidence visible, uncertainty labeled, verdict useful.
