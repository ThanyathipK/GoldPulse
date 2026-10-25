"""Plotly figure builders, independent of Streamlit UI state."""
import plotly.graph_objects as go
from goldpulse.i18n import tr


GOLD = "#9A7412"


def price_figure(data, label, title_range, monthly_resolution, comparison, language="English"):
    t = lambda text: tr(text, language)
    plot = data.copy()
    plot["movement"] = plot.value.diff()
    plot["movement_label"] = plot.movement.map(
        lambda value: f"฿{value:+,.0f}" if value == value else ("ไม่มีข้อมูลก่อนหน้า" if language == "ไทย" else "No prior observation"))
    plot["period_display"] = (plot.announcement_date.dt.strftime("%b %Y")
                              if monthly_resolution else plot.announcement_date)
    fig = go.Figure()
    fig.add_scatter(x=plot.period_display, y=plot.value, name=label,
                    line=dict(color=GOLD, width=2.5), mode="lines+markers",
                    customdata=plot[["movement_label"]],
                    hovertemplate=(("เดือน: %{x}<br>ราคาเฉลี่ยรายเดือน: ฿%{y:,.0f}<br>การเปลี่ยนแปลงเดือนต่อเดือน: %{customdata[0]}<extra></extra>" if language == "ไทย" else "Month: %{x}<br>Monthly average: ฿%{y:,.0f}<br>Month-to-month change: %{customdata[0]}<extra></extra>")
                                   if monthly_resolution else
                                   ("%{x|%d %b %Y}<br>ราคา: ฿%{y:,.0f}<br>การเปลี่ยนแปลงรายวัน: %{customdata[0]}<extra></extra>" if language == "ไทย" else "%{x|%d %b %Y}<br>Price: ฿%{y:,.0f}<br>Daily change: %{customdata[0]}<extra></extra>")))
    if comparison == "Starting price":
        fig.add_hline(y=plot.iloc[0].value, line_dash="dot", line_color="#8B8B84",
                      annotation_text=f"{'เริ่มต้น' if language == 'ไทย' else 'Start'} ฿{plot.iloc[0].value:,.0f}")
    else:
        window = 3 if monthly_resolution else 20
        average = plot.value.rolling(window, min_periods=max(2, window // 3)).mean()
        if average.notna().any():
            fig.add_scatter(x=plot.period_display, y=average, name=f"{('ค่าเฉลี่ย' if language == 'ไทย' else 'Average')} {window} {'ช่วง' if language == 'ไทย' else 'periods'}",
                            line=dict(color="#65777A", width=1.8))
    for name, row, color, position in (
        (("สูงสุดในช่วง" if language == "ไทย" else "Period high"), plot.loc[plot.value.idxmax()], "#47715A", "top center"),
        (("ต่ำสุดในช่วง" if language == "ไทย" else "Period low"), plot.loc[plot.value.idxmin()], "#A5544B", "bottom center")):
        fig.add_scatter(x=[row.period_display], y=[row.value], name=name,
                        mode="markers+text", text=[name.removeprefix("Period ").title()],
                        textposition=position, marker=dict(color=color, size=10))
    fig.update_layout(title=f"{label} · {title_range}", yaxis_title=("บาทต่อบาททองคำ" if language == "ไทย" else "THB per baht-weight"),
                      xaxis_title=None, template="goldpulse", hovermode="x unified")
    if monthly_resolution:
        fig.update_xaxes(type="category", categoryorder="array",
                         categoryarray=plot.period_display.tolist())
    return fig, plot
