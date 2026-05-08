# Findings

## Headline: country of origin matters more than nativity status

Across 25 years of ACS data, foreign-born US residents in aggregate earn
~95% of native-born comparators. But this aggregate hides order-of-magnitude
variation across origin countries:

| Country group | 20+ yrs vs Native | Story |
|---|---|---|
| United Kingdom | ~165% | Selection-effect immigration (financial services, tech) |
| India | ~125% | High-skill immigration pipeline |
| Philippines | ~110% | Strong convergence and exceedance |
| Korea | ~100% | Parity at long tenure |
| China | ~95% | Near-parity at long tenure |
| Vietnam | ~85% | Persistent gap, partial convergence |
| Mexico | ~65% | Largest population, persistent gap |
| Central America (region) | ~60% | Regional aggregate; persistent gap |

The implication: framing immigrant economic outcomes as a single category
obscures variation that is the actual story. "Immigrants" is not an
economically homogeneous group.

## Convergence patterns vary by country

The Trajectory page shows that immigrant earnings change with years since
arrival, but the rate and ceiling of convergence vary dramatically:

- **Mexican-born** immigrants close roughly half the gap to native-born
  over 20+ years (52% → 66%) but plateau short of full convergence
- **Filipino-born** immigrants exceed native-born medians at 20+ years
  (110%) while still earning less in their first 5 years (67%)
- **United Kingdom** trajectory shows incomplete cohort coverage because
  the UK-born population skews older and longer-tenured; recent-arrival
  cells fail the N ≥ 200 threshold

## Iran's elevated earnings reflect selection

Iranian-born US residents show ~150% of native-born median — among the
highest in the dataset. This is consistent with the post-1979 Iranian
diaspora skewing toward highly educated professionals, faculty, and
physicians. This is a population-composition observation, not an inherent
country-of-origin effect.

## Real wages declined 2000–2013, recovered 2014+

In constant 2024 dollars, both foreign-born and native-born medians
declined from ~$58K (2000) to ~$52K (2013), then recovered to ~$60K
(2024). The gap between the two groups remained roughly stable across
this macro cycle (~$2–4K spread), suggesting broadly correlated
labor-market exposure rather than divergent fortunes.

## Country fixed effects: selection bias is quantifiable

To separate "education explains earnings" from "country of origin explains
earnings, even at the same education level," we fit a weighted least squares
regression on the cell-level aggregated data:

```
log(median_wage) = alpha
                 + education_group  (4 dummies, "High school" omitted)
                 + age_group        (3 dummies, "35-44" omitted)
                 + year_fe          (year fixed effects, 2000 omitted)
                 + country          (~18 dummies, native-born = baseline)
                 + epsilon

weighted by n_weighted, with HC1 robust standard errors.
```

The country coefficients answer: *after holding education, age, and year
constant, how much does country of origin still predict earnings?* Code in
[scripts/regression.py](../scripts/regression.py); coefficients in
[data/aggregated/country_fixed_effects.csv](../data/aggregated/country_fixed_effects.csv).

**Weighted R² = 0.97** — the model accounts for 97% of weighted variance in
log-wages. Selected country fixed effects (% wage difference from native-born,
all 95% confidence intervals exclude zero unless flagged):

| Country | After-controls premium | 95% CI |
|---|---|---|
| India | **+33.6%** | [+31.1, +36.2] |
| United Kingdom | +22.3% | [+19.7, +25.0] |
| Canada | +19.0% | [+16.9, +21.2] |
| Former USSR / Russia | +12.6% | [+9.1, +16.2] |
| China | +10.9% | [+7.4, +14.6] |
| Italy | +10.1% | [+6.4, +14.0] |
| Japan | +3.6% | [+1.9, +5.3] |
| Korea | +3.6% | [-0.3, +7.6] *(not significant)* |
| Germany | +2.2% | [+1.0, +3.5] |
| Poland | +1.7% | [+0.2, +3.2] |
| Vietnam | +0.5% | [-2.5, +3.6] *(not significant)* |
| Philippines | -0.2% | [-1.8, +1.4] *(not significant)* |
| Africa (region) | -9.6% | [-11.5, -7.7] |
| Central America (region) | -10.9% | [-12.1, -9.7] |
| West Indies (region) | -11.4% | [-12.3, -10.4] |
| Cuba | -12.8% | [-15.8, -9.7] |
| South America (region) | -13.1% | [-14.7, -11.6] |
| Mexico | **-13.9%** | [-15.0, -12.8] |

### Reading the result

The country fixed effects describe **conditional correlations**, not causal
effects. They absorb everything that varies systematically by country of
origin and is not captured by the observable controls — most importantly:

- Visa pathway composition (employment-based vs family-reunification vs
  refugee). India, UK, and Canada are dominated by employment-visa flows
  (H-1B, TN, employment-based green cards) that pre-screen for specialized
  occupations. Mexico, Cuba, and Central America are dominated by
  family-reunification and refugee pathways with no occupational filter.
- Industry / occupation concentration not visible in EDUC alone.
- English proficiency.
- Whether education was earned in the US or abroad.
- Network effects on first job placement.

The 47-percentage-point spread between the India coefficient (+33.6%) and the
Mexico coefficient (-13.9%), at the same education and age, is the regression
analog of the descriptive Bachelor's-level spread in the dashboard. Both tell
the same story: country of origin is a strong predictor of US labor-market
outcomes for reasons the available human-capital controls do not explain. The
most parsimonious interpretation is that this residual reflects the
immigration-policy selection mechanism that routes different country flows
through different visa categories.

### Caveats on the regression

- **Cell-level, not individual-level.** Within-cell wage variance is unobserved,
  so standard errors should be interpreted as conservative lower bounds on
  uncertainty in the underlying individual-level relationships.
- **18 countries appear in the regression** vs. the larger country list in
  the descriptive dashboard. Smaller-population origins fail the n ≥ 200
  per-cell threshold often enough that they cannot contribute stable
  estimates after controlling for education × age × year combinations.
- **Tenure is omitted by design.** `years_in_us_group` is collinear with the
  foreign-born indicator (native-born = "n/a", every foreign-born obs has a
  non-reference value), so including it produces uninterpretable coefficients
  at an undefined reference point. Tenure dynamics are documented separately
  via the descriptive trajectory comparisons above.
- **Country FEs are an omnibus residual**, not a clean "selection only"
  estimator. They are the appropriate quantity for the descriptive question
  ("how much country-of-origin variation is explained by observables?") but
  not for causal claims about visa policy or selection effects per se.

## Pandemic disruption (2020–2021) was concentrated in immigrant-heavy sectors

The 2021 dip in foreign-born earnings (visible on the Overview page) is
consistent with documented pandemic labor-market effects. Immigrant
workers are over-represented in food service, hospitality, retail, and
construction trades — sectors that experienced the steepest 2020–2021
employment and earnings shocks. Recovery to pre-pandemic trajectories
appears largely complete by 2023–2024.