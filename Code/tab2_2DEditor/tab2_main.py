
"""
2D Editor Tab - Points & Connections
UPDATED for new data structure: Uses global point IDs instead of layer-based point lists
Features: Select mode toggle, Point ID recycling, Two add point modes, Position indicator
FIXED: Point copying in duplicate/extrude now properly copies X,Y coordinates
FIXED: Remove layer now deletes points on that layer
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import math
from tab2_2DEditor.DualViewConnectionHandler import DualViewConnectionHandler

import re


class Tab2DEditor:
    """2D Editor using new global point ID system"""

    # Import methods from other modules
    from tab2_2DEditor.tab2_layerOps import (update_layer_list, on_layer_select,
                                 add_layer, duplicate_layer, remove_layer,
                                 extrude_layer, edit_layer_z)
    from tab2_2DEditor.tab2_pointOps import (edit_point, add_point_manual, 
                                    delete_selected_point, clear_selection)

    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data

        # Canvas parameters
        self.canvas_width = 700
        self.canvas_height = 700
        self.scale = 50
        self.offset_x = self.canvas_width / 2
        self.offset_y = self.canvas_height / 2

        # Dual view offsets
        self.dual_offset_x = 0
        self.dual_offset_y = 0

        # Selection state - stores point IDs
        self.selected_points = []
        self.selected_connection = None

        # Mode
        self.mode = "select"

        # Add point mode: "click" or "snap"
        self.add_point_mode = "click"
        self.snap_grid_size = 1.0  # Grid size for snap mode

        # Dual view state
        self.dual_view_mode = False
        self.dual_view_layers = []
        self.dual_view_var = tk.BooleanVar(value=False)

        # Canvas widgets
        self.canvas = None
        self.canvas_left = None
        self.canvas_right = None

        # Position indicator label
        self.position_label = None

        # Pan/zoom state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0

        # Lasso selection state
        self.lasso_start_x = 0
        self.lasso_start_y = 0
        self.lasso_rect = None

        # Dark mode colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f44747',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'button_active': '#1177bb',
            'border': '#3e3e42',
            'canvas_bg': '#1e1e1e',
            'grid': '#3e3e42',
            'axis': '#6e6e6e',
            'select_bg': '#0e639c',
            'add_bg': '#4ec9b0',
            'connect_bg': '#ce9178',
            'delete_bg': '#f44747'
        }

        # Dual view connection handler
        self.dual_handler = DualViewConnectionHandler(self)

        # Setup UI
        from tab2_2DEditor.tab2_UI import setup_ui
        setup_ui(self)

    def setup_canvas_bindings(self, canvas):
        """Setup mouse bindings for a canvas"""
        # Right click bindings
        canvas.bind("<Button-3>", self.on_pan_start)
        canvas.bind("<B3-Motion>", self.on_pan_motion)
        canvas.bind("<ButtonRelease-3>", self.on_pan_end)

        # Lasso left click bindings
        canvas.bind("<B1-Motion>", self.on_lasso_drag)
        canvas.bind("<ButtonRelease-1>", self.on_lasso_end)

        # Zoom bindings
        canvas.bind("<MouseWheel>", self.on_zoom)
        canvas.bind("<Button-4>", self.on_zoom)
        canvas.bind("<Button-5>", self.on_zoom)

        # Add mouse motion binding for position indicator
        canvas.bind("<Motion>", self.on_canvas_motion)

    def on_canvas_motion(self, event):
        """Update position indicator on mouse move"""
        if self.dual_view_mode:
            # Determine which canvas the mouse is over
            widget = event.widget
            if widget == self.canvas_left:
                x, y = self.canvas_to_world(event.x, event.y, self.canvas_left)
                layer_name = self.dual_view_layers[0] if len(self.dual_view_layers) > 0 else ""
            elif widget == self.canvas_right:
                x, y = self.canvas_to_world(event.x, event.y, self.canvas_right)
                layer_name = self.dual_view_layers[1] if len(self.dual_view_layers) > 1 else ""
            else:
                return
        else:
            x, y = self.canvas_to_world(event.x, event.y, self.canvas)
            layer_name = self.mesh_data.current_layer

        # Update position label with matplotlib-like format
        if self.position_label:
            z = self.mesh_data.layers.get(layer_name, {}).get('z', 0.0) if layer_name else 0.0
            self.position_label.config(text=f"x={x:.2f}, y={y:.2f}, z={z:.2f} | {layer_name}")

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
        """Fit view to show all points"""
        all_x, all_y = [], []

        # Collect points from visible layers
        if self.dual_view_mode and len(self.dual_view_layers) == 2:
            layers_to_fit = self.dual_view_layers
        else:
            layers_to_fit = list(self.mesh_data.layers.keys())

        for layer_name in layers_to_fit:
            layer_data = self.mesh_data.layers.get(layer_name, {})
            for point_id in layer_data.get('point_refs', []):
                point_data = self.mesh_data.get_point(point_id)
                if point_data:
                    all_x.append(point_data['x'])
                    all_y.append(point_data['y'])

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
            self.dual_offset_x = -center_x * self.scale
            self.dual_offset_y = center_y * self.scale
        else:
            self.offset_x = canvas_w / 2 - center_x * self.scale
            self.offset_y = canvas_h / 2 + center_y * self.scale

        self.update_plot()

    def _setup_mode_controls(self, parent):
        """Setup mode control buttons"""
        mode_frame = tk.LabelFrame(parent, text="Mode", padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'])
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        self.select_btn = tk.Button(mode_frame, text="Select", 
                                     command=lambda: self.set_mode("select"), 
                                     relief=tk.SUNKEN, bg=self.colors['select_bg'],
                                     fg=self.colors['button_fg'], font=("Arial", 9, "bold"),
                                     activebackground=self.colors['button_active'],
                                     activeforeground=self.colors['button_fg'])
        self.select_btn.pack(fill=tk.X, pady=2)

        self.add_btn = tk.Button(mode_frame, text="Add Points", 
                                 command=lambda: self.set_mode("add"),
                                 bg=self.colors['secondary'], fg=self.colors['fg'],
                                 activebackground=self.colors['add_bg'],
                                 activeforeground=self.colors['button_fg'])
        self.add_btn.pack(fill=tk.X, pady=2)

        self.connect_btn = tk.Button(mode_frame, text="Connect", 
                                     command=lambda: self.set_mode("connect"),
                                     bg=self.colors['secondary'], fg=self.colors['fg'],
                                     activebackground=self.colors['connect_bg'],
                                     activeforeground=self.colors['button_fg'])
        self.connect_btn.pack(fill=tk.X, pady=2)

        self.delete_btn = tk.Button(mode_frame, text="Delete Points", 
                                    command=lambda: self.set_mode("delete"),
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    activebackground=self.colors['delete_bg'],
                                    activeforeground=self.colors['button_fg'])
        self.delete_btn.pack(fill=tk.X, pady=2)

        self.mode_label = tk.Label(mode_frame, text="Current Mode: Select", 
                                   font=("Arial", 10, "bold"), fg=self.colors['accent'],
                                   bg=self.colors['secondary'])
        self.mode_label.pack(pady=5)

    def _setup_add_point_controls(self, parent):
        """Setup add point mode controls (click vs snap)"""
        add_frame = tk.LabelFrame(parent, text="Add Point Mode", padx=10, pady=10,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'],
                                  highlightcolor=self.colors['accent'])
        add_frame.pack(fill=tk.X, padx=5, pady=5)

        # Mode variable
        self.add_mode_var = tk.StringVar(value="click")

        # Click mode radio button
        tk.Radiobutton(add_frame, text="Click-to-Add (Free)", 
                      variable=self.add_mode_var, value="click",
                      command=lambda: self.set_add_point_mode("click"),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'], font=("Arial", 9),
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W, pady=2)

        # Snap mode radio button
        snap_frame = tk.Frame(add_frame, bg=self.colors['secondary'])
        snap_frame.pack(fill=tk.X, pady=2)

        tk.Radiobutton(snap_frame, text="Snap-to-Grid", 
                      variable=self.add_mode_var, value="snap",
                      command=lambda: self.set_add_point_mode("snap"),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'], font=("Arial", 9),
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(side=tk.LEFT)

        # Grid size entry
        tk.Label(snap_frame, text="Grid:", bg=self.colors['secondary'], 
                fg=self.colors['fg'], font=("Arial", 8)).pack(side=tk.LEFT, padx=(10, 2))

        self.grid_size_var = tk.DoubleVar(value=self.snap_grid_size)
        grid_entry = tk.Entry(snap_frame, textvariable=self.grid_size_var, width=6,
                             bg=self.colors['bg'], fg=self.colors['fg'],
                             insertbackground=self.colors['fg'], font=("Arial", 9))
        grid_entry.pack(side=tk.LEFT)

        def update_grid_size(*args):
            try:
                self.snap_grid_size = self.grid_size_var.get()
                if self.mode == "add" and self.add_point_mode == "snap":
                    self.update_plot()
            except:
                pass

        self.grid_size_var.trace_add("write", update_grid_size)

        # Help text
        tk.Label(add_frame, text="Snap mode shows grid and snaps clicks to grid",
                bg=self.colors['secondary'], fg=self.colors['axis'], 
                font=("Arial", 8, "italic")).pack(anchor=tk.W, pady=(5, 0))

    def _suggest_layer_name(self):
        """Suggest a layer name: 'Layer 1' if empty, or 'Layer n+1' if last ends with int n."""
        if not self.mesh_data.layers:
            return "Layer 1"
        last_name = list(self.mesh_data.layers.keys())[-1]
        match = re.search(r'(\d+)\s*$', last_name)
        if match:
            n = int(match.group(1))
            prefix = last_name[:match.start(1)]
            return f"{prefix}{n + 1}"
        return f"Layer {len(self.mesh_data.layers) + 1}"

    def add_layer(self):
        """Add a new empty layer with Z-value input"""
        # Save undo state
        self.mesh_data.save_state()

        suggested = self._suggest_layer_name()
        layer_name = simpledialog.askstring("Add Layer", "Enter new layer name:",
                                            initialvalue=suggested,
                                            parent=self.parent)
        if not layer_name:
            return

        layer_name = layer_name.strip()
        if layer_name in self.mesh_data.layers:
            messagebox.showerror("Error", f"Layer '{layer_name}' already exists.")
            return

        # Ask for Z value
        z_value_str = simpledialog.askstring("Layer Z-Value", 
                                            f"Enter Z-value for layer '{layer_name}':",
                                            initialvalue="0.0",
                                            parent=self.parent)
        if z_value_str is None:
            return

        try:
            z_value = float(z_value_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid Z-value. Please enter a number.")
            return

        self.mesh_data.add_layer(layer_name, z_value)
        self.mesh_data.current_layer = layer_name
        self.update_layer_list()
        self.update_dual_view_buttons()
        self.update_plot()





    def remove_layer(self):
        """Remove the currently selected layer and delete all points on it"""
        # Save undo state
        self.mesh_data.save_state()

        selected_index = self.layer_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "No layer selected to remove.")
            return

        layer_name = self.layer_listbox.get(selected_index[0]).split(" (z=")[0]

        # Get the points that will be deleted
        layer_data = self.mesh_data.layers.get(layer_name, {})
        points_to_delete = layer_data.get('point_refs', [])

        # If current layer is being deleted, switch to another layer first
        if layer_name == self.mesh_data.current_layer and len(self.mesh_data.layers) > 1:
            other_layers = [name for name in self.mesh_data.layers if name != layer_name]
            if other_layers:
                self.mesh_data.current_layer = other_layers[0]

        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete layer '{layer_name}'?\n"
                              f"This will permanently delete {len(points_to_delete)} points on this layer."):

            # FIXED: Actually delete the points on this layer, not just dereference them
            for point_id in points_to_delete:
                self.mesh_data.remove_point(point_id)

            # Now remove the layer itself
            self.mesh_data.remove_layer(layer_name)

            self.update_layer_list()
            self.update_dual_view_buttons()
            self.update_plot()
            self.clear_selection()
            messagebox.showinfo("Deleted", f"Layer '{layer_name}' and {len(points_to_delete)} points deleted.")

    def edit_layer_z(self):
        """Edit the Z-value of the currently selected layer"""
        # Save undo state
        self.mesh_data.save_state()

        selected_index = self.layer_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "No layer selected to edit Z-value.")
            return

        layer_name = self.layer_listbox.get(selected_index[0]).split(" (z=")[0]
        current_z = self.mesh_data.layers[layer_name].get('z', 0.0)

        new_z_str = simpledialog.askstring("Edit Layer Z-value", 
                                          f"Enter new Z-value for layer '{layer_name}' (current: {current_z}):",
                                          initialvalue=str(current_z), 
                                          parent=self.parent)
        if new_z_str:
            try:
                new_z = float(new_z_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid Z-value. Please enter a number.")
                return

            self.mesh_data.set_layer_z(layer_name, new_z)
            self.update_layer_list()
            self.update_plot()

    def refresh_layers(self):
        """Refresh the layer list from mesh_data"""
        self.update_layer_list()
        self.update_dual_view_buttons()
        self.update_plot()
        messagebox.showinfo("Refreshed", "Layer list refreshed from current data")

    def _setup_layer_controls(self, parent):
        """Setup layer controls"""
        layer_frame = tk.LabelFrame(parent, text="Layers (sorted by name)", padx=10, pady=10,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightcolor=self.colors['accent'])
        layer_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Refresh button at top
        refresh_btn = tk.Button(layer_frame, text="🔄 Refresh", command=self.refresh_layers,
                               bg=self.colors['accent'], fg=self.colors['button_fg'],
                               activebackground=self.colors['button_active'],
                               activeforeground=self.colors['button_fg'],
                               font=("Arial", 9, "bold"))
        refresh_btn.pack(fill=tk.X, pady=(0, 5))

        self.layer_listbox = tk.Listbox(layer_frame, height=6, selectmode=tk.SINGLE,
                                        bg=self.colors['bg'], fg=self.colors['fg'],
                                        selectbackground=self.colors['accent'],
                                        selectforeground=self.colors['button_fg'],
                                        highlightbackground=self.colors['border'],
                                        font=("Arial", 9))
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        self.update_layer_list()

        layer_btn_frame = tk.Frame(layer_frame, bg=self.colors['secondary'])
        layer_btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(layer_btn_frame, text="Add", command=self.add_layer, width=5,
                  bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_fg']).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Duplicate", command=self.duplicate_layer, width=7,
                  bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_fg']).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Extrude", command=self.extrude_layer, width=6,
                  bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_fg']).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Remove", command=self.remove_layer, width=6,
                  bg=self.colors['error'], fg=self.colors['button_fg'],
                  activebackground='#d63636',
                  activeforeground=self.colors['button_fg']).pack(side=tk.LEFT, padx=1)

        layer_btn_frame2 = tk.Frame(layer_frame, bg=self.colors['secondary'])
        layer_btn_frame2.pack(fill=tk.X, pady=(5, 0))
        tk.Button(layer_btn_frame2, text="Edit Z", command=self.edit_layer_z, width=6,
                  bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_fg']).pack(side=tk.LEFT, padx=1)

        self.layer_info = tk.Label(layer_frame, text=f"Current: {self.mesh_data.current_layer}", 
                                   font=("Arial", 9, "bold"), fg=self.colors['success'],
                                   bg=self.colors['secondary'])
        self.layer_info.pack(pady=5)

        # Dual View Mode
        dual_frame = tk.LabelFrame(layer_frame, text="Dual View - Link 2 Layers", 
                                   padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'])
        dual_frame.pack(fill=tk.X, pady=5)

        tk.Checkbutton(dual_frame, text="Enable Dual View (Side-by-Side)", 
                      variable=self.dual_view_var, command=self.toggle_dual_view,
                      font=("Arial", 9, "bold"), bg=self.colors['secondary'],
                      fg=self.colors['fg'], selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)

        tk.Label(dual_frame, text="Click layers below to select (2 max):", 
                font=("Arial", 8), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(5,2))

        dual_canvas_frame = tk.Frame(dual_frame, height=100, bg=self.colors['secondary'])
        dual_canvas_frame.pack(fill=tk.BOTH)
        dual_canvas_frame.pack_propagate(False)

        self.dual_buttons_frame = tk.Frame(dual_canvas_frame, bg=self.colors['secondary'])
        self.dual_buttons_frame.pack(fill=tk.BOTH)

        self.update_dual_view_buttons()

        self.dual_label = tk.Label(dual_frame, text="Select exactly 2 layers", 
                                 font=("Arial", 8, "italic"), fg=self.colors['axis'],
                                 bg=self.colors['secondary'])
        self.dual_label.pack(pady=2)

    def _setup_manual_entry(self, parent):
        """Setup manual point entry controls - Edit button moved to top"""
        manual_frame = tk.LabelFrame(parent, text="Point Controls", padx=10, pady=10,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightcolor=self.colors['accent'])
        manual_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add Point row - uniform button width
        add_frame = tk.Frame(manual_frame, bg=self.colors['secondary'])
        add_frame.pack(fill=tk.X, pady=2)

        tk.Label(add_frame, text="X:", bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(side=tk.LEFT)
        self.x_entry = tk.Entry(add_frame, width=8, bg=self.colors['bg'],
                            fg=self.colors['fg'], insertbackground=self.colors['fg'],
                            highlightbackground=self.colors['border'])
        self.x_entry.pack(side=tk.LEFT, padx=2)
        self.x_entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
        self.x_entry.bind("<Button-1>", lambda e: e.widget.select_range(0, tk.END))

        tk.Label(add_frame, text="Y:", bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(side=tk.LEFT)
        self.y_entry = tk.Entry(add_frame, width=8, bg=self.colors['bg'],
                            fg=self.colors['fg'], insertbackground=self.colors['fg'],
                            highlightbackground=self.colors['border'])
        self.y_entry.pack(side=tk.LEFT, padx=2)
        self.y_entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
        self.y_entry.bind("<Button-1>", lambda e: e.widget.select_range(0, tk.END))

        # Uniform button size for Add button
        tk.Button(add_frame, text="Add", command=self.add_point_manual,
                bg=self.colors['success'], fg=self.colors['bg'],
                activebackground='#3db89f',
                activeforeground=self.colors['bg'],
                font=("Arial", 8, "bold"), width=6).pack(side=tk.LEFT, padx=2)

    def _setup_edit_point_button(self, parent):
        """Setup Edit Selected Point button - placed right after Add Point controls"""
        edit_frame = tk.Frame(parent, bg=self.colors['secondary'])
        edit_frame.pack(fill=tk.X, padx=5, pady=5)

        # Edit Selected Point button - full width like other buttons
        tk.Button(edit_frame, text="✎ Edit Selected Point", command=self.edit_point,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 font=("Arial", 10, "bold"), relief=tk.FLAT,
                 width=25).pack(fill=tk.X)

    def _setup_connection_controls(self, parent):
        """Setup connection controls"""
        conn_frame = tk.LabelFrame(parent, text="Connection Tools", padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'])
        conn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.selection_label = tk.Label(conn_frame, text="Selected: None", 
                                       fg=self.colors['success'],
                                       bg=self.colors['secondary'],
                                       font=("Arial", 9, "bold"))
        self.selection_label.pack(pady=5)

        tk.Button(conn_frame, text="Delete Connection", 
                 command=self.delete_connection, bg=self.colors['error'],
                 fg=self.colors['button_fg'], activebackground='#d63636',
                 activeforeground=self.colors['button_fg']).pack(fill=tk.X, pady=2)
        tk.Button(conn_frame, text="Clear Selection", 
                 command=self.clear_selection, bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'], activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_fg']).pack(fill=tk.X, pady=2)

        # Dual View Connection Section
        dual_conn_frame = tk.LabelFrame(conn_frame, text="Dual View Connections", 
                                  padx=10, pady=10,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'])
        dual_conn_frame.pack(fill=tk.X, pady=10)

        tk.Label(dual_conn_frame, text="Connect points between layers:", 
                font=("Arial", 9), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))

        self.dual_selection_label = tk.Label(dual_conn_frame, 
                                             text="Left: None | Right: None",
                                             font=("Arial", 9, "bold"),
                                             fg=self.colors['warning'],
                                             bg=self.colors['secondary'])
        self.dual_selection_label.pack(pady=5)

        btn_frame = tk.Frame(dual_conn_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=5)

        self.dual_connect_button = tk.Button(btn_frame, text="Make Connection", 
                                             command=self.dual_handler.create_dual_connection,
                                             bg=self.colors['button_bg'],
                                             fg=self.colors['button_fg'],
                                             font=("Arial", 10, "bold"),
                                             state=tk.DISABLED)
        self.dual_connect_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(btn_frame, text="Clear", 
                 command=self.dual_handler.clear_dual_selection,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, padx=2)

        tk.Label(dual_conn_frame, 
                text="Click one point on left canvas,\nthen one point on right canvas",
                font=("Arial", 8, "italic"), fg=self.colors['fg'],
                bg=self.colors['secondary']).pack(pady=(5, 0))

    def set_mode(self, mode):
        """Set the current interaction mode"""
        self.mode = mode

        # Reset all buttons
        self.select_btn.config(relief=tk.RAISED, bg=self.colors['secondary'], fg=self.colors['fg'])
        self.add_btn.config(relief=tk.RAISED, bg=self.colors['secondary'], fg=self.colors['fg'])
        self.connect_btn.config(relief=tk.RAISED, bg=self.colors['secondary'], fg=self.colors['fg'])
        self.delete_btn.config(relief=tk.RAISED, bg=self.colors['secondary'], fg=self.colors['fg'])

        # Highlight active button
        if mode == "select":
            self.select_btn.config(relief=tk.SUNKEN, bg=self.colors['select_bg'], fg=self.colors['button_fg'])
            self.mode_label.config(text="Current Mode: Select", fg=self.colors['accent'])
        elif mode == "add":
            self.add_btn.config(relief=tk.SUNKEN, bg=self.colors['add_bg'], fg=self.colors['button_fg'])
            mode_text = f"Add ({self.add_point_mode})"
            self.mode_label.config(text=f"Current Mode: {mode_text}", fg=self.colors['success'])
        elif mode == "connect":
            self.connect_btn.config(relief=tk.SUNKEN, bg=self.colors['connect_bg'], fg=self.colors['button_fg'])
            self.mode_label.config(text="Current Mode: Connect (select 2 points)", fg=self.colors['warning'])
        elif mode == "delete":
            self.delete_btn.config(relief=tk.SUNKEN, bg=self.colors['delete_bg'], fg=self.colors['button_fg'])
            self.mode_label.config(text="Current Mode: Delete", fg=self.colors['error'])

    def toggle_dual_view(self):
        """Toggle dual view mode"""
        self.dual_view_mode = self.dual_view_var.get()

        if self.dual_view_mode:
            if len(self.dual_view_layers) == 2:
                self.setup_dual_view_canvases()
                self.fit_all_view()
                self.dual_label.config(
                    text=f"Dual View Active: {self.dual_view_layers[0]} | {self.dual_view_layers[1]}", 
                    fg=self.colors['success'])
            else:
                messagebox.showwarning("Dual View Mode", "Select exactly 2 layers first!")
                self.dual_view_var.set(False)
                self.dual_view_mode = False
        else:
            self.setup_normal_canvas()
            self.dual_label.config(text="Select exactly 2 layers", fg=self.colors['axis'])

    def setup_normal_canvas(self):
        """Setup single canvas for normal mode"""
        for widget in self.canvas_container.winfo_children():
            widget.destroy()

        self.canvas_label.config(text="2D View", fg=self.colors['fg'])

        self.canvas = tk.Canvas(self.canvas_container, bg=self.colors['canvas_bg'],
                               width=self.canvas_width, height=self.canvas_height,
                               highlightthickness=1, highlightbackground=self.colors['border'])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.setup_canvas_bindings(self.canvas)

        self.canvas_left = None
        self.canvas_right = None
        self.update_plot()

    def setup_dual_view_canvases(self):
        """Setup side-by-side canvases for dual view mode"""
        for widget in self.canvas_container.winfo_children():
            widget.destroy()

        self.canvas_label.config(
            text=f"Dual View: {self.dual_view_layers[0]} (Left) | {self.dual_view_layers[1]} (Right)",
            fg=self.colors['fg'])

        # Left canvas
        left_frame = tk.Frame(self.canvas_container, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        tk.Label(left_frame, text=f"{self.dual_view_layers[0]} (Red)", 
                font=("Arial", 10, "bold"), fg="#ff6b6b",
                bg=self.colors['bg']).pack()

        self.canvas_left = tk.Canvas(left_frame, bg=self.colors['canvas_bg'],
                                     width=self.canvas_width//2, height=self.canvas_height,
                                     highlightthickness=1, highlightbackground=self.colors['border'])
        self.canvas_left.pack(fill=tk.BOTH, expand=True)
        self.canvas_left.bind("<Button-1>", lambda e: self.on_dual_click(e, 0))
        self.setup_canvas_bindings(self.canvas_left)

        # Right canvas
        right_frame = tk.Frame(self.canvas_container, bg=self.colors['bg'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        tk.Label(right_frame, text=f"{self.dual_view_layers[1]} (Blue)", 
                font=("Arial", 10, "bold"), fg="#4dabf7",
                bg=self.colors['bg']).pack()

        self.canvas_right = tk.Canvas(right_frame, bg=self.colors['canvas_bg'],
                                      width=self.canvas_width//2, height=self.canvas_height,
                                      highlightthickness=1, highlightbackground=self.colors['border'])
        self.canvas_right.pack(fill=tk.BOTH, expand=True)
        self.canvas_right.bind("<Button-1>", lambda e: self.on_dual_click(e, 1))
        self.setup_canvas_bindings(self.canvas_right)

        self.canvas = None
        self.update_plot()

    def update_layer_list(self):
        """Update layer listbox - sorted by name (not by Z)"""
        self.layer_listbox.delete(0, tk.END)
        # Sort layers by name instead of Z value
        sorted_layers = sorted(self.mesh_data.layers.items(), key=lambda x: x[0])
        for name, layer_data in sorted_layers:
            z = layer_data.get('z', 0)
            num_points = len(layer_data.get('point_refs', []))
            self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")

    def update_dual_view_buttons(self):
        """Update dual view layer selection buttons - sorted by name"""
        for widget in self.dual_buttons_frame.winfo_children():
            widget.destroy()

        # Sort layers by name instead of Z value
        sorted_layers = sorted(self.mesh_data.layers.items(), key=lambda x: x[0])

        for name, layer_data in sorted_layers:
            is_selected = name in self.dual_view_layers
            z = layer_data.get('z', 0)

            btn = tk.Button(
                self.dual_buttons_frame,
                text=f"{name} (z={z})",
                bg=self.colors['success'] if is_selected else self.colors['bg'],
                fg=self.colors['bg'] if is_selected else self.colors['fg'],
                relief=tk.SUNKEN if is_selected else tk.RAISED,
                font=("Arial", 8, "bold" if is_selected else "normal"),
                command=lambda n=name: self.toggle_layer_in_dual_view(n),
                activebackground=self.colors['accent'] if is_selected else self.colors['button_active'],
                activeforeground=self.colors['button_fg']
            )
            btn.pack(anchor=tk.W, fill=tk.X, pady=1)

    def toggle_layer_in_dual_view(self, layer_name):
        """Toggle layer selection for dual view"""
        if layer_name in self.dual_view_layers:
            self.dual_view_layers.remove(layer_name)
        else:
            if len(self.dual_view_layers) >= 2:
                self.dual_view_layers.pop(0)
            self.dual_view_layers.append(layer_name)

        self.update_dual_view_buttons()

        if len(self.dual_view_layers) == 2:
            self.dual_label.config(
                text=f"Ready: {self.dual_view_layers[0]} ↔ {self.dual_view_layers[1]}", 
                fg=self.colors['success'])
            if self.dual_view_mode:
                self.setup_dual_view_canvases()
        elif len(self.dual_view_layers) == 1:
            self.dual_label.config(
                text=f"Selected: {self.dual_view_layers[0]} - Select 1 more", 
                fg=self.colors['warning'])
        else:
            self.dual_label.config(text="Select exactly 2 layers", fg=self.colors['axis'])

    def world_to_canvas(self, x, y, canvas_widget=None):
        """Convert world coordinates to canvas coordinates"""
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            height = canvas_widget.winfo_height() or self.canvas_height
            cx = (width / 2 + self.dual_offset_x) + x * self.scale
            cy = (height / 2 + self.dual_offset_y) - y * self.scale
        else:
            cx = self.offset_x + x * self.scale
            cy = self.offset_y - y * self.scale
        return cx, cy

    def canvas_to_world(self, cx, cy, canvas_widget=None):
        """Convert canvas coordinates to world coordinates"""
        if canvas_widget and canvas_widget in [self.canvas_left, self.canvas_right]:
            width = canvas_widget.winfo_width() or self.canvas_width // 2
            height = canvas_widget.winfo_height() or self.canvas_height
            x = (cx - (width / 2 + self.dual_offset_x)) / self.scale
            y = ((height / 2 + self.dual_offset_y) - cy) / self.scale
        else:
            x = (cx - self.offset_x) / self.scale
            y = (self.offset_y - cy) / self.scale
        return x, y

    def on_canvas_click(self, event):
        """Handle click on normal canvas"""
        if self.dual_view_mode or self.panning:
            return

        # Initialize lasso selection coordinates
        if self.mode in ["select", "delete"]:
            self.lasso_start_x = event.x
            self.lasso_start_y = event.y

        x, y = self.canvas_to_world(event.x, event.y, self.canvas)
        layer_name = self.mesh_data.current_layer
        layer_data = self.mesh_data.layers.get(layer_name, {})
        point_refs = layer_data.get('point_refs', [])

        # Find clicked point
        clicked_point_id = None
        min_dist = float('inf')

        for point_id in point_refs:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                px, py = point_data['x'], point_data['y']
                dist = math.sqrt((px - x)**2 + (py - y)**2)
                if dist < 0.3:  # Click tolerance
                    if dist < min_dist:
                        min_dist = dist
                        clicked_point_id = point_id

        if self.mode == "delete":
            if clicked_point_id is not None:
                self.mesh_data.save_state()
                self.mesh_data.remove_point(clicked_point_id)
                self.clear_selection()
        elif self.mode == "add":
            if clicked_point_id is None:
                self.mesh_data.save_state()
                # Apply snap if in snap mode
                if self.add_point_mode == "snap":
                    x = round(x / self.snap_grid_size) * self.snap_grid_size
                    y = round(y / self.snap_grid_size) * self.snap_grid_size
                self.mesh_data.add_point(x, y, layer=layer_name)
        elif self.mode == "connect":
            if clicked_point_id is not None:
                if clicked_point_id not in self.selected_points:
                    self.selected_points.append(clicked_point_id)

                    if len(self.selected_points) == 2:
                        self.mesh_data.save_state()
                        # Create connection between two points
                        self.mesh_data.add_connection(
                            self.selected_points[0], 
                            self.selected_points[1])
                        self.selected_points = []

                    self.selection_label.config(text=f"Selected: {self.selected_points}")
        elif self.mode == "select":
            if clicked_point_id is not None:
                if clicked_point_id in self.selected_points:
                    # Deselect if already selected
                    self.selected_points.remove(clicked_point_id)
                else:
                    self.selected_points.append(clicked_point_id)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selection_label.config(text=f"Selected points: {self.selected_points}")

        self.update_plot()

    def on_dual_click(self, event, canvas_idx):
        """Handle click in dual view - delegates to dual_handler"""
        if not self.dual_view_mode or len(self.dual_view_layers) != 2 or self.panning:
            return

        self.dual_handler.handle_dual_canvas_click(event, canvas_idx)

    def on_lasso_drag(self, event):
        """Handle dragging left click to draw a lasso selection"""
        if self.mode not in ["select", "delete"] or self.panning:
            return

        canvas = event.widget
        if self.lasso_rect:
            canvas.delete(self.lasso_rect)

        # Draw the selection rectangle
        self.lasso_rect = canvas.create_rectangle(
            self.lasso_start_x, self.lasso_start_y, event.x, event.y,
            outline=self.colors['accent'], dash=(4, 4), tag="lasso"
        )

    def on_lasso_end(self, event):
        """Compute the enclosed points on releasing the drag"""
        if self.mode not in ["select", "delete"] or self.panning:
            return

        canvas = event.widget
        if self.lasso_rect:
            canvas.delete(self.lasso_rect)
            self.lasso_rect = None

        # Convert the bounding box to world coordinates
        x1, y1 = self.canvas_to_world(self.lasso_start_x, self.lasso_start_y, canvas)
        x2, y2 = self.canvas_to_world(event.x, event.y, canvas)

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        # Ignore tiny clicks (which are handled by on_canvas_click)
        if (max_x - min_x) < 0.1 and (max_y - min_y) < 0.1:
            return

        # Determine which layer data to check based on the canvas
        layers_to_check = []
        if self.dual_view_mode:
            if canvas == self.canvas_left and len(self.dual_view_layers) > 0:
                layers_to_check.append(self.dual_view_layers[0])
            elif canvas == self.canvas_right and len(self.dual_view_layers) > 1:
                layers_to_check.append(self.dual_view_layers[1])
        else:
            layers_to_check.append(self.mesh_data.current_layer)

        # Find enclosed points
        enclosed_points = []
        for layer_name in layers_to_check:
            layer_data = self.mesh_data.layers.get(layer_name, {})
            point_refs = layer_data.get('point_refs', [])

            for point_id in point_refs:
                point_data = self.mesh_data.get_point(point_id)
                if point_data:
                    px, py = point_data['x'], point_data['y']
                    if min_x <= px <= max_x and min_y <= py <= max_y:
                        enclosed_points.append(point_id)

        if not enclosed_points:
            return

        # Apply mode action
        if self.mode == "select":
            for point_id in enclosed_points:
                if point_id not in self.selected_points:
                    self.selected_points.append(point_id)
            self.selection_label.config(text=f"Selected points: {self.selected_points}")
        elif self.mode == "delete":
            if messagebox.askyesno("Confirm Delete", f"Delete {len(enclosed_points)} enclosed points?"):
                self.mesh_data.save_state()
                for point_id in enclosed_points:
                    self.mesh_data.remove_point(point_id)
                self.clear_selection()

        self.update_plot()

    def update_plot(self):
        """Update the canvas display"""
        if self.dual_view_mode and len(self.dual_view_layers) == 2:
            self.draw_dual_view()
        else:
            self.draw_normal_mode()

    def draw_normal_mode(self):
        """Draw normal single-layer view"""
        if not self.canvas:
            return

        self.canvas.delete("all")
        self.draw_grid(self.canvas)

        # Draw snap grid if in add mode and snap mode
        if self.mode == "add" and self.add_point_mode == "snap":
            self.draw_snap_grid(self.canvas)

        layer_name = self.mesh_data.current_layer
        layer_data = self.mesh_data.layers.get(layer_name, {})
        point_refs = layer_data.get('point_refs', [])

        # Build a set of points in this layer for quick lookup
        layer_point_set = set(point_refs)

        # Draw connections that involve points in this layer
        for conn_id, conn_data in self.mesh_data.connections.items():
            p1_id = conn_data.get('point1')
            p2_id = conn_data.get('point2')

            # Only draw if both points are in current layer
            if p1_id in layer_point_set and p2_id in layer_point_set:
                p1_data = self.mesh_data.get_point(p1_id)
                p2_data = self.mesh_data.get_point(p2_id)
                if p1_data and p2_data:
                    cx1, cy1 = self.world_to_canvas(p1_data['x'], p1_data['y'], self.canvas)
                    cx2, cy2 = self.world_to_canvas(p2_data['x'], p2_data['y'], self.canvas)
                    self.canvas.create_line(cx1, cy1, cx2, cy2, 
                                           fill=self.colors['accent'], width=2)

        # Draw points
        for point_id in point_refs:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                cx, cy = self.world_to_canvas(point_data['x'], point_data['y'], self.canvas)

                if point_id in self.selected_points:
                    color = self.colors['success']
                    radius = 8
                else:
                    color = self.colors['error']
                    radius = 5

                self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                       fill=color, outline=self.colors['fg'], width=2)
                self.canvas.create_text(cx, cy-15, text=str(point_id), 
                                       font=("Arial", 9, "bold"),
                                       fill=self.colors['fg'])

    def draw_snap_grid(self, canvas):
        """Draw snap grid lines on canvas"""
        width = canvas.winfo_width() or self.canvas_width
        height = canvas.winfo_height() or self.canvas_height

        # Calculate visible world bounds
        min_x = (0 - self.offset_x) / self.scale
        max_x = (width - self.offset_x) / self.scale
        min_y = (self.offset_y - height) / self.scale
        max_y = (self.offset_y - 0) / self.scale

        # Round to grid
        start_x = math.floor(min_x / self.snap_grid_size) * self.snap_grid_size
        end_x = math.ceil(max_x / self.snap_grid_size) * self.snap_grid_size
        start_y = math.floor(min_y / self.snap_grid_size) * self.snap_grid_size
        end_y = math.ceil(max_y / self.snap_grid_size) * self.snap_grid_size

        # Draw vertical lines
        x = start_x
        while x <= end_x:
            cx, _ = self.world_to_canvas(x, 0, canvas)
            canvas.create_line(cx, 0, cx, height, fill='#2a3f5f', width=1)
            x += self.snap_grid_size

        # Draw horizontal lines
        y = start_y
        while y <= end_y:
            _, cy = self.world_to_canvas(0, y, canvas)
            canvas.create_line(0, cy, width, cy, fill='#2a3f5f', width=1)
            y += self.snap_grid_size

    def draw_dual_view(self):
        """Draw dual-layer view side by side"""
        if not self.canvas_left or not self.canvas_right:
            return

        self.canvas_left.delete("all")
        self.canvas_right.delete("all")

        self.draw_grid(self.canvas_left)
        self.draw_grid(self.canvas_right)

        # Draw left layer
        layer_left = self.dual_view_layers[0]
        layer_data_left = self.mesh_data.layers.get(layer_left, {})
        point_refs_left = layer_data_left.get('point_refs', [])
        left_point_set = set(point_refs_left)

        # Draw connections for left layer
        for conn_id, conn_data in self.mesh_data.connections.items():
            p1_id = conn_data.get('point1')
            p2_id = conn_data.get('point2')
            if p1_id in left_point_set and p2_id in left_point_set:
                p1_data = self.mesh_data.get_point(p1_id)
                p2_data = self.mesh_data.get_point(p2_id)
                if p1_data and p2_data:
                    cx1, cy1 = self.world_to_canvas(p1_data['x'], p1_data['y'], self.canvas_left)
                    cx2, cy2 = self.world_to_canvas(p2_data['x'], p2_data['y'], self.canvas_left)
                    self.canvas_left.create_line(cx1, cy1, cx2, cy2, fill="#ff6b6b", width=2)

        # Draw points for left layer
        for point_id in point_refs_left:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                cx, cy = self.world_to_canvas(point_data['x'], point_data['y'], self.canvas_left)

                if point_id in self.selected_points:
                    color = self.colors['success']
                    radius = 8
                else:
                    color = "#ff6b6b"
                    radius = 5

                self.canvas_left.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                            fill=color, outline=self.colors['fg'], width=2)
                self.canvas_left.create_text(cx, cy-15, text=str(point_id), 
                                            font=("Arial", 9, "bold"),
                                            fill=self.colors['fg'])

        # Draw right layer
        layer_right = self.dual_view_layers[1]
        layer_data_right = self.mesh_data.layers.get(layer_right, {})
        point_refs_right = layer_data_right.get('point_refs', [])
        right_point_set = set(point_refs_right)

        # Draw connections for right layer
        for conn_id, conn_data in self.mesh_data.connections.items():
            p1_id = conn_data.get('point1')
            p2_id = conn_data.get('point2')
            if p1_id in right_point_set and p2_id in right_point_set:
                p1_data = self.mesh_data.get_point(p1_id)
                p2_data = self.mesh_data.get_point(p2_id)
                if p1_data and p2_data:
                    cx1, cy1 = self.world_to_canvas(p1_data['x'], p1_data['y'], self.canvas_right)
                    cx2, cy2 = self.world_to_canvas(p2_data['x'], p2_data['y'], self.canvas_right)
                    self.canvas_right.create_line(cx1, cy1, cx2, cy2, fill="#4dabf7", width=2)

        # Draw points for right layer
        for point_id in point_refs_right:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                cx, cy = self.world_to_canvas(point_data['x'], point_data['y'], self.canvas_right)

                if point_id in self.selected_points:
                    color = self.colors['success']
                    radius = 8
                else:
                    color = "#4dabf7"
                    radius = 5

                self.canvas_right.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                             fill=color, outline=self.colors['fg'], width=2)
                self.canvas_right.create_text(cx, cy-15, text=str(point_id), 
                                             font=("Arial", 9, "bold"),
                                             fill=self.colors['fg'])

        # Draw dual view selection markers
        self.canvas_left.delete('dual_selection')
        self.canvas_right.delete('dual_selection')
        self.dual_handler.draw_dual_selection_markers()

    def draw_grid(self, canvas):
        """Draw grid on canvas"""
        width = canvas.winfo_width() or (self.canvas_width if canvas == self.canvas else self.canvas_width // 2)
        height = canvas.winfo_height() or self.canvas_height

        for i in range(-20, 21):
            cx, cy = self.world_to_canvas(i, 0, canvas)
            canvas.create_line(cx, 0, cx, height, fill=self.colors['grid'], dash=(2, 2))

            cx, cy = self.world_to_canvas(0, i, canvas)
            canvas.create_line(0, cy, width, cy, fill=self.colors['grid'], dash=(2, 2))

        cx, cy = self.world_to_canvas(0, 0, canvas)
        canvas.create_line(0, cy, width, cy, fill=self.colors['axis'], width=2)
        canvas.create_line(cx, 0, cx, height, fill=self.colors['axis'], width=2)

    def delete_connection(self):
        """Delete selected connection"""
        # Save undo state
        self.mesh_data.save_state()

        if self.selected_connection is None:
            messagebox.showwarning("Warning", "No connection selected")
            return

        conn_id = self.selected_connection
        if conn_id in self.mesh_data.connections:
            self.mesh_data.remove_connection(conn_id)
            self.selected_connection = None
            self.update_plot()

    def set_add_point_mode(self, mode):
        """Set add point mode: 'click' or 'snap'"""
        self.add_point_mode = mode
        if self.mode == "add":
            self.set_mode("add")  # Refresh mode label
        self.update_plot()