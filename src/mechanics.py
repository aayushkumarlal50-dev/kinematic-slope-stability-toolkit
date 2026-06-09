import numpy as np
from .geometry import plunge_bearing

def check_plane_failure(dd, dip, slope_dd, slope_dip, phi, lat_limit):
    """Kinematic plane failure check."""
    dd_diff = abs((dd - slope_dd + 180) % 360 - 180)

    if dd_diff >= lat_limit:
        return False

    val = np.tan(np.radians(slope_dip)) * np.cos(np.radians(dd - slope_dd))

    if val <= 0:
        return False

    app_slope_dip = np.degrees(np.arctan(val))
    return phi <= dip < app_slope_dip

def check_toppling_failure(dd, dip, slope_dd, slope_dip, phi_d, lat_limit):
    """Kinematic toppling check."""
    if abs((dd - (slope_dd + 180) + 180) % 360 - 180) >= lat_limit:
        return False

    if slope_dip <= phi_d:
        return False

    pole_trend = (dd - 180) % 360
    val = (
        np.tan(np.radians(slope_dip - phi_d))
        * np.cos(np.radians(pole_trend - slope_dd))
    )
    return (90 - dip <= np.degrees(np.arctan(val))) if val > 0 else False

def check_wedge_failure(
    u_ab,
    slope_dd,
    slope_dip,
    phi,
    a_dd=None,
    b_dd=None,
):
    EPS = 1e-9

    def wrap360(angle):
        return float(angle) % 360.0

    def signed_diff(a, b):
        """Shortest signed angular difference (a - b) in [-180, 180]."""
        return ((float(a) - float(b) + 180.0) % 360.0) - 180.0

    def in_arc(angle, start, end):
        """Return True if angle lies on the clockwise arc from start to end."""
        angle = wrap360(angle)
        start = wrap360(start)
        end = wrap360(end)

        span = (end - start) % 360.0
        pos = (angle - start) % 360.0

        return False if span <= EPS else pos <= span + EPS

    def choose_wedge_arc(a, b, ref):
        """
        Choose the arc (a→b or b→a) that is consistent
        with the reference azimuth.
        """
        ab_contains = in_arc(ref, a, b)
        ba_contains = in_arc(ref, b, a)

        if ab_contains and not ba_contains:
            return a, b

        if ba_contains and not ab_contains:
            return b, a

        return (a, b) if ((b - a) % 360.0) <= 180.0 else (b, a)

    if u_ab is None:
        return False

    try:
        pl, tr = plunge_bearing(u_ab)

        pl = float(pl)
        tr = float(tr)
        slope_dd = float(slope_dd)
        slope_dip = float(slope_dip)
        phi = float(phi)

    except Exception:
        return False

    if not np.all(np.isfinite([pl, tr, slope_dd, slope_dip, phi])):
        return False

    slope_dd = wrap360(slope_dd)
    tr = wrap360(tr)

    if not (0.0 <= slope_dip <= 90.0 and 0.0 <= phi <= 90.0):
        return False

    if not (0.0 < pl < 90.0):
        return False

    if slope_dip <= phi + EPS:
        return False

    if a_dd is not None and b_dd is not None:
        a_dd = wrap360(a_dd)
        b_dd = wrap360(b_dd)

        sep = (b_dd - a_dd) % 360.0

        if sep <= EPS or abs(sep - 180.0) <= EPS:
            return False

        arc_start, arc_end = choose_wedge_arc(a_dd, b_dd, slope_dd)

        if not in_arc(tr, arc_start, arc_end):
            return False

    to_slope = signed_diff(tr, slope_dd)

    if abs(to_slope) > 90.0 + EPS:
        return False

    slope_dip_eff = np.clip(slope_dip, 0.0, 89.999999)

    apparent_dip = np.degrees(
        np.arctan(
            np.tan(np.radians(slope_dip_eff))
            * np.cos(np.radians(to_slope))
        )
    )

    if apparent_dip <= EPS:
        return False

    return phi + EPS < pl < apparent_dip - EPS