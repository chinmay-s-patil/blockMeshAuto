"""
Project Settings Tab - Configuration before building mesh
Modularized with separate sections for each setting group
"""
import tkinter as tk
from tkinter import messagebox


class TabProjectSettings:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        self.plane_var = tk.StringVar(value=self.mesh_data.sketch_plane)
        self.unit_var = tk.StringVar(value="m")
        self.sci_exponent_var = tk.StringVar(value="0")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main scrollable frame
        canvas = tk.Canvas(self.parent)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = tk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        self._create_title(main_frame)
        
        # Project Info Section
        self.project_info_section = ProjectInfoSection(main_frame, self.mesh_data)
        
        # Unit Selection Section
        self.unit_section = UnitSelectionSection(main_frame, self.unit_var, self.sci_exponent_var)
        
        # Sketch Plane Section
        self.sketch_plane_section = SketchPlaneSection(main_frame, self.mesh_data, self.plane_var)
        
        # Warnings Section
        self._setup_warnings(main_frame)
        
    def _create_title(self, parent):
        title_frame = tk.Frame(parent)
        title_frame.pack(pady=20)
        
        tk.Label(title_frame, text="Project Settings", 
                font=("Arial", 16, "bold")).pack()
        
        tk.Label(title_frame, text="Configure these settings before creating your mesh", 
                font=("Arial", 10, "italic"), fg="gray").pack(pady=(5, 0))
    
    def _setup_warnings(self, parent):
        warning_frame = tk.Frame(parent, bg="#fff3cd", relief=tk.RIDGE, bd=2)
        warning_frame.pack(fill=tk.X, pady=20)
        
        warning_label = tk.Label(warning_frame, 
                                text="⚠️ Warning: Changing the sketch plane will clear all existing geometry!",
                                font=("Arial", 10, "bold"), fg="#856404", bg="#fff3cd",
                                padx=10, pady=10)
        warning_label.pack()
    
    def update_display(self):
        """Update the display when data is loaded"""
        self.project_info_section.update_display()
        self.sketch_plane_section.update_display()
        # Units are stored in mesh_data now
        if hasattr(self.mesh_data, 'unit_system'):
            self.unit_var.set(self.mesh_data.unit_system)
        if hasattr(self.mesh_data, 'unit_sci_exponent'):
            self.sci_exponent_var.set(self.mesh_data.unit_sci_exponent)
    
    def save_all_settings(self):
        """Save all settings from all sections"""
        self.project_info_section.save_project_info()
        
        # Save unit settings
        self.mesh_data.unit_system = self.unit_var.get()
        self.mesh_data.unit_sci_exponent = self.sci_exponent_var.get()
        
        # Sketch plane is saved automatically on change
        

class ProjectInfoSection:
    """Project name and description section"""
    def __init__(self, parent, mesh_data):
        self.mesh_data = mesh_data
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        info_frame = tk.LabelFrame(parent, text="Project Information", 
                                   padx=20, pady=20, font=("Arial", 12, "bold"))
        info_frame.pack(fill=tk.X, pady=10)
        
        # Project name
        name_frame = tk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=5)
        tk.Label(name_frame, text="Project Name:", width=15, anchor=tk.W, 
                font=("Arial", 10)).pack(side=tk.LEFT)
        self.project_name_entry = tk.Entry(name_frame, width=40, font=("Arial", 10))
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_name_entry.pack(side=tk.LEFT, padx=5)
        
        # Description
        desc_frame = tk.Frame(info_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        tk.Label(desc_frame, text="Description:", width=15, anchor=tk.W, 
                font=("Arial", 10)).pack(side=tk.LEFT, anchor=tk.N)
        self.project_desc_text = tk.Text(desc_frame, width=40, height=3, font=("Arial", 10))
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)
        self.project_desc_text.pack(side=tk.LEFT, padx=5)
        
        # Save button
        tk.Button(info_frame, text="💾 Save Project Info", command=self.save_project_info,
                 bg="lightblue", font=("Arial", 10, "bold")).pack(pady=10)
    
    def save_project_info(self):
        self.mesh_data.project_name = self.project_name_entry.get()
        self.mesh_data.project_description = self.project_desc_text.get("1.0", tk.END).strip()
        messagebox.showinfo("Saved", "Project information saved!")
    
    def update_display(self):
        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_desc_text.delete("1.0", tk.END)
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)


