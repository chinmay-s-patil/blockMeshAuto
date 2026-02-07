"""
Hex Block Making Tab - With embedded 3D viewer and 4 sub-tabs
Vertex Order for Hex Block (OpenFOAM standard):
    Bottom face (z=min): 0-1-2-3 (counter-clockwise when viewed from -z)
    Top face (z=max): 4-5-6-7 (counter-clockwise when viewed from +z)
    Vertical edges: 0-4, 1-5, 2-6, 3-7
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import numpy as np
import math
from tab3_Hex.pyvista_embedded import EmbeddedPyVistaViewer


class TabHexBlockMaking:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Block management - use mesh_data.hex_blocks for persistence
        self.selected_points = []  # List of global indices
        self.current_block_idx = None
        self.editing_block_idx = None  # Track which block is being edited
        
        # Division settings
        self.division_mode = tk.StringVar(value="direct")
        self.nx_var = tk.IntVar(value=10)
        self.ny_var = tk.IntVar(value=10)
        self.nz_var = tk.IntVar(value=10)
        self.cell_size_var = tk.DoubleVar(value=1.0)
        self.sizing_mode = tk.StringVar(value="3d")
        self.single_div_dir = tk.StringVar(value="Z")
        self.grading_type = tk.StringVar(value="simpleGrading")
        self.grading_x = tk.DoubleVar(value=1.0)
        self.grading_y = tk.DoubleVar(value=1.0)
        self.grading_z = tk.DoubleVar(value=1.0)
        
        # Viewer
        self.viewer = None
        
        # Edit window reference
        self.edit_window = None
        
        self.setup_ui()
        
    @property
    def hex_blocks(self):
        """Access hex blocks from mesh_data for persistence"""
        return self.mesh_data.hex_blocks
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View (larger, centered)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Interactive 3D Hex Block Builder (Click points to select)",
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # 3D Viewer Frame
        viewer_frame = tk.Frame(left_frame, bg='#1e1e1e')
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize embedded viewer
        self.viewer = EmbeddedPyVistaViewer(viewer_frame, self.mesh_data, self)
        
        # Info label at bottom of viewer (no reset/refresh buttons here anymore)
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="Mouse: Left-Rotate | Right-Pan | Scroll-Zoom | Click: Select | Order: Bottom CCW, Top CCW",
                font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=10)
        
        # Right: Tabbed controls (The 4 tabs like old code)
        right_frame = tk.Frame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs - exactly like old code
        self.tab_layers = tk.Frame(self.notebook)
        self.tab_points = tk.Frame(self.notebook)
        self.tab_sizing = tk.Frame(self.notebook)
        self.tab_blocks = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_layers, text="1. Layers")
        self.notebook.add(self.tab_points, text="2. Points")
        self.notebook.add(self.tab_sizing, text="3. Sizing")
        self.notebook.add(self.tab_blocks, text="4. Blocks")
        
        self._setup_layers_tab()
        self._setup_points_tab()
        self._setup_sizing_tab()
        self._setup_blocks_tab()
        
        # Initialize data
        self.refresh_layers()
        self.update_block_list()  # Load any existing blocks from mesh_data
        
    def _setup_layers_tab(self):
        """Setup the Layers selection tab"""
        frame = tk.Frame(self.tab_layers)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Select Layers (Click to toggle)",
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Button(frame, text="🔄 Refresh Layers", command=self.refresh_layers,
                 bg="lightgreen", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame, text="Click any layer to select/deselect (no Ctrl needed):",
                font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        self.layer_listbox = tk.Listbox(frame, height=10, selectmode=tk.EXTENDED,
                                       exportselection=False)  # Prevent losing selection on click
        self.layer_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Custom binding for toggle selection without Ctrl
        self.layer_listbox.bind('<Button-1>', self._on_layer_click)
        
        # LAYER FILTERING: Also update viewer when selection changes
        self.layer_listbox.bind('<<ListboxSelect>>', self._on_layer_selection_changed)
        
        self.layer_status = tk.Label(frame, text="Select layers to visualize",
                                     fg="gray", font=("Arial", 9, "italic"))
        self.layer_status.pack(pady=10)
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Select All", command=self._select_all_layers,
                 bg="lightgray", font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self._clear_all_layers,
                 bg="lightgray", font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Cube vertex order explanation
        help_text = """Vertex Selection Order for Cube:
        
  7--------6         Select 4 points on BOTTOM layer
  /|       /|         (counter-clockwise looking down)
 4--------5 |         
 | |      | |         Then 4 points on TOP layer  
 | 3------|-2         (counter-clockwise looking down)
 |/       |/          
 0--------1           
                      
