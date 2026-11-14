"""Performance benchmark for the area-based approach. VM0047 Appendix 1.

The benchmark compares the trend of a remote-sensing stocking index (SI) in
project plots with the trend in matched control plots outside the project.
Only growth beyond the controls is credited.

These functions take SI time series that have already been extracted. They
are exercised by the tests and are ready for the monitoring phase; the
ex-ante scenario in this repository takes the benchmark as an input because a
hypothetical planting has no SI history to match on.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from scipy import stats


def standardised_difference(project: Sequence[float], control: Sequence[float]) -> float:
    """Match quality for one covariate. VM0047 Eq. (A2).

    SDM = |mean_wp - mean_bsl| / sqrt((var_wp + var_bsl) / 2); valid where <= 0.25.
    """
    def _mean(x): return sum(x) / len(x)
    def _var(x):
        m = _mean(x)
        return sum((v - m) ** 2 for v in x) / (len(x) - 1)
    pooled = math.sqrt((_var(project) + _var(control)) / 2)
    if pooled == 0:
        return 0.0 if _mean(project) == _mean(control) else math.inf
    return abs(_mean(project) - _mean(control)) / pooled


@dataclass(frozen=True)
class Trend:
    slope: float
    se: float
    p_value: float
    n: int


def weighted_trend(t: Sequence[float], si: Sequence[float], w: Sequence[float] | None = None) -> Trend:
    """Slope of a weighted linear regression of SI on time, with its standard
    error and two-sided P value. VM0047 needs at least three time steps."""
    n = len(t)
    if n < 3 or len(si) != n:
        raise ValueError("Need at least three matching time steps.")
    w = list(w) if w is not None else [1.0] * n
    sw = sum(w)
    tb = sum(wi * ti for wi, ti in zip(w, t)) / sw
    yb = sum(wi * yi for wi, yi in zip(w, si)) / sw
    sxx = sum(wi * (ti - tb) ** 2 for wi, ti in zip(w, t))
    sxy = sum(wi * (ti - tb) * (yi - yb) for wi, ti, yi in zip(w, t, si))
    slope = sxy / sxx
    resid = sum(wi * (yi - yb - slope * (ti - tb)) ** 2 for wi, ti, yi in zip(w, t, si))
    se = math.sqrt(resid / (n - 2) / sxx) if n > 2 else math.inf
    if se == 0:
        p = 0.0 if slope != 0 else 1.0
    else:
        p = 2 * (1 - stats.t.cdf(abs(slope / se), n - 2))
    return Trend(slope, se, p, n)


def z_statistic(project: Trend, control: Trend) -> float:
    """VM0047 Eq. (A5): Z = (dSI_wp - dSI_control) / sqrt(SE_wp^2 + SE_control^2)."""
    denom = math.sqrt(project.se ** 2 + control.se ** 2)
    if denom == 0:
        return math.inf if project.slope != control.slope else 0.0
    return (project.slope - control.slope) / denom


def performance_benchmark(
    project: Trend,
    control: Trend,
    z_critical: float = 1.96,
    control_p_max: float = 0.05,
) -> float:
    """VM0047 Eq. (A6). Returns PB in [0, 1]; credited share is (1 - PB).

    - Slopes not significantly different: PB = 1 (nothing is credited).
    - Control slope negative or not significant: treated as zero, so PB = 0.
    - Otherwise PB = dSI_control / dSI_wp.

    The methodology does not state a cap. A ratio above 1 would mean controls
    grew faster than the project, so it is capped at 1 here.
    """
    if abs(z_statistic(project, control)) < z_critical:
        return 1.0
    if control.slope <= 0 or control.p_value > control_p_max:
        return 0.0
    if project.slope <= 0:
        return 1.0
    return min(1.0, control.slope / project.slope)
