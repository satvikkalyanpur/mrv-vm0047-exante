"""From carbon stock change to issuable credits. VM0047 Eq. (30) plus the buffer."""
from __future__ import annotations

from typing import Sequence


def net_removals_cumulative(
    stock_change_tco2e: float,
    performance_benchmark: float,
    uncertainty: float,
    leakage_tco2e: float = 0.0,
    project_emissions_tco2e: float = 0.0,
) -> float:
    """The bracket in VM0047 Eq. (30), cumulative since the project start:

        dC_WP,t * (1 - PB_t) * (1 - UNC_t) - LK_t - PE_t

    Removals for a period are this value at the end of the period minus its
    value at the start.
    """
    return (
        stock_change_tco2e * (1 - performance_benchmark) * (1 - uncertainty)
        - leakage_tco2e
        - project_emissions_tco2e
    )


def schedule(
    years: Sequence[float],
    stock_change_tco2e: Sequence[float],
    performance_benchmark: float,
    uncertainty: float,
    buffer_fraction: float,
    leakage_tco2e: float = 0.0,
    project_emissions_tco2e: float = 0.0,
    verification_years: Sequence[int] = (),
) -> list[dict]:
    """Year-by-year accounting.

    Leakage and project emissions are treated as incurred in the first year
    and carried from then on. Buffer credits are a share of the carbon stock
    change after the benchmark and uncertainty deductions, before leakage.
    Credits are issued only at verification, and never as a negative number:
    a shortfall is carried forward.
    """
    rows, prev_net, prev_creditable_stock, vcu_cum, issued_cum = [], 0.0, 0.0, 0.0, 0.0
    for year, dc in zip(years, stock_change_tco2e):
        creditable_stock = dc * (1 - performance_benchmark) * (1 - uncertainty)
        charged = year > 0
        net = net_removals_cumulative(
            dc, performance_benchmark, uncertainty,
            leakage_tco2e if charged else 0.0,
            project_emissions_tco2e if charged else 0.0,
        )
        removals_year = net - prev_net
        buffer_year = buffer_fraction * (creditable_stock - prev_creditable_stock)
        vcu_year = removals_year - buffer_year
        vcu_cum += vcu_year
        issued_now = 0.0
        if year in verification_years:
            issued_now = max(0.0, vcu_cum - issued_cum)
            issued_cum += issued_now
        rows.append({
            "year": year,
            "stock_change_tco2e": dc,
            "after_benchmark_and_uncertainty_tco2e": creditable_stock,
            "net_removals_cumulative_tco2e": net,
            "removals_in_year_tco2e": removals_year,
            "buffer_in_year_tco2e": buffer_year,
            "credits_accrued_in_year": vcu_year,
            "credits_accrued_cumulative": vcu_cum,
            "credits_issued_at_verification": issued_now,
            "credits_issued_cumulative": issued_cum,
        })
        prev_net, prev_creditable_stock = net, creditable_stock
    return rows
