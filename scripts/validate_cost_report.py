#!/usr/bin/env python3
"""
Validate Cost-Xray cost_data.json and optional evidence ledger.

Usage:
    python validate_cost_report.py data/cost_data.json [evidence-ledger.md] [output.json]
"""

import json
import re
import sys
from pathlib import Path


def _read_text_flexible(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _load_json(path: Path) -> dict:
    return json.loads(_read_text_flexible(path))


def _status(fails: list, warns: list) -> str:
    if fails:
        return "FAIL"
    if warns:
        return "WARN"
    return "PASS"


def validate_cost_data(data: dict) -> tuple[list, list, dict]:
    fails = []
    warns = []

    product = data.get("product")
    if not isinstance(product, dict):
        fails.append("Missing product object.")
        product = {}

    price = product.get("price")
    try:
        price = float(price)
    except (TypeError, ValueError):
        price = 0.0

    if price <= 0:
        fails.append("Product price must be greater than 0.")

    if not product.get("category"):
        warns.append("Product category is missing.")

    breakdown = data.get("breakdown")
    if not isinstance(breakdown, list) or not breakdown:
        fails.append("Missing non-empty breakdown list.")
        breakdown = []

    total_amount = 0.0
    total_pct = 0.0
    low_confidence = 0
    source_missing = 0
    dimensions_seen = set()

    for idx, item in enumerate(breakdown, start=1):
        dim = item.get("dimension")
        if not dim:
            fails.append(f"Breakdown item {idx} missing dimension.")
        elif dim in dimensions_seen:
            warns.append(f"Duplicate dimension: {dim}.")
        else:
            dimensions_seen.add(dim)

        amount = item.get("amount")
        pct = item.get("pct")
        confidence = item.get("confidence")
        source = str(item.get("source", "")).strip()

        try:
            amount = float(amount)
            total_amount += amount
            if amount < 0:
                fails.append(f"{dim or 'item ' + str(idx)} has negative amount.")
        except (TypeError, ValueError):
            fails.append(f"{dim or 'item ' + str(idx)} has invalid amount.")

        try:
            pct = float(pct)
            total_pct += pct
            if pct < 0:
                fails.append(f"{dim or 'item ' + str(idx)} has negative percent.")
        except (TypeError, ValueError):
            fails.append(f"{dim or 'item ' + str(idx)} has invalid percent.")

        try:
            confidence = int(confidence)
            if confidence < 1 or confidence > 5:
                fails.append(f"{dim or 'item ' + str(idx)} confidence must be 1-5.")
            if confidence <= 2:
                low_confidence += 1
        except (TypeError, ValueError):
            fails.append(f"{dim or 'item ' + str(idx)} has invalid confidence.")

        if not source:
            source_missing += 1

    if price > 0 and breakdown:
        amount_delta = abs(total_amount - price)
        if amount_delta > max(1.0, price * 0.03):
            warns.append(
                f"Breakdown amount total {total_amount:.2f} differs from price {price:.2f} by more than 3%."
            )

    if breakdown and not (95 <= total_pct <= 105):
        deviation_note = data.get("summary", {}).get("deviation_note")
        msg = f"Breakdown percent total is {total_pct:.1f}%, outside 95%-105%."
        if deviation_note:
            warns.append(msg + " Deviation note exists.")
        else:
            fails.append(msg + " Add deviation_note or fix calculation.")

    if source_missing:
        fails.append(f"{source_missing} breakdown item(s) missing source labels.")

    if breakdown and low_confidence / len(breakdown) > 0.5:
        warns.append("More than half of breakdown items are confidence 1-2; disclose low evidence quality.")

    summary = {
        "price": price,
        "breakdown_items": len(breakdown),
        "total_amount": round(total_amount, 2),
        "total_pct": round(total_pct, 1),
        "low_confidence_items": low_confidence,
        "source_missing_items": source_missing,
    }
    return fails, warns, summary


def validate_ledger(path: Path | None, breakdown: list) -> tuple[list, list]:
    fails = []
    warns = []

    if path is None:
        warns.append("Evidence ledger not provided.")
        return fails, warns

    if not path.exists():
        fails.append(f"Evidence ledger not found: {path}")
        return fails, warns

    text = _read_text_flexible(path)
    if len(text.strip()) < 80:
        warns.append("Evidence ledger is very short.")

    has_table = "|" in text and "---" in text
    if not has_table:
        warns.append("Evidence ledger does not look like a Markdown table.")

    tier_hits = re.findall(r"\b[SABCD]\b|Tier\s*[SABCD]|[⭐★]{1,5}", text)
    if not tier_hits:
        warns.append("Evidence ledger has no visible tier/confidence labels.")

    for item in breakdown:
        dim = str(item.get("dimension", "")).strip()
        confidence = item.get("confidence", 0)
        try:
            confidence = int(confidence)
        except (TypeError, ValueError):
            confidence = 0
        if confidence >= 4 and dim and dim not in text:
            warns.append(f"High-confidence dimension not mentioned in ledger: {dim}.")

    return fails, warns


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate_cost_report.py data/cost_data.json [evidence-ledger.md] [output.json]", file=sys.stderr)
        return 2

    data_path = Path(sys.argv[1])
    ledger_path = Path(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].lower() != "none" else None
    output_path = Path(sys.argv[3]) if len(sys.argv) >= 4 else None

    try:
        data = _load_json(data_path)
    except Exception as exc:
        result = {"status": "FAIL", "fails": [f"Could not read JSON: {exc}"], "warns": [], "summary": {}}
    else:
        fails, warns, summary = validate_cost_data(data)
        ledger_fails, ledger_warns = validate_ledger(ledger_path, data.get("breakdown", []))
        fails.extend(ledger_fails)
        warns.extend(ledger_warns)
        result = {
            "status": _status(fails, warns),
            "fails": fails,
            "warns": warns,
            "summary": summary,
        }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
