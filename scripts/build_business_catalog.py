#!/usr/bin/env python3
"""Build a PII-free AutoCare product and service catalogue from the sales report."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT.parent / "downloads" / "Anonymized_Product_Sell_Report.csv"
OUTPUT = PROJECT_ROOT / "data" / "lino_business_catalog.json"

TYRE_RE = re.compile(
    r"^\s*(?P<width>\d{3})\s*(?:"
    r"/\s*(?P<aspect>\d{2,3})\s*/\s*(?P<rim>\d{2})(?P<commercial>[Cc])?"
    r"|/\s*(?P<commercial_rim>\d{2})(?P<slash_c>[Cc])"
    r"|[Rr]\s*(?P<radial_rim>\d{2})(?P<radial_c>[Cc])?"
    r")"
)
VISCOSITY_RE = re.compile(r"\b(0|5|10|15|20|25)\s*[Ww-]\s*-?\s*(16|20|30|40|50)\b")
VOLUME_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*[Ll]\b")
OIL_KEYWORDS_RE = re.compile(
    r"\b(engine oil|motor oil|helix|magnatec|castro|castrol|mobil 1|mobil super|"
    r"mobil 2000|mobil 3000|morris|motorcraft|total quartz|toyota oil)\b",
    re.I,
)


def money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def normalise_tyre_size(product: str) -> tuple[str, str] | tuple[None, None]:
    match = TYRE_RE.search(product)
    if not match:
        return None, None
    width = match.group("width")
    aspect = match.group("aspect")
    rim = match.group("rim")
    commercial = match.group("commercial")
    if aspect:
        normalized = f"{width}/{aspect}R{rim}{'C' if commercial else ''}"
        raw = f"{width}/{aspect}/{rim}{commercial.upper() if commercial else ''}"
    else:
        rim = match.group("commercial_rim") or match.group("radial_rim")
        is_commercial = bool(match.group("slash_c") or match.group("radial_c"))
        normalized = f"{width}R{rim}{'C' if is_commercial else ''}"
        raw = match.group(0).strip()
    return raw, normalized


def tyre_brand(product: str) -> str | None:
    remainder = TYRE_RE.sub("", product, count=1).strip(" -–")
    return remainder.strip() or None


def viscosity(product: str) -> str | None:
    match = VISCOSITY_RE.search(product)
    return f"{match.group(1)}W-{match.group(2)}" if match else None


def volume_litres(product: str) -> float | None:
    match = VOLUME_RE.search(product)
    return float(match.group(1)) if match else None


def oil_brand(product: str) -> str:
    lower = product.lower()
    if lower.startswith("castro") or lower.startswith("castrol"):
        return "Castrol"
    if lower.startswith("mobil"):
        return "Mobil"
    if lower.startswith("shell"):
        return "Shell"
    if lower.startswith("toyota"):
        return "Toyota"
    if lower.startswith("morris"):
        return "Morris"
    if lower.startswith("motorcraft"):
        return "Motorcraft"
    if lower.startswith("total"):
        return "Total"
    return product.split()[0]


def aggregate_products(rows: pd.DataFrame, kind: str) -> list[dict]:
    records: list[dict] = []
    for product, group in rows.groupby("Product", sort=True):
        group = group.sort_values("_date")
        valid = group[group["_unit_price"].gt(0)]
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        prices = valid["_unit_price"]
        item = {
            "product_name": product,
            "latest_recorded_unit_price_ngn": round(float(latest["_unit_price"]), 2),
            "latest_recorded_date": latest["_date"].date().isoformat(),
            "historical_min_unit_price_ngn": round(float(prices.min()), 2),
            "historical_max_unit_price_ngn": round(float(prices.max()), 2),
            "historical_transaction_count": int(len(valid)),
            "price_status": "historical_unconfirmed",
        }
        if kind == "tyre":
            raw, normalized = normalise_tyre_size(product)
            item.update(
                {
                    "size_as_recorded": raw,
                    "size_normalized": normalized,
                    "brand_or_description": tyre_brand(product),
                }
            )
        else:
            item.update(
                {
                    "brand": oil_brand(product),
                    "viscosity": viscosity(product),
                    "pack_size_litres": volume_litres(product),
                    "partial_pack_marker": "1/2" in product,
                }
            )
        records.append(item)
    return records


def main() -> None:
    df = pd.read_csv(SOURCE)
    required = {"Product", "Date", "Unit Price"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    working = df[["Product", "Date", "Unit Price"]].copy()
    working["Product"] = working["Product"].astype(str).str.strip()
    working["_date"] = pd.to_datetime(working["Date"], errors="coerce")
    working["_unit_price"] = money(working["Unit Price"])
    working = working.dropna(subset=["_date", "_unit_price"])

    tyre_mask = working["Product"].str.match(TYRE_RE)
    oil_mask = working["Product"].str.contains(VISCOSITY_RE, regex=True) | working["Product"].str.contains(
        OIL_KEYWORDS_RE, regex=True
    )
    tyres = aggregate_products(working[tyre_mask], "tyre")
    oils = aggregate_products(working[oil_mask & ~tyre_mask], "oil")
    unique_sizes = sorted({x["size_normalized"] for x in tyres if x["size_normalized"]})

    payload = {
        "metadata": {
            "catalog_name": "Lino AutoCare Copilot business catalogue",
            "generated_on": date(2026, 8, 10).isoformat(),
            "currency": "NGN",
            "source_document": "Anonymized historical product sales report",
            "privacy": "Customer names, contact details, invoice numbers and payment methods are excluded.",
            "pricing_rule": (
                "Only diagnostics is currently confirmed. Tyre and engine-oil prices are historical sales "
                "references and must be confirmed before quoting a customer."
            ),
        },
        "confirmed_services": [
            {
                "service": "Vehicle diagnostics",
                "current_price_ngn": 20000,
                "price_type": "fixed",
                "status": "user_confirmed_current",
                "confirmed_on": date(2026, 8, 10).isoformat(),
            }
        ],
        "tyre_catalog": {
            "unique_size_count": len(unique_sizes),
            "unique_product_count": len(tyres),
            "sizes": unique_sizes,
            "products": tyres,
        },
        "engine_oil_catalog": {
            "unique_product_count": len(oils),
            "products": oils,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    forbidden = [
        "Customer name",
        "Contact ID",
        "Contact Number",
        "Invoice No.",
        "Payment Method",
    ]
    rendered = OUTPUT.read_text(encoding="utf-8")
    found = [field for field in forbidden if f'"{field}"' in rendered]
    if found:
        raise ValueError(f"Sensitive source fields leaked into output: {found}")

    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "tyre_products": len(tyres),
                "tyre_sizes": len(unique_sizes),
                "engine_oil_products": len(oils),
                "confirmed_diagnostics_price_ngn": 20000,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
