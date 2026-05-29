#!/usr/bin/env python3
"""
McKinsey 风格 HTML 报告生成器

输入：cost JSON + 搜索数据 + LLM 解读
输出：单文件自包含 HTML（内联 CSS + base64 图表 + 严格网格对齐）

用法：
    python generate_html_report.py <cost_data.json> <output.html>
    或从 stdin 读取 JSON → stdout 输出 HTML
"""

import sys
import os
import json
import base64
import io
from datetime import datetime

# ---- 引入图表生成 ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from generate_charts import generate_all, setup_mckinsey_style
    CHARTS_OK = True
except Exception:
    CHARTS_OK = False

# ============================================================
# CSS 样式（McKinsey 极简商务风）
# ============================================================

CSS = """
:root {
    --blue-dark: #2C3E50;
    --blue-mid: #5D7B93;
    --gray: #95A5A6;
    --gray-light: #AEB6BF;
    --orange: #E67E22;
    --white: #FFFFFF;
    --bg-light: #F8F9FA;
    --border: #E5E7E9;
    --text: #2C3E50;
    --text-secondary: #7F8C8D;
    --sans: "Helvetica Neue", "Arial", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--sans);
    color: var(--text);
    background: var(--white);
    line-height: 1.75;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

.container {
    max-width: 780px;
    margin: 0 auto;
    padding: 60px 32px 48px;
}

/* ---- 标题 ---- */
.report-title {
    font-size: 26px;
    font-weight: 700;
    color: var(--blue-dark);
    letter-spacing: -0.3px;
    margin-bottom: 8px;
    line-height: 1.3;
}

.report-subtitle {
    font-size: 14px;
    color: var(--gray-light);
    font-weight: 400;
    margin-bottom: 32px;
}

.punchline {
    font-size: 16px;
    color: var(--blue-mid);
    border-left: 3px solid var(--orange);
    padding-left: 16px;
    margin-bottom: 48px;
    line-height: 1.7;
}

/* ---- 分区 ---- */
.section {
    margin-bottom: 56px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--blue-dark);
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 1.5px solid var(--border);
    letter-spacing: -0.2px;
}

.subsection-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--blue-dark);
    margin: 24px 0 8px;
}

/* ---- 表格 ---- */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin: 16px 0 24px;
}

.data-table thead th {
    background: var(--blue-dark);
    color: var(--white);
    font-weight: 600;
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
    letter-spacing: 0.3px;
    border: none;
}

.data-table tbody td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
}

.data-table tbody tr:nth-child(even) td {
    background: var(--bg-light);
}

.data-table .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
}

.data-table .highlight {
    color: var(--orange);
    font-weight: 700;
}

/* ---- 图表容器 ---- */
.chart-container {
    margin: 28px 0;
    text-align: center;
}

.chart-container img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}

.chart-caption {
    font-size: 12px;
    color: var(--gray);
    margin-top: 6px;
}

/* ---- 利润流向 ---- */
.flow-diagram {
    font-family: "SF Mono", "Consolas", "Courier New", monospace;
    font-size: 12px;
    color: var(--blue-dark);
    background: var(--bg-light);
    padding: 20px 24px;
    border-radius: 0;
    line-height: 1.8;
    white-space: pre;
    overflow-x: auto;
    margin: 16px 0;
}

/* ---- 解读块 ---- */
.insight-block {
    margin-bottom: 28px;
}

.insight-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--blue-dark);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 2px;
}

.insight-amount {
    font-size: 22px;
    font-weight: 700;
    color: var(--orange);
    margin-bottom: 6px;
}

.insight-text {
    font-size: 14px;
    color: var(--text);
    line-height: 1.8;
}

.insight-source {
    font-size: 11px;
    color: var(--gray-light);
    margin-top: 4px;
}

/* ---- 判定徽章 ---- */
.verdict {
    display: inline-block;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.verdict-good { background: #E8F6EF; color: #1E8449; }
.verdict-ok   { background: #FEF9E7; color: #B7950B; }
.verdict-bad  { background: #FDEDEC; color: #C0392B; }

/* ---- 替代方案 ---- */
.alt-list {
    list-style: none;
    padding: 0;
}
.alt-list li {
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
}
.alt-list li:last-child { border-bottom: none; }
.alt-list .alt-name { font-weight: 700; color: var(--blue-dark); }
.alt-list .alt-save { color: var(--orange); font-weight: 600; }

/* ---- 脚注 ---- */
.footnotes {
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1.5px solid var(--border);
    font-size: 11px;
    color: var(--gray-light);
    line-height: 1.7;
}

.footnotes p { margin-bottom: 6px; }

.disclaimer {
    font-size: 10px;
    color: var(--gray);
    margin-top: 16px;
    line-height: 1.6;
}
"""