Click in 3D view to select points (max 8)."""
        
        tk.Label(frame, text=help_text,
                font=("Courier", 9), fg="darkblue", justify=tk.LEFT, bg='#f0f0f0').pack(pady=10, fill=tk.X)
    
    def _on_layer_click(self, event):
        """Toggle layer selection on single click without requiring Ctrl"""
        index = self.layer_listbox.nearest(event.y)
        if self.layer_listbox.selection_includes(index):
            self.layer_listbox.selection_clear(index)
        else:
            self.layer_listbox.selection_set(index)
        return "break"  # Prevent default handling
    
    def _on_layer_selection_changed(self, event=None):
        """LAYER FILTERING: Update viewer when layer selection changes"""
        if not self.viewer:
            return
            
        # Get selected layer names from listbox
        selected_indices = self.layer_listbox.curselection()
        selected_layers = []
        
        # Get layer names from the listbox entries
        for i in selected_indices:
            layer_text = self.layer_listbox.get(i)
            # Extract layer name from text like "Layer 0 (z=0.0, 24 pts)"
            layer_name = layer_text.split(' (')[0]
            selected_layers.append(layer_name)
        
        # Update viewer with selected layers
        self.viewer.set_visible_layers(selected_layers)
        
        # Update status label
        if selected_layers:
            self.layer_status.config(text=f"Showing {len(selected_layers)} layer(s): {', '.join(selected_layers)}")
        else:
            self.layer_status.config(text="No layers selected - showing all")
    
    def _select_all_layers(self):
        self.layer_listbox.select_set(0, tk.END)
        self._on_layer_selection_changed()  # LAYER FILTERING: Update viewer
    
    def _clear_all_layers(self):
        self.layer_listbox.selection_clear(0, tk.END)
        self._on_layer_selection_changed()  # LAYER FILTERING: Update viewer
        
    def _setup_points_tab(self):
        """Setup the Points selection tab"""
        frame = tk.Frame(self.tab_points)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Point Selection (Global Numbers)",
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        info_text = """Click points in 3D view to toggle selection.
Select exactly 8 points (4 from bottom layer, 4 from top layer).

