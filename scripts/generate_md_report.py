#!/usr/bin/env python3
"""
Markdown 报告生成器

从 cost_calculator.py 的 JSON 输出生成"尖锐洞察风"的完整 Markdown 报告。

用法：
    echo '{...cost_data_json...}' | python generate_md_report.py
    或作为模块导入：from generate_md_report import generate_report
"""

import json
import sys
from datetime import datetime
from typing import Optional


def _confidence_stars(level: int) -> str:
    """可信度数字转星星"""
    stars = min(5, max(1, level))
    return "⭐" * stars


def _generate_opener(product_name: str, price: float, breakdown: list, category: str) -> str:
    """生成一句话暴击开头"""
    # 找到占比最大的溢价项
    high_margin_items = [
        item for item in breakdown
        if item["dimension"] in ("品牌溢价", "营销推广", "渠道加价", "渠道/商场", "渠道/零售",
                                  "营销/PR", "营销获客")
    ]
    high_margin_items.sort(key=lambda x: x["amount"], reverse=True)

    biggest = high_margin_items[0] if high_margin_items else breakdown[0]

    bom = next((item for item in breakdown if "物料" in item["dimension"] or "原料" in item["dimension"] or "食材" in item["dimension"] or "耗材" in item["dimension"]), None)

    if bom:
        return (f"你花了 ¥{price} 买这个 {product_name}，"
                f"但它的物料成本可能只有 ¥{bom['amount']:.0f} 左右。"
                f"最大头的 ¥{biggest['amount']:.0f}（{biggest['pct']}%）"
                f"花在了「{biggest['dimension']}」上——{_dimension_punchline(biggest['dimension'])}")
    else:
        return (f"你花了 ¥{price} 买这个 {product_name}。"
                f"其中 ¥{biggest['amount']:.0f}（{biggest['pct']}%）"
                f"花在了「{biggest['dimension']}」上——{_dimension_punchline(biggest['dimension'])}")


def _dimension_punchline(dim: str) -> str:
    """为每个成本维度生成一句扎心的总结"""
    punchlines = {
        "物料成本(BOM)": "这部分钱给了上游供应商，它们赚得最少，但离了你不行",
        "制造/代工": "代工厂累死累活，一台赚不了几块钱",
        "研发摊销": "你为工程师的工资和专利费买单",
        "营销推广": "你买的不是产品，是KOL的那句'这个真好用'",
        "渠道加价": "中间商赚差价，从来不是玩笑话",
        "品牌溢价": "品牌值钱，但不代表溢价全合理",
        "税费": "谁也逃不掉的硬成本",
        "企业净利": "品牌方股东最后装进口袋的钱",
        "营销/PR": "明星代言、时装周、旗舰店——都是你买单",
        "营销获客": "商家为了找到你花的钱，比服务本身还贵",
        "渠道/零售": "商场和经销商抽走的比你想象的多得多",
        "渠道/商场": "红星美凯龙们赚的钱，比造家具的多",
        "售后/保修": "品牌预留的退换货和维修成本",
        "原料/料体": "瓶子里真正有用的东西，其实没多少",
        "包装(瓶器)": "那个让你舍不得扔的漂亮瓶子，也是花重金买的",
        "医生/操作师": "医生的手值钱——但可能没你想的那么值钱",
        "讲师/教研": "老师的课酬，通常只占学费的一小半",
        "房租/场地": "你付的钱在替商家交房租",
        "物流仓储": "从工厂到你手上的每一步都有人收过路费",
        "服务器/基础设施": "云服务商赚着稳定的月费",
        "研发/工程师": "程序员的工资是你订阅费的最大开销",
        "销售/市场": "为了让你点'购买'按钮，商家花了不少",
    }
    return punchlines.get(dim, "这笔钱养活了整条产业链上的一个环节")


def _build_breakdown_table(breakdown: list, price: float) -> str:
    """生成成本全景表格"""
    rows = []
    for item in breakdown:
        stars = _confidence_stars(item["confidence"])
        rows.append(
            f"| {item['dimension']} | ¥{item['amount']:.0f} | {item['pct']}% "
            f"({item['min_pct']}-{item['max_pct']}%) | {stars} | {item['source']} |"
        )

    header = "| 成本维度 | 估算金额 | 占零售价（区间） | 可信度 | 数据来源 |"
    sep = "|---------|---------|----------------|--------|---------|"

    return "\n".join([header, sep] + rows)


def _build_flow_chart(breakdown: list, price: float) -> str:
    """生成利润流向 ASCII 图"""
    lines = [f"你付的 ¥{price}", "│"]
    n = len(breakdown)
    for i, item in enumerate(breakdown):
        prefix = "└─" if i == n - 1 else "├─"
        lines.append(
            f"{prefix} ¥{item['amount']:.0f} ({item['pct']}%) → {item['dimension']}"
        )
    return "\n".join(lines)


