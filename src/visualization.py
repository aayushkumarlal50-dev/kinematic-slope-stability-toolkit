import numpy as np
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import mplstereonet

from .geometry import plunge_bearing, plunge_trend_to_lonlat, strike

def compass(ax):
    for label, x, y, ha, va in [
        ("N", 0.50, 1.09, "center", "bottom"),
        ("S", 0.50, -0.09, "center", "top"),
        ("E", 1.09, 0.50, "left", "center"),
        ("W", -0.09, 0.50, "right", "center"),
    ]:
        ax.annotate(
            label,
            xy=(x, y),
            xycoords="axes fraction",
            ha=ha,
            va=va,
            fontsize=11,
            fontweight="bold",
            color="#37474F",
            clip_on=False,
        )

def apply_common_style(fig, ax):
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.grid(True, color="#B0BEC5", linestyle=":", alpha=0.5)
    compass(ax)
    return fig, ax

def draw_boundary_segments(ax, slope_dd, lat_limit, color, visible):
    if not visible:
        return
    for offset in (-lat_limit, lat_limit):
        trend = (slope_dd + 180 + offset) % 360
        lon, lat = plunge_trend_to_lonlat(np.linspace(0, 90, 50), np.full(50, trend))
        ax.plot(lon, lat, color=color, linewidth=2.2, zorder=3)

def draw_critical_zone_plane(ax, slope_dd, slope_dip, phi, lat_limit, color, visible):
    if not visible:
        return

    dds = np.linspace(slope_dd - lat_limit, slope_dd + lat_limit, 200)
    valid_dds, valid_dips = [], []

    for dd in dds:
        val = np.tan(np.radians(slope_dip)) * np.cos(np.radians(dd - slope_dd))
        if val <= 0:
            continue
        app_dip = np.degrees(np.arctan(val))
        if app_dip > phi:
            valid_dds.append(dd)
            valid_dips.append(app_dip)

    if not valid_dds:
        return

    poly_dds = np.concatenate([valid_dds, valid_dds[::-1]])
    poly_dips = np.concatenate([valid_dips, np.full(len(valid_dds), phi)])
    lon, lat = mplstereonet.stereonet_math.pole(np.array(poly_dds) - 90, np.array(poly_dips))
    ax.fill(lon, lat, facecolor=color, alpha=0.3, hatch="///", edgecolor=color, linewidth=1.5, zorder=2)

def draw_lateral_limits_toppling(ax, center_trend, lat_limit, color, visible):
    if not visible:
        return
    for offset in (-lat_limit, lat_limit):
        trend = (center_trend + offset) % 360
        lon, lat = plunge_trend_to_lonlat(np.linspace(0, 90, 50), np.full(50, trend))
        ax.plot(lon, lat, color=color, linewidth=2, zorder=3)

def draw_critical_zone_toppling(ax, slope_dd, slope_dip, phi_d, lat_limit, color, visible):
    if not visible or slope_dip <= phi_d:
        return

    trends = np.linspace(slope_dd - lat_limit, slope_dd + lat_limit, 100)
    in_plunge, out_plunge, tr = [], [], []
    slip_dip = slope_dip - phi_d

    for trend in trends:
        val = np.tan(np.radians(slip_dip)) * np.cos(np.radians(trend - slope_dd))
        if val > 0:
            in_plunge.append(np.degrees(np.arctan(val)))
            out_plunge.append(0.0)
            tr.append(trend)

    if tr:
        poly_trends = np.concatenate([tr, tr[::-1]])
        poly_plunges = np.concatenate([in_plunge, out_plunge[::-1]])
        lon, lat = plunge_trend_to_lonlat(poly_plunges, poly_trends)
        ax.fill(lon, lat, color=color, alpha=0.3, hatch=r"\\", edgecolor=color, linewidth=1.2, zorder=2)

