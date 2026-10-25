import json
from pathlib import Path

import pandas as pd
import pytest

from goldpulse.data_sources import build_official_monthly_dataset
from goldpulse.validation import validate_official_monthly


def test_checked_in_snapshot_rebuilds_existing_values(tmp_path: Path):
    output = tmp_path / "official.csv"
    provenance = tmp_path / "provenance.json"
    report = build_official_monthly_dataset(
        Path("data/raw/gta_monthly_averages_2026.csv"), output, provenance
    )
    expected = pd.read_csv("data/official_2026_monthly.csv", dtype=str)
    actual = pd.read_csv(output, dtype=str)
    pd.testing.assert_frame_equal(actual, expected)
    assert report.row_count == 9
    metadata = json.loads(provenance.read_text())
    assert metadata["input_row_count"] == metadata["output_row_count"] == 9
    assert len(metadata["raw_snapshot_sha256"]) == 64
    assert metadata["resolution"] == "monthly_average"


def test_validation_rejects_duplicate_month():
    frame = pd.read_csv("data/official_2026_monthly.csv")
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="one observation per month"):
        validate_official_monthly(duplicated)


def test_validation_rejects_non_month_start():
    frame = pd.read_csv("data/official_2026_monthly.csv")
    frame.loc[0, "month"] = "2026-01-15"
    with pytest.raises(ValueError, match="first calendar day"):
        validate_official_monthly(frame)
