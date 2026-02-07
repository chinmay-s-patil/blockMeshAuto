import tkinter as tk
from tkinter import messagebox

class SketchPlaneSection:
    """Sketch plane selection section - Dark Mode with custom radio buttons"""
    def __init__(self, parent, mesh_data, plane_var, colors=None):
        self.mesh_data = mesh_data
        self.plane_var = plane_var
        self.colors = colors or {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'warning': '#ce9178',
            'error': '#f44747',
            'success': '#4ec9b0',
            'border': '#3e3e42'
        }
        self.radio_buttons = []  # Store references to custom radio buttons
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
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
        
        self.plane_options = [
            ("XY Plane (Z depth)", "XY", "Sketch in X-Y, extrude in Z"),
            ("YZ Plane (X depth)", "YZ", "Sketch in Y-Z, extrude in X"),
            ("ZX Plane (Y depth)", "ZX", "Sketch in Z-X, extrude in Y")
        ]
        
        for label, value, description in self.plane_options:
            col = tk.Frame(options_frame, bg=self.colors['secondary'])
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            # Custom radio button using Label and Canvas
            self._create_custom_radiobutton(col, label, value, description)
        
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
    
    def _create_custom_radiobutton(self, parent, label, value, description):
        """Create a custom radio button without white outline/flash"""
        # Container frame
        container = tk.Frame(parent, bg=self.colors['secondary'], cursor='hand2')
        container.pack(fill=tk.X, pady=2)
        
        # Radio indicator (canvas circle)
        indicator = tk.Canvas(container, width=16, height=16, bg=self.colors['secondary'],
                             highlightthickness=0)
        indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        # Draw the circle
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
        
        # Store reference
        radio_data = {
            'container': container,
            'indicator': indicator,
            'outer': outer_circle,
            'inner': inner_circle,
            'value': value
        }
        self.radio_buttons.append(radio_data)
        
        # Click handler
        def on_click(event=None):
            self.plane_var.set(value)
            self._update_radio_appearance()
            self.on_plane_change()
        
        container.bind('<Button-1>', on_click)
        indicator.bind('<Button-1>', on_click)
        lbl.bind('<Button-1>', on_click)
        desc_lbl.bind('<Button-1>', on_click)
        
        # Initial state
        if self.plane_var.get() == value:
            indicator.itemconfig(inner_circle, fill=self.colors['accent'])
    
    def _update_radio_appearance(self):
        """Update all radio buttons to match current selection"""
        current_value = self.plane_var.get()
        for radio in self.radio_buttons:
            if radio['value'] == current_value:
                radio['indicator'].itemconfig(radio['inner'], fill=self.colors['accent'])
            else:
                radio['indicator'].itemconfig(radio['inner'], fill='')
    
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
                self.plane_var.set(self.mesh_data.sketch_plane)
                self._update_radio_appearance()
                return
        
        self.mesh_data.sketch_plane = new_plane
        self.plane_display.config(text=f"Current: {new_plane} plane")
        self.axis_display.config(text=self._get_axis_description())
        
        if has_geometry:
            self.mesh_data.clear_all()
            messagebox.showinfo("Geometry Cleared", 
                              "All geometry has been cleared due to plane change.")
    
    def update_display(self):
        self.plane_var.set(self.mesh_data.sketch_plane)
        self._update_radio_appearance()
        self.plane_display.config(text=f"Current: {self.mesh_data.sketch_plane} plane")
        self.axis_display.config(text=self._get_axis_description())