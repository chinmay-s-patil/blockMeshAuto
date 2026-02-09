"""
Modern stat card widget for displaying mesh statistics
"""
import tkinter as tk


class StatCard(tk.Frame):
    """A modern card widget for displaying a statistic with icon and color accent"""
    
    def __init__(self, parent, label, value, icon, color, colors_dict):
        super().__init__(parent, bg=colors_dict['card_bg'])
        self.colors = colors_dict
        self.color = color
        self.value_var = tk.StringVar(value=value)
        
        # Add subtle shadow effect with border
        self.configure(
            bg=self.colors['card_bg'],
            highlightbackground=self.colors['border'],
            highlightthickness=1,
            relief=tk.FLAT
        )
        
        # Main container with padding
        container = tk.Frame(self, bg=self.colors['card_bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top section: Icon and value in same row
        top_frame = tk.Frame(container, bg=self.colors['card_bg'])
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Icon with colored background circle
        icon_container = tk.Frame(top_frame, bg=self.colors['card_bg'])
        icon_container.pack(side=tk.LEFT)
        
        icon_bg = tk.Canvas(icon_container, width=48, height=48, 
                           bg=self.colors['card_bg'], highlightthickness=0)
        icon_bg.pack()
        
        # Draw circle background
        icon_bg.create_oval(4, 4, 44, 44, fill=color, outline='')
        
        # Add icon text
        icon_bg.create_text(24, 24, text=icon, 
                           font=('Segoe UI', 18), fill='white')
        
        # Value on the right side
        self.value_label = tk.Label(top_frame, textvariable=self.value_var,
                                   font=('Segoe UI', 32, 'bold'),
                                   bg=self.colors['card_bg'], fg=color,
                                   anchor=tk.E)
        self.value_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Bottom section: Label
        label_frame = tk.Frame(container, bg=self.colors['card_bg'])
        label_frame.pack(fill=tk.X)
        
        tk.Label(label_frame, text=label,
                font=('Segoe UI', 11),
                bg=self.colors['card_bg'], fg=self.colors['fg'],
                anchor=tk.W).pack(side=tk.LEFT)
        
        # Color accent bar at bottom
        accent_bar = tk.Frame(self, bg=color, height=4)
        accent_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_value(self, new_value):
        """Update the displayed value"""
        self.value_var.set(new_value)
    
    def set_color(self, new_color):
        """Update the accent color"""
        self.color = new_color
        self.value_label.config(fg=new_color)