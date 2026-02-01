import tkinter as tk
from tkinter import messagebox

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

