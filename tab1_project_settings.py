"""
Project Settings Tab - Configuration before building mesh
"""
import tkinter as tk
from tkinter import messagebox


class TabProjectSettings:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Project Settings", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        tk.Label(main_frame, text="Configure these settings before creating your mesh", 
                font=("Arial", 10, "italic"), fg="gray").pack(pady=(0, 30))
        
        # Sketch Plane Selection
        self._setup_sketch_plane(main_frame)
        
        # Project Info
        self._setup_project_info(main_frame)
        
        # Warnings
        self._setup_warnings(main_frame)
        
    def _setup_sketch_plane(self, parent):
        plane_frame = tk.LabelFrame(parent, text="Sketch Plane Selection", 
                                    padx=20, pady=20, font=("Arial", 12, "bold"))
        plane_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(plane_frame, 
                text="Select the plane to sketch your 2D geometry on.\nThe third axis will be the 'depth' direction for extrusion.",
                font=("Arial", 10), justify=tk.LEFT).pack(pady=(0, 15))
        
        # Radio buttons for plane selection
        plane_options_frame = tk.Frame(plane_frame)
        plane_options_frame.pack(pady=10)
        
        self.plane_var = tk.StringVar(value=self.mesh_data.sketch_plane)
        
        planes = [
            ("XY Plane (Z depth)", "XY", "Sketch in X-Y, extrude in Z direction (default)"),
            ("YZ Plane (X depth)", "YZ", "Sketch in Y-Z, extrude in X direction"),
            ("ZX Plane (Y depth)", "ZX", "Sketch in Z-X, extrude in Y direction")
        ]
        
        for label, value, description in planes:
            frame = tk.Frame(plane_options_frame)
            frame.pack(anchor=tk.W, pady=5)
            
            rb = tk.Radiobutton(frame, text=label, variable=self.plane_var, 
                              value=value, font=("Arial", 11, "bold"),
                              command=self.on_plane_change)
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=f"  ({description})", 
                                 font=("Arial", 9), fg="gray")
            desc_label.pack(side=tk.LEFT)
        
        # Current plane display
        self.plane_display = tk.Label(plane_frame, 
                                      text=f"Current: {self.mesh_data.sketch_plane} plane",
                                      font=("Arial", 11, "bold"), fg="blue")
        self.plane_display.pack(pady=(15, 5))
        
        # Axis orientation display
        self.axis_display = tk.Label(plane_frame, 
                                     text=self._get_axis_description(),
                                     font=("Arial", 9), fg="darkgreen")
        self.axis_display.pack(pady=5)
        
    def _setup_project_info(self, parent):
        info_frame = tk.LabelFrame(parent, text="Project Information (Optional)", 
                                   padx=20, pady=20, font=("Arial", 12, "bold"))
        info_frame.pack(fill=tk.X, pady=10)
        
        # Project name
        name_frame = tk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=5)
        tk.Label(name_frame, text="Project Name:", width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.project_name_entry = tk.Entry(name_frame, width=40)
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_name_entry.pack(side=tk.LEFT, padx=5)
        
        # Description
        desc_frame = tk.Frame(info_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        tk.Label(desc_frame, text="Description:", width=15, anchor=tk.W).pack(side=tk.LEFT, anchor=tk.N)
        self.project_desc_text = tk.Text(desc_frame, width=40, height=3)
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)
        self.project_desc_text.pack(side=tk.LEFT, padx=5)
        
        # Save button
        tk.Button(info_frame, text="Save Project Info", command=self.save_project_info,
                 bg="lightblue", font=("Arial", 10)).pack(pady=10)
        
    def _setup_warnings(self, parent):
        warning_frame = tk.Frame(parent, bg="#fff3cd", relief=tk.RIDGE, bd=2)
        warning_frame.pack(fill=tk.X, pady=20)
        
        warning_label = tk.Label(warning_frame, 
                                text="⚠️ Warning: Changing the sketch plane will clear all existing geometry!",
                                font=("Arial", 10, "bold"), fg="#856404", bg="#fff3cd",
                                padx=10, pady=10)
        warning_label.pack()
        
    def _get_axis_description(self):
        plane = self.mesh_data.sketch_plane
        if plane == "XY":
            return "3D View: X (horizontal) - Z (depth) - Y (vertical)"
        elif plane == "YZ":
            return "3D View: Y (horizontal) - X (depth) - Z (vertical)"
        elif plane == "ZX":
            return "3D View: Z (horizontal) - Y (depth) - X (vertical)"
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
    
    def save_project_info(self):
        self.mesh_data.project_name = self.project_name_entry.get()
        self.mesh_data.project_description = self.project_desc_text.get("1.0", tk.END).strip()
        messagebox.showinfo("Saved", "Project information saved!")
    
    def update_display(self):
        """Update the display when data is loaded"""
        self.plane_var.set(self.mesh_data.sketch_plane)
        self.plane_display.config(text=f"Current: {self.mesh_data.sketch_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_desc_text.delete("1.0", tk.END)
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)