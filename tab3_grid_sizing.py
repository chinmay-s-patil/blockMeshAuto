"""
Grid Sizing Tab - Connection Subdivision Controls with Clickable Connections
Uses Plotly for better 3D interaction and reliable connection selection
"""
import tkinter as tk
from tkinter import messagebox
import plotly.graph_objects as go
import numpy as np


class TabGridSizing:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.subdiv_var = tk.IntVar(value=10)
        self.global_subdiv_var = tk.IntVar(value=10)
        
        # Connection tracking
        self.connections_data = []  # List of connection info dicts
        self.connection_subdivisions = {}  # conn_idx -> num_subdivisions
        self.selected_connection_idx = None
        
        # Plotly figure
        self.fig = None
        self.plot_widget = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View (will embed Plotly HTML)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Connection View - Click connections to select", 
                font=("Arial", 12, "bold")).pack()
        
        # Info label
        info_label = tk.Label(left_frame, 
                             text="Click 'Update View' to load the 3D visualization",
                             font=("Arial", 10, "italic"), fg="gray")
        info_label.pack(pady=10)
        
        # Placeholder for Plotly
        self.plot_frame = tk.Frame(left_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.plot_label = tk.Label(self.plot_frame, 
                                   text="3D View will appear here\n\nClick 'Update View' button",
                                   font=("Arial", 12), fg="gray", bg="white")
        self.plot_label.pack(expand=True)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update View", command=self.update_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(right_frame, text="📊 Open Interactive View", command=self.open_interactive_view,
                 bg="lightblue", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        self._setup_selection_info(right_frame)
        self._setup_grid_controls(right_frame)
        self._setup_global_controls(right_frame)
        self._setup_connection_list(right_frame)
        
    def _setup_selection_info(self, parent):
        sel_frame = tk.LabelFrame(parent, text="Selected Connection", padx=10, pady=10)
        sel_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(sel_frame, text="Select from list below", 
                font=("Arial", 9, "italic"), fg="gray").pack(pady=(0, 5))
        
        self.selected_conn_label = tk.Label(sel_frame, text="None selected", 
                                           fg="blue", font=("Arial", 10, "bold"),
                                           wraplength=300, justify=tk.LEFT)
        self.selected_conn_label.pack(pady=5)
        
        self.conn_type_label = tk.Label(sel_frame, text="", fg="darkgreen",
                                        font=("Arial", 9))
        self.conn_type_label.pack(pady=2)
        
        self.current_subdiv_label = tk.Label(sel_frame, text="", fg="purple",
                                            font=("Arial", 9))
        self.current_subdiv_label.pack(pady=2)
        
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
    
    def _setup_connection_list(self, parent):
        list_frame = tk.LabelFrame(parent, text="All Connections (Click to Select)", 
                                  padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.conn_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                       font=("Courier", 8))
        self.conn_listbox.pack(fill=tk.BOTH, expand=True)
        self.conn_listbox.bind('<<ListboxSelect>>', self.on_connection_select)
        
        scrollbar.config(command=self.conn_listbox.yview)
    
    def update_view(self):
        """Generate 3D visualization with Plotly"""
        self.connections_data = []
        
        # Check if we have any geometry
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            for x, y in self.mesh_data.points[layer]:
                z = self.mesh_data.layers[layer]
                all_points.append((x, y, z))
        
        if not all_points:
            messagebox.showinfo("No Geometry", 
                              "No points to display. Add geometry in Tab 2 first.")
            return
        
        # Create Plotly figure
        self.fig = go.Figure()
        
        # Plot all points
        xs, ys, zs = zip(*all_points)
        self.fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(size=4, color='red', opacity=0.6),
            name='Points',
            hoverinfo='skip'
        ))
        
        conn_idx = 0
        
        # Horizontal connections (within layers)
        for layer in self.mesh_data.layers:
            z = self.mesh_data.layers[layer]
            points = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points) and conn[1] < len(points):
                    p1 = points[conn[0]]
                    p2 = points[conn[1]]
                    
                    is_selected = (conn_idx == self.selected_connection_idx)
                    color = 'red' if is_selected else 'blue'
                    width = 8 if is_selected else 4
                    
                    self.fig.add_trace(go.Scatter3d(
                        x=[p1[0], p2[0]],
                        y=[p1[1], p2[1]],
                        z=[z, z],
                        mode='lines',
                        line=dict(color=color, width=width),
                        name=f'H-Conn {conn_idx}',
                        showlegend=False,
                        hoverinfo='text',
                        text=f'Connection #{conn_idx}<br>{layer} [{conn[0]}-{conn[1]}]<br>Type: horizontal<br>Click to select',
                        customdata=[conn_idx]
                    ))
                    
                    self.connections_data.append({
                        'idx': conn_idx,
                        'type': 'horizontal',
                        'layer': layer,
                        'points': conn,
                        'label': f"{layer} [{conn[0]}-{conn[1]}]"
                    })
                    
                    conn_idx += 1
        
        # Inter-layer connections (explicit vertical)
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                p1 = self.mesh_data.points[layer1][idx1]
                p2 = self.mesh_data.points[layer2][idx2]
                
                is_selected = (conn_idx == self.selected_connection_idx)
                color = 'red' if is_selected else 'green'
                width = 8 if is_selected else 4
                
                self.fig.add_trace(go.Scatter3d(
                    x=[p1[0], p2[0]],
                    y=[p1[1], p2[1]],
                    z=[z1, z2],
                    mode='lines',
                    line=dict(color=color, width=width, dash='dash'),
                    name=f'V-Conn {conn_idx}',
                    showlegend=False,
                    hoverinfo='text',
                    text=f'Connection #{conn_idx}<br>{layer1}[{idx1}] ↔ {layer2}[{idx2}]<br>Type: inter-layer<br>Click to select',
                    customdata=[conn_idx]
                ))
                
                self.connections_data.append({
                    'idx': conn_idx,
                    'type': 'inter-layer',
                    'layers': (layer1, layer2),
                    'points': (idx1, idx2),
                    'label': f"{layer1}[{idx1}] ↔ {layer2}[{idx2}]"
                })
                
                conn_idx += 1
        
        # Auto-connections between adjacent layers
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
                    # Check if explicit connection exists
                    already_explicit = any(
                        (l1 == layer1 and i1 == j and l2 == layer2 and i2 == j) or
                        (l1 == layer2 and i1 == j and l2 == layer1 and i2 == j)
                        for l1, i1, l2, i2 in self.mesh_data.inter_layer_connections
                    )
                    
                    if not already_explicit:
                        p1 = points1[j]
                        p2 = points2[j]
                        
                        is_selected = (conn_idx == self.selected_connection_idx)
                        color = 'red' if is_selected else 'gray'
                        width = 8 if is_selected else 2
                        opacity = 1.0 if is_selected else 0.3
                        
                        self.fig.add_trace(go.Scatter3d(
                            x=[p1[0], p2[0]],
                            y=[p1[1], p2[1]],
                            z=[z1, z2],
                            mode='lines',
                            line=dict(color=color, width=width, dash='dot'),
                            name=f'A-Conn {conn_idx}',
                            showlegend=False,
                            opacity=opacity,
                            hoverinfo='text',
                            text=f'Connection #{conn_idx}<br>{layer1}[{j}] → {layer2}[{j}] (auto)<br>Type: auto-vertical<br>Click to select',
                            customdata=[conn_idx]
                        ))
                        
                        self.connections_data.append({
                            'idx': conn_idx,
                            'type': 'auto-vertical',
                            'layers': (layer1, layer2),
                            'point_idx': j,
                            'label': f"{layer1}[{j}] → {layer2}[{j}] (auto)"
                        })
                        
                        conn_idx += 1
        
        # Update layout
        self.fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode='closest',
            title="3D Connection View - Click connections to select"
        )
        
        # Update connection listbox
        self.update_connection_list()
        
        # Show message about interactive view
        self.plot_label.config(
            text=f"✓ {len(self.connections_data)} connections loaded\n\n"
                 "Click 'Open Interactive View' button\n"
                 "to see the 3D visualization\n\n"
                 "Or select connections from the list below"
        )
        
        messagebox.showinfo("View Updated", 
                          f"Loaded {len(self.connections_data)} connections.\n\n"
                          "Click 'Open Interactive View' to see 3D visualization,\n"
                          "or select connections from the list.")
    
    def update_connection_list(self):
        """Update the connection listbox"""
        self.conn_listbox.delete(0, tk.END)
        
        for conn in self.connections_data:
            idx = conn['idx']
            subdiv = self.connection_subdivisions.get(idx, 10)
            
            type_short = {
                'horizontal': 'H',
                'inter-layer': 'V',
                'auto-vertical': 'A'
            }.get(conn['type'], '?')
            
            # Format: [idx] Type Label (subdivs)
            line = f"[{idx:3d}] {type_short} {conn['label']:30s} ({subdiv:3d} divs)"
            self.conn_listbox.insert(tk.END, line)
    
    def on_connection_select(self, event):
        """Handle connection selection from listbox"""
        sel = self.conn_listbox.curselection()
        if not sel:
            return
        
        idx = sel[0]
        if idx < len(self.connections_data):
            self.selected_connection_idx = idx
            conn_data = self.connections_data[idx]
            
            # Update labels
            self.selected_conn_label.config(
                text=f"Connection #{idx}: {conn_data['label']}"
            )
            
            type_text = f"Type: {conn_data['type']}"
            self.conn_type_label.config(text=type_text)
            
            # Show current subdivision
            current_subdiv = self.connection_subdivisions.get(idx, 10)
            self.current_subdiv_label.config(
                text=f"Current subdivisions: {current_subdiv}"
            )
            
            # Update the scale
            self.subdiv_var.set(current_subdiv)
    
    def open_interactive_view(self):
        """Open the Plotly figure in a browser"""
        if self.fig is None:
            messagebox.showwarning("No View", 
                                 "Click 'Update View' first to generate the 3D visualization")
            return
        
        # Show in browser
        self.fig.show()
    
    def clear_selection(self):
        self.selected_connection_idx = None
        self.selected_conn_label.config(text="None selected")
        self.conn_type_label.config(text="")
        self.current_subdiv_label.config(text="")
        self.conn_listbox.selection_clear(0, tk.END)
    
    def apply_subdivisions(self):
        if self.selected_connection_idx is None:
            messagebox.showwarning("Warning", "Select a connection first")
            return
        
        subdivs = self.subdiv_var.get()
        conn_data = self.connections_data[self.selected_connection_idx]
        
        # Store the subdivision
        self.connection_subdivisions[self.selected_connection_idx] = subdivs
        
        # Update current subdiv label
        self.current_subdiv_label.config(
            text=f"Current subdivisions: {subdivs}"
        )
        
        # Update listbox
        self.update_connection_list()
        
        messagebox.showinfo("Applied", 
                          f"Set {subdivs} subdivisions for:\n{conn_data['label']}\n\n"
                          f"Type: {conn_data['type']}")
    
    def apply_global_subdivisions(self):
        subdivs = self.global_subdiv_var.get()
        
        # Apply to all connections
        for conn in self.connections_data:
            self.connection_subdivisions[conn['idx']] = subdivs
        
        # Update listbox
        self.update_connection_list()
        
        num_connections = len(self.connections_data)
        messagebox.showinfo("Applied", 
                          f"Set {subdivs} subdivisions for all {num_connections} connections")