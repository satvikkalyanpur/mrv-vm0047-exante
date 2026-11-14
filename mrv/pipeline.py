"""Run a scenario through the VM0047 rules and collect every table."""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from datetime import date
from statistics import mean

import pandas as pd
import yaml

from . import ledger
from .allometry import DAS_H_RANGE_M, palm_biomass
from .buffer import buffer_fraction
from .carbon import height_at, palms_per_ha, stock_change_tco2e, woody_carbon_t_per_ha
from .credits import schedule
from .eligibility import select_approach, site_checks
from .leakage import breakeven_carbon_stock_tc_per_ha, leakage
from .uncertainty import ci_halfwidth_fraction, unc_exante

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = "config/vm0047_v1_1.yaml"
SCENARIO = "config/scenario_arecanut_newplanting.yaml"
INPUT_FILES = [RULES, SCENARIO, "data/growth_anchor_bhoomika2023.csv", "data/parcel.geojson",
               "data/reference_stands.csv"]


def _path(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def load_yaml(p: str) -> dict:
    with open(_path(p), encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Result:
    rules: dict
    scenario: dict
    approach: str
    approach_reason: str
    checks: list
    cultivars: pd.DataFrame
    schedule: pd.DataFrame
    summary: dict
    extra: dict = field(default_factory=dict)


def _stock_change_by_cultivar(sc: dict, rules: dict, anchors: pd.DataFrame, age: float) -> list[float]:
    """Parcel stock change (t CO2e) at a given age, one value per cultivar."""
    k = rules["constants"]
    n = palms_per_ha(sc["stand"]["spacing_m"], sc["stand"]["survival_fraction"])
    out = []
    for row in anchors.itertuples():
        h = height_at(age, row.height_m, sc["stand"]["anchor_age_years"])
        c_t = woody_carbon_t_per_ha(
            sc["biomass"]["equation"], row.stem_diameter_cm, h, n,
            sc["biomass"]["root_to_shoot"], k["carbon_fraction"],
        )
        out.append(stock_change_tco2e(sc["site"]["area_ha"], c_t, 0.0, k["co2_per_c"]))
    return out


def run(scenario: dict | str = SCENARIO, rules: dict | str = RULES) -> Result:
    rules = load_yaml(rules) if isinstance(rules, str) else rules
    sc = load_yaml(scenario) if isinstance(scenario, str) else scenario
    anchors = pd.read_csv(_path(sc["stand"]["growth_anchor_csv"]))
    k, ded = rules["constants"], sc["deductions"]
    horizon = rules["exante"]["horizon_years"]
    area = sc["site"]["area_ha"]
    n = palms_per_ha(sc["stand"]["spacing_m"], sc["stand"]["survival_fraction"])
    eq, r = sc["biomass"]["equation"], sc["biomass"]["root_to_shoot"]

    # 1. Which approach applies, and what is not yet shown.
    approach, reason = select_approach(
        n, area,
        rules["approach_selection"]["census_max_planting_units_per_ha"],
        rules["approach_selection"]["area_based_min_contiguous_cover_ha"],
    )
    land = sc["land_at_start"]
    checks = site_checks(
        land["preexisting_woody_cover_pct"], land["cleared_in_last_10_years"],
        land["agricultural_production_displaced"], has_non_carbon_revenue=True, hypothetical=True,
    )

    # 2. Stock at the anchor age, per cultivar.
    rows = []
    for row in anchors.itertuples():
        palm = palm_biomass(eq, row.stem_diameter_cm, row.height_m, r)
        c = woody_carbon_t_per_ha(eq, row.stem_diameter_cm, row.height_m, n, r, k["carbon_fraction"])
        rows.append({
            "cultivar": row.cultivar,
            "height_m": row.height_m,
            "stem_diameter_cm": row.stem_diameter_cm,
            "agb_kg_per_palm": palm.agb_kg,
            "bgb_kg_per_palm": palm.bgb_kg,
            "carbon_t_per_ha": c,
            "co2e_t_per_ha": c * k["co2_per_c"],
            "within_equation_range": palm.in_calibration_range,
        })
    cultivars = pd.DataFrame(rows)

    # 3. Uncertainty from the spread between cultivars at the horizon.
    at_horizon = _stock_change_by_cultivar(sc, rules, anchors, horizon)
    u = ci_halfwidth_fraction(at_horizon, rules["uncertainty"]["confidence_level"])
    unc = (
        unc_exante(u, rules["uncertainty"]["exante_minimum_deduction"])
        if ded["uncertainty"] == "auto" else float(ded["uncertainty"])
    )
    if unc < rules["uncertainty"]["exante_minimum_deduction"]:
        raise ValueError("Ex-ante uncertainty deduction may not be below the methodology minimum.")

    # 4. Year-by-year schedule.
    years = list(range(0, horizon + 1))
    dc = [mean(_stock_change_by_cultivar(sc, rules, anchors, y)) for y in years]
    buf = buffer_fraction(ded["buffer_rating"], rules["buffer"]["minimum_rating"], rules["buffer"]["fail_overall"])
    sched = pd.DataFrame(schedule(
        years, dc, ded["performance_benchmark"], unc, buf,
        ded["leakage_tco2e"], ded["project_emissions_tco2e"], sc["timeline"]["verification_years"],
    ))
    start = date.fromisoformat(sc["timeline"]["project_start"])
    sched.insert(1, "calendar_year", [start.year + y for y in years])
    mean_h = [mean(height_at(y, h, sc["stand"]["anchor_age_years"]) for h in anchors.height_m) for y in years]
    sched["mean_height_m"] = mean_h
    sched["height_within_equation_range"] = [
        (DAS_H_RANGE_M[0] <= h <= DAS_H_RANGE_M[1]) if eq.startswith("das") else None for h in mean_h
    ]

    # 5. Position today.
    as_of = date.fromisoformat(sc["timeline"]["as_of"])
    elapsed = max(0.0, (as_of - start).days / 365.25)
    dc_now = mean(_stock_change_by_cultivar(sc, rules, anchors, min(elapsed, horizon)))
    now_rows = schedule([0, elapsed], [0.0, dc_now], ded["performance_benchmark"], unc, buf,
                        ded["leakage_tco2e"], ded["project_emissions_tco2e"], ())
    accrued_now = now_rows[-1]["credits_accrued_cumulative"]

    last = sched.iloc[-1]
    summary = {
        "scenario": sc["name"],
        "methodology": f'{rules["methodology"]["id"]} v{rules["methodology"]["version"]}',
        "approach": approach,
        "equation": eq,
        "area_ha": area,
        "palms_per_ha": n,
        "horizon_years": horizon,
        "performance_benchmark": ded["performance_benchmark"],
        "uncertainty_estimated": u,
        "uncertainty_deducted": unc,
        "buffer_fraction": buf,
        "stock_change_tco2e": float(last.stock_change_tco2e),
        "after_benchmark_and_uncertainty_tco2e": float(last.after_benchmark_and_uncertainty_tco2e),
        "leakage_tco2e": ded["leakage_tco2e"],
        "net_removals_tco2e": float(last.net_removals_cumulative_tco2e),
        "buffer_tco2e": float(sched.buffer_in_year_tco2e.sum()),
        "credits_issuable": float(last.credits_issued_cumulative),
        "credits_per_ha_per_year": float(last.credits_issued_cumulative) / area / horizon,
        "as_of": sc["timeline"]["as_of"],
        "years_elapsed": elapsed,
        "stock_change_to_date_tco2e": dc_now,
        "credits_accrued_to_date": accrued_now,
        "credits_issued_to_date": float(sched[sched.year <= elapsed].credits_issued_at_verification.sum()),
    }
    return Result(rules, sc, approach, reason, checks, cultivars, sched, summary)


def position_at(result: Result, age_years: float) -> dict:
    """Stock and credits accrued at any age, using the result's deductions."""
    sc, rules, s = result.scenario, result.rules, result.summary
    anchors = pd.read_csv(_path(sc["stand"]["growth_anchor_csv"]))
    ded = sc["deductions"]
    dc = mean(_stock_change_by_cultivar(sc, rules, anchors, age_years))
    rows = schedule([0, age_years], [0.0, dc], ded["performance_benchmark"], s["uncertainty_deducted"],
                    s["buffer_fraction"], ded["leakage_tco2e"], ded["project_emissions_tco2e"], ())
    height = mean(height_at(age_years, h, sc["stand"]["anchor_age_years"]) for h in anchors.height_m)
    return {"mean_height_m": height, "stock_change_tco2e": dc,
            "credits_accrued": rows[-1]["credits_accrued_cumulative"] if age_years > 0 else 0.0}


def progress_to_date(result: Result) -> pd.DataFrame:
    """Month by month from planting to the as-of date."""
    sc = result.scenario
    start = date.fromisoformat(sc["timeline"]["project_start"])
    as_of = date.fromisoformat(sc["timeline"]["as_of"])
    months = (as_of.year - start.year) * 12 + (as_of.month - start.month)
    if as_of.day < start.day:
        months -= 1
    notes = {int(k): v for k, v in sc.get("establishment", {}).get("milestones", {}).items()}
    rows = []
    for m in range(0, months + 1):
        y, mo = divmod(start.month - 1 + m, 12)
        pos = position_at(result, m / 12)
        rows.append({"month": m, "date": date(start.year + y, mo + 1, start.day).isoformat(),
                     **pos, "credits_issued": 0.0, "field_stage": notes.get(m, "")})
    return pd.DataFrame(rows)


def reality_check(result: Result) -> pd.DataFrame:
    """Modelled year-10 stock next to stands that were actually measured."""
    ref = pd.read_csv(_path("data/reference_stands.csv"))
    ref["carbon_kg_per_palm"] = ref.carbon_t_per_ha * 1000 / ref.palms_per_ha
    k = result.rules["constants"]
    horizon = result.summary["horizon_years"]
    c_ha = result.summary["stock_change_tco2e"] / k["co2_per_c"] / result.summary["area_ha"]
    model = pd.DataFrame([{
        "source": "This model", "location": result.scenario["site"]["district"], "age_years": horizon,
        "palms_per_ha": round(result.summary["palms_per_ha"]), "carbon_t_per_ha": c_ha,
        "pools": "above + below ground", "note": f'{result.summary["equation"]}, mean of 8 cultivars',
        "carbon_kg_per_palm": c_ha * 1000 / result.summary["palms_per_ha"],
    }])
    return pd.concat([model, ref], ignore_index=True)


def with_overrides(scenario: dict, **changes) -> dict:
    """Copy of a scenario with some inputs replaced. Keys: equation,
    survival_fraction, performance_benchmark, uncertainty, buffer_rating,
    leakage_tco2e."""
    sc = copy.deepcopy(scenario)
    for key, value in changes.items():
        if key == "equation":
            sc["biomass"]["equation"] = value
        elif key == "survival_fraction":
            sc["stand"]["survival_fraction"] = value
        elif key in sc["deductions"]:
            sc["deductions"][key] = value
        else:
            raise KeyError(key)
    return sc


def sensitivity(scenario: dict, rules: dict) -> pd.DataFrame:
    """One input changed at a time around the reference case."""
    reference = run(scenario, rules).summary["credits_issuable"]
    rows = []
    for key, values in scenario["sensitivity"].items():
        for v in values:
            case = run(with_overrides(scenario, **{key: v}), rules)
            credits = case.summary["credits_issuable"]
            in_range = case.cultivars.within_equation_range
            rows.append({"input": key, "value": v, "credits_issuable": credits,
                         "change_vs_reference": credits / reference - 1,
                         "cultivars_within_equation_range":
                             None if in_range.isna().all() else f"{int(in_range.sum())} of {len(in_range)}"})
    return pd.DataFrame(rows)


def cropland_alternative(result: Result) -> dict:
    """What VMD0054 implies if the same planting went onto working cropland
    instead of fallow. Yield cancels when new land yields what the parcel did."""
    lk_rules = result.rules["leakage"]
    lk = leakage(result.scenario["site"]["area_ha"], 1.0,
                 supply_increase_share=lk_rules["supply_increase_share"],
                 new_land_share=lk_rules["new_land_share"])
    removals = result.summary["after_benchmark_and_uncertainty_tco2e"]
    return {
        "new_land_ha": lk.new_land_ha,
        "removals_before_leakage_tco2e": removals,
        "breakeven_carbon_stock_tc_per_ha": breakeven_carbon_stock_tc_per_ha(
            removals, lk.new_land_ha, result.rules["constants"]["co2_per_c"]),
    }


def build_ledger(result: Result, files: list[str]) -> list[dict]:
    records = [{"record": "input", "file": f, "sha256": ledger.file_sha256(_path(f))} for f in files]
    s = result.summary
    for key in ("stock_change_tco2e", "uncertainty_deducted", "performance_benchmark",
                "buffer_fraction", "net_removals_tco2e", "credits_issuable"):
        records.append({"record": "result", "name": key, "value": round(float(s[key]), 4)})
    return ledger.build_chain(records)


def write_outputs(result: Result, out_dir: str = "outputs") -> dict:
    out = _path(out_dir)
    os.makedirs(out, exist_ok=True)
    result.cultivars.to_csv(os.path.join(out, "cultivars_at_year_10.csv"), index=False, float_format="%.4f")
    result.schedule.to_csv(os.path.join(out, "schedule.csv"), index=False, float_format="%.4f")
    progress = progress_to_date(result)
    progress.to_csv(os.path.join(out, "progress_to_date.csv"), index=False, float_format="%.4f")
    check = reality_check(result)
    check.to_csv(os.path.join(out, "reality_check.csv"), index=False, float_format="%.3f")
    sens = sensitivity(result.scenario, result.rules)
    sens.to_csv(os.path.join(out, "sensitivity.csv"), index=False, float_format="%.4f")
    illustrative = run(with_overrides(result.scenario, **result.scenario["illustrative_case"]), result.rules)
    crop = cropland_alternative(result)
    chain = build_ledger(result, INPUT_FILES)
    with open(os.path.join(out, "ledger.json"), "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=2)
    payload = {
        "reference_case": result.summary,
        "illustrative_case": illustrative.summary,
        "cropland_alternative": crop,
        "approach_reason": result.approach_reason,
        "checks": [c.__dict__ for c in result.checks],
        "ledger_head": chain[-1]["hash"],
    }
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"sensitivity": sens, "illustrative": illustrative, "cropland": crop, "ledger": chain,
            "progress": progress, "reality_check": check}
