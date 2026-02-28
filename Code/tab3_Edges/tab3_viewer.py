"""
Embedded 3D Viewer for Tab 3 (Edge Editor) - Pure Tkinter implementation
Updated for new data structure with proper connection visualization
FIXED: Use actual point IDs instead of global indices for display and selection
"""
import tkinter as tk
from tkinter import messagebox
import numpy as np
import math


class EmbeddedViewer:
    """3D viewer embedded in a tkinter frame using Canvas"""
    def __init__(self, parent_frame, mesh_data, parent_tab):
        self.parent_frame = parent_frame
        self.mesh_data = mesh_data
        self.parent_tab = parent_tab

        # Get sketch plane from mesh data
        self.sketch_plane = getattr(mesh_data, 'sketch_plane', 'XY')

        # PRESERVE ORDER: Use list instead of set to maintain selection order
        self.selected_points = []  # Point IDs (actual IDs from mesh_data) in order selected
        self.hidden_points = set()  # Point IDs that are hidden

        # LAYER FILTERING: Track which layers are visible
        self.visible_layers = set()  # Will be populated with all layers initially

        # 3D view parameters
        self.rotation_x = 30  # degrees
        self.rotation_y = -45  # degrees
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Track current view state for toggling
        self._current_view = None  # 'x', 'y', 'z', or 'iso'
        self._view_positive = True  # True for +ve, False for -ve

        # Mouse interaction state
        self._drag_data = {"x": 0, "y": 0, "action": None}

        # Cache
        self._point_list = []  # List of (point_id, coords) in order
        self._screen_coords = {}  # point_id -> (x, y) on canvas

        # Colors for dark mode
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'grid': '#404040',
            'text': '#cccccc',
            'x_axis': '#ff4444',  # Red
            'y_axis': '#44ff44',  # Green  
            'z_axis': '#4444ff',  # Blue
            'selected': '#00ff00',  # Bright green
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

        # Fit All button
        tk.Button(self.toolbar, text="Fit All", command=self.fit_all, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)

        # Separator
        tk.Frame(self.toolbar, bg='#555555', width=2, height=16).pack(side=tk.LEFT, padx=5, pady=2)

        # Reset and Refresh buttons
        tk.Button(self.toolbar, text="⟲ Reset", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(self.toolbar, text="⟳ Refresh", command=self.refresh, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)

        # Separator
        tk.Frame(self.toolbar, bg='#555555', width=2, height=16).pack(side=tk.LEFT, padx=5, pady=2)

        # View buttons with toggle functionality
        tk.Label(self.toolbar, text="Views:", bg='#2d2d2d', fg='white', font=('Arial', 9)).pack(side=tk.LEFT)

        self.view_buttons = {}
        for axis in ['x', 'y', 'z']:
            btn = tk.Button(self.toolbar, text=axis.upper(), 
                          command=lambda a=axis: self.set_view(a), **btn_style)
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            self.view_buttons[axis] = btn

        tk.Button(self.toolbar, text="Iso", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=1, pady=2)

        # Sketch plane indicator
        self.plane_label = tk.Label(self.toolbar, text=f"Plane: {self.sketch_plane}", 
                                   bg='#2d2d2d', fg='#aaaaaa', font=('Arial', 8))
        self.plane_label.pack(side=tk.RIGHT, padx=10)

        # Info label at bottom (floating)
        self.info_label = tk.Label(self.frame, 
                                  text=f"Middle: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}", 
                                  bg='#2d2d2d', fg=self.colors['text'], font=('Arial', 8))
        self.info_label.place(x=10, rely=1.0, y=-10, anchor='sw')

        # Bind events – same as Tab4/5: Middle=Rotate, Right=Pan, Left=Select
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-2>", self._on_middle_click)
        self.canvas.bind("<B2-Motion>", self._on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_middle_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>", self._on_scroll)
        self.canvas.bind("<Button-5>", self._on_scroll)
        self.canvas.bind("<Configure>", lambda e: self.draw())

    def _rebuild_coord_cache(self):
        """Cache all point coordinates with their actual IDs"""
        # Update sketch plane in case it changed
        self.sketch_plane = getattr(self.mesh_data, 'sketch_plane', 'XY')
        self.plane_label.config(text=f"Plane: {self.sketch_plane}")
        self.info_label.config(text=f"Left: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}")

        self._point_list = []  # List of (point_id, coords)

        # LAYER FILTERING: Only include visible layers
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
                    # Get standard (X, Y, Z) coordinates
                    coord_3d = np.array([point_data['x'], point_data['y'], point_data['z']])
                    self._point_list.append((point_id, coord_3d))

    def _rotate_point(self, point):
        """Apply rotation to a 3D point - Z is UP"""
        x, y, z = point

        # Rotate around X axis (rotates Z towards Y)
        rad_x = math.radians(self.rotation_x)
        cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

        # Rotate around Y axis (rotates X towards Z)
        rad_y = math.radians(self.rotation_y)
        cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
        z, x = z * cos_y - x * sin_y, z * sin_y + x * cos_y

        return np.array([x, y, z])

    def _project(self, point_3d):
        """Project 3D point to 2D canvas coordinates"""
        rotated = self._rotate_point(point_3d)
        x, y = rotated[0], rotated[1]  # X right, Y up (Z is depth)

        cx = self.canvas.winfo_width() / 2 + self.pan_x
        cy = self.canvas.winfo_height() / 2 + self.pan_y

        screen_x = cx + x * self.zoom * 5
        screen_y = cy - y * self.zoom * 5  # Y up means subtract

        return screen_x, screen_y, rotated[2]  # Return Z as depth

    def draw(self):
        """Redraw the 3D scene"""
        self.canvas.delete("all")

        if len(self._point_list) == 0:
            self._draw_axes_widget()
            return

        # Brighter colors for dark mode
        color_map = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']

        # LAYER FILTERING: Build layer to color mapping
        if self.visible_layers:
            layer_list = sorted([ln for ln in self.mesh_data.layers.keys() 
                                if ln in self.visible_layers], 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))
        else:
            layer_list = sorted(self.mesh_data.layers.keys(), 
                               key=lambda x: self.mesh_data.layers[x].get('z', 0))
        layer_to_idx = {name: i for i, name in enumerate(layer_list)}

        # Calculate all screen coordinates
        self._screen_coords = {}
        projected_points = []

        for point_id, coord in self._point_list:
            if point_id in self.hidden_points:
                continue
            screen_x, screen_y, z_depth = self._project(coord)
            self._screen_coords[point_id] = (screen_x, screen_y)
            projected_points.append((point_id, screen_x, screen_y, z_depth, coord))

        # Sort by Z depth (painter's algorithm)
        projected_points.sort(key=lambda x: x[3], reverse=True)

        # Group by layer for coloring
        points_by_layer = {i: [] for i in range(len(layer_list))}
        selected_points_list = []

        for point_id, screen_x, screen_y, z_depth, coord in projected_points:
            # Find which layer this point belongs to
            layer_name = None
            for ln in layer_list:
                if point_id in self.mesh_data.layers.get(ln, {}).get('point_refs', []):
                    layer_name = ln
                    break

            if layer_name is None:
                continue
            layer_idx = layer_to_idx.get(layer_name, 0)

            # Check if selected - use point_id not index
            if point_id in self.selected_points:
                selected_points_list.append((point_id, screen_x, screen_y, coord))
            else:
                points_by_layer[layer_idx].append((point_id, screen_x, screen_y, coord))

        # Draw connections first
        self._draw_connections(layer_to_idx, layer_list, color_map)

        # Draw unselected points with their ACTUAL point IDs
        for layer_idx in sorted(points_by_layer.keys(), reverse=True):
            pts = points_by_layer[layer_idx]
            color = color_map[layer_idx % len(color_map)]

            for point_id, x, y, coord in pts:
                r = 6
                self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                       fill=color, outline='white', width=1,
                                       tags=f"point_{point_id}")
                # Show ACTUAL point ID with larger, more visible text
                label = f"{point_id}"
                # Draw text with outline effect for visibility
                self.canvas.create_text(x+1, y-12, text=label, 
                                       fill='black', font=('Arial', 10, 'bold'),
                                       tags=f"label_bg_{point_id}")
                self.canvas.create_text(x, y-13, text=label, 
                                       fill='white', font=('Arial', 10, 'bold'),
                                       tags=f"label_{point_id}")

        # Draw selected points (on top, larger) - use point_id
        # Preserve selection order
        order_map = {pid: i for i, pid in enumerate(self.selected_points)}
        selected_points_list.sort(key=lambda x: order_map.get(x[0], 999))

        for point_id, x, y, coord in selected_points_list:
            r = 10
            self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                   fill=self.colors['selected'], outline='darkgreen', width=2,
                                   tags=f"point_{point_id}")
            label = f"{point_id}*"
            # Draw text with outline effect for visibility
            self.canvas.create_text(x+1, y-17, text=label, 
                                   fill='black', font=('Arial', 11, 'bold'),
                                   tags=f"label_bg_{point_id}")
            self.canvas.create_text(x, y-18, text=label, 
                                   fill='#00ff00', font=('Arial', 11, 'bold'),
                                   tags=f"label_{point_id}")

        # Draw axes widget last (on top of everything)
        self._draw_axes_widget()

    def _draw_connections(self, layer_to_idx, layer_list, color_map):
        """Draw lines between connected points - FIXED for new data structure"""
        # Get all connections from mesh_data.connections (flat dict, not by layer)
        all_connections = getattr(self.mesh_data, 'connections', {})

        # Get hidden connections from parent tab (edges hide their underlying connections)
        hidden_conns = getattr(self.parent_tab, '_get_hidden_connections', lambda: set())()

        # Draw each connection
        for conn_id, conn_data in all_connections.items():
            # Skip hidden connections (those that have edges)
            if conn_id in hidden_conns:
                continue

            p1_id = conn_data.get('point1')
            p2_id = conn_data.get('point2')

            if (p1_id in self.hidden_points or p2_id in self.hidden_points or
                p1_id not in self._screen_coords or p2_id not in self._screen_coords):
                continue

            # Get layer color for the connection (use first point's layer)
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
        """Handle point picking only - uses ACTUAL point IDs"""
        clicked_point = None
        min_dist = float('inf')

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

            self.parent_tab.on_selection_changed(self.selected_points.copy())
            self.draw()

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
        """Handle zoom - INCREASED ZOOM LIMITS"""
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9

        # INCREASED: Allow zoom from 0.01 to 1000.0 (was 0.1 to 10.0)
        self.zoom = max(0.01, min(1000.0, self.zoom))
        self.draw()

    def fit_all(self):
        """Zoom and pan to fit all visible points"""
        if len(self._point_list) == 0:
            return

        coords = np.array([c for _, c in self._point_list])
        min_coords = coords.min(axis=0)
        max_coords = coords.max(axis=0)
        center = (min_coords + max_coords) / 2

        self.pan_x = 0
        self.pan_y = 0

        temp_zoom = self.zoom
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

        # INCREASED: Allow zoom from 0.01 to 1000.0 (was 0.1 to 10.0)
        self.zoom = max(0.01, min(1000.0, self.zoom))
        self.draw()

    def set_view(self, axis):
        """
        Set view perpendicular to specified axis with toggle functionality.
        """
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
        if hasattr(self.parent_tab, 'update_point_list'):
            self.parent_tab.update_point_list()

    def set_selection(self, point_ids):
        """Set selection from outside - expects actual point IDs"""
        if isinstance(point_ids, set):
            self.selected_points = list(point_ids)
        else:
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
        """Set which layers should be visible. Empty set means show all."""
        self.visible_layers = set(layer_names)
        self._rebuild_coord_cache()
        # Clear selection if selected points are not in visible points
        visible_ids = {pid for pid, _ in self._point_list}
        self.selected_points = [pid for pid in self.selected_points if pid in visible_ids]
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