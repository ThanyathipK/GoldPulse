# Official daily-data access audit

**Audit date:** 25 October 2026  
**Decision:** Do not add an automated official daily-price adapter yet. Keep the
forecasting feature isolated as a clearly labelled synthetic methodology demo.

## Question reviewed

Can GoldPulse obtain a sufficiently long, reproducible series of official Thai
gold prices at daily resolution, with clear permission to automate collection
and redistribute the resulting dataset?

For forecasting, a useful source must satisfy all of these conditions:

1. It is the Gold Traders Association (GTA), or is an explicitly licensed
   official export from GTA.
2. It supplies dated historical observations at daily or announcement-level
   resolution, with enough history for chronological validation.
3. The access method is stable and documented (API or downloadable file), not a
   guessed private endpoint.
4. Automated retrieval and reuse are clearly permitted.
5. The original observations and provenance can be retained without silently
   filling missing dates.

## Evidence

### Historical observations exist in the official interface

The GTA [historical-price page](https://sse.goldtraders.or.th/updatepricelist)
provides start/end date controls and columns for date, time, announcement round,
gold-bar and ornament buy/sell prices, Gold Spot, THB, and price change. The
older official [historical-price interface](https://gtadmin.goldtraders.or.th/updatepricelist/)
also exposes historical announcement and Thailand Gold Fix sections.

This establishes that official observations exist, but the pages are
interactive interfaces rather than documented data-distribution endpoints.

### No official daily bulk export or documented public API was found

The GTA [downloads page](https://gtadmin.goldtraders.or.th/download/) lists
publications and administrative files, including an ornament-redemption table,
but no daily-price CSV/XLSX export. Searches of the official domains found no
public API documentation for historical prices.

The official historical page can therefore be used for human verification, but
this audit did not identify a stable, supported interface suitable for a
reproducible production adapter.

### robots.txt does not settle reuse rights

A single read-only check of
`https://sse.goldtraders.or.th/robots.txt` on the audit date returned a general
`Allow: /` rule and Cloudflare content signals of `search=yes`, `ai-train=no`,
and `use=reference`. The response also included application fallback HTML after
the directives, so it should not be treated as API documentation.

The general crawl rule is not a data licence and does not grant permission to
republish a historical price database. It also does not describe request-rate
limits or supported query parameters.

### Published terms did not provide a usable grant

The current site links to a
[terms-and-conditions page](https://sse.goldtraders.or.th/terms-and-conditions),
but both a browser read and one direct read-only request returned the page shell
without substantive terms text. Consequently, this audit could not verify a
licence covering automated extraction, storage, or redistribution of daily
history.

### Third-party histories are not a substitute for official permission

Third-party sites advertise long daily histories derived from GTA announcements.
They may be useful for cross-checking, but they are not an official GTA export,
and no third-party licence was evaluated here. GoldPulse must not relabel those
datasets as official or import them without a separate provenance and licence
review.

## Risk assessment

| Requirement | Result | Reason |
|---|---|---|
| Official provenance | Partial | Official history is visible in GTA interfaces. |
| Adequate resolution/history | Likely | Announcement-level fields are shown, but a complete export was not obtained. |
| Stable documented access | Fail | No documented public historical API or daily bulk file was found. |
| Clear automation/reuse permission | Fail | robots.txt is permissive for crawling but is not a reuse licence; usable terms text was unavailable. |
| Reproducible raw snapshot | Fail | There is no authorized bulk artifact to version and validate. |

Adding a scraper now would require assumptions about private endpoints and reuse
rights. That is not responsible for a portfolio project and would make the
pipeline less reproducible, not more.

## Implementation decision

- Do not scrape the official interactive page or reverse-engineer its network
  requests.
- Do not copy a third-party historical database and call it official.
- Do not generate, interpolate, or backfill official daily observations from
  monthly averages.
- Continue to use the checked-in official monthly-average snapshot for official
  analysis.
- Keep forecasting restricted to the visibly labelled synthetic demo until a
  permitted real daily source is available.

No source adapter or raw daily fixture was added because doing so would imply a
permission and reproducibility level that the evidence does not support.

## What would unblock real daily forecasting

Any one of the following should trigger a new audit:

1. GTA publishes a documented historical-price API with reuse terms.
2. GTA publishes a daily/announcement-level CSV or spreadsheet under a clear
   licence.
3. GTA gives written permission for GoldPulse to retrieve, store, and display
   the data, including an agreed request rate.
4. A licensed third-party provider is selected and labelled as third-party
   reference data rather than official GTA data.

Before enabling an adapter, save the permission record, archive one untouched
source response, document the schema and timezone/calendar conversion, validate
duplicates and missing dates, and add fixture-based parser tests. Network access
should remain opt-in and rate limited; tests must not depend on the live site.

## Audit limitations

This was a narrow, low-request review rather than a legal opinion. Site content,
terms, endpoints, and robots directives can change. The audit made only the two
direct read-only requests needed to inspect robots.txt and the linked terms page;
it did not crawl date ranges, probe private endpoints, bypass controls, or
download historical observations.
