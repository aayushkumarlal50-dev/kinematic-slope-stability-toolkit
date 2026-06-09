import io
import numpy as np
import streamlit as st
from pathlib import Path

from src.geometry import (
    acute_angle,
    fmt,
    plunge_bearing,
    strike,
    vec_str,
)

from src.mechanics import (
    check_plane_failure,
    check_toppling_failure,
    check_wedge_failure,
)

from src.tetrahedron_logic import tetrahedron_geometry

from src.visualization import (
    plot_plane_stereonet,
    plot_toppling_stereonet,
    plot_wedge_stereonet,
)

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

st.set_page_config(page_title="Kinematic Slope Stability Analyzer", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-size: 1.85rem !important; margin-bottom: 0.2rem; }
    h2, h3 { font-size: 1.15rem !important; margin-top: 0.35rem; margin-bottom: 0.25rem; }
    div[data-testid="stMetric"] { padding: 0.25rem 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; padding: 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "plane_joints" not in st.session_state:
    st.session_state.plane_joints = []
if "toppling_joints" not in st.session_state:
    st.session_state.toppling_joints = []

def render_mechanism_panel(image_name, title, explanation, legend_lines=None):
    st.markdown(f"**{title}**")
    image_path = ASSET_DIR / image_name
    st.image(str(image_path), width='stretch')
    st.caption(explanation)

    if legend_lines:
        st.markdown("**Legend**")
        for item in legend_lines:
            st.markdown(item, unsafe_allow_html=True)

st.title("Kinematic Slope Stability Toolkit")
st.caption("Interactive stereonet visualization and kinematic analysis for rock slope engineering.")
st.divider()

tab_plane, tab_toppling, tab_wedge = st.tabs(["Plane Failure", "Toppling Failure", "Wedge Failure"])

with tab_plane:
    col_controls, col_plot = st.columns([1.3, 1.7], gap="large")

    with col_controls:
        st.subheader("Slope Parameters")
        c1, c2, c3 = st.columns(3)
        slope_dd = c1.number_input("Face Dip direction (°)", 0, 360, 140, key="pf_slope_dd")
        slope_dip = c2.number_input("Face Dip angle (°)", 0, 90, 80, key="pf_slope_dip")
        phi = c3.number_input("Friction angle (°)", 0, 90, 35, key="pf_phi")
        lat_limit = st.slider("Lateral limit (±°)", 0, 90, 20, key="pf_lat")

        with st.expander("Display controls", expanded=False):
            layers = [
                ("Slope Face", "slope", "#000000"),
                ("Pole Friction Circle", "friction", "#FF6600"),
                ("Daylight Envelope", "daylight", "#0073FF"),
                ("Lateral Limits", "bounds", "#6A1B9A"),
                ("Critical Zone", "critical", "#FF0000"),
            ]
            toggles, colors = {}, {}
            for name, key, default_color in layers:
                col_tgl, col_clr = st.columns([4, 1])
                toggles[key] = col_tgl.toggle(name, value=True, key=f"pf_t_{key}")
                colors[key] = col_clr.color_picker(name, default_color, key=f"pf_c_{key}", label_visibility="collapsed")

        st.divider()
        st.subheader("Add Joint Plane")
        c4, c5, c6 = st.columns([2, 2, 1])
        p_dd = c4.number_input("Dip direction (°)", 0, 360, 140, key="pf_new_dd")
        p_dip = c5.number_input("Dip angle (°)", 0, 90, 80, key="pf_new_dip")
        p_color = c6.color_picker("Color", "#1E88E5", key="pf_new_clr", label_visibility="collapsed")

        if st.button("Add joint plane", width='stretch', key="pf_add"):
            st.session_state.plane_joints.append({"dd": p_dd, "dip": p_dip, "show_line": True, "show_pole": True, "color": p_color})
            st.rerun()

        st.divider()
        st.subheader("Joint Log")
        if not st.session_state.plane_joints:
            st.caption("No joints added yet.")

        for i, p in enumerate(st.session_state.plane_joints):
            susceptible = check_plane_failure(p["dd"], p["dip"], slope_dd, slope_dip, phi, lat_limit)
            badge = "🔴 Fail" if susceptible else "🟢 Safe"

            row = st.columns([1.8, 1.0, 0.9, 0.9, 0.8, 0.7])
            row[0].markdown(f"**J{i+1}** {p['dd']}°/{p['dip']}°")
            row[1].markdown(f"**{badge}**")
            p["show_line"] = row[2].checkbox("Plane", value=p["show_line"], key=f"pf_line_{i}")
            p["show_pole"] = row[3].checkbox("Pole", value=p["show_pole"], key=f"pf_pole_{i}")
            p["color"] = row[4].color_picker("", value=p["color"], key=f"pf_pclr_{i}", label_visibility="collapsed")
            if row[5].button("✕", key=f"pf_del_{i}"):
                st.session_state.plane_joints.pop(i)
                st.rerun()

    with col_plot:
        st.subheader("Schmidt Equal-Area Stereonet")
        st.caption(f"Slope Face {slope_dd}/{slope_dip}° | φ = {phi}° | Lateral ±{lat_limit}°")

        plot_col, diagram_col = st.columns([1.65, 0.85], gap="medium")
        with plot_col:
            fig, ax = plot_plane_stereonet(slope_dd, slope_dip, phi, lat_limit, toggles, colors, st.session_state.plane_joints)
            st.pyplot(fig, width='content', bbox_inches="tight")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=250, bbox_inches="tight")
            st.download_button("Download stereonet (PNG)", buf.getvalue(), "plane_failure_analysis.png", "image/png", width='stretch')

        with diagram_col:
            render_mechanism_panel(
                "planar_mechanics.png",
                "Plane Failure Mechanism",
                "Discontinuity planes within the lateral limits, daylighting on the slope face can slide if shear strength is exceeded.",
                [
                    f"<span style='color:{colors['slope']}; font-weight:700;'>■</span> Slope Face Plane",
                    f"<span style='color:{colors['friction']}; font-weight:700;'>■</span> Pole Friction Circle",
                    f"<span style='color:{colors['daylight']}; font-weight:700;'>■</span> Daylight Envelope",
                    f"<span style='color:{colors['bounds']}; font-weight:700;'>■</span> Lateral Limits",
                    f"<span style='color:{colors['critical']}; font-weight:700;'>■</span> Critical Pole Vector Failure Zone",
                ],
                )

