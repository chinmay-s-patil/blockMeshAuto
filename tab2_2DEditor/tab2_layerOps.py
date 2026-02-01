import tkinter as tk
from tkinter import messagebox, simpledialog
import math

def extrude_layer(self):
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
    self.update_dual_view_buttons()
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
        self.update_dual_view_buttons()

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
        self.update_dual_view_buttons()
        messagebox.showinfo("Success", f"Layer duplicated: {name}")

def remove_layer(self):
    if len(self.mesh_data.layers) <= 1:
        messagebox.showwarning("Warning", "Cannot remove last layer")
        return
    
    self.mesh_data.remove_layer(self.mesh_data.current_layer)
    self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
    self.update_layer_list()
    self.update_dual_view_buttons()
    self.update_plot()
