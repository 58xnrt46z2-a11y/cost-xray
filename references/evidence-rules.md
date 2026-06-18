# Evidence Rules

Cost-Xray should feel sharp, but the trust layer must be conservative.

## Evidence Tiers

| Tier | Meaning | Typical sources | Confidence |
|---|---|---|---|
| S | Official exact or near-exact data | annual report, prospectus, regulatory filing, official cost disclosure | 5 |
| A | Credible third-party quantified data | teardown BOM, respected analyst report, audited industry dataset | 4 |
| B | Reputable industry estimate | broker report, white paper, trade publication, platform fee schedule | 3 |
| C | Category baseline / practitioner estimate | common industry range, supplier quote, comparable product inference | 2 |
| D | Weak inference | forum claims, unsourced blog posts, old data, single anecdote | 1 |

## How To Use Evidence

- Use S/A evidence as anchors in `data/input.json`.
- Use B/C evidence to narrow or explain baseline ranges.
- Use D evidence only as color, never as a precise number.
- If two sources conflict, prefer the source with clearer methodology and more recent date.
- Convert all figures to the user's price currency and date if possible. If not, state the conversion caveat.

## Required Labels

Use these labels in reports:

- **Hard data**: official data or credible teardown with visible methodology.
- **Industry estimate**: derived from category baseline, margin range, or comparable products.
- **Assumption**: a necessary inference not directly supported by a source.
- **Unknown**: a cost bucket that cannot be responsibly estimated.

## Forbidden Moves

- Do not present one teardown sample as every unit's exact cost.
- Do not turn gross margin into net profit.
- Do not treat channel markup as brand profit.
- Do not double-count brand premium and enterprise net profit without explanation.
- Do not use "cost price" for a sum that includes marketing/channel/tax/profit.
- Do not cite a source that does not actually support the claim next to it.

## Evidence Ledger Rules

Every deep report needs an evidence ledger with:

- The claim or number.
- The cost dimension it supports.
- Evidence tier.
- Source title/URL.
- How the number was used.
- Caveat or uncertainty.

The evidence ledger is not decoration. If a number cannot be placed into the ledger, either remove it or mark it as an assumption.