def plot_plane_stereonet(
    slope_dd,
    slope_dip,
    phi,
    lat_limit,
    toggles,
    colors,
    joint_data,
):
    fig, ax = mplstereonet.subplots(figsize=(6.4, 6.4))
    if toggles["friction"]:
        ax.cone(90, 0, phi, facecolor="none", edgecolor=colors["friction"], linewidth=1.8, linestyle="--")
    if toggles["slope"]:
        ax.plane(strike(slope_dd), slope_dip, color=colors["slope"], linewidth=2.5)
    if toggles["daylight"]:
        x_deg = np.linspace(0, 360, 720)
        val = np.tan(np.radians(slope_dip)) * np.cos(np.radians(x_deg))
        beta = np.degrees(np.arctan(np.abs(val)))
        alpha = np.where(val >= 0, slope_dd + x_deg, slope_dd + x_deg + 180) % 360
        ax.pole(alpha - 90, beta, color=colors["daylight"], markersize=2.5)

    draw_boundary_segments(ax, slope_dd, lat_limit, colors["bounds"], toggles["bounds"])
    draw_critical_zone_plane(ax, slope_dd, slope_dip, phi, lat_limit, colors["critical"], toggles["critical"])

    for p in joint_data:
        s = strike(p["dd"])
        if p["show_line"]:
            ax.plane(s, p["dip"], color=p["color"], linewidth=1.8, alpha=0.9)
        if p["show_pole"]:
            ax.pole(s, p["dip"], color=p["color"], markersize=8, markeredgecolor="#000000", markeredgewidth=0.7)

    apply_common_style(fig, ax)
    return fig, ax

def plot_toppling_stereonet(
    slope_dd,
    slope_dip,
    phi_d,
    lat_limit,
    toggles,
    colors,
    joint_data,
):
    fig, ax = mplstereonet.subplots(figsize=(6.4, 6.4))
    if toggles["slip"]:
        ax.plane(strike(slope_dd), slope_dip - phi_d, color=colors["slip"], linewidth=1.8, linestyle="dashdot", zorder=4)
    if toggles["slope"]:
        ax.plane(strike(slope_dd), slope_dip, color=colors["slope"], linewidth=2.5, zorder=4)

    draw_lateral_limits_toppling(ax, slope_dd, lat_limit, colors["bounds_t"], toggles["bounds_t"])
    draw_critical_zone_toppling(ax, slope_dd, slope_dip, phi_d, lat_limit, colors["critical_t"], toggles["critical_t"])

    for p in joint_data:
        s = strike(p["dd"])
        if p["line"]:
            ax.plane(s, p["dip"], color=p["color"], linewidth=1.5, alpha=0.8, zorder=5)
        if p["pole"]:
            ax.pole(s, p["dip"], color=p["color"], markersize=8, markeredgecolor="#000000", markeredgewidth=0.7, zorder=6)

    apply_common_style(fig, ax)
    return fig, ax

def plot_wedge_stereonet(
    a_dd,
    a_dip,
    b_dd,
    b_dip,
    c_dd,
    c_dip,
    s_dd,
    s_dip,
    lines,
):
    fig, ax = mplstereonet.subplots(figsize=(7.0, 7.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plane(strike(a_dd), a_dip, color="#1f77b4", lw=2.0, zorder=4)
    ax.plane(strike(b_dd), b_dip, color="#ff7f0e", lw=2.0, zorder=4)
    ax.plane(strike(c_dd), c_dip, color="#6a3d9a", lw=1.6, ls="--", zorder=3)
    ax.plane(strike(s_dd), s_dip, color="#222222", lw=2.2, zorder=5)

    for key, color in [("A", "#1f77b4"), ("B", "#ff7f0e"), ("crest", "#6a3d9a"), ("slope", "#222222")]:
        dd, dip = {
            "A": (a_dd, a_dip),
            "B": (b_dd, b_dip),
            "crest": (c_dd, c_dip),
            "slope": (s_dd, s_dip),
        }[key]
        ax.pole(strike(dd), dip, marker="o", ms=7, mec="#000000", mew=0.5, mfc=color, zorder=6)

    intersections = {
        "A∩B": (lines["A∩B"], "#00FF62"),
        "Crest∩Slope": (lines["crest∩slope"], "#999999"),
        "A∩Crest": (lines["A∩crest"], "#17becf"),
        "B∩Crest": (lines["B∩crest"], "#bcbd22"),
        "A∩Slope": (lines["A∩slope"], "#d62728"),
        "B∩Slope": (lines["B∩slope"], "#8c564b"),
    }

    for _, (v, color) in intersections.items():
        if v is not None:
            pl, br = plunge_bearing(v)
            ax.line(pl, br, marker="o", ms=6, color=color, zorder=7)

    apply_common_style(fig, ax)
    return fig, ax