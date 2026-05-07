# IPUMS extract specification

This document records the exact IPUMS USA extract used for this dashboard,
so the analysis is reproducible.

## Samples

ACS 1-year, **2000 through 2024** (25 samples).

## Variables

### Auto-included
`YEAR`, `SAMPLE`, `SERIAL`, `CBSERIAL`, `HHWT`, `CLUSTER`, `STRATA`, `GQ`, `PERNUM`, `PERWT`

### Technical
`CPI99`

### Geographic
`STATEFIP`, `COUNTYFIP`

### Household economic
`HHINCOME`

### Person — demographic
`SEX`, `AGE`

### Person — nativity / citizenship
`BPL`, `BPLD`, `CITIZEN`, `YRIMMIG`, `YRSUSA1`

### Person — education
`EDUC`, `EDUCD`

### Person — work
`EMPSTAT`, `EMPSTATD`

### Person — income
`INCWAGE`, `INCTOT`

### Person — language
`SPEAKENG`

## Extract options

- **Data quality flags**: not requested
- **Specified cases**: none (full samples)
- **Multi-generation attach**: not requested
- **Subsampling**: none
- **Inflation adjustment**: applied to `INCWAGE` and `HHINCOME` using
  CPI-U with **2010 base year**. Adjusted columns named
  `INCWAGE_CPIU_2010` and `HHINCOME_CPIU_2010`.

## Format

- **Data Format**: CSV
- **Structure**: Rectangular (person)

## Reproduction

Register at <https://usa.ipums.org>, navigate to SELECT DATA, request the
samples and variables above with the same options. The IPUMS extract number
will differ but the resulting dataset is equivalent.