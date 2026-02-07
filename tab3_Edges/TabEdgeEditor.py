"""
Tab 3: Edge Editor - Define splines, arcs, and polyLines for blockMeshDict edges
"""
import tkinter as tk
from tkinter import messagebox, ttk
import math
import numpy as np


class TabEdgeEditor:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Edge storage - list of edge definitions
        # Each edge: {'type': 'arc'|'spline'|'polyLine'|'line', 
        #             'start': global_idx, 'end': global_idx, 
        #             'points': [(x,y,z), ...], 'intermediate': [global_idx, ...]}
        if not hasattr(self.mesh_data, 'edges'):
            self.mesh_data.edges = []
        
        # Selection state
        self.selected_points = []  # For selecting start/end points
        self.current_edge_type = tk.StringVar(value='arc')
        self.editing_edge_idx = None
        
        # For arc: need center point (can be existing point or manually defined)
        self.arc_center_mode = tk.StringVar(value='existing')  # 'existing' or 'manual'
        self.arc_center_point = None  # global_idx if existing, (x,y,z) if manual
        
        # For spline/polyLine: list of intermediate points
        self.spline_points = []  # list of global indices or (x,y,z) tuples
        
        # 3D viewer reference (will be created in setup_ui)
        self.viewer = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the edge editor interface"""
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View with edge rendering
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Edge Editor - Select points to define curved edges",
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # 3D Viewer Frame
        viewer_frame = tk.Frame(left_frame, bg='#1e1e1e')
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Import and create embedded viewer
        from tab4_Hex.embedded_viewer import EmbeddedViewer
        self.viewer = EmbeddedViewer(viewer_frame, self.mesh_data, self)
        
        # Override viewer's draw method to include edges
        self._override_viewer_draw()
        
        # Info label
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.info_label = tk.Label(control_frame, 
                                  text="Step 1: Select start point | Mode: Arc",
                                  font=("Arial", 10, "bold"), fg="blue")
        self.info_label.pack(side=tk.LEFT, padx=10)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Notebook for sub-tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create sub-tabs
        self.tab_create = tk.Frame(self.notebook)
        self.tab_manage = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_create, text="1. Create Edge")
        self.notebook.add(self.tab_manage, text="2. Manage Edges")
        
        self._setup_create_tab()
        self._setup_manage_tab()
        
        # Initialize
        self._update_ui_state()
        
    def _override_viewer_draw(self):
        """Override the viewer's draw method to render edges"""
        original_draw = self.viewer.draw
        
        def draw_with_edges():
            # Call original draw first
            original_draw()
            # Then draw edges on top
            self._draw_edges()
            
        self.viewer.draw = draw_with_edges
        
    def _draw_edges(self):
        """Render all defined edges in the 3D viewer"""
        for edge in self.mesh_data.edges:
            self._draw_single_edge(edge)
            
        # Draw currently being defined edge (preview)
        self._draw_preview_edge()
        
    def _draw_single_edge(self, edge):
        """Draw a single edge based on its type"""
        edge_type = edge.get('type', 'line')
        start_idx = edge['start']
        end_idx = edge['end']
        
        # Get 3D coordinates
        start_coords = self._get_point_coords(start_idx)
        end_coords = self._get_point_coords(end_idx)
        
        if start_coords is None or end_coords is None:
            return
            
        # Project to screen
        sx1, sy1, _ = self.viewer._project(np.array(start_coords))
        sx2, sy2, _ = self.viewer._project(np.array(end_coords))
        
        if edge_type == 'line':
            # Draw straight line (but edges replace connections, so this shouldn't happen)
            self.viewer.canvas.create_line(sx1, sy1, sx2, sy2, 
                                          fill='#ff00ff', width=3, dash=(5, 3))
        
        elif edge_type == 'arc':
            # Draw arc through center point
            center = edge.get('center')
            if center:
                if isinstance(center, int):
                    cx, cy, cz = self._get_point_coords(center)
                else:
                    cx, cy, cz = center
                    
                # Project center
                scx, scy, _ = self.viewer._project(np.array([cx, cy, cz]))
                
                # Draw arc as series of line segments
                points = self._calculate_arc_points(start_coords, end_coords, (cx, cy, cz))
                screen_points = []
                for p in points:
                    spx, spy, _ = self.viewer._project(np.array(p))
                    screen_points.append((spx, spy))
                
                # Draw the arc
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='#00ffff', width=3)
                
                # Draw center point marker
                self.viewer.canvas.create_oval(scx-4, scy-4, scx+4, scy+4,
                                              fill='cyan', outline='white')
                self.viewer.canvas.create_text(scx, scy-10, text="C", fill='cyan',
                                              font=('Arial', 8, 'bold'))
        
        elif edge_type in ['spline', 'polyLine']:
            # Draw spline through intermediate points
            intermediate = edge.get('intermediate', [])
            if intermediate:
                all_points = [start_coords]
                for pt in intermediate:
                    if isinstance(pt, int):
                        coords = self._get_point_coords(pt)
                    else:
                        coords = pt
                    all_points.append(coords)
                all_points.append(end_coords)
                
                # Draw as connected line segments
                screen_points = []
                for p in all_points:
                    spx, spy, _ = self.viewer._project(np.array(p))
                    screen_points.append((spx, spy))
                
                color = '#ffaa00' if edge_type == 'spline' else '#00ffaa'
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill=color, width=3)
        
        # Draw start and end markers
        self.viewer.canvas.create_oval(sx1-6, sy1-6, sx1+6, sy1+6,
                                      fill='green', outline='white', width=2)
        self.viewer.canvas.create_oval(sx2-6, sy2-6, sx2+6, sy2+6,
                                      fill='red', outline='white', width=2)
        
    def _draw_preview_edge(self):
        """Draw preview of edge being created"""
        if len(self.selected_points) == 0:
            return
            
        # Draw selected points highlighted
        for i, idx in enumerate(self.selected_points):
            coords = self._get_point_coords(idx)
            if coords:
                sx, sy, _ = self.viewer._project(np.array(coords))
                color = 'yellow' if i == 0 else 'orange'
                r = 8
                self.viewer.canvas.create_oval(sx-r, sy-r, sx+r, sy+r,
                                              fill=color, outline='white', width=2)
                self.viewer.canvas.create_text(sx, sy-15, text=f"S{i+1}", 
                                              fill=color, font=('Arial', 10, 'bold'))
        
        # Draw preview based on current mode
        if len(self.selected_points) >= 2:
            start = self._get_point_coords(self.selected_points[0])
            end = self._get_point_coords(self.selected_points[1])
            
            edge_type = self.current_edge_type.get()
            
            if edge_type == 'arc' and self.arc_center_point:
                # Preview arc
                if isinstance(self.arc_center_point, int):
                    center = self._get_point_coords(self.arc_center_point)
                else:
                    center = self.arc_center_point
                    
                if center:
                    points = self._calculate_arc_points(start, end, center)
                    screen_points = []
                    for p in points:
                        spx, spy, _ = self.viewer._project(np.array(p))
                        screen_points.append((spx, spy))
                    
                    for i in range(len(screen_points) - 1):
                        self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                      screen_points[i+1][0], screen_points[i+1][1],
                                                      fill='cyan', width=2, dash=(4, 2))
            
            elif edge_type in ['spline', 'polyLine'] and self.spline_points:
                # Preview spline
                all_points = [start]
                for pt in self.spline_points:
                    if isinstance(pt, int):
                        coords = self._get_point_coords(pt)
                    else:
                        coords = pt
                    all_points.append(coords)
                all_points.append(end)
                
                screen_points = []
                for p in all_points:
                    spx, spy, _ = self.viewer._project(np.array(p))
                    screen_points.append((spx, spy))
                
                color = 'orange' if edge_type == 'spline' else 'lightgreen'
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill=color, width=2, dash=(4, 2))
        
    def _calculate_arc_points(self, start, end, center, num_segments=20):
        """Calculate points along an arc from start to end through center"""
        # Convert to numpy arrays
        s = np.array(start)
        e = np.array(end)
        c = np.array(center)
        
        # Calculate radii
        r1 = np.linalg.norm(s - c)
        r2 = np.linalg.norm(e - c)
        
        # Average radius
        r = (r1 + r2) / 2
        
        # Calculate angles
        angle_start = math.atan2(s[1] - c[1], s[0] - c[0])
        angle_end = math.atan2(e[1] - c[1], e[0] - c[0])
        
        # Ensure we go the shorter way around
        angle_diff = angle_end - angle_start
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            angle = angle_start + t * angle_diff
            # Calculate point on arc (keeping z-coordinate interpolated)
            z = s[2] + t * (e[2] - s[2])
            x = c[0] + r * math.cos(angle)
            y = c[1] + r * math.sin(angle)
            points.append((x, y, z))
        
        return points
        
    def _get_point_coords(self, global_idx):
        """Get 3D coordinates for a global point index"""
        layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
        if layer is None:
            return None
        point_2d = self.mesh_data.points[layer][local_idx]
        return self.mesh_data.get_3d_coords_standard(layer, point_2d)
        
    def _setup_create_tab(self):
        """Setup the edge creation tab"""
        frame = tk.Frame(self.tab_create)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Edge type selection
        type_frame = tk.LabelFrame(frame, text="Edge Type", padx=10, pady=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        for edge_type, label in [('arc', 'Arc (circular)'), 
                                  ('spline', 'Spline (smooth curve)'),
                                  ('polyLine', 'PolyLine (straight segments)'),
                                  ('line', 'Line (straight)')]:
            tk.Radiobutton(type_frame, text=label, variable=self.current_edge_type,
                          value=edge_type, command=self._on_edge_type_changed,
                          font=("Arial", 10)).pack(anchor=tk.W, pady=2)
        
        # Dynamic configuration frame
        self.config_frame = tk.LabelFrame(frame, text="Configuration", padx=10, pady=10)
        self.config_frame.pack(fill=tk.X, pady=10)
        
        # Arc configuration
        self.arc_config = tk.Frame(self.config_frame)
        tk.Label(self.arc_config, text="Center Point:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        tk.Radiobutton(self.arc_config, text="Select existing point", 
                      variable=self.arc_center_mode, value='existing').pack(anchor=tk.W)
        tk.Radiobutton(self.arc_config, text="Manual coordinates",
                      variable=self.arc_center_mode, value='manual').pack(anchor=tk.W)
        
        self.manual_center_frame = tk.Frame(self.arc_config)
        self.manual_center_frame.pack(fill=tk.X, pady=5)
        
        self.center_x = tk.DoubleVar(value=0.0)
        self.center_y = tk.DoubleVar(value=0.0)
        self.center_z = tk.DoubleVar(value=0.0)
        
        for i, (label, var) in enumerate([('X:', self.center_x), ('Y:', self.center_y), ('Z:', self.center_z)]):
            tk.Label(self.manual_center_frame, text=label).grid(row=0, column=i*2)
            tk.Entry(self.manual_center_frame, textvariable=var, width=8).grid(row=0, column=i*2+1, padx=2)
        
        tk.Button(self.arc_config, text="Set Center", command=self._set_arc_center,
                 bg="lightblue").pack(fill=tk.X, pady=5)
        
        # Spline/PolyLine configuration
        self.spline_config = tk.Frame(self.config_frame)
        tk.Label(self.spline_config, text="Intermediate Points:", 
                font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.spline_listbox = tk.Listbox(self.spline_config, height=6)
        self.spline_listbox.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(self.spline_config)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Point", command=self._add_spline_point,
                 bg="lightgreen").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Remove Last", command=self._remove_spline_point,
                 bg="salmon").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self._clear_spline_points,
                 bg="yellow").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Selection status
        status_frame = tk.LabelFrame(frame, text="Selection Status", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(status_frame, text="Select start point", 
                                    font=("Courier", 10), justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W)
        
        # Action buttons
        action_frame = tk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(action_frame, text="✓ Create Edge", command=self._create_edge,
                 bg="lightgreen", font=("Arial", 11, "bold"), height=2).pack(fill=tk.X, pady=2)
        tk.Button(action_frame, text="✗ Cancel / Reset", command=self._reset_creation,
                 bg="salmon", font=("Arial", 10)).pack(fill=tk.X, pady=2)
        
        # Help text
        help_text = """How to create edges:
1. Select edge type above
2. Click start point in 3D view
3. Click end point in 3D view
4. Add intermediate points (spline/polyLine) or center (arc)
5. Click Create Edge

The original straight connection will be replaced."""
        
        tk.Label(frame, text=help_text, font=("Courier", 9), fg="darkblue",
                justify=tk.LEFT, bg='#f0f0f0').pack(fill=tk.X, pady=10)
        
    def _setup_manage_tab(self):
        """Setup the edge management tab"""
        frame = tk.Frame(self.tab_manage)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Defined Edges", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        # Edge list
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.edge_listbox = tk.Listbox(list_frame, font=("Courier", 10),
                                       yscrollcommand=scroll.set, bg='#2d2d2d', fg='white')
        self.edge_listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.edge_listbox.yview)
        
        self.edge_listbox.bind('<<ListboxSelect>>', self._on_edge_select)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Delete Selected", command=self._delete_edge,
                 bg="salmon", width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete All", command=self._delete_all_edges,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Highlight", command=self._highlight_edge,
                 bg="lightblue", width=12).pack(side=tk.LEFT, padx=2)
        
        # Edge details
        self.edge_details = tk.Label(frame, text="", font=("Courier", 9),
                                    justify=tk.LEFT, fg="gray")
        self.edge_details.pack(anchor=tk.W, pady=10)
        
        self._update_edge_list()
        
    def _on_edge_type_changed(self):
        """Handle edge type change"""
        self._update_ui_state()
        self._reset_creation()
        
    def _update_ui_state(self):
        """Update UI based on current edge type"""
        edge_type = self.current_edge_type.get()
        
        # Hide all config frames
        self.arc_config.pack_forget()
        self.spline_config.pack_forget()
        
        # Show relevant config
        if edge_type == 'arc':
            self.arc_config.pack(fill=tk.X)
            self.info_label.config(text="Step 1: Select start point | Mode: Arc")
        elif edge_type in ['spline', 'polyLine']:
            self.spline_config.pack(fill=tk.X)
            self.info_label.config(text=f"Step 1: Select start point | Mode: {edge_type}")
        else:
            self.info_label.config(text="Step 1: Select start point | Mode: Line")
            
        self.viewer.draw()
        
    def on_selection_changed(self, selected_list):
        """Called by viewer when points are clicked"""
        edge_type = self.current_edge_type.get()
        
        if len(self.selected_points) == 0:
            # Selecting start point
            if len(selected_list) > 0:
                self.selected_points.append(selected_list[-1])
                self.status_label.config(text=f"Start: {self.selected_points[0]}\nSelect end point")
                self.info_label.config(text="Step 2: Select end point")
                
        elif len(self.selected_points) == 1:
            # Selecting end point
            if len(selected_list) > 1:
                end_point = selected_list[-1]
                if end_point != self.selected_points[0]:
                    self.selected_points.append(end_point)
                    
                    if edge_type == 'arc':
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nNow set center point")
                        self.info_label.config(text="Step 3: Set center point (click existing or enter manual)")
                    elif edge_type in ['spline', 'polyLine']:
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nAdd intermediate points")
                        self.info_label.config(text="Step 3: Add intermediate points (optional)")
                    else:
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nReady to create")
                        self.info_label.config(text="Ready: Click Create Edge")
                        
        else:
            # For arc/spline, additional points can be selected
            if edge_type == 'arc' and self.arc_center_mode.get() == 'existing':
                if len(selected_list) > 2 and not self.arc_center_point:
                    self.arc_center_point = selected_list[-1]
                    self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nCenter: {self.arc_center_point}\nReady to create")
                    self.info_label.config(text="Ready: Click Create Edge")
                    
            elif edge_type in ['spline', 'polyLine']:
                # Add intermediate points
                new_point = selected_list[-1]
                if new_point not in self.selected_points and new_point not in self.spline_points:
                    self.spline_points.append(new_point)
                    self._update_spline_listbox()
                    
        self.viewer.draw()
        
    def _set_arc_center(self):
        """Set the arc center point"""
        if self.arc_center_mode.get() == 'manual':
            self.arc_center_point = (self.center_x.get(), self.center_y.get(), self.center_z.get())
        else:
            messagebox.showinfo("Info", "Click an existing point in the 3D view to select as center")
            return
            
        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nCenter: (manual)\nReady to create")
        self.info_label.config(text="Ready: Click Create Edge")
        self.viewer.draw()
        
    def _add_spline_point(self):
        """Add a point to the spline (manual entry)"""
        # Could open a dialog for manual coordinate entry
        messagebox.showinfo("Info", "Click points in the 3D view to add to spline")
        
    def _remove_spline_point(self):
        """Remove last spline point"""
        if self.spline_points:
            self.spline_points.pop()
            self._update_spline_listbox()
            self.viewer.draw()
            
    def _clear_spline_points(self):
        """Clear all spline points"""
        self.spline_points = []
        self._update_spline_listbox()
        self.viewer.draw()
        
    def _update_spline_listbox(self):
        """Update the spline points listbox"""
        self.spline_listbox.delete(0, tk.END)
        for i, pt in enumerate(self.spline_points):
            if isinstance(pt, int):
                coords = self._get_point_coords(pt)
                self.spline_listbox.insert(tk.END, f"{i+1}. Point {pt}: ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})")
            else:
                self.spline_listbox.insert(tk.END, f"{i+1}. Manual: ({pt[0]:.2f}, {pt[1]:.2f}, {pt[2]:.2f})")
                
    def _create_edge(self):
        """Create the edge and add to mesh_data"""
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need at least start and end points")
            return
            
        edge_type = self.current_edge_type.get()
        edge = {
            'type': edge_type,
            'start': self.selected_points[0],
            'end': self.selected_points[1]
        }
        
        if edge_type == 'arc':
            if not self.arc_center_point:
                messagebox.showwarning("Warning", "Need to define center point for arc")
                return
            edge['center'] = self.arc_center_point
            
            # Calculate arc points for export
            start_coords = self._get_point_coords(self.selected_points[0])
            end_coords = self._get_point_coords(self.selected_points[1])
            if isinstance(self.arc_center_point, int):
                center_coords = self._get_point_coords(self.arc_center_point)
            else:
                center_coords = self.arc_center_point
            edge['arc_points'] = self._calculate_arc_points(start_coords, end_coords, center_coords)
            
        elif edge_type in ['spline', 'polyLine']:
            edge['intermediate'] = self.spline_points.copy()
            
        # Add to mesh_data
        self.mesh_data.edges.append(edge)
        
        # Remove the straight connection if it exists
        self._remove_straight_connection(self.selected_points[0], self.selected_points[1])
        
        messagebox.showinfo("Success", f"{edge_type} edge created!")
        self._reset_creation()
        self._update_edge_list()
        
    def _remove_straight_connection(self, global_idx1, global_idx2):
        """Remove the straight line connection between two points"""
        layer1, local1 = self.mesh_data.get_layer_from_global_index(global_idx1)
        layer2, local2 = self.mesh_data.get_layer_from_global_index(global_idx2)
        
        if layer1 == layer2:
            # Same layer - remove from connections
            conn = tuple(sorted([local1, local2]))
            if conn in self.mesh_data.connections[layer1]:
                self.mesh_data.connections[layer1].remove(conn)
        else:
            # Inter-layer connection
            conn = (layer1, local1, layer2, local2)
            if conn in self.mesh_data.inter_layer_connections:
                self.mesh_data.inter_layer_connections.remove(conn)
                
    def _reset_creation(self):
        """Reset the edge creation state"""
        self.selected_points = []
        self.arc_center_point = None
        self.spline_points = []
        self._update_spline_listbox()
        self.status_label.config(text="Select start point")
        self._update_ui_state()
        self.viewer.clear_selection()
        
    def _update_edge_list(self):
        """Update the edge listbox"""
        self.edge_listbox.delete(0, tk.END)
        for i, edge in enumerate(self.mesh_data.edges):
            edge_type = edge['type']
            start = edge['start']
            end = edge['end']
            self.edge_listbox.insert(tk.END, f"Edge {i}: {edge_type} ({start} → {end})")
            
    def _on_edge_select(self, event):
        """Handle edge selection"""
        sel = self.edge_listbox.curselection()
        if sel:
            idx = sel[0]
            edge = self.mesh_data.edges[idx]
            details = f"Type: {edge['type']}\nStart: {edge['start']}\nEnd: {edge['end']}"
            if 'center' in edge:
                details += f"\nCenter: {edge['center']}"
            if 'intermediate' in edge:
                details += f"\nIntermediate points: {len(edge['intermediate'])}"
            self.edge_details.config(text=details)
            
    def _delete_edge(self):
        """Delete selected edge"""
        sel = self.edge_listbox.curselection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete selected edge?"):
            idx = sel[0]
            del self.mesh_data.edges[idx]
            self._update_edge_list()
            self.edge_details.config(text="")
            self.viewer.draw()
            
    def _delete_all_edges(self):
        """Delete all edges"""
        if not self.mesh_data.edges:
            return
        if messagebox.askyesno("Confirm", "Delete all edges?"):
            self.mesh_data.edges = []
            self._update_edge_list()
            self.edge_details.config(text="")
            self.viewer.draw()
            
    def _highlight_edge(self):
        """Highlight selected edge in viewer"""
        sel = self.edge_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        edge = self.mesh_data.edges[idx]
        # Select the edge's points in viewer
        points_to_select = [edge['start'], edge['end']]
        if 'intermediate' in edge:
            for pt in edge['intermediate']:
                if isinstance(pt, int):
                    points_to_select.append(pt)
        self.viewer.set_selection(points_to_select)
        
    def cleanup(self):
        """Cleanup when closing"""
        if self.viewer:
            self.viewer.close()