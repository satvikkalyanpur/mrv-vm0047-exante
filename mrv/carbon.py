"""Carbon stocks and stock change. VM0047 Eqs. (1), (3) and (4)."""
from __future__ import annotations

from .allometry import palm_biomass


def palms_per_ha(spacing_m: float, survival_fraction: float = 1.0) -> float:
    """Square planting: one palm per spacing^2 square metres."""
    return 10_000.0 / spacing_m ** 2 * survival_fraction


def height_at(age_years: float, anchor_height_m: float, anchor_age_years: float) -> float:
    """Growth model: height rises linearly from zero at planting to the height
    measured at the anchor age, and is held there afterwards.

    Ignoring the seedling's height at planting keeps the early years low.
    """
    if age_years <= 0:
        return 0.0
    return anchor_height_m * min(age_years, anchor_age_years) / anchor_age_years


def woody_carbon_t_per_ha(
    equation: str,
    d_cm: float,
    h_m: float,
    n_per_ha: float,
    root_to_shoot: float,
    carbon_fraction: float,
) -> float:
    """Woody biomass carbon stock, t C per ha.

    C_woody = C_woody-AB * (1 + R)   (VM0047 Eq. 4)
    """
    palm = palm_biomass(equation, d_cm, h_m, root_to_shoot)
    c_ab = palm.agb_kg * n_per_ha / 1000.0 * carbon_fraction
    return c_ab * (1 + root_to_shoot)


def stock_change_tco2e(
    area_ha: float, c_t: float, c_0: float, co2_per_c: float
) -> float:
    """Project carbon stock change since the start, t CO2e.

    dC_woody = A * (C_t - C_0)        (VM0047 Eq. 3)
    dC_WP    = dC_woody * 44/12       (VM0047 Eq. 1, woody pools only)
    """
    return area_ha * (c_t - c_0) * co2_per_c
