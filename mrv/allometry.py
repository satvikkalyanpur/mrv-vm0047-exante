"""Biomass equations for Areca catechu.

VM0047 asks for species equations from the same region first, then wider ones.
Three published equations are available for areca palm. None is from
Karnataka, so the nearest is the Indian one (Das et al. 2021).

All functions take stem diameter D in cm and total palm height H in m and
return dry biomass per palm in kg.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Das et al. 2021 calibration range (40 destructively sampled palms, Assam).
DAS_D_RANGE_CM = (6.37, 16.5)
DAS_H_RANGE_M = (6.66, 18.68)
# Log-bias correction factors reported in Das et al. 2021, Table 3.
DAS_CF_M2 = 1.074
DAS_CF_M3 = 1.074

EQUATIONS = ("prayogo2018", "das2021_m2", "das2021_m3")


def prayogo2018_agb(d_cm: float, h_m: float) -> float:
    """Above-ground biomass, kg per palm.

    AGB = 0.03883 * H * D^1.2 (R2 = 0.96).
    Prayogo et al. 2018, AGRIVITA 40(3): 381-389, doi:10.17503/agrivita.v40i3.1124.
    Developed in Indonesia. This is the equation used in the proof of concept.
    """
    return 0.03883 * h_m * d_cm ** 1.2


def das2021_m2_total(h_m: float, apply_cf: bool = True) -> float:
    """Total (above + below ground) biomass, kg per palm, from height only.

    ln(Y) = -0.496 + 1.616 ln(H), adj. R2 = 0.858.
    Das et al. 2021, Environ. Sustain. Indic. 10: 100115,
    doi:10.1016/j.indic.2021.100115.
    """
    y = math.exp(-0.496 + 1.616 * math.log(h_m))
    return y * DAS_CF_M2 if apply_cf else y


def das2021_m3_total(d_cm: float, h_m: float, apply_cf: bool = True) -> float:
    """Total (above + below ground) biomass, kg per palm, from D^2 * H.

    ln(Y) = -1.853 + 0.728 ln(D^2 H), adj. R2 = 0.859. The authors' preferred
    model. Same source as das2021_m2_total.
    """
    y = math.exp(-1.853 + 0.728 * math.log(d_cm ** 2 * h_m))
    return y * DAS_CF_M3 if apply_cf else y


@dataclass(frozen=True)
class PalmBiomass:
    agb_kg: float
    bgb_kg: float
    in_calibration_range: bool | None  # None where the range is not recorded here

    @property
    def total_kg(self) -> float:
        return self.agb_kg + self.bgb_kg


def _in_das_range(d_cm: float | None, h_m: float) -> bool:
    h_ok = DAS_H_RANGE_M[0] <= h_m <= DAS_H_RANGE_M[1]
    if d_cm is None:
        return h_ok
    return h_ok and DAS_D_RANGE_CM[0] <= d_cm <= DAS_D_RANGE_CM[1]


def palm_biomass(equation: str, d_cm: float, h_m: float, root_to_shoot: float) -> PalmBiomass:
    """Above- and below-ground dry biomass of one palm.

    Prayogo gives above-ground biomass; below ground is AGB * R (VM0047 Eq. 4).
    The Das models give total biomass, split here with the same R so that
    AGB * (1 + R) reproduces the modelled total.
    """
    if h_m <= 0:
        return PalmBiomass(0.0, 0.0, False if equation != "prayogo2018" else None)
    if equation == "prayogo2018":
        agb = prayogo2018_agb(d_cm, h_m)
        return PalmBiomass(agb, agb * root_to_shoot, None)
    if equation == "das2021_m2":
        total = das2021_m2_total(h_m)
        agb = total / (1 + root_to_shoot)
        return PalmBiomass(agb, total - agb, _in_das_range(None, h_m))
    if equation == "das2021_m3":
        total = das2021_m3_total(d_cm, h_m)
        agb = total / (1 + root_to_shoot)
        return PalmBiomass(agb, total - agb, _in_das_range(d_cm, h_m))
    raise ValueError(f"Unknown equation '{equation}'. Choose from {EQUATIONS}.")
