# GoldPulse product and analysis specification

## Problem and objectives

Thai retail buyers encounter many intraday gold announcements but often lack a simple way to put the latest reference price into historical context. GoldPulse consolidates traceable observations, makes change and uncertainty visible, and teaches responsible time-series analysis.

Objectives are to preserve source lineage; show current and historical reference prices in plain language; expose missingness rather than silently filling it; compare gold forms and related variables; and evaluate a small forecast honestly against a baseline.

## Users and needs

| User | Need | Product response |
|---|---|---|
| Retail buyer | Understand today's movement and spread | Latest price, daily delta, range, trend, calculator |
| Student | Learn how announcements become analysis | Raw/clean separation, lineage, quality view, documented metrics |
| Analyst | Explore frequency, volatility, intraday changes, relationships | Filters, resampling, rolling volatility, comparison and correlation |

## Scope

In scope: Thai 96.5% reference-price announcements; gold bars and ornaments; buy/sell prices; daily through monthly descriptive analysis; optional spot and USD/THB context; experimental 1–3 business-day forecasting; offline review; user-entered calculators.

Out of scope: trade execution, portfolio custody, alerts, authentication, guaranteed real-time service, shop inventory or workmanship fees, tax advice, financial recommendations, causal inference, and automated crawling of sources whose permission has not been reviewed.

## Functional requirements

1. Filter observations by inclusive date range and price series.
2. Show latest value, daily absolute change, period high/low/average, units, data status, and last sample date.
3. Visualize close history, announcement count, buy–sell spread, resampled trend, rolling volatility, gold-type comparison, and intraday movement.
4. Show a correlation matrix only when the relevant fields exist, alongside a non-causality warning.
5. Compare a naive baseline with a time-series model on a chronological holdout; report MAE and RMSE; show actual-versus-predicted results.
6. Label forecast date, selected model, uncertainty range, limitations, and non-advice status.
7. Keep raw source payloads separate from validated records and preserve URL, collection time, and observation status.
8. Provide cost-average and profit/loss calculators whose results exclude unspecified costs.

Non-functional requirements: deterministic transformations; readable on current desktop browsers; no credentials in code; idempotent storage; explicit units; reasonable accessibility contrast; offline startup using sample data; source requests with descriptive user agent, timeout, and delay.

## User stories and acceptance criteria

- As a retail buyer, I want to compare today's selling price with the selected-period average so I can understand recent movement.
  - Given a range with observations, the overview shows the latest final announcement and period average in THB per baht-weight.
- As an analyst, I want missing dates left visible so I do not mistake invented values for observations.
  - Given a date with no record, charts do not interpolate or add a database row, and the interface states the behavior.
- As a student, I want honest forecast evaluation so I can compare complexity with a baseline.
  - Given at least 35 daily values, training precedes the holdout dates, both models receive the same holdout, and MAE/RMSE are displayed.
- As a reviewer, I want lineage so I can tell sample, observed, and estimated data apart.
  - Every cleaned row has `source_url`, `collected_at`, and `data_status`; the quality view exposes status values.
- As a user, I want clear product boundaries.
  - Every forecast view says “estimate,” identifies limitations, and contains no buy/sell recommendation.

## Data dictionary

| Field | Type | Unit / rule |
|---|---|---|
| `announcement_date` | date | Local announcement date |
| `announcement_time` | string | `HH:MM`, Asia/Bangkok |
| `announcement_round` | integer | Sequence within date; positive |
| `bar_buy`, `bar_sell` | decimal | THB per baht-weight, 96.5%; sell must not be below buy |
| `ornament_buy`, `ornament_sell` | decimal, nullable | THB per baht-weight, 96.5% |
| `gold_spot_usd_oz` | decimal, nullable | USD per troy ounce |
| `usd_thb` | decimal, nullable | THB per USD |
| `source_url` | string | Exact origin or synthetic URI |
| `collected_at` | UTC timestamp | Acquisition time, not announcement time |
| `data_status` | enum-like string | `observed`, `estimated`, or `synthetic_demo` |

Natural key: date + time + round. On a duplicate, retain the most recently collected valid version. Never silently impute a missing price. Required-key or invalid-price rows go to a rejected set with a reason.

## Source and collection policy

Preferred order: documented official API; official downloadable file; official historical page; permitted third-party API with provenance; manually reviewed import. Before collection, record the current terms review and inspect `robots.txt`. Respect disallow rules, authentication, rate limits, copyright, database rights, and personal-data rules. Cache responses, request only the necessary range, identify the client, use timeouts and backoff, and stop on blocking or unexpected schema changes. Never evade a CAPTCHA, login, token requirement, or anti-bot system.

The official Gold Traders Association is the intended reference authority. As source structure and permissions can change, GoldPulse does not enable an unreviewed production scraper by default. Shop quotes must be stored under a distinct source and never labeled official reference prices.

## Dashboard wireframe

```text
┌ Filters ┐  ┌ GoldPulse — source/status/updated ─────────────────┐
│ range   │  │ latest │ change │ high │ low │ average            │
│ series  │  ├────────────────────────────────────────────────────┤
│ status  │  │ Overview | Analysis | Forecast | Tools | Quality   │
└─────────┘  │ main trend chart                                   │
             │ supporting chart          supporting chart         │
             │ plain-language explanation / limitations           │
             └────────────────────────────────────────────────────┘
```

## Forecast design

Daily final announcements form the target series. The holdout is the final 20 observations, capped at one quarter of available history, and is never shuffled. The baseline repeats the final training value. Ridge autoregression uses three lags and a time trend. Selection uses holdout MAE; RMSE remains visible. The forward range is the selected prediction ± the 90th percentile absolute holdout error, with a minimum demo width of THB 100. This is a heuristic uncertainty band, not a calibrated probabilistic interval.

## Risks, assumptions, and limitations

- Source markup, endpoints, terms, or access policy may change; adapters must fail closed and be reviewed.
- Announcements may be corrected or duplicated; the latest collected version wins but change history is not yet versioned.
- Timezone and Buddhist/Gregorian year conversion are common error sources; production adapters need explicit tests.
- Spot and FX timestamps may not align with announcement timestamps, producing misleading correlations.
- Reference prices do not include a shop's workmanship fees, inventory constraints, or exact buy-back policy.
- Historical relationships can break abruptly. The model omits macro news and is unsuitable for investment decisions.
- The current sample is synthetic and exists only to demonstrate functionality.

## Definition of done

The app starts from a clean environment using documented commands; sample data is visibly labeled; filters and charts work; tests pass; chronological forecast metrics render; raw/clean storage responsibilities are separate; and no claim presents an estimate as advice or an official observation.

