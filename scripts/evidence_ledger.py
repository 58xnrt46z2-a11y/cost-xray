#!/usr/bin/env python3
"""
证据账本生成器

为每个成本数据点记录来源类型、可信度等级、如何使用该数据。
输出 Markdown 证据账本：区分官方数据、第三方数据、行业估算和必要假设。
"""

import json
import sys
from datetime import datetime
from typing import Optional

# 来源分类
SOURCE_TYPES = {
    5: "官方硬数据 (official_financial)",
    4: "权威第三方 (third_party_teardown)",
    3: "行业研报/专家访谈 (industry_report)",
    2: "行业基线估算 (baseline_estimate)",
    1: "推测/假设 (speculation)",
}

# 使用方式
USAGE_LABELS = {
    "anchor": "锚定——搜索到的具体数字，直接采用",
    "cross_ref": "交叉验证——多个来源互相印证",
    "baseline_fill": "基线填补——无搜索结果，用品类经验区间",
    "derived": "推导——从其他数据点间接推算",
}


def build_ledger(breakdown, search_sources=None):
    """
    从成本拆解 JSON 构建证据账本

    breakdown: [{"dimension": ..., "amount": ..., "pct": ..., "confidence": ..., "source": ...}, ...]
    search_sources: [{"url": ..., "title": ..., "type": ..., "supports": [...]}, ...] (可选)
    """
    if search_sources is None:
        search_sources = []

    rows = []
    for item in breakdown:
        conf = item.get("confidence", 2)
        source_type = SOURCE_TYPES.get(conf, SOURCE_TYPES[2])

        # 判断使用方式
        if conf >= 5:
            usage = "anchor"
        elif conf >= 4:
            usage = "anchor"
        elif conf >= 3:
            usage = "cross_ref"
        elif conf >= 2:
            usage = "baseline_fill"
        else:
            usage = "derived"

        rows.append({
            "dimension": item["dimension"],
            "amount": item["amount"],
            "pct": item["pct"],
            "confidence": conf,
            "source_type": source_type,
            "source_label": item.get("source", "未标注"),
            "usage": USAGE_LABELS.get(usage, usage),
        })

    return rows


def render_ledger_md(rows, product_name, price, overall_confidence):
    """生成 Markdown 格式的证据账本"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# 证据账本 · {product_name}

**总价**：¥{price:,}
**报告生成时间**：{today}
**整体可信度**：{"●" * round(overall_confidence) + "○" * (5 - round(overall_confidence))} ({overall_confidence}/5)

---

## 数据来源分级

| 等级 | 类型 | 判定标准 |
|------|------|---------|
| ●●●●● | 官方硬数据 | 上市公司财报、品牌官方公布的成本/毛利率 |
| ●●●● | 权威第三方 | iFixit 拆机 BOM、头部券商研报、知名科技媒体拆解 |
| ●●● | 行业研报/专家 | 行业白皮书、咨询公司报告、从业者访谈 |
| ●● | 基线估算 | 品类通用成本结构、行业经验区间 |
| ● | 推测/假设 | 无直接数据，基于近似品类类比 |

---

## 逐项证据记录

| 成本维度 | 金额 | 占比 | 可信度 | 来源类型 | 证据来源 | 使用方式 |
|---------|------|------|--------|---------|---------|---------|
"""

    for row in rows:
        stars = "●" * row["confidence"] + "○" * (5 - row["confidence"])
        md += (
            f"| {row['dimension']} "
            f"| ¥{row['amount']:,.0f} "
            f"| {row['pct']}% "
            f"| {stars} "
            f"| {row['source_type']} "
            f"| {row['source_label'][:40]} "
            f"| {row['usage']} |\n"
        )

    # 统计
    official = sum(1 for r in rows if r["confidence"] >= 5)
    third_party = sum(1 for r in rows if r["confidence"] == 4)
    industry = sum(1 for r in rows if r["confidence"] == 3)
    baseline = sum(1 for r in rows if r["confidence"] == 2)
    guess = sum(1 for r in rows if r["confidence"] <= 1)

    md += f"""
---

## 证据覆盖统计

| 数据等级 | 数量 | 占比 |
|---------|------|------|
| 官方硬数据 (●5) | {official} | {official/len(rows)*100:.0f}% |
| 权威第三方 (●4) | {third_party} | {third_party/len(rows)*100:.0f}% |
| 行业研报 (●3) | {industry} | {industry/len(rows)*100:.0f}% |
| 基线估算 (●2) | {baseline} | {baseline/len(rows)*100:.0f}% |
| 推测/假设 (●1) | {guess} | {guess/len(rows)*100:.0f}% |

> **判定**：{_coverage_verdict(official, third_party, len(rows))}

---

*证据账本由 Cost-Xray 自动生成 · {today}*
"""
    return md


def _coverage_verdict(official, third_party, total):
    hard_ratio = (official + third_party) / total
    if hard_ratio >= 0.7:
        return "🟢 证据覆盖良好——大部分数据有硬数据或权威第三方支撑，分析结论可靠。"
    elif hard_ratio >= 0.4:
        return "🟡 证据覆盖中等——有部分行业估算数据，建议对关键维度（如物料成本、毛利率）追加深度搜索。"
    else:
        return "🔴 证据覆盖不足——多数数据依赖行业基线或推测，建议触发深度模式重新搜索。"


# ---- CLI ----
def main():
    if len(sys.argv) < 2:
        print("用法: python evidence_ledger.py <cost_data.json> [output.md]", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    product = data.get("product", {})
    name = product.get("name", "未知产品")
    price = product.get("price", 0)
    breakdown = data.get("breakdown", [])
    summary = data.get("summary", {})

    rows = build_ledger(breakdown)
    md = render_ledger_md(rows, name, price, summary.get("overall_confidence", 2))

    out_path = sys.argv[2] if len(sys.argv) > 2 else "evidence-ledger.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"证据账本已生成: {out_path}")


if __name__ == "__main__":
    main()