# ============================================================
# HTML 构建器
# ============================================================

def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_table(rows, num_cols=None):
    """rows: list of lists. 首行为表头."""
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    html = '<table class="data-table"><thead><tr>'
    for cell in header:
        html += f"<th>{_esc(cell)}</th>"
    html += "</tr></thead><tbody>"
    for row in body:
        html += "<tr>"
        for j, cell in enumerate(row):
            cls = ""
            cell_str = _esc(str(cell))
            # 数字列右对齐
            if j >= 1 and any(c.isdigit() for c in str(cell)):
                cls = ' class="num"'
            html += f"<td{cls}>{cell_str}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def _build_insight(dim, amount, pct, text, source, confidence):
    """单条成本解读模块"""
    stars = "●" * confidence + "○" * (5 - confidence)
    return f"""
    <div class="insight-block">
        <div class="insight-label">{_esc(dim)}</div>
        <div class="insight-amount">&yen;{amount:.0f} <span style="font-size:14px;font-weight:400;color:var(--gray);">· {pct}%</span></div>
        <div class="insight-text">{_esc(text)}</div>
        <div class="insight-source">{stars} &nbsp;{_esc(source)}</div>
    </div>"""


def _verdict_badge(judgment):
    badges = {
        "值回票价": "verdict-good",
        "合理": "verdict-ok",
        "偏贵": "verdict-bad",
        "纯智商税": "verdict-bad",
    }
    cls = badges.get(judgment, "verdict-ok")
    return f'<span class="verdict {cls}">{_esc(judgment)}</span>'


