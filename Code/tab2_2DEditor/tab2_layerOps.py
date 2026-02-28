"""
Layer Operations for 2D Editor Tab - UPDATED for new data structure
Uses global point IDs instead of layer-based point lists
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import math


def update_layer_list(self):
    """Update the layer listbox display"""
    self.layer_listbox.delete(0, tk.END)
    # Sort layers by Z value
    sorted_layers = sorted(self.mesh_data.layers.items(), 
                          key=lambda x: x[1].get('z', 0))
    for name, layer_data in sorted_layers:
        z = layer_data.get('z', 0)
        num_points = len(layer_data.get('point_refs', []))
        self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")


def on_layer_select(self, event):
    """Handle layer selection from listbox"""
    sel = self.layer_listbox.curselection()
    
    if sel:
        text = self.layer_listbox.get(sel[0])
        name = text.split(" (z=")[0]
        self.mesh_data.current_layer = name
        self.layer_info.config(text=f"Current: {name}")
        self.clear_selection()
        self.update_plot()


def add_layer(self):
    """Add a new layer"""
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
    """Duplicate current layer with all its points and connections"""
    current = self.mesh_data.current_layer
    if not current:
        messagebox.showwarning("Warning", "No layer selected")
        return
    
    name = simpledialog.askstring("Duplicate Layer", 
                                    f"Name for duplicated layer:", 
                                    initialvalue=f"{current}_copy")
    if not name:
        return
    
    current_z = self.mesh_data.layers[current]['z']
    z = simpledialog.askfloat("Z Value", f"Z-value for {name}:", 
                                initialvalue=current_z + 1.0)
    if z is None:
        return
    
    # Create new layer
    self.mesh_data.add_layer(name, z)
    
    # Copy points from current layer to new layer and track ID mapping
    current_refs = self.mesh_data.layers[current].get('point_refs', [])
    id_mapping = {}  # Maps old point IDs to new point IDs
    
    for point_id in current_refs:
        point_data = self.mesh_data.get_point(point_id)
        if point_data:
            # Create new point at same X,Y but new Z
            new_id = self.mesh_data.add_point(point_data['x'], point_data['y'], z, name)
            id_mapping[point_id] = new_id
    
    # Recreate ALL connections between the new points (preserve topology completely)
    # We need to check ALL connections in the mesh, not just those in the original layer
    # because connections might reference points across layers
    connections_copied = 0
    
    # Get all connections and check which ones should be duplicated
    # A connection should be duplicated if BOTH endpoints are in the duplicated layer
    for conn_id, conn_data in list(self.mesh_data.connections.items()):
        p1 = conn_data.get('point1')
        p2 = conn_data.get('point2')
        # If both points of the connection were in the original layer,
        # create the same connection between their duplicates in the NEW layer
        if p1 in id_mapping and p2 in id_mapping:
            self.mesh_data.add_connection(id_mapping[p1], id_mapping[p2])
            connections_copied += 1
    
    self.update_layer_list()
    self.update_dual_view_buttons()
    messagebox.showinfo("Success", 
                       f"Layer duplicated: {name}\n"
                       f"{len(current_refs)} points copied\n"
                       f"{connections_copied} connections preserved")


def remove_layer(self):
    """Remove current layer (points are dereferenced, not deleted)"""
    if len(self.mesh_data.layers) <= 1:
        messagebox.showwarning("Warning", "Cannot remove last layer")
        return
    
    current = self.mesh_data.current_layer
    if messagebox.askyesno("Confirm", f"Remove layer '{current}'?\nPoints will remain in global storage."):
        self.mesh_data.remove_layer(current)
        self.mesh_data.current_layer = list(self.mesh_data.layers.keys())[0]
        self.update_layer_list()
        self.update_dual_view_buttons()
        self.update_plot()


def extrude_layer(self):
    """Extrude current layer to create a new layer with inter-layer connections only for overlapping points"""
    current = self.mesh_data.current_layer
    if not current:
        messagebox.showwarning("Warning", "No layer selected")
        return
    
    current_z = self.mesh_data.layers[current]['z']
    
    name = simpledialog.askstring("Extrude Layer", 
                                    f"Name for extruded layer:", 
                                    initialvalue=f"Layer {int(current_z+1)}")
    if not name:
        return
    
    z = simpledialog.askfloat("Z Value", f"Z-value for {name}:", 
                                initialvalue=current_z + 1.0)
    if z is None:
        return
    
    # Create new layer
    self.mesh_data.add_layer(name, z)
    
    # Copy points from current layer to new layer
    current_refs = list(self.mesh_data.layers[current].get('point_refs', []))
    id_mapping = {}  # Maps old point IDs to new point IDs
    
    # Store original point positions for overlap checking
    original_positions = {}  # point_id -> (x, y)
    
    for point_id in current_refs:
        point_data = self.mesh_data.get_point(point_id)
        if point_data:
            # Store original position
            original_positions[point_id] = (point_data['x'], point_data['y'])
            # Create new point at same X,Y but new Z
            new_id = self.mesh_data.add_point(point_data['x'], point_data['y'], z, name)
            id_mapping[point_id] = new_id
    
    # Create inter-layer connections ONLY for overlapping points (same X,Y)
    num_inter_connections = 0
    tolerance = 1e-6  # Small tolerance for floating point comparison
    
    for old_id, new_id in id_mapping.items():
        old_pos = original_positions[old_id]
        new_pos = (old_pos[0], old_pos[1])  # Same X,Y, different Z
        
        # Check if positions overlap (they should since we copied same X,Y)
        # Only connect if X and Y are the same (within tolerance)
        if abs(old_pos[0] - new_pos[0]) < tolerance and abs(old_pos[1] - new_pos[1]) < tolerance:
            self.mesh_data.add_connection(old_id, new_id)
            num_inter_connections += 1
    
    # Recreate intra-layer connections between the new points (preserve topology in new layer)
    # We look at all connections in the original layer and recreate them in the new layer
    intra_connections_copied = 0
    
    # Get the original layer's point set for quick lookup
    original_point_set = set(current_refs)
    
    # Check all connections - if both endpoints are in the original layer,
    # recreate that connection between the corresponding new points
    for conn_id, conn_data in list(self.mesh_data.connections.items()):
        p1 = conn_data.get('point1')
        p2 = conn_data.get('point2')
        
        # If both points of this connection are in the original layer
        if p1 in original_point_set and p2 in original_point_set:
            # Check if we have mappings for both (they should be in id_mapping)
            if p1 in id_mapping and p2 in id_mapping:
                # Create the same connection between the new points
                self.mesh_data.add_connection(id_mapping[p1], id_mapping[p2])
                intra_connections_copied += 1
    
    self.update_layer_list()
    self.update_dual_view_buttons()
    messagebox.showinfo("Success", 
                       f"Layer extruded: {name}\n"
                       f"{num_inter_connections} inter-layer connections (overlapping points)\n"
                       f"{intra_connections_copied} intra-layer connections preserved")


def edit_layer_z(self):
    """Edit the Z value of the currently selected layer"""
    current = self.mesh_data.current_layer
    if not current:
        messagebox.showwarning("Warning", "No layer selected")
        return
    
    current_z = self.mesh_data.layers[current]['z']
    
    # Create edit window
    edit_win = tk.Toplevel(self.parent)
    edit_win.title(f"Edit Z - {current}")
    edit_win.geometry("250x120")
    edit_win.resizable(False, False)
    edit_win.transient(self.parent)
    edit_win.grab_set()
    edit_win.attributes('-topmost', True)
    edit_win.configure(bg='#252526')
    
    # Center
    edit_win.update_idletasks()
    x = (edit_win.winfo_screenwidth() // 2) - (250 // 2)
    y = (edit_win.winfo_screenheight() // 2) - (120 // 2)
    edit_win.geometry(f"+{x}+{y}")
    
    # Main frame
    main_frame = tk.Frame(edit_win, bg='#252526', padx=15, pady=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Z entry
    z_frame = tk.Frame(main_frame, bg='#252526')
    z_frame.pack(fill=tk.X, pady=5)
    
    tk.Label(z_frame, text="Z Value:", bg='#252526', fg='#d4d4d4',
            font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    
    z_var = tk.DoubleVar(value=current_z)
    z_entry = tk.Entry(z_frame, textvariable=z_var, bg='#2d2d2d', fg='#d4d4d4',
                      insertbackground='white', font=("Arial", 10),
                      highlightbackground='#3e3e42', width=12)
    z_entry.pack(side=tk.RIGHT)
    z_entry.bind("<FocusIn>", lambda e: z_entry.select_range(0, tk.END))
    z_entry.select_range(0, tk.END)
    
    # Buttons
    btn_frame = tk.Frame(main_frame, bg='#252526')
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    def save_and_close():
        new_z = z_var.get()
        # Update layer Z and all points in layer
        self.mesh_data.set_layer_z(current, new_z)
        self.update_layer_list()
        self.update_plot()
        messagebox.showinfo("Success", f"Layer '{current}' Z-value updated to {new_z}")
        edit_win.destroy()
    
    # Save button (green)
    tk.Button(btn_frame, text="💾 Save", command=save_and_close,
             bg='#4ec9b0', fg='#1e1e1e', font=("Arial", 9, "bold"),
             relief=tk.FLAT, activebackground='#3db89f',
             width=8).pack(side=tk.LEFT, padx=2)
    
    # Cancel button (gray)
    tk.Button(btn_frame, text="✕", command=edit_win.destroy,
             bg='#3e3e42', fg='white', font=("Arial", 9, "bold"),
             relief=tk.FLAT, activebackground='#555555',
             width=3).pack(side=tk.RIGHT, padx=2)