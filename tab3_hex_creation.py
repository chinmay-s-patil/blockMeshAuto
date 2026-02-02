"""
Hex Block Making Tab - Create hexahedral blocks with PyVista 3D viewer
- Left-click drag: Rotate
- Right-click drag: Pan  
- Scroll wheel: Zoom
- Click point: Select/Deselect toggle
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import numpy as np
import pyvista as pv
import threading
import time


class PyVistaHexViewer:
    """PyVista-based 3D viewer with point picking - FIXED for Tkinter compatibility"""
    def __init__(self, mesh_data, parent_tab):
        self.mesh_data = mesh_data
        self.parent = parent_tab  # Tkinter parent widget
        self.plotter = None
        self.selected_points = set()  # Global indices
        self.hidden_points = set()
        self._setup_plotter()
        
        # Start update pump from Tkinter's main loop (NO THREADING)
        self._pump_pyvista()
        
    def _setup_plotter(self):
        """Initialize PyVista plotter"""
        self.plotter = pv.Plotter(
            title="3D Hex Block Builder - Click to Toggle Points",
            window_size=[800, 600],
            off_screen=False
        )
        self.plotter.background_color = 'white'
        
        # Enable point picking (click to pick)
        self.plotter.enable_point_picking(
            callback=self._on_point_click,
            use_picker=True,
            show_point=False,
            show_message=False,
            tolerance=0.01
        )
        
        # Show in non-blocking mode
        self.plotter.show(interactive=False, auto_close=False)
        
    def _pump_pyvista(self):
        """Update PyVista window from Tkinter's main loop"""
        if self.plotter and not self.plotter._closed:
            self.plotter.update()
        # Schedule next update in 50ms (~20 FPS)
        self.parent.after(50, self._pump_pyvista)
        
    def _on_point_click(self, point):
        """Handle point picking - toggle selection"""
        if point is None:
            return
            
        # Find closest global point
        global_idx = self._find_closest_global_point(point)
        if global_idx is None:
            return
            
        # Toggle selection (no Ctrl needed)
        if global_idx in self.selected_points:
            self.selected_points.remove(global_idx)
        else:
            if len(self.selected_points) < 8:
                self.selected_points.add(global_idx)
            else:
                messagebox.showwarning("Limit", "Maximum 8 points allowed")
                return
        
        # Update parent UI (use tkinter's thread-safe method)
        self.parent.after(0, lambda: self.parent.on_selection_changed(self.selected_points.copy()))
        self.draw()
        
    def _find_closest_global_point(self, coord):
        """Find global point index closest to picked coordinate"""
        coord = np.array(coord)
        min_dist = float('inf')
        closest_idx = None
        
        if not hasattr(self, '_global_coords'):
            self._rebuild_coord_cache()
            
        for idx, pt_coord in enumerate(self._global_coords):
            if idx in self.hidden_points:
                continue
            dist = np.linalg.norm(pt_coord - coord)
            if dist < min_dist and dist < 0.5:
                min_dist = dist
                closest_idx = idx
                
        return closest_idx
        
    def _rebuild_coord_cache(self):
        """Cache all global point coordinates"""
        coords = []
        self._global_to_local = {}
        
        idx = 0
        for layer_name in sorted(self.mesh_data.layers.keys(), 
                                key=lambda x: self.mesh_data.layers[x]):
            if layer_name in self.mesh_data.points:
                for local_idx, pt_2d in enumerate(self.mesh_data.points[layer_name]):
                    coord_3d = self.mesh_data.get_3d_coords(layer_name, pt_2d)
                    coords.append(coord_3d)
                    self._global_to_local[idx] = (layer_name, local_idx)
                    idx += 1
                    
        self._global_coords = np.array(coords)
        self._total_points = idx
        
    def hide_selected(self):
        """Hide currently selected points"""
        self.hidden_points.update(self.selected_points)
        self.selected_points.clear()
        self.draw()
        self.parent.update_point_list()
        
    def show_only_selected(self):
        """Show only selected points, hide others"""
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
        
    def draw(self):
        """Redraw the 3D scene"""
        if not self.plotter or self.plotter._closed:
            return
            
        self.plotter.clear()
        self._rebuild_coord_cache()
        
        if len(self._global_coords) == 0:
            self.plotter.add_text("No points to display", font_size=20)
            return
            
        # Colors for layers
        color_map = ['red', 'blue', 'green', 'orange', 'purple', 'cyan']
        layer_list = sorted(self.mesh_data.layers.keys(), 
                           key=lambda x: self.mesh_data.layers[x])
        layer_to_idx = {name: i for i, name in enumerate(layer_list)}
        
        # Organize points by state
        visible_by_layer = {i: [] for i in range(len(self.mesh_data.layers))}
        selected_list = []
        
        for global_idx, coord in enumerate(self._global_coords):
            if global_idx in self.hidden_points:
                continue
                
            layer_name, _ = self._global_to_local[global_idx]
            layer_idx = layer_to_idx[layer_name]
            
            if global_idx in self.selected_points:
                selected_list.append((global_idx, coord))
            else:
                visible_by_layer[layer_idx].append((global_idx, coord))
                
        # Draw unselected points by layer
        for layer_idx, pts in visible_by_layer.items():
            if not pts:
                continue
            coords = np.array([p[1] for p in pts])
            cloud = pv.PolyData(coords)
            color = color_map[layer_idx % len(color_map)]
            self.plotter.add_points(cloud, color=color, point_size=10, 
                                   render_points_as_spheres=True)
            # Labels
            labels = [str(p[0]) for p in pts]
            if len(labels) > 0:
                self.plotter.add_point_labels(coords, labels, font_size=10, 
                                             text_color=color, show_points=False,
                                             shape_opacity=0.3, font_family='courier')
        
        # Draw selected points (lime, larger)
        if selected_list:
            coords = np.array([p[1] for p in selected_list])
            cloud = pv.PolyData(coords)
            self.plotter.add_points(cloud, color='lime', point_size=15, 
                                   render_points_as_spheres=True)
            labels = [f"{p[0]}*" for p in selected_list]
            self.plotter.add_point_labels(coords, labels, font_size=12, 
                                         text_color='darkgreen', show_points=False,
                                         shape_color='lightgreen', shape_opacity=0.5)
        
        # Draw connections
        for layer_name in layer_list:
            if layer_name not in self.mesh_data.connections:
                continue
            layer_idx = layer_to_idx[layer_name]
            color = color_map[layer_idx % len(color_map)]
            
            for conn in self.mesh_data.connections[layer_name]:
                p1_local, p2_local = conn
                p1_global = self._local_to_global(layer_name, p1_local)
                p2_global = self._local_to_global(layer_name, p2_local)
                
                if p1_global in self.hidden_points or p2_global in self.hidden_points:
                    continue
                    
                if (p1_global < len(self._global_coords) and 
                    p2_global < len(self._global_coords)):
                    line = pv.Line(self._global_coords[p1_global], 
                                  self._global_coords[p2_global])
                    self.plotter.add_mesh(line, color=color, line_width=3)
        
        # Draw inter-layer connections
        for layer1, idx1, layer2, idx2 in getattr(self.mesh_data, 'inter_layer_connections', []):
            g1 = self._local_to_global(layer1, idx1)
            g2 = self._local_to_global(layer2, idx2)
            
            if g1 in self.hidden_points or g2 in self.hidden_points:
                continue
                
            if g1 < len(self._global_coords) and g2 < len(self._global_coords):
                line = pv.Line(self._global_coords[g1], self._global_coords[g2])
                self.plotter.add_mesh(line, color='gray', line_width=2)
        
        # Draw hex blocks
        for block in getattr(self.parent, 'hex_blocks', []):
            verts = block['vertices']
            # Edges
            edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7)]
            for i, j in edges:
                line = pv.Line(verts[i], verts[j])
                self.plotter.add_mesh(line, color='darkgreen', line_width=4)
            
            # Faces (translucent)
            faces = [
                [verts[0], verts[1], verts[2], verts[3]],
                [verts[4], verts[5], verts[6], verts[7]], 
                [verts[0], verts[1], verts[5], verts[4]],
                [verts[2], verts[3], verts[7], verts[6]],
                [verts[1], verts[2], verts[6], verts[5]],
                [verts[0], verts[3], verts[7], verts[4]]
            ]
            for face in faces:
                if len(face) == 4:
                    face_mesh = pv.Rectangle(face)
                    self.plotter.add_mesh(face_mesh, color='lightgreen', 
                                        opacity=0.2, show_edges=True, 
                                        edge_color='green', line_width=1)
        
        # Instructions
        self.plotter.add_text("Click: Toggle Select | Drag: Rotate/Pan | Scroll: Zoom", 
                             position='lower_left', font_size=10, color='black')
        
        self.plotter.render()
        
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
        
    def reset_view(self):
        """Reset camera"""
        if self.plotter:
            self.plotter.reset_camera()
            self.plotter.render()
        
    def close(self):
        """Cleanup"""
        if self.plotter:
            self.plotter.close()

