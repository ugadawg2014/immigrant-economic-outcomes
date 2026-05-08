"""Weighted least squares earnings regression with country fixed effects.

Reads the cell-level aggregated CSV produced by ipums_aggregator.py and fits
a Mincer-style log-earnings regression:

    log(median_incwage_2024) = alpha
                             + education_group  (4 dummies, "High school" omitted)
                             + age_group        (3 dummies, "35-44" omitted)
                             + year             (year fixed effects)
                             + country          (~50 dummies, native-born = baseline)
                             + epsilon

weighted by n_weighted (so high-population cells dominate). Native-born is the
omitted country category; the country coefficients are interpreted as the
approximate log-wage difference relative to native-born after controlling for
observable human capital and year fixed effects.

We deliberately do NOT include years_in_us_group as a regressor here. It is
collinear with the foreign-born indicator (native-born observations carry
yrs="n/a", which is the omitted reference; every foreign-born observation
carries one of the non-reference levels). Including it would estimate the
country fixed effect at an undefined reference point and produce
uninterpretable coefficients. Tenure dynamics are documented separately in
docs/findings.md via descriptive comparisons across yrs-in-US groups.

Standard errors are HC1 (heteroskedasticity-robust). Cell-level data carries
unequal residual variance by construction, so OLS standard errors would be
unreliable.

Outputs:
  data/aggregated/country_fixed_effects.csv     - country coefficients with
                                                   95% CI, sorted descending
  data/aggregated/regression_coefficients.csv   - full coefficient table

Dependencies: pandas, statsmodels
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def load_cells(path: Path) -> pd.DataFrame:
    """Load the aggregated CSV, drop the 'All' education rollup rows, drop
    non-positive wage / weight rows.
    """
    df = pd.read_csv(path)
    df = df[df["education_group"] != "All"].copy()
    df = df[(df["median_incwage_2024"] > 0) & (df["n_weighted"] > 0)].copy()
    df["log_wage"] = np.log(df["median_incwage_2024"])
    # Use a single 'country' column where native-born collapses to a single
    # baseline label; foreign-born keeps country_name.
    df["country"] = np.where(
        df["cohort_kind"] == "native_born",
        "_NATIVE_BASELINE",
        df["country_name"],
    )
    # year-as-category so each gets its own fixed effect
    df["year_fe"] = df["year"].astype(str)
    return df


def fit_model(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fit weighted least squares with HC1 robust standard errors.

    Reference categories (omitted dummies):
      education_group:    "High school"
      years_in_us_group:  "n/a"  (native-born baseline)
      age_group:          "35-44" (peak earning years)
      country:            "_NATIVE_BASELINE"
    """
    df = df.copy()
    df["education_group"] = pd.Categorical(
        df["education_group"],
        categories=["High school", "Less than HS", "Some college", "Bachelor's", "Graduate"],
        ordered=False,
    )
    df["age_group"] = pd.Categorical(
        df["age_group"],
        categories=["35-44", "25-34", "45-54", "55-64"],
        ordered=False,
    )
    # Country: ensure native baseline is first so it becomes the omitted level.
    countries = sorted(df["country"].unique())
    countries.remove("_NATIVE_BASELINE")
    df["country"] = pd.Categorical(
        df["country"],
        categories=["_NATIVE_BASELINE"] + countries,
        ordered=False,
    )

    formula = (
        "log_wage ~ C(education_group) "
        "+ C(age_group) "
        "+ C(year_fe) "
        "+ C(country)"
    )
    model = smf.wls(formula, data=df, weights=df["n_weighted"])
    # HC1 robust standard errors
    return model.fit(cov_type="HC1")


def write_country_table(result, dst: Path) -> None:
    """Write country coefficients with 95% CI, sorted descending by effect size.

    Converts log-point coefficients to approximate percent differences from
    the native-born baseline.
    """
    coefs = result.params
    ses = result.bse
    cis = result.conf_int(alpha=0.05)

    rows = []
    for name in coefs.index:
        if not name.startswith("C(country)[T."):
            continue
        country = name.replace("C(country)[T.", "").rstrip("]")
        b = coefs[name]
        s = ses[name]
        ci_lo, ci_hi = cis.loc[name, 0], cis.loc[name, 1]
        rows.append({
            "country_name":     country,
            "log_coef":         round(b, 4),
            "se":               round(s, 4),
            "ci95_low_log":     round(ci_lo, 4),
            "ci95_high_log":    round(ci_hi, 4),
            "pct_vs_native":    round((np.exp(b) - 1) * 100, 1),
            "pct_ci95_low":     round((np.exp(ci_lo) - 1) * 100, 1),
            "pct_ci95_high":    round((np.exp(ci_hi) - 1) * 100, 1),
            "significant_5pct": "yes" if (ci_lo > 0 or ci_hi < 0) else "no",
        })

    out = pd.DataFrame(rows).sort_values("pct_vs_native", ascending=False)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)


def write_full_coefs(result, dst: Path) -> None:
    """Write full coefficient table for transparency / reproducibility."""
    coefs = result.params
    ses = result.bse
    cis = result.conf_int(alpha=0.05)

    out = pd.DataFrame({
        "term":       coefs.index,
        "coef_log":   coefs.values.round(4),
        "se":         ses.values.round(4),
        "ci95_low":   cis[0].values.round(4),
        "ci95_high":  cis[1].values.round(4),
        "approx_pct": ((np.exp(coefs.values) - 1) * 100).round(2),
    })
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--src", type=Path,
                   default=Path("data/aggregated/medians_by_country_age_year.csv"))
    p.add_argument("--dst-country", type=Path,
                   default=Path("data/aggregated/country_fixed_effects.csv"))
    p.add_argument("--dst-full", type=Path,
                   default=Path("data/aggregated/regression_coefficients.csv"))
    args = p.parse_args()

    print(f"Loading {args.src}")
    df = load_cells(args.src)
    print(f"  {len(df):,} cells, {df['country'].nunique() - 1} foreign-born countries")
    print(f"  weight range = [{df['n_weighted'].min():,.0f}, {df['n_weighted'].max():,.0f}]")

    print("Fitting WLS with HC1 robust standard errors...")
    result = fit_model(df)
    print(f"  weighted R^2 = {result.rsquared:.4f}")
    print(f"  observations = {int(result.nobs):,}")
    print(f"  k regressors = {len(result.params):,}")

    write_country_table(result, args.dst_country)
    print(f"Wrote {args.dst_country}")
    write_full_coefs(result, args.dst_full)
    print(f"Wrote {args.dst_full}")

    # Brief summary printed to stdout
    coefs = result.params
    cis = result.conf_int(alpha=0.05)
    country_terms = [n for n in coefs.index if n.startswith("C(country)[T.")]
    pcts = [(n.replace("C(country)[T.", "").rstrip("]"),
             (np.exp(coefs[n]) - 1) * 100) for n in country_terms]
    pcts.sort(key=lambda x: -x[1])
    print("\nTop 5 country fixed effects (% wage premium vs native-born, all controls):")
    for c, pct in pcts[:5]:
        print(f"  {c:<35s} {pct:+6.1f}%")
    print("\nBottom 5 country fixed effects:")
    for c, pct in pcts[-5:]:
        print(f"  {c:<35s} {pct:+6.1f}%")


if __name__ == "__main__":
    main()
