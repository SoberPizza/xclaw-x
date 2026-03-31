"""Humanization math utilities — used by BezierStrategy."""

import math
import random


def bezier_point(t: float, p0, p1, p2, p3):
    """Compute a point on a cubic Bezier curve at parameter t."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def lognormal_delay(median: float, sigma: float = 0.3, lo: float = 0.0, hi: float = float("inf")) -> float:
    """Sample a delay (seconds) from a lognormal distribution.

    *median* is the distribution median (=exp(mu)), *sigma* controls spread.
    Result is clamped to [lo, hi].
    """
    mu = math.log(median)
    return max(lo, min(hi, random.lognormvariate(mu, sigma)))


def asymmetric_ease(t: float, accel: float = 1.6, decel: float = 2.2) -> float:
    """Asymmetric ease-in-out: fast acceleration, long deceleration tail.

    Uses the generalised logistic sigmoid ``t^a / (t^a + (1-t)^b)``.
    With default params the deceleration phase is ~40% longer than acceleration,
    matching real human mouse movement velocity profiles.
    """
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    ta = t ** accel
    return ta / (ta + (1.0 - t) ** decel)
