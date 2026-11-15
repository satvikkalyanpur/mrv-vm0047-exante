"""Checks against hand calculations and the methodology's own examples.

Run with:  python -m pytest -q
"""
import copy
import json
import math
import os

import pytest

from mrv import allometry, benchmark, buffer, carbon, credits, eligibility, leakage, ledger, pipeline, uncertainty


# ---- biomass equations -------------------------------------------------

def test_prayogo_matches_hand_calculation():
    # 0.03883 * 10 * 12^1.2, with 12^1.2 = 19.7259
    assert allometry.prayogo2018_agb(12, 10) == pytest.approx(7.660, abs=0.005)


def test_das_models_reproduce_the_papers_mean_palm():
    # Das et al. 2021 mean palm: D 11.11 cm, H 11.43 m, total biomass 34.08 kg.
    # Both models should land within about 5 % of that.
    assert allometry.das2021_m2_total(11.43) == pytest.approx(34.08, rel=0.05)
    assert allometry.das2021_m3_total(11.11, 11.43) == pytest.approx(34.08, rel=0.05)


def test_das_split_reproduces_modelled_total():
    palm = allometry.palm_biomass("das2021_m2", 15.0, 8.0, 0.25)
    assert palm.total_kg == pytest.approx(allometry.das2021_m2_total(8.0))
    assert palm.bgb_kg / palm.agb_kg == pytest.approx(0.25)


def test_calibration_range_is_flagged():
    assert allometry.palm_biomass("das2021_m2", 15.0, 8.0, 0.25).in_calibration_range is True
    assert allometry.palm_biomass("das2021_m2", 15.0, 3.0, 0.25).in_calibration_range is False
    assert allometry.palm_biomass("das2021_m3", 17.38, 9.02, 0.25).in_calibration_range is False  # D above 16.5 cm


def test_unknown_equation_is_rejected():
    with pytest.raises(ValueError):
        allometry.palm_biomass("made_up", 12, 10, 0.25)


# ---- carbon (VM0047 Eqs. 1, 3, 4) ---------------------------------------

def test_planting_density():
    assert carbon.palms_per_ha(2.7) == pytest.approx(1371.74, abs=0.01)


def test_height_growth_is_linear_then_flat():
    assert carbon.height_at(0, 8.0, 10) == 0
    assert carbon.height_at(5, 8.0, 10) == pytest.approx(4.0)
    assert carbon.height_at(12, 8.0, 10) == pytest.approx(8.0)


def test_carbon_chain_by_hand():
    # Prayogo, D 12, H 10: AGB 7.660 kg/palm. 1000 palms/ha, R 0.25, CF 0.47.
    # C = 7.660 * 1000 / 1000 * 0.47 * 1.25 = 4.500 t C/ha; on 2 ha: 9.000 t C = 33.00 t CO2e.
    c = carbon.woody_carbon_t_per_ha("prayogo2018", 12, 10, 1000, 0.25, 0.47)
    assert c == pytest.approx(4.500, abs=0.005)
    assert carbon.stock_change_tco2e(2.0, c, 0.0, 44 / 12) == pytest.approx(33.00, abs=0.05)


# ---- uncertainty (Section 8.4, 8.6) -------------------------------------

def test_confidence_interval_by_hand():
    # Values 10, 12, 14: mean 12, sd 2, se 1.1547, t(0.95, 2) = 2.920 -> 28.1 %
    assert uncertainty.ci_halfwidth_fraction([10, 12, 14]) == pytest.approx(0.2810, abs=0.0005)


def test_exante_floor_of_ten_percent():
    assert uncertainty.unc_exante(0.04) == 0.10
    assert uncertainty.unc_exante(0.18) == 0.18


def test_expost_area_equation_27():
    # One pool. Start: U 0.05, C 100. Now: U 0.08, C 160. Change 60.
    # sqrt(5^2 + 12.8^2) / 60 = 0.2290; minus the 10 % allowance = 0.1290
    unc = uncertainty.unc_expost_area([(0.05, 100)], [(0.08, 160)], 60)
    assert unc == pytest.approx(0.1290, abs=0.0005)


def test_expost_allowance_means_small_uncertainty_costs_nothing():
    assert uncertainty.unc_expost_area([(0.0, 0)], [(0.05, 100)], 100) == 0.0
    assert uncertainty.unc_expost_census(0.06, 0.05) == 0.0


def test_no_crediting_above_100_percent_uncertainty():
    assert uncertainty.creditable(0.99) and not uncertainty.creditable(1.01)


# ---- performance benchmark (Appendix 1) ---------------------------------

def test_benchmark_reproduces_methodology_example():
    # VM0047 Appendix 1, Example 1: control slope 0.02, project slope 0.15 -> PB = 13 %
    project = benchmark.Trend(0.15, 0.01, 0.0001, 10)
    control = benchmark.Trend(0.02, 0.005, 0.01, 10)
    assert benchmark.performance_benchmark(project, control) == pytest.approx(0.1333, abs=0.0005)


