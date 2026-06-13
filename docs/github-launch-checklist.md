# GitHub Launch Checklist

Use this checklist after pushing the repository updates. These settings improve discoverability, trust, and measurable downloads.

## Repository About Section

Set the repository description to:

```text
Cost-Xray: a Claude Code / Codex skill for product cost breakdown and pricing analysis.
```

Set the website field only if you later create a demo page, documentation page, or release landing page.

Add topics:

```text
claude-code
codex
skill
ai-agent
cost-analysis
pricing
consumer-research
business-analysis
product-research
xray
```

## Release

Create a first release:

- Tag: `v0.1.0`
- Title: `Cost-Xray v0.1.0`
- Target: `main`

Release notes:

````markdown
## Cost-Xray v0.1.0

First public release of Cost-Xray, a Claude Code / Codex skill for product cost breakdown and pricing analysis.

### Highlights

- Analyze products from a product name and purchase price.
- Estimate cost structure across BOM, manufacturing, R&D, marketing, channel margin, tax, brand premium, after-sales, and profit.
- Support quick judgment and deep report modes.
- Generate Markdown and HTML-style cost reports.
- Include category baselines, report templates, and a DJI Mic Mini 2 example.

### Install

Codex:

```bash
git clone https://github.com/58xnrt46z2-a11y/cost-xray.git ~/.codex/skills/cost-xray
```

Claude Code:

```bash
git clone https://github.com/58xnrt46z2-a11y/cost-xray.git ~/.claude/skills/cost-xray
```
````

Optional: attach a zip archive or example HTML report as a release asset if you want GitHub to show asset download counts.

## Social Launch Copy

Short launch post:

```text
I built Cost-Xray, a Claude Code / Codex skill that breaks down product pricing into materials, manufacturing, R&D, marketing, channels, tax, brand premium, and profit.

Give it a product name + price, and it tells you where the money likely goes and whether the product is worth it.

Repo: https://github.com/58xnrt46z2-a11y/cost-xray
```

Chinese launch post:

```text
我做了一个 Claude Code / Codex skill：Cost-Xray（成本透视）。

你只要输入「产品名 + 价格」，它会搜索拆机/BOM、财报、供应链、行业基线和竞品信息，把物料、制造、研发、营销、渠道、税费、品牌溢价和利润拆开看，最后给一个明确的「值不值」判断。

适合做消费决策、商业观察、小红书/公众号选题和产品价格分析。

GitHub: https://github.com/58xnrt46z2-a11y/cost-xray
```

## Traffic Check

After launch, check:

- GitHub `Insights -> Traffic`
- Views and unique visitors
- Clones and unique cloners
- Referring sites
- Popular content

GitHub public search usually takes time to re-index README and topic changes. Recheck after 24-48 hours.
