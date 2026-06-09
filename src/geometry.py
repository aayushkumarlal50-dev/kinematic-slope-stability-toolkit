import numpy as np
EPS = 1e-9

def unit(v):
    if v is None:       
        return None
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < EPS:
        return None
    return v / n

def length(v):
    v = np.asarray(v, dtype=float)
    return float(np.linalg.norm(v))

def plane_normal(dd, dip):
    """Return lower-hemisphere pole/normal from dip direction and dip."""
    a = np.deg2rad(dip)
    b = np.deg2rad(dd % 360.0)
    return unit([np.sin(a) * np.sin(b), np.sin(a) * np.cos(b), np.cos(a)])

def strike(dd):
    return (dd - 90.0) % 360.0

def acute_angle(v1, v2):
    v1, v2 = unit(v1), unit(v2)
    if v1 is None or v2 is None:
        return np.nan
    return np.degrees(np.arccos(np.clip(abs(np.dot(v1, v2)), -1.0, 1.0)))

def inter_line(n1, n2):
    """Intersection line of two planes (lower hemisphere)."""
    if n1 is None or n2 is None:
        return None
    v = unit(np.cross(n1, n2))
    if v is None:
        return None
    return v if v[2] <= 0 else -v

def plunge_bearing(v):
    """Return plunge and trend/bearing for a line vector."""
    v = unit(v)
    if v is None:
        return np.nan, np.nan
    if v[2] > 0:
        v = -v
    h = np.hypot(v[0], v[1])
    plunge = np.degrees(np.arctan2(-v[2], h))
    bearing = 0.0 if h < EPS else (np.degrees(np.arctan2(v[0], v[1])) % 360.0)
    return plunge, bearing

def plunge_trend_to_lonlat(plunges, trends):
    import mplstereonet.stereonet_math as smath
    strikes = np.array(trends) + 90
    dips = 90 - np.array(plunges)
    return smath.pole(strikes, dips)

def fmt(x, d=3):
    return "n/a" if not np.isfinite(x) else f"{x:.{d}f}"

def vec_str(v):
    return "n/a" if v is None or np.any(~np.isfinite(v)) else np.array2string(np.asarray(v), precision=4, suppress_small=True)