def test_no_credit_when_project_grows_like_controls():
    # An existing garden and its neighbours: same trend -> PB = 1 -> nothing credited.
    project = benchmark.Trend(0.010, 0.004, 0.03, 10)
    control = benchmark.Trend(0.009, 0.004, 0.04, 10)
    assert benchmark.performance_benchmark(project, control) == 1.0


def test_flat_or_noisy_controls_count_as_zero():
    project = benchmark.Trend(0.15, 0.01, 0.0001, 10)
    assert benchmark.performance_benchmark(project, benchmark.Trend(-0.01, 0.003, 0.01, 10)) == 0.0
    assert benchmark.performance_benchmark(project, benchmark.Trend(0.02, 0.02, 0.40, 10)) == 0.0


def test_trend_and_z_statistic():
    trend = benchmark.weighted_trend([0, 1, 2, 3], [0.10, 0.21, 0.29, 0.41])
    assert trend.slope == pytest.approx(0.101, abs=0.001)
    z = benchmark.z_statistic(benchmark.Trend(0.15, 0.03, 0, 5), benchmark.Trend(0.03, 0.04, 0, 5))
    assert z == pytest.approx(0.12 / 0.05)


def test_standardised_difference():
    assert benchmark.standardised_difference([1, 2, 3], [1, 2, 3]) == 0
    assert benchmark.standardised_difference([1, 2, 3], [2, 3, 4]) == pytest.approx(1.0)


# ---- leakage (VMD0054) and buffer (NPRT) --------------------------------

def test_new_land_from_default_shares():
    # 1.27 ha displaced, same yield on new land: 1.27 * 0.75 * 0.40 = 0.381 ha
    lk = leakage.leakage(1.27, 3.0)
    assert lk.new_land_ha == pytest.approx(0.381)
    assert lk.emissions_tco2e is None


def test_leakage_emissions_and_zero_when_nothing_displaced():
    lk = leakage.leakage(10, 2.0, carbon_stock_new_land_tc_per_ha=100)
    assert lk.emissions_tco2e == pytest.approx(10 * 0.75 * 0.40 * 100 * 44 / 12)
    kept = leakage.leakage(10, 2.0, monitored_production_t=20, carbon_stock_new_land_tc_per_ha=100)
    assert kept.emissions_tco2e == 0


def test_buffer_floor_and_failure():
    assert buffer.buffer_fraction(5) == 0.12
    assert buffer.buffer_fraction(25) == 0.25
    with pytest.raises(buffer.RiskAnalysisFailed):
        buffer.buffer_fraction(61)


# ---- credits (Eq. 30) ---------------------------------------------------

def test_equation_30_bracket():
    # 100 * (1 - 0.2) * (1 - 0.1) - 5 - 1 = 66
    assert credits.net_removals_cumulative(100, 0.2, 0.1, 5, 1) == pytest.approx(66)


def test_schedule_adds_up_and_issues_only_at_verification():
    rows = credits.schedule([0, 1, 2, 3, 4], [0, 10, 25, 45, 70], 0.1, 0.1, 0.2, verification_years=[2, 4])
    assert sum(r["removals_in_year_tco2e"] for r in rows) == pytest.approx(70 * 0.9 * 0.9)
    assert rows[-1]["credits_accrued_cumulative"] == pytest.approx(70 * 0.9 * 0.9 * 0.8)
    assert rows[-1]["credits_issued_cumulative"] == pytest.approx(rows[-1]["credits_accrued_cumulative"])
    assert [r["year"] for r in rows if r["credits_issued_at_verification"] > 0] == [2, 4]


def test_leakage_can_wipe_out_early_issuance():
    rows = credits.schedule([0, 1, 2], [0, 10, 25], 0.0, 0.1, 0.12, leakage_tco2e=40, verification_years=[2])
    assert rows[-1]["credits_issued_cumulative"] == 0


# ---- approach selection and ledger --------------------------------------

def test_dense_planting_is_area_based_sparse_is_census():
    assert eligibility.select_approach(1372, 1.27)[0] == "area-based"
    assert eligibility.select_approach(40, 1.27)[0] == "census-based"


def test_ledger_detects_tampering():
    chain = ledger.build_chain([{"a": 1}, {"b": 2}, {"c": 3}])
    assert ledger.verify_chain(chain)
    tampered = copy.deepcopy(chain)
    tampered[1]["b"] = 99
    assert not ledger.verify_chain(tampered)


# ---- the scenario, end to end -------------------------------------------

@pytest.fixture(scope="module")
def result():
    return pipeline.run()


def test_parcel_area_matches_polygon(result):
    # Shoelace area on a local projection should be within 1 % of the 1.27 ha in the scenario.
    with open(os.path.join(pipeline.ROOT, result.scenario["site"]["parcel_geojson"])) as f:
        ring = json.load(f)["features"][0]["geometry"]["coordinates"][0]
    lat0 = math.radians(sum(p[1] for p in ring[:-1]) / (len(ring) - 1))
    a, e2 = 6378137.0, 0.00669437999
    m_per_deg_lat = math.radians(1) * a * (1 - e2) / (1 - e2 * math.sin(lat0) ** 2) ** 1.5
    m_per_deg_lon = math.radians(1) * a * math.cos(lat0) / math.sqrt(1 - e2 * math.sin(lat0) ** 2)
    pts = [(p[0] * m_per_deg_lon, p[1] * m_per_deg_lat) for p in ring]
    area_ha = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:]))) / 2 / 10_000
    assert area_ha == pytest.approx(result.scenario["site"]["area_ha"], rel=0.01)


