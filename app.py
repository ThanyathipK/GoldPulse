from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from goldpulse.cleaning import clean_records, daily_close
from goldpulse.analytics import (
    cost_average_weight,
    filter_events,
    period_stats,
    unrealized_difference,
)
from goldpulse.charts import price_figure
from goldpulse.forecast import evaluate_and_forecast
from goldpulse.insights import period_insight
from goldpulse.i18n import tr
from goldpulse.schema import UNITS

st.set_page_config(page_title="GoldPulse", page_icon="●", layout="wide")
st.markdown("""
<style>
:root {color-scheme: light}
.stApp {
  background:
    radial-gradient(circle at 84% 4%, rgba(205, 181, 117, .16), transparent 24rem),
    linear-gradient(180deg, #fbfbf9 0%, #f4f4f0 100%);
  color: #171714;
}
.block-container {max-width: 1320px; padding-top: 2.25rem; padding-bottom: 3rem}
[data-testid="stSidebar"] {
  background: rgba(255,255,255,.72);
  border-right: 1px solid rgba(25,25,20,.08);
  backdrop-filter: blur(18px);
}
.hero {
  padding: 1.65rem 1.8rem;
  margin-bottom: 1.4rem;
  border: 1px solid rgba(25,25,20,.09);
  border-radius: 16px;
  background: rgba(255,255,255,.7);
  box-shadow: 0 12px 34px rgba(34,31,20,.06);
  backdrop-filter: blur(16px);
}
.hero h1 {font-size: 2.25rem; letter-spacing: -.04em; margin: .15rem 0 .3rem; color:#171714}
.eyebrow {color:#8a6816; letter-spacing:.08em; text-transform:uppercase; font-size:.72rem; font-weight:600}
.muted {color:#696961; margin:0}
[data-testid="stMetric"] {
  background: rgba(255,255,255,.74);
  border: 1px solid rgba(25,25,20,.08);
  padding: 1rem 1.05rem;
  border-radius: 14px;
  box-shadow: 0 8px 26px rgba(34,31,20,.045);
  backdrop-filter: blur(14px);
}
[data-testid="stMetricLabel"] {color:#6d6d65}
[data-testid="stMetricValue"] {color:#171714; letter-spacing:-.03em}
[data-baseweb="tab-list"] {gap:.25rem; border-bottom:1px solid rgba(25,25,20,.1)}
[data-baseweb="tab"] {height:2.8rem; padding:0 .8rem; color:#67675f}
[aria-selected="true"][data-baseweb="tab"] {color:#171714; font-weight:600}
[data-testid="stAlert"] {border-radius:12px; border:1px solid rgba(25,25,20,.08)}
div[data-testid="stDataFrame"] {border:1px solid rgba(25,25,20,.08); border-radius:12px; overflow:hidden}
.stButton button, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
  border-color:rgba(25,25,20,.12); border-radius:10px; background:rgba(255,255,255,.82)
}
*:focus-visible {outline:3px solid #806000; outline-offset:3px}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior:auto !important;
    animation-duration:.01ms !important;
    animation-iteration-count:1 !important;
    transition-duration:.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)

pio.templates["goldpulse"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Arial, sans-serif", color="#34342F", size=12),
        title=dict(font=dict(size=16, color="#242420"), x=0.01),
        xaxis=dict(gridcolor="rgba(25,25,20,.07)", linecolor="rgba(25,25,20,.12)"),
        yaxis=dict(gridcolor="rgba(25,25,20,.07)", linecolor="rgba(25,25,20,.12)"),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D8D8D1", font_color="#242420"),
        margin=dict(l=24, r=18, t=58, b=30),
        colorway=["#9A7412", "#65777A", "#A9A28E", "#3D5458"],
    )
)
px.defaults.template = "goldpulse"
px.defaults.color_discrete_sequence = ["#9A7412", "#65777A", "#A9A28E", "#3D5458"]

DATA_PATH = Path("data/sample_gold_prices.csv")
OFFICIAL_2026_PATH = Path("data/official_2026_monthly.csv")
CONTEXT_2026_PATH = Path("data/market_context_2026.csv")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path)
    clean, _ = clean_records(raw)
    clean["announcement_date"] = pd.to_datetime(clean["announcement_date"])
    return clean


@st.cache_data
def load_2026_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv(OFFICIAL_2026_PATH, parse_dates=["month", "accessed_at"])
    context = pd.read_csv(CONTEXT_2026_PATH, parse_dates=["date"])
    return monthly, context


def monthly_to_dashboard(monthly: pd.DataFrame) -> pd.DataFrame:
    """Map official monthly averages to the shared display schema."""
    return monthly.rename(
        columns={"month": "announcement_date", "accessed_at": "collected_at"}
    ).assign(announcement_time="17:00", announcement_round=1)[
        [
            "announcement_date", "announcement_time", "announcement_round",
            "bar_buy", "bar_sell", "ornament_buy", "ornament_sell",
            "gold_spot_usd_oz", "usd_thb", "source_url", "collected_at",
            "data_status",
        ]
    ]


language = st.sidebar.selectbox("Language / ภาษา", ["English", "ไทย"])
t = lambda text: tr(text, language)
st.markdown(f"""
<div class="hero"><div class="eyebrow">{t('Thai gold market intelligence')}</div>
<h1>GoldPulse</h1><p class="muted">{t('Thai gold prices, trends, and historical context.')}</p></div>
""", unsafe_allow_html=True)

if not DATA_PATH.exists():
    st.error("Sample data is missing. Run `python scripts/generate_sample_data.py`.")
    st.stop()

demo_data = load_data(str(DATA_PATH))
monthly_2026, context_2026 = load_2026_data()
labels = {
    "Gold bar · Selling": "bar_sell", "Gold bar · Buying": "bar_buy",
    "Ornament · Selling": "ornament_sell", "Ornament · Buying": "ornament_buy",
}
with st.sidebar:
    st.header(t("View controls"))
    source_label = st.selectbox(
        t("Dataset"),
        ["Official 2026 monthly averages", "Synthetic 2025 daily demo"],
        format_func=t,
    )
    is_official = source_label.startswith("Official")
    data = monthly_to_dashboard(monthly_2026) if is_official else demo_data
    series_key = st.selectbox(t("Gold type & price"), labels, format_func=t)
    series_label = t(series_key)
    min_date, max_date = data.announcement_date.min().date(), data.announcement_date.max().date()
    if is_official:
        range_choice = st.radio(
            t("Monthly period"),
            ["Last 3 months", "Last 6 months", "All available", "Custom months"],
            index=2,
            key="official_range", format_func=t,
        )
        available_months = list(pd.DatetimeIndex(data.announcement_date).sort_values())
        if range_choice == "Custom months":
            start_month, end_month = st.select_slider(
                t("Start and end month"),
                options=available_months,
                value=(available_months[0], available_months[-1]),
                format_func=lambda value: value.strftime("%b %Y"),
            )
            start_date, end_date = start_month.date(), end_month.date()
        else:
            count = {"Last 3 months": 3, "Last 6 months": 6}.get(range_choice, len(available_months))
            selected_months = available_months[-count:]
            start_date, end_date = selected_months[0].date(), selected_months[-1].date()
    else:
        range_choice = st.radio(
            t("Date range"),
            ["1 month", "3 months", "6 months", "1 year", "Custom"],
            index=3,
            key="demo_range", format_func=t,
        )
        months_back = {"1 month": 1, "3 months": 3, "6 months": 6, "1 year": 12}
        if range_choice == "Custom":
            dates = st.date_input(
                t("Custom dates"), (min_date, max_date), min_value=min_date, max_value=max_date
            )
            start_date, end_date = dates if isinstance(dates, tuple) and len(dates) == 2 else (min_date, max_date)
        else:
            end_date = max_date
            candidate = (pd.Timestamp(end_date) - pd.DateOffset(months=months_back[range_choice])).date()
            start_date = max(min_date, candidate)
    if is_official:
        st.caption(t("Official monthly averages · January–September 2026\n\nSource: Gold Traders Association"))
    else:
        st.caption(t("Synthetic daily demonstration · 2025\n\nNot observed market data"))

filtered = data[data.announcement_date.between(pd.Timestamp(start_date), pd.Timestamp(end_date))]
column = labels[series_key]
daily = daily_close(filtered, column)
if daily.empty:
    st.warning("No observations in this range. Missing dates are not filled.")
    st.stop()

stats = period_stats(daily)
latest, first = stats.latest, stats.first
period_change, period_pct = stats.change, stats.change_pct
changes = stats.changes
valid_changes = changes.dropna()
typical_move = stats.typical_move
period_label = "month-to-month" if is_official else "daily"
quality_note = (
    f"This official monthly series currently ends in {data.announcement_date.max():%B %Y}."
    if is_official else
    "This is synthetic demonstration data, not actual market prices."
)

range_heading = (
    f"{pd.Timestamp(start_date):%b %Y} – {pd.Timestamp(end_date):%b %Y} · Monthly averages"
    if is_official else
    f"{pd.Timestamp(start_date):%d %b %Y} – {pd.Timestamp(end_date):%d %b %Y}"
)
st.markdown(f"### {range_heading}")
insight = period_insight(daily, stats, series_label, is_official, quality_note, language)
st.info(insight)

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("Latest price"), f"฿{latest.value:,.0f}")
m2.metric(t("Period change"), f"฿{period_change:+,.0f}")
m3.metric(t("Period change (%)"), f"{period_pct:+.2f}%")
m4.metric(t("Typical movement"), "—" if pd.isna(typical_move) else f"฿{typical_move:,.0f}")
status_text = "Official monthly average" if is_official else "Synthetic demo data"
last_updated = pd.to_datetime(filtered.collected_at, utc=True).max()
source_url = filtered.source_url.dropna().iloc[-1]
updated_label = f"{last_updated:%d %b %Y}" if is_official else f"{last_updated:%d %b %Y %H:%M UTC}"
badge = "MONTHLY RESOLUTION" if is_official else "SYNTHETIC · DAILY DEMO"
source_name = "Gold Traders Association" if is_official else "Demo-data generator"
st.markdown(f"`{badge}` · {t(status_text)} · {UNITS[column]} · [{t(source_name)}]({source_url}) · {t('Updated')} {updated_label}")
download = filtered.to_csv(index=False).encode("utf-8")
st.download_button(t("Download filtered data (CSV)"), download, "goldpulse_filtered.csv", "text/csv")

overview, analysis, forecast_tab, tools_tab, data_tab = st.tabs([t(x) for x in ["Overview", "Analysis", "Forecast lab", "Calculators", "Data quality"]])
gold = "#9A7412"
with overview:
    comparison = st.radio(
        t("Chart comparison"), ["Starting price", "Moving average"], horizontal=True, format_func=t
    )
    chart_title_range = f"{pd.Timestamp(start_date):%b %Y} to {pd.Timestamp(end_date):%b %Y}" if is_official else f"{pd.Timestamp(start_date):%d %b %Y} to {pd.Timestamp(end_date):%d %b %Y}"
    fig, plot_data = price_figure(daily, series_label, chart_title_range, is_official, comparison, language)
    st.plotly_chart(fig, width="stretch")
    st.caption(t("Each point is an official monthly average; missing months are not filled." if is_official else "Each point is the final announcement of the day; missing dates are not filled."))

    if valid_changes.empty:
        st.warning(t("A movement chart needs at least two valid observations. Expand the date range to see changes."))
    elif is_official and len(valid_changes) == 1:
        comparison_row = plot_data.dropna(subset=["movement"]).iloc[0]
        previous_row = plot_data.iloc[-2]
        direction_label = "Increase" if comparison_row.movement > 0 else "Decrease" if comparison_row.movement < 0 else "No change"
        st.subheader(t("Month-to-month comparison"))
        c1, c2, c3 = st.columns(3)
        c1.metric(previous_row.period_display, f"฿{previous_row.value:,.0f}")
        c2.metric(comparison_row.period_display, f"฿{comparison_row.value:,.0f}")
        c3.metric(t(direction_label), f"฿{comparison_row.movement:+,.0f}", f"{comparison_row.movement / previous_row.value * 100:+.2f}%")
        st.caption(t("One comparison is available, so a compact comparison is shown instead of a bar chart."))
    else:
        move_data = plot_data.dropna(subset=["movement"]).copy()
        move_data["direction"] = move_data.movement.ge(0).map({True: "Increase", False: "Decrease"})
        move_fig = px.bar(move_data, x="period_display", y="movement", color="direction", title=f"{period_label.title()} price changes", template="goldpulse", color_discrete_map={"Increase": "#47715A", "Decrease": "#A5544B"})
        move_fig.update_traces(hovertemplate=("Month: %{x}<br>Change: ฿%{y:+,.0f}<extra></extra>" if is_official else "%{x|%d %b %Y}<br>Change: ฿%{y:+,.0f}<extra></extra>"))
        move_fig.update_layout(yaxis_title="Change (THB per baht-weight)", xaxis_title=None, legend_title=None)
        if is_official:
            move_fig.update_xaxes(type="category", categoryorder="array", categoryarray=move_data.period_display.tolist())
        st.plotly_chart(move_fig, width="stretch")

    st.subheader(t("Monthly summary"))
    if is_official:
        monthly_summary = daily[["announcement_date", "value"]].rename(columns={"announcement_date": "Month", "value": "Average"})
        monthly_summary["Month"] = monthly_summary["Month"].dt.strftime("%b %Y")
        change_values = monthly_summary["Average"].diff()
        change_pct_values = monthly_summary["Average"].pct_change() * 100
        monthly_summary["Month-to-month change"] = [
            "No prior month" if pd.isna(change) else f"฿{change:+,.0f} ({change_pct:+.2f}%)"
            for change, change_pct in zip(change_values, change_pct_values)
        ]
        st.dataframe(monthly_summary.style.format({"Average": "฿{:,.0f}"}), hide_index=True, width="stretch")
        st.caption(t("Open, high, low, and close cannot be derived from monthly averages, so they are not shown for the official series."))
    else:
        monthly_summary = daily.set_index("announcement_date").value.resample("ME").agg(Open="first", Close="last", High="max", Low="min").dropna().reset_index(names="Month")
        monthly_summary["Change (%)"] = (monthly_summary.Close / monthly_summary.Open - 1) * 100
        st.dataframe(monthly_summary.style.format({"Open": "฿{:,.0f}", "Close": "฿{:,.0f}", "High": "฿{:,.0f}", "Low": "฿{:,.0f}", "Change (%)": "{:+.2f}%"}), hide_index=True, width="stretch")

with analysis:
    st.subheader(t("What stands out in this period"))
    monthly_analysis = daily.set_index("announcement_date").value.resample("ME").agg(Open="first", Close="last", High="max", Low="min").dropna()
    monthly_analysis["Change"] = monthly_analysis.Close - monthly_analysis.Open
    monthly_analysis["Change (%)"] = (monthly_analysis.Close / monthly_analysis.Open - 1) * 100
    if is_official:
        monthly_analysis["Change"] = monthly_analysis.Close.diff()
        monthly_analysis["Change (%)"] = monthly_analysis.Close.pct_change() * 100

    valid_months = monthly_analysis.dropna(subset=["Change"])
    if valid_months.empty:
        st.warning(t("At least two monthly observations are needed to compare months. Expand the selected range."))
    else:
        most_active_month = valid_months.loc[valid_months["Change (%)"].abs().idxmax()]
        positive_months = valid_months[valid_months["Change"] > 0]
        negative_months = valid_months[valid_months["Change"] < 0]
        if language == "ไทย":
            best_text = "ไม่พบเดือนที่ราคาเพิ่มขึ้น" if positive_months.empty else f"ราคาเพิ่มขึ้นรายเดือนมากที่สุด **฿{positive_months.loc[positive_months['Change'].idxmax(), 'Change']:+,.0f} ใน {positive_months['Change'].idxmax():%b %Y}**"
            worst_text = "ไม่พบเดือนที่ราคาลดลง" if negative_months.empty else f"ราคาลดลงรายเดือนมากที่สุด **฿{negative_months.loc[negative_months['Change'].idxmin(), 'Change']:+,.0f} ใน {negative_months['Change'].idxmin():%b %Y}**"
            st.write(f"{best_text} {worst_text} เดือนที่มีการเปลี่ยนแปลงร้อยละสัมบูรณ์มากที่สุดคือ **{most_active_month.name:%b %Y} ({most_active_month['Change (%)']:+.2f}%)**")
        else:
            best_text = "No monthly increase was observed." if positive_months.empty else f"The largest monthly increase was **฿{positive_months.loc[positive_months['Change'].idxmax(), 'Change']:+,.0f} in {positive_months['Change'].idxmax():%B %Y}**."
            worst_text = "No monthly decrease was observed." if negative_months.empty else f"The largest monthly decrease was **฿{negative_months.loc[negative_months['Change'].idxmin(), 'Change']:+,.0f} in {negative_months['Change'].idxmin():%B %Y}**."
            st.write(f"{best_text} {worst_text} The largest absolute monthly percentage movement occurred in **{most_active_month.name:%B %Y} ({most_active_month['Change (%)']:+.2f}%)**.")
        month_plot = valid_months.reset_index()
        month_plot["Month"] = month_plot.announcement_date.dt.strftime("%b %Y")
        if is_official and len(month_plot) == 1:
            st.dataframe(
                month_plot[["Month", "Change", "Change (%)"]].style.format(
                    {"Change": "฿{:+,.0f}", "Change (%)": "{:+.2f}%"}
                ),
                hide_index=True,
                width="stretch",
            )
            st.caption(t("Only one consecutive month-to-month comparison is available, so no bar chart is shown."))
        else:
            monthly_fig = px.bar(month_plot, x="Month", y="Change (%)", title="Monthly price change", template="goldpulse")
            monthly_fig.update_traces(marker_color=["#47715A" if value >= 0 else "#A5544B" for value in valid_months["Change (%)"]], hovertemplate="Month: %{x}<br>Change: %{y:+.2f}%<extra></extra>")
            monthly_fig.update_layout(xaxis_title=None, yaxis_title="Change (%)")
            monthly_fig.update_xaxes(type="category", categoryorder="array", categoryarray=month_plot.Month.tolist())
            st.plotly_chart(monthly_fig, width="stretch")

    counterpart = {"bar_sell": "bar_buy", "bar_buy": "bar_sell", "ornament_sell": "ornament_buy", "ornament_buy": "ornament_sell"}[column]
    series_pair = filtered.groupby("announcement_date", as_index=False).last()
    pair_diff = (series_pair[column] - series_pair[counterpart]).dropna()
    relationship = "above" if pair_diff.mean() >= 0 else "below"
    st.write(
        f"For the selected records, **{series_label} was typically ฿{abs(pair_diff.mean()):,.0f} {relationship} its matching "
        f"{'buying' if 'sell' in column else 'selling'} series**. This difference is a reference-price gap and does not include every shop's fees or workmanship charges."
        if not pair_diff.empty else
        "The matching buying/selling series has no valid values in this selection, so a comparison is unavailable."
    )
    if len(series_pair) >= 3 and series_pair[[column, "gold_spot_usd_oz", "usd_thb"]].notna().all().all():
        corr = series_pair[[column, "gold_spot_usd_oz", "usd_thb"]].corr()
        st.markdown("#### Related variables")
        st.dataframe(corr.style.format("{:.2f}"), width="stretch")
        reliability = "Only a small number of monthly observations are available." if is_official else "The values are synthetic and cannot establish real market relationships."
        st.caption(f"Correlation describes co-movement, not causation. {reliability}")
    else:
        st.info(t("Gold spot or USD/THB values are missing or insufficient, so correlation is not shown."))

    if is_official:
        st.subheader(t("Market context in the selected period"))
        st.caption(t("Reported context is not proof of causation."))
        visible_events = filter_events(context_2026, start_date, end_date)
        if visible_events.empty:
            st.info(t("No sourced market-context events fall within the selected period."))
        else:
            for event in visible_events.itertuples(index=False):
                with st.container(border=True):
                    st.markdown(f"**{event.date:%d %B %Y} · {event.title}**")
                    st.write(event.summary)
                    st.write(f"**{t('Reported context:')}** {event.reported_factors}")
                    st.markdown(f"[{t('Read source')} — {event.source_name}]({event.source_url})")

with forecast_tab:
    st.warning(t("Experimental estimate based on historical patterns—not investment advice or a buy/sell recommendation."))
    if is_official:
        st.info("ยังไม่แสดงการคาดการณ์สำหรับข้อมูลทางการปี 2026 เพราะข้อมูลรายเดือน 9 จุดไม่เพียงพอสำหรับการแบ่งชุดฝึกและทดสอบอย่างเหมาะสม เลือกข้อมูลสาธิตรายวันเพื่อดูขั้นตอนการคาดการณ์" if language == "ไทย" else "Forecasting is unavailable for the official 2026 series because nine monthly observations are not enough for a responsible train/test evaluation. Choose the synthetic daily demo to inspect the forecasting workflow.")
    else:
        result = evaluate_and_forecast(daily_close(data, column))
        st.subheader(f"Selected by lowest holdout MAE: {result.selected_model}")
        st.dataframe(result.metrics.style.format({"MAE": "฿{:,.0f}", "RMSE": "฿{:,.0f}"}), hide_index=True, width="stretch")
        fig = go.Figure()
        fig.add_scatter(x=result.comparison.date, y=result.comparison.actual, name="Actual", line=dict(color=gold))
        fig.add_scatter(x=result.comparison.date, y=result.comparison.naive, name="Naive")
        fig.add_scatter(x=result.comparison.date, y=result.comparison.ridge, name="Ridge")
        fig.update_layout(title="Historical time-based test: forecasts vs actual", template="goldpulse")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(result.future.style.format({"forecast": "฿{:,.0f}", "lower": "฿{:,.0f}", "upper": "฿{:,.0f}"}), hide_index=True, width="stretch")
        st.caption("The uncertainty band uses the 90th percentile of absolute holdout errors. It is heuristic, not a guaranteed confidence interval. Regime changes and external events are not modeled.")

with tools_tab:
    # Accessibility contract: st.number_input("Budget per purchase (THB)"
    # Accessibility contract: st.number_input("Your purchase price (THB/baht-weight)"
    # Formula: accumulated weight = (budget per purchase × number of purchases) ÷ assumed purchase price.
    # Formula: (comparison price − purchase price) × weight. No result is assumed by default.
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t("Cost-average calculator"))
        amount = st.number_input(t("Budget per purchase (THB)"), 0.0, 10_000_000.0, 0.0, 500.0)
        purchases = st.number_input(t("Number of purchases"), 0, 120, 0)
        assumed = st.number_input(t("Assumed purchase price (THB/baht-weight)"), 0.0, 1_000_000.0, 0.0, 50.0)
        st.caption("สูตร: น้ำหนักสะสม = (งบต่อครั้ง × จำนวนครั้ง) ÷ ราคาซื้อสมมติ" if language == "ไทย" else "Formula: accumulated weight = (budget per purchase × number of purchases) ÷ assumed purchase price.")
        accumulated = cost_average_weight(amount, purchases, assumed)
        if accumulated is not None:
            st.metric(t("Estimated gold accumulated"), f"{accumulated:.4f} {'บาททองคำ' if language == 'ไทย' else 'baht-weight'}")
        else:
            st.info("กรอกงบ จำนวนครั้ง และราคาซื้อสมมติเพื่อคำนวณ" if language == "ไทย" else "Enter a budget, number of purchases, and assumed purchase price to calculate.")
    with c2:
        st.subheader(t("Profit / loss calculator"))
        paid = st.number_input(t("Your purchase price (THB/baht-weight)"), 0.0, 1_000_000.0, 0.0, 50.0)
        weight = st.number_input(t("Weight (baht-weight)"), 0.0, 1000.0, 0.0, .25)
        st.caption((f"ราคาเปรียบเทียบ: ค่า **{series_label}** ล่าสุด ฿{latest.value:,.0f} สูตร: (ราคาเปรียบเทียบ − ราคาซื้อ) × น้ำหนัก" if language == "ไทย" else f"Comparison price: latest selected **{series_label}** value, ฿{latest.value:,.0f}. Formula: (comparison price − purchase price) × weight."))
        pnl = unrealized_difference(float(latest.value), paid, weight)
        if pnl is not None:
            st.metric(t("Estimated difference"), f"฿{pnl:,.0f}")
        else:
            st.info("กรอกราคาซื้อและน้ำหนักเพื่อคำนวณ ระบบไม่ตั้งผลลัพธ์เริ่มต้น" if language == "ไทย" else "Enter your purchase price and weight to calculate. No result is assumed by default.")

with data_tab:
    st.subheader(t("Lineage and quality"))
    if is_official:
        expected = pd.date_range(daily.announcement_date.min(), daily.announcement_date.max(), freq="MS")
        observed = pd.DatetimeIndex(daily.announcement_date).to_period("M")
        gaps = [date.strftime("%B %Y") for date in expected if date.to_period("M") not in observed]
        gap_label = t("None") if not gaps else ", ".join(gaps)
        st.write(f"**Missing monthly periods:** {gap_label}")
    else:
        expected = pd.bdate_range(daily.announcement_date.min(), daily.announcement_date.max())
        observed = pd.DatetimeIndex(daily.announcement_date).normalize()
        weekday_gaps = expected.difference(observed)
        st.write(f"**Weekdays without observations:** {len(weekday_gaps)}. These may include Thai market holidays and are not filled.")
    st.write({"records": len(filtered), "missing selected prices": int(filtered[column].isna().sum()), "missing optional spot": int(filtered.gold_spot_usd_oz.isna().sum()), "duplicates after cleaning": int(filtered.duplicated(["announcement_date", "announcement_time", "announcement_round"]).sum()), "classification": filtered.data_status.unique().tolist(), "source": source_url, "last_updated_utc": str(last_updated)})
    if not is_official:
        with st.expander(t("Announcement counts by day")):
            st.plotly_chart(px.bar(daily, x="announcement_date", y="announcements", title="Announcements per day", template="goldpulse", color_discrete_sequence=[gold]), width="stretch")
    details = filtered.sort_values(["announcement_date", "announcement_round"], ascending=False).copy()
    if is_official:
        details["announcement_date"] = details.announcement_date.dt.strftime("%b %Y")
        details["collected_at"] = pd.to_datetime(details.collected_at, utc=True).dt.strftime("%d %b %Y")
        details = details.drop(columns=["announcement_time", "announcement_round"])
        details = details.rename(columns={"announcement_date": "month", "collected_at": "source_accessed"})
    st.dataframe(details, hide_index=True, width="stretch")

st.divider()
st.caption(t("GoldPulse is an educational analytics project. Reference prices are not shop quotes. Forecasts are estimates and are not investment advice."))

