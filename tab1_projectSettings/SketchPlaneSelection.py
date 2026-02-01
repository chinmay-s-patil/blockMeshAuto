import tkinter as tk
from tkinter import messagebox

class SketchPlaneSection:
    """Sketch plane selection section"""
    def __init__(self, parent, mesh_data, plane_var):
        self.mesh_data = mesh_data
        self.plane_var = plane_var
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        plane_frame = tk.LabelFrame(parent, text="Sketch Plane Selection", 
                                    padx=15, pady=15, font=("Arial", 11, "bold"))
        plane_frame.pack(fill=tk.BOTH)
        
        tk.Label(plane_frame, 
                text="Select the plane to sketch your 2D geometry on. The third axis will be the 'depth' direction for extrusion.",
                font=("Arial", 9), justify=tk.LEFT, fg="gray").pack(pady=(0, 10), anchor=tk.W)
        
        # Create three columns for plane options
        options_frame = tk.Frame(plane_frame)
        options_frame.pack(fill=tk.X)
        
        planes = [
            ("XY Plane (Z depth)", "XY", "Sketch in X-Y, extrude in Z"),
            ("YZ Plane (X depth)", "YZ", "Sketch in Y-Z, extrude in X"),
            ("ZX Plane (Y depth)", "ZX", "Sketch in Z-X, extrude in Y")
        ]
        
        for label, value, description in planes:
            col = tk.Frame(options_frame)
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            rb = tk.Radiobutton(col, text=label, variable=self.plane_var, 
                              value=value, font=("Arial", 10, "bold"),
                              command=self.on_plane_change)
            rb.pack(anchor=tk.W)
            
            desc_label = tk.Label(col, text=description, 
                                 font=("Arial", 8), fg="gray")
            desc_label.pack(anchor=tk.W, padx=(20, 0))
        
        # Status frame
        status_frame = tk.Frame(plane_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Current plane display
        self.plane_display = tk.Label(status_frame, 
                                      text=f"Current: {self.mesh_data.sketch_plane} plane",
                                      font=("Arial", 10, "bold"), fg="blue",
                                      relief=tk.SUNKEN, padx=10, pady=5)
        self.plane_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Axis orientation display
        self.axis_display = tk.Label(status_frame, 
                                     text=self._get_axis_description(),
                                     font=("Arial", 9), fg="darkgreen",
                                     relief=tk.SUNKEN, padx=10, pady=5)
        self.axis_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _get_axis_description(self):
        plane = self.mesh_data.sketch_plane
        if plane == "XY":
            return "3D View: X (horiz.) - Z (depth) - Y (vert.)"
        elif plane == "YZ":
            return "3D View: Y (horiz.) - X (depth) - Z (vert.)"
        elif plane == "ZX":
            return "3D View: Z (horiz.) - Y (depth) - X (vert.)"
        return ""
    
    def on_plane_change(self):
        new_plane = self.plane_var.get()
        
        # Check if there's existing geometry
        has_geometry = False
        for layer in self.mesh_data.points.values():
            if len(layer) > 0:
                has_geometry = True
                break
        
        if has_geometry and new_plane != self.mesh_data.sketch_plane:
            result = messagebox.askyesno(
                "Change Sketch Plane",
                "Changing the sketch plane will clear all existing geometry.\n\n"
                "Do you want to continue?",
                icon='warning'
            )
            
            if not result:
                # Revert to previous selection
                self.plane_var.set(self.mesh_data.sketch_plane)
                return
        
        # Update sketch plane
        self.mesh_data.sketch_plane = new_plane
        self.plane_display.config(text=f"Current: {new_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
        
        # Clear geometry if changed
        if has_geometry:
            self.mesh_data.clear_all()
            messagebox.showinfo("Geometry Cleared", 
                              "All geometry has been cleared due to plane change.")
    
    def update_display(self):
        self.plane_var.set(self.mesh_data.sketch_plane)
        self.plane_display.config(text=f"Current: {self.mesh_data.sketch_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
