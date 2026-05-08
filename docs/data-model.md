# Data Model

## Tables

| Table | Source | Grain | Notes |
|---|---|---|---|
| `Medians` | Aggregated CSV from `scripts/ipums_aggregator.py` | One row per (cohort_kind × country × age × YRS × education_group × year), where `education_group="All"` rows are the rolled-up totals | Fact table |
| `Date` | Generated in Power Query (`List.Numbers`) | One row per year, 2000–2024 | Time dim |
| `Countries` | Static `#table` lookup | One row per BPL code | Country dim with region + tier |

## Relationships

- `Medians[year]` → `Date[Year]` (many-to-one, single direction)
- `Medians[country_code]` → `Countries[bpl_code]` (many-to-one, single direction)

## Aggregated CSV schema (`Medians`)

| Column | Type | Notes |
|---|---|---|
| `cohort_kind` | text | `foreign_born` or `native_born` |
| `country_code` | int | BPL code; 99 for native-born |
| `country_name` | text | Display name |
| `age_group` | text | "25-34", "35-44", "45-54", "55-64" |
| `years_in_us_group` | text | "0-5", "6-10", "11-20", "20+", or "n/a" for native-born |
| `education_group` | text | "Less than HS", "High school", "Some college", "Bachelor's", "Graduate", or "All" for the rolled-up total. **Non-education visuals must filter `education_group = "All"` to avoid double-counting / averaging medians across buckets.** |
| `year` | int | ACS sample year, 2000–2024 |
| `n_unweighted` | int | Sample size for suppression decisions |
| `n_weighted` | float | Sum of person weights |
| `median_incwage_2024` | float | Weighted median wage, 2024 dollars |
| `median_hhincome_2024` | float | Weighted median household income, 2024 dollars |

## Countries dimension schema

| Column | Notes |
|---|---|
| `bpl_code` | IPUMS BPL value; primary key |
| `country_name` | Display name |
| `region` | Coarse geographic grouping (North America, East Asia, etc.) |
| `tier` | Data-density classification: `featured`, `available`, `sparse`, `regional`, `native` |

## Key DAX measures

| Measure | Definition | Where used |
|---|---|---|
| `Foreign Born Median` | `AVERAGE(Medians[median_incwage_2024])` filtered to `tier <> "native"` AND `education_group = "All"` | Overview KPIs, Comparison line/bars |
| `Native Born Median` | Same, but `REMOVEFILTERS(Countries)`, `tier = "native"`, and `education_group = "All"` | Overview KPIs (always-on baseline) |
| `Earnings Ratio to Native` | `[Foreign Born Median] / [Native Born Median]` | Overview KPI |
| `Recent Arrivals (0-5 yrs)` etc. | Same, filtered to `years_in_us_group = "0-5"` etc. | Trajectory chart and KPIs |
| `Country vs Native Ratio` | Same as Earnings Ratio, but per-country in filter context | Comparison bar leaderboard |
| `Chart Title` (dynamic) | Constructs title text from current country selection | Overview chart title binding |