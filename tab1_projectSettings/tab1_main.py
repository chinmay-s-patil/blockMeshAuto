"""
Project Settings Tab - Configuration before building mesh
Modularized with optimized horizontal layout for 1920x1080
"""
import tkinter as tk
from tkinter import messagebox

from tab1_projectSettings.ProjectInfoSection import ProjectInfoSection
from tab1_projectSettings.SketchPlaneSelection import SketchPlaneSection
from tab1_projectSettings.UnitSelectionSection import UnitSelectionSection

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

