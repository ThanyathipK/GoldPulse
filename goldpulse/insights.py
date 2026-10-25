"""Dataset-aware narrative generation."""
import pandas as pd

from goldpulse.analytics import PeriodStats


def period_insight(series: pd.DataFrame, stats: PeriodStats, label: str,
                   monthly_resolution: bool, quality_note: str, language: str = "English") -> str:
    valid = stats.changes.dropna()
    if valid.empty and language == "ไทย":
        return f"ช่วงที่เลือกมีข้อมูลที่ถูกต้องเพียงหนึ่งจุด จึงยังคำนวณแนวโน้มและการเคลื่อนไหวสูงสุดไม่ได้ {quality_note}"
    if valid.empty:
        return ("Only one valid observation is available for this selection, so a trend "
                f"and largest movements cannot be calculated. {quality_note}")
    cadence = "month-to-month" if monthly_resolution else "daily"
    date_format = "%b %Y" if monthly_resolution else "%d %b %Y"
    positive, negative = valid[valid > 0], valid[valid < 0]
    if positive.empty:
        increase = f"No {cadence} increase was observed"
    else:
        idx = positive.idxmax()
        increase = (f"The largest {cadence} increase was **฿{positive.loc[idx]:+,.0f} "
                    f"in {series.loc[idx, 'announcement_date']:{date_format}}**")
    if negative.empty:
        decrease = f"no {cadence} decrease was observed"
    else:
        idx = negative.idxmin()
        decrease = (f"the largest {cadence} decrease was **฿{negative.loc[idx]:+,.0f} "
                    f"in {series.loc[idx, 'announcement_date']:{date_format}}**")
    if language == "ไทย":
        cadence_th = "เดือนต่อเดือน" if monthly_resolution else "รายวัน"
        increase_th = ("ไม่พบการเพิ่มขึ้น" if positive.empty else
                       f"การเพิ่มขึ้น{cadence_th}มากที่สุดคือ **฿{positive.max():+,.0f} ใน {series.loc[positive.idxmax(), 'announcement_date']:{date_format}}**")
        decrease_th = ("ไม่พบการลดลง" if negative.empty else
                       f"การลดลง{cadence_th}มากที่สุดคือ **฿{negative.min():+,.0f} ใน {series.loc[negative.idxmin(), 'announcement_date']:{date_format}}**")
        direction_th = "เพิ่มขึ้น" if stats.change > 0 else "ลดลง" if stats.change < 0 else "ไม่เปลี่ยนแปลง"
        return (f"{label} **{direction_th} ฿{abs(stats.change):,.0f} ({stats.change_pct:+.2f}%)** ในช่วงที่เลือก "
                f"{increase_th}; {decrease_th} ราคาสิ้นสุดอยู่{'สูงกว่า' if stats.change > 0 else 'ต่ำกว่า' if stats.change < 0 else 'เท่ากับ'}ราคาเริ่มต้น {quality_note}")
    direction = "rose" if stats.change > 0 else "fell" if stats.change < 0 else "was unchanged"
    ending = "above" if stats.change > 0 else "below" if stats.change < 0 else "the same as"
    return (f"{label} **{direction} ฿{abs(stats.change):,.0f} ({stats.change_pct:+.2f}%)** "
            f"over the selected period. {increase}; {decrease}. The ending price was "
            f"{ending} the starting price. {quality_note}")

