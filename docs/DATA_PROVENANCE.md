# Official dataset provenance

`data/official_2026_monthly.csv` contains monthly averages, not daily quotes. Its
checked-in input is `data/raw/gta_monthly_averages_2026.csv`. The snapshot records
the source URL and access timestamp on every observation so the published artifact
can be rebuilt and audited without relying on a live website.

Build it from the repository root:

```bash
python scripts/build_official_dataset.py
```

The command validates schema, monthly uniqueness and ordering, positive values,
buy/sell relationships, status, source, and timestamps. It writes the canonical
CSV plus `data/official_2026_monthly.provenance.json`, which records row counts,
coverage, the raw file SHA-256 digest, and transformations. No dates are filled,
and no values are interpolated. The raw snapshot is retained because changes to
the upstream page or its access policy could otherwise make the build irreproducible.
