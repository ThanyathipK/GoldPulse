#!/usr/bin/env python3
"""Build and validate the official monthly dataset from its raw snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from goldpulse.data_sources import build_official_monthly_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=PROJECT_ROOT / "data/raw/gta_monthly_averages_2026.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data/official_2026_monthly.csv")
    parser.add_argument("--provenance", type=Path, default=PROJECT_ROOT / "data/official_2026_monthly.provenance.json")
    args = parser.parse_args()
    report = build_official_monthly_dataset(args.snapshot, args.output, args.provenance)
    print(f"Built {report.row_count} monthly observations ({report.first_month} to {report.last_month})")
    print(f"Dataset: {args.output}")
    print(f"Provenance: {args.provenance}")


if __name__ == "__main__":
    main()
