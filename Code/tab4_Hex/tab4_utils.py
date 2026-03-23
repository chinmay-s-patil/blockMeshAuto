"""
Utility functions for Tab 4 - Hex Block Making
Contains shared functions for hex calculations, sorting, etc.
"""
import math
import numpy as np


def auto_sort_hex_points(point_ids, mesh_data):
    """
    Sort 8 points into proper hex block order: 4 bottom CCW, 4 top CCW.
    Returns the sorted list of point IDs.
    """
    if len(point_ids) != 8:
        return point_ids

    # Get coordinates for all points
    pts = []
    for pid in point_ids:
        p = mesh_data.get_point(pid)
        if p:
            pts.append((pid, p['x'], p['y'], p['z']))

    if len(pts) != 8:
        return point_ids

    # Sort by Z coordinate to separate bottom (lowest) and top (highest)
    pts.sort(key=lambda p: p[3])
    bottom = pts[0:4]
    top = pts[4:8]

    # Sort quadrilaterals Counter-Clockwise around their center
    def sort_quad(quad):
        cx = sum(p[1] for p in quad) / 4
        cy = sum(p[2] for p in quad) / 4
        # atan2 gives angle from center; sort by angle gives CCW order
        return sorted(quad, key=lambda p: math.atan2(p[2] - cy, p[1] - cx))

    bottom = sort_quad(bottom)
    top = sort_quad(top)

    # Return ordered: bottom 4 CCW, then top 4 CCW
    return [p[0] for p in bottom + top]


def calculate_divisions_from_cell_size(vertices, cell_size):
    """
    Calculate divisions from cell size using OpenFOAM edge definitions.
    Returns (nx, ny, nz) tuple.
    """
    # X edges: (0,1), (3,2), (4,5), (7,6)
    x_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
               for i, j in [(0,1), (3,2), (4,5), (7,6)]]
    # Y edges: (1,2), (0,3), (5,6), (4,7)
    y_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
               for i, j in [(1,2), (0,3), (5,6), (4,7)]]
    # Z edges: (0,4), (1,5), (2,6), (3,7)
    z_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
               for i, j in [(0,4), (1,5), (2,6), (3,7)]]

    nx = max(1, int(round(np.mean(x_edges) / cell_size)))
    ny = max(1, int(round(np.mean(y_edges) / cell_size)))
    nz = max(1, int(round(np.mean(z_edges) / cell_size)))
    return nx, ny, nz


def get_block_vertices(block_data, mesh_data):
    """
    Get current 3D vertices for a block from its point references.
    Returns list of 8 (x, y, z) tuples or None if points missing.
    """
    point_refs = block_data.get('point_refs', [])
    if len(point_refs) != 8:
        return None

    vertices = []
    for point_id in point_refs:
        point_data = mesh_data.get_point(point_id)
        if point_data is None:
            return None  # Point no longer exists
        vertices.append((point_data['x'], point_data['y'], point_data['z']))

    return vertices


def validate_hex_points(point_refs):
    """
    Validate that point_refs contains exactly 8 unique points.
    Returns (is_valid, error_message)
    """
    if len(point_refs) != 8:
        return False, f"Need exactly 8 points, have {len(point_refs)}"

    # Check for duplicate points in the selection
    if len(set(point_refs)) != 8:
        return False, "Duplicate points selected - each point can only be used once per hex"

    return True, ""


def get_next_hex_id(hex_blocks_dict):
    """
    Find the smallest available hex ID (recycles deleted IDs).
    Returns string ID.
    """
    existing_ids = set()
    for key in hex_blocks_dict.keys():
        try:
            # Handle both "Hex X" format and just numbers
            if isinstance(key, str):
                if key.startswith("Hex "):
                    existing_ids.add(int(key.split()[1]))
                else:
                    existing_ids.add(int(key))
        except (ValueError, IndexError):
            continue

    # Find smallest positive integer not in use
    i = 1
    while i in existing_ids:
        i += 1
    return str(i)


def check_duplicate_hex(point_refs, hex_blocks_dict):
    """
    Check if a hex with these 8 points already exists.
    Returns the block ID if duplicate found, None otherwise.
    """
    # Normalize point set (convert to set for comparison)
    point_set = frozenset(point_refs)

    for block_id, block_data in hex_blocks_dict.items():
        existing_refs = block_data.get('point_refs', [])
        if len(existing_refs) != 8:
            continue  # Skip invalid blocks

        # Check if same set of points (order-independent for duplicate check)
        if frozenset(existing_refs) == point_set:
            return block_id

    return None