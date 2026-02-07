import tkinter as tk
from tkinter import messagebox

class UnitSelectionSection:
    """Unit system selection section - Dark Mode with custom radio buttons"""
    def __init__(self, parent, unit_var, sci_exponent_var, colors=None):
        self.unit_var = unit_var
        self.sci_exponent_var = sci_exponent_var
        self.colors = colors or {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'border': '#3e3e42'
        }
        self.radio_buttons = []
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
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
            self._create_custom_radiobutton(left_col, label, value, description)
        
        # Right column: Scientific notation
        right_col = tk.Frame(columns_frame, bg=self.colors['secondary'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_col, text="Scientific Notation", font=("Arial", 10, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        self._create_custom_radiobutton(right_col, "Custom: 10^n", "scientific", "")
        
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
        self.unit_var.trace('w', self.update_display)
        self.sci_exponent_var.trace('w', self.update_display)
        self.update_display()
    
    def _create_custom_radiobutton(self, parent, label, value, description):
        """Create a custom radio button without white outline/flash"""
        container = tk.Frame(parent, bg=self.colors['secondary'], cursor='hand2')
        container.pack(anchor=tk.W, pady=2, fill=tk.X)
        
        # Radio indicator
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
            lbl.bind('<Button-1>', lambda e: self._select_unit(value))
            desc_lbl.bind('<Button-1>', lambda e: self._select_unit(value))
        else:
            lbl = tk.Label(container, text=label, font=("Arial", 9),
                          bg=self.colors['secondary'], fg=self.colors['fg'])
            lbl.pack(side=tk.LEFT)
            lbl.bind('<Button-1>', lambda e: self._select_unit(value))
        
        # Store reference
        self.radio_buttons.append({
            'indicator': indicator,
            'inner': inner_circle,
            'value': value
        })
        
        # Bind clicks
        container.bind('<Button-1>', lambda e: self._select_unit(value))
        indicator.bind('<Button-1>', lambda e: self._select_unit(value))
        
        # Initial state
        if self.unit_var.get() == value:
            indicator.itemconfig(inner_circle, fill=self.colors['accent'])
    
    def _select_unit(self, value):
        self.unit_var.set(value)
        self._update_radio_appearance()
    
    def _update_radio_appearance(self):
        current_value = self.unit_var.get()
        for radio in self.radio_buttons:
            if radio['value'] == current_value:
                radio['indicator'].itemconfig(radio['inner'], fill=self.colors['accent'])
            else:
                radio['indicator'].itemconfig(radio['inner'], fill='')
    
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