with tab_toppling:
    col_controls, col_plot = st.columns([1.3, 1.7], gap="large")
    with col_controls:
        st.subheader("Slope Parameters")
        c1, c2 = st.columns(2)
        slope_dd = c1.number_input("Face Dip direction (°)", 0, 360, 140, key="tp_slope_dd")
        slope_dip = c2.number_input("Face Dip angle (°)", 0, 90, 80, key="tp_slope_dip")
        c3, c4 = st.columns(2)
        phi_d = c3.number_input("Toppling Friction angle φ_d (°)", 0, 90, 32, key="tp_phi")
        lat_limit = c4.slider("Lateral limit (±°)", 0, 90, 20, key="tp_lat")

        with st.expander("Display controls", expanded=False):
            layers = [
                ("Slope face", "slope", "#000000"),
                ("Slip limit plane", "slip", "#00897B"),
                ("Lateral limits", "bounds_t", "#283593"),
                ("Critical zone", "critical_t", "#E53935"),
            ]
            toggles, colors = {}, {}
            for name, key, hex_val in layers:
                tgl_col, clr_col = st.columns([4, 1])
                toggles[key] = tgl_col.toggle(name, value=True, key=f"tp_t_{key}")
                colors[key] = clr_col.color_picker(name, hex_val, key=f"tp_c_{key}", label_visibility="collapsed")

        st.divider()
        st.subheader("Add Joint Plane")
        c5, c6, c7 = st.columns([2, 2, 1])
        p_dd = c5.number_input("Dip direction (°)", 0, 360, 315, key="tp_new_dd")
        p_dip = c6.number_input("Dip angle (°)", 0, 90, 75, key="tp_new_dip")
        p_color = c7.color_picker("Color", "#1E88E5", key="tp_new_clr", label_visibility="collapsed")

        if st.button("Add joint plane", width='stretch', key="tp_add"):
            st.session_state.toppling_joints.append({"dd": p_dd, "dip": p_dip, "line": True, "pole": True, "color": p_color})
            st.rerun()

        st.divider()
        st.subheader("Joint Log")
        if not st.session_state.toppling_joints:
            st.caption("No joints added yet.")

        for i, p in enumerate(st.session_state.toppling_joints):
            fail_t = check_toppling_failure(p["dd"], p["dip"], slope_dd, slope_dip, phi_d, lat_limit)
            badge = "🔴 Topple" if fail_t else "🟢 Safe"

            row = st.columns([1.7, 1.3, 0.8, 0.8, 0.8, 0.7])
            row[0].markdown(f"**J{i+1}** {p['dd']}°/{p['dip']}°")
            row[1].markdown(f"**{badge}**")
            p["line"] = row[2].checkbox("Plane", value=p["line"], key=f"tp_line_{i}")
            p["pole"] = row[3].checkbox("Pole", value=p["pole"], key=f"tp_pole_{i}")
            p["color"] = row[4].color_picker("", value=p["color"], key=f"tp_pclr_{i}", label_visibility="collapsed")
            if row[5].button("✕", key=f"tp_del_{i}"):
                st.session_state.toppling_joints.pop(i)
                st.rerun()

    with col_plot:
        st.subheader("Schmidt Equal-Area Stereonet")
        st.caption(f"Slope Face {slope_dd}/{slope_dip}° | φ_d = {phi_d}° | Lateral ±{lat_limit}°")

        plot_col, diagram_col = st.columns([1.65, 0.85], gap="medium")
        with plot_col:
            fig, ax = plot_toppling_stereonet(slope_dd, slope_dip, phi_d, lat_limit, toggles, colors, st.session_state.toppling_joints)
            st.pyplot(fig, width='content', bbox_inches="tight")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=250, bbox_inches="tight")
            st.download_button("Download stereonet (PNG)", buf.getvalue(), "toppling_failure_analysis.png", "image/png", width='stretch')

        with diagram_col:
            render_mechanism_panel(
                "toppling_mechanics.png",
                "Flexural Toppling Mechanism",
                "Blocks separated by steep discontinuities rotate and topple out of the slope when the slip limit is exceeded.",
                [
                    f"<span style='color:{colors['slope']}; font-weight:700;'>■</span> Slope Face Plane",
                    f"<span style='color:{colors['slip']}; font-weight:700;'>■</span> Slip Limit Plane",
                    f"<span style='color:{colors['bounds_t']}; font-weight:700;'>■</span> Lateral Limits",
                    f"<span style='color:{colors['critical_t']}; font-weight:700;'>■</span> Critical Pole Vector Toppling Zone",
                ],
            )

