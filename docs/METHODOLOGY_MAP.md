# Rule-by-rule map

Where each rule comes from, where it lives in the code, and whether it is in use. Equation and section numbers follow the VM0047 v1.0 text; v1.1 is a minor revision and its published change list does not alter these equations. Confirm numbering against the v1.1 PDF before quoting.

## Implemented and used in the scenario

| Rule | Source | Code | Test |
|---|---|---|---|
| Approach selection (census ≤ 50 planting units/ha, else area-based) | VM0047 v1.1 applicability | `eligibility.select_approach` | `test_dense_planting_is_area_based_sparse_is_census` |
| Stock change = area × (stock now − stock at start) | Eq. (3) | `carbon.stock_change_tco2e` | `test_carbon_chain_by_hand` |
| Woody carbon = above-ground × (1 + R) | Eq. (4) | `carbon.woody_carbon_t_per_ha` | `test_carbon_chain_by_hand` |
| Carbon fraction 0.47; CO₂ = C × 44/12 | Parameter CF; Eq. (1) | `config/vm0047_v1_1.yaml` | `test_year_10_reference_case_by_hand` |
| Species equation chosen by preference order | Section 9 (monitoring) | `allometry.palm_biomass` | `test_das_models_reproduce_the_papers_mean_palm` |
| Ex-ante horizon of 10 years | Section 8.6 | `pipeline.run` | end-to-end tests |
| Ex-ante uncertainty deduction ≥ 10 % | Section 8.6 | `uncertainty.unc_exante` | `test_exante_floor_of_ten_percent` |
| Net removals = ΔC × (1 − PB) × (1 − UNC) − LK − PE | Eq. (30) | `credits.net_removals_cumulative` | `test_equation_30_bracket` |
| Monitoring at most five years apart | Section 9 (monitoring) | `credits.schedule` (verification years) | `test_schedule_adds_up_and_issues_only_at_verification` |
| Buffer ≥ 12 %, fail above 60 | Non-Permanence Risk Tool v4.2, 2.5.2 to 2.5.4 | `buffer.buffer_fraction` | `test_buffer_floor_and_failure` |
| Leakage zero where nothing is displaced | VMD0054 Eq. (2) | `leakage.leakage` | `test_leakage_emissions_and_zero_when_nothing_displaced` |

## Implemented and tested, not yet fed with real data

| Rule | Source | Code | Test |
|---|---|---|---|
| Ex-post uncertainty, area-based: max(0, U − 10 %) | Eq. (27) | `uncertainty.unc_expost_area` | `test_expost_area_equation_27` |
| Ex-post uncertainty, census-based | Eq. (28) | `uncertainty.unc_expost_census` | `test_expost_allowance_means_small_uncertainty_costs_nothing` |
| No crediting above 100 % uncertainty | Section 8.4 | `uncertainty.creditable` | `test_no_crediting_above_100_percent_uncertainty` |
| Match quality, standardised difference ≤ 0.25 | Eq. (A2) | `benchmark.standardised_difference` | `test_standardised_difference` |
| Stocking-index trend by weighted regression | Appendix 1, Step 5 | `benchmark.weighted_trend` | `test_trend_and_z_statistic` |
| Z test between project and control trends | Eq. (A5) | `benchmark.z_statistic` | `test_trend_and_z_statistic` |
| Performance benchmark | Eq. (A6) | `benchmark.performance_benchmark` | `test_benchmark_reproduces_methodology_example` |
| New land from displaced production (75 % × 40 %) | VMD0054 Eqs. (5) to (7) | `leakage.displaced_new_land_ha` | `test_new_land_from_default_shares` |
| Leakage emissions = new land × carbon stock × 44/12 | VMD0054 Eq. (10) | `leakage.leakage` | `test_leakage_emissions_and_zero_when_nothing_displaced` |

## Not implemented

| Rule | Source | Why it matters |
|---|---|---|
| Donor pool, nearest-neighbour matching and weights | Appendix 1, Steps 1 to 4, Eqs. (A1), (A3), (A4) | Needed to compute a real benchmark from satellite data. Requires at least 30 project plots, which one 1.27 ha parcel cannot supply on its own; this is a reason to aggregate parcels. |
| Ex-ante benchmark from a 10-year control trend | Section 8.6 | The scenario takes the benchmark as an input instead. |
| Census-based quantification | Eqs. (5) to (7), (29), (31) | The route for sparse boundary or intercrop planting on small farms. |
| Non-woody biomass, dead wood, litter, soil carbon | Eq. (2), Tables 1 and 2 | Optional or conditional pools; left out, which under-counts. |
| Project emissions from burning and fertiliser | Eq. (15) | Set to zero in the scenario. |
| Risk rating calculation | Non-Permanence Risk Tool | The scenario uses the floor of 12; a real rating scores internal, external and natural risk. |
| VMD0054 five-year time structure and mitigation areas | VMD0054 Steps 1 and 2 | Only the single-period form is coded. |
| Additionality: regulatory surplus, investment barrier | Section 7 | Listed as "not shown" in the eligibility checks. |
