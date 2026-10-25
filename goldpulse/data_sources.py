"""Adapters for reproducibly building GoldPulse source datasets."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

from goldpulse.validation import ValidationReport, validate_official_monthly


OUTPUT_FIELDS = (
    "month", "bar_buy", "bar_sell", "ornament_buy", "ornament_sell",
    "gold_spot_usd_oz", "usd_thb", "source_url", "accessed_at", "data_status",
)
VALUE_FIELDS = OUTPUT_FIELDS[1:7]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_path(path: Path) -> str:
    """Prefer a repository-relative path in committed provenance metadata."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def build_official_monthly_dataset(
    snapshot_path: Path, output_path: Path, provenance_path: Path
) -> ValidationReport:
    """Transform a checked-in source snapshot into the canonical monthly CSV."""
    with snapshot_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError("Raw snapshot contains no observations")

    canonical: list[dict[str, str]] = []
    for row in rows:
        canonical.append({
            "month": pd.Period(row["month"], freq="M").start_time.strftime("%Y-%m-%d"),
            **{field: row[field] for field in VALUE_FIELDS},
            "source_url": row["source_url"],
            "accessed_at": row["accessed_at"],
            "data_status": "official_monthly_average",
        })

    frame = pd.DataFrame(canonical, columns=OUTPUT_FIELDS)
    report = validate_official_monthly(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, lineterminator="\n")

    provenance = {
        "dataset": "Thai gold official monthly averages",
        "resolution": "monthly_average",
        "source_url": canonical[0]["source_url"],
        "accessed_at": canonical[0]["accessed_at"],
        "raw_snapshot": _portable_path(snapshot_path),
        "raw_snapshot_sha256": _sha256(snapshot_path),
        "output": _portable_path(output_path),
        "input_row_count": len(rows),
        "output_row_count": report.row_count,
        "first_month": report.first_month,
        "last_month": report.last_month,
        "transformations": [
            "normalized month labels to first-of-month ISO dates",
            "preserved published monthly-average values without interpolation",
            "assigned official_monthly_average data status",
        ],
    }
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return report