with tab_wedge:
    col_in, col_plot, col_out = st.columns([1.05, 2.05, 0.90], gap="large")

    with col_in:
        st.subheader("Wedge Parameters")
        st.caption("Define the two intersecting planes and the slope bounds.")

        a_dd = st.number_input("Plane A dip direction (°)", 0.0, 360.0, 330.0, 1.0, key="wg_a_dd")
        a_dip = st.number_input("Plane A dip angle (°)", 0.0, 90.0, 60.0, 1.0, key="wg_a_dip")

        st.divider()
        b_dd = st.number_input("Plane B dip direction (°)", 0.0, 360.0, 120.0, 1.0, key="wg_b_dd")
        b_dip = st.number_input("Plane B dip angle (°)", 0.0, 90.0, 60.0, 1.0, key="wg_b_dip")

        st.divider()
        s_dd = st.number_input("Slope face dip direction (°)", 0.0, 360.0, 45.0, 1.0, key="wg_s_dd")
        s_dip = st.number_input("Slope face dip angle (°)", 0.0, 90.0, 75.0, 1.0, key="wg_s_dip")
        phi_w = st.number_input("Maximum friction angle φ (°)", 0.0, 90.0, 30.0, 1.0, key="wg_phi")

        st.divider()
        c1, c2, c3 = st.columns(3)
        c_dd = c1.number_input("Crest plane dip direction (°)", 0.0, 360.0, 45.0, 1.0, key="wg_c_dd")
        c_dip = c2.number_input("Crest plane dip angle (°)", 0.0, 90.0, 0.0, 1.0, key="wg_c_dip")
        H = c3.number_input("Vertical wedge height H", 0.0, 1e9, 20.0, 1.0, key="wg_H")

    try:
        geo = tetrahedron_geometry(
            {"A": (a_dd, a_dip), "B": (b_dd, b_dip), "C": (c_dd, c_dip), "S": (s_dd, s_dip)},
            H
        )
        nA, nB, nC, nS = (geo["normals"][k] for k in "ABCS")

        lines = {
            "A∩B":         geo["lines"]["L5"],  # A ∩ B
            "crest∩slope": geo["lines"]["L6"],  # C ∩ S
            "A∩crest":     geo["lines"]["L1"],  # A ∩ C
            "A∩slope":     geo["lines"]["L2"],  # A ∩ S
            "B∩crest":     geo["lines"]["L3"],  # C ∩ B
            "B∩slope":     geo["lines"]["L4"],  # B ∩ S
        }
        u_ab = lines["A∩B"]
        u_cs = lines["crest∩slope"]

        line_ab_len  = geo["lengths_m"]["L5"]
        wedge_volume = geo["volume_m3"]
        br_ab, pl_ab = geo["trend_plunge"]["L5"]   # returns (trend, plunge)
        is_wedge_failing = check_wedge_failure(u_ab, s_dd, s_dip, phi_w, a_dd, b_dd)

    except ValueError as _geo_err:
        geo = None
        nA = nB = nC = nS = u_ab = u_cs = None
        lines = {k: None for k in ["A∩B", "crest∩slope", "A∩crest", "A∩slope", "B∩crest", "B∩slope"]}
        line_ab_len = wedge_volume = br_ab = pl_ab = float("nan")
        is_wedge_failing = False
        _geo_failed = str(_geo_err)

    planes = {
        "A":     (a_dd, a_dip, nA),
        "B":     (b_dd, b_dip, nB),
        "crest": (c_dd, c_dip, nC),
        "slope": (s_dd, s_dip, nS),
    }
    pairs = [("A", "B"), ("A", "crest"), ("A", "slope"), ("B", "crest"), ("B", "slope"), ("crest", "slope")]

    with col_plot:
        # Centered Header with HTML
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <h3 style="margin-bottom: 0.2rem;">Schmidt Equal-Area Stereonet</h3>
                <div style="color: #5F6368; font-size: 0.95rem; font-weight: 500;">
                    Slope Face {s_dd}/{s_dip}° | φ = {phi_w}°
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        fig, ax = plot_wedge_stereonet(a_dd, a_dip, b_dd, b_dip, c_dd, c_dip, s_dd, s_dip, lines)
        st.pyplot(fig, width='content', bbox_inches="tight")

        st.markdown(
            """
            <div style="
                margin-top: 0.55rem;
                padding-top: 0.5rem;
                border-top: 1px solid #D9E2EC;
                font-size: 0.84rem;
                line-height: 1.45;
            ">
                <div style="font-weight: 700; margin-bottom: 0.25rem;">Legend</div>
                <div style="font-size:14px; white-space:nowrap;">
                    <span style="color:#1f77b4;">■</span> Plane A&nbsp;&nbsp;&nbsp;
                    <span style="color:#ff7f0e;">■</span> Plane B&nbsp;&nbsp;&nbsp;
                    <span style="color:#00FF62;">■</span> Line of Intersection&nbsp;&nbsp;&nbsp;
                    <span style="color:#222222;">■</span> Slope Face&nbsp;&nbsp;&nbsp;
                    <span style="color:#6a3d9a;">■</span> Crest Plane
            </div>
            """,
            unsafe_allow_html=True,
        )

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        st.download_button("Download stereonet (PNG)", buf.getvalue(), "wedge_failure_analysis.png", "image/png", width='stretch')

        st.markdown("<div style='height:0.7rem;'></div>", unsafe_allow_html=True)
        render_mechanism_panel(
            "wedge_mechanics.png",
            "Wedge Failure Mechanism",
            "",  
            None,
        )
        
        st.markdown(
            """
            <div style="text-align: center; color: #5F6368; font-size: 0.86rem; margin-top: 0.5rem; margin-bottom: 1rem;">
                Intersection of two discontinuities forms a removable wedge.
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_out:
        if geo is None:
            st.warning(f"Geometry could not be computed: {_geo_failed}")
        st.markdown("#### Susceptibility Summary")

        if is_wedge_failing:
            st.markdown(
                """
                <div style="padding:0.65rem 0.8rem; border:1px solid #F1B0B7; background:#FFF5F5; border-radius:0.4rem; margin-bottom:0.6rem;">
                    <div style="font-weight:700; color:#B42318;">🔴 Failure Possible</div>
                    <div style="font-size:0.86rem; color:#5F6368;">The wedge geometry permits sliding along the line of intersection and daylighting from the slope face. Under the specified friction conditions, wedge failure is kinematically feasible.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="padding:0.65rem 0.8rem; border:1px solid #B7E1C1; background:#F5FFF7; border-radius:0.4rem; margin-bottom:0.6rem;">
                    <div style="font-weight:700; color:#16794C;">🟢 Stable</div>
                    <div style="font-size:0.86rem; color:#5F6368;">The defined wedge does not satisfy the kinematic failure condition.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Detailed Geometry Data", expanded=False):
            if geo is None:
                st.warning("Detailed geometry data could not be computed.")
            else:
                st.markdown("**PLANE NORMALS**")
                for k, v in geo["normals"].items():
                    st.write(f"- **{k}**: {vec_str(v)}")

                st.markdown("**LINE DIRECTIONS**")
                for k, v in geo["lines"].items():
                    st.write(f"- **{k}**: {vec_str(v)}")

                st.markdown("**TREND / PLUNGE**")
                for k, (tr, pl) in geo["trend_plunge"].items():
                    st.write(f"- **{k}**: Trend={fmt(tr, 2)}°, Plunge={fmt(pl, 2)}°")

                st.markdown("**PLANE ANGLES**")
                # Generate a markdown table for the plane angle matrix
                p_names = geo["plane_angle_labels"]
                p_matrix = geo["plane_angle_matrix_deg"]
                p_table = "| | " + " | ".join(p_names) + " |\n"
                p_table += "|" + "|".join(["---"] * (len(p_names) + 1)) + "|\n"
                for i, row_name in enumerate(p_names):
                    row_vals = [f"{val:.2f}°" for val in p_matrix[i]]
                    p_table += f"| **{row_name}** | " + " | ".join(row_vals) + " |\n"
                st.markdown(p_table)

                st.markdown("**LINE ANGLES**")
                for k, v in geo["line_angles_deg"].items():
                    st.write(f"- **{k}**: {fmt(v, 2)}°")

                st.markdown("**LENGTHS**")
                for k, v in geo["lengths_m"].items():
                    st.write(f"- **{k}**: {fmt(v, 3)} m")

                st.markdown("**AREAS**")
                for k, v in geo["areas_m2"].items():
                    st.write(f"- **{k}**: {fmt(v, 3)} m²")

                st.markdown("**VOLUME**")
                st.write(f"- **Tetrahedron Volume**: {fmt(geo['volume_m3'], 3)} m³")
    st.divider()