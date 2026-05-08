"""Aggregate raw IPUMS USA extract to country/age/education/year medians for Power BI.

Reads the raw IPUMS CSV extract, applies the methodology defined in
docs/methodology.md (sample restrictions, weights, suppression threshold),
and writes a small aggregated CSV that the Power BI dashboard consumes.

Per the IPUMS USA Usage License, raw microdata cannot be redistributed.
This script is the bridge between the licensed raw extract (kept locally)
and the aggregated outputs (publishable).

Usage:
    python ipums_aggregator.py --src "D:\\IPUMS\\usa_00001.csv"

No third-party packages required — uses only the Python standard library.

NOTES ON COUNTRY CONSOLIDATION:
    - England (BPL 410), Scotland (411), and Wales (412) are remapped to
      United Kingdom (413) before aggregation. IPUMS coded UK-born
      immigrants inconsistently across years; consolidating gives one
      combined population.
    - Czechoslovakia (BPL 452) dissolved 1993; relabeled "Former Czechoslovakia"
    - Yugoslavia (BPL 457) dissolved 1991-2003; relabeled "Former Yugoslavia".
      Post-Yugoslav countries (Serbia, Bosnia, Croatia, etc.) are not
      separately coded in harmonized BPL — they all roll up to 457.
    - Other USSR/Russia (BPL 465) covers the USSR (dissolved 1991) and
      most post-Soviet states except the Baltics (codes 460-462);
      relabeled "Former USSR / Russia".

NOTES ON EDUCATION GROUPS:
    EDUC is the IPUMS general-version educational attainment code.
    Grouped into 5 buckets: Less than HS, High school, Some college,
    Bachelor's, Graduate. See education_group() for code mapping.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


# ─── Methodology constants (see docs/methodology.md) ──────────────────────────

# 2010 → 2024 CPI-U conversion factor.
# Annual avg CPI-U: 2010 = 218.056, 2024 = ~314.4 (Bureau of Labor Statistics).
# Update this if you re-run with newer CPI data:
# https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-202412.pdf
CPI2010_TO_2024 = 314.4 / 218.056  # ≈ 1.4419

# Minimum unweighted sample size per cell. Cells below this are suppressed
# to prevent unstable medians on small immigrant groups.
MIN_SAMPLE_SIZE = 200

# Working-age window for earnings analysis.
MIN_AGE = 25
MAX_AGE = 64

# IPUMS BPL codes: 001-056 = US states, 099 = US n.s., 100-120 = US territories.
# Anything above 120 is foreign-born. (See IPUMS BPL codebook for exact codes.)
NATIVE_BPL_MAX = 120

# BPL code remapping — combine UK constituent countries into a single
# "United Kingdom" entry. IPUMS coded UK-born immigrants inconsistently
# across years (some years used England/Scotland/Wales separately, others
# used the catch-all UK code 413). Consolidating gives one combined
# population of UK-born immigrants.
BPL_REMAP: dict[int, int] = {
    410: 413,  # England → United Kingdom
    411: 413,  # Scotland → United Kingdom
    412: 413,  # Wales → United Kingdom
}

# Country name lookup (BPL code → display name). This covers the major
# foreign-born populations in the US ACS data. Codes for entities that have
# dissolved (Yugoslavia, USSR, Czechoslovakia) are labeled with "Former"
# prefix for historical accuracy.
COUNTRY_NAMES: dict[int, str] = {
    # ─── US territories (treated as native_born) ──────────
    99:  "United States",
    100: "American Samoa",
    105: "Guam",
    110: "Puerto Rico",
    115: "U.S. Virgin Islands",
    120: "Other US Possessions",

    # ─── Other North America ──────────────────────────────
    150: "Canada",
    155: "St. Pierre and Miquelon",
    160: "Atlantic Islands",
    199: "Other North America",

    # ─── Central America and Caribbean ────────────────────
    200: "Mexico",
    210: "Central America (region)",
    250: "Cuba",
    260: "West Indies (region)",
    299: "Other Americas",

    # ─── South America ────────────────────────────────────
    300: "South America (region)",

    # ─── Northern Europe ──────────────────────────────────
    400: "Denmark",
    401: "Finland",
    402: "Iceland",
    403: "Lapland",
    404: "Norway",
    405: "Sweden",
    # 410-412 (England, Scotland, Wales) are remapped to 413 above
    413: "United Kingdom",
    414: "Ireland",
    419: "Other Northern Europe",

    # ─── Western Europe ───────────────────────────────────
    420: "Belgium",
    421: "France",
    422: "Liechtenstein",
    423: "Luxembourg",
    424: "Monaco",
    425: "Netherlands",
    426: "Switzerland",
    429: "Other Western Europe",

    # ─── Southern Europe ──────────────────────────────────
    430: "Albania",
    431: "Andorra",
    432: "Gibraltar",
    433: "Greece",
    434: "Italy",
    435: "Malta",
    436: "Portugal",
    437: "San Marino",
    438: "Spain",
    439: "Vatican City",
    440: "Other Southern Europe",

    # ─── Central/Eastern Europe ───────────────────────────
    450: "Austria",
    451: "Bulgaria",
    452: "Former Czechoslovakia",   # dissolved 1993
    453: "Germany",
    454: "Hungary",
    455: "Poland",
    456: "Romania",
    457: "Former Yugoslavia",        # dissolved 1991-2003
    458: "Other Central Europe",
    459: "Other Eastern Europe",

    # ─── Baltic States / Russia ───────────────────────────
    460: "Estonia",
    461: "Latvia",
    462: "Lithuania",
    463: "Other Baltic States",
    465: "Former USSR / Russia",     # USSR dissolved 1991
    499: "Other Europe",

    # ─── East Asia ────────────────────────────────────────
    500: "China",
    501: "Japan",
    502: "Korea",
    509: "Other East Asia",

    # ─── Southeast Asia ───────────────────────────────────
    510: "Brunei",
    511: "Cambodia",
    512: "Indonesia",
    513: "Laos",
    514: "Malaysia",
    515: "Philippines",
    516: "Singapore",
    517: "Thailand",
    518: "Vietnam",
    519: "Other Southeast Asia",

    # ─── India / Southwest Asia ───────────────────────────
    520: "Afghanistan",
    521: "India",
    522: "Iran",
    523: "Maldives",
    524: "Nepal",

    # ─── Middle East / Asia Minor ─────────────────────────
    530: "Bahrain",
    531: "Cyprus",
    532: "Iraq",
    533: "Iraq/Saudi Arabia",
    534: "Israel/Palestine",
    535: "Jordan",
    536: "Kuwait",
    537: "Lebanon",
    538: "Oman",
    539: "Qatar",
    540: "Saudi Arabia",
    541: "Syria",
    542: "Turkey",
    543: "United Arab Emirates",
    544: "North Yemen",
    545: "South Yemen",
    546: "Persian Gulf States",
    547: "Other Middle East",
    548: "Southwest Asia",
    549: "Asia Minor",
    550: "South Asia",
    599: "Other Asia",

    # ─── Africa ───────────────────────────────────────────
    600: "Africa (region)",

    # ─── Oceania ──────────────────────────────────────────
    700: "Australia and New Zealand",
    710: "Pacific Islands",

    # ─── Other / unknown ──────────────────────────────────
    800: "Antarctica",
    900: "Abroad (unknown)",
    950: "Other n.e.c.",
    997: "Unknown",
    999: "Missing/blank",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def age_group(age: int) -> str | None:
    """Map age to a cohort label, or None if outside the analytical window."""
    if 25 <= age <= 34: return "25-34"
    if 35 <= age <= 44: return "35-44"
    if 45 <= age <= 54: return "45-54"
    if 55 <= age <= 64: return "55-64"
    return None


def years_in_us_group(years: int) -> str:
    """Map years-in-US to a cohort label."""
    if years <= 5: return "0-5"
    if years <= 10: return "6-10"
    if years <= 20: return "11-20"
    return "20+"


def education_group(educ: int) -> str:
    """Map IPUMS EDUC code to a 5-bucket education label.

    EDUC codebook:
      00-05 = no high school completion (less than HS)
      06    = grade 12 / HS graduate or equivalent
      07-09 = some college, no bachelor's
      10    = bachelor's degree (4 years of college)
      11    = graduate / professional degree (5+ years)
      99    = missing
    """
    if educ <= 5:  return "Less than HS"
    if educ == 6:  return "High school"
    if educ <= 9:  return "Some college"
    if educ == 10: return "Bachelor's"
    if educ == 11: return "Graduate"
    return "Unknown"


def weighted_median(values_weights: list[tuple[float, float]]) -> float:
    """Compute the weighted median of a list of (value, weight) tuples.

    Sorts values, accumulates weights, returns the value at which cumulative
    weight crosses half of total weight.
    """
    if not values_weights:
        return float("nan")
    sorted_vw = sorted(values_weights, key=lambda x: x[0])
    total_weight = sum(w for _, w in sorted_vw)
    half = total_weight / 2.0
    cumulative = 0.0
    for v, w in sorted_vw:
        cumulative += w
        if cumulative >= half:
            return v
    return sorted_vw[-1][0]


# ─── Main aggregation ────────────────────────────────────────────────────────

def aggregate(src_path: Path, dst_path: Path, min_n: int = MIN_SAMPLE_SIZE) -> tuple[int, int, int]:
    """Stream-read the IPUMS extract, accumulate per-cell observations, write
    aggregated medians. Returns (rows_scanned, rows_kept, cells_emitted).
    """
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

    # Cell key → list of (incwage_adj, hhincome_adj, weight) tuples.
    # Two parallel accumulators: one keyed with education_group (per-bucket),
    # one with education_group="All" (rolled-up, preserves the original grain
    # so pre-education DAX measures keep working unchanged).
    cells: dict[tuple, list[tuple[float, float, float]]] = defaultdict(list)
    cells_all_edu: dict[tuple, list[tuple[float, float, float]]] = defaultdict(list)

    scanned = kept = 0
    unmapped_bpls: set[int] = set()
    remapped_count = 0

    with src_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = {col: i for i, col in enumerate(header)}

        # Required columns — fail fast if missing.
        for required in ("YEAR", "AGE", "BPL", "EMPSTAT", "YRSUSA1", "PERWT", "EDUC",
                         "INCWAGE_CPIU_2010", "HHINCOME_CPIU_2010"):
            if required not in idx:
                raise SystemExit(f"Missing required column: {required}")

        for row in reader:
            scanned += 1

            try:
                year = int(row[idx["YEAR"]])
                age = int(row[idx["AGE"]])
                bpl_raw = int(row[idx["BPL"]])
                empstat = int(row[idx["EMPSTAT"]])
                yrs = int(row[idx["YRSUSA1"]] or 0)
                educ = int(row[idx["EDUC"]] or 0)
                perwt = float(row[idx["PERWT"]])
                wage_adj = float(row[idx["INCWAGE_CPIU_2010"]] or 0)
                hh_adj = float(row[idx["HHINCOME_CPIU_2010"]] or 0)
            except (ValueError, KeyError):
                continue

            # Apply BPL remapping (UK consolidation, etc.)
            bpl = BPL_REMAP.get(bpl_raw, bpl_raw)
            if bpl != bpl_raw:
                remapped_count += 1

            # Working-age filter
            ag = age_group(age)
            if ag is None:
                continue

            # Employed filter (EMPSTAT = 1 = employed)
            if empstat != 1:
                continue

            # Must have positive wage to compute earnings median
            if wage_adj <= 0:
                continue

            # Education group
            edu_group = education_group(educ)

            # Cohort
            if bpl <= NATIVE_BPL_MAX:
                cohort_kind = "native_born"
                country_code = 99
                country_name = "United States"
                yrs_group = "n/a"
            else:
                cohort_kind = "foreign_born"
                country_code = bpl
                country_name = COUNTRY_NAMES.get(bpl)
                if country_name is None:
                    country_name = f"BPL_{bpl}"
                    unmapped_bpls.add(bpl)
                yrs_group = years_in_us_group(yrs)

            key = (cohort_kind, country_code, country_name, ag, yrs_group, edu_group, year)
            cells[key].append((wage_adj, hh_adj, perwt))
            key_all = (cohort_kind, country_code, country_name, ag, yrs_group, "All", year)
            cells_all_edu[key_all].append((wage_adj, hh_adj, perwt))
            kept += 1

            if scanned % 1_000_000 == 0:
                print(f"  scanned {scanned:>11,}  kept {kept:>11,}  cells {len(cells):>6,}")

    # ─── Compute aggregates per cell ─────────────────────────────────────────
    # Emit rolled-up (education_group="All") rows first so the original
    # dashboard grain is preserved, then per-education-bucket rows for the
    # new education visuals. Measures that don't slice by education should
    # filter education_group="All" to avoid double-counting.
    output_rows = []
    for (cohort_kind, country_code, country_name, ag, yrs_group, edu_group, year), obs in (
        list(cells_all_edu.items()) + list(cells.items())
    ):
        n = len(obs)
        if n < min_n:
            continue

        weighted_n = sum(w for _, _, w in obs)
        wage_median_2010 = weighted_median([(v, w) for v, _, w in obs])
        hh_pairs = [(h, w) for _, h, w in obs if h > 0]
        hh_median_2010 = weighted_median(hh_pairs) if hh_pairs else float("nan")

        output_rows.append({
            "cohort_kind":          cohort_kind,
            "country_code":         country_code,
            "country_name":         country_name,
            "age_group":            ag,
            "years_in_us_group":    yrs_group,
            "education_group":      edu_group,
            "year":                 year,
            "n_unweighted":         n,
            "n_weighted":           round(weighted_n, 0),
            "median_incwage_2024":  round(wage_median_2010 * CPI2010_TO_2024, 0),
            "median_hhincome_2024": (round(hh_median_2010 * CPI2010_TO_2024, 0)
                                     if hh_median_2010 == hh_median_2010
                                     else ""),
        })

    output_rows.sort(key=lambda r: (
        r["cohort_kind"], r["country_name"], r["year"],
        r["age_group"], r["years_in_us_group"], r["education_group"],
    ))

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with dst_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    if remapped_count:
        print(f"\n  Applied BPL remapping to {remapped_count:,} rows.")

    if unmapped_bpls:
        print(f"\n  Note: {len(unmapped_bpls)} BPL codes were not in COUNTRY_NAMES.")
        print(f"  These rows kept their numeric label (BPL_<code>). Sample:")
        for code in sorted(unmapped_bpls)[:15]:
            print(f"    BPL_{code}")
        print("  Extend COUNTRY_NAMES in this script to label them.")

    return scanned, kept, len(output_rows)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--src",
        type=Path,
        default=Path(r"D:\IPUMS\usa_00001.csv"),
        help="Path to the unzipped IPUMS CSV (default: %(default)s)",
    )
    p.add_argument(
        "--dst",
        type=Path,
        default=Path("data/aggregated/medians_by_country_age_year.csv"),
        help="Where to write the aggregated CSV (default: %(default)s)",
    )
    p.add_argument(
        "--min-n",
        type=int,
        default=MIN_SAMPLE_SIZE,
        help="Minimum unweighted cell size to retain (default: %(default)s)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not args.src.exists():
        raise SystemExit(f"Source file not found: {args.src}")

    print(f"Aggregating {args.src}")
    print(f"Filters: AGE {MIN_AGE}-{MAX_AGE}, EMPSTAT=1 (employed), INCWAGE > 0")
    print(f"Suppression threshold: n_unweighted >= {args.min_n}")
    print(f"Inflation: 2010 dollars × {CPI2010_TO_2024:.4f} → 2024 dollars")
    print(f"BPL remapping: {len(BPL_REMAP)} codes ({BPL_REMAP})")
    print(f"Education groups: 5 buckets (Less than HS / High school / Some college / Bachelor's / Graduate)\n")

    scanned, kept, emitted = aggregate(args.src, args.dst, min_n=args.min_n)

    print(f"\nDone.")
    print(f"  Rows scanned:       {scanned:>11,}")
    print(f"  Rows kept (filtered): {kept:>11,}")
    print(f"  Cells emitted:      {emitted:>11,}")
    print(f"  Output: {args.dst}")


if __name__ == "__main__":
    main()