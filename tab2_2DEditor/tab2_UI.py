import tkinter as tk
from tkinter import messagebox, simpledialog
import math

def setup_ui(self):
    main_frame = tk.Frame(self.parent)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Left: Canvas area
    self.left_frame = tk.Frame(main_frame)
    self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    self.canvas_label = tk.Label(self.left_frame, text="2D View", font=("Arial", 12, "bold"))
    self.canvas_label.pack()
    
    # Container for canvas(es)
    self.canvas_container = tk.Frame(self.left_frame)
    self.canvas_container.pack(fill=tk.BOTH, expand=True)
    
    # Single canvas (normal mode)
    self.canvas = tk.Canvas(self.canvas_container, bg="white", 
                            width=self.canvas_width, height=self.canvas_height)
    self.canvas.pack(fill=tk.BOTH, expand=True)
    self.setup_canvas_bindings(self.canvas)
    
    # Control buttons at bottom
    button_frame = tk.Frame(self.left_frame)
    button_frame.pack(fill=tk.X, pady=5)
    
    tk.Button(button_frame, text="🔍 Fit All", command=self.fit_all_view,
                bg="lightblue", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Label(button_frame, text="Pan: Right-drag | Zoom: Scroll",
            font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=10)
    
    # Right: Controls
    right_frame = tk.Frame(main_frame, width=350)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
    right_frame.pack_propagate(False)
    
    self._setup_mode_controls(right_frame)
    self._setup_layer_controls(right_frame)
    self._setup_manual_entry(right_frame)
    self._setup_connection_controls(right_frame)
    
    self.update_plot()