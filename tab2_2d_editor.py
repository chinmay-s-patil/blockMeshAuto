"""
2D Editor Tab - Points & Connections
Uses tkinter Canvas for direct 2D drawing (no matplotlib/plotly)
Dual View mode shows 2 separate canvases side-by-side
Includes pan/zoom controls
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import math


class Tab2DEditor:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.selected_points = []
        self.selected_connection = None
        self.mode = "select"
        self.dual_view_mode = False
        self.dual_view_layers = []
        self.dual_view_var = tk.BooleanVar(value=False)
        self.dual_view_layer_vars = {}
        
        # Canvas parameters
        self.canvas_width = 700
        self.canvas_height = 700
        self.scale = 50  # pixels per unit
        self.offset_x = self.canvas_width / 2
        self.offset_y = self.canvas_height / 2
        
        # Pan/zoom state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Canvas widgets (initialized in setup)
        self.canvas = None
        self.canvas_left = None
        self.canvas_right = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas area
        self.left_frame = tk.Frame(main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_label = tk.Label(self.left_frame, text="2D View", font=("Arial", 12, "bold"))
        self.canvas_label.pack()
        
        # Container for canvas(es)
        self.canvas_container = tk.Frame(self.left_frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Single canvas (normal mode)
        self.canvas = tk.Canvas(self.canvas_container, bg="white", 
                               width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.setup_canvas_bindings(self.canvas)
        
        # Control buttons at bottom
        button_frame = tk.Frame(self.left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(button_frame, text="🔍 Fit All", command=self.fit_all_view,
                 bg="lightblue", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Label(button_frame, text="Pan: Right-drag | Zoom: Scroll",
                font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=10)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        self._setup_mode_controls(right_frame)
        self._setup_layer_controls(right_frame)
        self._setup_manual_entry(right_frame)
        self._setup_connection_controls(right_frame)
        
        self.update_plot()
    
    def setup_canvas_bindings(self, canvas):
        """Setup mouse bindings for a canvas"""
        canvas.bind("<Button-1>", self.on_canvas_click)
        canvas.bind("<Button-3>", self.on_pan_start)  # Right mouse for pan
        canvas.bind("<B3-Motion>", self.on_pan_motion)
        canvas.bind("<ButtonRelease-3>", self.on_pan_end)
        canvas.bind("<MouseWheel>", self.on_zoom)  # Windows/Mac
        canvas.bind("<Button-4>", self.on_zoom)  # Linux scroll up
        canvas.bind("<Button-5>", self.on_zoom)  # Linux scroll down
    
    def on_pan_start(self, event):
        """Start panning"""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def on_pan_motion(self, event):
        """Pan the view"""
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            self.offset_x += dx
            self.offset_y += dy
            
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            
            self.update_plot()
    
    def on_pan_end(self, event):
        """End panning"""
        self.panning = False
    
    def on_zoom(self, event):
        """Zoom in/out"""
        # Get zoom direction
        if event.num == 4 or event.delta > 0:  # Scroll up
            factor = 1.1
        elif event.num == 5 or event.delta < 0:  # Scroll down
            factor = 0.9
        else:
            return
        
        # Zoom centered on mouse position
        canvas = event.widget
        
        # Get mouse position in world coords before zoom
        old_world_x = (event.x - self.offset_x) / self.scale
        old_world_y = (self.offset_y - event.y) / self.scale
        
        # Apply zoom
        self.scale *= factor
        
        # Adjust offset to keep mouse position fixed
        self.offset_x = event.x - old_world_x * self.scale
        self.offset_y = event.y + old_world_y * self.scale
        
        self.update_plot()
    
    def fit_all_view(self):
        """Fit all points in view with margin"""
        # Collect all points
        all_x, all_y = [], []
        for layer in self.mesh_data.points:
            for x, y in self.mesh_data.points[layer]:
                all_x.append(x)
                all_y.append(y)
        
        if not all_x or not all_y:
            # Reset to default if no points
            self.scale = 50
            self.offset_x = (self.canvas.winfo_width() or self.canvas_width) / 2
            self.offset_y = (self.canvas.winfo_height() or self.canvas_height) / 2
            self.update_plot()
            return
        
        # Calculate bounds
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        # Get the maximum range
        range_x = max_x - min_x
        range_y = max_y - min_y
        max_range = max(range_x, range_y, 0.1)  # Avoid division by zero
        
        # Add buffer (2 units on each side)
        buffer = 2.0
        display_range = max_range + 2 * buffer
        
        # Get actual canvas size
        if self.canvas:
            canvas_w = self.canvas.winfo_width() or self.canvas_width
            canvas_h = self.canvas.winfo_height() or self.canvas_height
        else:
            canvas_w = self.canvas_width // 2
            canvas_h = self.canvas_height
        
        # Calculate scale to fit (use 90% of canvas to leave some margin)
        self.scale = (min(canvas_w, canvas_h) * 0.9) / display_range
        
        # Center the view on the data center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        self.offset_x = canvas_w / 2 - center_x * self.scale
        self.offset_y = canvas_h / 2 + center_y * self.scale
        
        self.update_plot()
        
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
        
        # Dual View Mode
        dual_frame = tk.LabelFrame(layer_frame, text="Dual View - Link 2 Layers", padx=10, pady=10)
        dual_frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(dual_frame, text="Enable Dual View (Side-by-Side)", 
                      variable=self.dual_view_var, command=self.toggle_dual_view,
                      font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        tk.Label(dual_frame, text="Select exactly 2 layers:", font=("Arial", 8)).pack(anchor=tk.W, pady=(5,2))
        
        dual_canvas_frame = tk.Frame(dual_frame, height=100)
        dual_canvas_frame.pack(fill=tk.BOTH)
        dual_canvas_frame.pack_propagate(False)
        
        self.dual_checkboxes_frame = tk.Frame(dual_canvas_frame)
        self.dual_checkboxes_frame.pack(fill=tk.BOTH)
        
        self.update_dual_view_checkboxes()
        
        self.dual_label = tk.Label(dual_frame, text="Select exactly 2 layers", 
                                 font=("Arial", 8, "italic"), fg="gray")
        self.dual_label.pack(pady=2)
        
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
            self.mode_label.config(text="Current Mode: Connect (select 2 points)", fg="orange")
        elif mode == "delete":
            self.delete_btn.config(relief=tk.SUNKEN, bg="salmon")
            self.mode_label.config(text="Current Mode: Delete", fg="red")
    
    def toggle_dual_view(self):
        self.dual_view_mode = self.dual_view_var.get()
        
        if self.dual_view_mode:
            self.update_dual_view_layers_from_checkboxes()
            if len(self.dual_view_layers) == 2:
                self.setup_dual_view_canvases()
                self.dual_label.config(text=f"Dual View Active: {self.dual_view_layers[0]} | {self.dual_view_layers[1]}", fg="green")
            else:
                messagebox.showwarning("Dual View Mode", "Select exactly 2 layers first!")
                self.dual_view_var.set(False)
                self.dual_view_mode = False
        else:
            self.setup_normal_canvas()
            self.dual_label.config(text="Select exactly 2 layers", fg="gray")
            self.dual_view_layers = []
    
    def setup_normal_canvas(self):
        """Setup single canvas for normal mode"""
        for widget in self.canvas_container.winfo_children():
            widget.destroy()
        
        self.canvas_label.config(text="2D View")
        
        self.canvas = tk.Canvas(self.canvas_container, bg="white",
                               width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.setup_canvas_bindings(self.canvas)
        
        self.canvas_left = None
        self.canvas_right = None
        self.update_plot()
    
    def setup_dual_view_canvases(self):
        """Setup two side-by-side canvases for dual view mode"""
        for widget in self.canvas_container.winfo_children():
            widget.destroy()
        
        self.canvas_label.config(text=f"Dual View: {self.dual_view_layers[0]} (Left) | {self.dual_view_layers[1]} (Right)")
        
        # Left canvas
        left_frame = tk.Frame(self.canvas_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        tk.Label(left_frame, text=f"{self.dual_view_layers[0]} (Red)", 
                font=("Arial", 10, "bold"), fg="red").pack()
        
        self.canvas_left = tk.Canvas(left_frame, bg="white",
                                     width=self.canvas_width//2, height=self.canvas_height)
        self.canvas_left.pack(fill=tk.BOTH, expand=True)
        self.canvas_left.bind("<Button-1>", lambda e: self.on_dual_click(e, 0))
        self.setup_canvas_bindings(self.canvas_left)
        
        # Right canvas
        right_frame = tk.Frame(self.canvas_container)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        tk.Label(right_frame, text=f"{self.dual_view_layers[1]} (Blue)", 
                font=("Arial", 10, "bold"), fg="blue").pack()
        
        self.canvas_right = tk.Canvas(right_frame, bg="white",
                                      width=self.canvas_width//2, height=self.canvas_height)
        self.canvas_right.pack(fill=tk.BOTH, expand=True)
        self.canvas_right.bind("<Button-1>", lambda e: self.on_dual_click(e, 1))
        self.setup_canvas_bindings(self.canvas_right)
        
        self.canvas = None
        self.update_plot()
    
    def update_dual_view_checkboxes(self):
        for widget in self.dual_checkboxes_frame.winfo_children():
            widget.destroy()
        
        self.dual_view_layer_vars = {}
        
        for name in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            var = tk.BooleanVar(value=False)
            self.dual_view_layer_vars[name] = var
            cb = tk.Checkbutton(self.dual_checkboxes_frame, text=f"{name} (z={self.mesh_data.layers[name]})", 
                              variable=var, command=self.update_dual_view_layers_from_checkboxes)
            cb.pack(anchor=tk.W)
    
    def update_dual_view_layers_from_checkboxes(self):
        self.dual_view_layers = [name for name, var in self.dual_view_layer_vars.items() if var.get()]
        
        if len(self.dual_view_layers) > 2:
            oldest = self.dual_view_layers[0]
            self.dual_view_layer_vars[oldest].set(False)
            self.dual_view_layers = [name for name, var in self.dual_view_layer_vars.items() if var.get()]
        
        if len(self.dual_view_layers) == 2:
            self.dual_label.config(text=f"Ready: {self.dual_view_layers[0]} ↔ {self.dual_view_layers[1]}", fg="green")
            if self.dual_view_mode:
                self.setup_dual_view_canvases()
        elif len(self.dual_view_layers) == 1:
            self.dual_label.config(text=f"Selected: {self.dual_view_layers[0]} - Select 1 more", fg="orange")
        else:
            self.dual_label.config(text="Select exactly 2 layers", fg="gray")
    
    def world_to_canvas(self, x, y, canvas_widget=None):
        """Convert world coordinates to canvas coordinates"""
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            cx = width / 2 + x * self.scale
        else:
            cx = self.offset_x + x * self.scale
        cy = self.offset_y - y * self.scale
        return cx, cy
    
    def canvas_to_world(self, cx, cy, canvas_widget=None):
        """Convert canvas coordinates to world coordinates"""
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            x = (cx - width / 2) / self.scale
        else:
            x = (cx - self.offset_x) / self.scale
        y = (self.offset_y - cy) / self.scale
        return x, y
    
    def on_canvas_click(self, event):
        """Handle click on single canvas (normal mode)"""
        if self.dual_view_mode or self.panning:
            return
        
        x, y = self.canvas_to_world(event.x, event.y, self.canvas)
        layer = self.mesh_data.current_layer
        points = self.mesh_data.points[layer]
        
        # Find clicked point
        clicked_idx = None
        for idx, (px, py) in enumerate(points):
            dist = math.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.3:
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
                self.selection_label.config(text=f"Selected points: {self.selected_points}")
        
        self.update_plot()
    
    def on_dual_click(self, event, canvas_idx):
        """Handle click on dual view canvases"""
        if not self.dual_view_mode or len(self.dual_view_layers) != 2 or self.panning:
            return
        
        canvas_widget = self.canvas_left if canvas_idx == 0 else self.canvas_right
        layer = self.dual_view_layers[canvas_idx]
        
        x, y = self.canvas_to_world(event.x, event.y, canvas_widget)
        points = self.mesh_data.points[layer]
        
        # Find clicked point
        clicked_idx = None
        for idx, (px, py) in enumerate(points):
            dist = math.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.3:
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
                point_ref = (layer, clicked_idx)
                if point_ref not in self.selected_points:
                    self.selected_points.append(point_ref)
                    
                    # If 2 points from different layers, create inter-layer connection
                    if len(self.selected_points) == 2:
                        layer1, idx1 = self.selected_points[0]
                        layer2, idx2 = self.selected_points[1]
                        
                        if layer1 != layer2:
                            self.mesh_data.add_inter_layer_connection(layer1, idx1, layer2, idx2)
                        else:
                            self.mesh_data.add_connection(layer1, idx1, idx2)
                        
                        self.selected_points = []
                    
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
        elif self.mode == "select":
            if clicked_idx is not None:
                point_ref = (layer, clicked_idx)
                if point_ref not in self.selected_points:
                    self.selected_points.append(point_ref)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selection_label.config(text=f"Selected: {self.selected_points}")
        
        self.update_plot()
    
    def update_plot(self):
        """Redraw the canvas(es)"""
        if self.dual_view_mode and len(self.dual_view_layers) == 2:
            self.draw_dual_view()
        else:
            self.draw_normal_mode()
    
    def draw_normal_mode(self):
        """Draw single layer on one canvas"""
        if not self.canvas:
            return
        
        self.canvas.delete("all")
        
        # Draw grid
        self.draw_grid(self.canvas)
        
        layer = self.mesh_data.current_layer
        points = self.mesh_data.points[layer]
        
        # Draw connections
        for conn in self.mesh_data.connections[layer]:
            if conn[0] < len(points) and conn[1] < len(points):
                p1 = points[conn[0]]
                p2 = points[conn[1]]
                cx1, cy1 = self.world_to_canvas(p1[0], p1[1], self.canvas)
                cx2, cy2 = self.world_to_canvas(p2[0], p2[1], self.canvas)
                self.canvas.create_line(cx1, cy1, cx2, cy2, fill="blue", width=2)
        
        # Draw points
        for idx, (x, y) in enumerate(points):
            cx, cy = self.world_to_canvas(x, y, self.canvas)
            
            if isinstance(self.selected_points[0] if self.selected_points else None, int) and idx in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "red"
                radius = 5
            
            self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                   fill=color, outline="black")
            self.canvas.create_text(cx, cy-15, text=str(idx), font=("Arial", 9, "bold"))
    
    def draw_dual_view(self):
        """Draw two layers on separate canvases"""
        if not self.canvas_left or not self.canvas_right:
            return
        
        self.canvas_left.delete("all")
        self.canvas_right.delete("all")
        
        # Draw grids
        self.draw_grid(self.canvas_left)
        self.draw_grid(self.canvas_right)
        
        # Draw left layer (red)
        layer_left = self.dual_view_layers[0]
        points_left = self.mesh_data.points[layer_left]
        
        for conn in self.mesh_data.connections[layer_left]:
            if conn[0] < len(points_left) and conn[1] < len(points_left):
                p1 = points_left[conn[0]]
                p2 = points_left[conn[1]]
                cx1, cy1 = self.world_to_canvas(p1[0], p1[1], self.canvas_left)
                cx2, cy2 = self.world_to_canvas(p2[0], p2[1], self.canvas_left)
                self.canvas_left.create_line(cx1, cy1, cx2, cy2, fill="red", width=2)
        
        for idx, (x, y) in enumerate(points_left):
            cx, cy = self.world_to_canvas(x, y, self.canvas_left)
            
            if (layer_left, idx) in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "red"
                radius = 5
            
            self.canvas_left.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                        fill=color, outline="black", width=2)
            self.canvas_left.create_text(cx, cy-15, text=str(idx), font=("Arial", 9, "bold"))
        
        # Draw right layer (blue)
        layer_right = self.dual_view_layers[1]
        points_right = self.mesh_data.points[layer_right]
        
        for conn in self.mesh_data.connections[layer_right]:
            if conn[0] < len(points_right) and conn[1] < len(points_right):
                p1 = points_right[conn[0]]
                p2 = points_right[conn[1]]
                cx1, cy1 = self.world_to_canvas(p1[0], p1[1], self.canvas_right)
                cx2, cy2 = self.world_to_canvas(p2[0], p2[1], self.canvas_right)
                self.canvas_right.create_line(cx1, cy1, cx2, cy2, fill="blue", width=2)
        
        for idx, (x, y) in enumerate(points_right):
            cx, cy = self.world_to_canvas(x, y, self.canvas_right)
            
            if (layer_right, idx) in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "blue"
                radius = 5
            
            self.canvas_right.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                         fill=color, outline="black", width=2)
            self.canvas_right.create_text(cx, cy-15, text=str(idx), font=("Arial", 9, "bold"))
    
    def draw_grid(self, canvas):
        """Draw grid on canvas"""
        width = canvas.winfo_width() or (self.canvas_width if canvas == self.canvas else self.canvas_width // 2)
        height = canvas.winfo_height() or self.canvas_height
        
        # Draw grid lines every 1 unit
        for i in range(-20, 21):
            cx, cy = self.world_to_canvas(i, 0, canvas)
            canvas.create_line(cx, 0, cx, height, fill="lightgray", dash=(2, 2))
            
            cx, cy = self.world_to_canvas(0, i, canvas)
            canvas.create_line(0, cy, width, cy, fill="lightgray", dash=(2, 2))
        
        # Draw axes
        cx, cy = self.world_to_canvas(0, 0, canvas)
        canvas.create_line(0, cy, width, cy, fill="black", width=2)
        canvas.create_line(cx, 0, cx, height, fill="black", width=2)
    
    def add_point_manual(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            self.mesh_data.add_point(self.mesh_data.current_layer, x, y)
            self.update_plot()
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
        self.update_dual_view_checkboxes()
        messagebox.showinfo("Success", f"Layer extruded: {name}\n{num_points} inter-layer connections created")
    
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
            self.update_dual_view_checkboxes()
    
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
            self.update_dual_view_checkboxes()
            messagebox.showinfo("Success", f"Layer duplicated: {name}")
    
    def remove_layer(self):
        if len(self.mesh_data.layers) <= 1:
            messagebox.showwarning("Warning", "Cannot remove last layer")
            return
        
        self.mesh_data.remove_layer(self.mesh_data.current_layer)
        self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
        self.update_layer_list()
        self.update_dual_view_checkboxes()
        self.update_plot()