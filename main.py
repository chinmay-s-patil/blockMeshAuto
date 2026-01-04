import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class MeshBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("2D Mesh Builder with Layers")
        self.root.geometry("1200x700")
        
        # Data storage
        self.layers = {"Layer 0": 0.0}  # {name: z_value}
        self.current_layer = "Layer 0"
        self.points = {}  # {layer_name: [(x, y), ...]}
        self.connections = {}  # {layer_name: [(idx1, idx2), ...]}
        self.selected_points = []  # For creating connections
        
        for layer in self.layers:
            self.points[layer] = []
            self.connections[layer] = []
        
        self.setup_ui()
        self.update_plot()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - X-Y Plane
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="X-Y Plane View", font=("Arial", 12, "bold")).pack()
        
        # Matplotlib figure
        self.fig = Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Click event for adding points
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        
        # Right side - Controls
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Layer management
        layer_frame = tk.LabelFrame(right_frame, text="Layers (Z-values)", padx=10, pady=10)
        layer_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.layer_listbox = tk.Listbox(layer_frame, height=8)
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        self.update_layer_list()
        
        layer_btn_frame = tk.Frame(layer_frame)
        layer_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(layer_btn_frame, text="Add Layer", command=self.add_layer).pack(side=tk.LEFT, padx=2)
        tk.Button(layer_btn_frame, text="Remove Layer", command=self.remove_layer).pack(side=tk.LEFT, padx=2)
        
        # Current layer info
        self.layer_info = tk.Label(layer_frame, text=f"Current: {self.current_layer}", 
                                   font=("Arial", 9, "bold"), fg="blue")
        self.layer_info.pack(pady=5)
        
        # Point and connection controls
        control_frame = tk.LabelFrame(right_frame, text="Points & Connections", padx=10, pady=10)
        control_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        tk.Label(control_frame, text="Click on canvas to add points", 
                font=("Arial", 9, "italic")).pack(pady=5)
        
        # Manual point addition
        manual_frame = tk.Frame(control_frame)
        manual_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(manual_frame, text="X:").grid(row=0, column=0)
        self.x_entry = tk.Entry(manual_frame, width=8)
        self.x_entry.grid(row=0, column=1, padx=2)
        
        tk.Label(manual_frame, text="Y:").grid(row=0, column=2)
        self.y_entry = tk.Entry(manual_frame, width=8)
        self.y_entry.grid(row=0, column=3, padx=2)
        
        tk.Button(manual_frame, text="Add Point", command=self.add_point_manual).grid(row=1, column=0, columnspan=4, pady=5)
        
        # Connection controls
        tk.Label(control_frame, text="Select 2 points to connect:", 
                font=("Arial", 9)).pack(pady=(10, 2))
        
        self.selection_label = tk.Label(control_frame, text="Selected: None", fg="green")
        self.selection_label.pack()
        
        conn_btn_frame = tk.Frame(control_frame)
        conn_btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(conn_btn_frame, text="Create Connection", 
                 command=self.create_connection).pack(side=tk.LEFT, padx=2)
        tk.Button(conn_btn_frame, text="Clear Selection", 
                 command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        
        # Subdivision controls
        subdiv_frame = tk.LabelFrame(right_frame, text="Mesh Subdivisions", padx=10, pady=10)
        subdiv_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        tk.Label(subdiv_frame, text="Grid Subdivisions:").pack()
        self.subdiv_var = tk.IntVar(value=10)
        tk.Scale(subdiv_frame, from_=5, to=50, variable=self.subdiv_var, 
                orient=tk.HORIZONTAL, command=lambda x: self.update_plot()).pack(fill=tk.X)
        
        # Action buttons
        action_frame = tk.Frame(right_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        tk.Button(action_frame, text="Clear All", command=self.clear_all, 
                 bg="#ff6b6b", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(action_frame, text="Export Data", command=self.export_data).pack(fill=tk.X, pady=2)
        
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        for layer_name, z_val in sorted(self.layers.items(), key=lambda x: x[1]):
            self.layer_listbox.insert(tk.END, f"{layer_name} (z={z_val})")
            
    def on_layer_select(self, event):
        selection = self.layer_listbox.curselection()
        if selection:
            layer_text = self.layer_listbox.get(selection[0])
            layer_name = layer_text.split(" (z=")[0]
            self.current_layer = layer_name
            self.layer_info.config(text=f"Current: {self.current_layer}")
            self.clear_selection()
            self.update_plot()
            
    def add_layer(self):
        layer_num = len(self.layers)
        layer_name = f"Layer {layer_num}"
        
        # Simple dialog for z-value
        z_value = tk.simpledialog.askfloat("New Layer", 
                                           f"Enter Z-value for {layer_name}:",
                                           initialvalue=float(layer_num))
        if z_value is not None:
            self.layers[layer_name] = z_value
            self.points[layer_name] = []
            self.connections[layer_name] = []
            self.update_layer_list()
            
    def remove_layer(self):
        if len(self.layers) <= 1:
            messagebox.showwarning("Warning", "Cannot remove the last layer!")
            return
        if self.current_layer in self.layers:
            del self.layers[self.current_layer]
            del self.points[self.current_layer]
            del self.connections[self.current_layer]
            self.current_layer = list(self.layers.keys())[0]
            self.update_layer_list()
            self.layer_info.config(text=f"Current: {self.current_layer}")
            self.update_plot()
            
    def on_canvas_click(self, event):
        if event.inaxes != self.ax:
            return
        
        x, y = event.xdata, event.ydata
        
        # Check if clicking near existing point (for selection)
        points = self.points[self.current_layer]
        for idx, (px, py) in enumerate(points):
            dist = np.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.5:  # Selection threshold
                if idx not in self.selected_points:
                    self.selected_points.append(idx)
                    if len(self.selected_points) > 2:
                        self.selected_points.pop(0)
                    self.selection_label.config(text=f"Selected: {self.selected_points}")
                    self.update_plot()
                return
        
        # Add new point
        self.points[self.current_layer].append((x, y))
        self.update_plot()
        
    def add_point_manual(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            self.points[self.current_layer].append((x, y))
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            self.update_plot()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for X and Y")
            
    def create_connection(self):
        if len(self.selected_points) != 2:
            messagebox.showwarning("Warning", "Please select exactly 2 points")
            return
        
        connection = tuple(sorted(self.selected_points))
        if connection not in self.connections[self.current_layer]:
            self.connections[self.current_layer].append(connection)
        self.clear_selection()
        self.update_plot()
        
    def clear_selection(self):
        self.selected_points = []
        self.selection_label.config(text="Selected: None")
        self.update_plot()
        
    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all points and connections?"):
            for layer in self.points:
                self.points[layer] = []
                self.connections[layer] = []
            self.clear_selection()
            self.update_plot()
            
    def update_plot(self):
        self.ax.clear()
        
        # Grid
        subdivs = self.subdiv_var.get()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        
        # Grid lines
        for i in range(-10, 11, 20 // subdivs):
            self.ax.axhline(y=i, color='gray', alpha=0.2, linewidth=0.5)
            self.ax.axvline(x=i, color='gray', alpha=0.2, linewidth=0.5)
        
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(f"Layer: {self.current_layer} (z={self.layers[self.current_layer]})")
        
        # Draw connections
        points = self.points[self.current_layer]
        for conn in self.connections[self.current_layer]:
            p1, p2 = points[conn[0]], points[conn[1]]
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-', linewidth=1.5)
        
        # Draw points
        if points:
            xs, ys = zip(*points)
            self.ax.plot(xs, ys, 'ro', markersize=8, label="Points")
            
            # Highlight selected points
            for idx in self.selected_points:
                if idx < len(points):
                    self.ax.plot(points[idx][0], points[idx][1], 'go', 
                               markersize=12, alpha=0.5)
        
        self.canvas.draw()
        
    def export_data(self):
        data = {
            "layers": self.layers,
            "points": self.points,
            "connections": self.connections
        }
        print("\n=== Mesh Data ===")
        print(f"Layers: {data['layers']}")
        print(f"\nPoints per layer:")
        for layer, pts in data['points'].items():
            print(f"  {layer}: {len(pts)} points")
        print(f"\nConnections per layer:")
        for layer, conns in data['connections'].items():
            print(f"  {layer}: {len(conns)} connections")
        messagebox.showinfo("Export", "Data printed to console!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MeshBuilder(root)
    root.mainloop()