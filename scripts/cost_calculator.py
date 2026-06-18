#!/usr/bin/env python3
"""
成本估算计算引擎

输入：产品价格、品类标签、各项百分比区间、搜索到的硬数据锚点
输出：JSON格式的完整成本拆解

用法：
    echo '{"price": 350, "category": "消费电子", "anchors": {...}}' | python cost_calculator.py
    或作为模块导入：from cost_calculator import calculate
"""

import json
import sys
from typing import Optional


# 行业基线数据库（与 references/industry-baselines.md 同步）
BASELINES = {
    "消费电子": {
        "物料成本(BOM)": (0.20, 0.35),
        "制造/代工": (0.05, 0.10),
        "研发摊销": (0.05, 0.10),
        "营销推广": (0.05, 0.15),
        "渠道加价": (0.20, 0.35),
        "物流仓储": (0.02, 0.05),
        "品牌溢价": (0.10, 0.25),
        "税费": (0.05, 0.13),
        "售后/保修": (0.02, 0.04),
        "企业净利": (0.05, 0.10),
    },
    "化妆品/护肤品": {
        "原料/料体": (0.05, 0.15),
        "包装(瓶器)": (0.05, 0.10),
        "研发/配方": (0.03, 0.05),
        "生产制造": (0.03, 0.05),
        "营销推广": (0.30, 0.50),
        "渠道加价": (0.20, 0.30),
        "品牌溢价": (0.15, 0.25),
        "税费": (0.05, 0.13),
        "企业净利": (0.10, 0.20),
    },
    "奢侈品/时尚": {
        "原材料": (0.05, 0.15),
        "手工/制造": (0.10, 0.20),
        "研发/设计": (0.02, 0.05),
        "营销/PR": (0.15, 0.25),
        "渠道/零售": (0.20, 0.30),
        "品牌溢价": (0.40, 0.60),
        "税费/关税": (0.05, 0.15),
        "企业净利": (0.10, 0.20),
    },
    "餐饮/食品饮料": {
        "食材/原料": (0.25, 0.35),
        "人工": (0.15, 0.25),
        "房租/场地": (0.10, 0.20),
        "营销": (0.05, 0.10),
        "研发/菜品开发": (0.01, 0.03),
        "管理/行政": (0.03, 0.05),
        "税费": (0.03, 0.06),
        "企业净利": (0.05, 0.15),
    },
    "软件/SaaS": {
        "服务器/基础设施": (0.05, 0.15),
        "研发/工程师": (0.30, 0.50),
        "销售/市场": (0.20, 0.40),
        "客户成功/支持": (0.05, 0.10),
        "管理/行政": (0.05, 0.10),
        "税费": (0.05, 0.15),
        "企业净利": (0.15, 0.30),
    },
    "教育/培训服务": {
        "讲师/教研": (0.30, 0.45),
        "场地/设备": (0.10, 0.20),
        "课程研发": (0.05, 0.10),
        "营销获客": (0.10, 0.20),
        "教务/管理": (0.05, 0.10),
        "税费": (0.03, 0.06),
        "企业净利": (0.10, 0.20),
    },
    "医疗美容服务": {
        "耗材/药品": (0.05, 0.10),
        "医生/操作师": (0.20, 0.30),
        "设备摊销": (0.02, 0.05),
        "场地/装修": (0.15, 0.25),
        "营销获客": (0.20, 0.35),
        "资质/合规": (0.02, 0.05),
        "税费": (0.03, 0.06),
        "企业净利": (0.15, 0.25),
    },
    "家居/家具": {
        "原材料": (0.20, 0.30),
        "制造/加工": (0.10, 0.15),
        "设计/研发": (0.03, 0.05),
        "物流/仓储": (0.05, 0.10),
        "渠道/商场": (0.25, 0.40),
        "营销": (0.05, 0.10),
        "税费": (0.05, 0.13),
        "企业净利": (0.05, 0.10),
    },
}

