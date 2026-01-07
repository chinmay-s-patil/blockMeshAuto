"""
Grid Sizing Tab - Connection Subdivision Controls with Clickable Connections
"""
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np


class TabGridSizing:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.subdiv_var = tk.IntVar(value=10)
        self.global_subdiv_var = tk.IntVar(value=10)
        
        # Connection tracking
        self.connections_data = []  # List of (start_3d, end_3d, type, info_dict)
        self.selected_connection_idx = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Connection View - Click connections to select", 
                font=("Arial", 12, "bold")).pack()
        
        self.fig_grid_3d = Figure(figsize=(7, 7))
        self.ax_grid_3d = self.fig_grid_3d.add_subplot(111, projection='3d')
        self.canvas_grid_3d = FigureCanvasTkAgg(self.fig_grid_3d, left_frame)
        self.canvas_grid_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_grid_3d, toolbar_frame)
        toolbar.update()
        
        self.canvas_grid_3d.mpl_connect('button_press_event', self.on_grid_3d_click)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update View", command=self.update_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        self._setup_selection_info(right_frame)
        self._setup_grid_controls(right_frame)
        self._setup_global_controls(right_frame)
        
    def _setup_selection_info(self, parent):
        sel_frame = tk.LabelFrame(parent, text="Selected Connection", padx=10, pady=10)
        sel_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(sel_frame, text="Click a connection in the 3D view", 
                font=("Arial", 9, "italic"), fg="gray").pack(pady=(0, 5))
        
        self.selected_conn_label = tk.Label(sel_frame, text="None selected", 
                                           fg="blue", font=("Arial", 10, "bold"),
                                           wraplength=300, justify=tk.LEFT)
        self.selected_conn_label.pack(pady=5)
        
        self.conn_type_label = tk.Label(sel_frame, text="", fg="darkgreen",
                                        font=("Arial", 9))
        self.conn_type_label.pack(pady=2)
        
        tk.Button(sel_frame, text="Clear Selection", 
                 command=self.clear_selection, bg="lightgray").pack(fill=tk.X, pady=5)
    
    def _setup_grid_controls(self, parent):
        grid_frame = tk.LabelFrame(parent, text="Grid Subdivisions", padx=10, pady=10)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(grid_frame, text="Divisions for selected connection:", 
                font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Scale(grid_frame, from_=1, to=100, variable=self.subdiv_var, 
                orient=tk.HORIZONTAL, label="Subdivisions",
                font=("Arial", 9)).pack(fill=tk.X, pady=5)
        
        tk.Button(grid_frame, text="Apply to Selected", 
                 command=self.apply_subdivisions, bg="lightblue",
                 font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
    
    def _setup_global_controls(self, parent):
        global_frame = tk.LabelFrame(parent, text="Global Settings", padx=10, pady=10)
        global_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(global_frame, text="Apply to all connections:", 
                font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Scale(global_frame, from_=1, to=100, variable=self.global_subdiv_var, 
                orient=tk.HORIZONTAL, label="Default Subdivisions",
                font=("Arial", 9)).pack(fill=tk.X)
        
        tk.Button(global_frame, text="Apply to All Connections", 
                 command=self.apply_global_subdivisions, bg="lightyellow",
                 font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
    
    def update_view(self):
        self.ax_grid_3d.clear()
        self.ax_grid_3d.set_xlabel('X')
        self.ax_grid_3d.set_ylabel('Y')
        self.ax_grid_3d.set_zlabel('Z')
        self.ax_grid_3d.set_title("3D Connection View - Click to Select")
        
        self.connections_data = []
        
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            z = self.mesh_data.layers[layer]
            for x, y in self.mesh_data.points[layer]:
                all_points.append((x, y, z))
        
        if not all_points:
            self.ax_grid_3d.text(0, 0, 0, "No points to display\nAdd geometry in Tab 2", 
                               ha='center', va='center', fontsize=12)
            self.canvas_grid_3d.draw()
            return
        
        xs, ys, zs = zip(*all_points)
        self.ax_grid_3d.scatter(xs, ys, zs, c='red', marker='o', s=50, alpha=0.6)
        
        # Draw connections within layers (horizontal)
        for layer in self.mesh_data.layers:
            z = self.mesh_data.layers[layer]
            points = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points) and conn[1] < len(points):
                    p1 = points[conn[0]]
                    p2 = points[conn[1]]
                    
                    start_3d = (p1[0], p1[1], z)
                    end_3d = (p2[0], p2[1], z)
                    
                    conn_idx = len(self.connections_data)
                    is_selected = (conn_idx == self.selected_connection_idx)
                    
                    color = 'red' if is_selected else 'blue'
                    linewidth = 4 if is_selected else 2
                    
                    self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z, z], 
                                       color=color, linewidth=linewidth, alpha=0.8)
                    
                    self.connections_data.append({
                        'start': start_3d,
                        'end': end_3d,
                        'type': 'horizontal',
                        'layer': layer,
                        'points': conn,
                        'label': f"{layer} [{conn[0]}-{conn[1]}]"
                    })
        
        # Draw inter-layer connections (vertical - explicit)
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                p1 = self.mesh_data.points[layer1][idx1]
                p2 = self.mesh_data.points[layer2][idx2]
                
                start_3d = (p1[0], p1[1], z1)
                end_3d = (p2[0], p2[1], z2)
                
                conn_idx = len(self.connections_data)
                is_selected = (conn_idx == self.selected_connection_idx)
                
                color = 'red' if is_selected else 'green'
                linewidth = 4 if is_selected else 2
                linestyle = '-' if is_selected else '--'
                
                self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 
                                   color=color, linewidth=linewidth, alpha=0.8,
                                   linestyle=linestyle)
                
                self.connections_data.append({
                    'start': start_3d,
                    'end': end_3d,
                    'type': 'inter-layer',
                    'layers': (layer1, layer2),
                    'points': (idx1, idx2),
                    'label': f"{layer1}[{idx1}] ↔ {layer2}[{idx2}]"
                })
        
        # Draw auto-connections between adjacent layers (implicit)
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            if len(points1) == len(points2):
                for j in range(len(points1)):
                    # Check if this connection already exists as explicit inter-layer
                    already_explicit = any(
                        (l1 == layer1 and i1 == j and l2 == layer2 and i2 == j) or
                        (l1 == layer2 and i1 == j and l2 == layer1 and i2 == j)
                        for l1, i1, l2, i2 in self.mesh_data.inter_layer_connections
                    )
                    
                    if not already_explicit:
                        p1 = points1[j]
                        p2 = points2[j]
                        
                        start_3d = (p1[0], p1[1], z1)
                        end_3d = (p2[0], p2[1], z2)
                        
                        conn_idx = len(self.connections_data)
                        is_selected = (conn_idx == self.selected_connection_idx)
                        
                        if is_selected:
                            self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 
                                               color='red', linewidth=4, alpha=0.8)
                        else:
                            self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 
                                               color='gray', linewidth=1, alpha=0.3, linestyle=':')
                        
                        self.connections_data.append({
                            'start': start_3d,
                            'end': end_3d,
                            'type': 'auto-vertical',
                            'layers': (layer1, layer2),
                            'point_idx': j,
                            'label': f"{layer1}[{j}] → {layer2}[{j}] (auto)"
                        })
        
        self.canvas_grid_3d.draw()
    
    def on_grid_3d_click(self, event):
        if event.inaxes != self.ax_grid_3d:
            return
        
        if event.button != 1:  # Only left click
            return
        
        # Get click position in 2D screen coordinates
        if event.xdata is None or event.ydata is None:
            return
        
        # Find closest connection to click
        closest_conn_idx = None
        min_distance = float('inf')
        threshold = 0.05  # Threshold in normalized screen coordinates
        
        for idx, conn_data in enumerate(self.connections_data):
            start_3d = conn_data['start']
            end_3d = conn_data['end']
            
            # Project 3D points to 2D screen coordinates
            try:
                start_2d = self.ax_grid_3d.transData.transform(start_3d)
                end_2d = self.ax_grid_3d.transData.transform(end_3d)
                
                # Normalize to axes coordinates (0-1)
                inv_trans = self.ax_grid_3d.transAxes.inverted()
                start_norm = inv_trans.transform(start_2d)
                end_norm = inv_trans.transform(end_2d)
                
                # Get click position in axes coordinates
                click_display = self.ax_grid_3d.transData.transform((event.xdata, event.ydata, 0))
                click_norm = inv_trans.transform(click_display)
                
                # Calculate distance from click to line segment
                distance = self._point_to_line_distance_2d(
                    click_norm[:2], start_norm[:2], end_norm[:2]
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_conn_idx = idx
            except:
                continue
        
        # Select connection if close enough
        if closest_conn_idx is not None and min_distance < threshold:
            self.selected_connection_idx = closest_conn_idx
            conn_data = self.connections_data[closest_conn_idx]
            
            # Update labels
            self.selected_conn_label.config(
                text=f"Connection #{closest_conn_idx}: {conn_data['label']}"
            )
            
            type_text = f"Type: {conn_data['type']}"
            self.conn_type_label.config(text=type_text)
            
            # Redraw to highlight selected connection
            self.update_view()
    
    def _point_to_line_distance_2d(self, point, line_start, line_end):
        """Calculate minimum distance from point to line segment in 2D"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vector from start to end
        dx = x2 - x1
        dy = y2 - y1
        
        # If line segment is a point
        if dx == 0 and dy == 0:
            return np.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Parameter t of closest point on line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx**2 + dy**2)))
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance to closest point
        return np.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def clear_selection(self):
        self.selected_connection_idx = None
        self.selected_conn_label.config(text="None selected")
        self.conn_type_label.config(text="")
        self.update_view()
    
    def apply_subdivisions(self):
        if self.selected_connection_idx is None:
            messagebox.showwarning("Warning", "Select a connection first by clicking on it")
            return
        
        subdivs = self.subdiv_var.get()
        conn_data = self.connections_data[self.selected_connection_idx]
        
        messagebox.showinfo("Applied", 
                          f"Set {subdivs} subdivisions for:\n{conn_data['label']}\n\n"
                          f"Type: {conn_data['type']}")
    
    def apply_global_subdivisions(self):
        subdivs = self.global_subdiv_var.get()
        num_connections = len(self.connections_data)
        messagebox.showinfo("Applied", 
                          f"Set {subdivs} subdivisions for all {num_connections} connections")