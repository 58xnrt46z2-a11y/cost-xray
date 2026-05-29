#!/usr/bin/env python3
"""
McKinsey 风格图表生成器

生成扁平、干净、无 3D/渐变/多余装饰的商务图表：
- 横向条形图（成本拆解）
- 堆叠条形图（利润流向）
"""

import sys
import json
import os
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import numpy as np

# ---- McKinsey 配色 ----
BLUE_DARK = "#2C3E50"
BLUE_MID = "#5D7B93"
GRAY = "#95A5A6"
ORANGE = "#E67E22"
LIGHT_BG = "#F8F9FA"
WHITE = "#FFFFFF"

# 图表调色板（低饱和蓝系 + 一个橙色）
CHART_PALETTE = [
    "#3A6B8C", "#5B8FA8", "#7BA9C0", "#9BC3D8",
    "#4A7A9B", "#6899B8", "#86B0CC", "#A4C7DF",
    "#E67E22", "#C0C0C0",
]


def find_cjk_font():
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    for f in fm.fontManager.ttflist:
        if any(k in f.name.lower() for k in ["yahei", "simhei", "noto sans cjk"]):
            return f.fname
    return None


def setup_mckinsey_style():
    """全局应用 McKinsey 风格"""
    font_path = find_cjk_font()
    if font_path:
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        font_name = prop.get_name()
        plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams.get("font.sans-serif", [])
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False

    # McKinsey 风格：干净、扁平、无线框
    plt.rcParams.update({
        "axes.facecolor": WHITE,
        "figure.facecolor": WHITE,
        "axes.edgecolor": "#D5D8DC",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.color": "#D5D8DC",
        "grid.linewidth": 0.5,
        "xtick.color": GRAY,
        "ytick.color": BLUE_DARK,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": BLUE_DARK,
        "axes.labelcolor": GRAY,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "legend.labelcolor": GRAY,
        "legend.loc": "lower right",
    })


def fig_to_base64(fig, dpi=150):
    """将 matplotlib figure 转为 base64 PNG"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=WHITE, edgecolor="none")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


def bar_chart(breakdown, price):
    """McKinsey 横向条形图：按金额降序，橙色高亮最大项"""
    setup_mckinsey_style()

    dims = [d["dimension"] for d in breakdown]
    amounts = [d["amount"] for d in breakdown]
    pcts = [d["pct"] for d in breakdown]

    # 排序
    order = np.argsort(amounts)
    dims = [dims[i] for i in order]
    amounts = [amounts[i] for i in order]
    pcts = [pcts[i] for i in order]

    max_idx = amounts.index(max(amounts))
    colors = [ORANGE if i == max_idx else BLUE_MID for i in range(len(amounts))]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(range(len(dims)), amounts, height=0.55, color=colors, edgecolor=WHITE, linewidth=0)

    # 数据标注
    for i, (amt, pct) in enumerate(zip(amounts, pcts)):
        label = f"  ¥{amt:.0f}  ·  {pct}%"
        ax.text(amt + max(amounts) * 0.01, i, label, va="center", fontsize=8.5,
                color=BLUE_DARK, fontweight="bold" if i == max_idx else "normal")

    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels(dims, fontsize=9)
    ax.set_xlim(0, max(amounts) * 1.25)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("¥%.0f"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False)
    ax.set_title(f"成本拆解  ·  总价 ¥{price}", loc="left", pad=12)

    plt.tight_layout()
    return fig_to_base64(fig)


def stacked_bar_chart(breakdown, price):
    """堆叠条形图：单条展示成本如何构成 100%（McKinsey 经典图型）"""
    setup_mckinsey_style()

    dims = [d["dimension"] for d in breakdown]
    pcts = [d["pct"] for d in breakdown]
    amounts = [d["amount"] for d in breakdown]

    # 按占比排序
    order = np.argsort(pcts)
    dims = [dims[i] for i in order]
    pcts = [pcts[i] for i in order]
    amounts = [amounts[i] for i in order]

    fig, ax = plt.subplots(figsize=(10, 1.8))
    left = 0
    for i, (dim, pct, amt) in enumerate(zip(dims, pcts, amounts)):
        color = ORANGE if pct == max(pcts) else CHART_PALETTE[i % len(CHART_PALETTE)]
        bar = ax.barh(0, pct, left=left, height=0.45, color=color, edgecolor=WHITE, linewidth=1.5)
        # 标注（占比 > 4% 的才标，避免太挤）
        if pct > 4:
            ax.text(left + pct / 2, 0, f"{dim}\n¥{amt:.0f} ({pct}%)",
                    ha="center", va="center", fontsize=7.5, color=WHITE if pct > 15 else BLUE_DARK,
                    fontweight="bold")
        left += pct

    ax.set_xlim(0, 105)
    ax.set_ylim(-0.5, 0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.set_title(f"¥{price} 的 100% 构成", loc="left", pad=10)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())

    plt.tight_layout()
    return fig_to_base64(fig)


def flow_chart(breakdown, price):
    """瀑布图风格：从总价逐步拆出各项成本（可选）"""
    return None  # 暂不实现，堆叠条已足够


def generate_all(breakdown, price):
    """生成全部图表，返回 {name: base64_data_uri}"""
    charts = {}
    charts["bar"] = bar_chart(breakdown, price)
    charts["stacked"] = stacked_bar_chart(breakdown, price)
    return charts


# ---- CLI ----
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_charts.py <cost_data.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    price = data.get("product", {}).get("price", 0)
    breakdown = data.get("breakdown", [])
    charts = generate_all(breakdown, price)

    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(__file__)), "charts_output")
    os.makedirs(out, exist_ok=True)
    for name, b64 in charts.items():
        path = os.path.join(out, f"{name}.png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64.split(",", 1)[1]))
        print(f"已生成: {path}")
