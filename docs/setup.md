# Setup

## Prerequisites

- **Power BI Desktop** (free) — <https://powerbi.microsoft.com/desktop/>
- **Python 3.10+**
- An **IPUMS USA account** — register at <https://usa.ipums.org> (free,
  approval typically within 1 business day)
- ~50 GB free disk for the IPUMS extract + working space

## One-time data prep

### 1. Pull the IPUMS extract

Per [ipums/extract-spec.md](../ipums/extract-spec.md):
- Samples: ACS 1-year 2000–2024
- Variables: see extract-spec.md for the full list
- Format: CSV
- Structure: Rectangular (person)
- Inflation adjustment: CPI-U, 2024 base year, applied to INCWAGE, INCTOT, HHINCOME

Submit, wait for the email, download. Save the unzipped CSV to:
D:\IPUMS\usa_NNNNN.csv

(Replace `NNNNN` with your extract number.)

### 2. Run the aggregator
python scripts/ipums_aggregator.py --src "D:\IPUMS\usa_NNNNN.csv"

Output: `data/aggregated/medians_by_country_age_year.csv` — small file (~50 KB),
the only data file Power BI reads. The raw extract stays out of the repo.

## Open the dashboard

1. Open `pbix/immigrant-outcomes.pbix` in Power BI Desktop
2. The `Medians` query reads `data/aggregated/medians_by_country_age_year.csv`.
   If you saved your aggregated CSV elsewhere, update the source path in
   Power Query Editor → Medians query → first step.
3. **Home → Refresh.** Refresh is fast (~10 sec) since the model only sees
   the small aggregated file.

## Refresh strategy

- **For new IPUMS data releases (annual):** re-pull the extract, re-run the
  aggregator, refresh Power BI.
- **For methodology iteration:** edit `scripts/ipums_aggregator.py`, re-run,
  refresh.

## Working directory vs repo

Large data files (raw IPUMS extracts) live outside the repo at `D:\IPUMS\` and
are gitignored. The repo contains code, documentation, the small aggregated
CSV (optional), and the .pbix.
