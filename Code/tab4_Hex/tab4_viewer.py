"""
Embedded 3D Viewer for Tkinter - Pure Tkinter implementation
No PyVista, No VTK, No Matplotlib, No Plotly
Dark Mode with View Controls and Rotating Axes
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import math
from matplotlib.path import Path


class EmbeddedViewer:
    """3D viewer embedded in a tkinter frame using Canvas"""
    def __init__(self, parent_frame, mesh_data, parent_tab):
        self.parent_frame = parent_frame
        self.mesh_data = mesh_data
        self.parent_tab = parent_tab

        # Get sketch plane from mesh data
        self.sketch_plane = getattr(mesh_data, 'sketch_plane', 'XY')

        # SELECTED POINTS NOW STORE ACTUAL POINT IDs (not global indices)
        self.selected_points = []  # List of actual point IDs
        self.hidden_points = set()  # Set of hidden point IDs

        # LAYER FILTERING: Track which layers are visible
        self.visible_layers = set()

        # 3D view parameters
        self.rotation_x = 30
        self.rotation_y = -45
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Track current view state for toggling
        self._current_view = None
        self._view_positive = True

        # Mouse interaction state
        self._drag_data = {"x": 0, "y": 0, "action": None}

        # Cache: point_id -> (x, y, z) coordinates
        self._point_coords = {}  # point_id -> (x, y, z)
        # Cache: point_id -> (screen_x, screen_y) 
        self._screen_coords = {}  # point_id -> (x, y)

        # Colors for dark mode
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'grid': '#404040',
            'text': '#cccccc',
            'x_axis': '#ff4444',
            'y_axis': '#44ff44',
            'z_axis': '#4444ff',
            'selected': '#00ff00',
        }

        self.setup_ui()
        self._rebuild_coord_cache()
        self.draw()

    def setup_ui(self):
        """Create the canvas and controls"""
        # Main canvas
        self.frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame, bg=self.colors['bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Toolbar frame at top left (floating)
        self.toolbar = tk.Frame(self.frame, bg='#2d2d2d', highlightbackground='#555', highlightthickness=1)
        self.toolbar.place(x=10, y=10)

        # View control buttons
        btn_style = {'bg': '#404040', 'fg': 'white', 'relief': tk.FLAT, 
                    'font': ('Arial', 9, 'bold'), 'padx': 8, 'pady': 2}

        tk.Button(self.toolbar, text="Fit All", command=self.fit_all, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(self.toolbar, bg='#555555', width=2, height=16).pack(side=tk.LEFT, padx=5, pady=2)

        tk.Button(self.toolbar, text="⟲ Reset", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(self.toolbar, text="⟳ Refresh", command=self.refresh, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(self.toolbar, bg='#555555', width=2, height=16).pack(side=tk.LEFT, padx=5, pady=2)

        tk.Label(self.toolbar, text="Views:", bg='#2d2d2d', fg='white', font=('Arial', 9)).pack(side=tk.LEFT)

        self.view_buttons = {}
        for axis in ['x', 'y', 'z']:
            btn = tk.Button(self.toolbar, text=axis.upper(), 
                          command=lambda a=axis: self.set_view(a), **btn_style)
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            self.view_buttons[axis] = btn

        tk.Button(self.toolbar, text="Iso", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=1, pady=2)

        self.plane_label = tk.Label(self.toolbar, text=f"Plane: {self.sketch_plane}", 
                                   bg='#2d2d2d', fg='#aaaaaa', font=('Arial', 8))
        self.plane_label.pack(side=tk.RIGHT, padx=10)

        # Add Select Mode Toggle
        self.select_mode = tk.StringVar(value="Square")
        tk.Radiobutton(self.toolbar, text="Square", variable=self.select_mode, value="Square",
                      bg='#2d2d2d', fg='white', selectcolor='#404040', activebackground='#2d2d2d',
                      activeforeground='white', font=('Arial', 8)).pack(side=tk.RIGHT, padx=2)
        tk.Radiobutton(self.toolbar, text="Lasso", variable=self.select_mode, value="Lasso",
                      bg='#2d2d2d', fg='white', selectcolor='#404040', activebackground='#2d2d2d',
                      activeforeground='white', font=('Arial', 8)).pack(side=tk.RIGHT, padx=2)

        # Info label at bottom (floating)
        self.info_label = tk.Label(self.frame, 
                                  text=f"Middle: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}", 
                                  bg='#2d2d2d', fg=self.colors['text'], font=('Arial', 8))
        self.info_label.place(x=10, rely=1.0, y=-10, anchor='sw')

        # Bind events
        self.canvas.bind("<Button-2>", self._on_middle_click)
        self.canvas.bind("<B2-Motion>", self._on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_middle_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>", self._on_scroll)
        self.canvas.bind("<Button-5>", self._on_scroll)
        self.canvas.bind("<Configure>", lambda e: self.draw())

        # Selection state
        self.selection_start = None
        self.selection_rect = None
        self.is_dragging = False
        self.lasso_points = []

    def _rebuild_coord_cache(self):
        """Cache all point coordinates by their actual point IDs"""
        self.sketch_plane = getattr(self.mesh_data, 'sketch_plane', 'XY')
        self.plane_label.config(text=f"Plane: {self.sketch_plane}")
        self.info_label.config(text=f"Middle: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}")

        self._point_coords = {}  # point_id -> (x, y, z)

        # Get visible layers
        if self.visible_layers:
            layer_list = sorted([ln for ln in self.mesh_data.layers.keys() 
                                if ln in self.visible_layers], 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))
        else:
            layer_list = sorted(self.mesh_data.layers.keys(), 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))

        for layer_name in layer_list:
            layer_data = self.mesh_data.layers.get(layer_name, {})
            point_refs = layer_data.get('point_refs', [])

            for point_id in point_refs:
                point_data = self.mesh_data.get_point(point_id)
                if point_data:
                    self._point_coords[point_id] = (point_data['x'], point_data['y'], point_data['z'])

        # Clean up selected/hidden points that no longer exist
        existing_points = set(self._point_coords.keys())
        self.selected_points = [p for p in self.selected_points if p in existing_points]
        self.hidden_points = self.hidden_points.intersection(existing_points)

    def _rotate_point(self, point):
        """Apply rotation to a 3D point"""
        x, y, z = point

        rad_x = math.radians(self.rotation_x)
        cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

        rad_y = math.radians(self.rotation_y)
        cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
        z, x = z * cos_y - x * sin_y, z * sin_y + x * cos_y

        return np.array([x, y, z])

    def _project(self, point_3d):
        """Project 3D point to 2D canvas coordinates"""
        rotated = self._rotate_point(point_3d)
        x, y = rotated[0], rotated[1]

        cx = self.canvas.winfo_width() / 2 + self.pan_x
        cy = self.canvas.winfo_height() / 2 + self.pan_y

        screen_x = cx + x * self.zoom * 5
        screen_y = cy - y * self.zoom * 5

        return screen_x, screen_y, rotated[2]

    def _get_edge_points(self, edge_data):
        """Get all points that define an edge (start, end, and any intermediate)"""
        points = []

        start = edge_data.get('start')
        if start is not None:
            if isinstance(start, int):
                points.append(start)

        end = edge_data.get('end')
        if end is not None:
            if isinstance(end, int):
                points.append(end)

        intermediate = edge_data.get('intermediate')
        if intermediate is not None:
            if isinstance(intermediate, list):
                for pt in intermediate:
                    if isinstance(pt, int):
                        points.append(pt)
            elif isinstance(intermediate, int):
                points.append(intermediate)

        return points

    def _get_edge_curve_points(self, edge_data, num_segments=30):
        """Calculate curve points for an edge (arc, spline, polyLine)"""
        edge_type = edge_data.get('type', 'line')

        start = edge_data.get('start')
        end = edge_data.get('end')
        intermediate = edge_data.get('intermediate')

        # Get coordinates
        def get_coord(pt):
            if isinstance(pt, int):
                return self._point_coords.get(pt)
            elif isinstance(pt, (list, tuple)) and len(pt) == 3:
                return pt
            return None

        start_coord = get_coord(start)
        end_coord = get_coord(end)

        if start_coord is None or end_coord is None:
            return []

        if edge_type == 'line':
            return [start_coord, end_coord]

        elif edge_type == 'arc':
            if intermediate is None:
                return [start_coord, end_coord]

            mid_coord = get_coord(intermediate)
            if mid_coord is None:
                return [start_coord, end_coord]

            return self._calculate_arc_points(start_coord, mid_coord, end_coord, num_segments)

        elif edge_type in ['spline', 'polyLine']:
            all_points = [start_coord]

            if intermediate is not None:
                if isinstance(intermediate, list):
                    for pt in intermediate:
                        coord = get_coord(pt)
                        if coord:
                            all_points.append(coord)
                else:
                    coord = get_coord(intermediate)
                    if coord:
                        all_points.append(coord)

            all_points.append(end_coord)

            if edge_type == 'spline':
                return self._calculate_spline_points(all_points, num_segments)
            else:
                return all_points

        return [start_coord, end_coord]

    def _calculate_arc_points(self, p1, p2, p3, num_segments=30):
        """Calculate points on an arc through three points"""
        A, B, C = np.array(p1), np.array(p2), np.array(p3)

        # Calculate circle center and radius
        a = np.linalg.norm(C - B)
        b = np.linalg.norm(C - A)
        c = np.linalg.norm(B - A)

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

        # Calculate angles
        def angle_from_center(point):
            v = np.array(point) - center
            return math.atan2(v[1], v[0])

        angle1 = angle_from_center(A)
        angle2 = angle_from_center(B)
        angle3 = angle_from_center(C)

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

        # Generate arc points
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            angle = angle1 + t * total_angle
            x = center[0] + R * math.cos(angle)
            y = center[1] + R * math.sin(angle)
            z = A[2] + t * (C[2] - A[2])
            points.append((x, y, z))

        return points

    def _calculate_spline_points(self, control_points, num_segments=50):
        """Calculate Catmull-Rom spline points"""
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

    def draw(self):
        """Redraw the 3D scene"""
        self.canvas.delete("all")

        if len(self._point_coords) == 0:
            self._draw_axes_widget()
            return

        # Calculate all screen coordinates for visible points
        self._screen_coords = {}
        for point_id, coord in self._point_coords.items():
            if point_id in self.hidden_points:
                continue
            screen_x, screen_y, z_depth = self._project(coord)
            self._screen_coords[point_id] = (screen_x, screen_y)

        # Get layer colors
        color_map = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']

        # Build layer to color mapping
        if self.visible_layers:
            layer_list = sorted([ln for ln in self.mesh_data.layers.keys() 
                                if ln in self.visible_layers], 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))
        else:
            layer_list = sorted(self.mesh_data.layers.keys(), 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))
        layer_to_idx = {name: i for i, name in enumerate(layer_list)}

        # Get edges and build set of connections that have edges
        edges = getattr(self.mesh_data, 'edges', {})
        connections_with_edges = set()
        edge_curves = []  # List of (points, color, width) for drawing

        for edge_id, edge_data in edges.items():
            # Get the point IDs that this edge connects
            edge_point_ids = self._get_edge_points(edge_data)
            if len(edge_point_ids) >= 2:
                # Mark these connections as having edges
                for i in range(len(edge_point_ids) - 1):
                    p1, p2 = edge_point_ids[i], edge_point_ids[i+1]
                    # Store both orderings
                    connections_with_edges.add((min(p1, p2), max(p1, p2)))

            # Calculate curve points for visualization
            curve_points = self._get_edge_curve_points(edge_data)
            if len(curve_points) >= 2:
                # Determine color based on start point's layer
                start_id = edge_data.get('start')
                if isinstance(start_id, int):
                    layer_name = None
                    for ln, l_data in self.mesh_data.layers.items():
                        if start_id in l_data.get('point_refs', []):
                            layer_name = ln
                            break
                    color = color_map[layer_to_idx.get(layer_name, 0) % len(color_map)] if layer_name else '#00ff00'
                else:
                    color = '#00ff00'  # Green for manual points

                edge_curves.append((curve_points, color))

        # Draw connections first (but skip those that have edges)
        self._draw_connections(layer_to_idx, layer_list, color_map, connections_with_edges)

        # Draw edge curves on top
        for curve_points, color in edge_curves:
            screen_points = []
            for pt in curve_points:
                sx, sy, _ = self._project(np.array(pt))
                screen_points.append((sx, sy))

            # Draw the curve
            for i in range(len(screen_points) - 1):
                x1, y1 = screen_points[i]
                x2, y2 = screen_points[i+1]
                self.canvas.create_line(x1, y1, x2, y2, fill='#00ff00', width=3)

        # Draw hex blocks wireframes
        self._draw_hex_blocks()

        # Group points by layer for coloring
        points_by_layer = {i: [] for i in range(len(layer_list))}
        selected_points_list = []

        for point_id, coord in self._point_coords.items():
            if point_id in self.hidden_points:
                continue

            if point_id not in self._screen_coords:
                continue

            screen_x, screen_y = self._screen_coords[point_id]

            # Find which layer this point belongs to
            layer_name = None
            for ln, l_data in self.mesh_data.layers.items():
                if point_id in l_data.get('point_refs', []):
                    layer_name = ln
                    break

            layer_idx = layer_to_idx.get(layer_name, 0)

            if point_id in self.selected_points:
                selected_points_list.append((point_id, screen_x, screen_y, coord))
            else:
                points_by_layer[layer_idx].append((point_id, screen_x, screen_y, coord))

        # Draw unselected points
        for layer_idx in sorted(points_by_layer.keys(), reverse=True):
            pts = points_by_layer[layer_idx]
            color = color_map[layer_idx % len(color_map)]

            for point_id, x, y, coord in pts:
                r = 6
                self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                       fill=color, outline='white', width=1,
                                       tags=f"point_{point_id}")
                # Show point ID
                self.canvas.create_text(x, y-10, text=str(point_id), 
                                       fill=color, font=('Courier', 9, 'bold'),
                                       tags=f"label_{point_id}")

        # Draw selected points (on top, larger) - preserve selection order
        order_map = {pid: i for i, pid in enumerate(self.selected_points)}
        selected_points_list.sort(key=lambda x: order_map.get(x[0], 999))

        for point_id, x, y, coord in selected_points_list:
            r = 10
            self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                   fill=self.colors['selected'], outline='darkgreen', width=2,
                                   tags=f"point_{point_id}")
            label = f"{point_id}*"
            self.canvas.create_text(x, y-15, text=label, 
                                   fill=self.colors['selected'], font=('Courier', 10, 'bold'),
                                   tags=f"label_{point_id}")

        # Draw axes widget last
        self._draw_axes_widget()

    def _draw_connections(self, layer_to_idx, layer_list, color_map, connections_with_edges=None):
        """Draw lines between connected points - FIXED for flat connections dict"""
        if connections_with_edges is None:
            connections_with_edges = set()

        # Connections are stored as a flat dict: {conn_id: {"point1": id, "point2": id}}
        all_connections = getattr(self.mesh_data, 'connections', {})

        for conn_id, conn_data in all_connections.items():
            p1_id = conn_data.get('point1')
            p2_id = conn_data.get('point2')

            if p1_id is None or p2_id is None:
                continue

            # Skip if this connection has an edge covering it
            if (min(p1_id, p2_id), max(p1_id, p2_id)) in connections_with_edges:
                continue

            # Skip if points are hidden or not visible
            if (p1_id in self.hidden_points or p2_id in self.hidden_points or
                p1_id not in self._screen_coords or p2_id not in self._screen_coords):
                continue

            # Get layer color for the connection
            layer_name = None
            for ln in layer_list:
                if p1_id in self.mesh_data.layers.get(ln, {}).get('point_refs', []):
                    layer_name = ln
                    break

            if layer_name and layer_name in layer_to_idx:
                layer_idx = layer_to_idx[layer_name]
                color = color_map[layer_idx % len(color_map)]
            else:
                color = '#888888'  # Default gray

            x1, y1 = self._screen_coords[p1_id]
            x2, y2 = self._screen_coords[p2_id]

            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

    def _draw_hex_blocks(self):
        """Draw hex block wireframes using dynamically computed vertices"""
        hex_blocks = getattr(self.mesh_data, 'hex_blocks', {})

        for block_id, block in hex_blocks.items():
            point_refs = block.get('point_refs', [])

            if len(point_refs) != 8:
                continue

            # Compute current 3D coordinates from point references
            vertices = []
            valid = True
            for point_id in point_refs:
                if point_id not in self._point_coords:
                    valid = False
                    break
                vertices.append(np.array(self._point_coords[point_id]))

            if not valid:
                continue

            # Project to screen
            screen_verts = []
            for v in vertices:
                sx, sy, sz = self._project(v)
                screen_verts.append((sx, sy, sz))

            # Draw edges
            edges = [
                (0,1), (1,2), (2,3), (3,0),
                (4,5), (5,6), (6,7), (7,4),
                (0,4), (1,5), (2,6), (3,7)
            ]

            for i, j in edges:
                x1, y1, z1 = screen_verts[i]
                x2, y2, z2 = screen_verts[j]
                avg_z = (z1 + z2) / 2
                width = 3 if avg_z > 0 else 2
                color = '#66ff66' if avg_z > 0 else '#44aa44'
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

            # Draw faces
            faces = [(0,1,2,3), (4,5,6,7), (0,1,5,4), (2,3,7,6), (1,2,6,5), (0,3,7,4)]
            for face in faces:
                points = [(screen_verts[i][0], screen_verts[i][1]) for i in face]
                avg_z_face = sum(screen_verts[i][2] for i in face) / 4
                alpha = 'gray75' if avg_z_face > 0 else 'gray25'
                self.canvas.create_polygon(points, fill='#66ff66', 
                                        stipple=alpha, outline='#44ff44', width=1)

    def _draw_axes_widget(self):
        """Draw rotating axes indicator in bottom right corner"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        center_x = w - 50
        center_y = h - 50
        length = 30

        x_vec = self._rotate_point([length, 0, 0])
        y_vec = self._rotate_point([0, length, 0])
        z_vec = self._rotate_point([0, 0, length])

        # X axis - Red
        self.canvas.create_line(center_x, center_y, 
                               center_x + x_vec[0], center_y - x_vec[1],
                               fill=self.colors['x_axis'], width=3, arrow=tk.LAST)
        # Y axis - Green
        self.canvas.create_line(center_x, center_y, 
                               center_x + y_vec[0], center_y - y_vec[1],
                               fill=self.colors['y_axis'], width=3, arrow=tk.LAST)
        # Z axis - Blue
        self.canvas.create_line(center_x, center_y, 
                               center_x + z_vec[0], center_y - z_vec[1],
                               fill=self.colors['z_axis'], width=3, arrow=tk.LAST)

        label_offset = 8
        self.canvas.create_text(center_x + x_vec[0] + label_offset, 
                               center_y - x_vec[1] - label_offset,
                               text="X", fill=self.colors['x_axis'], 
                               font=('Arial', 10, 'bold'))
        self.canvas.create_text(center_x + y_vec[0] + label_offset, 
                               center_y - y_vec[1] - label_offset,
                               text="Y", fill=self.colors['y_axis'], 
                               font=('Arial', 10, 'bold'))
        self.canvas.create_text(center_x + z_vec[0] + label_offset, 
                               center_y - z_vec[1] - label_offset,
                               text="Z", fill=self.colors['z_axis'], 
                               font=('Arial', 10, 'bold'))

        self.canvas.create_oval(center_x-35, center_y-35, center_x+35, center_y+35,
                               outline='#444444', width=1, stipple='gray50')

    def _on_left_click(self, event):
        """Start point selection"""
        self.selection_start = (event.x, event.y)
        self.is_dragging = False
        self.lasso_points = [(event.x, event.y)]

    def _on_left_drag(self, event):
        """Draw selection rectangle or lasso"""
        if not self.selection_start: return
        self.is_dragging = True

        if self.selection_rect:
            self.canvas.delete(self.selection_rect)

        if getattr(self, 'select_mode', None) and self.select_mode.get() == "Lasso":
            self.lasso_points.append((event.x, event.y))
            flat_pts = [c for p in self.lasso_points for c in p]
            if len(flat_pts) >= 4:
                self.selection_rect = self.canvas.create_polygon(
                    flat_pts, outline='#00ff00', fill='', dash=(4, 4), tags="selection_rect"
                )
        else:
            # Rectangle selection
            x0, y0 = self.selection_start
            x1, y1 = event.x, event.y
            self.selection_rect = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline='#00ff00', dash=(4, 4), tags="selection_rect"
            )

    def _on_left_release(self, event):
        """Complete selection - NOW USES ACTUAL POINT IDs"""
        if not self.selection_start: return

        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

        if self.is_dragging:
            selected_in_rect = []
            if getattr(self, 'select_mode', None) and self.select_mode.get() == "Lasso":
                if len(self.lasso_points) > 2:
                    lasso_path = Path(self.lasso_points)
                    for point_id, (sx, sy) in self._screen_coords.items():
                        if lasso_path.contains_point((sx, sy)):
                            selected_in_rect.append(point_id)
            else:
                # Rectangle selection
                x0, y0 = self.selection_start
                x1, y1 = event.x, event.y
                xmin, xmax = min(x0, x1), max(x0, x1)
                ymin, ymax = min(y0, y1), max(y0, y1)

                for point_id, (sx, sy) in self._screen_coords.items():
                    if xmin <= sx <= xmax and ymin <= sy <= ymax:
                        selected_in_rect.append(point_id)

            # Toggle logic
            for pt in selected_in_rect:
                if pt not in self.selected_points:
                    if len(self.selected_points) < 8:
                        self.selected_points.append(pt)
                    else:
                        messagebox.showwarning("Limit", "Maximum 8 points allowed")
                        break
                else:
                    self.selected_points.remove(pt)

            self.parent_tab.on_selection_changed(self.selected_points.copy())
            self.draw()

        else:
            # Single point selection
            clicked_point = None
            min_dist = float('inf')

            # Find closest point within click radius
            for point_id, (sx, sy) in self._screen_coords.items():
                dist = ((sx - event.x)**2 + (sy - event.y)**2)**0.5
                if dist < 15:
                    if dist < min_dist:
                        min_dist = dist
                        clicked_point = point_id

            if clicked_point is not None:
                if clicked_point in self.selected_points:
                    self.selected_points.remove(clicked_point)
                else:
                    if len(self.selected_points) < 8:
                        self.selected_points.append(clicked_point)
                    else:
                        messagebox.showwarning("Limit", "Maximum 8 points allowed")
                        return

                # Pass actual point IDs to parent
                self.parent_tab.on_selection_changed(self.selected_points.copy())
                self.draw()

        self.selection_start = None
        self.is_dragging = False

    def _on_middle_click(self, event):
        """Handle middle mouse press for rotation"""
        self._drag_data = {"x": event.x, "y": event.y, "action": "rotate"}

    def _on_middle_drag(self, event):
        """Handle middle mouse drag for rotation"""
        if self._drag_data.get("action") == "rotate":
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]

            self.rotation_y += dx * 0.5
            self.rotation_x -= dy * 0.5

            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y

            self._current_view = None
            self._update_view_button_labels()
            self.draw()

    def _on_middle_release(self, event):
        """Handle middle mouse release"""
        self._drag_data = {"x": 0, "y": 0, "action": None}

    def _on_right_click(self, event):
        """Handle right mouse press for panning"""
        self._drag_data = {"x": event.x, "y": event.y, "action": "pan"}

    def _on_right_drag(self, event):
        """Handle right mouse drag for panning"""
        if self._drag_data.get("action") == "pan":
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]

            self.pan_x += dx
            self.pan_y += dy

            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y

            self.draw()

    def _on_right_release(self, event):
        """Handle right mouse release"""
        self._drag_data = {"x": 0, "y": 0, "action": None}

    def _on_scroll(self, event):
        """Handle zoom"""
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9

        self.zoom = max(0.01, min(1000.0, self.zoom))
        self.draw()

    def fit_all(self):
        """Zoom and pan to fit all visible points"""
        if len(self._point_coords) == 0:
            return

        coords = np.array(list(self._point_coords.values()))
        min_coords = coords.min(axis=0)
        max_coords = coords.max(axis=0)

        self.pan_x = 0
        self.pan_y = 0

        self.zoom = 1.0

        corners = []
        for i in [0, 1]:
            for j in [0, 1]:
                for k in [0, 1]:
                    corners.append([min_coords[0] if i==0 else max_coords[0],
                                  min_coords[1] if j==0 else max_coords[1],
                                  min_coords[2] if k==0 else max_coords[2]])

        screen_pts = []
        for corner in corners:
            sx, sy, _ = self._project(corner)
            screen_pts.append((sx - self.canvas.winfo_width()/2, 
                              -(sy - self.canvas.winfo_height()/2)))

        screen_pts = np.array(screen_pts)
        screen_range = np.abs(screen_pts).max() * 2

        canvas_size = min(self.canvas.winfo_width(), self.canvas.winfo_height())
        if screen_range > 0:
            self.zoom = (canvas_size / screen_range) * 0.8

        self.zoom = max(0.01, min(1000.0, self.zoom))
        self.draw()

    def set_view(self, axis):
        """Set view perpendicular to specified axis with toggle functionality"""
        if self._current_view == axis:
            self._view_positive = not self._view_positive
        else:
            self._current_view = axis
            self._view_positive = True

        if axis == 'x':
            if self._view_positive:
                self.rotation_x = 0
                self.rotation_y = -90
            else:
                self.rotation_x = 0
                self.rotation_y = 90

        elif axis == 'y':
            if self._view_positive:
                self.rotation_x = -90
                self.rotation_y = 0
            else:
                self.rotation_x = 90
                self.rotation_y = 0

        elif axis == 'z':
            if self._view_positive:
                self.rotation_x = 0
                self.rotation_y = 0
            else:
                self.rotation_x = 0
                self.rotation_y = 180

        self._update_view_button_labels()
        self.draw()

    def _update_view_button_labels(self):
        """Update view button labels to show + or - direction"""
        for axis, btn in self.view_buttons.items():
            if self._current_view == axis:
                sign = '+' if self._view_positive else '-'
                btn.config(text=f"{sign}{axis.upper()}", bg='#606060')
            else:
                btn.config(text=axis.upper(), bg='#404040')

    def hide_selected(self):
        """Hide currently selected points"""
        self.hidden_points.update(self.selected_points)
        self.selected_points = []
        self.draw()

    def set_selection(self, point_ids):
        """Set selection from outside - accepts list of point IDs"""
        self.selected_points = list(point_ids)
        self.draw()

    def show_all(self):
        """Show all points"""
        self.hidden_points.clear()
        self.draw()

    def clear_selection(self):
        """Clear selection"""
        self.selected_points = []
        self.draw()

    def set_visible_layers(self, layer_names):
        """Set which layers should be visible"""
        self.visible_layers = set(layer_names)
        self._rebuild_coord_cache()
        self.draw()

    def reset_view(self):
        """Reset camera to isometric view"""
        self.rotation_x = 30
        self.rotation_y = -45
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._current_view = 'iso'
        self._view_positive = True
        self._update_view_button_labels()
        self.draw()

    def refresh(self):
        """Refresh view"""
        self._rebuild_coord_cache()
        self.draw()

    def close(self):
        """Cleanup"""
        pass