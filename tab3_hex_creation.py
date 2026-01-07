"""
Hex Block Making Tab - Create hexahedral blocks with proper sizing and grading
Uses matplotlib 3D for in-window visualization
"""
import tkinter as tk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


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
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Hex Block Builder", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # Matplotlib 3D canvas
        self.fig_3d = Figure(figsize=(8, 8))
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar for pan/zoom/rotate
        toolbar = NavigationToolbar2Tk(self.canvas_3d, left_frame)
        toolbar.update()
        
        self.canvas_3d.mpl_connect('button_press_event', self.on_3d_click)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Create scrollable frame for controls
        canvas = tk.Canvas(right_frame)
        scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._setup_layer_selection(scrollable_frame)
        self._setup_point_selection(scrollable_frame)
        self._setup_sizing_controls(scrollable_frame)
        self._setup_grading_controls(scrollable_frame)
        self._setup_block_list(scrollable_frame)
        
        self.update_3d_view()
        
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
    
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            num_points = len(self.mesh_data.points[name])
            self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")
    
    def on_layer_select(self, event):
        sel = self.layer_listbox.curselection()
        
        # Extract layer names
        self.selected_layers = []
        for idx in sel:
            text = self.layer_listbox.get(idx)
            name = text.split(" (z=")[0]
            self.selected_layers.append(name)
        
        if len(self.selected_layers) > 2:
            # Keep only last 2 selected
            self.selected_layers = self.selected_layers[-2:]
            # Update listbox selection
            self.layer_listbox.selection_clear(0, tk.END)
            for name in self.selected_layers:
                for idx in range(self.layer_listbox.size()):
                    if self.layer_listbox.get(idx).startswith(name):
                        self.layer_listbox.selection_set(idx)
        
        if len(self.selected_layers) == 2:
            self.layer_status.config(
                text=f"✓ Selected: {self.selected_layers[0]} & {self.selected_layers[1]}", 
                fg="green"
            )
        elif len(self.selected_layers) == 1:
            self.layer_status.config(
                text=f"Selected: {self.selected_layers[0]} - Select 1 more", 
                fg="orange"
            )
        else:
            self.layer_status.config(text="Select 2 layers", fg="gray")
        
        self.clear_point_selection()
        self.update_3d_view()
    
    def update_3d_view(self):
        self.ax_3d.clear()
        
        if len(self.selected_layers) != 2:
            self.ax_3d.text(0, 0, 0, "Select 2 layers first", 
                           fontsize=12, ha='center')
            self.canvas_3d.draw()
            return
        
        # Get points from selected layers
        all_points = []
        point_colors = []
        
        colors = ['red', 'blue']
        for i, layer in enumerate(self.selected_layers):
            z = self.mesh_data.layers[layer]
            for point_2d in self.mesh_data.points[layer]:
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                all_points.append(coords_3d)
                point_colors.append(colors[i])
        
        if not all_points:
            self.ax_3d.text(0, 0, 0, "No points in selected layers", 
                           fontsize=12, ha='center')
            self.canvas_3d.draw()
            return
        
        # Plot points
        for coords, color in zip(all_points, point_colors):
            self.ax_3d.scatter(*coords, c=color, s=100, alpha=0.6)
        
        # Plot connections within layers
        for i, layer in enumerate(self.selected_layers):
            z = self.mesh_data.layers[layer]
            points_2d = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1 = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2 = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    
                    self.ax_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], 
                                   colors[i] + '-', linewidth=2, alpha=0.5)
        
        # Highlight selected points
        for layer, idx in self.selected_points:
            if layer in self.selected_layers:
                point_2d = self.mesh_data.points[layer][idx]
                coords = self.mesh_data.get_3d_coords(layer, point_2d)
                self.ax_3d.scatter(*coords, c='green', s=200, marker='o', 
                                  edgecolors='darkgreen', linewidths=3, alpha=0.8)
        
        # Draw existing hex blocks
        for block in self.hex_blocks:
            self._draw_hex_block(block)
        
        # Set labels and limits
        self.ax_3d.set_xlabel('X')
        self.ax_3d.set_ylabel('Z')
        self.ax_3d.set_zlabel('Y')
        
        # Auto-scale
        if all_points:
            xs, ys, zs = zip(*all_points)
            self.ax_3d.set_xlim(min(xs)-1, max(xs)+1)
            self.ax_3d.set_ylim(min(ys)-1, max(ys)+1)
            self.ax_3d.set_zlim(min(zs)-1, max(zs)+1)
        
        self.ax_3d.set_title(f"Layers: {self.selected_layers[0]} (red) & {self.selected_layers[1]} (blue)")
        
        self.canvas_3d.draw()
    
    def _draw_hex_block(self, block):
        """Draw a hex block in the 3D view"""
        verts = block['vertices']
        
        # Draw edges of hex
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
            (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical edges
        ]
        
        for i, j in edges:
            p1 = verts[i]
            p2 = verts[j]
            self.ax_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], 
                           'g-', linewidth=2, alpha=0.7)
    
    def on_3d_click(self, event):
        if event.inaxes != self.ax_3d or len(self.selected_layers) != 2:
            return
        
        if event.button != 1:  # Only left click
            return
        
        # Find closest point
        min_dist = float('inf')
        closest = None
        
        # Get 2D projection of click
        x2d, y2d = event.xdata, event.ydata
        
        for layer in self.selected_layers:
            z = self.mesh_data.layers[layer]
            for idx, point_2d in enumerate(self.mesh_data.points[layer]):
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                
                # Project to 2D screen space (approximate)
                proj = self.ax_3d.transData.transform(coords_3d)
                click_proj = self.ax_3d.transData.transform([x2d, y2d, 0])
                
                dist = np.sqrt((proj[0] - event.x)**2 + (proj[1] - event.y)**2)
                
                if dist < min_dist and dist < 30:  # 30 pixel threshold
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
            self.update_3d_view()
    
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
        self.update_3d_view()
    
    def update_sizing_ui(self):
        # Hide all frames
        self.universal_frame.pack_forget()
        self.mode_2d_frame.pack_forget()
        self.custom_frame.pack_forget()
        
        # Show appropriate frame
        mode = self.sizing_mode.get()
        if mode == "universal":
            self.universal_frame.pack(fill=tk.X, pady=5)
        elif mode == "2d":
            self.mode_2d_frame.pack(fill=tk.X, pady=5)
        elif mode == "custom":
            self.custom_frame.pack(fill=tk.X, pady=5)
    
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