def test_year_10_reference_case_by_hand(result):
    # Independent recomputation of the headline number from the cited inputs.
    heights = [7.25, 7.64, 8.24, 9.02, 7.06, 7.21, 8.02, 7.95]
    per_palm = [1.074 * math.exp(-0.496 + 1.616 * math.log(h)) for h in heights]   # total kg
    mean_total_kg = sum(per_palm) / len(per_palm)
    stock = mean_total_kg * (10_000 / 2.7 ** 2) / 1000 * 0.47 * (44 / 12) * 1.27    # t CO2e on the parcel
    assert result.summary["stock_change_tco2e"] == pytest.approx(stock, rel=1e-9)
    assert result.summary["credits_issuable"] == pytest.approx(stock * 0.90 * 0.88, rel=1e-9)


def test_deductions_never_fall_below_methodology_floors(result):
    assert result.summary["uncertainty_deducted"] >= 0.10
    assert result.summary["buffer_fraction"] >= 0.12
    low = pipeline.with_overrides(result.scenario, uncertainty=0.05)
    with pytest.raises(ValueError):
        pipeline.run(low, result.rules)


def test_nothing_issued_before_first_verification(result):
    assert result.summary["credits_issued_to_date"] == 0
    assert 0 < result.summary["credits_accrued_to_date"] < result.summary["credits_issuable"]


def test_run_is_reproducible(result):
    again = pipeline.run()
    assert again.summary == result.summary
    files = pipeline.INPUT_FILES
    assert pipeline.build_ledger(result, files) == pipeline.build_ledger(again, files)


# ---- progress so far, reality check, observed record ---------------------

def test_progress_runs_from_planting_to_as_of(result):
    progress = pipeline.progress_to_date(result)
    assert progress.month.iloc[0] == 0 and progress.credits_accrued.iloc[0] == 0
    assert progress.month.iloc[-1] == 5                        # 1 June 2026 to 15 November 2026
    assert progress.credits_accrued.is_monotonic_increasing
    assert (progress.credits_issued == 0).all()                # first verification is in year 5
    assert progress.stock_change_tco2e.iloc[-1] < result.schedule.stock_change_tco2e[1]   # less than a year in


def test_model_is_below_measured_palms(result):
    check = pipeline.reality_check(result)
    model = check.iloc[0].carbon_kg_per_palm
    measured = check[check.source.str.startswith("Das")].carbon_kg_per_palm
    # Das et al. 2021, age 10: 7.8 t C/ha over 650 palms = 12.0 kg C per palm
    assert measured.iloc[0] == pytest.approx(12.0)
    assert model < measured.min()


def test_weather_parser_sums_days_and_drops_fill_values():
    from mrv import observe
    payload = {"properties": {"parameter": {
        "PRECTOTCORR": {"20250601": 10.0, "20250602": 5.0, "20250603": -999.0, "20250701": 2.0},
        "T2M": {"20250601": 24.0, "20250602": 26.0, "20250603": -999.0, "20250701": 23.0},
    }}}
    monthly = observe.parse_power_daily(payload)
    june = monthly.iloc[0]
    assert june.rain_mm == pytest.approx(15.0) and june.temp_c == pytest.approx(25.0) and june.days_with_data == 2
    assert monthly.iloc[1].rain_mm == pytest.approx(2.0)


def test_ndvi_parser_scales_and_drops_fill_values():
    from mrv import observe
    payload = {"scale": "0.0001", "subset": [
        {"calendar_date": "2025-06-10", "data": [8123]},
        {"calendar_date": "2025-06-26", "data": [-3000]},
    ]}
    assert observe.parse_modis_subset(payload) == [{"date": "2025-06-10", "ndvi": 0.8123}]


def test_parcel_centroid_and_shipped_observation(result):
    from mrv import observe
    lat, lon = observe.parcel_centroid(os.path.join(pipeline.ROOT, "data/parcel.geojson"))
    assert lat == pytest.approx(13.4000, abs=0.001) and lon == pytest.approx(75.7588, abs=0.001)
    obs = observe.load(os.path.join(pipeline.ROOT, "data/observed"))
    assert obs["ndvi_poc"].ndvi.iloc[0] == pytest.approx(0.873)


def test_observed_chart_draws_with_partial_data():
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from mrv import figures
    obs = {"weather": pd.DataFrame({"month": ["2025-06-01", "2025-07-01"], "rain_mm": [300.0, 600.0]}),
           "ndvi_modis": pd.DataFrame({"date": ["2025-06-10", "2025-07-12"], "ndvi": [0.71, 0.80]})}
    assert figures.observed_record(obs, "2025-06-01") is not None
    assert figures.observed_record({}, None) is not None
