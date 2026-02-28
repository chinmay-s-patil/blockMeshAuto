"""
Tab 3 Edge Math - Mathematical calculations for arcs and splines
"""
import math
import numpy as np


def calculate_arc_through_three_points(p1, p2, p3, num_segments=30):
    """Calculate arc passing through three points (start, mid, end)"""
    A, B, C = np.array(p1), np.array(p2), np.array(p3)

    a, b, c = np.linalg.norm(C - B), np.linalg.norm(C - A), np.linalg.norm(B - A)

    if abs(a + b - c) < 1e-10 or abs(a + c - b) < 1e-10 or abs(b + c - a) < 1e-10:
        return [p1, p3]

    s = (a + b + c) / 2
    area = math.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))

    if area < 1e-10:
        return [p1, p3]

    R = a * b * c / (4 * area)
    denom = a**2 * (b**2 + c**2 - a**2) + b**2 * (a**2 + c**2 - b**2) + c**2 * (a**2 + b**2 - c**2)

    if abs(denom) < 1e-10:
        return [p1, p3]

    alpha = a**2 * (b**2 + c**2 - a**2) / denom
    beta = b**2 * (a**2 + c**2 - b**2) / denom
    gamma = c**2 * (a**2 + b**2 - c**2) / denom

    center = alpha * A + beta * B + gamma * C

    def angle_from_center(point):
        v = np.array(point) - center
        return math.atan2(v[1], v[0])

    angle1, angle2, angle3 = angle_from_center(A), angle_from_center(B), angle_from_center(C)

    def normalize_angle(a):
        while a < 0: a += 2 * math.pi
        while a >= 2 * math.pi: a -= 2 * math.pi
        return a

    a1, a2, a3 = normalize_angle(angle1), normalize_angle(angle2), normalize_angle(angle3)

    going_ccw = a1 < a2 < a3 if a1 < a3 else not (a3 < a2 < a1)

    if going_ccw:
        total_angle = a3 - a1 if a3 > a1 else (2 * math.pi - a1) + a3
    else:
        total_angle = -(a1 - a3 if a1 > a3 else (2 * math.pi - a3) + a1)

    points = []
    for i in range(num_segments + 1):
        t = i / num_segments
        angle = angle1 + t * total_angle
        x = center[0] + R * math.cos(angle)
        y = center[1] + R * math.sin(angle)
        z = A[2] + t * (C[2] - A[2])
        points.append((x, y, z))

    return points


def calculate_spline_points(control_points, num_segments=50):
    """
    True Catmull-Rom spline for OpenFOAM/blockMesh compatibility.
    Interpolates smoothly through all control points.
    """
    if len(control_points) < 2:
        return control_points

    points = [np.array(p) for p in control_points]
    n = len(points)

    if n == 2:
        return [tuple(points[0]), tuple(points[1])]

    result = []

    for i in range(n - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(n - 1, i + 2)]

        for j in range(num_segments + 1):
            t = j / num_segments
            t2 = t * t
            t3 = t2 * t

            # Catmull-Rom spline matrix
            point = 0.5 * (
                (2 * p1) +
                (-p0 + p2) * t +
                (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                (-p0 + 3 * p1 - 3 * p2 + p3) * t3
            )

            result.append(tuple(point))

    # Remove duplicates
    filtered = [result[0]]
    for i in range(1, len(result)):
        if not np.allclose(result[i], result[i-1], atol=1e-10):
            filtered.append(result[i])

    return filtered


def calculate_arc_center_from_radius(p1, p2, radius, direction=1):
    """
    Calculate arc center given two points and a radius.
    Returns center point on the perpendicular bisector.

    Args:
        p1, p2: Start and end points (tuples/lists of 3 coords)
        radius: Desired radius (must be >= half the distance between p1 and p2)
        direction: 1 for one side of the bisector, -1 for the other

    Returns:
        center point (x, y, z) or None if radius is too small
    """
    p1 = np.array(p1)
    p2 = np.array(p2)

    # Midpoint of p1-p2
    midpoint = (p1 + p2) / 2

    # Distance from p1 to p2
    chord_length = np.linalg.norm(p2 - p1)

    if chord_length < 1e-10:
        return None

    if radius < chord_length / 2:
        return None  # Radius too small

    # Distance from midpoint to center
    # Using: r^2 = (chord/2)^2 + d^2
    # So: d = sqrt(r^2 - (chord/2)^2)
    d = math.sqrt(radius**2 - (chord_length / 2)**2)

    # Direction perpendicular to p1-p2 in the XY plane
    # Vector from p1 to p2
    chord_vec = p2 - p1
    # Perpendicular vector (rotate 90 degrees in XY plane)
    perp_vec = np.array([-chord_vec[1], chord_vec[0], 0])

    # Normalize
    perp_length = np.linalg.norm(perp_vec)
    if perp_length < 1e-10:
        # Chord is vertical, use different perpendicular
        perp_vec = np.array([1, 0, 0])
    else:
        perp_vec = perp_vec / perp_length

    # Calculate center
    center = midpoint + direction * d * perp_vec

    return tuple(center)


def calculate_arc_midpoint(p1, p2, center):
    """
    Calculate the midpoint on an arc (the point at the angle halfway between p1 and p2).
    """
    p1 = np.array(p1)
    p2 = np.array(p2)
    center = np.array(center)

    # Vectors from center to p1 and p2
    v1 = p1 - center
    v2 = p2 - center

    # Calculate angle between them
    angle1 = math.atan2(v1[1], v1[0])
    angle2 = math.atan2(v2[1], v2[0])

    # Normalize angles
    def normalize_angle(a):
        while a < 0: a += 2 * math.pi
        while a >= 2 * math.pi: a -= 2 * math.pi
        return a

    a1 = normalize_angle(angle1)
    a2 = normalize_angle(angle2)

    # Find the midpoint angle (taking the shorter arc)
    diff = a2 - a1
    while diff > math.pi:
        diff -= 2 * math.pi
    while diff < -math.pi:
        diff += 2 * math.pi

    mid_angle = a1 + diff / 2

    # Radius
    r = np.linalg.norm(v1)

    # Calculate midpoint on arc
    mid_x = center[0] + r * math.cos(mid_angle)
    mid_y = center[1] + r * math.sin(mid_angle)
    mid_z = (p1[2] + p2[2]) / 2  # Average Z

    return (mid_x, mid_y, mid_z)