---
name: cost-xray
description: Use when the user asks whether a product or service is worth its price, why it is expensive, where the money goes, or requests cost breakdown, pricing anatomy, margin analysis, brand premium, BOM, channel markup, 智商税, or a Xiaohongshu/公众号 cost-analysis article.
---

# Cost-Xray

Turn a product or service price into a transparent cost story: who gets paid, which costs are hard data, which are estimates, and whether the price is reasonable.

## What To Produce

Choose the deliverable by user intent:

- **Quick judgment**: a short answer in chat when the user wants a fast "值不值".
- **Deep report**: a project folder with structured data, evidence notes, Markdown/HTML report, charts when possible, and validation output.
- **Self-media copy**: a Xiaohongshu/公众号 version after the cost report is stable.
- **Follow-up assets**: social-card cover, deck, or PDF only when the user asks or the workflow has already produced the base report.

Do not use this skill to invent exact private costs, claim insider data without evidence, attack a brand, provide investment advice, or present estimates as official facts.

## Core Principles

- **Evidence first**: every important number needs a source, evidence tier, or explicit "industry baseline estimate" label.
- **Sharp but honest**: keep the voice direct, but never manufacture precision.
- **Separate money buckets**: do not merge BOM, gross margin, channel markup, tax, brand premium, and net profit.
- **Confidence visible**: attach 1-5 confidence to each cost line and explain low-confidence items.
- **Decision useful**: end with a clear verdict, alternatives, and caveats.

## Search Tools

Use the available web search and page extraction tools. If AnySearch is installed, prefer its batch search and URL extraction for parallel research. Fall back to the environment's built-in browsing tools without blocking the workflow.

## Required References

Read only what the task needs:

- `references/production-workflow.md` for folder shape, file names, and deep-report execution.
- `references/evidence-rules.md` before using numbers from search, reports, teardown posts, or industry baselines.
- `references/industry-baselines.md` to select category cost ranges.
- `references/category-playbook.md` when the product belongs to a specific category or service type.
- `references/analysis-framework.md` for cost dimensions and category-specific search angles.
- `references/report-template.md` for the deep report structure.
- `references/social_media_template.md` when creating Xiaohongshu/公众号 text.
- `references/qa-checklist.md` before delivering a deep report or public-facing copy.

## Workflow

### 1. Intake

Extract:

- Product/service name, brand, model, country/region if relevant.
- Retail price and currency. If missing, ask once before calculating.
- User goal: fast purchase decision, deep research, self-media article, or comparison.
- Category and purchase channel if obvious.

If the user asks about current prices, recent financials, current product specs, or new releases, verify with browsing and cite sources.

### 2. Choose Mode

Use a reasonable default instead of over-asking:

- If the user only asks "值不值/为什么贵": run quick judgment.
- If the user asks "深度/完整/报告/文章/拆开讲": run deep report.
- If the user gives a product and price but no mode: start with quick judgment, then offer deep report as a follow-up.

### 3. Quick Judgment

Search only the highest-yield evidence:

```text
"[product] BOM teardown cost"
"[brand/company] gross margin annual report"
"[product/category] channel markup cost structure"
```

Output:

```text
## Quick Cost Judgment: [product] [price]

Cost center: top 3 money buckets.
Brand/company keeps: gross/net margin estimate with source.
Verdict: 值回票价 / 合理 / 偏贵 / 高溢价.
Better buys: 1-2 alternatives.
Confidence: high / medium / low and why.
```

Do not generate files for quick mode unless the user asks.

### 4. Deep Report

Follow `references/production-workflow.md`.

Default folder:

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

Process:

1. Search in parallel across teardown/BOM, company financials, channel/retail economics, competitors, and category baselines.
2. Build `data/input.json` with price, category, anchors, and source notes.
3. Run `scripts/cost_calculator.py` to create `data/cost_data.json`.
4. Run `scripts/evidence_ledger.py data/cost_data.json evidence/evidence-ledger.md`, then enrich it with source URLs, evidence tiers, and caveats from `references/evidence-rules.md`.
5. Generate report with `scripts/generate_md_report.py` and/or `scripts/generate_html_report.py`.
6. Run `scripts/validate_cost_report.py data/cost_data.json evidence/evidence-ledger.md output/validation.json`.
7. Fix FAIL items before delivery. WARN items may remain only if disclosed.

### 5. Public-Facing Copy

Only create Xiaohongshu/公众号 copy after the cost structure is internally consistent.

Use `references/social_media_template.md`, then check:

- No fake exactness.
- No defamatory wording.
- No investment advice.
- No absolute consumer claims like "必买/别买/唯一选择".
- Include one short disclaimer: "基于公开信息和行业估算，不代表品牌官方成本。"

### 6. Delivery

For deep reports, include:

- Output folder path.
- The core verdict.
- Confidence level and weakest data point.
- Generated files.
- Validation summary.
- Any unresolved caveats.

## Scripts

- `scripts/cost_calculator.py` — category baseline + evidence anchor calculation.
- `scripts/generate_charts.py` — chart generation for HTML reports.
- `scripts/generate_html_report.py` — `cost_data.json` to HTML report.
- `scripts/generate_md_report.py` — `cost_data.json` to Markdown report.
- `scripts/md_to_pdf.py` — optional Markdown to PDF conversion.
- `scripts/evidence_ledger.py` — generates the initial evidence ledger from `cost_data.json`.
- `scripts/validate_cost_report.py` — checks report data integrity and evidence coverage.

## Non-Negotiables

- Do not guess price when the user omitted it.
- Do not call a number "real cost" unless the source is official or a teardown/BOM with clear methodology.
- Do not use "智商税" as the verdict unless the evidence shows function/quality/alternatives are severely mismatched with price.
- Do not let cost percentages silently exceed or fall far below 100% without a deviation note.
- Do not deliver public copy from an unvalidated deep report.
