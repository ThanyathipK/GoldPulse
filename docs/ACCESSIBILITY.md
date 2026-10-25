# Accessibility review

GoldPulse targets WCAG 2.2 AA for its portfolio presentation. This is a practical
review of the Streamlit interface, not a certification.

## What is covered

- The light theme uses dark text on white or near-white surfaces. The primary
  accent is `#806000`, which has a 5.85:1 contrast ratio against white.
- Positive (`#47715A`) and negative (`#A5544B`) chart colors both exceed 4.5:1
  against white. Direction is also communicated by signed values, labels, and
  position relative to zero; color is not the only cue.
- Price charts identify their series, units, period, high, and low. Hover text
  includes the date, value, and change. The same values are available in tables
  where a chart alone would be difficult to interpret.
- Every filter and calculator field has a visible label. Calculator results are
  withheld until the required values are entered, and formulas are shown in text.
- Native Streamlit controls are retained for keyboard operation and focus
  management. The interface does not replace controls with clickable HTML.
- Charts are followed by captions or data tables that explain resolution and
  limitations. Meaningful content does not depend on animation.
- The wide layout uses Streamlit's responsive column behavior and a bounded
  content width. Charts use concise labels suitable for laptop screens.

## Keyboard review checklist

Run this checklist after significant UI changes and before publishing:

1. Starting at the browser address bar, press Tab through the sidebar controls,
   tabs, download button, calculators, expanders, and source links.
2. Confirm every focused control has a visible browser/Streamlit focus indicator.
3. Change radio buttons and select boxes using arrow keys, and activate buttons
   with Enter or Space.
4. Confirm focus order follows the visual reading order and never becomes trapped.
5. At 200% browser zoom, confirm controls, KPI values, tables, and chart captions
   remain readable without overlapping.

## Screen-reader and chart limitations

Plotly charts are supplemental visualizations and are not a complete replacement
for their surrounding narrative and tables. GoldPulse supplies a generated insight
summary, KPI text, monthly table, and downloadable CSV so the core result remains
available without interpreting the graphics. Streamlit and Plotly determine some
generated accessibility-tree details, so the deployed build should also receive a
manual check with VoiceOver or NVDA.

## Automated checks

`tests/test_accessibility.py` guards the theme and chart presentation against common
regressions. Run it with:

```bash
pytest tests/test_accessibility.py
```

The checks verify WCAG contrast ratios, visible form labels/formulas, signed chart
changes, high/low annotations, explicit units, and non-color direction labels.

