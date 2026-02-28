"""
Point Operations for 2D Editor Tab - UPDATED for new data structure
Handles point editing, adding, deleting operations using global point IDs
"""
import tkinter as tk
from tkinter import messagebox


def edit_point(self):
    """Edit the X,Y coordinates of selected point(s)"""
    # Check if we have selected points
    if not hasattr(self, 'selected_points') or len(self.selected_points) == 0:
        messagebox.showwarning("Warning", "No point selected. Select a point first.")
        return
    
    if len(self.selected_points) > 1:
        messagebox.showwarning("Warning", "Multiple points selected. Can only edit one at a time.")
        return
    
    point_id = self.selected_points[0]
    point_data = self.mesh_data.get_point(point_id)
    
    if point_data is None:
        messagebox.showerror("Error", "Could not find point data")
        return
    
    current_x = point_data['x']
    current_y = point_data['y']
    
    # Find which layer this point belongs to
    current_layer = None
    for layer_name, layer_data in self.mesh_data.layers.items():
        if point_id in layer_data.get('point_refs', []):
            current_layer = layer_name
            break
    
    # Create edit window
    win = tk.Toplevel(self.parent)
    win.title(f"Edit Point {point_id}")
    win.geometry("250x220")
    win.resizable(False, False)
    win.transient(self.parent)
    win.grab_set()
    win.attributes('-topmost', True)
    win.configure(bg='#252526')
    
    # Center
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (250 // 2)
    y = (win.winfo_screenheight() // 2) - (220 // 2)
    win.geometry(f"+{x}+{y}")
    
    # Frame
    frame = tk.Frame(win, bg='#252526', padx=15, pady=15)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Info
    layer_text = f" in {current_layer}" if current_layer else ""
    tk.Label(frame, text=f"Point {point_id}{layer_text}", 
            bg='#252526', fg='#4ec9b0',
            font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 10))
    
    # X entry
    x_frame = tk.Frame(frame, bg='#252526')
    x_frame.pack(fill=tk.X, pady=5)
    tk.Label(x_frame, text="X:", bg='#252526', fg='#d4d4d4',
            font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    x_var = tk.DoubleVar(value=current_x)
    x_entry = tk.Entry(x_frame, textvariable=x_var, bg='#2d2d2d', fg='#d4d4d4',
                      insertbackground='white', font=("Arial", 10),
                      highlightbackground='#3e3e42', width=12)
    x_entry.pack(side=tk.RIGHT)
    x_entry.bind("<FocusIn>", lambda e: x_entry.select_range(0, tk.END))
    
    # Y entry
    y_frame = tk.Frame(frame, bg='#252526')
    y_frame.pack(fill=tk.X, pady=5)
    tk.Label(y_frame, text="Y:", bg='#252526', fg='#d4d4d4',
            font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    y_var = tk.DoubleVar(value=current_y)
    y_entry = tk.Entry(y_frame, textvariable=y_var, bg='#2d2d2d', fg='#d4d4d4',
                      insertbackground='white', font=("Arial", 10),
                      highlightbackground='#3e3e42', width=12)
    y_entry.pack(side=tk.RIGHT)
    y_entry.bind("<FocusIn>", lambda e: y_entry.select_range(0, tk.END))
    
    # Warning about Z
    tk.Label(frame, text="Note: Z is controlled by layer", 
            bg='#252526', fg='#ce9178',
            font=("Arial", 8, "italic")).pack(anchor=tk.W, pady=(5, 0))
    
    # Buttons
    btn_frame = tk.Frame(frame, bg='#252526')
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    def save_and_close():
        new_x = x_var.get()
        new_y = y_var.get()
        # Update point coordinates (Z stays the same)
        point_data = self.mesh_data.get_point(point_id)
        if point_data:
            self.mesh_data.update_point(point_id, x=new_x, y=new_y)
        
        self.clear_selection()
        self.update_plot()
        messagebox.showinfo("Success", f"Point updated to ({new_x:.2f}, {new_y:.2f})")
        win.destroy()
    
    def delete_and_close():
        # Remove the point using mesh_data method
        self.mesh_data.remove_point(point_id)
        self.clear_selection()
        self.update_plot()
        messagebox.showinfo("Deleted", f"Point {point_id} deleted")
        win.destroy()
    
    # Save (green)
    tk.Button(btn_frame, text="💾 Save", command=save_and_close,
             bg='#4ec9b0', fg='#1e1e1e', font=("Arial", 9, "bold"),
             relief=tk.FLAT, activebackground='#3db89f',
             width=8).pack(side=tk.LEFT, padx=2)
    
    # Delete (red)
    tk.Button(btn_frame, text="🗑 Delete", command=delete_and_close,
             bg='#f44747', fg='white', font=("Arial", 9, "bold"),
             relief=tk.FLAT, activebackground='#d63636',
             width=8).pack(side=tk.LEFT, padx=2)
    
    # Cancel (gray X)
    tk.Button(btn_frame, text="✕", command=win.destroy,
             bg='#3e3e42', fg='white', font=("Arial", 9, "bold"),
             relief=tk.FLAT, activebackground='#555555',
             width=3).pack(side=tk.RIGHT, padx=2)


def add_point_manual(self):
    """Add point from manual X/Y entry fields"""
    try:
        x = float(self.x_entry.get())
        y = float(self.y_entry.get())
        # Add point to current layer (Z comes from layer)
        self.mesh_data.add_point(x, y, layer=self.mesh_data.current_layer)
        self.update_plot()
    except ValueError:
        messagebox.showerror("Error", "Enter valid numbers")


def delete_selected_point(self):
    """Delete the currently selected point (if exactly one is selected)"""
    if not hasattr(self, 'selected_points') or len(self.selected_points) == 0:
        messagebox.showwarning("Warning", "No point selected")
        return
    
    if len(self.selected_points) > 1:
        messagebox.showwarning("Warning", "Multiple points selected. Can only delete one at a time.")
        return
    
    point_id = self.selected_points[0]
    
    # Confirm deletion
    if messagebox.askyesno("Confirm Delete", f"Delete point {point_id}?"):
        self.mesh_data.remove_point(point_id)
        self.clear_selection()
        self.update_plot()
        messagebox.showinfo("Deleted", f"Point {point_id} deleted")


def clear_selection(self):
    """Clear point and connection selection"""
    self.selected_points = []
    self.selected_connection = None
    if hasattr(self, 'selection_label'):
        self.selection_label.config(text="Selected: None")
    self.update_plot()
