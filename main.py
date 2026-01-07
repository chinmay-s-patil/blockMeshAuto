"""
OpenFOAM blockMesh Builder - Main Application
Modularized version with separated tab components
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

from mesh_data import MeshData
from tab1_project_settings import TabProjectSettings
from tab2_2d_editor import Tab2DEditor
from tab3_grid_sizing import TabGridSizing
from tab4_3d_patches import Tab3DPatches
from tab5_export import TabExport


class MeshBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenFOAM blockMesh Builder")
        self.root.geometry("1400x900")
        
        self.mesh_data = MeshData()
        self.temp_json_file = "mesh_export_temp.json"
        
        self.setup_top_bar()
        self.setup_notebook()
        self.setup_tabs()
        
        self.auto_save()
        
    def setup_top_bar(self):
        """Create top bar with save/load/new buttons"""
        top_frame = tk.Frame(self.root, bg="lightgray", height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="OpenFOAM Mesh Builder", 
                font=("Arial", 14, "bold"), bg="lightgray").pack(side=tk.LEFT, padx=10)
        
        button_frame = tk.Frame(top_frame, bg="lightgray")
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(button_frame, text="💾 Save", command=self.save_to_json,
                 bg="lightgreen", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 Load", command=self.load_from_json,
                 bg="lightblue", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 New", command=self.new_project,
                 bg="lightyellow", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=2)
        
    def setup_notebook(self):
        """Create the tabbed notebook interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab frames
        self.tab_project = tk.Frame(self.notebook)
        self.tab_2d = tk.Frame(self.notebook)
        self.tab_grid = tk.Frame(self.notebook)
        self.tab_3d = tk.Frame(self.notebook)
        self.tab_export = tk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.tab_project, text="1. Project Settings")
        self.notebook.add(self.tab_2d, text="2. Points & Connections")
        self.notebook.add(self.tab_grid, text="3. Grid Sizing")
        self.notebook.add(self.tab_3d, text="4. 3D View & Patches")
        self.notebook.add(self.tab_export, text="5. Export blockMeshDict")
        
    def setup_tabs(self):
        """Initialize all tab components"""
        self.project_settings = TabProjectSettings(self.tab_project, self.mesh_data)
        self.editor_2d = Tab2DEditor(self.tab_2d, self.mesh_data)
        self.grid_sizing = TabGridSizing(self.tab_grid, self.mesh_data)
        self.patches_3d = Tab3DPatches(self.tab_3d, self.mesh_data)
        self.export_tab = TabExport(self.tab_export, self.mesh_data)
    
    def save_to_json(self):
        """Save project to JSON file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="mesh_export_project.json"
        )
        
        if filename:
            try:
                data = self.mesh_data.to_dict()
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Project saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def load_from_json(self):
        """Load project from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.mesh_data.from_dict(data)
                
                # Update all tab views
                self.project_settings.update_display()
                self.editor_2d.update_layer_list()
                self.editor_2d.update_iso_checkboxes()
                self.editor_2d.update_plot()
                self.patches_3d.update_view()
                self.export_tab.update_summary()
                
                messagebox.showinfo("Success", f"Project loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
    
    def auto_save(self):
        """Auto-save project every 30 seconds"""
        try:
            data = self.mesh_data.to_dict()
            with open(self.temp_json_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
        
        self.root.after(30000, self.auto_save)
    
    def new_project(self):
        """Start a new project"""
        result = messagebox.askyesnocancel("New Project", 
                                          "Do you want to save the current project before starting a new one?")
        if result is None:
            return
        elif result:
            self.save_to_json()
        
        # Reset mesh data
        self.mesh_data = MeshData()
        
        # Reset all tab components with new mesh data
        self.project_settings.mesh_data = self.mesh_data
        self.editor_2d.mesh_data = self.mesh_data
        self.grid_sizing.mesh_data = self.mesh_data
        self.patches_3d.mesh_data = self.mesh_data
        self.patches_3d.viewer_3d.mesh_data = self.mesh_data
        self.export_tab.mesh_data = self.mesh_data
        
        # Update all views
        self.project_settings.update_display()
        self.editor_2d.selected_points = []
        self.editor_2d.iso_layers = []
        self.editor_2d.iso_mode = False
        self.editor_2d.iso_mode_var.set(False)
        
        self.editor_2d.update_layer_list()
        self.editor_2d.update_iso_checkboxes()
        self.editor_2d.update_plot()
        self.patches_3d.update_view()
        self.patches_3d.clear_face_selection()
        self.export_tab.update_summary()
        
        messagebox.showinfo("New Project", "Started a new project")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MeshBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()