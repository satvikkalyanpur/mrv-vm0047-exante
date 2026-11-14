"""Leakage from displaced farm production. VMD0054, Steps 1 to 5.

Planting trees on land that was growing food pushes that production
elsewhere, and some of it lands on newly cleared land. VMD0054 turns the
displaced tonnes into hectares of new land and then into emissions.

This is the single-commodity form of the module. VMD0054 assesses leakage for
five years after the project start; how the annual terms accumulate must be
confirmed against the module text before use in a real project description.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Leakage:
    foregone_production_t: float
    new_land_ha: float
    emissions_tco2e: float | None  # None where no carbon stock for the new land was supplied


def displaced_new_land_ha(
    foregone_production_t: float,
    yield_on_new_land_t_per_ha: float,
    mitigation_t: float = 0.0,
    supply_increase_share: float = 0.75,
    new_land_share: float = 0.40,
) -> float:
    """VMD0054 Eqs. (5) and (6).

    l   = max(FP - LM, 0)
    INL = l * IS * NL / y
    """
    subject = max(foregone_production_t - mitigation_t, 0.0)
    return subject * supply_increase_share * new_land_share / yield_on_new_land_t_per_ha


def leakage(
    area_displaced_ha: float,
    historical_yield_t_per_ha: float,
    monitored_production_t: float = 0.0,
    mitigation_t: float = 0.0,
    yield_on_new_land_t_per_ha: float | None = None,
    carbon_stock_new_land_tc_per_ha: float | None = None,
    supply_increase_share: float = 0.75,
    new_land_share: float = 0.40,
    co2_per_c: float = 44 / 12,
) -> Leakage:
    """Foregone production (Eq. 2), new land (Eqs. 5-7) and emissions (Eq. 10).

    LK = AL * CS * 44/12, where CS is the carbon lost per hectare of new land.
    VMD0054 assumes that land is forest with complete loss of biomass.
    """
    baseline_production = area_displaced_ha * historical_yield_t_per_ha
    foregone = max(baseline_production - monitored_production_t, 0.0)
    y = yield_on_new_land_t_per_ha or historical_yield_t_per_ha
    new_land = displaced_new_land_ha(foregone, y, mitigation_t, supply_increase_share, new_land_share)
    emissions = None
    if carbon_stock_new_land_tc_per_ha is not None:
        emissions = new_land * carbon_stock_new_land_tc_per_ha * co2_per_c
    return Leakage(foregone, new_land, emissions)


def breakeven_carbon_stock_tc_per_ha(removals_tco2e: float, new_land_ha: float, co2_per_c: float = 44 / 12) -> float:
    """Carbon stock on the displaced-to land at which leakage cancels the
    removals entirely."""
    if new_land_ha <= 0:
        return float("inf")
    return removals_tco2e / (new_land_ha * co2_per_c)
