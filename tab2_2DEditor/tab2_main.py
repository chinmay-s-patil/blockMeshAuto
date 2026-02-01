"""
2D Editor Tab - Points & Connections
UPDATED: Global point numbering and click-to-toggle layer selection
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import math


class Tab2DEditor:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.dual_offset_x = 0
        self.dual_offset_y = 0
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
        self.scale = 50
        self.offset_x = self.canvas_width / 2
        self.offset_y = self.canvas_height / 2
        
        # Pan/zoom state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Canvas widgets
        self.canvas = None
        self.canvas_left = None
        self.canvas_right = None
        
        self.setup_ui()
        
    from tab2_2DEditor.tab2_UI import setup_ui
    
    def setup_canvas_bindings(self, canvas):
        """Setup mouse bindings for a canvas"""
        canvas.bind("<Button-1>", self.on_canvas_click)
        canvas.bind("<Button-3>", self.on_pan_start)
        canvas.bind("<B3-Motion>", self.on_pan_motion)
        canvas.bind("<ButtonRelease-3>", self.on_pan_end)
        canvas.bind("<MouseWheel>", self.on_zoom)
        canvas.bind("<Button-4>", self.on_zoom)
        canvas.bind("<Button-5>", self.on_zoom)
    
    def on_pan_start(self, event):
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def on_pan_motion(self, event):
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            if self.dual_view_mode:
                self.dual_offset_x += dx
                self.dual_offset_y += dy
            else:
                self.offset_x += dx
                self.offset_y += dy
            
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            
            self.update_plot()
    
    def on_pan_end(self, event):
        self.panning = False
    
    def on_zoom(self, event):
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        elif event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            return
        
        canvas = event.widget
        old_world_x = (event.x - self.offset_x) / self.scale
        old_world_y = (self.offset_y - event.y) / self.scale
        
        self.scale *= factor
        
        self.offset_x = event.x - old_world_x * self.scale
        self.offset_y = event.y + old_world_y * self.scale
        
        self.update_plot()
    
    def fit_all_view(self):
        all_x, all_y = [], []
        
        # Collect points from visible layers (dual view or normal)
        if self.dual_view_mode and len(self.dual_view_layers) == 2:
            layers_to_fit = self.dual_view_layers
        else:
            layers_to_fit = list(self.mesh_data.points.keys())
        
        for layer in layers_to_fit:
            for x, y in self.mesh_data.points[layer]:
                all_x.append(x)
                all_y.append(y)
        
        if not all_x or not all_y:
            self.scale = 50
            if self.dual_view_mode:
                self.dual_offset_x = 0
                self.dual_offset_y = 0
            else:
                self.offset_x = (self.canvas.winfo_width() or self.canvas_width) / 2
                self.offset_y = (self.canvas.winfo_height() or self.canvas_height) / 2
            self.update_plot()
            return
        
        buffer = 2.0
        # FIX: Apply buffer to min/max separately (min-2, max+2)
        min_x = min(all_x) - buffer
        max_x = max(all_x) + buffer
        min_y = min(all_y) - buffer
        max_y = max(all_y) + buffer
        
        range_x = max_x - min_x
        range_y = max_y - min_y
        max_range = max(range_x, range_y, 0.1)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        if self.dual_view_mode:
            canvas_w = self.canvas_left.winfo_width() or self.canvas_width // 2
            canvas_h = self.canvas_left.winfo_height() or self.canvas_height
        else:
            if self.canvas:
                canvas_w = self.canvas.winfo_width() or self.canvas_width
                canvas_h = self.canvas.winfo_height() or self.canvas_height
            else:
                canvas_w = self.canvas_width // 2
                canvas_h = self.canvas_height
        
        self.scale = (min(canvas_w, canvas_h) * 0.9) / max_range
        
        if self.dual_view_mode:
            # Dual view: offsets are relative to canvas center
            self.dual_offset_x = -center_x * self.scale
            self.dual_offset_y = center_y * self.scale
        else:
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
        
        # Dual View Mode - UPDATED: Click to toggle instead of checkboxes
        dual_frame = tk.LabelFrame(layer_frame, text="Dual View - Link 2 Layers", padx=10, pady=10)
        dual_frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(dual_frame, text="Enable Dual View (Side-by-Side)", 
                      variable=self.dual_view_var, command=self.toggle_dual_view,
                      font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        tk.Label(dual_frame, text="Click layers below to select (2 max):", 
                font=("Arial", 8)).pack(anchor=tk.W, pady=(5,2))
        
        dual_canvas_frame = tk.Frame(dual_frame, height=100)
        dual_canvas_frame.pack(fill=tk.BOTH)
        dual_canvas_frame.pack_propagate(False)
        
        self.dual_buttons_frame = tk.Frame(dual_canvas_frame)
        self.dual_buttons_frame.pack(fill=tk.BOTH)
        
        self.update_dual_view_buttons()
        
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
            if len(self.dual_view_layers) == 2:
                self.setup_dual_view_canvases()
                self.fit_all_view()  # <-- ADD THIS LINE to set initial dual offsets
                self.dual_label.config(text=f"Dual View Active: {self.dual_view_layers[0]} | {self.dual_view_layers[1]}", fg="green")
            else:
                messagebox.showwarning("Dual View Mode", "Select exactly 2 layers first!")
                self.dual_view_var.set(False)
                self.dual_view_mode = False
        else:
            self.setup_normal_canvas()
            self.dual_label.config(text="Select exactly 2 layers", fg="gray")
    
    def setup_normal_canvas(self):
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
    
    def update_dual_view_buttons(self):
        """UPDATED: Use buttons instead of checkboxes, click to toggle"""
        for widget in self.dual_buttons_frame.winfo_children():
            widget.destroy()
        
        for name in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            is_selected = name in self.dual_view_layers
            
            btn = tk.Button(
                self.dual_buttons_frame,
                text=f"{name} (z={self.mesh_data.layers[name]})",
                bg="lightgreen" if is_selected else "lightgray",
                relief=tk.SUNKEN if is_selected else tk.RAISED,
                font=("Arial", 8, "bold" if is_selected else "normal"),
                command=lambda n=name: self.toggle_layer_in_dual_view(n)
            )
            btn.pack(anchor=tk.W, fill=tk.X, pady=1)
    
    def toggle_layer_in_dual_view(self, layer_name):
        """UPDATED: Click to toggle layer selection"""
        if layer_name in self.dual_view_layers:
            # Deselect
            self.dual_view_layers.remove(layer_name)
        else:
            # Select (limit to 2)
            if len(self.dual_view_layers) >= 2:
                # Remove oldest selection
                self.dual_view_layers.pop(0)
            self.dual_view_layers.append(layer_name)
        
        # Update buttons
        self.update_dual_view_buttons()
        
        # Update label
        if len(self.dual_view_layers) == 2:
            self.dual_label.config(
                text=f"Ready: {self.dual_view_layers[0]} ↔ {self.dual_view_layers[1]}", 
                fg="green"
            )
            if self.dual_view_mode:
                self.setup_dual_view_canvases()
        elif len(self.dual_view_layers) == 1:
            self.dual_label.config(
                text=f"Selected: {self.dual_view_layers[0]} - Select 1 more", 
                fg="orange"
            )
        else:
            self.dual_label.config(text="Select exactly 2 layers", fg="gray")
    
    def world_to_canvas(self, x, y, canvas_widget=None):
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            # Dual view: center-origin + pan offset
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            height = canvas_widget.winfo_height() or self.canvas_height
            cx = (width / 2 + self.dual_offset_x) + x * self.scale
            cy = (height / 2 + self.dual_offset_y) - y * self.scale
        else:
            # Normal mode
            cx = self.offset_x + x * self.scale
            cy = self.offset_y - y * self.scale
        return cx, cy

    def canvas_to_world(self, cx, cy, canvas_widget=None):
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            # Dual view (reverse the center+offset calculation)
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            height = canvas_widget.winfo_height() or self.canvas_height
            x = (cx - (width / 2 + self.dual_offset_x)) / self.scale
            y = ((height / 2 + self.dual_offset_y) - cy) / self.scale
        else:
            # Normal mode
            x = (cx - self.offset_x) / self.scale
            y = (self.offset_y - cy) / self.scale
        return x, y
    
    def on_canvas_click(self, event):
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
                # Convert to global index
                global_idx = self.mesh_data.get_global_point_index(layer, clicked_idx)
                
                if global_idx not in self.selected_points:
                    self.selected_points.append(global_idx)
                    
                    if len(self.selected_points) == 2:
                        # Get layers and local indices
                        layer1, idx1 = self.mesh_data.get_layer_from_global_index(self.selected_points[0])
                        layer2, idx2 = self.mesh_data.get_layer_from_global_index(self.selected_points[1])
                        
                        if layer1 == layer2:
                            self.mesh_data.add_connection(layer1, idx1, idx2)
                        else:
                            self.mesh_data.add_inter_layer_connection(layer1, idx1, layer2, idx2)
                        
                        self.selected_points = []
                    
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
        elif self.mode == "select":
            if clicked_idx is not None:
                global_idx = self.mesh_data.get_global_point_index(layer, clicked_idx)
                if global_idx not in self.selected_points:
                    self.selected_points.append(global_idx)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selection_label.config(text=f"Selected points: {self.selected_points}")
        
        self.update_plot()
    
    def on_dual_click(self, event, canvas_idx):
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
                # Convert to global index
                global_idx = self.mesh_data.get_global_point_index(layer, clicked_idx)
                
                if global_idx not in self.selected_points:
                    self.selected_points.append(global_idx)
                    
                    if len(self.selected_points) == 2:
                        layer1, idx1 = self.mesh_data.get_layer_from_global_index(self.selected_points[0])
                        layer2, idx2 = self.mesh_data.get_layer_from_global_index(self.selected_points[1])
                        
                        if layer1 == layer2:
                            self.mesh_data.add_connection(layer1, idx1, idx2)
                        else:
                            self.mesh_data.add_inter_layer_connection(layer1, idx1, layer2, idx2)
                        
                        self.selected_points = []
                    
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
        elif self.mode == "select":
            if clicked_idx is not None:
                global_idx = self.mesh_data.get_global_point_index(layer, clicked_idx)
                if global_idx not in self.selected_points:
                    self.selected_points.append(global_idx)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selection_label.config(text=f"Selected: {self.selected_points}")
        
        self.update_plot()
    
    def update_plot(self):
        if self.dual_view_mode and len(self.dual_view_layers) == 2:
            self.draw_dual_view()
        else:
            self.draw_normal_mode()
    
    def draw_normal_mode(self):
        if not self.canvas:
            return
        
        self.canvas.delete("all")
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
        
        # Draw points with GLOBAL numbering
        for local_idx, (x, y) in enumerate(points):
            global_idx = self.mesh_data.get_global_point_index(layer, local_idx)
            cx, cy = self.world_to_canvas(x, y, self.canvas)
            
            if global_idx in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "red"
                radius = 5
            
            self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                   fill=color, outline="black")
            # UPDATED: Show global index
            self.canvas.create_text(cx, cy-15, text=str(global_idx), 
                                   font=("Arial", 9, "bold"))
    
    def draw_dual_view(self):
        if not self.canvas_left or not self.canvas_right:
            return
        
        self.canvas_left.delete("all")
        self.canvas_right.delete("all")
        
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
        
        for local_idx, (x, y) in enumerate(points_left):
            global_idx = self.mesh_data.get_global_point_index(layer_left, local_idx)
            cx, cy = self.world_to_canvas(x, y, self.canvas_left)
            
            if global_idx in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "red"
                radius = 5
            
            self.canvas_left.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                        fill=color, outline="black", width=2)
            # UPDATED: Show global index
            self.canvas_left.create_text(cx, cy-15, text=str(global_idx), 
                                        font=("Arial", 9, "bold"))
        
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
        
        for local_idx, (x, y) in enumerate(points_right):
            global_idx = self.mesh_data.get_global_point_index(layer_right, local_idx)
            cx, cy = self.world_to_canvas(x, y, self.canvas_right)
            
            if global_idx in self.selected_points:
                color = "green"
                radius = 8
            else:
                color = "blue"
                radius = 5
            
            self.canvas_right.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                         fill=color, outline="black", width=2)
            # UPDATED: Show global index
            self.canvas_right.create_text(cx, cy-15, text=str(global_idx), 
                                         font=("Arial", 9, "bold"))
    
    def draw_grid(self, canvas):
        width = canvas.winfo_width() or (self.canvas_width if canvas == self.canvas else self.canvas_width // 2)
        height = canvas.winfo_height() or self.canvas_height
        
        for i in range(-20, 21):
            cx, cy = self.world_to_canvas(i, 0, canvas)
            canvas.create_line(cx, 0, cx, height, fill="lightgray", dash=(2, 2))
            
            cx, cy = self.world_to_canvas(0, i, canvas)
            canvas.create_line(0, cy, width, cy, fill="lightgray", dash=(2, 2))
        
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

    from tab2_2DEditor.tab2_layerOps import (update_layer_list, on_layer_select,
                                     add_layer, duplicate_layer, remove_layer,
                                     extrude_layer)
