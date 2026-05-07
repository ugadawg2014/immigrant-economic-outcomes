# Methodology

This dashboard presents median earnings of foreign-born US residents alongside
native-born comparators. The methodology choices below are the load-bearing
decisions that shape the visuals; understanding them is required to interpret
the findings correctly.

## Data source

- **IPUMS USA** harmonized ACS microdata, 1-year samples, 2000–2024
- Variables: `BPL`, `BPLD`, `AGE`, `YRSUSA1`, `YRIMMIG`, `CITIZEN`, `EDUC`,
  `EMPSTAT`, `SPEAKENG`, `SEX`, `INCWAGE`, `INCTOT`, `HHINCOME`, `STATEFIP`,
  `COUNTYFIP`, plus auto-included weights (`PERWT`, `HHWT`) and `CPI99`
- Inflation adjustment: **CPI-U with 2010 base year**, applied at extract time
  by IPUMS to `INCWAGE` and `HHINCOME`. Aggregator further converts to
  **2024 dollars** using the BLS CPI-U series.

## Sample restrictions

Median earnings are computed only on:
- **Persons aged 25–64** — captures core working-age population, avoids
  student-age earners and retirees
- **Employed** — `EMPSTAT = 1`
- **Wage > $0** — must have positive wage income (`INCWAGE > 0`)
- **Group quarters residents excluded** for cleaner population definition

## Weights

All medians are computed as **weighted medians** using `PERWT` (person weight),
which scales each sample observation to its population-level representation.

## Sample-size threshold

A `(country × age_group × years_in_us × year)` cell is **suppressed** if its
unweighted sample size is < **200 persons**. This prevents unstable medians
on small immigrant groups from creating noisy or misleading visuals.

## Native-born comparator

For every immigrant cell shown, a native-born comparator is computed using
the same age cohort and year. The comparator is:

> All persons with `BPL ≤ 120` (US states + DC + US territories), of the
> same age cohort and year, meeting the same employment and income filters.

Native-born observations are aggregated into a single "United States" entry
with `years_in_us_group = "n/a"`.

## Country-of-origin consolidations

To produce defensible analytical groupings, the aggregator applies these
remappings before computing medians:

- **United Kingdom**: BPL codes 410 (England), 411 (Scotland), 412 (Wales)
  remapped to 413 (UK). IPUMS coded UK-born immigrants inconsistently across
  ACS years; consolidating gives one combined population.

And these display-name updates for historical accuracy:

- **Former Yugoslavia** (BPL 457) — Yugoslavia dissolved 1991–2003. Modern
  successor states (Serbia, Bosnia, Croatia, etc.) are not separately coded
  in harmonized BPL; all roll up to 457.
- **Former Czechoslovakia** (BPL 452) — dissolved 1993; modern Czechia
  and Slovakia are not separately coded.
- **Former USSR / Russia** (BPL 465) — USSR dissolved 1991. Most post-Soviet
  states (Ukraine, Belarus, Kazakhstan, Armenia, etc.) roll up to 465 in
  harmonized BPL; only Estonia, Latvia, Lithuania have separate codes.

## Country tier classification

Countries in the dashboard are classified by data density:

| Tier | Cell count threshold | Treatment in visuals |
|---|---|---|
| **Featured** | ≥ 50 cells | Default visible in slicers and charts |
| **Available** | 25–49 cells | Available via slicer; included in defaults |
| **Sparse** | < 25 cells | Excluded by default; opt-in via slicer |
| **Regional** | regional aggregates (Central America, etc.) | Available; visually flagged with "(region)" suffix |
| **Native** | United States | Used as comparator only; not a "country" in the slicer |

## Age cohorts

Age is grouped into:
- 25–34
- 35–44
- 45–54
- 55–64

## Years-since-arrival cohorts (foreign-born only)

`YRSUSA1` is grouped as:
- 0–5 years (recent arrivals)
- 6–10 years (settling in)
- 11–20 years (established)
- 20+ years (long-tenured)

Recent arrivals naturally earn less due to credential transfer, English
acquisition, and job-search frictions. Convergence to native-born benchmarks
typically happens at 10–20 years; this cohorting makes the trajectory visible.

## Default time window

Default slicer range: **2005–2024**. ACS samples for 2000–2004 were materially
smaller (50K–1M persons/year vs 3M+ from 2005 onward) and produce sparser
country-cohort cells when sliced finely. The 2000–2004 window is included
in the underlying data but defaulted out.

## ACS 2020 — experimental weights

The ACS 2020 1-year PUMS file uses experimental weights to account for
COVID-19 response disruption. Per the U.S. Census Bureau, this sample
should not be directly compared to other ACS years. The 2021 dip in
foreign-born earnings reflects pandemic labor-market effects (immigrant-heavy
sectors hit harder than the broader economy). Both years remain in the
dataset for transparency; the methodology note flags them prominently.

## Limitations

Several economically meaningful dimensions are intentionally out of scope:

- **Wealth and assets** — ACS measures income, not balance sheets
- **Undocumented immigrants** — not separately identifiable in ACS
- **Second-generation outcomes** — ACS lacks parental-nativity at the adult
  level; identifying second-generation immigrant adults requires CPS data
- **Industry / occupation effects** — confounders we acknowledge but don't
  control for in v1
- **Education-controlled comparisons** — `EDUC` is in the extract but v1
  does not present education-stratified medians; planned for v2
- **Country-level Latin America / Caribbean / Africa** — harmonized BPL
  aggregates these to regional buckets; country-level detail requires `BPLD`
  (planned for v2)
  
  ### Citation

This analysis uses IPUMS USA Version 16.0 (2025). Users of this dashboard
or its findings should cite the data as:

> Steven Ruggles, Sarah Flood, Matthew Sobek, Daniel Backman, Grace Cooper,
> Julia A. Rivera Drew, Stephanie Richards, Renae Rodgers, Jonathan
> Schroeder, and Kari C.W. Williams. *IPUMS USA: Version 16.0* [dataset].
> Minneapolis, MN: IPUMS, 2025. <https://doi.org/10.18128/D010.V16.0>

The underlying data is collected by the U.S. Census Bureau through the
American Community Survey. IPUMS USA harmonizes the Census Bureau's data
across years for cross-temporal comparison.

## Future enhancements (v2)

- **Country-level detail for Latin America / Caribbean / Africa** using
  BPLD instead of harmonized BPL. Specifically: split Central America (210)
  into Guatemala/Honduras/El Salvador/Nicaragua/Costa Rica/Panama; split
  South America (300) into individual countries; split West Indies (260)
  into Dominican Republic/Haiti/Jamaica/Trinidad; unpack Africa (600) into
  individual countries.
- **Post-Yugoslav and post-Soviet country detail** using BPLD codes
  (Serbia, Bosnia, Croatia, Slovenia, Ukraine, Belarus, etc.).
- **Education-stratified medians** to test whether immigrant earnings gaps
  persist after controlling for educational attainment.
- **State-level geographic view** showing where major immigrant origin
  groups concentrate (uses STATEFIP, already in extract).