# 成本维度中文名称映射（按链条顺序）
DIMENSION_ORDER = {
    "消费电子": [
        "物料成本(BOM)", "制造/代工", "研发摊销", "物流仓储",
        "营销推广", "渠道加价", "品牌溢价", "税费", "售后/保修", "企业净利"
    ],
    "化妆品/护肤品": [
        "原料/料体", "包装(瓶器)", "研发/配方", "生产制造",
        "营销推广", "渠道加价", "品牌溢价", "税费", "企业净利"
    ],
    "奢侈品/时尚": [
        "原材料", "手工/制造", "研发/设计", "营销/PR",
        "渠道/零售", "品牌溢价", "税费/关税", "企业净利"
    ],
    "餐饮/食品饮料": [
        "食材/原料", "人工", "房租/场地", "营销",
        "研发/菜品开发", "管理/行政", "税费", "企业净利"
    ],
    "软件/SaaS": [
        "服务器/基础设施", "研发/工程师", "销售/市场",
        "客户成功/支持", "管理/行政", "税费", "企业净利"
    ],
    "教育/培训服务": [
        "讲师/教研", "场地/设备", "课程研发", "营销获客",
        "教务/管理", "税费", "企业净利"
    ],
    "医疗美容服务": [
        "耗材/药品", "医生/操作师", "设备摊销", "场地/装修",
        "营销获客", "资质/合规", "税费", "企业净利"
    ],
    "家居/家具": [
        "原材料", "制造/加工", "设计/研发", "物流/仓储",
        "渠道/商场", "营销", "税费", "企业净利"
    ],
}


def get_baseline(category: str) -> dict:
    """获取品类的成本基线，支持模糊匹配"""
    if category in BASELINES:
        return BASELINES[category]

    # 模糊匹配
    for key in BASELINES:
        if key in category or category in key:
            return BASELINES[key]

    # 默认返回消费电子（最通用）
    return BASELINES["消费电子"]


def apply_anchors(baseline: dict, anchors: dict) -> dict:
    """
    将搜索到的硬数据锚点应用至基线。
    anchors 格式：{"物料成本(BOM)": {"pct": 0.28, "confidence": 4, "source": "iFixit拆机"}}
    返回：更新后的基线，含 confidence 和 source 信息
    """
    result = {}
    for dim, (lo, hi) in baseline.items():
        entry = {
            "min_pct": lo,
            "max_pct": hi,
            "mid_pct": round((lo + hi) / 2, 4),
            "confidence": 2,  # 默认 ⭐⭐
            "source": "行业经验基线",
        }

        if dim in anchors:
            anchor = anchors[dim]
            if "pct" in anchor:
                pct = anchor["pct"]
                entry["mid_pct"] = round(pct, 4)
                # 硬数据锚定后，收窄区间为 ±20%
                margin = pct * 0.2
                entry["min_pct"] = round(max(0.0, pct - margin), 4)
                entry["max_pct"] = round(min(1.0, pct + margin), 4)
            if "min_pct" in anchor and "max_pct" in anchor:
                entry["min_pct"] = round(anchor["min_pct"], 4)
                entry["max_pct"] = round(anchor["max_pct"], 4)
                entry["mid_pct"] = round((anchor["min_pct"] + anchor["max_pct"]) / 2, 4)
            entry["confidence"] = anchor.get("confidence", 4)
            entry["source"] = anchor.get("source", "搜索结果")

        result[dim] = entry

    return result


def normalize(results: dict) -> dict:
    """使所有维度百分比之和在 90-110% 之间，如超出则按比例缩放"""
    total_mid = sum(v["mid_pct"] for v in results.values())

    if total_mid == 0:
        return results

    if 0.90 <= total_mid <= 1.10:
        return results

    # 需要归一化
    target = 1.0
    scale = target / total_mid
    for dim in results:
        results[dim]["mid_pct"] = round(results[dim]["mid_pct"] * scale, 4)
        results[dim]["min_pct"] = round(results[dim]["min_pct"] * scale, 4)
        results[dim]["max_pct"] = round(results[dim]["max_pct"] * scale, 4)

    return results


