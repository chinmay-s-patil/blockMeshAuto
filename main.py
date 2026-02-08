"""
OpenFOAM blockMesh Builder - Main Application
Dark Mode Edition with Edge Editor Tab and New Hex/Patch System
"""

import os
os.environ['PYVISTA_TRAME'] = 'false'
os.environ['PYVISTA_TRAME_SERVER'] = 'false'

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

from mesh_data import MeshData
from tab1_projectSettings.tab1_main import TabProjectSettings
from tab2_2DEditor.tab2_main import Tab2DEditor
from tab3_Edges.TabEdgeEditor import TabEdgeEditor
from tab4_Hex.tab4_main import TabHexBlockMaking
# UPDATED: New tab5 with hex block rendering and patch assignment
from tab5_Patches.tab5_main import Tab5HexPatches
from tab6_export.tab6_main import TabExport


class MeshBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenFOAM blockMesh Builder")
        self.root.geometry("1400x900")
        
        # Dark mode colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f44747',
            'secondary': '#252526',
            'border': '#3e3e42',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'tab_bg': '#2d2d2d',
            'tab_fg': '#ffffff',
            'tab_selected': '#007acc'
        }
        
        self.mesh_data = MeshData()
        
        # Ensure temp directory exists
        if not os.path.exists("temp"):
            os.makedirs("temp")
        
        self.setup_dark_mode()
        self.setup_top_bar()
        self.setup_notebook()
        self.setup_tabs()
        
        self.auto_save()
        
    def setup_dark_mode(self):
        """Configure dark mode styles"""
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles for dark mode
        style = ttk.Style()
        style.theme_use('default')
        
        # Notebook styling
        style.configure('TNotebook', background=self.colors['secondary'], tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab', 
                       background=self.colors['tab_bg'],
                       foreground=self.colors['tab_fg'],
                       padding=[10, 5],
                       font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['tab_selected']),
                           ('active', self.colors['accent'])],
                 foreground=[('selected', self.colors['tab_fg'])])
        
        # Frame styling
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelframe', background=self.colors['secondary'], 
                       foreground=self.colors['fg'])
        style.configure('TLabelframe.Label', 
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=('Arial', 10, 'bold'))
        
        # Other widget styles
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', 
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_fg'])
        
    def setup_top_bar(self):
        """Create top bar with dark mode styling"""
        top_frame = tk.Frame(self.root, bg=self.colors['secondary'], height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        tk.Label(top_frame, text="OpenFOAM Mesh Builder", 
                font=("Arial", 14, "bold"), 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        button_frame = tk.Frame(top_frame, bg=self.colors['secondary'])
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        btn_style = {
            'bg': self.colors['button_bg'],
            'fg': self.colors['button_fg'],
            'font': ('Arial', 10, 'bold'),
            'width': 8,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        tk.Button(button_frame, text="💾 Save", command=self.save_to_json, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 Load", command=self.load_from_json, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 New", command=self.new_project, **btn_style).pack(side=tk.LEFT, padx=2)
        
    def setup_notebook(self):
        """Create the tabbed notebook interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab frames
        self.tab_project = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_2d = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_edges = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_grid = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_3d = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_export = tk.Frame(self.notebook, bg=self.colors['bg'])
        
        # Add tabs to notebook
        self.notebook.add(self.tab_project, text="1. Project Settings")
        self.notebook.add(self.tab_2d, text="2. Points & Connections")
        self.notebook.add(self.tab_edges, text="3. Edge Editor")
        self.notebook.add(self.tab_grid, text="4. Hex Blocks")
        # UPDATED: Changed tab title to reflect new functionality
        self.notebook.add(self.tab_3d, text="5. Hex View & Patches")
        self.notebook.add(self.tab_export, text="6. Export blockMeshDict")
        
    def setup_tabs(self):
        """Initialize all tab components"""
        self.project_settings = TabProjectSettings(self.tab_project, self.mesh_data)
        self.editor_2d = Tab2DEditor(self.tab_2d, self.mesh_data)
        self.edge_editor = TabEdgeEditor(self.tab_edges, self.mesh_data)
        self.hex_blocks = TabHexBlockMaking(self.tab_grid, self.mesh_data)
        # UPDATED: Use new Tab5HexPatches class
        self.patches_3d = Tab5HexPatches(self.tab_3d, self.mesh_data)
        self.export_tab = TabExport(self.tab_export, self.mesh_data)
    
    def get_temp_filename(self):
        """Get the temp filename based on project name"""
        safe_name = self.mesh_data.get_safe_project_name()
        return os.path.join("temp", f"{safe_name}_temp.json")
    
    def get_default_save_filename(self):
        """Get the default save filename based on project name"""
        safe_name = self.mesh_data.get_safe_project_name()
        return f"{safe_name}.json"
    
    def save_to_json(self):
        """Save project to JSON file"""
        if hasattr(self.project_settings, 'save_all_settings'):
            self.project_settings.save_all_settings()
        
        default_filename = self.get_default_save_filename()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_filename
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
                self.editor_2d.update_dual_view_buttons()
                self.editor_2d.update_plot()
                
                # Update edge editor
                self.edge_editor._update_edge_list()
                self.edge_editor.viewer.refresh()
                
                self.hex_blocks.refresh_layers()
                self.hex_blocks.update_block_list()
                
                # UPDATED: Use _refresh_view() instead of update_view()
                self.patches_3d._refresh_view()
                
                self.export_tab.update_summary()
                
                messagebox.showinfo("Success", f"Project loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
    
    def auto_save(self):
        """Auto-save project every 30 seconds to temp folder"""
        try:
            if hasattr(self.project_settings, 'save_all_settings'):
                self.project_settings.save_all_settings()
            
            temp_file = self.get_temp_filename()
            data = self.mesh_data.to_dict()
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Auto-save error: {e}")
        
        self.root.after(30000, self.auto_save)
    
    def new_project(self):
        """Start a new project"""
        result = messagebox.askyesnocancel("New Project", 
                                          "Save current project before starting new?")
        if result is None:
            return
        elif result:
            self.save_to_json()
        
        # Reset mesh data
        self.mesh_data = MeshData()
        
        # Reset all tab components
        self.project_settings.mesh_data = self.mesh_data
        self.editor_2d.mesh_data = self.mesh_data
        self.edge_editor.mesh_data = self.mesh_data
        self.edge_editor.viewer.mesh_data = self.mesh_data
        self.hex_blocks.mesh_data = self.mesh_data
        self.patches_3d.mesh_data = self.mesh_data
        
        # Update all views
        self.project_settings.update_display()
        self.editor_2d.selected_points = []
        self.editor_2d.dual_view_layers = []
        self.editor_2d.dual_view_var.set(False)
        
        self.editor_2d.update_layer_list()
        self.editor_2d.update_dual_view_buttons()
        self.editor_2d.update_plot()
        
        # Reset edge editor
        self.edge_editor._reset_creation()
        self.edge_editor._update_edge_list()
        
        self.hex_blocks.refresh_layers()
        self.hex_blocks.update_block_list()
        
        # UPDATED: Refresh the new tab5
        self.patches_3d._refresh_view()
        
        self.export_tab.update_summary()
        
        messagebox.showinfo("New Project", "Started a new project")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MeshBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