def _dimension_detail(item: dict, category: str) -> str:
    """为每项成本生成 150-300 字的通俗解读模板"""
    dim = item["dimension"]
    amount = item["amount"]
    pct = item["pct"]
    confidence = item["confidence"]
    source = item["source"]

    # 根据维度类型生成针对性解读
    templates = {
        "物料成本(BOM)": (
            f"物料成本约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"这部分包括芯片、传感器、电池、结构件等核心元器件的采购成本。"
            f"上游供应商（如高通、TI、索尼等）的芯片毛利率通常在 50-60%，"
            f"而被动元件和结构件的利润要薄得多。"
            f"对于这个价格段的产品，BOM 成本通常控制在这个区间。"
        ),
        "制造/代工": (
            f"代工费用约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"消费电子代工厂（富士康、立讯精密、歌尔股份等）的净利率极低，"
            f"通常在 3-5%——也就是说，代工厂真正装进口袋的可能只有十几块钱。"
            f"制造业赚的是辛苦钱，规模越大、单价越低的订单，代工厂议价能力越弱。"
        ),
        "营销推广": (
            f"营销费用约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"这笔钱花在了：KOL种草投放、信息流广告、发布会活动、电商平台的推广费用。"
            f"对于消费品来说，营销费用往往是第二或第三大成本项。"
            f"你看到的每一条开箱视频、每一篇种草笔记，都是品牌方花钱买来的。"
        ),
        "品牌溢价": (
            f"品牌溢价约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"这是超越物料和功能价值的、纯粹的品牌认知溢价。"
            f"它来自于品牌多年的声誉积累、消费者信任、以及「用这个牌子」的身份标签。"
            f"品牌溢价不是坏事——好品牌确实值得一定的溢价。"
            f"但问题是：这笔溢价有没有超出合理范围？"
        ),
        "渠道加价": (
            f"渠道加价约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"经销商、零售商、电商平台——每一层都要抽一笔。"
            f"线下渠道（数码城、专柜）的抽成通常高于线上，"
            f"这也是为什么品牌越来越推崇直营——省掉渠道成本，利润直接留给自己。"
        ),
        "企业净利": (
            f"品牌方净利润约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"这是品牌股东最终装进口袋的钱。"
            f"要判断这个利润率是否合理，可以和同行对比——"
            f"消费电子品牌的净利率通常在 5-10% 之间。"
        ),
    }

    if dim in templates:
        detail = templates[dim]
    else:
        detail = (
            f"{dim}约 ¥{amount:.0f}，占零售价的 {pct}%。"
            f"这部分成本对应产业链上的一个必要环节。"
        )

    # 追加来源说明
    if confidence >= 4:
        detail += f"\n\n*数据可信度较高：{source}。*"
    elif confidence == 3:
        detail += f"\n\n*数据参考：{source}，有一定参考价值。*"
    else:
        detail += f"\n\n*此为行业经验估算（{source}），精确数字建议触发深度搜索模式获取。*"

    return detail


def generate_report(cost_data: dict, interpretations: Optional[dict] = None) -> str:
    """
    主报告生成函数

    参数：
        cost_data: cost_calculator.py 的输出 JSON
        interpretations: 各项成本的人工/LLM写的深度解读（可选）

    返回：完整的 Markdown 报告字符串
    """
    if interpretations is None:
        interpretations = {}

    product = cost_data.get("product", {})
    product_name = product.get("name", "未知产品")
    price = product.get("price", 0)
    category = product.get("category", "消费电子")
    breakdown = cost_data.get("breakdown", [])
    summary = cost_data.get("summary", {})

    opener = _generate_opener(product_name, price, breakdown, category)
    table = _build_breakdown_table(breakdown, price)
    flow = _build_flow_chart(breakdown, price)

    # 逐项深度解读
    details_sections = []
    for i, item in enumerate(breakdown):
        dim = item["dimension"]
        if dim in interpretations:
            text = interpretations[dim]
        else:
            text = _dimension_detail(item, category)

        details_sections.append(f"### {i+1}. {dim}\n\n{text}")

    details_md = "\n\n".join(details_sections)

    # 竞品对比占位（LLM填充）
    competitor_section = "{competitor_analysis}"

    # 值不值占位（LLM填充）
    value_section = "{value_judgment}"

    # 数据来源附录
    sources_list = []
    for item in breakdown:
        stars = _confidence_stars(item["confidence"])
        sources_list.append(
            f"| {item['dimension']} | {item['source']} | {stars} |"
        )

    sources_header = "| 成本维度 | 数据来源 | 可信度 |"
    sources_sep = "|---------|---------|--------|"
    sources_table = "\n".join([sources_header, sources_sep] + sources_list)

    today = datetime.now().strftime("%Y-%m-%d")

    report = f"""# 🔪 价格解剖：{product_name}（¥{price}）

> **一句话暴击**：{opener}

---

## 📊 成本全景

{table}

> 合计占比：{summary.get('total_pct', 'N/A')}%。{summary.get('deviation_note', '')}
> 整体可信度：{_confidence_stars(round(summary.get('overall_confidence', 2)))} · 硬数据点 {summary.get('hard_data_points', 0)} 个 · 估算点 {summary.get('estimated_points', 0)} 个

---

## 🔍 逐项深挖

{details_md}

---

## 💸 利润流向图

```
{flow}
```

---

## 🆚 竞品对比

{competitor_section}

---

## ⚖️ 值不值？

{value_section}

---

## 📚 数据来源

{sources_table}

---

> **免责声明**：以上分析基于公开信息和行业经验估算，非品牌官方数据。实际成本结构可能因供应链变化、采购量、定价策略等因素有显著差异。本报告仅供决策参考。

---
*报告由 Cost-Anatomist 生成 · {today}*
"""

    return report


def main():
    """从 stdin 读取 JSON，输出 Markdown 报告"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print("错误：无输入数据", file=sys.stderr)
            sys.exit(1)

        data = json.loads(raw)
        report = generate_report(data)
        print(report)

    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
