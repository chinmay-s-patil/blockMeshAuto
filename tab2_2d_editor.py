"""
2D Editor Tab - Points & Connections
ISO Mode now uses Plotly 3D for proper point selection
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import plotly.graph_objects as go
import webbrowser
import os
import tempfile


class Tab2DEditor:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.selected_points = []
        self.selected_connection = None
        self.mode = "select"
        self.iso_mode = False
        self.iso_layers = []
        self.iso_mode_var = tk.BooleanVar(value=False)
        self.iso_layer_vars = {}
        
        # For Plotly ISO mode
        self.iso_fig = None
        self.iso_html_file = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas (will switch between 2D matplotlib and 3D plotly message)
        self.left_frame = tk.Frame(main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.view_label = tk.Label(self.left_frame, text="X-Y Plane View (2D)", 
                                   font=("Arial", 12, "bold"))
        self.view_label.pack()
        
        # Container for view (will swap between matplotlib and plotly placeholder)
        self.view_container = tk.Frame(self.left_frame, bg="white")
        self.view_container.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib view
        self.setup_2d_view()
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        self._setup_mode_controls(right_frame)
        self._setup_layer_controls(right_frame)
        self._setup_manual_entry(right_frame)
        self._setup_connection_controls(right_frame)
        
        self.update_plot()
        
    def setup_2d_view(self):
        """Setup matplotlib 2D view"""
        # Clear container
        for widget in self.view_container.winfo_children():
            widget.destroy()
        
        self.fig_2d = Figure(figsize=(7, 7))
        self.ax_2d = self.fig_2d.add_subplot(111)
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, self.view_container)
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_2d.mpl_connect('button_press_event', self.on_2d_click)
        
    def setup_iso_view(self):
        """Setup Plotly 3D ISO view placeholder"""
        # Clear container
        for widget in self.view_container.winfo_children():
            widget.destroy()
        
        # Create placeholder with open button
        placeholder_frame = tk.Frame(self.view_container, bg="white")
        placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(placeholder_frame, 
                text="ISO Mode - 3D View Active\n\n"
                     f"Layers: {self.iso_layers[0]} & {self.iso_layers[1]}\n\n"
                     "Click button below to open interactive 3D view",
                font=("Arial", 11), bg="white", fg="darkblue").pack(pady=30)
        
        tk.Button(placeholder_frame, text="🔍 Open 3D ISO View in Browser",
                 command=self.open_iso_view_browser,
                 bg="lightgreen", font=("Arial", 12, "bold"),
                 padx=20, pady=15).pack(pady=10)
        
        tk.Label(placeholder_frame,
                text="In 3D view:\n"
                     "• Click points to select them\n"
                     "• Switch to 'Connect' mode and click 2 points to link layers\n"
                     "• Green circles = selected points\n"
                     "• Rotate: left-drag | Pan: right-drag | Zoom: scroll",
                font=("Arial", 9), bg="white", fg="gray", justify=tk.LEFT).pack(pady=20)
        
        tk.Button(placeholder_frame, text="🔄 Refresh ISO View",
                 command=self.update_iso_3d,
                 bg="lightblue", font=("Arial", 10, "bold"),
                 padx=15, pady=10).pack(pady=5)
        
    def _setup_mode_controls(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.select_btn = tk.Button(mode_frame, text="Select", 
                                     command=lambda: self.set_mode("select"), 
                                     relief=tk.SUNKEN, bg="lightblue")
        self.select_btn.pack(fill=tk.X, pady=2)
        
        self.add_btn = tk.Button(mode_frame, text="Add Points", 
                                 command=lambda: self.set_mode("add"))
        self.add_btn.pack(fill=tk.X, pady=2)
        
        self.connect_btn = tk.Button(mode_frame, text="Connect", 
                                     command=lambda: self.set_mode("connect"))
        self.connect_btn.pack(fill=tk.X, pady=2)
        
        self.delete_btn = tk.Button(mode_frame, text="Delete Points", 
                                    command=lambda: self.set_mode("delete"))
        self.delete_btn.pack(fill=tk.X, pady=2)
        
        self.mode_label = tk.Label(mode_frame, text="Current Mode: Select", 
                                   font=("Arial", 10, "bold"), fg="blue")
        self.mode_label.pack(pady=5)
        
    def _setup_layer_controls(self, parent):
        layer_frame = tk.LabelFrame(parent, text="Layers (Z-values)", padx=10, pady=10)
        layer_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.layer_listbox = tk.Listbox(layer_frame, height=6, selectmode=tk.SINGLE)
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        self.update_layer_list()
        
        layer_btn_frame = tk.Frame(layer_frame)
        layer_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(layer_btn_frame, text="Add", command=self.add_layer, width=5).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Duplicate", command=self.duplicate_layer, width=7).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Extrude", command=self.extrude_layer, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Remove", command=self.remove_layer, width=6).pack(side=tk.LEFT, padx=1)
        
        self.layer_info = tk.Label(layer_frame, text=f"Current: {self.mesh_data.current_layer}", 
                                   font=("Arial", 9, "bold"), fg="blue")
        self.layer_info.pack(pady=5)
        
        # ISO Mode
        iso_frame = tk.LabelFrame(layer_frame, text="ISO Mode - Link Between Layers", padx=10, pady=10)
        iso_frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(iso_frame, text="Enable Iso Mode (3D View)", 
                      variable=self.iso_mode_var, command=self.toggle_iso_mode,
                      font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        tk.Label(iso_frame, text="Select 2 layers to link:", font=("Arial", 8)).pack(anchor=tk.W, pady=(5,2))
        
        iso_canvas_frame = tk.Frame(iso_frame, height=100)
        iso_canvas_frame.pack(fill=tk.BOTH)
        iso_canvas_frame.pack_propagate(False)
        
        self.iso_checkboxes_frame = tk.Frame(iso_canvas_frame)
        self.iso_checkboxes_frame.pack(fill=tk.BOTH)
        
        self.update_iso_checkboxes()
        
        self.iso_label = tk.Label(iso_frame, text="Select exactly 2 layers", 
                                 font=("Arial", 8, "italic"), fg="gray")
        self.iso_label.pack(pady=2)
        
    def _setup_manual_entry(self, parent):
        manual_frame = tk.LabelFrame(parent, text="Manual Entry", padx=10, pady=10)
        manual_frame.pack(fill=tk.X, padx=5, pady=5)
        
        entry_grid = tk.Frame(manual_frame)
        entry_grid.pack()
        
        tk.Label(entry_grid, text="X:").grid(row=0, column=0)
        self.x_entry = tk.Entry(entry_grid, width=8)
        self.x_entry.grid(row=0, column=1, padx=2)
        self.x_entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
        self.x_entry.bind("<Button-1>", lambda e: e.widget.select_range(0, tk.END))
        
        tk.Label(entry_grid, text="Y:").grid(row=0, column=2)
        self.y_entry = tk.Entry(entry_grid, width=8)
        self.y_entry.grid(row=0, column=3, padx=2)
        self.y_entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
        self.y_entry.bind("<Button-1>", lambda e: e.widget.select_range(0, tk.END))
        
        tk.Button(manual_frame, text="Add Point", command=self.add_point_manual).pack(pady=5)
        
    def _setup_connection_controls(self, parent):
        conn_frame = tk.LabelFrame(parent, text="Connection Tools", padx=10, pady=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selection_label = tk.Label(conn_frame, text="Selected: None", fg="green")
        self.selection_label.pack(pady=5)
        
        tk.Button(conn_frame, text="Delete Connection", 
                 command=self.delete_connection, bg="salmon").pack(fill=tk.X, pady=2)
        tk.Button(conn_frame, text="Clear Selection", 
                 command=self.clear_selection).pack(fill=tk.X, pady=2)
    
    def set_mode(self, mode):
        self.mode = mode
        
        self.select_btn.config(relief=tk.RAISED, bg="lightgray")
        self.add_btn.config(relief=tk.RAISED, bg="lightgray")
        self.connect_btn.config(relief=tk.RAISED, bg="lightgray")
        self.delete_btn.config(relief=tk.RAISED, bg="lightgray")
        
        if mode == "select":
            self.select_btn.config(relief=tk.SUNKEN, bg="lightblue")
            self.mode_label.config(text="Current Mode: Select", fg="blue")
        elif mode == "add":
            self.add_btn.config(relief=tk.SUNKEN, bg="lightgreen")
            self.mode_label.config(text="Current Mode: Add", fg="green")
        elif mode == "connect":
            self.connect_btn.config(relief=tk.SUNKEN, bg="lightyellow")
            self.mode_label.config(text="Current Mode: Connect (click 2 points)", fg="orange")
        elif mode == "delete":
            self.delete_btn.config(relief=tk.SUNKEN, bg="salmon")
            self.mode_label.config(text="Current Mode: Delete", fg="red")
    
    def toggle_iso_mode(self):
        self.iso_mode = self.iso_mode_var.get()
        
        if self.iso_mode:
            self.iso_label.config(text="Iso Mode Active - Select 2 layers below", fg="green")
            self.update_iso_layers_from_checkboxes()
            
            if len(self.iso_layers) == 2:
                self.view_label.config(text="ISO Mode - 3D View")
                self.setup_iso_view()
                self.update_iso_3d()
            else:
                messagebox.showwarning("ISO Mode", "Please select exactly 2 layers first!")
                self.iso_mode_var.set(False)
                self.iso_mode = False
        else:
            self.iso_label.config(text="Select exactly 2 layers", fg="gray")
            self.iso_layers = []
            self.view_label.config(text="X-Y Plane View (2D)")
            self.setup_2d_view()
            self.update_plot()
    
    def update_iso_checkboxes(self):
        for widget in self.iso_checkboxes_frame.winfo_children():
            widget.destroy()
        
        self.iso_layer_vars = {}
        
        for name in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            var = tk.BooleanVar(value=False)
            self.iso_layer_vars[name] = var
            cb = tk.Checkbutton(self.iso_checkboxes_frame, text=f"{name} (z={self.mesh_data.layers[name]})", 
                              variable=var, command=self.update_iso_layers_from_checkboxes)
            cb.pack(anchor=tk.W)
    
    def update_iso_layers_from_checkboxes(self):
        self.iso_layers = [name for name, var in self.iso_layer_vars.items() if var.get()]
        
        if len(self.iso_layers) > 2:
            oldest = self.iso_layers[0]
            self.iso_layer_vars[oldest].set(False)
            self.iso_layers = [name for name, var in self.iso_layer_vars.items() if var.get()]
        
        if len(self.iso_layers) == 2:
            self.iso_label.config(text=f"Linking: {self.iso_layers[0]} ↔ {self.iso_layers[1]}", fg="green")
            if self.iso_mode:
                self.update_iso_3d()
        elif len(self.iso_layers) == 1:
            self.iso_label.config(text=f"Selected: {self.iso_layers[0]} - Select 1 more", fg="orange")
        else:
            self.iso_label.config(text="Select exactly 2 layers", fg="gray")
    
    def update_iso_3d(self):
        """Create Plotly 3D view for ISO mode"""
        if len(self.iso_layers) != 2:
            return
        
        self.iso_fig = go.Figure()
        
        colors = ['red', 'blue']
        point_data = []  # Store point info for click handling
        
        # Draw points and connections for both layers
        for i, layer in enumerate(self.iso_layers):
            color = colors[i]
            points = self.mesh_data.points[layer]
            z = self.mesh_data.layers[layer]
            
            if not points:
                continue
            
            # Plot points
            for idx, (x, y) in enumerate(points):
                coords_3d = self.mesh_data.get_3d_coords(layer, (x, y))
                is_selected = (layer, idx) in self.selected_points
                
                point_data.append({
                    'layer': layer,
                    'idx': idx,
                    'coords': coords_3d,
                    'x': coords_3d[0],
                    'y': coords_3d[1],
                    'z': coords_3d[2]
                })
                
                marker_size = 20 if is_selected else 12
                marker_color = 'lime' if is_selected else color
                
                self.iso_fig.add_trace(go.Scatter3d(
                    x=[coords_3d[0]],
                    y=[coords_3d[1]],
                    z=[coords_3d[2]],
                    mode='markers+text',
                    marker=dict(size=marker_size, color=marker_color, 
                               line=dict(color='black', width=2) if is_selected else dict(width=0)),
                    text=[f'{idx}'],
                    textposition='top center',
                    textfont=dict(size=10, color='black'),
                    name=f'{layer}[{idx}]',
                    showlegend=False,
                    hoverinfo='text',
                    hovertext=f'{layer}[{idx}]<br>Click to select<br>Coords: ({coords_3d[0]:.2f}, {coords_3d[1]:.2f}, {coords_3d[2]:.2f})',
                    customdata=[{'layer': layer, 'idx': idx}]
                ))
            
            # Draw connections within layer
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points) and conn[1] < len(points):
                    p1 = self.mesh_data.get_3d_coords(layer, points[conn[0]])
                    p2 = self.mesh_data.get_3d_coords(layer, points[conn[1]])
                    
                    self.iso_fig.add_trace(go.Scatter3d(
                        x=[p1[0], p2[0]],
                        y=[p1[1], p2[1]],
                        z=[p1[2], p2[2]],
                        mode='lines',
                        line=dict(color=color, width=4),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
        
        # Draw inter-layer connections
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            if layer1 in self.iso_layers and layer2 in self.iso_layers:
                if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                    p1 = self.mesh_data.get_3d_coords(layer1, self.mesh_data.points[layer1][idx1])
                    p2 = self.mesh_data.get_3d_coords(layer2, self.mesh_data.points[layer2][idx2])
                    
                    self.iso_fig.add_trace(go.Scatter3d(
                        x=[p1[0], p2[0]],
                        y=[p1[1], p2[1]],
                        z=[p1[2], p2[2]],
                        mode='lines',
                        line=dict(color='green', width=6, dash='dash'),
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f'Inter-layer: {layer1}[{idx1}] ↔ {layer2}[{idx2}]'
                    ))
        
        # Update layout
        self.iso_fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Z',
                zaxis_title='Y',
                aspectmode='data'
            ),
            title=f"ISO Mode: {self.iso_layers[0]} (red) & {self.iso_layers[1]} (blue)",
            hovermode='closest',
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
    def open_iso_view_browser(self):
        """Open ISO 3D view in browser"""
        if self.iso_fig is None:
            self.update_iso_3d()
        
        if self.iso_fig:
            # Add instructions to the figure
            self.iso_fig.add_annotation(
                text=f"<b>ISO Mode Instructions</b><br>"
                     f"Current Mode: {self.mode.upper()}<br><br>"
                     f"<b>Connect Mode:</b> Click 2 points (one from each layer) to link them<br>"
                     f"<b>Select Mode:</b> Click points to select/deselect<br>"
                     f"<b>Delete Mode:</b> Click points to delete<br><br>"
                     f"Green markers = Selected | Red = {self.iso_layers[0]} | Blue = {self.iso_layers[1]}<br>"
                     f"After clicking, refresh view to see changes",
                xref="paper", yref="paper",
                x=0.5, y=0.98,
                showarrow=False,
                font=dict(size=11),
                bgcolor="lightyellow",
                bordercolor="black",
                borderwidth=2,
                xanchor='center',
                yanchor='top'
            )
            
            # Show in browser
            self.iso_fig.show()
            
            messagebox.showinfo("ISO View Opened",
                              f"3D view opened in browser\n\n"
                              f"Current mode: {self.mode}\n"
                              f"Selected points: {len(self.selected_points)}\n\n"
                              f"NOTE: Point clicking in browser is view-only.\n"
                              f"Use the list below to select points, then click 'Refresh ISO View'")
    
    def on_2d_click(self, event):
        """Handle clicks in 2D matplotlib view (non-ISO mode only)"""
        if self.iso_mode:
            return
        
        if event.inaxes != self.ax_2d:
            return
        
        x, y = event.xdata, event.ydata
        layer = self.mesh_data.current_layer
        points = self.mesh_data.points[layer]
        
        # Check if clicking near a connection for deletion
        if self.mode == "select":
            clicked_conn = self._find_connection_near_point(x, y, layer)
            if clicked_conn is not None:
                self.selected_connection = (layer, clicked_conn)
                self.selection_label.config(text=f"Selected connection: {clicked_conn}")
                self.update_plot()
                return
        
        clicked_idx = None
        for idx, (px, py) in enumerate(points):
            dist = np.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.5:
                clicked_idx = idx
                break
        
        if self.mode == "delete":
            if clicked_idx is not None:
                self.mesh_data.remove_point(layer, clicked_idx)
                self.clear_selection()
        elif self.mode == "add":
            if clicked_idx is None:
                self.mesh_data.add_point(layer, x, y)
        elif self.mode == "connect":
            if clicked_idx is not None:
                if clicked_idx not in self.selected_points:
                    self.selected_points.append(clicked_idx)
                    
                    if len(self.selected_points) == 2:
                        self.mesh_data.add_connection(layer, 
                                                     self.selected_points[0], 
                                                     self.selected_points[1])
                        self.selected_points = []
                    
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
        elif self.mode == "select":
            if clicked_idx is not None:
                if clicked_idx not in self.selected_points:
                    self.selected_points.append(clicked_idx)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selected_connection = None
                self.selection_label.config(text=f"Selected points: {self.selected_points}")
        
        self.update_plot()
    
    def _find_connection_near_point(self, x, y, layer):
        """Find if click is near a connection line"""
        points = self.mesh_data.points[layer]
        threshold = 0.3
        
        for conn in self.mesh_data.connections[layer]:
            p1 = np.array(points[conn[0]])
            p2 = np.array(points[conn[1]])
            click = np.array([x, y])
            
            line_vec = p2 - p1
            line_len = np.linalg.norm(line_vec)
            if line_len < 1e-6:
                continue
            
            line_unitvec = line_vec / line_len
            point_vec = click - p1
            proj_length = np.dot(point_vec, line_unitvec)
            
            if proj_length < 0 or proj_length > line_len:
                continue
            
            proj_point = p1 + proj_length * line_unitvec
            dist = np.linalg.norm(click - proj_point)
            
            if dist < threshold:
                return conn
        
        return None
    
    def add_point_manual(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            self.mesh_data.add_point(self.mesh_data.current_layer, x, y)
            self.update_plot()
            if self.iso_mode:
                self.update_iso_3d()
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers")
    
    def delete_connection(self):
        """Delete the selected connection"""
        if self.selected_connection is None:
            messagebox.showwarning("Warning", "No connection selected")
            return
        
        layer, conn = self.selected_connection
        if conn in self.mesh_data.connections[layer]:
            self.mesh_data.connections[layer].remove(conn)
            self.selected_connection = None
            self.update_plot()
    
    def clear_selection(self):
        self.selected_points = []
        self.selected_connection = None
        self.selection_label.config(text="Selected: None")
        self.update_plot()
        if self.iso_mode:
            self.update_iso_3d()
    
    def extrude_layer(self):
        """Extrude current layer"""
        current = self.mesh_data.current_layer
        current_z = self.mesh_data.layers[current]
        
        name = simpledialog.askstring("Extrude Layer", 
                                     f"Name for extruded layer:", 
                                     initialvalue=f"{current}_extruded")
        if not name:
            return
        
        z = simpledialog.askfloat("Z Value", f"Z-value for {name}:", 
                                 initialvalue=current_z + 1.0)
        if z is None:
            return
        
        self.mesh_data.add_layer(name, z)
        self.mesh_data.points[name] = self.mesh_data.points[current].copy()
        self.mesh_data.connections[name] = self.mesh_data.connections[current].copy()
        
        num_points = len(self.mesh_data.points[current])
        for i in range(num_points):
            self.mesh_data.add_inter_layer_connection(current, i, name, i)
        
        self.update_layer_list()
        self.update_iso_checkboxes()
        messagebox.showinfo("Success", f"Layer extruded: {name}\n{num_points} inter-layer connections created")
    
    def update_plot(self):
        """Update 2D matplotlib plot (non-ISO mode)"""
        if self.iso_mode:
            return
        
        self.ax_2d.clear()
        self.ax_2d.grid(True, alpha=0.3)
        self.ax_2d.set_xlabel("X")
        self.ax_2d.set_ylabel("Y")
        
        layer = self.mesh_data.current_layer
        z = self.mesh_data.layers[layer]
        self.ax_2d.set_title(f"Layer: {layer} (z={z})")
        
        points = self.mesh_data.points[layer]
        
        # Draw connections
        for conn in self.mesh_data.connections[layer]:
            p1, p2 = points[conn[0]], points[conn[1]]
            
            if self.selected_connection and self.selected_connection == (layer, conn):
                self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=3, alpha=0.8)
            else:
                self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-', linewidth=1.5)
        
        # Draw points
        if points:
            xs, ys = zip(*points)
            self.ax_2d.plot(xs, ys, 'ro', markersize=8)
            
            for idx in self.selected_points:
                if isinstance(idx, int) and idx < len(points):
                    self.ax_2d.plot(points[idx][0], points[idx][1], 'go', 
                                   markersize=12, alpha=0.5)
        
        # Auto-scale
        all_x, all_y = [], []
        for lyr in self.mesh_data.points:
            for x, y in self.mesh_data.points[lyr]:
                all_x.append(x)
                all_y.append(y)
        
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            range_val = max(max_x - min_x, max_y - min_y, 2)
            center_x = (max_x + min_x) / 2
            center_y = (max_y + min_y) / 2
            margin = range_val * 0.2 + 1
            self.ax_2d.set_xlim(center_x - range_val/2 - margin, center_x + range_val/2 + margin)
            self.ax_2d.set_ylim(center_y - range_val/2 - margin, center_y + range_val/2 + margin)
        else:
            self.ax_2d.set_xlim(-1, 1)
            self.ax_2d.set_ylim(-1, 1)
        
        self.canvas_2d.draw()
    
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            self.layer_listbox.insert(tk.END, f"{name} (z={z})")
    
    def on_layer_select(self, event):
        sel = self.layer_listbox.curselection()
        
        if sel:
            text = self.layer_listbox.get(sel[0])
            name = text.split(" (z=")[0]
            self.mesh_data.current_layer = name
            self.layer_info.config(text=f"Current: {name}")
            self.clear_selection()
            self.update_plot()
    
    def add_layer(self):
        num = len(self.mesh_data.layers)
        name = simpledialog.askstring("Layer Name", f"Name for new layer:", 
                                        initialvalue=f"Layer {num}")
        if not name:
            return
        
        z = simpledialog.askfloat("Z Value", f"Z-value for {name}:", 
                                    initialvalue=float(num))
        if z is not None:
            self.mesh_data.add_layer(name, z)
            self.update_layer_list()
            self.update_iso_checkboxes()
    
    def duplicate_layer(self):
        current = self.mesh_data.current_layer
        
        name = simpledialog.askstring("Duplicate Layer", 
                                     f"Name for duplicated layer:", 
                                     initialvalue=f"{current}_copy")
        if not name:
            return
        
        current_z = self.mesh_data.layers[current]
        z = simpledialog.askfloat("Z Value", f"Z-value for {name}:", 
                                 initialvalue=current_z + 1.0)
        if z is not None:
            self.mesh_data.add_layer(name, z)
            self.mesh_data.points[name] = self.mesh_data.points[current].copy()
            self.mesh_data.connections[name] = self.mesh_data.connections[current].copy()
            self.update_layer_list()
            self.update_iso_checkboxes()
            messagebox.showinfo("Success", f"Layer duplicated: {name}")
    
    def remove_layer(self):
        if len(self.mesh_data.layers) <= 1:
            messagebox.showwarning("Warning", "Cannot remove last layer")
            return
        
        self.mesh_data.remove_layer(self.mesh_data.current_layer)
        self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
        self.update_layer_list()
        self.update_iso_checkboxes()
        self.update_plot()