def build_html(data, interpretations=None, competitor_rows=None, value_judgment=None, alternatives=None):
    """
    构建完整 HTML 报告。

    data: cost_calculator 输出的 JSON
    interpretations: {dimension_name: "解读文字"}
    competitor_rows: [[col1, col2, ...], ...] 首行为表头
    value_judgment: {"verdict": "值回票价", "reason": "...", "alternatives": [...]}
    """
    if interpretations is None:
        interpretations = {}
    if competitor_rows is None:
        competitor_rows = []

    product = data.get("product", {})
    product_name = product.get("name", "未知产品")
    price = product.get("price", 0)
    category = product.get("category", "")
    brand_note = product.get("brand_note", "")
    breakdown = data.get("breakdown", [])
    summary = data.get("summary", {})

    # ---- 生成图表 ----
    chart_imgs = {}
    if CHARTS_OK and breakdown:
        try:
            chart_imgs = generate_all(breakdown, price)
        except Exception:
            pass

    today = datetime.now().strftime("%Y-%m-%d")
    overall_stars = "●" * round(summary.get("overall_confidence", 2)) + "○" * (5 - round(summary.get("overall_confidence", 2)))

    # ---- 构建 HTML ----
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>价格解剖：{_esc(product_name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<!-- ===== 标题区 ===== -->
<header>
    <h1 class="report-title">价格解剖：{_esc(product_name)}</h1>
    <div class="report-subtitle">成本结构分析报告 &middot; {today} &middot; 品类：{_esc(category)}</div>
</header>

<!-- ===== 一句话暴击 ===== -->
<div class="punchline">
    {_build_punchline(product_name, price, breakdown)}
</div>
"""

    # ===== 成本全景表 =====
    table_rows = [["成本维度", "估算金额", "占零售价", "可信度", "数据来源"]]
    for item in breakdown:
        stars = "●" * item["confidence"] + "○" * (5 - item["confidence"])
        # 最大项标橙色
        pct_str = f"{item['pct']}%"
        pct_range = f"({item['min_pct']}-{item['max_pct']}%)"
        table_rows.append([
            item["dimension"],
            f"¥{item['amount']:.0f}",
            f"{pct_str} {pct_range}",
            stars,
            item["source"],
        ])

    html += f"""
<!-- ===== 成本全景 ===== -->
<section class="section">
    <h2 class="section-title">成本全景</h2>
    {_build_table(table_rows)}
    <p style="font-size:12px;color:var(--gray);margin-top:4px;">
        合计占比：{summary.get('total_pct', 'N/A')}%
        &nbsp;&middot;&nbsp;
        整体可信度：{overall_stars}
        &nbsp;&middot;&nbsp;
        硬数据点 {summary.get('hard_data_points', 0)} 个
        &nbsp;&middot;&nbsp;
        估算点 {summary.get('estimated_points', 0)} 个
    </p>
</section>
"""

    # ===== 图表区 =====
    if chart_imgs:
        html += '<section class="section"><h2 class="section-title">可视化</h2>'
        if "bar" in chart_imgs:
            html += f'<div class="chart-container"><img src="{chart_imgs["bar"]}" alt="成本拆解条图"><div class="chart-caption">图1：各成本维度金额与占比 &mdash; 橙色为最大项</div></div>'
        if "stacked" in chart_imgs:
            html += f'<div class="chart-container"><img src="{chart_imgs["stacked"]}" alt="成本构成堆叠图"><div class="chart-caption">图2：100% 堆叠 &mdash; 每项成本在总价中的比重</div></div>'
        html += '</section>'

    # ===== 逐项解读 =====
    html += '<section class="section"><h2 class="section-title">逐项深挖</h2>'
    for item in breakdown:
        dim = item["dimension"]
        text = interpretations.get(dim, f"{dim}约 ¥{item['amount']:.0f}，占零售价的 {item['pct']}%。")
        html += _build_insight(
            dim, item["amount"], item["pct"],
            text, item["source"], item["confidence"]
        )
    html += '</section>'

    # ===== 利润流向图（ASCII风格→代码块） =====
    flow_lines = _build_flow(breakdown, price)
    html += f"""
<section class="section">
    <h2 class="section-title">利润流向</h2>
    <div class="flow-diagram">{_esc(flow_lines)}</div>
</section>
"""

    # ===== 竞品对比 =====
    if competitor_rows:
        html += f"""
<section class="section">
    <h2 class="section-title">竞品对比</h2>
    {_build_table(competitor_rows)}
</section>
"""

    # ===== 值不值 =====
    if value_judgment:
        verdict = value_judgment.get("verdict", "")
        reason = value_judgment.get("reason", "")
        alts = value_judgment.get("alternatives", [])

        html += f"""
<section class="section">
    <h2 class="section-title">值不值？</h2>
    <p style="margin-bottom:16px;">{_verdict_badge(verdict)}</p>
    <p style="font-size:14px;line-height:1.8;color:var(--text);margin-bottom:16px;">{_esc(reason)}</p>
"""
        if alts:
            html += '<p class="subsection-title">更优选择</p><ul class="alt-list">'
            for alt in alts:
                name = alt.get("name", "")
                save = alt.get("save", "")
                why = alt.get("why", "")
                html += f'<li><span class="alt-name">{_esc(name)}</span> &mdash; <span class="alt-save">省 ¥{_esc(str(save))}</span> &middot; {_esc(why)}</li>'
            html += '</ul>'
        html += '</section>'

    # ===== 脚注 =====
    html += f"""
<footer class="footnotes">
    <p><strong>品类基线</strong>：{_esc(category)}，基于 {_esc(brand_note or '行业公开数据')}</p>
    <p><strong>生成日期</strong>：{today} &middot; Cost-Anatomist</p>
    <p class="disclaimer">免责声明：以上分析基于公开信息和行业经验估算，非品牌官方数据。实际成本结构可能因供应链变化、采购量、定价策略等因素有显著差异。本报告仅供决策参考，不构成投资或购买建议。</p>
</footer>

</div>
</body>
</html>"""

    return html


def _build_punchline(name, price, breakdown):
    """生成暴击金句"""
    if not breakdown:
        return f"你花了 &yen;{price} 买这个 {_esc(name)}。"
    # 最大成本项
    biggest = max(breakdown, key=lambda x: x["amount"])
    bom = next((d for d in breakdown if "物料" in d["dimension"] or "原料" in d["dimension"] or "食材" in d["dimension"]), None)
    if bom:
        return (f"你花了 &yen;{price} 买这个 {_esc(name)}，但物料成本仅 &yen;{bom['amount']:.0f}。"
                f"最大的一笔 &yen;{biggest['amount']:.0f}（{biggest['pct']}%）"
                f"花在了「{_esc(biggest['dimension'])}」上。")
    return (f"你花了 &yen;{price} 买这个 {_esc(name)}。"
            f"最大的一笔 &yen;{biggest['amount']:.0f}（{biggest['pct']}%）"
            f"花在了「{_esc(biggest['dimension'])}」上。")


def _build_flow(breakdown, price):
    lines = [f"你付的 ¥{price}"]
    for i, item in enumerate(breakdown):
        prefix = "└─" if i == len(breakdown) - 1 else "├─"
        lines.append(f"{prefix} ¥{item['amount']:.0f} ({item['pct']}%) → {item['dimension']}")
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        # stdin 模式
        raw = sys.stdin.read()
        if not raw.strip():
            print("用法: python generate_html_report.py <cost_data.json> [output.html]", file=sys.stderr)
            sys.exit(1)
        data = json.loads(raw)
        html = build_html(data)
        print(html)
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        html = build_html(data)
        out_path = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace(".json", ".html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML 报告已生成: {out_path}")


if __name__ == "__main__":
    main()
