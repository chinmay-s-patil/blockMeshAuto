"""
OpenFOAM blockMesh Builder - Main Application
Dark Mode Edition with Edge Editor Tab and New Hex/Patch System
Updated to work with new data structure (Points, Layers, Connections, Edges, Hexes, Patches, Specs)
FIXED: Better error handling for auto-save and file operations
FIXED: Proper cleanup of pending callbacks on exit
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
import atexit

from mesh_data import MeshData
from tab1_projectSettings.tab1_main import TabProjectSettings
from tab2_2DEditor.tab2_main import Tab2DEditor
from tab3_Edges.tab3_main import Tab3EdgeEditor
from tab4_Hex.tab4_main import TabHexBlockMaking
from tab5_Patches.tab5_main import Tab5HexPatches
from tab6_export.tab6_main import TabExport
from utils.history_manager import HistoryManager
from utils.blockmesh_importer import import_blockmesh_file, BlockMeshImporter


class MeshBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BlockmeshAuto - Your OpenFoam Mesh Builder.")
        self.root.geometry("1400x900")

        # Track all pending after callbacks for proper cleanup
        self._pending_after_ids = []
        self._auto_save_id = None
        self.is_fullscreen = False

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
            'tab_selected': '#007acc',
            'button_active': '#1177bb'
        }

        self.mesh_data = MeshData()

        # Setup history manager for Undo/Redo
        self.history_manager = HistoryManager(self.mesh_data, max_states=5)
        self.mesh_data.set_save_state_callback(self.history_manager.save_state)

        # Ensure temp directory exists - with better error handling
        self._ensure_temp_dir()

        self.setup_dark_mode()
        self.setup_menubar()
        self.setup_notebook()
        self.setup_shortcuts()
        self.setup_tabs()

        # Register history UI update callback
        self.history_manager.set_update_callback(self._update_all_views)

        # Register cleanup on exit
        atexit.register(self._cleanup)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start auto-save with error tracking
        self.auto_save_error_count = 0
        self._schedule_auto_save()

    def _schedule_auto_save(self):
        """Schedule auto-save with proper ID tracking"""
        self._auto_save_id = self.root.after(30000, self._auto_save_wrapper)

    def _auto_save_wrapper(self):
        """Wrapper to handle auto-save and reschedule"""
        self.auto_save()
        self._schedule_auto_save()

    def _cleanup(self):
        """Clean up all pending callbacks"""
        # Cancel auto-save
        if self._auto_save_id:
            try:
                self.root.after_cancel(self._auto_save_id)
            except:
                pass
            self._auto_save_id = None

        # Cancel any other pending after callbacks
        for after_id in self._pending_after_ids:
            try:
                self.root.after_cancel(after_id)
            except:
                pass
        self._pending_after_ids.clear()

    def _on_close(self):
        """Handle window close - cleanup and destroy"""
        self._cleanup()

        # Cleanup tab4 viewer if exists
        try:
            if hasattr(self, 'hex_blocks') and self.hex_blocks:
                self.hex_blocks.cleanup()
        except:
            pass

        self.root.destroy()

    def _ensure_temp_dir(self):
        """Ensure temp directory exists with proper error handling"""
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        try:
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
                print(f"Created temp directory: {temp_dir}")
            # Test write permissions
            test_file = os.path.join(temp_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            print(f"Warning: Could not create or write to temp directory: {e}")
            # Try to use a fallback temp location
            try:
                import tempfile
                self.temp_dir = tempfile.gettempdir()
                print(f"Using system temp directory instead: {self.temp_dir}")
            except:
                self.temp_dir = temp_dir  # Use original even if it fails

    def get_temp_dir(self):
        """Get the temp directory path"""
        return getattr(self, 'temp_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp"))

    def setup_dark_mode(self):
        """Configure dark mode styles"""
        self.root.configure(bg=self.colors['bg'])

        # Configure ttk styles for dark mode
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook styling
        style.configure('TNotebook', 
                        background=self.colors['bg'], 
                        borderwidth=2, 
                        darkcolor=self.colors['border'],
                        lightcolor=self.colors['border'])

        style.configure('TNotebook.Tab', 
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       padding=[18, 10],  # Slightly more padded tabs
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor=self.colors['bg'])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent']), ('active', self.colors['button_active'])],
                 foreground=[('selected', '#ffffff')])

        # Remove dotted focus ring
        style.layout('TNotebook.Tab', [('Notebook.tab', {'sticky': 'nswe', 'children': [('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [('Notebook.label', {'side': 'top', 'sticky': ''})]})]})])

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

    def setup_menubar(self):
        """Create standard OS Menubar"""
        self.menubar = tk.Menu(self.root, 
                               bg=self.colors['button_bg'], 
                               fg=self.colors['button_fg'],
                               activebackground=self.colors['accent'],
                               activeforeground='#ffffff',
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat', bd=0)

        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0, 
                            bg=self.colors['secondary'], 
                            fg=self.colors['fg'],
                            activebackground=self.colors['accent'], 
                            activeforeground='#ffffff',
                            font=('Segoe UI', 10),
                            relief='solid', bd=1)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Load Project...", command=self.load_from_json)
        file_menu.add_command(label="Save Project...", command=self.save_to_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Actions Menu
        actions_menu = tk.Menu(self.menubar, tearoff=0, 
                               bg=self.colors['secondary'], 
                               fg=self.colors['fg'],
                               activebackground=self.colors['accent'], 
                               activeforeground='#ffffff',
                               font=('Segoe UI', 10),
                               relief='solid', bd=1)
        actions_menu.add_command(label="Undo", command=self.on_undo, accelerator="Ctrl+Z")
        actions_menu.add_command(label="Redo", command=self.on_redo, accelerator="Ctrl+Y")
        self.menubar.add_cascade(label="Actions", menu=actions_menu)

        # BlockMesh Menu (NEW)
        blockmesh_menu = tk.Menu(self.menubar, tearoff=0,
                                 bg=self.colors['secondary'],
                                 fg=self.colors['fg'],
                                 activebackground=self.colors['accent'],
                                 activeforeground='#ffffff',
                                 font=('Segoe UI', 10),
                                 relief='solid', bd=1)
        blockmesh_menu.add_command(label="Import BlockMesh...", command=self.import_blockmesh)
        self.menubar.add_cascade(label="BlockMesh", menu=blockmesh_menu)

        self.root.config(menu=self.menubar)

    def setup_shortcuts(self):
        """Bind global keyboard shortcuts"""
        self.root.bind('<Control-z>', self.on_undo_event)
        self.root.bind('<Control-Z>', self.on_undo_event)  # Shift+Z variant
        self.root.bind('<Control-y>', self.on_redo_event)
        self.root.bind('<Control-Y>', self.on_redo_event)
        self.root.bind('<Control-Shift-Z>', self.on_redo_event)  # Common alternative for redo
        self.root.bind('<F11>', self.toggle_fullscreen)

    def on_undo_event(self, event):
        self.on_undo()
        return "break"  # Prevent default widget handling

    def on_redo_event(self, event):
        self.on_redo()
        return "break"

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def on_undo(self):
        if not self.history_manager.undo():
            print("Nothing to undo")

    def on_redo(self):
        if not self.history_manager.redo():
            print("Nothing to redo")

    def import_blockmesh(self):
        """Import a blockMeshDict file"""
        # Check if there's existing geometry
        has_geometry = len(self.mesh_data.points) > 0

        if has_geometry:
            result = messagebox.askyesnocancel(
                "Import BlockMesh",
                "Importing a blockMeshDict will clear all existing geometry.\n\n"
                "Save current project before importing?",
                icon='warning'
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes - save first
                self.save_to_json()
                # Don't return, continue with import

        # Show import dialog
        success = import_blockmesh_file(self.mesh_data, self.root)

        if success:
            # Update all views to reflect imported data
            self._update_all_views()
            messagebox.showinfo("Import Successful", 
                              f"Project imported: {self.mesh_data.project_name}")

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
        self.notebook.add(self.tab_3d, text="5. Hex View & Patches")
        self.notebook.add(self.tab_export, text="6. Export blockMeshDict")

    def setup_tabs(self):
        """Initialize all tab components"""
        self.project_settings = TabProjectSettings(self.tab_project, self.mesh_data)
        self.editor_2d = Tab2DEditor(self.tab_2d, self.mesh_data)
        self.edge_editor = Tab3EdgeEditor(self.tab_edges, self.mesh_data)
        self.hex_blocks = TabHexBlockMaking(self.tab_grid, self.mesh_data)
        self.patches_3d = Tab5HexPatches(self.tab_3d, self.mesh_data)
        self.export_tab = TabExport(self.tab_export, self.mesh_data)

    def get_temp_filename(self):
        """Get the temp filename based on project name"""
        safe_name = self.mesh_data.get_safe_project_name()
        return os.path.join(self.get_temp_dir(), f"{safe_name}_temp.json")

    def get_default_save_filename(self):
        """Get the default save filename based on project name"""
        safe_name = self.mesh_data.get_safe_project_name()
        return f"{safe_name}.json"

    def save_to_json(self):
        """Save project to JSON file with better error handling"""
        if hasattr(self.project_settings, 'save_all_settings'):
            try:
                self.project_settings.save_all_settings()
            except Exception as e:
                print(f"Warning: Could not save project settings: {e}")

        default_filename = self.get_default_save_filename()

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*")],
                initialfile=default_filename
            )
        except Exception as e:
            messagebox.showerror("Dialog Error", f"Could not open save dialog: {e}")
            return

        if filename:
            try:
                # Validate we can write to this location
                test_path = os.path.dirname(filename)
                if test_path and not os.path.exists(test_path):
                    os.makedirs(test_path, exist_ok=True)

                data = self.mesh_data.to_dict()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Project saved to {filename}")
            except PermissionError as e:
                messagebox.showerror("Permission Error", 
                    f"Cannot save to {filename}:Permission denied."
                    f"Try saving to a different location where you have write permissions.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def load_from_json(self):
        """Load project from JSON file with better error handling"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*")]
            )
        except Exception as e:
            messagebox.showerror("Dialog Error", f"Could not open file dialog: {e}")
            return

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate data structure before loading
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure: root must be an object")

                self.mesh_data.from_dict(data)

                # Update all tab views with error handling
                self._update_all_views()

                messagebox.showinfo("Success", f"Project loaded from {filename}")
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON file:{str(e)}")
            except PermissionError as e:
                messagebox.showerror("Permission Error", 
                    f"Cannot read {filename}:Permission denied.")
            except ValueError as e:
                messagebox.showerror("Data Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
                import traceback
                traceback.print_exc()

    def _update_all_views(self):
        """Update all tab views with error handling"""
        try:
            self.project_settings.update_display()
        except Exception as e:
            print(f"Warning: Could not update project settings: {e}")

        try:
            self.editor_2d.update_layer_list()
            self.editor_2d.update_dual_view_buttons()
            self.editor_2d.update_plot()
        except Exception as e:
            print(f"Warning: Could not update 2D editor: {e}")

        try:
            self.edge_editor._update_edge_list()
            self.edge_editor.viewer.refresh()
        except Exception as e:
            print(f"Warning: Could not update edge editor: {e}")

        try:
            self.hex_blocks.refresh_layers()
            self.hex_blocks.update_block_list()
        except Exception as e:
            print(f"Warning: Could not update hex blocks: {e}")

        try:
            self.patches_3d._refresh_view()
        except Exception as e:
            print(f"Warning: Could not update patches view: {e}")

        try:
            self.export_tab.update_summary()
        except Exception as e:
            print(f"Warning: Could not update export tab: {e}")

    def auto_save(self):
        """Auto-save project every 30 seconds to temp folder with better error handling"""
        try:
            if hasattr(self.project_settings, 'save_all_settings'):
                try:
                    self.project_settings.save_all_settings()
                except Exception as e:
                    if self.auto_save_error_count < 3:
                        print(f"Auto-save warning (settings): {e}")

            temp_file = self.get_temp_filename()
            temp_dir = os.path.dirname(temp_file)

            # Ensure temp directory exists
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)

            data = self.mesh_data.to_dict()

            # Write to a temp file first, then rename (atomic operation)
            temp_write_file = temp_file + ".tmp"
            with open(temp_write_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Rename to final filename (atomic on most systems)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rename(temp_write_file, temp_file)

            # Reset error count on success
            self.auto_save_error_count = 0

        except PermissionError as e:
            self.auto_save_error_count += 1
            if self.auto_save_error_count <= 3:
                print(f"Auto-save permission error (attempt {self.auto_save_error_count}): {e}")
        except Exception as e:
            self.auto_save_error_count += 1
            if self.auto_save_error_count <= 3:
                print(f"Auto-save error (attempt {self.auto_save_error_count}): {e}")

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
        self.hex_blocks.mesh_data = self.mesh_data
        self.patches_3d.mesh_data = self.mesh_data

        # Also update edge editor viewer if it exists
        if hasattr(self.edge_editor, 'viewer'):
            self.edge_editor.viewer.mesh_data = self.mesh_data

        # Update all views
        try:
            self.project_settings.update_display()
        except:
            pass

        try:
            self.editor_2d.selected_points = []
            self.editor_2d.dual_view_layers = []
            self.editor_2d.dual_view_var.set(False)
            self.editor_2d.update_layer_list()
            self.editor_2d.update_dual_view_buttons()
            self.editor_2d.update_plot()
        except:
            pass

        try:
            self.edge_editor._reset_creation()
            self.edge_editor._update_edge_list()
        except:
            pass

        try:
            self.hex_blocks.refresh_layers()
            self.hex_blocks.update_block_list()
        except:
            pass

        try:
            self.patches_3d._refresh_view()
        except:
            pass

        try:
            self.export_tab.update_summary()
        except:
            pass

        messagebox.showinfo("New Project", "Started a new project")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MeshBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()