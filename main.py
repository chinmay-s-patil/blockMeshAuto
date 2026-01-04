import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

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
        self.mode = "select"  # "add", "delete", or "select"
        self.iso_mode = False
        self.iso_layers = []  # For linking between layers
        
        self.setup_notebook()
        self.setup_2d_view()
        self.setup_3d_view()
        self.setup_patch_view()
        
    def setup_notebook(self):
        """Create tabbed interface for different sections"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: 2D Point & Connection Editor
        self.tab_2d = tk.Frame(self.notebook)
        self.notebook.add(self.tab_2d, text="1. Points & Connections")
        
        # Tab 2: 3D View & Patch Selection
        self.tab_3d = tk.Frame(self.notebook)
        self.notebook.add(self.tab_3d, text="2. 3D View & Patches")
        
        # Tab 3: Export
        self.tab_export = tk.Frame(self.notebook)
        self.notebook.add(self.tab_export, text="3. Export blockMeshDict")
        
    def setup_2d_view(self):
        """Setup 2D editing interface"""
        main_frame = tk.Frame(self.tab_2d)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Canvas
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="X-Y Plane View (2D)", font=("Arial", 12, "bold")).pack()
        
        self.fig_2d = Figure(figsize=(7, 7))
        self.ax_2d = self.fig_2d.add_subplot(111)
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, left_frame)
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas_2d.mpl_connect('button_press_event', self.on_2d_click)
        
        # Right - Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Mode controls
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
        
        # Layer management
        layer_frame = tk.LabelFrame(right_frame, text="Layers (Z-values)", padx=10, pady=10)
        layer_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.layer_listbox = tk.Listbox(layer_frame, height=6, selectmode=tk.EXTENDED)
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
        
        # Iso mode
        iso_frame = tk.Frame(layer_frame)
        iso_frame.pack(fill=tk.X, pady=5)
        
        self.iso_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(iso_frame, text="Iso Mode (Link 2 Layers)", 
                      variable=self.iso_mode_var, command=self.toggle_iso_mode).pack()
        
        self.iso_label = tk.Label(layer_frame, text="Select 2 layers for Iso Mode", 
                                 font=("Arial", 8, "italic"), fg="gray")
        self.iso_label.pack()
        
        # Manual point entry
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
        
        # Connection controls
        conn_frame = tk.LabelFrame(right_frame, text="Connections", padx=10, pady=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selection_label = tk.Label(conn_frame, text="Selected: None", fg="green")
        self.selection_label.pack()
        
        tk.Button(conn_frame, text="Create Connection", 
                 command=self.create_connection).pack(fill=tk.X, pady=2)
        tk.Button(conn_frame, text="Clear Selection", 
                 command=self.clear_selection).pack(fill=tk.X, pady=2)
        
        # Grid controls
        grid_frame = tk.LabelFrame(right_frame, text="Grid", padx=10, pady=10)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.subdiv_var = tk.IntVar(value=10)
        tk.Scale(grid_frame, from_=5, to=50, variable=self.subdiv_var, 
                orient=tk.HORIZONTAL, command=lambda x: self.update_2d_plot()).pack(fill=tk.X)
        
        self.update_2d_plot()
        
    def setup_3d_view(self):
        """Setup 3D visualization and patch selection"""
        main_frame = tk.Frame(self.tab_3d)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - 3D View
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Mesh View", font=("Arial", 12, "bold")).pack()
        
        self.fig_3d = Figure(figsize=(8, 7))
        self.viewer_3d = Viewer3D(self.fig_3d, self.mesh_data)
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar for zoom, pan, rotate
        toolbar_frame = tk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
        toolbar.update()
        
        self.canvas_3d.mpl_connect('button_press_event', self.on_3d_click)
        
        # Right - Patch Controls
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Update button
        tk.Button(right_frame, text="🔄 Update 3D View", command=self.update_3d_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        # Face selection info
        info_frame = tk.LabelFrame(right_frame, text="Face Selection", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="Click faces to select", font=("Arial", 9, "italic")).pack()
        self.face_count_label = tk.Label(info_frame, text="Selected: 0 faces", fg="blue")
        self.face_count_label.pack(pady=5)
        
        tk.Button(info_frame, text="Clear Selection", command=self.clear_face_selection).pack(fill=tk.X)
        
        # Patch type selection
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
        
        # Patch list
        list_frame = tk.LabelFrame(right_frame, text="Defined Patches", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.patch_listbox = tk.Listbox(list_frame)
        self.patch_listbox.pack(fill=tk.BOTH, expand=True)
        
    def setup_patch_view(self):
        """Setup export interface"""
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
        
    # Mode management
    def set_mode(self, mode):
        """Set current editing mode"""
        self.mode = mode
        
        # Reset all button states
        self.select_btn.config(relief=tk.RAISED, bg="SystemButtonFace")
        self.add_btn.config(relief=tk.RAISED, bg="SystemButtonFace")
        self.delete_btn.config(relief=tk.RAISED, bg="SystemButtonFace")
        
        # Set active button
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
        """Toggle iso mode for linking between layers"""
        self.iso_mode = self.iso_mode_var.get()
        if self.iso_mode:
            self.iso_label.config(text="Iso Mode Active", fg="green")
        else:
            self.iso_label.config(text="Select 2 layers for Iso Mode", fg="gray")
        self.update_2d_plot()
        
    # 2D View functions
    def on_2d_click(self, event):
        if event.inaxes != self.ax_2d:
            return
        
        x, y = event.xdata, event.ydata
        
        if self.iso_mode and len(self.iso_layers) == 2:
            # In iso mode, clicking adds inter-layer connection
            self.handle_iso_click(x, y)
            return
        
        layer = self.mesh_data.current_layer
        points = self.mesh_data.points[layer]
        
        # Check if clicking near existing point
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
        """Handle clicks in iso mode for inter-layer connections"""
        # Find which layer the click is closest to
        for layer in self.iso_layers:
            points = self.mesh_data.points[layer]
            for idx, (px, py) in enumerate(points):
                dist = np.sqrt((px - x)**2 + (py - y)**2)
                if dist < 0.5:
                    # Add to selection with layer info
                    point_ref = (layer, idx)
                    if point_ref not in self.selected_points:
                        self.selected_points.append(point_ref)
                        if len(self.selected_points) > 2:
                            self.selected_points.pop(0)
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
                    self.update_2d_plot()
                    return
        
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
        
        # Check if iso mode connection (between layers)
        if self.iso_mode and isinstance(self.selected_points[0], tuple):
            layer1, idx1 = self.selected_points[0]
            layer2, idx2 = self.selected_points[1]
            if layer1 != layer2:
                # Add inter-layer connection
                self.mesh_data.add_inter_layer_connection(layer1, idx1, layer2, idx2)
                messagebox.showinfo("Success", f"Connected {layer1}[{idx1}] to {layer2}[{idx2}]")
        else:
            # Same layer connection
            self.mesh_data.add_connection(self.mesh_data.current_layer, 
                                         self.selected_points[0], 
                                         self.selected_points[1])
        
        self.clear_selection()
        self.update_2d_plot()
        
    def clear_selection(self):
        self.selected_points = []
        self.selection_label.config(text="Selected: None")
        self.update_2d_plot()
        
    def update_2d_plot(self):
        self.ax_2d.clear()
        
        subdivs = self.subdiv_var.get()
        self.ax_2d.grid(True, alpha=0.3)
        self.ax_2d.set_xlim(-10, 10)
        self.ax_2d.set_ylim(-10, 10)
        self.ax_2d.set_xlabel("X")
        self.ax_2d.set_ylabel("Y")
        
        # Draw layers based on mode
        if self.iso_mode and len(self.iso_layers) == 2:
            # Show both layers
            self.ax_2d.set_title(f"Iso Mode: {self.iso_layers[0]} & {self.iso_layers[1]}")
            
            colors = ['red', 'blue']
            for i, layer in enumerate(self.iso_layers):
                points = self.mesh_data.points[layer]
                
                # Draw connections
                for conn in self.mesh_data.connections[layer]:
                    p1, p2 = points[conn[0]], points[conn[1]]
                    self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                                   color=colors[i], linewidth=1.5, alpha=0.7)
                
                # Draw points
                if points:
                    xs, ys = zip(*points)
                    self.ax_2d.plot(xs, ys, 'o', color=colors[i], markersize=8, 
                                   label=f"{layer}")
            
            # Draw inter-layer connections
            for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
                if layer1 in self.iso_layers and layer2 in self.iso_layers:
                    p1 = self.mesh_data.points[layer1][idx1]
                    p2 = self.mesh_data.points[layer2][idx2]
                    self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 
                                   'g--', linewidth=2, alpha=0.5)
            
            self.ax_2d.legend()
        else:
            # Single layer view
            layer = self.mesh_data.current_layer
            z = self.mesh_data.layers[layer]
            self.ax_2d.set_title(f"Layer: {layer} (z={z})")
            
            # Grid lines
            for i in range(-10, 11, max(1, 20 // subdivs)):
                self.ax_2d.axhline(y=i, color='gray', alpha=0.2, linewidth=0.5)
                self.ax_2d.axvline(x=i, color='gray', alpha=0.2, linewidth=0.5)
            
            # Connections
            points = self.mesh_data.points[layer]
            for conn in self.mesh_data.connections[layer]:
                p1, p2 = points[conn[0]], points[conn[1]]
                self.ax_2d.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-', linewidth=1.5)
            
            # Points
            if points:
                xs, ys = zip(*points)
                self.ax_2d.plot(xs, ys, 'ro', markersize=8)
                
                # Selected points
                for idx in self.selected_points:
                    if isinstance(idx, int) and idx < len(points):
                        self.ax_2d.plot(points[idx][0], points[idx][1], 'go', 
                                       markersize=12, alpha=0.5)
        
        self.canvas_2d.draw()
        
    # Layer functions
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            self.layer_listbox.insert(tk.END, f"{name} (z={z})")
            
    def on_layer_select(self, event):
        sel = self.layer_listbox.curselection()
        
        if self.iso_mode:
            # In iso mode, allow selecting 2 layers
            if len(sel) <= 2:
                self.iso_layers = []
                for idx in sel:
                    text = self.layer_listbox.get(idx)
                    name = text.split(" (z=")[0]
                    self.iso_layers.append(name)
                
                if len(self.iso_layers) == 2:
                    self.iso_label.config(text=f"Linking: {self.iso_layers[0]} ↔ {self.iso_layers[1]}", 
                                         fg="green")
                self.update_2d_plot()
        else:
            # Normal mode - single selection
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
    
    def duplicate_layer(self):
        """Duplicate the current layer"""
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
            # Copy points and connections
            self.mesh_data.points[name] = self.mesh_data.points[current].copy()
            self.mesh_data.connections[name] = self.mesh_data.connections[current].copy()
            self.update_layer_list()
            messagebox.showinfo("Success", f"Layer duplicated: {name}")
            
    def remove_layer(self):
        if len(self.mesh_data.layers) <= 1:
            messagebox.showwarning("Warning", "Cannot remove last layer")
            return
        
        self.mesh_data.remove_layer(self.mesh_data.current_layer)
        self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
        self.update_layer_list()
        self.update_2d_plot()
        
    # 3D View functions
    def update_3d_view(self):
        self.viewer_3d.mesh_data = self.mesh_data  # Ensure reference is updated
        self.viewer_3d.update_view()
        self.canvas_3d.draw()
        
    def on_3d_click(self, event):
        if event.inaxes != self.viewer_3d.ax:
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
        
    # Export functions
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

if __name__ == "__main__":
    root = tk.Tk()
    app = MeshBuilderApp(root)
    root.mainloop()