"""
Grid Sizing Tab - Connection Subdivision Controls
"""
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class TabGridSizing:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.subdiv_var = tk.IntVar(value=10)
        self.global_subdiv_var = tk.IntVar(value=10)
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View
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
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update View", command=self.update_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        self._setup_selection_controls(right_frame)
        self._setup_grid_controls(right_frame)
        self._setup_global_controls(right_frame)
        
    def _setup_selection_controls(self, parent):
        sel_frame = tk.LabelFrame(parent, text="Connection Selection", padx=10, pady=10)
        sel_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(sel_frame, text="Click connections to select", font=("Arial", 9, "italic")).pack()
        
        self.conn_listbox = tk.Listbox(sel_frame, height=10, selectmode=tk.SINGLE)
        self.conn_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.conn_listbox.bind('<<ListboxSelect>>', self.on_connection_select)
        
        self.selected_conn_label = tk.Label(sel_frame, text="Selected: None", fg="blue")
        self.selected_conn_label.pack(pady=5)
    
    def _setup_grid_controls(self, parent):
        grid_frame = tk.LabelFrame(parent, text="Grid Subdivisions", padx=10, pady=10)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(grid_frame, text="Divisions for selected connection:").pack(anchor=tk.W)
        
        tk.Scale(grid_frame, from_=1, to=100, variable=self.subdiv_var, 
                orient=tk.HORIZONTAL, label="Subdivisions").pack(fill=tk.X, pady=5)
        
        tk.Button(grid_frame, text="Apply to Selected", 
                 command=self.apply_subdivisions, bg="lightblue").pack(fill=tk.X, pady=5)
    
    def _setup_global_controls(self, parent):
        global_frame = tk.LabelFrame(parent, text="Global Settings", padx=10, pady=10)
        global_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Scale(global_frame, from_=1, to=100, variable=self.global_subdiv_var, 
                orient=tk.HORIZONTAL, label="Default Subdivisions").pack(fill=tk.X)
        
        tk.Button(global_frame, text="Apply to All Connections", 
                 command=self.apply_global_subdivisions, bg="lightyellow").pack(fill=tk.X, pady=5)
    
    def update_view(self):
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
        
        # Draw connections within layers
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
        
        # Draw inter-layer connections
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
        
        # Draw auto-connections between adjacent layers
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