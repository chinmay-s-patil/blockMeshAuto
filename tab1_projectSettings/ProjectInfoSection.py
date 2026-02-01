import tkinter as tk
from tkinter import messagebox

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