def calculate(price: float, category: str, anchors: Optional[dict] = None,
              brand_note: Optional[str] = None) -> dict:
    """
    主计算函数

    参数：
        price: 产品零售价格（元）
        category: 品类标签
        anchors: 搜索到的硬数据锚点（可选）
        brand_note: 品牌特殊说明（可选）

    返回：完整的成本拆解 JSON
    """
    if anchors is None:
        anchors = {}

    baseline = get_baseline(category)
    dimensions = DIMENSION_ORDER.get(category)
    if dimensions is None:
        # 模糊匹配取 dimension order
        for key in DIMENSION_ORDER:
            if key in category or category in key:
                dimensions = DIMENSION_ORDER[key]
                break
        if dimensions is None:
            dimensions = DIMENSION_ORDER["消费电子"]

    # 应用锚点
    results = apply_anchors(baseline, anchors)

    # 归一化
    results = normalize(results)

    # 计算金额
    output = {
        "product": {
            "price": price,
            "category": category,
            "brand_note": brand_note,
        },
        "breakdown": [],
        "summary": {
            "total_pct": 0.0,
            "hard_data_points": 0,
            "estimated_points": 0,
            "overall_confidence": 0,
        },
    }

    total_amount = 0.0
    total_pct = 0.0
    confidences = []

    for dim_name in dimensions:
        if dim_name not in results:
            continue

        r = results[dim_name]
        mid_pct = r["mid_pct"]
        amount = round(price * mid_pct, 2)

        total_amount += amount
        total_pct += mid_pct
        confidences.append(r["confidence"])

        entry = {
            "dimension": dim_name,
            "amount": amount,
            "pct": round(mid_pct * 100, 1),
            "min_pct": round(r["min_pct"] * 100, 1),
            "max_pct": round(r["max_pct"] * 100, 1),
            "confidence": r["confidence"],
            "source": r["source"],
        }
        output["breakdown"].append(entry)

        if r["confidence"] >= 4:
            output["summary"]["hard_data_points"] += 1
        else:
            output["summary"]["estimated_points"] += 1

    # 调整最后一项使金额总和 = price（处理舍入误差）
    if output["breakdown"] and total_amount != price:
        diff = round(price - total_amount, 2)
        output["breakdown"][-1]["amount"] = round(output["breakdown"][-1]["amount"] + diff, 2)

    output["summary"]["total_pct"] = round(total_pct * 100, 1)
    output["summary"]["overall_confidence"] = round(sum(confidences) / len(confidences), 1) if confidences else 2.0
    output["summary"]["deviation_note"] = _deviation_note(total_pct)

    return output


def _deviation_note(total_pct: float) -> str:
    """生成百分比偏离说明"""
    if total_pct < 0.90:
        return f"各项成本占比合计仅 {round(total_pct * 100, 1)}%，低于 100%。可能存在未拆解出的其他成本项，或部分成本被低估。"
    elif total_pct > 1.10:
        return f"各项成本占比合计 {round(total_pct * 100, 1)}%，超出 100%。部分成本项可能被高估，或存在重叠计算。"
    else:
        return ""


def main():
    """从 stdin 读取 JSON 输入，输出 JSON 结果"""
    try:
        raw_bytes = sys.stdin.buffer.read()
        raw = None
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "gbk"):
            try:
                raw = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if raw is None:
            raw = raw_bytes.decode("utf-8", errors="replace")
        if not raw.strip():
            print(json.dumps({"error": "无输入数据"}, ensure_ascii=False))
            sys.exit(1)

        data = json.loads(raw)
        price = float(data.get("price", 0))
        category = data.get("category", "消费电子")
        anchors = data.get("anchors", {})
        brand_note = data.get("brand_note")

        if price <= 0:
            print(json.dumps({"error": "价格必须大于 0"}, ensure_ascii=False))
            sys.exit(1)

        result = calculate(price, category, anchors, brand_note)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON 解析错误: {e}"}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
