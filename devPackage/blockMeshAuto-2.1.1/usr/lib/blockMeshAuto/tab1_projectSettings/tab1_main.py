"""
Project Settings Tab - Configuration before building mesh
Dark Mode Edition - Uses new JSON data structure
"""
import tkinter as tk
from tkinter import messagebox

class TabProjectSettings:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Dark mode colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f44747',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'border': '#3e3e42',
            'axis': '#6e6e6e'
        }
        
        # Create StringVars linked to mesh_data Specs
        self.plane_var = tk.StringVar(value=self.mesh_data.sketch_plane)
        self.unit_var = tk.StringVar(value=self.mesh_data.unit_system)
        self.sci_exponent_var = tk.StringVar(value=self.mesh_data.unit_sci_exponent)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Unified Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(header_frame, text="1. Project Settings", 
                font=("Segoe UI", 14, "bold"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        tk.Label(header_frame, text="Configure these settings before creating your mesh", 
                font=("Segoe UI", 10, "italic"), fg=self.colors['axis'],
                bg=self.colors['bg']).pack(side=tk.LEFT, padx=15, pady=(4,0))
        
        # Top row: Project Info and Unit System side-by-side
        top_row = tk.Frame(main_frame, bg=self.colors['bg'])
        top_row.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left: Project Info (40% width)
        left_panel = tk.Frame(top_row, bg=self.colors['bg'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self._setup_project_info(left_panel)
        
        # Right: Unit Selection (60% width)
        right_panel = tk.Frame(top_row, bg=self.colors['bg'])
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._setup_unit_selection(right_panel)
        
        # Bottom row: Sketch Plane (full width)
        bottom_row = tk.Frame(main_frame, bg=self.colors['bg'])
        bottom_row.pack(fill=tk.BOTH, pady=10)
        self._setup_sketch_plane(bottom_row)
        
        # Warning at bottom
        self._setup_warnings(main_frame)
        

    
    def _setup_project_info(self, parent):
        """Project Information section - saves to Specs"""
        info_frame = tk.LabelFrame(parent, text="Project Information", 
                                   padx=15, pady=15, font=("Arial", 11, "bold"),
                                   bg=self.colors['secondary'], fg=self.colors['fg'])
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Project name
        name_frame = tk.Frame(info_frame, bg=self.colors['secondary'])
        name_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(name_frame, text="Project Name:", width=12, anchor=tk.W, 
                font=("Arial", 10), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(side=tk.TOP, anchor=tk.W)
        
        self.project_name_entry = tk.Entry(name_frame, font=("Arial", 10),
                                          bg=self.colors['bg'], fg=self.colors['fg'],
                                          insertbackground=self.colors['fg'],
                                          relief=tk.FLAT, highlightthickness=1,
                                          highlightbackground=self.colors['border'])
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Description
        desc_frame = tk.Frame(info_frame, bg=self.colors['secondary'])
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        
        tk.Label(desc_frame, text="Description:", anchor=tk.W, 
                font=("Arial", 10), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(side=tk.TOP, anchor=tk.W)
        
        self.project_desc_text = tk.Text(desc_frame, height=4, font=("Arial", 10),
                                        bg=self.colors['bg'], fg=self.colors['fg'],
                                        insertbackground=self.colors['fg'],
                                        relief=tk.FLAT, highlightthickness=1,
                                        highlightbackground=self.colors['border'])
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)
        self.project_desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Save button
        tk.Button(info_frame, text="💾 Save Project Info", command=self.save_project_info_manual,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 10, "bold"), relief=tk.FLAT, cursor='hand2',
                 activebackground=self.colors['accent'], activeforeground=self.colors['fg']).pack(pady=(10, 0))
    
    def _setup_unit_selection(self, parent):
        """Unit System section - saves to Specs"""
        unit_frame = tk.LabelFrame(parent, text="Unit System", 
                                   padx=15, pady=15, font=("Arial", 11, "bold"),
                                   bg=self.colors['secondary'], fg=self.colors['fg'])
        unit_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(unit_frame, 
                text="Select the unit system for your geometry (affects 'scale' in blockMeshDict)",
                font=("Arial", 9), justify=tk.LEFT, fg=self.colors['fg'],
                bg=self.colors['secondary']).pack(pady=(0, 10), anchor=tk.W)
        
        # Create two columns
        columns_frame = tk.Frame(unit_frame, bg=self.colors['secondary'])
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column: Standard units
        left_col = tk.Frame(columns_frame, bg=self.colors['secondary'])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_col, text="Standard Units", font=("Arial", 10, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        units = [
            ("Meters (m)", "m", "scale = 1.0"),
            ("Centimeters (cm)", "cm", "scale = 0.01"),
            ("Millimeters (mm)", "mm", "scale = 0.001"),
        ]
        
        for label, value, description in units:
            self._create_radio_button(left_col, label, value, description, self.unit_var)
        
        # Right column: Scientific notation
        right_col = tk.Frame(columns_frame, bg=self.colors['secondary'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_col, text="Scientific Notation", font=("Arial", 10, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        self._create_radio_button(right_col, "Custom: 10^n", "scientific", "", self.unit_var)
        
        exponent_frame = tk.Frame(right_col, bg=self.colors['secondary'])
        exponent_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(exponent_frame, text="scale = 10^", font=("Arial", 9),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        self.exponent_entry = tk.Entry(exponent_frame, textvariable=self.sci_exponent_var, 
                                       width=6, font=("Arial", 9), bg=self.colors['bg'],
                                       fg=self.colors['fg'], insertbackground=self.colors['fg'],
                                       relief=tk.FLAT, highlightthickness=1,
                                       highlightbackground=self.colors['border'])
        self.exponent_entry.pack(side=tk.LEFT, padx=3)
        
        self.example_label = tk.Label(exponent_frame, text="", 
                                font=("Arial", 9, "italic"), fg=self.colors['accent'],
                                bg=self.colors['secondary'])
        self.example_label.pack(side=tk.LEFT, padx=5)
        
        # Update example when exponent changes
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
                font=("Arial", 8), fg=self.colors['fg'],
                bg=self.colors['secondary']).pack(anchor=tk.W, padx=0)
        
        # Current selection display
        self.unit_display = tk.Label(unit_frame, text="", 
                                     font=("Arial", 10, "bold"), fg=self.colors['success'],
                                     bg=self.colors['bg'], relief=tk.FLAT,
                                     padx=10, pady=5, highlightthickness=1,
                                     highlightbackground=self.colors['border'])
        self.unit_display.pack(pady=(10, 0), fill=tk.X)
        
        # Update display when unit changes
        self.unit_var.trace('w', self._update_unit_display)
        self.sci_exponent_var.trace('w', self._update_unit_display)
        self._update_unit_display()
    
    def _create_radio_button(self, parent, label, value, description, variable):
        """Create a custom radio button"""
        container = tk.Frame(parent, bg=self.colors['secondary'], cursor='hand2')
        container.pack(anchor=tk.W, pady=2, fill=tk.X)
        
        # Radio indicator (canvas circle)
        indicator = tk.Canvas(container, width=16, height=16, bg=self.colors['secondary'],
                             highlightthickness=0)
        indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        outer_circle = indicator.create_oval(2, 2, 14, 14, outline=self.colors['fg'], width=2)
        inner_circle = indicator.create_oval(5, 5, 11, 11, fill='', outline='')
        
        # Text
        if description:
            text_frame = tk.Frame(container, bg=self.colors['secondary'])
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            lbl = tk.Label(text_frame, text=label, font=("Arial", 9),
                          bg=self.colors['secondary'], fg=self.colors['fg'])
            lbl.pack(side=tk.LEFT)
            
            desc_lbl = tk.Label(text_frame, text=f"→ {description}", 
                               font=("Arial", 8), fg=self.colors['fg'],
                               bg=self.colors['secondary'])
            desc_lbl.pack(side=tk.LEFT, padx=(5, 0))
            
            # Bind clicks
            lbl.bind('<Button-1>', lambda e: variable.set(value))
            desc_lbl.bind('<Button-1>', lambda e: variable.set(value))
        else:
            lbl = tk.Label(container, text=label, font=("Arial", 9),
                          bg=self.colors['secondary'], fg=self.colors['fg'])
            lbl.pack(side=tk.LEFT)
            lbl.bind('<Button-1>', lambda e: variable.set(value))
        
        # Bind clicks
        container.bind('<Button-1>', lambda e: variable.set(value))
        indicator.bind('<Button-1>', lambda e: variable.set(value))
        
        # Update appearance when variable changes
        def update_appearance(*args):
            if variable.get() == value:
                indicator.itemconfig(inner_circle, fill=self.colors['accent'])
            else:
                indicator.itemconfig(inner_circle, fill='')
        
        variable.trace('w', update_appearance)
        update_appearance()
    
    def _update_unit_display(self, *args):
        """Update the unit display label"""
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
    
    def _setup_sketch_plane(self, parent):
        """Sketch Plane section - saves to Specs"""
        plane_frame = tk.LabelFrame(parent, text="Sketch Plane Selection", 
                                    padx=15, pady=15, font=("Arial", 11, "bold"),
                                    bg=self.colors['secondary'], fg=self.colors['fg'])
        plane_frame.pack(fill=tk.BOTH)
        
        tk.Label(plane_frame, 
                text="Select the plane to sketch your 2D geometry on. The third axis will be the 'depth' direction for extrusion.",
                font=("Arial", 9), justify=tk.LEFT, fg=self.colors['fg'],
                bg=self.colors['secondary']).pack(pady=(0, 10), anchor=tk.W)
        
        # Create three columns for plane options
        options_frame = tk.Frame(plane_frame, bg=self.colors['secondary'])
        options_frame.pack(fill=tk.X)
        
        plane_options = [
            ("XY Plane (Z depth)", "XY", "Sketch in X-Y, extrude in Z"),
            ("YZ Plane (X depth)", "YZ", "Sketch in Y-Z, extrude in X"),
            ("ZX Plane (Y depth)", "ZX", "Sketch in Z-X, extrude in Y")
        ]
        
        for label, value, description in plane_options:
            col = tk.Frame(options_frame, bg=self.colors['secondary'])
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self._create_plane_radiobutton(col, label, value, description)
        
        # Status frame
        status_frame = tk.Frame(plane_frame, bg=self.colors['secondary'])
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Current plane display
        self.plane_display = tk.Label(status_frame, 
                                      text=f"Current: {self.mesh_data.sketch_plane} plane",
                                      font=("Arial", 10, "bold"), fg=self.colors['success'],
                                      bg=self.colors['bg'], relief=tk.FLAT,
                                      padx=10, pady=5, highlightthickness=1,
                                      highlightbackground=self.colors['border'])
        self.plane_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Axis orientation display
        self.axis_display = tk.Label(status_frame, 
                                     text=self._get_axis_description(),
                                     font=("Arial", 9), fg=self.colors['accent'],
                                     bg=self.colors['bg'], relief=tk.FLAT,
                                     padx=10, pady=5, highlightthickness=1,
                                     highlightbackground=self.colors['border'])
        self.axis_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Trace plane changes
        self.plane_var.trace('w', self._on_plane_change)
    
    def _create_plane_radiobutton(self, parent, label, value, description):
        """Create a custom radio button for plane selection"""
        container = tk.Frame(parent, bg=self.colors['secondary'], cursor='hand2')
        container.pack(fill=tk.X, pady=2)
        
        # Radio indicator (canvas circle)
        indicator = tk.Canvas(container, width=16, height=16, bg=self.colors['secondary'],
                             highlightthickness=0)
        indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        outer_circle = indicator.create_oval(2, 2, 14, 14, outline=self.colors['fg'], width=2)
        inner_circle = indicator.create_oval(5, 5, 11, 11, fill='', outline='')
        
        # Label
        text_frame = tk.Frame(container, bg=self.colors['secondary'])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        lbl = tk.Label(text_frame, text=label, font=("Arial", 10, "bold"),
                      bg=self.colors['secondary'], fg=self.colors['fg'])
        lbl.pack(anchor=tk.W)
        
        desc_lbl = tk.Label(text_frame, text=description, font=("Arial", 8),
                           bg=self.colors['secondary'], fg=self.colors['fg'])
        desc_lbl.pack(anchor=tk.W)
        
        # Click handler
        def on_click(event=None):
            self.plane_var.set(value)
        
        container.bind('<Button-1>', on_click)
        indicator.bind('<Button-1>', on_click)
        lbl.bind('<Button-1>', on_click)
        desc_lbl.bind('<Button-1>', on_click)
        
        # Update appearance when plane_var changes
        def update_appearance(*args):
            if self.plane_var.get() == value:
                indicator.itemconfig(inner_circle, fill=self.colors['accent'])
            else:
                indicator.itemconfig(inner_circle, fill='')
        
        self.plane_var.trace('w', update_appearance)
        update_appearance()
    
    def _get_axis_description(self):
        plane = self.plane_var.get()
        if plane == "XY":
            return "3D View: X (horiz.) - Z (depth) - Y (vert.)"
        elif plane == "YZ":
            return "3D View: Y (horiz.) - X (depth) - Z (vert.)"
        elif plane == "ZX":
            return "3D View: Z (horiz.) - Y (depth) - X (vert.)"
        return ""
    
    def _on_plane_change(self, *args):
        """Handle sketch plane change"""
        new_plane = self.plane_var.get()
        
        # Check if geometry exists
        has_geometry = len(self.mesh_data.points) > 0
        
        if has_geometry and new_plane != self.mesh_data.sketch_plane:
            result = messagebox.askyesno(
                "Change Sketch Plane",
                "Changing the sketch plane will clear all existing geometry.\n\n"
                "Do you want to continue?",
                icon='warning'
            )
            
            if not result:
                self.plane_var.set(self.mesh_data.sketch_plane)
                return
            
            # Clear geometry
            self.mesh_data.clear_all()
            messagebox.showinfo("Geometry Cleared", 
                              "All geometry has been cleared due to plane change.")
        
        # Update mesh_data
        self.mesh_data.sketch_plane = new_plane
        self.plane_display.config(text=f"Current: {new_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
    
    def _setup_warnings(self, parent):
        """Setup warning message"""
        warning_frame = tk.Frame(parent, bg=self.colors['warning'], relief=tk.FLAT, bd=2,
                                highlightthickness=2, highlightbackground=self.colors['error'])
        warning_frame.pack(fill=tk.X, pady=(10, 0))
        
        warning_label = tk.Label(warning_frame, 
                                text="⚠️ Warning: Changing the sketch plane will clear all existing geometry!",
                                font=("Arial", 10, "bold"), fg=self.colors['bg'],
                                bg=self.colors['warning'], padx=10, pady=8)
        warning_label.pack()
    
    def save_project_info(self, silent=False):
        """Save project info to mesh_data (Specs)"""
        self.mesh_data.project_name = self.project_name_entry.get()
        self.mesh_data.project_description = self.project_desc_text.get("1.0", tk.END).strip()
        self.mesh_data.unit_system = self.unit_var.get()
        self.mesh_data.unit_sci_exponent = self.sci_exponent_var.get()
        if not silent:
            messagebox.showinfo("Saved", "Project information saved!")
    
    def save_project_info_manual(self):
        """Manual save with confirmation"""
        self.save_project_info(silent=False)
    
    def save_all_settings(self):
        """Save all settings (called by auto-save)"""
        self.save_project_info(silent=True)
    
    def update_display(self):
        """Update display when data is loaded from JSON"""
        # Update Project Info
        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, self.mesh_data.project_name)
        self.project_desc_text.delete("1.0", tk.END)
        self.project_desc_text.insert("1.0", self.mesh_data.project_description)
        
        # Update Unit Selection
        self.unit_var.set(self.mesh_data.unit_system)
        self.sci_exponent_var.set(self.mesh_data.unit_sci_exponent)
        
        # Update Sketch Plane
        self.plane_var.set(self.mesh_data.sketch_plane)
        self.plane_display.config(text=f"Current: {self.mesh_data.sketch_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
