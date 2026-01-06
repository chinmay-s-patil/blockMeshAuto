"""
2D Editor Tab - Points & Connections
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


class Tab2DEditor:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.selected_points = []
        self.mode = "select"
        self.iso_mode = False
        self.iso_layers = []
        self.iso_mode_var = tk.BooleanVar(value=False)
        self.iso_layer_vars = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="X-Y Plane View (2D)", font=("Arial", 12, "bold")).pack()
        
        self.fig_2d = Figure(figsize=(7, 7))
        self.ax_2d = self.fig_2d.add_subplot(111)
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, left_frame)
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas_2d.mpl_connect('button_press_event', self.on_2d_click)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        self._setup_mode_controls(right_frame)
        self._setup_layer_controls(right_frame)
        self._setup_manual_entry(right_frame)
        self._setup_connection_controls(right_frame)
        
        self.update_plot()
        
    def _setup_mode_controls(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.select_btn = tk.Button(mode_frame, text="Select Points (Connect)", 
                                     command=lambda: self.set_mode("select"), 
                                     relief=tk.SUNKEN, bg="lightblue")
        self.select_btn.pack(fill=tk.X, pady=2)
        
        self.add_btn = tk.Button(mode_frame, text="Add Points", 
                                 command=lambda: self.set_mode("add"))
        self.add_btn.pack(fill=tk.X, pady=2)
        
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
        
        tk.Button(layer_btn_frame, text="Add", command=self.add_layer, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Duplicate", command=self.duplicate_layer, width=8).pack(side=tk.LEFT, padx=1)
        tk.Button(layer_btn_frame, text="Remove", command=self.remove_layer, width=7).pack(side=tk.LEFT, padx=1)
        
        self.layer_info = tk.Label(layer_frame, text=f"Current: {self.mesh_data.current_layer}", 
                                   font=("Arial", 9, "bold"), fg="blue")
        self.layer_info.pack(pady=5)
        
        # ISO Mode
        iso_frame = tk.LabelFrame(layer_frame, text="ISO Mode - Link Between Layers", padx=10, pady=10)
        iso_frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(iso_frame, text="Enable Iso Mode", 
                      variable=self.iso_mode_var, command=self.toggle_iso_mode,
                      font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        tk.Label(iso_frame, text="Select 2 layers to link:", font=("Arial", 8)).pack(anchor=tk.W, pady=(5,2))
        
        iso_canvas_frame = tk.Frame(iso_frame, height=100)
        iso_canvas_frame.pack(fill=tk.BOTH)
        iso_canvas_frame.pack_propagate(False)
        
        self.iso_checkboxes_frame = tk.Frame(iso_canvas_frame)
        self.iso_checkboxes_frame.pack(fill=tk.BOTH)
        
        self.update_iso_checkboxes()
        
        self.iso_label = tk.Label(iso_frame, text="Select exactly 2 layers", 
                                 font=("Arial", 8, "italic"), fg="gray")
        self.iso_label.pack(pady=2)
        
    def _setup_manual_entry(self, parent):
        manual_frame = tk.LabelFrame(parent, text="Manual Entry", padx=10, pady=10)
        manual_frame.pack(fill=tk.X, padx=5, pady=5)
        
        entry_grid = tk.Frame(manual_frame)
        entry_grid.pack()
        
        tk.Label(entry_grid, text="X:").grid(row=0, column=0)
        self.x_entry = tk.Entry(entry_grid, width=8)
        self.x_entry.grid(row=0, column=1, padx=2)
        
        tk.Label(entry_grid, text="Y:").grid(row=0, column=2)
        self.y_entry = tk.Entry(entry_grid, width=8)
        self.y_entry.grid(row=0, column=3, padx=2)
        
        tk.Button(manual_frame, text="Add Point", command=self.add_point_manual).pack(pady=5)
        
    def _setup_connection_controls(self, parent):
        conn_frame = tk.LabelFrame(parent, text="Connections", padx=10, pady=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selection_label = tk.Label(conn_frame, text="Selected: None", fg="green")
        self.selection_label.pack()
        
        tk.Button(conn_frame, text="Create Connection", 
                 command=self.create_connection).pack(fill=tk.X, pady=2)
        tk.Button(conn_frame, text="Clear Selection", 
                 command=self.clear_selection).pack(fill=tk.X, pady=2)
    
    def set_mode(self, mode):
        self.mode = mode
        
        self.select_btn.config(relief=tk.RAISED, bg="lightgray")
        self.add_btn.config(relief=tk.RAISED, bg="lightgray")
        self.delete_btn.config(relief=tk.RAISED, bg="lightgray")
        
        if mode == "select":
            self.select_btn.config(relief=tk.SUNKEN, bg="lightblue")
            self.mode_label.config(text="Current Mode: Select", fg="blue")
        elif mode == "add":
            self.add_btn.config(relief=tk.SUNKEN, bg="lightgreen")
            self.mode_label.config(text="Current Mode: Add", fg="green")
        elif mode == "delete":
            self.delete_btn.config(relief=tk.SUNKEN, bg="salmon")
            self.mode_label.config(text="Current Mode: Delete", fg="red")
    
    def toggle_iso_mode(self):
        self.iso_mode = self.iso_mode_var.get()
        if self.iso_mode:
            self.iso_label.config(text="Iso Mode Active - Select 2 layers below", fg="green")
            self.update_iso_layers_from_checkboxes()
        else:
            self.iso_label.config(text="Select exactly 2 layers", fg="gray")
            self.iso_layers = []
        self.update_plot()
    
    def update_iso_checkboxes(self):
        for widget in self.iso_checkboxes_frame.winfo_children():
            widget.destroy()
        
        self.iso_layer_vars = {}
        
        for name in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            var = tk.BooleanVar(value=False)
            self.iso_layer_vars[name] = var
            cb = tk.Checkbutton(self.iso_checkboxes_frame, text=f"{name} (z={self.mesh_data.layers[name]})", 
                              variable=var, command=self.update_iso_layers_from_checkboxes)
            cb.pack(anchor=tk.W)
    
    def update_iso_layers_from_checkboxes(self):
        self.iso_layers = [name for name, var in self.iso_layer_vars.items() if var.get()]
        
        if len(self.iso_layers) > 2:
            oldest = self.iso_layers[0]
            self.iso_layer_vars[oldest].set(False)
            self.iso_layers = [name for name, var in self.iso_layer_vars.items() if var.get()]
        
        if len(self.iso_layers) == 2:
            self.iso_label.config(text=f"Linking: {self.iso_layers[0]} ↔ {self.iso_layers[1]}", fg="green")
        elif len(self.iso_layers) == 1:
            self.iso_label.config(text=f"Selected: {self.iso_layers[0]} - Select 1 more", fg="orange")
        else:
            self.iso_label.config(text="Select exactly 2 layers", fg="gray")
        
        if self.iso_mode:
            self.update_plot()
    
    def on_2d_click(self, event):
        if event.inaxes != self.ax_2d:
            return
        
        x, y = event.xdata, event.ydata
        
        if self.iso_mode and len(self.iso_layers) == 2:
            self.handle_iso_click(x, y)
            return
        
        layer = self.mesh_data.current_layer
        points = self.mesh_data.points[layer]
        
        clicked_idx = None
        for idx, (px, py) in enumerate(points):
            dist = np.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.5:
                clicked_idx = idx
                break
        
        if self.mode == "delete":
            if clicked_idx is not None:
                self.mesh_data.remove_point(layer, clicked_idx)
                self.clear_selection()
        elif self.mode == "add":
            if clicked_idx is None:
                self.mesh_data.add_point(layer, x, y)
        elif self.mode == "select":
            if clicked_idx is not None:
                if clicked_idx not in self.selected_points:
                    self.selected_points.append(clicked_idx)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                self.selection_label.config(text=f"Selected: {self.selected_points}")
        
        self.update_plot()
    
    def handle_iso_click(self, x, y):
        min_dist = float('inf')
        closest_point = None
        
        for layer in self.iso_layers:
            points = self.mesh_data.points[layer]
            for idx, (px, py) in enumerate(points):
                dist = np.sqrt((px - x)**2 + (py - y)**2)
                if dist < min_dist and dist < 0.5:
                    min_dist = dist
                    closest_point = (layer, idx)
        
        if closest_point:
            if closest_point not in self.selected_points:
                self.selected_points.append(closest_point)
                if len(self.selected_points) > 2:
                    self.selected_points.pop(0)
            else:
                self.selected_points.remove(closest_point)
            
            self.selection_label.config(text=f"Selected: {self.selected_points}")
            self.update_plot()
    
    def add_point_manual(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            self.mesh_data.add_point(self.mesh_data.current_layer, x, y)
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            self.update_plot()
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers")
    
    def create_connection(self):
        if len(self.selected_points) != 2:
            messagebox.showwarning("Warning", "Select exactly 2 points")
            return
        
        if isinstance(self.selected_points[0], tuple) and isinstance(self.selected_points[1], tuple):
            layer1, idx1 = self.selected_points[0]
            layer2, idx2 = self.selected_points[1]
            
            if layer1 != layer2:
                self.mesh_data.add_inter_layer_connection(layer1, idx1, layer2, idx2)
                messagebox.showinfo("Success", f"Inter-layer connection created:\n{layer1}[{idx1}] ↔ {layer2}[{idx2}]")
            else:
                self.mesh_data.add_connection(layer1, idx1, idx2)
                messagebox.showinfo("Success", f"Connection created in {layer1}")
        else:
            if not isinstance(self.selected_points[0], int) or not isinstance(self.selected_points[1], int):
                messagebox.showerror("Error", "Invalid point selection. Exit ISO mode for regular connections.")
                return
            
            self.mesh_data.add_connection(self.mesh_data.current_layer, 
                                         self.selected_points[0], 
                                         self.selected_points[1])
        
        self.clear_selection()
        self.update_plot()
    
    def clear_selection(self):
        self.selected_points = []
        self.selection_label.config(text="Selected: None")
        self.update_plot()
    
    def update_plot(self):
        self.ax_2d.clear()
        
        self.ax_2d.grid(True, alpha=0.3)
        self.ax_2d.set_xlabel("X")
        self.ax_2d.set_ylabel("Y")
        
        all_x, all_y = [], []
        for layer in self.mesh_data.points:
            for x, y in self.mesh_data.points[layer]:
                all_x.append(x)
                all_y.append(y)
        
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            
            range_x = max(max_x - min_x, 2)
            range_y = max(max_y - min_y, 2)
            
            max_range = max(range_x, range_y)
            center_x = (max_x + min_x) / 2
            center_y = (max_y + min_y) / 2
            
            margin = max_range * 0.2 + 1
            self.ax_2d.set_xlim(center_x - max_range/2 - margin, center_x + max_range/2 + margin)
            self.ax_2d.set_ylim(center_y - max_range/2 - margin, center_y + max_range/2 + margin)
        else:
            self.ax_2d.set_xlim(-1, 7)
            self.ax_2d.set_ylim(-1, 7)
        
        if self.iso_mode and len(self.iso_layers) == 2:
            self.ax_2d.set_title(f"Iso Mode: {self.iso_layers[0]} & {self.iso_layers[1]}")
            
            colors = ['red', 'blue']
            for i, layer in enumerate(self.iso_layers):
                points = self.mesh_data.points[layer]
                
                for conn in self.mesh_data.connections[layer]:
                    p1, p2 = points[conn[0]], points[conn[1]]
                    self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                                   color=colors[i], linewidth=1.5, alpha=0.7)
                
                if points:
                    xs, ys = zip(*points)
                    self.ax_2d.plot(xs, ys, 'o', color=colors[i], markersize=8, 
                                   label=f"{layer}")
                    
                    for selected in self.selected_points:
                        if isinstance(selected, tuple) and selected[0] == layer:
                            idx = selected[1]
                            if idx < len(points):
                                self.ax_2d.plot(points[idx][0], points[idx][1], 'go', 
                                              markersize=15, alpha=0.6, markeredgewidth=2,
                                              markeredgecolor='green')
            
            for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
                if layer1 in self.iso_layers and layer2 in self.iso_layers:
                    if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                        p1 = self.mesh_data.points[layer1][idx1]
                        p2 = self.mesh_data.points[layer2][idx2]
                        self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                                       'g--', linewidth=2, alpha=0.5)
            
            self.ax_2d.legend()
        else:
            layer = self.mesh_data.current_layer
            z = self.mesh_data.layers[layer]
            self.ax_2d.set_title(f"Layer: {layer} (z={z})")
            
            points = self.mesh_data.points[layer]
            for conn in self.mesh_data.connections[layer]:
                p1, p2 = points[conn[0]], points[conn[1]]
                self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-', linewidth=1.5)
            
            if points:
                xs, ys = zip(*points)
                self.ax_2d.plot(xs, ys, 'ro', markersize=8)
                
                for idx in self.selected_points:
                    if isinstance(idx, int) and idx < len(points):
                        self.ax_2d.plot(points[idx][0], points[idx][1], 'go', 
                                       markersize=12, alpha=0.5)
        
        self.canvas_2d.draw()
    
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
            self.update_iso_checkboxes()
    
    def duplicate_layer(self):
        current = self.mesh_data.current_layer
        num = len(self.mesh_data.layers)
        
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
            self.update_iso_checkboxes()
            messagebox.showinfo("Success", f"Layer duplicated: {name}")
    
    def remove_layer(self):
        if len(self.mesh_data.layers) <= 1:
            messagebox.showwarning("Warning", "Cannot remove last layer")
            return
        
        self.mesh_data.remove_layer(self.mesh_data.current_layer)
        self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
        self.update_layer_list()
        self.update_iso_checkboxes()
        self.update_plot()