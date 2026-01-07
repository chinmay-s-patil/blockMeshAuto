"""
Hex Block Making Tab - Create hexahedral blocks with proper sizing and grading
Uses tkinter Canvas for simple 3D visualization
"""
import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np
import math


class TabHexBlockMaking:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Block management
        self.hex_blocks = []  # List of HexBlock objects
        self.selected_layers = []
        self.selected_points = []  # List of (layer, point_idx) tuples
        self.current_block_idx = None
        
        # Sizing mode
        self.sizing_mode = tk.StringVar(value="universal")
        self.cell_size_var = tk.DoubleVar(value=1.0)  # mm
        self.nx_var = tk.IntVar(value=10)
        self.ny_var = tk.IntVar(value=10)
        self.nz_var = tk.IntVar(value=10)
        
        # Grading
        self.grading_type = tk.StringVar(value="simpleGrading")
        
        # View angles for canvas
        self.view_angle = 45
        self.view_tilt = 30
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create sub-tabs
        self.tab_selection = tk.Frame(self.notebook)
        self.tab_sizing = tk.Frame(self.notebook)
        self.tab_blocks = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_selection, text="1. Point Selection")
        self.notebook.add(self.tab_sizing, text="2. Sizing & Grading")
        self.notebook.add(self.tab_blocks, text="3. Manage Blocks")
        
        # Setup each tab
        self._setup_selection_tab()
        self._setup_sizing_tab()
        self._setup_blocks_tab()
    
    def _setup_selection_tab(self):
        main_frame = tk.Frame(self.tab_selection)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas for 3D-ish view
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Hex Block Builder", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # Simple canvas for drawing
        self.canvas = tk.Canvas(left_frame, bg="white", width=600, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Rotation controls
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="Rotation:").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="↻ Rotate", 
                 command=lambda: self.rotate_view(30)).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="🔄 Reset View", 
                 command=self.reset_view).pack(side=tk.LEFT, padx=2)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Layer selection
        layer_frame = tk.LabelFrame(right_frame, text="1. Select 2 Layers", 
                                    padx=10, pady=10, font=("Arial", 10, "bold"))
        layer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(layer_frame, text="🔄 Refresh Layers", command=self.refresh_layers,
                 bg="lightgreen", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=(0, 5))
        
        self.layer_listbox = tk.Listbox(layer_frame, height=6, selectmode=tk.EXTENDED)
        self.layer_listbox.pack(fill=tk.X, pady=5)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        
        self.layer_status = tk.Label(layer_frame, text="Select 2 layers", 
                                     fg="gray", font=("Arial", 9, "italic"))
        self.layer_status.pack(pady=5)
        
        # Point selection
        point_frame = tk.LabelFrame(right_frame, text="2. Select 8 Points", 
                                    padx=10, pady=10, font=("Arial", 10, "bold"))
        point_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(point_frame, text="Click points in the view\n4 from each layer\nOrder: counter-clockwise",
                font=("Arial", 8), justify=tk.LEFT, fg="gray").pack(pady=(0, 5))
        
        self.point_status = tk.Label(point_frame, text="Selected: 0/8 points", 
                                     fg="blue", font=("Arial", 9, "bold"))
        self.point_status.pack(pady=5)
        
        # List of selected points
        point_scroll = tk.Scrollbar(point_frame)
        point_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_list = tk.Listbox(point_frame, height=10, font=("Courier", 8),
                                     yscrollcommand=point_scroll.set)
        self.point_list.pack(fill=tk.BOTH, expand=True, pady=5)
        point_scroll.config(command=self.point_list.yview)
        
        btn_frame = tk.Frame(point_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Clear", command=self.clear_point_selection, 
                 width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Next: Sizing →", command=lambda: self.notebook.select(1),
                 bg="lightblue", font=("Arial", 9, "bold"), width=12).pack(side=tk.LEFT, padx=2)
        
        self.refresh_layers()
    
    def _setup_sizing_tab(self):
        main_frame = tk.Frame(self.tab_sizing)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Sizing & Grading Configuration", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Two columns
        columns = tk.Frame(main_frame)
        columns.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left: Sizing
        left_col = tk.Frame(columns)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        sizing_frame = tk.LabelFrame(left_col, text="Cell Divisions", 
                                     padx=15, pady=15, font=("Arial", 11, "bold"))
        sizing_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mode selection
        tk.Label(sizing_frame, text="Sizing Mode:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Radiobutton(sizing_frame, text="Universal (auto-calculate)", 
                      variable=self.sizing_mode, value="universal",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Radiobutton(sizing_frame, text="2D Mesh (1 division in one direction)", 
                      variable=self.sizing_mode, value="2d",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Radiobutton(sizing_frame, text="Custom (manual divisions)", 
                      variable=self.sizing_mode, value="custom",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Universal mode
        self.universal_frame = tk.Frame(sizing_frame)
        self.universal_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.universal_frame, text="Target cell size:", 
                font=("Arial", 9)).pack(anchor=tk.W)
        tk.Scale(self.universal_frame, from_=0.1, to=10.0, resolution=0.1,
                variable=self.cell_size_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # 2D mode
        self.mode_2d_frame = tk.Frame(sizing_frame)
        
        tk.Label(self.mode_2d_frame, text="Target cell size:", 
                font=("Arial", 9)).pack(anchor=tk.W)
        tk.Scale(self.mode_2d_frame, from_=0.1, to=10.0, resolution=0.1,
                variable=self.cell_size_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        tk.Label(self.mode_2d_frame, text="Single division direction:", 
                font=("Arial", 9)).pack(anchor=tk.W, pady=(5, 0))
        self.single_div_dir = tk.StringVar(value="Z")
        dir_frame = tk.Frame(self.mode_2d_frame)
        dir_frame.pack(anchor=tk.W, pady=5)
        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(dir_frame, text=direction, 
                          variable=self.single_div_dir, value=direction).pack(side=tk.LEFT, padx=5)
        
        # Custom mode
        self.custom_frame = tk.Frame(sizing_frame)
        
        for label, var in [("X divisions:", self.nx_var), 
                          ("Y divisions:", self.ny_var), 
                          ("Z divisions:", self.nz_var)]:
            row = tk.Frame(self.custom_frame)
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label, width=12, anchor=tk.W).pack(side=tk.LEFT)
            tk.Scale(row, from_=1, to=100, variable=var, 
                    orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Right: Grading
        right_col = tk.Frame(columns)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        grading_frame = tk.LabelFrame(right_col, text="Grading", 
                                      padx=15, pady=15, font=("Arial", 11, "bold"))
        grading_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(grading_frame, text="Grading type:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        grading_types = [
            ("simpleGrading", "simpleGrading"),
            ("edgeGrading", "edgeGrading"),
            ("multiGrading", "multiGrading")
        ]
        
        for label, value in grading_types:
            tk.Radiobutton(grading_frame, text=label, variable=self.grading_type, 
                          value=value, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Label(grading_frame, text="Expansion ratios:", 
                font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.grading_x = tk.DoubleVar(value=1.0)
        self.grading_y = tk.DoubleVar(value=1.0)
        self.grading_z = tk.DoubleVar(value=1.0)
        
        for label, var in [("X:", self.grading_x), ("Y:", self.grading_y), ("Z:", self.grading_z)]:
            row = tk.Frame(grading_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=3).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Create button
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="← Back", command=lambda: self.notebook.select(0),
                 width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Create Hex Block", command=self.create_hex_block,
                 bg="lightgreen", font=("Arial", 11, "bold"), width=18).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View Blocks →", command=lambda: self.notebook.select(2),
                 width=12).pack(side=tk.LEFT, padx=5)
        
        self.update_sizing_ui()
    
    def _setup_blocks_tab(self):
        main_frame = tk.Frame(self.tab_blocks)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Created Hex Blocks", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Block list with scrollbar
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.block_listbox = tk.Listbox(list_frame, font=("Courier", 10),
                                        yscrollcommand=scrollbar.set, height=20)
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scrollbar.config(command=self.block_listbox.yview)
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="← Back to Sizing", command=lambda: self.notebook.select(1),
                 width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Block", command=self.edit_block,
                 bg="lightblue", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Block", command=self.delete_block,
                 bg="salmon", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=5)
        
    def _setup_layer_selection(self, parent):
        frame = tk.LabelFrame(parent, text="1. Select 2 Layers", 
                             padx=10, pady=10, font=("Arial", 10, "bold"))
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(frame, text="Click layers below (Ctrl+Click for multi-select):",
                font=("Arial", 9)).pack(anchor=tk.W)
        
        self.layer_listbox = tk.Listbox(frame, height=6, selectmode=tk.EXTENDED)
        self.layer_listbox.pack(fill=tk.X, pady=5)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        
        self.update_layer_list()
        
        self.layer_status = tk.Label(frame, text="Select 2 layers", 
                                     fg="gray", font=("Arial", 9, "italic"))
        self.layer_status.pack(pady=5)
        
        tk.Button(frame, text="🔄 Update 3D View", command=self.update_3d_view,
                 bg="lightgreen", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
    
    def _setup_point_selection(self, parent):
        frame = tk.LabelFrame(parent, text="2. Select 8 Points for Hex", 
                             padx=10, pady=10, font=("Arial", 10, "bold"))
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(frame, text="Click points in 3D view above\n4 from first layer, 4 from second layer\nOrder: counter-clockwise on each layer",
                font=("Arial", 8), justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 5))
        
        self.point_status = tk.Label(frame, text="Selected: 0/8 points", 
                                     fg="blue", font=("Arial", 9, "bold"))
        self.point_status.pack(pady=5)
        
        # List of selected points
        self.point_list = tk.Listbox(frame, height=8, font=("Courier", 8))
        self.point_list.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Clear Selection", 
                 command=self.clear_point_selection, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Create Hex Block", 
                 command=self.create_hex_block, bg="lightblue", 
                 font=("Arial", 9, "bold"), width=12).pack(side=tk.LEFT, padx=2)
    
    def _setup_sizing_controls(self, parent):
        frame = tk.LabelFrame(parent, text="3. Sizing Mode", 
                             padx=10, pady=10, font=("Arial", 10, "bold"))
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mode selection
        tk.Radiobutton(frame, text="Universal (auto-calculate divisions)", 
                      variable=self.sizing_mode, value="universal",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Radiobutton(frame, text="2D Mesh (1 division in one direction)", 
                      variable=self.sizing_mode, value="2d",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Radiobutton(frame, text="Custom (manual X, Y, Z divisions)", 
                      variable=self.sizing_mode, value="custom",
                      command=self.update_sizing_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Universal mode controls
        self.universal_frame = tk.Frame(frame)
        self.universal_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.universal_frame, text="Target cell size (units):", 
                font=("Arial", 8)).pack(anchor=tk.W)
        tk.Scale(self.universal_frame, from_=0.1, to=10.0, resolution=0.1,
                variable=self.cell_size_var, orient=tk.HORIZONTAL,
                font=("Arial", 8)).pack(fill=tk.X)
        
        # 2D mode controls
        self.mode_2d_frame = tk.Frame(frame)
        
        tk.Label(self.mode_2d_frame, text="Target cell size (units):", 
                font=("Arial", 8)).pack(anchor=tk.W)
        tk.Scale(self.mode_2d_frame, from_=0.1, to=10.0, resolution=0.1,
                variable=self.cell_size_var, orient=tk.HORIZONTAL,
                font=("Arial", 8)).pack(fill=tk.X)
        
        tk.Label(self.mode_2d_frame, text="Single division direction:", 
                font=("Arial", 8)).pack(anchor=tk.W, pady=(5, 0))
        self.single_div_dir = tk.StringVar(value="Z")
        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(self.mode_2d_frame, text=direction, 
                          variable=self.single_div_dir, value=direction,
                          font=("Arial", 8)).pack(side=tk.LEFT)
        
        # Custom mode controls
        self.custom_frame = tk.Frame(frame)
        
        for i, (label, var) in enumerate([("X divisions:", self.nx_var), 
                                          ("Y divisions:", self.ny_var), 
                                          ("Z divisions:", self.nz_var)]):
            row = tk.Frame(self.custom_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=12, anchor=tk.W, 
                    font=("Arial", 8)).pack(side=tk.LEFT)
            tk.Scale(row, from_=1, to=100, variable=var, orient=tk.HORIZONTAL,
                    font=("Arial", 8)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.update_sizing_ui()
    
    def _setup_grading_controls(self, parent):
        frame = tk.LabelFrame(parent, text="4. Grading", 
                             padx=10, pady=10, font=("Arial", 10, "bold"))
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(frame, text="Grading type:", font=("Arial", 9)).pack(anchor=tk.W)
        
        grading_types = [
            ("simpleGrading (uniform)", "simpleGrading"),
            ("edgeGrading (per-edge control)", "edgeGrading"),
            ("multiGrading (multi-segment)", "multiGrading")
        ]
        
        for label, value in grading_types:
            tk.Radiobutton(frame, text=label, variable=self.grading_type, 
                          value=value, font=("Arial", 8)).pack(anchor=tk.W)
        
        # Simple grading parameters
        self.simple_grading_frame = tk.Frame(frame)
        self.simple_grading_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.simple_grading_frame, text="Expansion ratio (X, Y, Z):",
                font=("Arial", 8)).pack(anchor=tk.W)
        
        self.grading_x = tk.DoubleVar(value=1.0)
        self.grading_y = tk.DoubleVar(value=1.0)
        self.grading_z = tk.DoubleVar(value=1.0)
        
        for i, (label, var) in enumerate([("X:", self.grading_x), 
                                          ("Y:", self.grading_y), 
                                          ("Z:", self.grading_z)]):
            row = tk.Frame(self.simple_grading_frame)
            row.pack(fill=tk.X)
            tk.Label(row, text=label, width=3, font=("Arial", 8)).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=8, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
    
    def _setup_block_list(self, parent):
        frame = tk.LabelFrame(parent, text="Created Hex Blocks", 
                             padx=10, pady=10, font=("Arial", 10, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.block_listbox = tk.Listbox(frame, font=("Courier", 8))
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Edit", command=self.edit_block,
                 width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete", command=self.delete_block,
                 bg="salmon", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg="lightcoral", width=8).pack(side=tk.LEFT, padx=2)
    
    def refresh_layers(self):
        """Refresh the layer list from mesh_data"""
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            num_points = len(self.mesh_data.points[name])
            self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")
        self.draw_view()
    
    def rotate_view(self, angle):
        """Rotate the view"""
        self.view_angle = (self.view_angle + angle) % 360
        self.draw_view()
    
    def reset_view(self):
        """Reset view to default"""
        self.view_angle = 45
        self.view_tilt = 30
        self.draw_view()
    
    def project_3d_to_2d(self, point_3d):
        """Simple isometric projection"""
        x, y, z = point_3d
        
        # Rotate around Z axis
        angle_rad = math.radians(self.view_angle)
        x_rot = x * math.cos(angle_rad) - y * math.sin(angle_rad)
        y_rot = x * math.sin(angle_rad) + y * math.cos(angle_rad)
        
        # Isometric projection
        screen_x = x_rot - z
        screen_y = y_rot * 0.5 + z * 0.5
        
        # Center on canvas
        canvas_x = 300 + screen_x * 50
        canvas_y = 300 - screen_y * 50
        
        return canvas_x, canvas_y
    
    def draw_view(self):
        """Draw the 3D view on canvas"""
        self.canvas.delete("all")
        
        if len(self.selected_layers) != 2:
            self.canvas.create_text(300, 300, text="Select 2 layers first",
                                   font=("Arial", 16), fill="gray")
            return
        
        # Collect all points from selected layers
        all_points_3d = []
        point_refs = []  # (layer, idx)
        colors = ['red', 'blue']
        
        for i, layer in enumerate(self.selected_layers):
            for idx, point_2d in enumerate(self.mesh_data.points[layer]):
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                all_points_3d.append(coords_3d)
                point_refs.append((layer, idx, colors[i]))
        
        if not all_points_3d:
            self.canvas.create_text(300, 300, text="No points in selected layers",
                                   font=("Arial", 16), fill="gray")
            return
        
        # Project and draw points
        self.canvas_points = []  # Store for click detection
        for (point_3d, (layer, idx, color)) in zip(all_points_3d, point_refs):
            x, y = self.project_3d_to_2d(point_3d)
            
            # Check if selected
            is_selected = (layer, idx) in self.selected_points
            size = 8 if not is_selected else 12
            fill_color = 'green' if is_selected else color
            
            # Draw point
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill=fill_color, outline='black', width=2,
                                   tags=f"point_{layer}_{idx}")
            
            # Add label
            self.canvas.create_text(x, y-15, text=f"{idx}",
                                   font=("Arial", 8), fill="black")
            
            # Store for click detection
            self.canvas_points.append((x, y, layer, idx, point_3d))
        
        # Draw connections within layers
        for i, layer in enumerate(self.selected_layers):
            points_2d = self.mesh_data.points[layer]
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    
                    x1, y1 = self.project_3d_to_2d(p1_3d)
                    x2, y2 = self.project_3d_to_2d(p2_3d)
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill=colors[i], width=2)
        
        # Draw existing hex blocks
        for block in self.hex_blocks:
            verts = block['vertices']
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom
                (4, 5), (5, 6), (6, 7), (7, 4),  # Top
                (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical
            ]
            
            for i, j in edges:
                x1, y1 = self.project_3d_to_2d(verts[i])
                x2, y2 = self.project_3d_to_2d(verts[j])
                self.canvas.create_line(x1, y1, x2, y2, fill='green', width=3, dash=(5, 3))
        
        # Add title
        title = f"Layers: {self.selected_layers[0]} (red) & {self.selected_layers[1]} (blue)"
        self.canvas.create_text(300, 20, text=title, font=("Arial", 12, "bold"))
    
    def on_canvas_click(self, event):
        """Handle click on canvas"""
        if len(self.selected_layers) != 2:
            return
        
        # Find closest point
        min_dist = float('inf')
        closest = None
        
        for canvas_x, canvas_y, layer, idx, point_3d in self.canvas_points:
            dist = math.sqrt((canvas_x - event.x)**2 + (canvas_y - event.y)**2)
            if dist < min_dist and dist < 20:
                min_dist = dist
                closest = (layer, idx)
        
        if closest:
            # Toggle selection
            if closest in self.selected_points:
                self.selected_points.remove(closest)
            else:
                if len(self.selected_points) < 8:
                    self.selected_points.append(closest)
                else:
                    messagebox.showwarning("Limit", "Maximum 8 points for hex block")
                    return
            
            self.update_point_list()
            self.draw_view()
    
    def on_layer_select(self, event):
        sel = self.layer_listbox.curselection()
        
        # Extract layer names
        self.selected_layers = []
        for idx in sel:
            text = self.layer_listbox.get(idx)
            name = text.split(" (z=")[0]
            self.selected_layers.append(name)
        
        if len(self.selected_layers) > 2:
            # Keep only last 2
            self.selected_layers = self.selected_layers[-2:]
            self.layer_listbox.selection_clear(0, tk.END)
            for name in self.selected_layers:
                for idx in range(self.layer_listbox.size()):
                    if self.layer_listbox.get(idx).startswith(name):
                        self.layer_listbox.selection_set(idx)
        
        if len(self.selected_layers) == 2:
            self.layer_status.config(
                text=f"✓ Selected: {self.selected_layers[0]} & {self.selected_layers[1]}", 
                fg="green")
        elif len(self.selected_layers) == 1:
            self.layer_status.config(
                text=f"Selected: {self.selected_layers[0]} - Select 1 more", fg="orange")
        else:
            self.layer_status.config(text="Select 2 layers", fg="gray")
        
        self.clear_point_selection()
        self.draw_view()
    
    def update_point_list(self):
        self.point_list.delete(0, tk.END)
        
        for i, (layer, idx) in enumerate(self.selected_points):
            point_2d = self.mesh_data.points[layer][idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            self.point_list.insert(tk.END, 
                f"{i}: {layer}[{idx}] = ({coords_3d[0]:.2f}, {coords_3d[1]:.2f}, {coords_3d[2]:.2f})")
        
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
    
    def clear_point_selection(self):
        self.selected_points = []
        self.update_point_list()
        self.draw_view()
    
    def update_sizing_ui(self):
        # Hide all frames
        self.universal_frame.pack_forget()
        self.mode_2d_frame.pack_forget()
        self.custom_frame.pack_forget()
        
        # Show appropriate frame
        mode = self.sizing_mode.get()
        if mode == "universal":
            self.universal_frame.pack(fill=tk.X, pady=10)
        elif mode == "2d":
            self.mode_2d_frame.pack(fill=tk.X, pady=10)
        elif mode == "custom":
            self.custom_frame.pack(fill=tk.X, pady=10)
    
    def create_hex_block(self):
        if len(self.selected_points) != 8:
            messagebox.showwarning("Warning", 
                f"Need exactly 8 points, you have {len(self.selected_points)}")
            return
        
        # Separate points by layer
        layer1_points = [(layer, idx) for layer, idx in self.selected_points 
                        if layer == self.selected_layers[0]]
        layer2_points = [(layer, idx) for layer, idx in self.selected_points 
                        if layer == self.selected_layers[1]]
        
        if len(layer1_points) != 4 or len(layer2_points) != 4:
            messagebox.showerror("Error", 
                "Need 4 points from each layer!\n"
                f"You have {len(layer1_points)} from {self.selected_layers[0]}\n"
                f"and {len(layer2_points)} from {self.selected_layers[1]}")
            return
        
        # Get 3D coordinates
        vertices = []
        for layer, idx in layer1_points:
            point_2d = self.mesh_data.points[layer][idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            vertices.append(coords_3d)
        
        for layer, idx in layer2_points:
            point_2d = self.mesh_data.points[layer][idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            vertices.append(coords_3d)
        
        # Calculate divisions based on mode
        mode = self.sizing_mode.get()
        
        if mode == "universal":
            cell_size = self.cell_size_var.get()
            nx, ny, nz = self._calculate_divisions_universal(vertices, cell_size)
        elif mode == "2d":
            cell_size = self.cell_size_var.get()
            single_dir = self.single_div_dir.get()
            nx, ny, nz = self._calculate_divisions_2d(vertices, cell_size, single_dir)
        else:  # custom
            nx = self.nx_var.get()
            ny = self.ny_var.get()
            nz = self.nz_var.get()
        
        # Create block object
        block = {
            'vertices': vertices,
            'point_refs': self.selected_points.copy(),
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {
                'x': self.grading_x.get(),
                'y': self.grading_y.get(),
                'z': self.grading_z.get()
            }
        }
        
        self.hex_blocks.append(block)
        self.update_block_list()
        self.clear_point_selection()
        self.update_3d_view()
        
        messagebox.showinfo("Success", 
            f"Hex block created!\nDivisions: {nx} × {ny} × {nz}")
    
    def _calculate_divisions_universal(self, vertices, cell_size):
        """Calculate divisions based on edge lengths and target cell size"""
        # Calculate average edge lengths in each direction
        # X direction (edges 0-1, 3-2, 4-5, 7-6)
        x_edges = [
            np.linalg.norm(np.array(vertices[1]) - np.array(vertices[0])),
            np.linalg.norm(np.array(vertices[2]) - np.array(vertices[3])),
            np.linalg.norm(np.array(vertices[5]) - np.array(vertices[4])),
            np.linalg.norm(np.array(vertices[6]) - np.array(vertices[7]))
        ]
        avg_x = np.mean(x_edges)
        
        # Y direction (edges 1-2, 0-3, 5-6, 4-7)
        y_edges = [
            np.linalg.norm(np.array(vertices[2]) - np.array(vertices[1])),
            np.linalg.norm(np.array(vertices[3]) - np.array(vertices[0])),
            np.linalg.norm(np.array(vertices[6]) - np.array(vertices[5])),
            np.linalg.norm(np.array(vertices[7]) - np.array(vertices[4]))
        ]
        avg_y = np.mean(y_edges)
        
        # Z direction (edges 0-4, 1-5, 2-6, 3-7)
        z_edges = [
            np.linalg.norm(np.array(vertices[4]) - np.array(vertices[0])),
            np.linalg.norm(np.array(vertices[5]) - np.array(vertices[1])),
            np.linalg.norm(np.array(vertices[6]) - np.array(vertices[2])),
            np.linalg.norm(np.array(vertices[7]) - np.array(vertices[3]))
        ]
        avg_z = np.mean(z_edges)
        
        nx = max(1, int(round(avg_x / cell_size)))
        ny = max(1, int(round(avg_y / cell_size)))
        nz = max(1, int(round(avg_z / cell_size)))
        
        return nx, ny, nz
    
    def _calculate_divisions_2d(self, vertices, cell_size, single_dir):
        """Calculate divisions for 2D mesh (one direction has 1 division)"""
        nx, ny, nz = self._calculate_divisions_universal(vertices, cell_size)
        
        if single_dir == "X":
            nx = 1
        elif single_dir == "Y":
            ny = 1
        elif single_dir == "Z":
            nz = 1
        
        return nx, ny, nz
    
    def update_block_list(self):
        self.block_listbox.delete(0, tk.END)
        
        for i, block in enumerate(self.hex_blocks):
            nx, ny, nz = block['divisions']
            grading = block['grading_type']
            self.block_listbox.insert(tk.END, 
                f"Block {i}: {nx}×{ny}×{nz} cells, {grading}")
    
    def on_block_select(self, event):
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
    
    def edit_block(self):
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        
        messagebox.showinfo("Edit", "Edit functionality coming soon")
    
    def delete_block(self):
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected block?"):
            del self.hex_blocks[self.current_block_idx]
            self.current_block_idx = None
            self.update_block_list()
            self.update_3d_view()
    
    def clear_all_blocks(self):
        if not self.hex_blocks:
            return
        
        if messagebox.askyesno("Confirm", "Delete all hex blocks?"):
            self.hex_blocks = []
            self.current_block_idx = None
            self.update_block_list()
            self.update_3d_view()
    
    def get_hex_blocks(self):
        """Return list of hex blocks for export"""
        return self.hex_blocks