class TabHexBlockMaking:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Block management - now using GLOBAL indices
        self.hex_blocks = []
        self.selected_points = []  # List of global indices (continuous numbering)
        self.current_block_idx = None
        
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
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Controls (since PyVista opens separate window or we embed instructions)
        left_frame = tk.Frame(main_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        left_frame.pack_propagate(False)
        
        # Instructions
        tk.Label(left_frame, text="3D Hex Block Builder", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        info_text = """Controls:
• Left-drag: Rotate view
• Right-drag: Pan view  
• Scroll: Zoom
• Click point: Select/Deselect (toggle)
• Click again on selected: Deselect"""
        
        tk.Label(left_frame, text=info_text, justify=tk.LEFT, 
                font=("Courier", 10)).pack(anchor=tk.W, padx=10, pady=5)
        
        # Selection management
        sel_frame = tk.LabelFrame(left_frame, text="Point Selection (Global Numbers)", padx=10, pady=10)
        sel_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.point_status = tk.Label(sel_frame, text="Selected: 0/8 points", 
                                    font=("Arial", 11, "bold"), fg="blue")
        self.point_status.pack(pady=5)
        
        # Listbox with scrollbar showing selected points
        list_frame = tk.Frame(sel_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_list = tk.Listbox(list_frame, height=8, font=("Courier", 10),
                                     yscrollcommand=scroll.set)
        self.point_list.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.point_list.yview)
        
        # NEW: Hide/Show buttons
        btn_frame = tk.Frame(sel_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Hide Selected", command=self.hide_selected,
                 bg="yellow", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Show Only Selected", command=self.show_only_selected,
                 bg="lightblue", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Show All", command=self.show_all,
                 bg="lightgreen", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear Selection", command=self.clear_selection,
                 bg="salmon", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Layer info (for context)
        tk.Label(sel_frame, text="Layers available:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10,0))
        self.layer_info = tk.Label(sel_frame, text="", font=("Arial", 9))
        self.layer_info.pack(anchor=tk.W)
        
        # Block creation
        block_frame = tk.LabelFrame(left_frame, text="Create Block", padx=10, pady=10)
        block_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(block_frame, text="Create Hex Block (8 points)", 
                 command=self.create_hex_block,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, pady=5)
        
        # Division settings
        div_frame = tk.Frame(block_frame)
        div_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(div_frame, text="Divisions X/Y/Z:").pack(side=tk.LEFT)
        for var in [self.nx_var, self.ny_var, self.nz_var]:
            tk.Entry(div_frame, textvariable=var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Blocks list
        blocks_frame = tk.LabelFrame(left_frame, text="Created Blocks", padx=10, pady=10)
        blocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll2 = tk.Scrollbar(blocks_frame)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.block_listbox = tk.Listbox(blocks_frame, font=("Courier", 9),
                                        yscrollcommand=scroll2.set)
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scroll2.config(command=self.block_listbox.yview)
        
        btn_frame2 = tk.Frame(blocks_frame)
        btn_frame2.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame2, text="Delete Block", command=self.delete_block,
                 bg="salmon", width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame2, text="Clear All", command=self.clear_all_blocks,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=2)
        
        # Change this line in TabHexBlockMaking.setup_ui():
        self.viewer = PyVistaHexViewer(self.mesh_data, self.parent)
        self.update_layer_info()
        
    def update_layer_info(self):
        """Update layer info display"""
        info = []
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            count = len(self.mesh_data.points.get(name, []))
            info.append(f"{name}: {count} pts")
        self.layer_info.config(text="\n".join(info))
        
    def on_selection_changed(self, selected_set):
        """Callback from viewer when selection changes"""
        self.selected_points = sorted(list(selected_set))
        self.update_point_list()
        
    def update_point_list(self):
        """Update the listbox with selected points (global numbering)"""
        self.point_list.delete(0, tk.END)
        
        for global_idx in self.selected_points:
            # Convert global to local for coordinate display
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            point_2d = self.mesh_data.points[layer][local_idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            
            self.point_list.insert(tk.END, 
                f"Point {global_idx}: {layer}[{local_idx}] "
                f"({coords_3d[0]:.2f}, {coords_3d[1]:.2f}, {coords_3d[2]:.2f})")
        
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
        
    def hide_selected(self):
        """Hide selected points from view"""
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
            
    def clear_selection(self):
        """Clear point selection"""
        self.selected_points = []
        if self.viewer:
            self.viewer.clear_selection()
        self.update_point_list()
        
    def create_hex_block(self):
        """Create a hexahedral block from selected points"""
        if len(self.selected_points) != 8:
            messagebox.showwarning("Warning", f"Need exactly 8 points, have {len(self.selected_points)}")
            return
        
        # Get coordinates for all 8 points
        vertices = []
        layers_used = set()
        
        for global_idx in self.selected_points:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            layers_used.add(layer)
            point_2d = self.mesh_data.points[layer][local_idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            vertices.append(coords_3d)
        
        if len(layers_used) != 2:
            messagebox.showerror("Error", "Points must come from exactly 2 layers (4 from each)")
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
            'vertices': vertices,
            'point_refs': self.selected_points.copy(),  # Store global indices
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {'x': self.grading_x.get(),
                             'y': self.grading_y.get(),
                             'z': self.grading_z.get()}
        }
        
        self.hex_blocks.append(block)
        self.update_block_list()
        self.clear_selection()
        if self.viewer:
            self.viewer.draw()
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
        """Update block list display"""
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.hex_blocks):
            nx, ny, nz = block['divisions']
            grading = block['grading_type']
            self.block_listbox.insert(tk.END, f"Block {i}: {nx}×{ny}×{nz}, {grading}")
            
    def on_block_select(self, event):
        """Handle block selection"""
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
            
    def delete_block(self):
        """Delete selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        if messagebox.askyesno("Confirm", "Delete block?"):
            del self.hex_blocks[self.current_block_idx]
            self.current_block_idx = None
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
                
    def clear_all_blocks(self):
        """Clear all blocks"""
        if not self.hex_blocks:
            return
        if messagebox.askyesno("Confirm", "Delete all blocks?"):
            self.hex_blocks = []
            self.current_block_idx = None
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
                
    def get_hex_blocks(self):
        """Get all hex blocks"""
        return self.hex_blocks
        
    def cleanup(self):
        """Call this when closing tab/app"""
        if self.viewer:
            self.viewer.close()