"""
Project Settings Tab - Configuration before building mesh
Modularized with optimized horizontal layout for 1920x1080
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
        # Main frame without scrolling
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        self._create_title(main_frame)
        
        # Top row: Project Info and Unit System side-by-side
        top_row = tk.Frame(main_frame)
        top_row.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left: Project Info (40% width)
        left_panel = tk.Frame(top_row)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.project_info_section = ProjectInfoSection(left_panel, self.mesh_data)
        
        # Right: Unit Selection (60% width)
        right_panel = tk.Frame(top_row)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.unit_section = UnitSelectionSection(right_panel, self.unit_var, self.sci_exponent_var)
        
        # Bottom row: Sketch Plane (full width)
        bottom_row = tk.Frame(main_frame)
        bottom_row.pack(fill=tk.BOTH, pady=10)
        self.sketch_plane_section = SketchPlaneSection(bottom_row, self.mesh_data, self.plane_var)
        
        # Warning at bottom
        self._setup_warnings(main_frame)
        
    def _create_title(self, parent):
        title_frame = tk.Frame(parent)
        title_frame.pack(pady=(0, 10))
        
        tk.Label(title_frame, text="Project Settings", 
                font=("Arial", 16, "bold")).pack()
        
        tk.Label(title_frame, text="Configure these settings before creating your mesh", 
                font=("Arial", 10, "italic"), fg="gray").pack(pady=(2, 0))
    
    def _setup_warnings(self, parent):
        warning_frame = tk.Frame(parent, bg="#fff3cd", relief=tk.RIDGE, bd=2)
        warning_frame.pack(fill=tk.X, pady=(10, 0))
        
        warning_label = tk.Label(warning_frame, 
                                text="⚠️ Warning: Changing the sketch plane will clear all existing geometry!",
                                font=("Arial", 10, "bold"), fg="#856404", bg="#fff3cd",
                                padx=10, pady=8)
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
        """Save all settings from all sections (silent save for auto-save)"""
        self.project_info_section.save_project_info(silent=True)
        
        # Save unit settings
        self.mesh_data.unit_system = self.unit_var.get()
        self.mesh_data.unit_sci_exponent = self.sci_exponent_var.get()
        

class ProjectInfoSection:
    """Project name and description section"""
    def __init__(self, parent, mesh_data):
        self.mesh_data = mesh_data
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        info_frame = tk.LabelFrame(parent, text="Project Information", 
                                   padx=15, pady=15, font=("Arial", 11, "bold"))
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Project name
        name_frame = tk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=8)
        tk.Label(name_frame, text="Project Name:", width=12, anchor=tk.W, 
                font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.project_name_entry = tk.Entry(name_frame, font=("Arial", 10))
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Description
        desc_frame = tk.Frame(info_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        tk.Label(desc_frame, text="Description:", anchor=tk.W, 
                font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.project_desc_text = tk.Text(desc_frame, height=4, font=("Arial", 10))
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)
        self.project_desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Save button
        tk.Button(info_frame, text="💾 Save Project Info", command=self.save_project_info_manual,
                 bg="lightblue", font=("Arial", 10, "bold")).pack(pady=(10, 0))
    
    def save_project_info(self, silent=False):
        """Save project info, optionally without showing message"""
        self.mesh_data.project_name = self.project_name_entry.get()
        self.mesh_data.project_description = self.project_desc_text.get("1.0", tk.END).strip()
        if not silent:
            messagebox.showinfo("Saved", "Project information saved!")
    
    def save_project_info_manual(self):
        """Manual save with confirmation message"""
        self.save_project_info(silent=False)
    
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
                                   padx=15, pady=15, font=("Arial", 11, "bold"))
        unit_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(unit_frame, 
                text="Select the unit system for your geometry (affects 'scale' in blockMeshDict)",
                font=("Arial", 9), justify=tk.LEFT, fg="gray").pack(pady=(0, 10), anchor=tk.W)
        
        # Create two columns
        columns_frame = tk.Frame(unit_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column: Standard units
        left_col = tk.Frame(columns_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_col, text="Standard Units", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        units = [
            ("Meters (m)", "m", "scale = 1.0"),
            ("Centimeters (cm)", "cm", "scale = 0.01"),
            ("Millimeters (mm)", "mm", "scale = 0.001"),
        ]
        
        for label, value, description in units:
            frame = tk.Frame(left_col)
            frame.pack(anchor=tk.W, pady=2)
            
            rb = tk.Radiobutton(frame, text=label, variable=self.unit_var, 
                              value=value, font=("Arial", 9))
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=f"→ {description}", 
                                 font=("Arial", 8), fg="gray")
            desc_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Right column: Scientific notation
        right_col = tk.Frame(columns_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_col, text="Scientific Notation", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Radiobutton(right_col, text="Custom: 10^n", variable=self.unit_var, 
                      value="scientific", font=("Arial", 9)).pack(anchor=tk.W)
        
        exponent_frame = tk.Frame(right_col)
        exponent_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(exponent_frame, text="scale = 10^", font=("Arial", 9)).pack(side=tk.LEFT)
        
        self.exponent_entry = tk.Entry(exponent_frame, textvariable=self.sci_exponent_var, 
                                       width=6, font=("Arial", 9))
        self.exponent_entry.pack(side=tk.LEFT, padx=3)
        
        # Example
        self.example_label = tk.Label(exponent_frame, text="", 
                                font=("Arial", 9, "italic"), fg="blue")
        self.example_label.pack(side=tk.LEFT, padx=5)
        
        def update_example(*args):
            try:
                exp = float(self.sci_exponent_var.get())
                value = 10**exp
                self.example_label.config(text=f"= {value:.2e}")
            except:
                self.example_label.config(text="(invalid)")
        
        self.sci_exponent_var.trace('w', update_example)
        update_example()
        
        tk.Label(right_col, text="Examples: -3 for mm, -6 for μm, 3 for km", 
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, padx=0)
        
        # Current selection display
        self.unit_display = tk.Label(unit_frame, text="", 
                                     font=("Arial", 10, "bold"), fg="darkgreen",
                                     relief=tk.SUNKEN, padx=10, pady=5)
        self.unit_display.pack(pady=(10, 0), fill=tk.X)
        
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