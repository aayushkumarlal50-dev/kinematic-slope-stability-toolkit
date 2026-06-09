import numpy as np
EPS = 1e-9

def unit_vector(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < EPS:
        raise ValueError("Zero-length vector.")
    return v / n

def sin_deg(x):
    return np.sin(np.radians(x))

def plane_normal(dip_direction_deg, dip_angle_deg):
    """
    n = (sinA sinB, sinA cosB, cosA)

    A = dip angle
    B = dip direction
    """
    A = np.radians(dip_angle_deg)
    B = np.radians(dip_direction_deg)

    return unit_vector([
        np.sin(A) * np.sin(B),
        np.sin(A) * np.cos(B),
        np.cos(A),
    ])

def line_direction(n1, n2):
    """
    Unit vector along plane intersection.
    Convention:
        force downward (z <= 0)
    """
    v = np.cross(n1, n2)
    if np.linalg.norm(v) < EPS:
        raise ValueError("Planes are parallel or nearly parallel.")
    v = unit_vector(v)
    if v[2] > 0:
        v = -v
    return v

def angle_deg(v1, v2):
    """
    True geometric angle in degrees.
    Range: [0, 180]
    """
    v1 = unit_vector(v1)
    v2 = unit_vector(v2)
    c = np.clip(np.dot(v1, v2), -1.0, 1.0)
    return np.degrees(np.arccos(c))

def trend_plunge(v):
    """
    x = East
    y = North
    z = Up
    Trend clockwise from North.
    Plunge positive downward.
    """
    v = unit_vector(v)
    if v[2] > 0:
        v = -v
    horizontal = np.hypot(v[0], v[1])
    plunge = np.degrees(np.arctan2(-v[2], horizontal))
    trend = (np.degrees(np.arctan2(v[0], v[1])) + 360.0) % 360.0
    return trend, plunge

def pairwise_angle_matrix(vectors):
    names = list(vectors.keys())
    n = len(names)
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            ang = angle_deg(vectors[names[i]], vectors[names[j]])
            M[i, j] = ang
            M[j, i] = ang
    return names, M

def tetrahedron_geometry(planes, H):
    """
    planes = {
        "A": (dipdir, dip),
        "B": (dipdir, dip),
        "C": (dipdir, dip),
        "S": (dipdir, dip),
    }
    H = vertical height (m)
    """
    normals = {
        name: plane_normal(dd, dip)
        for name, (dd, dip) in planes.items()
    }

    nA = normals["A"]
    nB = normals["B"]
    nC = normals["C"]
    nS = normals["S"]

    lines = {
        "L1": line_direction(nA, nC),  # A ∩ C
        "L2": line_direction(nA, nS),  # A ∩ S
        "L3": line_direction(nC, nB),  # C ∩ B
        "L4": line_direction(nB, nS),  # B ∩ S
        "L5": line_direction(nA, nB),  # A ∩ B
        "L6": line_direction(nC, nS),  # C ∩ S
    }

    trend_plunge_data = {
        k: trend_plunge(v)
        for k, v in lines.items()
    }

    plane_names, plane_angle_matrix = pairwise_angle_matrix(normals)
    line_names, line_angle_matrix = pairwise_angle_matrix(lines)

    line_angles = {}

    for i in range(1, 7):
        for j in range(i + 1, 7):
            line_angles[f"theta_{i}{j}"] = angle_deg(
                lines[f"L{i}"],
                lines[f"L{j}"]
            )

    theta_12 = line_angles["theta_12"]
    theta_15 = line_angles["theta_15"]
    theta_25 = line_angles["theta_25"]

    theta_34 = line_angles["theta_34"]
    theta_35 = line_angles["theta_35"]
    theta_45 = line_angles["theta_45"]

    plunge5 = trend_plunge_data["L5"][1]

    if abs(sin_deg(plunge5)) < EPS:
        raise ValueError("Plunge(L5) too small.")

    L5 = H / sin_deg(plunge5)

    if abs(sin_deg(theta_12)) < EPS:
        raise ValueError("theta_12 invalid.")

    if abs(sin_deg(theta_34)) < EPS:
        raise ValueError("theta_34 invalid.")

    L1 = L5 * sin_deg(theta_25) / sin_deg(theta_12)
    L2 = L5 * sin_deg(theta_15) / sin_deg(theta_12)
    L3 = L5 * sin_deg(theta_45) / sin_deg(theta_34)
    L4 = L5 * sin_deg(theta_35) / sin_deg(theta_34)

    lengths = {
        "L1": L1,
        "L2": L2,
        "L3": L3,
        "L4": L4,
        "L5": L5,
    }

    area_A = 0.5 * L2 * L5 * sin_deg(theta_25)
    area_B = 0.5 * L4 * L5 * sin_deg(theta_45)

    areas = {
        "Plane A": area_A,
        "Plane B": area_B,
    }

    n2 = lines["L2"]
    n4 = lines["L4"]
    n5 = lines["L5"]

    scalar_triple_product = abs(
        np.dot(n2, np.cross(n5, n4))
    )

    volume = (
        L2 * L5 * L4 / 6.0
        * scalar_triple_product
    )

    return {
        "normals": normals,
        "lines": lines,
        "trend_plunge": trend_plunge_data,
        "plane_angle_labels": plane_names,
        "plane_angle_matrix_deg": plane_angle_matrix,
        "line_angle_labels": line_names,
        "line_angle_matrix_deg": line_angle_matrix,
        "line_angles_deg": line_angles,
        "lengths_m": lengths,
        "areas_m2": areas,
        "scalar_triple_product": scalar_triple_product,
        "volume_m3": volume,
    }

if __name__ == "__main__":
    planes = {
        "A": (330, 60),
        "B": (120, 60),
        "C": (45, 0),
        "S": (45, 75),
    }

    H = 20.0

    result = tetrahedron_geometry(planes, H)

    print("\nPLANE NORMALS")
    for k, v in result["normals"].items():
        print(f"{k}: {np.round(v, 6)}")

    print("\nLINE DIRECTIONS")
    for k, v in result["lines"].items():
        print(f"{k}: {np.round(v, 6)}")

    print("\nTREND / PLUNGE")
    for k, (tr, pl) in result["trend_plunge"].items():
        print(f"{k}: Trend={tr:.2f}°, Plunge={pl:.2f}°")

    print("\nPLANE ANGLES")

    plane_names = result["plane_angle_labels"]
    plane_matrix = result["plane_angle_matrix_deg"]

    print("     ", end="")
    for name in plane_names:
        print(f"{name:>10}", end="")
    print()

    for i, name in enumerate(plane_names):
        print(f"{name:>5}", end="")
        for j in range(len(plane_names)):
            print(f"{plane_matrix[i, j]:10.2f}", end="")
        print()

    print("\nLINE ANGLES")
    for k, v in result["line_angles_deg"].items():
        print(f"{k}: {v:.2f}°")

    print("\nLENGTHS")
    for k, v in result["lengths_m"].items():
        print(f"{k}: {v:.3f} m")

    print("\nAREAS")
    for k, v in result["areas_m2"].items():
        print(f"{k}: {v:.3f} m²")

    print("\nVOLUME")
    print(
        f"Scalar Triple Product = "
        f"{result['scalar_triple_product']:.6f}"
    )

    print(
        f"Tetrahedron Volume = "
        f"{result['volume_m3']:.3f} m³"
    )