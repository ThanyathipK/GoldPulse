"""Small, deterministic accessibility regression checks for the portfolio UI."""
from pathlib import Path
import re
import tomllib

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from goldpulse.charts import price_figure


ROOT = Path(__file__).resolve().parents[1]


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_text_and_primary_colors_meet_wcag_aa_on_their_surfaces():
    with (ROOT / ".streamlit/config.toml").open("rb") as config_file:
        theme = tomllib.load(config_file)["theme"]

    assert _contrast(theme["textColor"], theme["backgroundColor"]) >= 4.5
    assert _contrast(theme["textColor"], theme["secondaryBackgroundColor"]) >= 4.5
    assert _contrast(theme["primaryColor"], theme["secondaryBackgroundColor"]) >= 4.5


def test_direction_palette_meets_contrast_and_is_not_the_only_cue():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    direction_map = re.search(
        r'color_discrete_map=\{"Increase": "(#[0-9A-Fa-f]{6})", "Decrease": "(#[0-9A-Fa-f]{6})"\}',
        source,
    )
    assert direction_map, "Movement bars must retain explicit direction labels."
    assert all(_contrast(color, "#FFFFFF") >= 4.5 for color in direction_map.groups())
    assert 'hovertemplate=("Month: %{x}<br>Change: ฿%{y:+,.0f}' in source


def test_price_chart_exposes_context_units_and_non_color_extrema_labels():
    # The application registers this shared template before rendering charts.
    pio.templates["goldpulse"] = go.layout.Template()
    data = pd.DataFrame(
        {
            "announcement_date": pd.to_datetime(["2026-01-01", "2026-02-01"]),
            "value": [50_000.0, 51_000.0],
        }
    )
    figure, _ = price_figure(
        data,
        "Gold bar · Selling",
        "Jan–Feb 2026",
        monthly_resolution=True,
        comparison="Starting price",
    )

    assert "Gold bar · Selling" in figure.layout.title.text
    assert figure.layout.yaxis.title.text == "THB per baht-weight"
    assert {trace.name for trace in figure.data} >= {"Period high", "Period low"}
    assert "Month-to-month change" in figure.data[0].hovertemplate
    extrema_text = {text for trace in figure.data[1:] for text in (trace.text or ())}
    assert extrema_text >= {"High", "Low"}


def test_calculators_keep_visible_labels_formulas_and_empty_default_results():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'st.number_input("Budget per purchase (THB)"' in source
    assert 'st.number_input("Your purchase price (THB/baht-weight)"' in source
    assert "Formula: accumulated weight =" in source
    assert "Formula: (comparison price − purchase price) × weight." in source
    assert "No result is assumed by default." in source
