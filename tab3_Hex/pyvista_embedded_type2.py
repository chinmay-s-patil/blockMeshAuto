"""
Embedded 3D Viewer for Tkinter - Pure Tkinter implementation
No PyVista, No VTK, No Matplotlib, No Plotly
Dark Mode with View Controls and Rotating Axes
HANDLES: XZ plane input (Y is layer/height), displays as standard XYZ
"""
import tkinter as tk
from tkinter import messagebox
import numpy as np
import math

class EmbeddedPyVistaViewer:
    """3D viewer embedded in a tkinter frame using Canvas"""
    def init(self, parent_frame, mesh_data, parent_tab):
        self.parent_frame = parent_frame
        self.mesh_data = mesh_data
        self.parent_tab = parent_tab
        self.selected_points = set()  # Global indices
        self.hidden_points = set()
        
        # 3D view parameters
        self.rotation_x = 30  # degrees
        self.rotation_y = -45  # degrees
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Mouse interaction state
        self._drag_data = {"x": 0, "y": 0, "action": None}
        
        # Cache
        self._global_coords = None  # Will store transformed coords (X, Y, Z)
        self._global_to_local = {}
        self._screen_coords = {}  # global_idx -> (x, y) on canvas
        
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
        # Toolbar frame at top
        self.toolbar = tk.Frame(self.parent_frame, bg='#2d2d2d')
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # View control buttons
        btn_style = {'bg': '#404040', 'fg': 'white', 'relief': tk.FLAT, 
                    'font': ('Arial', 9, 'bold'), 'padx': 8, 'pady': 2}
        
        tk.Button(self.toolbar, text="Fit All", command=self.fit_all, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Frame(self.toolbar, bg='#2d2d2d', width=20).pack(side=tk.LEFT)
        
        tk.Label(self.toolbar, text="Views:", bg='#2d2d2d', fg='white', font=('Arial', 9)).pack(side=tk.LEFT)
        
        tk.Button(self.toolbar, text="X", command=lambda: self.set_view('x'), **btn_style).pack(side=tk.LEFT, padx=1)
        tk.Button(self.toolbar, text="Y", command=lambda: self.set_view('y'), **btn_style).pack(side=tk.LEFT, padx=1)
        tk.Button(self.toolbar, text="Z", command=lambda: self.set_view('z'), **btn_style).pack(side=tk.LEFT, padx=1)
        tk.Button(self.toolbar, text="Iso", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=1)
        
        # Main canvas
        self.frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.frame, bg=self.colors['bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Info label at bottom
        self.info_label = tk.Label(self.frame, 
                                text="Left: Rotate | Right: Pan | Scroll: Zoom | Click: Select", 
                                bg='#2d2d2d', fg=self.colors['text'], font=('Arial', 8))
        self.info_label.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>", self._on_scroll)
        self.canvas.bind("<Button-5>", self._on_scroll)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        
    def _transform_coordinate(self, layer_name, point_2d, layer_z):
        """
        Transform from JSON coordinate system to display coordinate system.
        
        JSON Input: point_2d = (x, z), layer_z = y (height)
        Display: (x, y, z) where y is up
        """
        x, z = point_2d  # JSON has X and Z as the plane
        y = layer_z      # Layer value is actually Y (height) in standard CFD coords
        
        # Return as (X, Y, Z) for standard right-handed coordinate system
        return np.array([x, y, z])
        
    def _rebuild_coord_cache(self):
        """Cache all global point coordinates with proper transform"""
        coords = []
        self._global_to_local = {}
        
        idx = 0
        layer_list = sorted(self.mesh_data.layers.keys(), 
                        key=lambda x: self.mesh_data.layers[x])
        
        for layer_name in layer_list:
            if layer_name in self.mesh_data.points:
                layer_y = self.mesh_data.layers[layer_name]  # This is the Y coordinate
                for local_idx, pt_2d in enumerate(self.mesh_data.points[layer_name]):
                    # pt_2d is (x, z) from JSON
                    coord_3d = self._transform_coordinate(layer_name, pt_2d, layer_y)
                    coords.append(coord_3d)
                    self._global_to_local[idx] = (layer_name, local_idx)
                    idx += 1
                    
        self._global_coords = np.array(coords) if coords else np.array([])
        self._total_points = idx
        
    def _rotate_point(self, point):
        """Apply rotation to a 3D point"""
        x, y, z = point
            
        # Rotate around X axis (rotates Y towards Z)
        rad_x = math.radians(self.rotation_x)
        cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
            
        # Rotate around Y axis (rotates Z towards X)
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
        
        if len(self._global_coords) == 0:
            self._draw_axes_widget()  # Still draw axes even if no points
            return
            
        # Brighter colors for dark mode
        color_map = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
        layer_list = sorted(self.mesh_data.layers.keys(), 
                        key=lambda x: self.mesh_data.layers[x])
        layer_to_idx = {name: i for i, name in enumerate(layer_list)}
        
        # Calculate all screen coordinates
        self._screen_coords = {}
        projected_points = []
        
        for global_idx, coord in enumerate(self._global_coords):
            if global_idx in self.hidden_points:
                continue
            screen_x, screen_y, z_depth = self._project(coord)
            self._screen_coords[global_idx] = (screen_x, screen_y)
            projected_points.append((global_idx, screen_x, screen_y, z_depth, coord))
        
        # Sort by Z depth (painter's algorithm)
        projected_points.sort(key=lambda x: x[3], reverse=True)
        
        points_by_layer = {i: [] for i in range(len(self.mesh_data.layers))}
        selected_points_list = []
        
        for global_idx, screen_x, screen_y, z_depth, coord in projected_points:
            layer_name, _ = self._global_to_local[global_idx]
            layer_idx = layer_to_idx[layer_name]
            
            if global_idx in self.selected_points:
                selected_points_list.append((global_idx, screen_x, screen_y, coord))
            else:
                points_by_layer[layer_idx].append((global_idx, screen_x, screen_y, coord))
        
        # Draw connections first
        self._draw_connections(layer_to_idx, layer_list, color_map)
        
        # Draw hex blocks wireframes
        self._draw_hex_blocks()
        
        # Draw unselected points
        for layer_idx in sorted(points_by_layer.keys(), reverse=True):
            pts = points_by_layer[layer_idx]
            color = color_map[layer_idx % len(color_map)]
            
            for global_idx, x, y, coord in pts:
                r = 6
                self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                    fill=color, outline='white', width=1,
                                    tags=f"point_{global_idx}")
                # Show coordinates in X,Y,Z format
                self.canvas.create_text(x, y-10, text=str(global_idx), 
                                    fill=color, font=('Courier', 9, 'bold'),
                                    tags=f"label_{global_idx}")
        
        # Draw selected points (on top, larger)
        for global_idx, x, y, coord in selected_points_list:
            r = 10
            self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                fill=self.colors['selected'], outline='darkgreen', width=2,
                                tags=f"point_{global_idx}")
            self.canvas.create_text(x, y-15, text=f"{global_idx}*", 
                                fill=self.colors['selected'], font=('Courier', 10, 'bold'),
                                tags=f"label_{global_idx}")
        
        # Draw axes widget last (on top of everything)
        self._draw_axes_widget()

    def _draw_connections(self, layer_to_idx, layer_list, color_map):
        """Draw lines between connected points"""
        for layer_name in layer_list:
            if layer_name not in self.mesh_data.connections:
                continue
            layer_idx = layer_to_idx[layer_name]
            color = color_map[layer_idx % len(color_map)]
            
            for conn in self.mesh_data.connections[layer_name]:
                p1_local, p2_local = conn
                p1_global = self._local_to_global(layer_name, p1_local)
                p2_global = self._local_to_global(layer_name, p2_local)
                
                if (p1_global in self.hidden_points or p2_global in self.hidden_points or
                    p1_global not in self._screen_coords or p2_global not in self._screen_coords):
                    continue
                
                x1, y1 = self._screen_coords[p1_global]
                x2, y2 = self._screen_coords[p2_global]
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
        
        # Inter-layer connections (these are vertical connections in Y direction)
        for layer1, idx1, layer2, idx2 in getattr(self.mesh_data, 'inter_layer_connections', []):
            g1 = self._local_to_global(layer1, idx1)
            g2 = self._local_to_global(layer2, idx2)
            
            if (g1 in self.hidden_points or g2 in self.hidden_points or
                g1 not in self._screen_coords or g2 not in self._screen_coords):
                continue
            
            x1, y1 = self._screen_coords[g1]
            x2, y2 = self._screen_coords[g2]
            
            # Inter-layer connections are vertical (Y-direction), draw them differently
            self.canvas.create_line(x1, y1, x2, y2, fill='#888888', width=1, dash=(4, 2))

    def _draw_hex_blocks(self):
        """Draw hex block wireframes"""
        for block in getattr(self.parent_tab, 'hex_blocks', []):
            verts = block['vertices']  # These are already in (X,Y,Z) format from create_hex_block
            
            screen_verts = []
            valid = True
            for v in verts:
                if len(v) == 3:
                    sx, sy, sz = self._project(v)
                    screen_verts.append((sx, sy, sz))
                else:
                    valid = False
                    break
            
            if not valid or len(screen_verts) != 8:
                continue
            
            edges = [(0,1),(1,2),(2,3),(3,0),
                    (4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7)]
            
            for i, j in edges:
                x1, y1, z1 = screen_verts[i]
                x2, y2, z2 = screen_verts[j]
                avg_z = (z1 + z2) / 2
                width = 3 if avg_z > 0 else 2
                self.canvas.create_line(x1, y1, x2, y2, fill='#66ff66', width=width)
            
            # Translucent faces
            faces = [(0,1,2,3), (4,5,6,7), (0,1,5,4), (2,3,7,6), (1,2,6,5), (0,3,7,4)]
            for face in faces:
                points = [(screen_verts[i][0], screen_verts[i][1]) for i in face]
                self.canvas.create_polygon(points, fill='#66ff66', 
                                        stipple='gray50', outline='#44ff44', width=1)

    def _draw_axes_widget(self):
        """Draw rotating axes indicator in bottom right corner"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Position in bottom right with padding
        center_x = w - 50
        center_y = h - 50
        length = 30
        
        # Get rotated basis vectors
        x_vec = self._rotate_point([length, 0, 0])
        y_vec = self._rotate_point([0, length, 0])
        z_vec = self._rotate_point([0, 0, length])
        
        # Draw axis lines (2D projection: we use x and y of rotated vector)
        # X axis - Red
        self.canvas.create_line(center_x, center_y, 
                            center_x + x_vec[0], center_y - x_vec[1],
                            fill=self.colors['x_axis'], width=3, arrow=tk.LAST)
        # Y axis - Green (UP in CFD standard)
        self.canvas.create_line(center_x, center_y, 
                            center_x + y_vec[0], center_y - y_vec[1],
                            fill=self.colors['y_axis'], width=3, arrow=tk.LAST)
        # Z axis - Blue
        self.canvas.create_line(center_x, center_y, 
                            center_x + z_vec[0], center_y - z_vec[1],
                            fill=self.colors['z_axis'], width=3, arrow=tk.LAST)
        
        # Labels
        label_offset = 5
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
        
        # Draw background circle for contrast
        self.canvas.create_oval(center_x-35, center_y-35, center_x+35, center_y+35,
                            outline='#444444', width=1, stipple='gray50')

    def _local_to_global(self, layer_name, local_idx):
        """Convert local index to global index"""
        layer_list = sorted(self.mesh_data.layers.keys(), 
                        key=lambda x: self.mesh_data.layers[x])
        offset = 0
        for name in layer_list:
            if name == layer_name:
                return offset + local_idx
            offset += len(self.mesh_data.points.get(name, []))
        return -1

    def _on_left_click(self, event):
        """Handle point picking"""
        clicked_point = None
        min_dist = float('inf')
        
        for global_idx, (sx, sy) in self._screen_coords.items():
            dist = ((sx - event.x)**2 + (sy - event.y)**2)**0.5
            if dist < 15:
                if dist < min_dist:
                    min_dist = dist
                    clicked_point = global_idx
        
        if clicked_point is not None:
            if clicked_point in self.selected_points:
                self.selected_points.remove(clicked_point)
            else:
                if len(self.selected_points) < 8:
                    self.selected_points.add(clicked_point)
                else:
                    messagebox.showwarning("Limit", "Maximum 8 points allowed")
                    return
            
            self.parent_tab.on_selection_changed(self.selected_points.copy())
            self.draw()
        else:
            self._drag_data = {"x": event.x, "y": event.y, "action": "rotate"}

    def _on_drag(self, event):
        """Handle mouse drag"""
        if self._drag_data["action"] == "rotate":
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]
            
            self.rotation_y += dx * 0.5
            self.rotation_x -= dy * 0.5
            
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            
            self.draw()
        elif self._drag_data["action"] == "pan":
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]
            
            self.pan_x += dx
            self.pan_y += dy
            
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            
            self.draw()

    def _on_release(self, event):
        self._drag_data = {"x": 0, "y": 0, "action": None}

    def _on_right_click(self, event):
        self._drag_data = {"x": event.x, "y": event.y, "action": "pan"}

    def _on_right_drag(self, event):
        if self._drag_data["action"] == "pan":
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]
            
            self.pan_x += dx
            self.pan_y += dy
            
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            
            self.draw()

    def _on_scroll(self, event):
        """Handle zoom"""
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9
        
        self.zoom = max(0.1, min(10.0, self.zoom))
        self.draw()

    def fit_all(self):
        """Zoom and pan to fit all visible points"""
        if len(self._global_coords) == 0:
            return
        
        # Get bounding box of all points
        coords = self._global_coords
        min_coords = coords.min(axis=0)
        max_coords = coords.max(axis=0)
        center = (min_coords + max_coords) / 2
        
        # Reset pan to center the object
        self.pan_x = 0
        self.pan_y = 0
        
        # Project bounds to screen to calculate required zoom
        # First try with current zoom=1 to get size in pixels
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
            self.zoom = (canvas_size / screen_range) * 0.8  # 80% fit with margin
        
        self.zoom = max(0.1, min(10.0, self.zoom))
        self.draw()

    def set_view(self, axis):
        """Set view perpendicular to specified axis"""
        if axis == 'x':
            self.rotation_x = 0
            self.rotation_y = 90  # Look from +X, see YZ plane
        elif axis == 'y':
            self.rotation_x = 0   # Look from +Y down (top view in CFD)
            self.rotation_y = 0
        elif axis == 'z':
            self.rotation_x = 90  # Look from +Z, see XY plane
            self.rotation_y = 0
        self.draw()

    def hide_selected(self):
        """Hide currently selected points"""
        self.hidden_points.update(self.selected_points)
        self.selected_points.clear()
        self.draw()
        self.parent_tab.update_point_list()
        
    def show_only_selected(self):
        """Show only selected points"""
        all_points = set(range(self._total_points))
        self.hidden_points = all_points - self.selected_points
        self.draw()
        
    def show_all(self):
        """Show all points"""
        self.hidden_points.clear()
        self.draw()
        
    def clear_selection(self):
        """Clear selection"""
        self.selected_points.clear()
        self.draw()
        
    def set_selection(self, global_indices):
        """Set selection from outside"""
        self.selected_points = set(global_indices)
        self.draw()
        
    def reset_view(self):
        """Reset camera to isometric view"""
        self.rotation_x = 30
        self.rotation_y = -45
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.draw()
        
    def refresh(self):
        """Refresh view"""
        self._rebuild_coord_cache()
        self.draw()
        
    def close(self):
        """Cleanup"""
        pass