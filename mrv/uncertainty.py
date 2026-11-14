"""Uncertainty deduction. VM0047 Section 8.4 (ex post) and Section 8.6 (ex ante)."""
from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Sequence

from scipy import stats


def ci_halfwidth_fraction(values: Sequence[float], confidence: float = 0.90) -> float:
    """Half-width of the two-sided confidence interval of the mean, as a
    fraction of the mean. This is the form VM0047 uses for U."""
    n = len(values)
    if n < 2:
        raise ValueError("Need at least two values to estimate uncertainty.")
    m = mean(values)
    if m == 0:
        raise ValueError("Mean is zero; relative uncertainty is undefined.")
    se = stdev(values) / math.sqrt(n)
    t_crit = stats.t.ppf(1 - (1 - confidence) / 2, n - 1)
    return abs(t_crit * se / m)


def unc_exante(u: float, minimum: float = 0.10) -> float:
    """Ex-ante deduction.

    VM0047 Section 8.6 sets a floor of 10 % and lets the proponent pick more.
    This engine takes the larger of the floor and the estimated uncertainty.
    """
    return min(1.0, max(minimum, u))


def unc_expost_area(
    u_and_c_at_start: Sequence[tuple[float, float]],
    u_and_c_at_t: Sequence[tuple[float, float]],
    stock_change: float,
    allowance: float = 0.10,
) -> float:
    """Ex-post deduction, area-based approach. VM0047 Eq. (27).

    UNC = min(1, max(0, sqrt(sum((U*C)^2 at t=0) + sum((U*C)^2 at t)) / dC - 10 %))

    Each pair is (U, C): the pool's 90 % CI half-width as a fraction of its
    mean, and the pool's carbon stock. The first 10 points of uncertainty are
    free; only the excess is deducted.
    """
    if stock_change <= 0:
        return 1.0
    s = sum((u * c) ** 2 for u, c in u_and_c_at_start) + sum((u * c) ** 2 for u, c in u_and_c_at_t)
    return min(1.0, max(0.0, math.sqrt(s) / stock_change - allowance))


def unc_expost_census(u_pool: float, u_mortality: float, allowance: float = 0.10) -> float:
    """Ex-post deduction, census-based approach. VM0047 Eq. (28)."""
    return min(1.0, max(0.0, math.sqrt(u_pool ** 2 + u_mortality ** 2) - allowance))


def creditable(ci_halfwidth: float, limit: float = 1.0) -> bool:
    """No removals may be claimed where the CI half-width exceeds 100 %."""
    return ci_halfwidth <= limit
