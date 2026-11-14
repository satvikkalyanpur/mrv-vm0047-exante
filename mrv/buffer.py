"""Non-permanence buffer. VCS AFOLU Non-Permanence Risk Tool v4.2."""
from __future__ import annotations


class RiskAnalysisFailed(ValueError):
    """The overall risk rating is above the limit; the project cannot issue."""


def buffer_fraction(rating: float, minimum_rating: float = 12, fail_overall: float = 60) -> float:
    """Share of credits withheld in the pooled buffer account.

    The rating converts straight to a percentage (a rating of 20 withholds
    20 %). It may not be below 12 whatever the tool calculates, and a rating
    above 60 fails the risk analysis.
    """
    if rating > fail_overall:
        raise RiskAnalysisFailed(f"Overall risk rating {rating} exceeds {fail_overall}.")
    return max(rating, minimum_rating) / 100.0
