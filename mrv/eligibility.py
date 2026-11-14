"""Which VM0047 approach applies, and which applicability checks pass."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    rule: str
    status: str   # "pass", "fail", "not shown"
    note: str


def select_approach(
    planting_units_per_ha: float,
    contiguous_cover_ha: float,
    census_max_units_per_ha: float = 50,
    area_min_cover_ha: float = 1.0,
) -> tuple[str, str]:
    """Census-based is for sparse direct planting that does not change the
    land use (at most 50 planting units per hectare in v1.1). Dense planting
    that closes canopy over more than a hectare is area-based."""
    if planting_units_per_ha <= census_max_units_per_ha:
        return "census-based", (
            f"{planting_units_per_ha:.0f} planting units/ha is within the census limit of "
            f"{census_max_units_per_ha:.0f}/ha."
        )
    reason = (
        f"{planting_units_per_ha:.0f} planting units/ha exceeds the census limit of "
        f"{census_max_units_per_ha:.0f}/ha"
    )
    if contiguous_cover_ha > area_min_cover_ha:
        reason += f", and the planting forms continuous cover over {contiguous_cover_ha:.2f} ha"
    return "area-based", reason + "."


def site_checks(
    preexisting_woody_cover_pct: float,
    cleared_in_last_10_years: bool,
    production_displaced: bool,
    has_non_carbon_revenue: bool,
    hypothetical: bool,
) -> list[Check]:
    """Applicability and additionality items that decide whether credits can
    be issued at all. Quantification alone does not settle them."""
    checks = [
        Check(
            "Project activity increases vegetative cover",
            "pass" if preexisting_woody_cover_pct < 10 else "fail",
            f"Scenario assumes {preexisting_woody_cover_pct:.0f} % woody cover at the start."
            + (" The real parcel is an established garden, so this holds only for the what-if." if hypothetical else ""),
        ),
        Check(
            "No clearing of woody vegetation in the 10 years before the start",
            "fail" if cleared_in_last_10_years else "pass",
            "Assumed in the scenario; a real project shows it with a 10-year stocking-index record.",
        ),
        Check(
            "Leakage from displaced production (VMD0054)",
            "not shown" if production_displaced else "pass",
            "Production displaced: leakage must be quantified." if production_displaced
            else "Fallow land: no production displaced, so leakage is zero.",
        ),
        Check(
            "Additionality step 1: regulatory surplus",
            "not shown",
            "Needs a check that no law or programme requires the planting.",
        ),
        Check(
            "Additionality step 2: performance benchmark",
            "not shown",
            "Needs at least 30 project plots and matched control plots from satellite data, re-tested at every verification.",
        ),
        Check(
            "Additionality step 3: investment barrier",
            "not shown" if has_non_carbon_revenue else "pass",
            "Arecanut earns nut revenue, so an investment analysis is required. A profitable cash crop is hard to show as dependent on carbon finance."
            if has_non_carbon_revenue else "No revenue other than carbon credits.",
        ),
    ]
    return checks
