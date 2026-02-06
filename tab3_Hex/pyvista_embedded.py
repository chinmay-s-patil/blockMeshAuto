"""
Embedded 3D Viewer for Tkinter - Pure Tkinter implementation
No PyVista, No VTK, No Matplotlib, No Plotly
Dark Mode with View Controls and Rotating Axes

Coordinate System Handling:
- Reads sketch_plane from mesh_data to determine transformation
- XY plane: points are (x,y), layer is z -> 3D is (x, y, z)
- XZ plane: points are (x,z), layer is y -> 3D is (x, y, z) [swapped]
"""
import tkinter as tk
from tkinter import messagebox
import numpy as np
import math


class EmbeddedPyVistaViewer:
    """3D viewer embedded in a tkinter frame using Canvas"""
    def __init__(self, parent_frame, mesh_data, parent_tab):
        self.parent_frame = parent_frame
        self.mesh_data = mesh_data
        self.parent_tab = parent_tab
        
        # Get sketch plane from mesh data
        self.sketch_plane = getattr(mesh_data, 'sketch_plane', 'XY')
        
        self.selected_points = set()  # Global indices
        self.hidden_points = set()
        
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
        
        # Fit All button
        tk.Button(self.toolbar, text="Fit All", command=self.fit_all, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Separator
        tk.Frame(self.toolbar, bg='#555555', width=2, height=20).pack(side=tk.LEFT, padx=5, pady=2)
        
        # Reset and Refresh buttons
        tk.Button(self.toolbar, text="⟲ Reset", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(self.toolbar, text="⟳ Refresh", command=self.refresh, **btn_style).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Separator
        tk.Frame(self.toolbar, bg='#555555', width=2, height=20).pack(side=tk.LEFT, padx=5, pady=2)
        
        # View buttons with toggle functionality
        tk.Label(self.toolbar, text="Views:", bg='#2d2d2d', fg='white', font=('Arial', 9)).pack(side=tk.LEFT)
        
        self.view_buttons = {}
        for axis in ['x', 'y', 'z']:
            btn = tk.Button(self.toolbar, text=axis.upper(), 
                          command=lambda a=axis: self.set_view(a), **btn_style)
            btn.pack(side=tk.LEFT, padx=1)
            self.view_buttons[axis] = btn
            
        tk.Button(self.toolbar, text="Iso", command=self.reset_view, **btn_style).pack(side=tk.LEFT, padx=1)
        
        # Sketch plane indicator
        self.plane_label = tk.Label(self.toolbar, text=f"Plane: {self.sketch_plane}", 
                                   bg='#2d2d2d', fg='#aaaaaa', font=('Arial', 8))
        self.plane_label.pack(side=tk.RIGHT, padx=10)
        
        # Main canvas
        self.frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.frame, bg=self.colors['bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Info label at bottom
        self.info_label = tk.Label(self.frame, 
                                  text=f"Left: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}", 
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
        
    def _transform_coordinate(self, layer_name, point_2d, layer_value):
        """
        Transform from JSON coordinate system to display coordinate system.
        
        Based on sketch_plane setting:
        - XY plane: point_2d = (x, y), layer_value = z -> 3D is (x, y, z)
        - XZ plane: point_2d = (x, z), layer_value = y -> 3D is (x, y, z) [Y/Z swapped]
        - YZ plane: point_2d = (y, z), layer_value = x -> 3D is (x, y, z) [X/Y/Z cycled]
        
        Display coordinate system: X (right), Y (up/forward), Z (up/height)
        """
        x_2d, y_2d = point_2d
        
        if self.sketch_plane == "XY":
            # XY plane: points are (x, y), layer is z
            x = x_2d
            y = y_2d
            z = layer_value
        elif self.sketch_plane == "XZ":
            # XZ plane: points are (x, z), layer is y
            x = x_2d
            y = layer_value
            z = y_2d
        elif self.sketch_plane == "YZ":
            # YZ plane: points are (y, z), layer is x
            x = layer_value
            y = x_2d
            z = y_2d
        else:
            # Default to XY
            x = x_2d
            y = y_2d
            z = layer_value
        
        return np.array([x, y, z])
        
    def _rebuild_coord_cache(self):
        """Cache all global point coordinates with proper transform"""
        # Update sketch plane in case it changed
        self.sketch_plane = getattr(self.mesh_data, 'sketch_plane', 'XY')
        self.plane_label.config(text=f"Plane: {self.sketch_plane}")
        self.info_label.config(text=f"Left: Rotate | Right: Pan | Scroll: Zoom | Click: Select | Plane: {self.sketch_plane}")
        
        coords = []
        self._global_to_local = {}
        
        idx = 0
        layer_list = sorted(self.mesh_data.layers.keys(), 
                           key=lambda x: self.mesh_data.layers[x])
        
        for layer_name in layer_list:
            # LAYER FILTERING: Skip layers not in visible_layers (if visible_layers is set)
            # If visible_layers is empty, show all layers
            if self.visible_layers and layer_name not in self.visible_layers:
                continue
                
            if layer_name in self.mesh_data.points:
                layer_value = self.mesh_data.layers[layer_name]
                for local_idx, pt_2d in enumerate(self.mesh_data.points[layer_name]):
                    coord_3d = self._transform_coordinate(layer_name, pt_2d, layer_value)
                    coords.append(coord_3d)
                    self._global_to_local[idx] = (layer_name, local_idx)
                    idx += 1
                    
        self._global_coords = np.array(coords) if coords else np.array([])
        self._total_points = idx
        
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
        
        if len(self._global_coords) == 0:
            self._draw_axes_widget()
            return
            
        # Brighter colors for dark mode
        color_map = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
        
        # LAYER FILTERING: Only include visible layers in layer list
        layer_list = sorted([ln for ln in self.mesh_data.layers.keys() 
                            if not self.visible_layers or ln in self.visible_layers], 
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
        
        points_by_layer = {i: [] for i in range(len(layer_list))}
        selected_points_list = []
        
        for global_idx, screen_x, screen_y, z_depth, coord in projected_points:
            layer_name, _ = self._global_to_local[global_idx]
            layer_idx = layer_to_idx.get(layer_name, 0)
            
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
                # Show coordinates
                label = f"{global_idx}:({coord[0]:.1f},{coord[1]:.1f},{coord[2]:.1f})"
                self.canvas.create_text(x, y-10, text=str(global_idx), 
                                       fill=color, font=('Courier', 9, 'bold'),
                                       tags=f"label_{global_idx}")
        
        # Draw selected points (on top, larger)
        for global_idx, x, y, coord in selected_points_list:
            r = 10
            self.canvas.create_oval(x-r, y-r, x+r, y+r, 
                                   fill=self.colors['selected'], outline='darkgreen', width=2,
                                   tags=f"point_{global_idx}")
            label = f"{global_idx}*:({coord[0]:.1f},{coord[1]:.1f},{coord[2]:.1f})"
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
        
        # Inter-layer connections (vertical connections)
        # LAYER FILTERING: Only draw inter-layer connections if both layers are visible
        for layer1, idx1, layer2, idx2 in getattr(self.mesh_data, 'inter_layer_connections', []):
            # Skip if layer filtering is active and either layer is not visible
            if self.visible_layers:
                if layer1 not in self.visible_layers or layer2 not in self.visible_layers:
                    continue
                    
            g1 = self._local_to_global(layer1, idx1)
            g2 = self._local_to_global(layer2, idx2)
            
            if (g1 in self.hidden_points or g2 in self.hidden_points or
                g1 not in self._screen_coords or g2 not in self._screen_coords):
                continue
            
            x1, y1 = self._screen_coords[g1]
            x2, y2 = self._screen_coords[g2]
            
            self.canvas.create_line(x1, y1, x2, y2, fill='#888888', width=1, dash=(4, 2))
    
    def _draw_hex_blocks(self):
        """Draw hex block wireframes"""
        for block in getattr(self.parent_tab, 'hex_blocks', []):
            verts = block.get('vertices', [])
            
            if len(verts) != 8:
                continue
                
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
    
    def _local_to_global(self, layer_name, local_idx):
        """Convert local index to global index - ACCOUNTING FOR LAYER FILTERING"""
        # LAYER FILTERING: If filtering is active, we need to recalculate indices
        if self.visible_layers:
            # Only count layers that are visible
            layer_list = sorted([ln for ln in self.mesh_data.layers.keys() 
                                if ln in self.visible_layers], 
                               key=lambda x: self.mesh_data.layers[x])
        else:
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
            
            self._current_view = None
            self._update_view_button_labels()
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
        
        coords = self._global_coords
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
        
        self.zoom = max(0.1, min(10.0, self.zoom))
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
                self.rotation_x = 0
                self.rotation_y = 0
            else:
                self.rotation_x = 0
                self.rotation_y = 180
                
        elif axis == 'z':
            if self._view_positive:
                self.rotation_x = -90
                self.rotation_y = 0
            else:
                self.rotation_x = 90
                self.rotation_y = 0
        
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
    
    # LAYER FILTERING: New method to set visible layers
    def set_visible_layers(self, layer_names):
        """Set which layers should be visible. Empty set means show all."""
        self.visible_layers = set(layer_names)
        self._rebuild_coord_cache()
        # Clear selection if selected points are in hidden layers
        self.selected_points = {idx for idx in self.selected_points 
                               if idx < self._total_points}
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