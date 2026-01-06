import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import json
import os

from mesh_data import MeshData
from blockmesh_export import BlockMeshExporter
from viewer_3d import Viewer3D

class MeshBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenFOAM blockMesh Builder")
        self.root.geometry("1400x900")
        
        self.mesh_data = MeshData()
        self.selected_points = []
        self.mode = "select"
        self.iso_mode = False
        self.iso_layers = []
        self.face_selection_mode = False
        self.temp_json_file = "mesh_temp.json"
        
        self.setup_top_bar()
        self.setup_notebook()
        self.setup_2d_view()
        self.setup_grid_view()
        self.setup_3d_view()
        self.setup_patch_view()
        
        self.auto_save()
        
    def setup_top_bar(self):
        top_frame = tk.Frame(self.root, bg="lightgray", height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="OpenFOAM Mesh Builder", 
                font=("Arial", 14, "bold"), bg="lightgray").pack(side=tk.LEFT, padx=10)
        
        button_frame = tk.Frame(top_frame, bg="lightgray")
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(button_frame, text="💾 Save", command=self.save_to_json,
                 bg="lightgreen", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 Load", command=self.load_from_json,
                 bg="lightblue", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 New", command=self.new_project,
                 bg="lightyellow", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        
    def setup_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.tab_2d = tk.Frame(self.notebook)
        self.notebook.add(self.tab_2d, text="1. Points & Connections")
        
        self.tab_grid = tk.Frame(self.notebook)
        self.notebook.add(self.tab_grid, text="2. Grid Sizing")
        
        self.tab_3d = tk.Frame(self.notebook)
        self.notebook.add(self.tab_3d, text="3. 3D View & Patches")
        
        self.tab_export = tk.Frame(self.notebook)
        self.notebook.add(self.tab_export, text="4. Export blockMeshDict")
        
    def setup_2d_view(self):
        main_frame = tk.Frame(self.tab_2d)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="X-Y Plane View (2D)", font=("Arial", 12, "bold")).pack()
        
        self.fig_2d = Figure(figsize=(7, 7))
        self.ax_2d = self.fig_2d.add_subplot(111)
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, left_frame)
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas_2d.mpl_connect('button_press_event', self.on_2d_click)
        
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        mode_frame = tk.LabelFrame(right_frame, text="Mode", padx=10, pady=10)
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
        
        layer_frame = tk.LabelFrame(right_frame, text="Layers (Z-values)", padx=10, pady=10)
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
        
        iso_frame = tk.LabelFrame(layer_frame, text="ISO Mode - Link Between Layers", padx=10, pady=10)
        iso_frame.pack(fill=tk.X, pady=5)
        
        self.iso_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(iso_frame, text="Enable Iso Mode", 
                      variable=self.iso_mode_var, command=self.toggle_iso_mode,
                      font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        tk.Label(iso_frame, text="Select 2 layers to link:", font=("Arial", 8)).pack(anchor=tk.W, pady=(5,2))
        
        iso_canvas_frame = tk.Frame(iso_frame, height=100)
        iso_canvas_frame.pack(fill=tk.BOTH)
        iso_canvas_frame.pack_propagate(False)
        
        self.iso_layer_vars = {}
        self.iso_checkboxes_frame = tk.Frame(iso_canvas_frame)
        self.iso_checkboxes_frame.pack(fill=tk.BOTH)
        
        self.update_iso_checkboxes()
        
        self.iso_label = tk.Label(iso_frame, text="Select exactly 2 layers", 
                                 font=("Arial", 8, "italic"), fg="gray")
        self.iso_label.pack(pady=2)
        
        manual_frame = tk.LabelFrame(right_frame, text="Manual Entry", padx=10, pady=10)
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
        
        conn_frame = tk.LabelFrame(right_frame, text="Connections", padx=10, pady=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selection_label = tk.Label(conn_frame, text="Selected: None", fg="green")
        self.selection_label.pack()
        
        tk.Button(conn_frame, text="Create Connection", 
                 command=self.create_connection).pack(fill=tk.X, pady=2)
        tk.Button(conn_frame, text="Clear Selection", 
                 command=self.clear_selection).pack(fill=tk.X, pady=2)
        
        self.update_2d_plot()
        
    def setup_grid_view(self):
        main_frame = tk.Frame(self.tab_grid)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Connection View", font=("Arial", 12, "bold")).pack()
        
        self.fig_grid_3d = Figure(figsize=(7, 7))
        self.ax_grid_3d = self.fig_grid_3d.add_subplot(111, projection='3d')
        self.canvas_grid_3d = FigureCanvasTkAgg(self.fig_grid_3d, left_frame)
        self.canvas_grid_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_grid_3d, toolbar_frame)
        toolbar.update()
        
        self.canvas_grid_3d.mpl_connect('button_press_event', self.on_grid_3d_click)
        
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update View", command=self.update_grid_3d_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        sel_frame = tk.LabelFrame(right_frame, text="Connection Selection", padx=10, pady=10)
        sel_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(sel_frame, text="Click connections to select", font=("Arial", 9, "italic")).pack()
        
        self.conn_listbox = tk.Listbox(sel_frame, height=10, selectmode=tk.SINGLE)
        self.conn_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.conn_listbox.bind('<<ListboxSelect>>', self.on_connection_select)
        
        self.selected_conn_label = tk.Label(sel_frame, text="Selected: None", fg="blue")
        self.selected_conn_label.pack(pady=5)
        
        grid_frame = tk.LabelFrame(right_frame, text="Grid Subdivisions", padx=10, pady=10)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(grid_frame, text="Divisions for selected connection:").pack(anchor=tk.W)
        
        self.subdiv_var = tk.IntVar(value=10)
        tk.Scale(grid_frame, from_=1, to=100, variable=self.subdiv_var, 
                orient=tk.HORIZONTAL, label="Subdivisions").pack(fill=tk.X, pady=5)
        
        tk.Button(grid_frame, text="Apply to Selected", 
                 command=self.apply_subdivisions, bg="lightblue").pack(fill=tk.X, pady=5)
        
        global_frame = tk.LabelFrame(right_frame, text="Global Settings", padx=10, pady=10)
        global_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.global_subdiv_var = tk.IntVar(value=10)
        tk.Scale(global_frame, from_=1, to=100, variable=self.global_subdiv_var, 
                orient=tk.HORIZONTAL, label="Default Subdivisions").pack(fill=tk.X)
        
        tk.Button(global_frame, text="Apply to All Connections", 
                 command=self.apply_global_subdivisions, bg="lightyellow").pack(fill=tk.X, pady=5)
        
    def setup_3d_view(self):
        main_frame = tk.Frame(self.tab_3d)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Mesh View", font=("Arial", 12, "bold")).pack()
        
        self.fig_3d = Figure(figsize=(8, 7))
        self.viewer_3d = Viewer3D(self.fig_3d, self.mesh_data)
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
        toolbar.update()
        
        self.canvas_3d.mpl_connect('button_press_event', self.on_3d_click)
        
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update 3D View", command=self.update_3d_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        mode_frame = tk.LabelFrame(right_frame, text="Selection Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.face_sel_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(mode_frame, text="Enable Face Selection", 
                      variable=self.face_sel_mode_var, 
                      command=self.toggle_face_selection_mode,
                      font=("Arial", 10, "bold")).pack()
        
        self.face_mode_label = tk.Label(mode_frame, text="Face selection disabled", 
                                        font=("Arial", 9), fg="gray")
        self.face_mode_label.pack(pady=5)
        
        info_frame = tk.LabelFrame(right_frame, text="Face Selection", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="Click faces to select", font=("Arial", 9, "italic")).pack()
        self.face_count_label = tk.Label(info_frame, text="Selected: 0 faces", fg="blue")
        self.face_count_label.pack(pady=5)
        
        tk.Button(info_frame, text="Clear Selection", command=self.clear_face_selection).pack(fill=tk.X)
        
        patch_frame = tk.LabelFrame(right_frame, text="Assign Patch", padx=10, pady=10)
        patch_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        tk.Label(patch_frame, text="Patch Name:").pack(anchor=tk.W)
        self.patch_name_entry = tk.Entry(patch_frame)
        self.patch_name_entry.pack(fill=tk.X, pady=2)
        
        tk.Label(patch_frame, text="Patch Type:").pack(anchor=tk.W, pady=(10, 0))
        self.patch_type_var = tk.StringVar(value="wall")
        
        patch_types = ["wall", "patch", "symmetry", "symmetryPlane", "wedge", "empty", "cyclic"]
        for ptype in patch_types:
            tk.Radiobutton(patch_frame, text=ptype, variable=self.patch_type_var, 
                          value=ptype).pack(anchor=tk.W)
        
        tk.Button(patch_frame, text="Assign to Selected Faces", 
                 command=self.assign_patch, bg="lightblue").pack(fill=tk.X, pady=10)
        
        list_frame = tk.LabelFrame(right_frame, text="Defined Patches", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.patch_listbox = tk.Listbox(list_frame)
        self.patch_listbox.pack(fill=tk.BOTH, expand=True)
        
    def setup_patch_view(self):
        main_frame = tk.Frame(self.tab_export)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Export to blockMeshDict", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        info_text = tk.Text(main_frame, height=15, width=80)
        info_text.pack(pady=10)
        info_text.insert("1.0", "Summary:\n\n")
        info_text.insert("end", "This will generate an OpenFOAM blockMeshDict file.\n\n")
        info_text.insert("end", "Current mesh:\n")
        info_text.insert("end", f"  Layers: {len(self.mesh_data.layers)}\n")
        info_text.insert("end", f"  Total points: {sum(len(pts) for pts in self.mesh_data.points.values())}\n")
        info_text.insert("end", f"  Patches defined: {len(self.mesh_data.patches)}\n")
        info_text.config(state=tk.DISABLED)
        
        self.export_info = info_text
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Generate & Preview", command=self.preview_blockmesh,
                 bg="lightblue", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save to File", command=self.save_blockmesh,
                 bg="lightgreen", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.preview_text = tk.Text(main_frame, height=20, width=100, font=("Courier", 9))
        scrollbar = tk.Scrollbar(main_frame, command=self.preview_text.yview)
        self.preview_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
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
        self.update_2d_plot()
    
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
            self.update_2d_plot()
        
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
        
        self.update_2d_plot()
    
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
            self.update_2d_plot()
        
    def add_point_manual(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            self.mesh_data.add_point(self.mesh_data.current_layer, x, y)
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            self.update_2d_plot()
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
        self.update_2d_plot()
        self.update_3d_view()
        
    def clear_selection(self):
        self.selected_points = []
        self.selection_label.config(text="Selected: None")
        self.update_2d_plot()
        
    def update_2d_plot(self):
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
            self.update_2d_plot()
            
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
        self.update_2d_plot()
        
    def update_3d_view(self):
        self.viewer_3d.mesh_data = self.mesh_data
        self.viewer_3d.update_view()
        self.canvas_3d.draw()
    
    def toggle_face_selection_mode(self):
        self.face_selection_mode = self.face_sel_mode_var.get()
        if self.face_selection_mode:
            self.face_mode_label.config(text="Face selection enabled - Click faces!", fg="green")
        else:
            self.face_mode_label.config(text="Face selection disabled", fg="gray")
        
    def on_3d_click(self, event):
        if event.inaxes != self.viewer_3d.ax:
            return
        
        if not self.face_selection_mode:
            return
        
        face_idx = self.viewer_3d.pick_face(event.xdata, event.ydata)
        if face_idx is not None:
            self.face_count_label.config(text=f"Selected: {len(self.viewer_3d.selected_faces)} faces")
            self.update_3d_view()
            
    def clear_face_selection(self):
        self.viewer_3d.clear_selection()
        self.face_count_label.config(text="Selected: 0 faces")
        self.update_3d_view()
        
    def assign_patch(self):
        name = self.patch_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Enter patch name")
            return
        
        patch_type = self.patch_type_var.get()
        selected = self.viewer_3d.get_selected_faces()
        
        if not selected:
            messagebox.showwarning("Warning", "No faces selected")
            return
        
        self.viewer_3d.assign_patch_to_selected(name, patch_type)
        self.mesh_data.add_patch(name, patch_type, selected)
        
        self.patch_listbox.insert(tk.END, f"{name} ({patch_type}) - {len(selected)} faces")
        self.patch_name_entry.delete(0, tk.END)
        self.clear_face_selection()
        
    def preview_blockmesh(self):
        exporter = BlockMeshExporter(self.mesh_data)
        content = exporter.generate_blockmesh_dict()
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content)
        self.preview_text.config(state=tk.DISABLED)
        
    def save_blockmesh(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("blockMeshDict", "blockMeshDict"), ("All files", "*.*")],
            initialfile="blockMeshDict"
        )
        
        if filename:
            exporter = BlockMeshExporter(self.mesh_data)
            exporter.save_to_file(filename)
            messagebox.showinfo("Success", f"Saved to {filename}")
    
    def save_to_json(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="mesh_project.json"
        )
        
        if filename:
            try:
                data = self.mesh_data.to_dict()
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Project saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def load_from_json(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.mesh_data.from_dict(data)
                
                self.update_layer_list()
                self.update_iso_checkboxes()
                self.update_2d_plot()
                self.update_3d_view()
                
                messagebox.showinfo("Success", f"Project loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
    
    def auto_save(self):
        try:
            data = self.mesh_data.to_dict()
            with open(self.temp_json_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
        
        self.root.after(30000, self.auto_save)
    
    def new_project(self):
        result = messagebox.askyesnocancel("New Project", 
                                          "Do you want to save the current project before starting a new one?")
        if result is None:
            return
        elif result:
            self.save_to_json()
        
        self.mesh_data = MeshData()
        self.selected_points = []
        self.iso_layers = []
        self.iso_mode = False
        self.iso_mode_var.set(False)
        
        self.update_layer_list()
        self.update_iso_checkboxes()
        self.update_2d_plot()
        self.update_3d_view()
        self.clear_face_selection()
        
        messagebox.showinfo("New Project", "Started a new project")
    
    def update_grid_3d_view(self):
        self.ax_grid_3d.clear()
        self.ax_grid_3d.set_xlabel('X')
        self.ax_grid_3d.set_ylabel('Y')
        self.ax_grid_3d.set_zlabel('Z')
        self.ax_grid_3d.set_title("3D Connection View")
        
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            z = self.mesh_data.layers[layer]
            for x, y in self.mesh_data.points[layer]:
                all_points.append((x, y, z))
        
        if not all_points:
            self.ax_grid_3d.text(0, 0, 0, "No points to display", ha='center', va='center')
            self.canvas_grid_3d.draw()
            return
        
        xs, ys, zs = zip(*all_points)
        self.ax_grid_3d.scatter(xs, ys, zs, c='red', marker='o', s=50)
        
        self.conn_listbox.delete(0, tk.END)
        conn_idx = 0
        
        for layer in self.mesh_data.layers:
            z = self.mesh_data.layers[layer]
            points = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points) and conn[1] < len(points):
                    p1 = points[conn[0]]
                    p2 = points[conn[1]]
                    self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z, z], 
                                       'b-', linewidth=2, picker=5)
                    self.conn_listbox.insert(tk.END, f"C{conn_idx}: {layer} [{conn[0]}-{conn[1]}]")
                    conn_idx += 1
        
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                p1 = self.mesh_data.points[layer1][idx1]
                p2 = self.mesh_data.points[layer2][idx2]
                self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 
                                   'g--', linewidth=2, picker=5)
                self.conn_listbox.insert(tk.END, f"C{conn_idx}: {layer1}[{idx1}] ↔ {layer2}[{idx2}]")
                conn_idx += 1
        
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            if len(points1) == len(points2):
                for j in range(len(points1)):
                    p1 = points1[j]
                    p2 = points2[j]
                    self.ax_grid_3d.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 
                                       'gray', linewidth=1, alpha=0.3, linestyle=':')
        
        self.canvas_grid_3d.draw()
    
    def on_grid_3d_click(self, event):
        pass
    
    def on_connection_select(self, event):
        sel = self.conn_listbox.curselection()
        if sel:
            conn_text = self.conn_listbox.get(sel[0])
            self.selected_conn_label.config(text=f"Selected: {conn_text}")
    
    def apply_subdivisions(self):
        sel = self.conn_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a connection first")
            return
        
        subdivs = self.subdiv_var.get()
        conn_text = self.conn_listbox.get(sel[0])
        messagebox.showinfo("Applied", f"Set {subdivs} subdivisions for {conn_text}")
    
    def apply_global_subdivisions(self):
        subdivs = self.global_subdiv_var.get()
        messagebox.showinfo("Applied", f"Set {subdivs} subdivisions for all connections")

if __name__ == "__main__":
    root = tk.Tk()
    app = MeshBuilderApp(root)
    root.mainloop()