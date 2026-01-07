"""
Hex Block Making Tab - Create hexahedral blocks with interactive 3D viewer
Enhanced 3D visualization with:
- Left-click drag: Rotate
- Right-click drag: Pan  
- Scroll wheel: Zoom
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Interactive3DViewer:
    """Interactive 3D viewer with mouse controls"""
    def __init__(self, figure, canvas, mesh_data):
        self.fig = figure
        self.canvas = canvas
        self.mesh_data = mesh_data
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # View state
        self.azim = 45
        self.elev = 30
        self.zoom_scale = 1.0
        
        # Mouse interaction
        self.mouse_down = False
        self.mouse_button = None
        self.last_x = None
        self.last_y = None
        
        # Data
        self.selected_layers = []
        self.selected_points = []
        self.hex_blocks = []
        self.canvas_point_map = []  # For point selection
        
        self._setup_view()
        self._connect_events()
        
    def _setup_view(self):
        """Initialize 3D view"""
        self.ax.set_xlabel('X', fontweight='bold')
        self.ax.set_ylabel('Y', fontweight='bold')
        self.ax.set_zlabel('Z', fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.view_init(elev=self.elev, azim=self.azim)
        
    def _connect_events(self):
        """Connect mouse events"""
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        
    def _on_press(self, event):
        """Mouse button press"""
        if event.inaxes != self.ax:
            return
        self.mouse_down = True
        self.mouse_button = event.button
        self.last_x = event.x
        self.last_y = event.y
        
    def _on_release(self, event):
        """Mouse button release"""
        # Check for point selection (left click without drag)
        if self.mouse_button == 1 and event.inaxes == self.ax:
            if self.last_x is not None and self.last_y is not None:
                dx = abs(event.x - self.last_x)
                dy = abs(event.y - self.last_y)
                if dx < 5 and dy < 5:  # Click, not drag
                    self._handle_point_click(event)
        
        self.mouse_down = False
        self.mouse_button = None
        
    def _on_motion(self, event):
        """Mouse motion"""
        if not self.mouse_down or event.inaxes != self.ax:
            return
        
        if self.last_x is None or self.last_y is None:
            self.last_x = event.x
            self.last_y = event.y
            return
        
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        if self.mouse_button == 1:  # Left button - rotate
            self.azim += dx * 0.5
            self.elev -= dy * 0.5
            self.elev = np.clip(self.elev, -90, 90)
            self.ax.view_init(elev=self.elev, azim=self.azim)
            self.canvas.draw_idle()
            
        elif self.mouse_button == 3:  # Right button - pan
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            zlim = self.ax.get_zlim()
            
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            
            pan_x = -dx * x_range * 0.002
            pan_y = dy * y_range * 0.002
            
            self.ax.set_xlim([xlim[0] + pan_x, xlim[1] + pan_x])
            self.ax.set_ylim([ylim[0] + pan_y, ylim[1] + pan_y])
            self.canvas.draw_idle()
        
        self.last_x = event.x
        self.last_y = event.y
        
    def _on_scroll(self, event):
        """Mouse scroll - zoom"""
        if event.inaxes != self.ax:
            return
        
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zlim = self.ax.get_zlim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        z_center = (zlim[0] + zlim[1]) / 2
        
        factor = 1.1 if event.button == 'up' else 0.9
        
        x_range = (xlim[1] - xlim[0]) * factor / 2
        y_range = (ylim[1] - ylim[0]) * factor / 2
        z_range = (zlim[1] - zlim[0]) * factor / 2
        
        self.ax.set_xlim([x_center - x_range, x_center + x_range])
        self.ax.set_ylim([y_center - y_range, y_center + y_range])
        self.ax.set_zlim([z_center - z_range, z_center + z_range])
        
        self.canvas.draw_idle()
        
    def _handle_point_click(self, event):
        """Handle point selection by clicking"""
        if not self.canvas_point_map:
            return
        
        # Find closest point in screen space
        min_dist = float('inf')
        closest_point = None
        
        for layer, idx, screen_x, screen_y in self.canvas_point_map:
            dist = np.sqrt((event.x - screen_x)**2 + (event.y - screen_y)**2)
            if dist < min_dist and dist < 30:  # 30 pixel threshold
                min_dist = dist
                closest_point = (layer, idx)
        
        if closest_point:
            # Notify parent (would need callback mechanism)
            self.on_point_selected(closest_point)
            
    def on_point_selected(self, point):
        """Override this in parent class"""
        pass
        
    def draw(self):
        """Draw the 3D scene"""
        self.ax.clear()
        self._setup_view()
        self.canvas_point_map = []
        
        if len(self.selected_layers) < 2:
            self.ax.text(0.5, 0.5, 0.5, "Select 2 layers first",
                        transform=self.ax.transAxes,
                        ha='center', va='center',
                        fontsize=16, color='gray')
            self.canvas.draw()
            return
        
        colors = ['red', 'blue', 'green', 'orange']
        all_coords = []
        
        # Draw points and collect coordinates
        for i, layer in enumerate(self.selected_layers):
            color = colors[i % len(colors)]
            points_2d = self.mesh_data.points[layer]
            
            for idx, point_2d in enumerate(points_2d):
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                all_coords.append(coords_3d)
                
                is_selected = (layer, idx) in self.selected_points
                size = 150 if is_selected else 80
                marker_color = 'lime' if is_selected else color
                edge_color = 'black' if is_selected else 'darkgray'
                alpha = 1.0 if is_selected else 0.7
                
                self.ax.scatter([coords_3d[0]], [coords_3d[1]], [coords_3d[2]],
                              c=[marker_color], s=size, alpha=alpha,
                              edgecolors=edge_color, linewidths=2,
                              depthshade=True)
                
                # Label
                self.ax.text(coords_3d[0], coords_3d[1], coords_3d[2] + 0.15,
                           f'{idx}', fontsize=10, ha='center',
                           weight='bold' if is_selected else 'normal')
                
                # Store screen coordinates for clicking (approximate)
                # Matplotlib doesn't expose exact projection, so we'll handle in click event
        
        # Draw connections within layers
        for i, layer in enumerate(self.selected_layers):
            color = colors[i % len(colors)]
            points_2d = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1 = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2 = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                               color=color, linewidth=2.5, alpha=0.7)
        
        # Draw inter-layer connections
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            if layer1 in self.selected_layers and layer2 in self.selected_layers:
                if idx1 < len(self.mesh_data.points[layer1]) and \
                   idx2 < len(self.mesh_data.points[layer2]):
                    p1 = self.mesh_data.get_3d_coords(layer1, 
                                                     self.mesh_data.points[layer1][idx1])
                    p2 = self.mesh_data.get_3d_coords(layer2,
                                                     self.mesh_data.points[layer2][idx2])
                    
                    self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                               'gray', linewidth=2, linestyle='--', alpha=0.5)
        
        # Draw hex blocks
        for block in self.hex_blocks:
            verts = block['vertices']
            
            # Edges
            edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7)]
            
            for i, j in edges:
                self.ax.plot([verts[i][0], verts[j][0]],
                           [verts[i][1], verts[j][1]],
                           [verts[i][2], verts[j][2]],
                           'darkgreen', linewidth=3.5, alpha=0.9)
            
            # Faces
            faces = [
                [verts[0], verts[1], verts[2], verts[3]],
                [verts[4], verts[5], verts[6], verts[7]],
                [verts[0], verts[1], verts[5], verts[4]],
                [verts[2], verts[3], verts[7], verts[6]],
                [verts[1], verts[2], verts[6], verts[5]],
                [verts[0], verts[3], verts[7], verts[4]]
            ]
            
            face_collection = Poly3DCollection(faces, alpha=0.2,
                                             facecolor='lightgreen',
                                             edgecolor='green',
                                             linewidths=1)
            self.ax.add_collection3d(face_collection)
        
        # Auto-scale with margin
        if all_coords:
            coords = np.array(all_coords)
            margin_factor = 0.15
            
            for axis, data in zip([self.ax.set_xlim, self.ax.set_ylim, self.ax.set_zlim],
                                 [coords[:,0], coords[:,1], coords[:,2]]):
                range_val = data.max() - data.min()
                margin = max(range_val * margin_factor, 0.5)
                axis([data.min() - margin, data.max() + margin])
        
        # Title
        title = f"3D View: {self.selected_layers[0]} (red) & {self.selected_layers[1]} (blue)"
        self.ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Add control legend
        self.ax.text2D(0.02, 0.98,
                      "Mouse Controls:\n"
                      "• Left-drag: Rotate\n"
                      "• Right-drag: Pan\n"
                      "• Scroll: Zoom\n"
                      "• Click points to select",
                      transform=self.ax.transAxes,
                      fontsize=9, verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='lightyellow',
                              alpha=0.9, edgecolor='black'))
        
        self.ax.view_init(elev=self.elev, azim=self.azim)
        self.canvas.draw()
        
    def reset_view(self):
        """Reset to default view"""
        self.azim = 45
        self.elev = 30
        self.zoom_scale = 1.0
        self.draw()


class TabHexBlockMaking:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Block management
        self.hex_blocks = []
        self.selected_layers = []
        self.selected_points = []
        self.current_block_idx = None
        
        # Division settings
        self.division_mode = tk.StringVar(value="direct")
        self.nx_var = tk.IntVar(value=10)
        self.ny_var = tk.IntVar(value=10)
        self.nz_var = tk.IntVar(value=10)
        self.cell_size_var = tk.DoubleVar(value=1.0)
        
        # Sizing mode
        self.sizing_mode = tk.StringVar(value="3d")
        self.single_div_dir = tk.StringVar(value="Z")
        
        # Grading
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
        
        # Left: 3D View (larger, centered)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Interactive 3D Hex Block Builder",
                font=("Arial", 13, "bold")).pack(pady=5)
        
        # Matplotlib canvas
        self.fig_3d = Figure(figsize=(9, 9), dpi=100)
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create viewer
        self.viewer = Interactive3DViewer(self.fig_3d, self.canvas_3d, self.mesh_data)
        self.viewer.on_point_selected = self.on_point_clicked
        
        # Controls below canvas
        control_frame = tk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(control_frame, text="🔄 Reset View",
                 command=self.reset_view, width=12,
                 bg="lightblue", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="🔁 Refresh",
                 command=self.refresh_view, width=12,
                 bg="lightgreen", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Right: Tabbed controls
        right_frame = tk.Frame(main_frame, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
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
        tk.Radiobutton(div_frame, text="Cell Size (auto-calculate)",
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
        """Show/hide division inputs"""
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
        self.refresh_view()
    
    def reset_view(self):
        """Reset 3D view"""
        if self.viewer:
            self.viewer.reset_view()
    
    def refresh_view(self):
        """Refresh 3D visualization"""
        if self.viewer:
            self.viewer.selected_layers = self.selected_layers
            self.viewer.selected_points = self.selected_points
            self.viewer.hex_blocks = self.hex_blocks
            self.viewer.draw()
    
    def on_layer_select(self, event):
        """Handle layer selection"""
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
        self.refresh_view()
    
    def on_point_clicked(self, point):
        """Handle point click from 3D view"""
        if point in self.selected_points:
            self.selected_points.remove(point)
        else:
            if len(self.selected_points) < 8:
                self.selected_points.append(point)
            else:
                messagebox.showwarning("Limit", "Maximum 8 points")
                return
        self.update_point_list()
        self.refresh_view()
    
    def update_point_list(self):
        """Update point list display"""
        self.point_list.delete(0, tk.END)
        for i, (layer, idx) in enumerate(self.selected_points):
            point_2d = self.mesh_data.points[layer][idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            self.point_list.insert(tk.END,
                f"{i}: {layer}[{idx}] ({coords_3d[0]:.2f},{coords_3d[1]:.2f},{coords_3d[2]:.2f})")
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
    
    def clear_point_selection(self):
        """Clear point selection"""
        self.selected_points = []
        self.update_point_list()
        self.refresh_view()
    
    def create_hex_block(self):
        """Create a hexahedral block from selected points"""
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
        self.refresh_view()
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
            self.refresh_view()
    
    def clear_all_blocks(self):
        """Clear all blocks"""
        if not self.hex_blocks:
            return
        if messagebox.askyesno("Confirm", "Delete all blocks?"):
            self.hex_blocks = []
            self.current_block_idx = None
            self.update_block_list()
            self.refresh_view()
    
    def get_hex_blocks(self):
        """Get all hex blocks"""
        return self.hex_blocks