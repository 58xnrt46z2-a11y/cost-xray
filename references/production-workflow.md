# Production Workflow

Use this workflow for deep Cost-Xray reports. Quick judgments can stay in chat.

## Folder Shape

Create a task folder under the current workspace:

```text
cost-xray-<product-slug>/
  data/
    input.json
    cost_data.json
  evidence/
    evidence-ledger.md
    sources.md
  output/
    report.md
    report.html
    social-copy.md
    validation.json
```

Use short descriptive slugs:

- `cost-xray-dji-mic-mini`
- `cost-xray-iphone-17-pro`
- `cost-xray-lv-speedy-30`

## Input JSON

Create `data/input.json` before calculation:

```json
{
  "product": "DJI Mic Mini",
  "brand": "DJI",
  "price": 350,
  "currency": "CNY",
  "category": "消费电子",
  "region": "China",
  "purchase_channel": "电商平台",
  "analysis_date": "2026-06-18",
  "anchors": {
    "物料成本(BOM)": {
      "pct": 0.22,
      "confidence": 4,
      "source": "teardown/BOM source URL or citation"
    }
  }
}
```

Only pass fields supported by `scripts/cost_calculator.py` into the calculator:

```bash
python scripts/cost_calculator.py < data/input.json > data/cost_data.json
```

If `input.json` contains extra metadata, keep it for evidence and report writing, but the calculator will ignore unknown fields.

## Evidence Ledger

Generate the initial ledger alongside `cost_data.json`:

```bash
python scripts/evidence_ledger.py data/cost_data.json evidence/evidence-ledger.md
```

Then enrich the generated rows with the actual source URL/title, evidence tier, usage, and caveat. The generator provides a starting structure; it does not replace source verification.

Required columns:

```markdown
| Claim / number | Cost dimension | Evidence tier | Source | How used | Caveat |
|---|---|---|---|---|---|
| BOM about 22% | 物料成本(BOM) | A | URL/title | Anchor pct=0.22 | Teardown sample may differ from retail batch |
```

Also create `evidence/sources.md` with URLs, titles, publisher, date accessed, and which claim each source supports.

## Search Pattern

Run 4 lanes, then add more only if evidence is thin:

1. **Product evidence**: teardown, BOM, material cost, component list.
2. **Company evidence**: gross margin, net margin, annual report, IPO prospectus, investor presentation.
3. **Channel evidence**: distributor markup, platform take rate, retail margin, franchise economics.
4. **Comparator evidence**: direct competitor price/cost/spec/value.

For service products, replace teardown/BOM with unit economics: labor hours, equipment amortization, rent, licensing, CAC, utilization.

## Report Generation

Generate Markdown first because it is easiest to inspect:

```bash
python scripts/generate_md_report.py data/cost_data.json output/report.md
```

Generate HTML when the user needs a polished artifact:

```bash
python scripts/generate_html_report.py data/cost_data.json output/report.html
```

If chart dependencies fail, keep the Markdown report and disclose the chart fallback.

## Validation

Run validation before delivery:

```bash
python scripts/validate_cost_report.py data/cost_data.json evidence/evidence-ledger.md output/validation.json
```

Fix all FAIL items. WARN items can remain only when the final response says why.

## Delivery Standard

Deliver:

- Core verdict.
- Highest three cost buckets.
- Confidence summary.
- Weakest evidence point.
- File paths.
- Validation result.

Do not hide that the analysis is an estimate. The trust comes from showing what is known, what is inferred, and what remains uncertain.
