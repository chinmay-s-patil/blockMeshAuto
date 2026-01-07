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
        self.hex_blocks = []
        self.selected_layers = []
        self.selected_points = []
        self.current_block_idx = None
        
        # Division mode
        self.division_mode = tk.StringVar(value="direct")  # direct or cell_size
        self.nx_var = tk.IntVar(value=10)
        self.ny_var = tk.IntVar(value=10)
        self.nz_var = tk.IntVar(value=10)
        self.cell_size_var = tk.DoubleVar(value=1.0)
        
        # Sizing mode for 2D
        self.sizing_mode = tk.StringVar(value="3d")  # 3d or 2d
        self.single_div_dir = tk.StringVar(value="Z")
        
        # Grading
        self.grading_type = tk.StringVar(value="simpleGrading")
        self.grading_x = tk.DoubleVar(value=1.0)
        self.grading_y = tk.DoubleVar(value=1.0)
        self.grading_z = tk.DoubleVar(value=1.0)
        
        # View angles
        self.view_angle = 45
        self.view_tilt = 30
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View (always visible)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Hex Block Builder", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # Canvas
        self.canvas = tk.Canvas(left_frame, bg="white", width=600, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Controls under canvas
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(control_frame, text="↻ Rotate", 
                 command=lambda: self.rotate_view(30), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="🔄 Reset View", 
                 command=self.reset_view, width=10).pack(side=tk.LEFT, padx=5)
        
        # Right: Tabbed controls
        right_frame = tk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Create notebook for right side tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_layers = tk.Frame(self.notebook)
        self.tab_points = tk.Frame(self.notebook)
        self.tab_sizing = tk.Frame(self.notebook)
        self.tab_blocks = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_layers, text="1. Layers")
        self.notebook.add(self.tab_points, text="2. Points")
        self.notebook.add(self.tab_sizing, text="3. Sizing")
        self.notebook.add(self.tab_blocks, text="4. Blocks")
        
        # Setup each tab
        self._setup_layers_tab()
        self._setup_points_tab()
        self._setup_sizing_tab()
        self._setup_blocks_tab()
        
        self.refresh_layers()
        
    def _setup_layers_tab(self):
        frame = tk.Frame(self.tab_layers)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Select 2 Layers", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Button(frame, text="🔄 Refresh Layers", command=self.refresh_layers,
                 bg="lightgreen", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame, text="Ctrl+Click to select 2 layers:",
                font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        self.layer_listbox = tk.Listbox(frame, height=10, selectmode=tk.EXTENDED)
        self.layer_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        
        self.layer_status = tk.Label(frame, text="Select 2 layers", 
                                     fg="gray", font=("Arial", 9, "italic"))
        self.layer_status.pack(pady=10)
        
    def _setup_points_tab(self):
        frame = tk.Frame(self.tab_points)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Select 8 Points", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(frame, text="Click points in 3D view\n4 from each layer\nOrder: counter-clockwise",
                font=("Arial", 8), justify=tk.LEFT, fg="gray").pack(anchor=tk.W, pady=(0, 10))
        
        self.point_status = tk.Label(frame, text="Selected: 0/8 points", 
                                     fg="blue", font=("Arial", 9, "bold"))
        self.point_status.pack(pady=5)
        
        # Scrollable list
        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_list = tk.Listbox(frame, height=15, font=("Courier", 8),
                                     yscrollcommand=scroll.set)
        self.point_list.pack(fill=tk.BOTH, expand=True, pady=5)
        scroll.config(command=self.point_list.yview)
        
        tk.Button(frame, text="Clear Selection", command=self.clear_point_selection,
                 bg="salmon").pack(fill=tk.X, pady=10)
        
    def _setup_sizing_tab(self):
        frame = tk.Frame(self.tab_sizing)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Cell Sizing", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Division mode
        div_frame = tk.LabelFrame(frame, text="Division Mode", padx=10, pady=10)
        div_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(div_frame, text="Direct (specify number of cells)", 
                      variable=self.division_mode, value="direct",
                      command=self.update_division_ui, font=("Arial", 9)).pack(anchor=tk.W)
        tk.Radiobutton(div_frame, text="Cell Size (auto-calculate from target size)", 
                      variable=self.division_mode, value="cell_size",
                      command=self.update_division_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Direct divisions
        self.direct_frame = tk.Frame(frame)
        
        for label, var in [("X divisions:", self.nx_var), 
                          ("Y divisions:", self.ny_var), 
                          ("Z divisions:", self.nz_var)]:
            row = tk.Frame(self.direct_frame)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                    font=("Arial", 9)).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10,
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Cell size mode
        self.cellsize_frame = tk.Frame(frame)
        
        row = tk.Frame(self.cellsize_frame)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text="Target cell size:", width=15, anchor=tk.W,
                font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.cell_size_var, width=10,
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="units", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # 2D/3D mode
        mode_frame = tk.LabelFrame(frame, text="Mesh Type", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, pady=(10, 10))
        
        tk.Radiobutton(mode_frame, text="3D Mesh", 
                      variable=self.sizing_mode, value="3d",
                      font=("Arial", 9)).pack(anchor=tk.W)
        
        row2d = tk.Frame(mode_frame)
        row2d.pack(fill=tk.X, pady=5)
        tk.Radiobutton(row2d, text="2D Mesh (1 div in:", 
                      variable=self.sizing_mode, value="2d",
                      font=("Arial", 9)).pack(side=tk.LEFT)
        
        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(row2d, text=direction, 
                          variable=self.single_div_dir, value=direction,
                          font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        
        # Grading
        grad_frame = tk.LabelFrame(frame, text="Grading", padx=10, pady=10)
        grad_frame.pack(fill=tk.X, pady=(10, 10))
        
        for label, value in [("simpleGrading", "simpleGrading"),
                            ("edgeGrading", "edgeGrading"),
                            ("multiGrading", "multiGrading")]:
            tk.Radiobutton(grad_frame, text=label, variable=self.grading_type, 
                          value=value, font=("Arial", 9)).pack(anchor=tk.W)
        
        tk.Label(grad_frame, text="Expansion ratios:", 
                font=("Arial", 9)).pack(anchor=tk.W, pady=(10, 5))
        
        for label, var in [("X:", self.grading_x), ("Y:", self.grading_y), ("Z:", self.grading_z)]:
            row = tk.Frame(grad_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=3, font=("Arial", 9)).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Create button
        tk.Button(frame, text="Create Hex Block", command=self.create_hex_block,
                 bg="lightgreen", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=20)
        
        self.update_division_ui()
        
    def _setup_blocks_tab(self):
        frame = tk.Frame(self.tab_blocks)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Created Blocks", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.block_listbox = tk.Listbox(frame, font=("Courier", 9),
                                        yscrollcommand=scroll.set)
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scroll.config(command=self.block_listbox.yview)
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Delete", command=self.delete_block,
                 bg="salmon", width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg="lightcoral", width=10).pack(side=tk.LEFT, padx=2)
    
    def update_division_ui(self):
        """Show/hide division input based on mode"""
        self.direct_frame.pack_forget()
        self.cellsize_frame.pack_forget()
        
        if self.division_mode.get() == "direct":
            self.direct_frame.pack(fill=tk.X, pady=(10, 10))
        else:
            self.cellsize_frame.pack(fill=tk.X, pady=(10, 10))
    
    def refresh_layers(self):
        """Refresh layer list"""
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            num_points = len(self.mesh_data.points[name])
            self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")
        self.draw_view()
    
    def rotate_view(self, angle):
        self.view_angle = (self.view_angle + angle) % 360
        self.draw_view()
    
    def reset_view(self):
        self.view_angle = 45
        self.view_tilt = 30
        self.draw_view()
    
    def project_3d_to_2d(self, point_3d):
        """Isometric projection"""
        x, y, z = point_3d
        angle_rad = math.radians(self.view_angle)
        x_rot = x * math.cos(angle_rad) - y * math.sin(angle_rad)
        y_rot = x * math.sin(angle_rad) + y * math.cos(angle_rad)
        screen_x = x_rot - z
        screen_y = y_rot * 0.5 + z * 0.5
        canvas_x = 300 + screen_x * 50
        canvas_y = 300 - screen_y * 50
        return canvas_x, canvas_y
    
    def draw_view(self):
        """Draw 3D view"""
        self.canvas.delete("all")
        
        if len(self.selected_layers) != 2:
            self.canvas.create_text(300, 300, text="Select 2 layers first",
                                   font=("Arial", 16), fill="gray")
            return
        
        all_points_3d = []
        point_refs = []
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
        
        self.canvas_points = []
        for (point_3d, (layer, idx, color)) in zip(all_points_3d, point_refs):
            x, y = self.project_3d_to_2d(point_3d)
            is_selected = (layer, idx) in self.selected_points
            size = 8 if not is_selected else 12
            fill_color = 'green' if is_selected else color
            
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                   fill=fill_color, outline='black', width=2)
            self.canvas.create_text(x, y-15, text=f"{idx}",
                                   font=("Arial", 8), fill="black")
            self.canvas_points.append((x, y, layer, idx, point_3d))
        
        # Draw connections
        for i, layer in enumerate(self.selected_layers):
            points_2d = self.mesh_data.points[layer]
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    x1, y1 = self.project_3d_to_2d(p1_3d)
                    x2, y2 = self.project_3d_to_2d(p2_3d)
                    self.canvas.create_line(x1, y1, x2, y2, fill=colors[i], width=2)
        
        # Draw hex blocks
        for block in self.hex_blocks:
            verts = block['vertices']
            edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
            for i, j in edges:
                x1, y1 = self.project_3d_to_2d(verts[i])
                x2, y2 = self.project_3d_to_2d(verts[j])
                self.canvas.create_line(x1, y1, x2, y2, fill='green', width=3, dash=(5, 3))
        
        title = f"Layers: {self.selected_layers[0]} (red) & {self.selected_layers[1]} (blue)"
        self.canvas.create_text(300, 20, text=title, font=("Arial", 12, "bold"))
    
    def on_canvas_click(self, event):
        if len(self.selected_layers) != 2:
            return
        
        min_dist = float('inf')
        closest = None
        
        for canvas_x, canvas_y, layer, idx, point_3d in self.canvas_points:
            dist = math.sqrt((canvas_x - event.x)**2 + (canvas_y - event.y)**2)
            if dist < min_dist and dist < 20:
                min_dist = dist
                closest = (layer, idx)
        
        if closest:
            if closest in self.selected_points:
                self.selected_points.remove(closest)
            else:
                if len(self.selected_points) < 8:
                    self.selected_points.append(closest)
                else:
                    messagebox.showwarning("Limit", "Maximum 8 points")
                    return
            self.update_point_list()
            self.draw_view()
    
    def on_layer_select(self, event):
        sel = self.layer_listbox.curselection()
        self.selected_layers = []
        for idx in sel:
            text = self.layer_listbox.get(idx)
            name = text.split(" (z=")[0]
            self.selected_layers.append(name)
        
        if len(self.selected_layers) > 2:
            self.selected_layers = self.selected_layers[-2:]
            self.layer_listbox.selection_clear(0, tk.END)
            for name in self.selected_layers:
                for idx in range(self.layer_listbox.size()):
                    if self.layer_listbox.get(idx).startswith(name):
                        self.layer_listbox.selection_set(idx)
        
        if len(self.selected_layers) == 2:
            self.layer_status.config(
                text=f"✓ {self.selected_layers[0]} & {self.selected_layers[1]}", fg="green")
        elif len(self.selected_layers) == 1:
            self.layer_status.config(text=f"{self.selected_layers[0]} - Select 1 more", fg="orange")
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
                f"{i}: {layer}[{idx}] ({coords_3d[0]:.2f},{coords_3d[1]:.2f},{coords_3d[2]:.2f})")
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
    
    def clear_point_selection(self):
        self.selected_points = []
        self.update_point_list()
        self.draw_view()
    
    def create_hex_block(self):
        if len(self.selected_points) != 8:
            messagebox.showwarning("Warning", f"Need 8 points, have {len(self.selected_points)}")
            return
        
        layer1_points = [(l, i) for l, i in self.selected_points if l == self.selected_layers[0]]
        layer2_points = [(l, i) for l, i in self.selected_points if l == self.selected_layers[1]]
        
        if len(layer1_points) != 4 or len(layer2_points) != 4:
            messagebox.showerror("Error", 
                f"Need 4 from each layer!\nHave {len(layer1_points)} and {len(layer2_points)}")
            return
        
        vertices = []
        for layer, idx in layer1_points + layer2_points:
            point_2d = self.mesh_data.points[layer][idx]
            vertices.append(self.mesh_data.get_3d_coords(layer, point_2d))
        
        # Calculate divisions
        if self.division_mode.get() == "direct":
            nx, ny, nz = self.nx_var.get(), self.ny_var.get(), self.nz_var.get()
        else:
            cell_size = self.cell_size_var.get()
            nx, ny, nz = self._calculate_divisions(vertices, cell_size)
        
        # Apply 2D mode
        if self.sizing_mode.get() == "2d":
            if self.single_div_dir.get() == "X":
                nx = 1
            elif self.single_div_dir.get() == "Y":
                ny = 1
            elif self.single_div_dir.get() == "Z":
                nz = 1
        
        block = {
            'vertices': vertices,
            'point_refs': self.selected_points.copy(),
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {'x': self.grading_x.get(), 
                             'y': self.grading_y.get(), 
                             'z': self.grading_z.get()}
        }
        
        self.hex_blocks.append(block)
        self.update_block_list()
        self.clear_point_selection()
        self.draw_view()
        messagebox.showinfo("Success", f"Block created!\nDivisions: {nx}×{ny}×{nz}")
    
    def _calculate_divisions(self, vertices, cell_size):
        """Calculate divisions from cell size"""
        x_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j])) 
                   for i, j in [(0,1),(2,3),(4,5),(6,7)]]
        y_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j])) 
                   for i, j in [(1,2),(0,3),(5,6),(4,7)]]
        z_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j])) 
                   for i, j in [(0,4),(1,5),(2,6),(3,7)]]
        
        nx = max(1, int(round(np.mean(x_edges) / cell_size)))
        ny = max(1, int(round(np.mean(y_edges) / cell_size)))
        nz = max(1, int(round(np.mean(z_edges) / cell_size)))
        return nx, ny, nz
    
    def update_block_list(self):
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.hex_blocks):
            nx, ny, nz = block['divisions']
            grading = block['grading_type']
            self.block_listbox.insert(tk.END, f"Block {i}: {nx}×{ny}×{nz}, {grading}")
    
    def on_block_select(self, event):
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
    
    def delete_block(self):
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        if messagebox.askyesno("Confirm", "Delete block?"):
            del self.hex_blocks[self.current_block_idx]
            self.current_block_idx = None
            self.update_block_list()
            self.draw_view()
    
    def clear_all_blocks(self):
        if not self.hex_blocks:
            return
        if messagebox.askyesno("Confirm", "Delete all blocks?"):
            self.hex_blocks = []
            self.current_block_idx = None
            self.update_block_list()
            self.draw_view()
    
    def get_hex_blocks(self):
        return self.hex_blocks