ORDER MATTERS for hex block:
Bottom layer: 0→1→2→3 (counter-clockwise, viewed from below)
Top layer: 4→5→6→7 (counter-clockwise, viewed from above)"""
        
        tk.Label(frame, text=info_text, font=("Arial", 9), justify=tk.LEFT, fg="gray").pack(anchor=tk.W, pady=(0, 10))
        
        self.point_status = tk.Label(frame, text="Selected: 0/8 points",
                                     fg="blue", font=("Arial", 10, "bold"))
        self.point_status.pack(pady=5)
        
        # Selected points list
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_list = tk.Listbox(list_frame, height=15, font=("Courier", 9),
                                     yscrollcommand=scroll.set, bg='#2d2d2d', fg='white',
                                     selectbackground='#404040')
        self.point_list.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.point_list.yview)
        
        # Control buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Hide Selected", command=self.hide_selected,
                 bg="yellow", font=("Arial", 9)).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show Only Selected", command=self.show_only_selected,
                 bg="lightblue", font=("Arial", 9)).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show All Points", command=self.show_all,
                 bg="lightgreen", font=("Arial", 9)).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Clear Selection", command=self.clear_point_selection,
                 bg="salmon", font=("Arial", 9)).pack(fill=tk.X, pady=2)
        
    def _setup_sizing_tab(self):
        """Setup the Sizing/Grading tab"""
        frame = tk.Frame(self.tab_sizing)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Cell Sizing & Grading",
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Division mode
        div_frame = tk.LabelFrame(frame, text="Division Mode", padx=10, pady=10)
        div_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(div_frame, text="Direct (specify number of cells)",
                      variable=self.division_mode, value="direct",
                      command=self.update_division_ui, font=("Arial", 9)).pack(anchor=tk.W)
        tk.Radiobutton(div_frame, text="Cell Size (auto-calculate)",
                      variable=self.division_mode, value="cell_size",
                      command=self.update_division_ui, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Direct divisions inputs
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
        
        # Cell size mode inputs
        self.cellsize_frame = tk.Frame(frame)
        
        row = tk.Frame(self.cellsize_frame)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text="Target cell size:", width=15, anchor=tk.W,
                font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.cell_size_var, width=10,
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
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
        
        # Grading section
        grade_frame = tk.LabelFrame(frame, text="Grading", padx=10, pady=10)
        grade_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(grade_frame, text="simpleGrading:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        for label, var in [("X ratio:", self.grading_x),
                          ("Y ratio:", self.grading_y),
                          ("Z ratio:", self.grading_z)]:
            row = tk.Frame(grade_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=10, anchor=tk.W).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=8).pack(side=tk.LEFT)
        
        # Create button
        tk.Button(frame, text="Create Hex Block", command=self.create_hex_block,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, pady=20)
        
        self.update_division_ui()
        
    def _setup_blocks_tab(self):
        """Setup the Blocks management tab"""
        frame = tk.Frame(self.tab_blocks)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Created Blocks",
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.block_listbox = tk.Listbox(frame, font=("Courier", 9),
                                        yscrollcommand=scroll.set, bg='#2d2d2d', fg='white',
                                        selectbackground='#404040')
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scroll.config(command=self.block_listbox.yview)
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_block,
                 bg="salmon", width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit Selected", command=self.edit_block,
                 bg="lightblue", width=12).pack(side=tk.LEFT, padx=2)
        
        # Block info display
        self.block_info = tk.Label(frame, text="", font=("Arial", 9), 
                                  justify=tk.LEFT, fg="gray")
        self.block_info.pack(anchor=tk.W, pady=10)
    
    def update_division_ui(self):
        """Show/hide division inputs based on mode"""
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
        
        # LAYER FILTERING: Select all layers by default
        self.layer_listbox.select_set(0, tk.END)
        self._on_layer_selection_changed()  # Update viewer with all layers
        
    def reset_view(self):
        """Reset 3D view"""
        if self.viewer:
            self.viewer.reset_view()
    
    def refresh_view(self):
        """Refresh 3D visualization"""
        if self.viewer:
            self.viewer.refresh()
    
    def on_selection_changed(self, selected_set):
        """Called by viewer when points are clicked"""
        # Preserve selection order - do NOT sort!
        self.selected_points = list(selected_set)
        self.update_point_list()
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
    
    def update_point_list(self):
        """Update the points listbox"""
        self.point_list.delete(0, tk.END)
        for global_idx in self.selected_points:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            point_2d = self.mesh_data.points[layer][local_idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            self.point_list.insert(tk.END,
                f"Point {global_idx}: {layer}[{local_idx}] "
                f"({coords_3d[0]:.2f},{coords_3d[1]:.2f},{coords_3d[2]:.2f})")
    
    def hide_selected(self):
        """Hide selected points"""
        if self.viewer:
            self.viewer.hide_selected()
    
    def show_only_selected(self):
        """Show only selected points"""
        if self.viewer:
            self.viewer.show_only_selected()
    
    def show_all(self):
        """Show all points"""
        if self.viewer:
            self.viewer.show_all()
    
    def clear_point_selection(self):
        """Clear point selection"""
        self.selected_points = []
        if self.viewer:
            self.viewer.clear_selection()
        self.update_point_list()
        self.point_status.config(text="Selected: 0/8 points")
    
    def _get_3d_coords_standard(self, global_idx):
        """
        Get 3D coordinates in standard (X, Y, Z) format.
        mesh_data.get_3d_coords returns (X, Z, Y) for XY plane.
        """
        layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
        point_2d = self.mesh_data.points[layer][local_idx]
        coords_raw = self.mesh_data.get_3d_coords(layer, point_2d)
        # Swap Y and Z: mesh_data returns (X, Z, Y), we want (X, Y, Z)
        x, z, y = coords_raw
        return (x, y, z)
    
    def create_hex_block(self):
        """Create a hexahedral block from selected points"""
        if len(self.selected_points) != 8:
            messagebox.showwarning("Warning", f"Need exactly 8 points, have {len(self.selected_points)}")
            return
        
        # Trust the user's selection order exactly as OpenFOAM expects:
        # User selects: 0, 1, 2, 3 on bottom (CCW from below)
        # Then: 4, 5, 6, 7 on top (CCW from above)
        # Vertical edges are: 0-4, 1-5, 2-6, 3-7
        
        vertices = []
        layers_used = set()
        
        for global_idx in self.selected_points:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            layers_used.add(layer)
            coords_3d = self._get_3d_coords_standard(global_idx)
            vertices.append(coords_3d)
        
        if len(layers_used) != 2:
            messagebox.showerror("Error", "Points must come from exactly 2 layers (4 bottom, 4 top)")
            return
        
        # Validate: first 4 should be bottom layer (lower Z), last 4 should be top
        z_bottom = [v[2] for v in vertices[0:4]]
        z_top = [v[2] for v in vertices[4:8]]
        
        if max(z_bottom) > min(z_top):
            messagebox.showerror("Error", 
                "First 4 points must be on the bottom layer (lower Z),\\n"
                "and last 4 points must be on the top layer (higher Z)")
            return
        
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
            'vertices': vertices,  # In OpenFOAM order: 0-1-2-3 bottom, 4-5-6-7 top
            'point_refs': self.selected_points.copy(),  # Store the global indices used
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {'x': self.grading_x.get(),
                             'y': self.grading_y.get(),
                             'z': self.grading_z.get()}
        }
        
        # Add to mesh_data.hex_blocks for persistence
        self.mesh_data.hex_blocks.append(block)
        self.update_block_list()
        self.clear_point_selection()
        if self.viewer:
            self.viewer.draw()
        messagebox.showinfo("Success", f"Hex Block created!\\n\\n"
                           f"Vertex order: 0-1-2-3 (bottom), 4-5-6-7 (top)\\n"
                           f"Divisions: {nx}×{ny}×{nz}\\n"
                           f"Grading: ({self.grading_x.get()}, {self.grading_y.get()}, {self.grading_z.get()})")
    
    def _calculate_divisions(self, vertices, cell_size):
        """Calculate divisions from cell size using OpenFOAM edge definitions"""
        # OpenFOAM hex edge definitions:
        # X edges: 0-1, 3-2, 4-5, 7-6
        x_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(0,1), (3,2), (4,5), (7,6)]]
        # Y edges: 1-2, 0-3, 5-6, 4-7
        y_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(1,2), (0,3), (5,6), (4,7)]]
        # Z edges: 0-4, 1-5, 2-6, 3-7 (vertical)
        z_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(0,4), (1,5), (2,6), (3,7)]]
        
        nx = max(1, int(round(np.mean(x_edges) / cell_size)))
        ny = max(1, int(round(np.mean(y_edges) / cell_size)))
        nz = max(1, int(round(np.mean(z_edges) / cell_size)))
        return nx, ny, nz
    
    def update_block_list(self):
        """Update block list display"""
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.mesh_data.hex_blocks):
            nx, ny, nz = block['divisions']
            grading = block['grading_type']
            self.block_listbox.insert(tk.END, f"Block {i}: {nx}×{ny}×{nz}, {grading}")
    
    def on_block_select(self, event):
        """Handle block selection"""
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
            # Show block info
            block = self.mesh_data.hex_blocks[self.current_block_idx]
            verts = block['vertices']
            info = f"Vertices: {len(verts)}\\nDivisions: {block['divisions']}\\nGrading: {block['grading_params']}"
            self.block_info.config(text=info)
            
            # Highlight the selected block's points in the viewer
            if self.viewer and block.get('point_refs'):
                self.viewer.set_selection(set(block['point_refs']))
    
    def edit_block(self):
        """Open edit dialog for selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block to edit first")
            return
        
        # Close existing edit window if open
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()
        
        block = self.mesh_data.hex_blocks[self.current_block_idx]
        self.editing_block_idx = self.current_block_idx
        
        # Create edit window
        self.edit_window = tk.Toplevel(self.parent)
        self.edit_window.title(f"Edit Block {self.current_block_idx}")
        self.edit_window.geometry("350x500")
        self.edit_window.transient(self.parent)  # Stay on top of parent
        self.edit_window.grab_set()  # Modal
        
        # Create form
        frame = tk.Frame(self.edit_window, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Editing Block {self.current_block_idx}", 
                font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Divisions
        div_frame = tk.LabelFrame(frame, text="Divisions", padx=5, pady=5)
        div_frame.pack(fill=tk.X, pady=5)
        
        nx, ny, nz = block['divisions']
        
        tk.Label(div_frame, text="X divisions:").pack(anchor=tk.W)
        nx_var = tk.IntVar(value=nx)
        tk.Entry(div_frame, textvariable=nx_var).pack(fill=tk.X)
        
        tk.Label(div_frame, text="Y divisions:").pack(anchor=tk.W)
        ny_var = tk.IntVar(value=ny)
        tk.Entry(div_frame, textvariable=ny_var).pack(fill=tk.X)
        
        tk.Label(div_frame, text="Z divisions:").pack(anchor=tk.W)
        nz_var = tk.IntVar(value=nz)
        tk.Entry(div_frame, textvariable=nz_var).pack(fill=tk.X)
        
        # Grading
        grade_frame = tk.LabelFrame(frame, text="Grading", padx=5, pady=5)
        grade_frame.pack(fill=tk.X, pady=5)
        
        gp = block['grading_params']
        
        tk.Label(grade_frame, text="X ratio:").pack(anchor=tk.W)
        gx_var = tk.DoubleVar(value=gp['x'])
        tk.Entry(grade_frame, textvariable=gx_var).pack(fill=tk.X)
        
        tk.Label(grade_frame, text="Y ratio:").pack(anchor=tk.W)
        gy_var = tk.DoubleVar(value=gp['y'])
        tk.Entry(grade_frame, textvariable=gy_var).pack(fill=tk.X)
        
        tk.Label(grade_frame, text="Z ratio:").pack(anchor=tk.W)
        gz_var = tk.DoubleVar(value=gp['z'])
        tk.Entry(grade_frame, textvariable=gz_var).pack(fill=tk.X)
        
        # Grading type
        tk.Label(frame, text="Grading Type:").pack(anchor=tk.W, pady=(10, 0))
        grading_type_var = tk.StringVar(value=block['grading_type'])
        tk.OptionMenu(frame, grading_type_var, "simpleGrading", "edgeGrading", "multiGrading").pack(fill=tk.X)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        def save_changes():
            # Update block with new values
            block['divisions'] = (nx_var.get(), ny_var.get(), nz_var.get())
            block['grading_params'] = {
                'x': gx_var.get(),
                'y': gy_var.get(),
                'z': gz_var.get()
            }
            block['grading_type'] = grading_type_var.get()
            
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
            self.edit_window.destroy()
            messagebox.showinfo("Success", "Block updated!")
        
        def highlight_vertices():
            """Highlight the vertices of this block in the 3D view"""
            if self.viewer and block.get('point_refs'):
                self.viewer.set_selection(set(block['point_refs']))
                # Switch to points tab to see selection
                self.notebook.select(self.tab_points)
        
        tk.Button(btn_frame, text="💾 Save Changes", command=save_changes,
                 bg="lightgreen", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="👁 Highlight Vertices", command=highlight_vertices,
                 bg="lightblue").pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="❌ Cancel", command=self.edit_window.destroy,
                 bg="salmon").pack(fill=tk.X, pady=2)
        
        # Show current vertices info
        info_frame = tk.LabelFrame(frame, text="Current Vertices", padx=5, pady=5)
        info_frame.pack(fill=tk.X, pady=5)
        
        verts = block['vertices']
        info_text = ""
        for i, v in enumerate(verts):
            info_text += f"{i}: ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})\\n"
        tk.Label(info_frame, text=info_text, font=("Courier", 8), justify=tk.LEFT).pack(anchor=tk.W)
    
    def delete_block(self):
        """Delete selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        if messagebox.askyesno("Confirm", "Delete block?"):
            del self.mesh_data.hex_blocks[self.current_block_idx]
            self.current_block_idx = None
            self.block_info.config(text="")
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
    
    def clear_all_blocks(self):
        """Clear all blocks"""
        if not self.mesh_data.hex_blocks:
            return
        if messagebox.askyesno("Confirm", "Delete all blocks?"):
            self.mesh_data.hex_blocks.clear()
            self.current_block_idx = None
            self.block_info.config(text="")
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
    
    def get_hex_blocks(self):
        """Get all hex blocks"""
        return self.mesh_data.hex_blocks
    
    def cleanup(self):
        """Call when closing"""
        if self.viewer:
            self.viewer.close()
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()