class UnitSelectionSection:
    """Unit system selection section"""
    def __init__(self, parent, unit_var, sci_exponent_var):
        self.unit_var = unit_var
        self.sci_exponent_var = sci_exponent_var
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        unit_frame = tk.LabelFrame(parent, text="Unit System", 
                                   padx=20, pady=20, font=("Arial", 12, "bold"))
        unit_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(unit_frame, 
                text="Select the unit system for your geometry.\nThis affects the 'scale' parameter in blockMeshDict.",
                font=("Arial", 10), justify=tk.LEFT).pack(pady=(0, 15))
        
        # Standard units
        standard_frame = tk.LabelFrame(unit_frame, text="Standard Units", 
                                       padx=15, pady=10, font=("Arial", 10, "bold"))
        standard_frame.pack(fill=tk.X, pady=5)
        
        units = [
            ("Meters (m)", "m", "1.0 - Default OpenFOAM unit"),
            ("Centimeters (cm)", "cm", "0.01"),
            ("Millimeters (mm)", "mm", "0.001"),
        ]
        
        for label, value, description in units:
            frame = tk.Frame(standard_frame)
            frame.pack(anchor=tk.W, pady=3)
            
            rb = tk.Radiobutton(frame, text=label, variable=self.unit_var, 
                              value=value, font=("Arial", 10))
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=f"  → scale = {description}", 
                                 font=("Arial", 9), fg="gray")
            desc_label.pack(side=tk.LEFT)
        
        # Scientific notation
        sci_frame = tk.LabelFrame(unit_frame, text="Scientific Notation", 
                                  padx=15, pady=10, font=("Arial", 10, "bold"))
        sci_frame.pack(fill=tk.X, pady=5)
        
        tk.Radiobutton(sci_frame, text="Custom: 10^n", variable=self.unit_var, 
                      value="scientific", font=("Arial", 10)).pack(anchor=tk.W)
        
        exponent_frame = tk.Frame(sci_frame)
        exponent_frame.pack(fill=tk.X, pady=5, padx=20)
        
        tk.Label(exponent_frame, text="scale = 10^", font=("Arial", 10)).pack(side=tk.LEFT)
        
        self.exponent_entry = tk.Entry(exponent_frame, textvariable=self.sci_exponent_var, 
                                       width=8, font=("Arial", 10))
        self.exponent_entry.pack(side=tk.LEFT, padx=3)
        
        # Example
        example_label = tk.Label(exponent_frame, text="", 
                                font=("Arial", 9, "italic"), fg="blue")
        example_label.pack(side=tk.LEFT, padx=5)
        
        def update_example(*args):
            try:
                exp = float(self.sci_exponent_var.get())
                value = 10**exp
                example_label.config(text=f"= {value:.2e}")
            except:
                example_label.config(text="(invalid)")
        
        self.sci_exponent_var.trace('w', update_example)
        update_example()
        
        tk.Label(sci_frame, text="Examples: -3 for mm (0.001), -6 for μm, 3 for km", 
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, padx=20)
        
        # Current selection display
        self.unit_display = tk.Label(unit_frame, text="", 
                                     font=("Arial", 11, "bold"), fg="darkgreen")
        self.unit_display.pack(pady=(15, 5))
        
        # Update display when unit changes
        self.unit_var.trace('w', self.update_display)
        self.sci_exponent_var.trace('w', self.update_display)
        self.update_display()
    
    def update_display(self, *args):
        unit = self.unit_var.get()
        
        if unit == "m":
            text = "Current: Meters (scale = 1.0)"
        elif unit == "cm":
            text = "Current: Centimeters (scale = 0.01)"
        elif unit == "mm":
            text = "Current: Millimeters (scale = 0.001)"
        elif unit == "scientific":
            try:
                exp = float(self.sci_exponent_var.get())
                value = 10**exp
                text = f"Current: Scientific (scale = 10^{exp} = {value:.2e})"
            except:
                text = "Current: Scientific (invalid exponent)"
        else:
            text = f"Current: {unit}"
        
        self.unit_display.config(text=text)
    
    def get_scale_value(self):
        """Get the numerical scale value for blockMeshDict"""
        unit = self.unit_var.get()
        
        if unit == "m":
            return 1.0
        elif unit == "cm":
            return 0.01
        elif unit == "mm":
            return 0.001
        elif unit == "scientific":
            try:
                exp = float(self.sci_exponent_var.get())
                return 10**exp
            except:
                return 1.0
        else:
            return 1.0


class SketchPlaneSection:
    """Sketch plane selection section"""
    def __init__(self, parent, mesh_data, plane_var):
        self.mesh_data = mesh_data
        self.plane_var = plane_var
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        plane_frame = tk.LabelFrame(parent, text="Sketch Plane Selection", 
                                    padx=20, pady=20, font=("Arial", 12, "bold"))
        plane_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(plane_frame, 
                text="Select the plane to sketch your 2D geometry on.\nThe third axis will be the 'depth' direction for extrusion.",
                font=("Arial", 10), justify=tk.LEFT).pack(pady=(0, 15))
        
        # Radio buttons for plane selection
        plane_options_frame = tk.Frame(plane_frame)
        plane_options_frame.pack(pady=10)
        
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
    
    def update_display(self):
        self.plane_var.set(self.mesh_data.sketch_plane)
        self.plane_display.config(text=f"Current: {self.mesh_data.sketch_plane} plane")
        self.axis_display.config(text=self._get_axis_description())