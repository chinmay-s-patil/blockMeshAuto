"""
OpenFOAM blockMesh Builder - Main Application
Dark Mode Edition with Edge Editor Tab and New Hex/Patch System
FIXED: new_project() now calls tab5.reset() to fully clear all stale references

CLI Usage:
  python main.py              - Normal launch
  python main.py /path/to/dir - Open in dir; auto-import system/blockMeshDict if found
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

#  Help text for each tab (F1) 

HELP_TEXTS = {
    0: (
        "Tab 1 · Project Settings",
        """\
PROJECT NAME & DESCRIPTION
  Enter a name and optional description for your mesh project.
  Click "Save Project Info" to commit.

UNIT SYSTEM
  Choose the unit your coordinates are written in:
    • Meters (m)     → scale = 1.0
    • Centimetres    → scale = 0.01
    • Millimetres    → scale = 0.001
    • Scientific     → scale = 10^n  (set exponent n)
  The chosen unit only affects the 'scale' line in the exported
  blockMeshDict — your coordinates stay as typed.

SKETCH PLANE
  Pick the plane your 2-D profile is drawn on.
  The remaining axis becomes the extrusion / depth direction.
  ⚠  Changing the plane after geometry exists clears everything.

KEYBOARD SHORTCUTS
  Ctrl+Z  Undo        Ctrl+Y  Redo
  F11     Toggle full-screen    F1  This help
"""
    ),
    1: (
        "Tab 2 · Points & Connections",
        """\
MODES (toolbar on the left panel)
  Select     – Click or drag-lasso to highlight points.
  Add Points – Click the canvas to place a point.
               Switch to "Snap-to-Grid" for aligned placement.
  Connect    – Click two points in sequence to draw an edge.
  Delete     – Click a point to remove it (and its edges).
  Edit Point – Move a selected point's X / Y coordinates.

LAYERS
  Every point lives on a named layer with a fixed Z value.
  Use Add / Duplicate / Extrude / Remove to manage layers.
  "Edit Z" changes the Z of an existing layer and updates
  all points on it.

DUAL VIEW
  Select exactly 2 layers, enable "Dual View".
  Click one point on the left panel and one on the right to
  create inter-layer connections for hex-block building.

CANVAS NAVIGATION
  Right-drag  Pan     Scroll  Zoom     "Fit All" to reset view.

MANUAL ENTRY
  Type X / Y in the bottom fields and click "Add" to place a
  point at exact coordinates.
"""
    ),
    2: (
        "Tab 3 · Edge Editor",
        """\
PURPOSE
  Replace straight connections with curved edges
  (arc, spline, polyLine) for rounded geometry.

EDGE TYPES
  arc      – Smooth circular arc through 3 points.
             Use the Arc Helper tabs:
               Point  – pick a point on the arc
               Center – pick the arc's centre point
               Radius – enter a radius and preview both sides
  spline   – Catmull-Rom spline through intermediate points.
  polyLine – Straight segments through intermediate points.
  line     – Straight (default; mainly used to delete a curve).

WORKFLOW (arc)
  1. Select Start then End in the 3-D viewer (left-click).
  2. Use Arc Helper to define the curvature.
  3. Click "Create Edge".

WORKFLOW (spline / polyLine)
  1. Choose Start & End from the dropdowns, click "Set".
  2. Click intermediate points in the viewer (or add manually).
  3. Click "Create Edge".

MANAGE TAB
  Lists all edges. Select one → Edit / Delete / Highlight.

3-D VIEWER CONTROLS
  Middle-drag  Rotate     Right-drag  Pan     Scroll  Zoom
"""
    ),
    3: (
        "Tab 4 · Hex Blocks",
        """\
PURPOSE
  Group 8 mesh points into a hexahedral block.

POINT SELECTION ORDER
  Bottom layer: vertices 0–3 counter-clockwise (view from below)
  Top    layer: vertices 4–7 counter-clockwise (view from above)

  The "Automake" toggle sorts 8 selected points automatically
  and creates the block without extra clicks.

LAYERS TAB
  Toggle each layer on/off to reduce clutter in the viewer.
  "All On / All Off" bulk-toggle.

SIZING TAB
  Direct   – Enter X / Y / Z cell counts directly.
  Cell Size – Enter a target cell size; divisions auto-calculated.
  2-D Mesh – Force 1 division in one direction (empty case).
  Grading  – simpleGrading ratios for non-uniform spacing.

BLOCKS TAB
  Lists created blocks. Select → Edit / Delete / Cleanup.
  "Edit All Hexes" applies one setting to every block at once.

3-D VIEWER CONTROLS
  Left-click / drag  Select points (Square or Lasso mode)
  Middle-drag        Rotate
  Right-drag         Pan
  Scroll             Zoom
"""
    ),
    4: (
        "Tab 5 · Patches & Assignment",
        """\
PURPOSE
  Assign names and boundary types to the external faces of
  your hex blocks for OpenFOAM boundary conditions.

VIEWING
  🎨 Patches ON/OFF – colour-code faces by patch.
  Mode: Select      – click faces to select them.
  Mode: Hide        – click faces to hide them temporarily.
  ◑ Translucent     – see through the mesh.
  Show All          – unhide any hidden faces.
  Fit All           – reset camera to show everything.

ASSIGNING FACES (Assign tab)
  1. Select faces in the 3-D view (click or drag).
  2. Type a Patch Name.
  3. Choose a boundary type (patch, wall, symmetry, empty …).
  4. Click "Assign to Selected Faces".
     On a name clash you can Append or Replace.

PATCHES TAB
  Lists all defined patches.
  Highlight – flash the patch faces in the 3-D view.
  Edit      – rename, retype, add or remove faces.
  Delete    – remove the patch entirely.

NORMALS TAB
  Select a patch from the dropdown.
  "Flip Normal Mode" → click any face to reverse the whole
  patch's normal direction.
  Click "Apply Changes" to save the direction to the project.

3-D VIEWER CONTROLS
  Left-drag   Brush-select faces
  Middle-drag Rotate    Right-drag Pan    Scroll Zoom
"""
    ),
    5: (
        "Tab 6 · Export blockMeshDict",
        """\
ACTIONS TAB
  Export to File  – Save a ready-to-run blockMeshDict.
  Copy to Clipboard – Paste straight into your case folder.

PREVIEW PANEL (left)
  Shows the full generated file.  Click "Refresh Preview"
  after changes to update it.

SUMMARY TAB
  Dashboard of vertex count, block count, total cell count,
  patch count, and per-block division breakdown.

DETAILS TAB
  Patches – name, type, face count.
  Hex Blocks – block index and division grid.
  Edges – block edge point counts.

VALIDATION
  Warnings appear in the Actions tab if:
    • A block has the wrong number of vertices.
    • Bottom-face Z is higher than top-face Z.
    • Duplicate vertex references exist.

FILE FORMAT
  The exported file follows OpenFOAM's blockMeshDict syntax
  and can be placed directly in <case>/system/.
"""
    ),
}


class MeshBuilderApp:
    def __init__(self, root, working_dir=None):
        self.root = root
        self.root.title("BlockmeshAuto - Your OpenFoam Mesh Builder.")
        self.root.geometry("1400x900")

        # Working directory (set by CLI argument)
        self.working_dir = os.path.abspath(working_dir) if working_dir else None

        self._pending_after_ids = []
        self._auto_save_id = None
        self.is_fullscreen = False

        # Track project name for rename-based temp-file cleanup
        self._last_safe_project_name = None

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

        self.history_manager = HistoryManager(self.mesh_data, max_states=5)
        self.mesh_data.set_save_state_callback(self.history_manager.save_state)

        self._ensure_temp_dir()
        self._set_window_icon()

        self.setup_dark_mode()
        self.setup_menubar()
        self.setup_notebook()
        self.setup_shortcuts()
        self.setup_tabs()

        self.history_manager.set_update_callback(self._update_all_views)

        atexit.register(self._cleanup)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.auto_save_error_count = 0
        self._last_safe_project_name = self.mesh_data.get_safe_project_name()
        self._schedule_auto_save()

        # Auto-import if a working directory was supplied
        if self.working_dir:
            self.root.after(600, self._try_auto_import)

    #  Window icon 

    def _set_window_icon(self):
        """Try to set the window icon using BlockMeshLogo.png from base dir."""
        # Base dir is one level above the Code/ directory
        code_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(os.path.dirname(code_dir), "BlockMeshLogo.png"),
            os.path.join(code_dir, "BlockMeshLogo.png"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    img = tk.PhotoImage(file=path)
                    self.root.iconphoto(True, img)
                except Exception:
                    pass
                return

    #  Auto-import from working directory 

    def _try_auto_import(self):
        """If a working directory was given, look for system/blockMeshDict."""
        blockmesh_path = os.path.join(self.working_dir, "system", "blockMeshDict")
        if os.path.exists(blockmesh_path):
            result = messagebox.askyesno(
                "Auto Import",
                f"Found blockMeshDict in:\n{blockmesh_path}\n\nImport it now?",
            )
            if result:
                importer = BlockMeshImporter(self.mesh_data)
                success = importer.import_file(blockmesh_path)
                if success:
                    self._update_all_views()
        else:
            # No blockMeshDict found — just set a friendly title hint
            self.root.title(
                f"BlockmeshAuto — {self.working_dir}"
            )

    #  Scheduling / cleanup 

    def _schedule_auto_save(self):
        self._auto_save_id = self.root.after(30000, self._auto_save_wrapper)

    def _auto_save_wrapper(self):
        self.auto_save()
        self._schedule_auto_save()

    def _cleanup(self):
        if self._auto_save_id:
            try:
                self.root.after_cancel(self._auto_save_id)
            except Exception:
                pass
            self._auto_save_id = None
        for after_id in self._pending_after_ids:
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        self._pending_after_ids.clear()

    def _on_close(self):
        self._cleanup()
        try:
            if hasattr(self, 'hex_blocks') and self.hex_blocks:
                self.hex_blocks.cleanup()
        except Exception:
            pass
        self.root.destroy()

    #  Temp directory 

    def _ensure_temp_dir(self):
        temp_dir = self.get_temp_dir()
        try:
            os.makedirs(temp_dir, exist_ok=True)
            test_file = os.path.join(temp_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            print(f"Warning: Could not create or write to temp directory: {e}")
            import tempfile
            self._fallback_temp_dir = tempfile.gettempdir()

    def get_temp_dir(self):
        # Prefer working directory's hidden subfolder when one is set
        if self.working_dir:
            d = os.path.join(self.working_dir, ".blockmeshauto_temp")
            try:
                os.makedirs(d, exist_ok=True)
                return d
            except Exception:
                pass
        if hasattr(self, '_fallback_temp_dir'):
            return self._fallback_temp_dir
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")

    #  UI setup 

    def setup_dark_mode(self):
        self.root.configure(bg=self.colors['bg'])
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook',
                        background=self.colors['bg'],
                        borderwidth=2,
                        darkcolor=self.colors['border'],
                        lightcolor=self.colors['border'])
        style.configure('TNotebook.Tab',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       padding=[18, 10],
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor=self.colors['bg'])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent']), ('active', self.colors['button_active'])],
                 foreground=[('selected', '#ffffff')])
        style.layout('TNotebook.Tab', [('Notebook.tab', {'sticky': 'nswe', 'children': [('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [('Notebook.label', {'side': 'top', 'sticky': ''})]})]})])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelframe', background=self.colors['secondary'], foreground=self.colors['fg'])
        style.configure('TLabelframe.Label',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=('Arial', 10, 'bold'))
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_fg'])

    def setup_menubar(self):
        self.menubar = tk.Menu(self.root,
                               bg=self.colors['button_bg'],
                               fg=self.colors['button_fg'],
                               activebackground=self.colors['accent'],
                               activeforeground='#ffffff',
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat', bd=0)

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

        blockmesh_menu = tk.Menu(self.menubar, tearoff=0,
                                 bg=self.colors['secondary'],
                                 fg=self.colors['fg'],
                                 activebackground=self.colors['accent'],
                                 activeforeground='#ffffff',
                                 font=('Segoe UI', 10),
                                 relief='solid', bd=1)
        blockmesh_menu.add_command(label="Import BlockMesh...", command=self.import_blockmesh)
        self.menubar.add_cascade(label="BlockMesh", menu=blockmesh_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=self.colors['secondary'],
                            fg=self.colors['fg'],
                            activebackground=self.colors['accent'],
                            activeforeground='#ffffff',
                            font=('Segoe UI', 10),
                            relief='solid', bd=1)
        help_menu.add_command(label="Tab Help (F1)", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)

    def setup_shortcuts(self):
        self.root.bind('<Control-z>', self.on_undo_event)
        self.root.bind('<Control-Z>', self.on_undo_event)
        self.root.bind('<Control-y>', self.on_redo_event)
        self.root.bind('<Control-Y>', self.on_redo_event)
        self.root.bind('<Control-Shift-Z>', self.on_redo_event)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<F1>',  self.show_help)

    def on_undo_event(self, event):
        self.on_undo()
        return "break"

    def on_redo_event(self, event):
        self.on_redo()
        return "break"

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def on_undo(self):
        if not self.history_manager.undo():
            print("Nothing to undo")

    def on_redo(self):
        if not self.history_manager.redo():
            print("Nothing to redo")

    #  F1 Help 

    def show_help(self, event=None):
        """Show context-sensitive help for the currently visible tab."""
        try:
            tab_idx = self.notebook.index(self.notebook.select())
        except Exception:
            tab_idx = 0

        title, body = HELP_TEXTS.get(tab_idx, ("Help", "No help available for this tab."))

        win = tk.Toplevel(self.root)
        win.title(f"Help — {title}")
        
        # Larger, more comfortable size and centered on parent
        win.geometry("900x700")
        win.minsize(600, 400)
        
        # Center on parent window
        win.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        win_w = win.winfo_width()
        win_h = win.winfo_height()
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        win.geometry(f"+{x}+{y}")
        
        win.configure(bg=self.colors['secondary'])
        win.transient(self.root)
        win.grab_set()
        win.focus_set()

        # Main container with proper weight for resizing
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)  # Text area expands

        # Header frame (fixed height)
        header_frame = tk.Frame(win, bg=self.colors['secondary'], height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        # Accent bar
        tk.Frame(header_frame, bg=self.colors['accent'], height=3).pack(fill=tk.X, side=tk.TOP)
        
        # Title
        tk.Label(header_frame, text=title,
                font=("Segoe UI", 14, "bold"),
                bg=self.colors['secondary'], fg=self.colors['accent'],
                anchor=tk.W).pack(fill=tk.X, side=tk.TOP, pady=(10, 0))

        # Separator
        tk.Frame(win, bg=self.colors['border'], height=1).grid(row=0, column=0, sticky="sew", padx=20, pady=(55, 0))

        # Body text frame (expanding)
        txt_frame = tk.Frame(win, bg=self.colors['secondary'])
        txt_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        txt_frame.grid_columnconfigure(0, weight=1)
        txt_frame.grid_rowconfigure(0, weight=1)

        # Scrollbar
        sb = tk.Scrollbar(txt_frame, bg=self.colors['secondary'], troughcolor=self.colors['bg'])
        sb.grid(row=0, column=1, sticky="ns")

        # Text widget with better font and spacing
        txt = tk.Text(txt_frame,
                    font=("Segoe UI", 10),
                    bg=self.colors['bg'],
                    fg=self.colors['fg'],
                    insertbackground=self.colors['fg'],
                    relief=tk.FLAT,
                    wrap=tk.WORD,
                    yscrollcommand=sb.set,
                    padx=12, pady=12,
                    spacing1=3, spacing2=3, spacing3=3)
        txt.grid(row=0, column=0, sticky="nsew")
        sb.config(command=txt.yview)

        # Configure text tags for formatting
        txt.tag_configure("heading", foreground=self.colors['success'],
                        font=("Segoe UI", 10, "bold"))
        txt.tag_configure("key", foreground=self.colors['warning'])
        txt.tag_configure("bullet", foreground=self.colors['accent'],
                        font=("Segoe UI", 10, "bold"))
        txt.tag_configure("normal", foreground=self.colors['fg'])
        txt.tag_configure("indent", lmargin1=20, lmargin2=30)

        # Parse and insert content with formatting
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            if not stripped:
                txt.insert(tk.END, "\n", "normal")
            elif stripped.startswith('•') or stripped.startswith('-'):
                # Bullet point
                txt.insert(tk.END, "  • " + stripped[1:].strip() + "\n", "bullet")
            elif stripped.startswith('  ') and i > 0 and lines[i-1].strip():
                # Indented continuation
                txt.insert(tk.END, line + "\n", "indent")
            elif stripped == stripped.upper() and len(stripped) > 2 and not stripped.startswith(' '):
                # Section header (all caps)
                if i > 0:
                    txt.insert(tk.END, "\n", "normal")
                txt.insert(tk.END, line + "\n", "heading")
            else:
                txt.insert(tk.END, line + "\n", "normal")
            i += 1

        txt.config(state=tk.DISABLED)

        # Bottom frame with tab switcher and close button
        bottom_frame = tk.Frame(win, bg=self.colors['secondary'], height=50)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        bottom_frame.grid_propagate(False)
        bottom_frame.grid_columnconfigure(0, weight=1)  # Push buttons to edges

        # Tab switcher on left
        nav_frame = tk.Frame(bottom_frame, bg=self.colors['secondary'])
        nav_frame.grid(row=0, column=0, sticky="w")

        tab_labels = ["1·Settings", "2·Points", "3·Edges",
                    "4·Hex", "5·Patches", "6·Export"]

        def switch_help(idx, current_win=win):
            current_win.destroy()
            saved = self.notebook.index(self.notebook.select())
            self.notebook.select(idx)
            self.show_help()

        for i, lbl in enumerate(tab_labels):
            bg = self.colors['accent'] if i == tab_idx else self.colors['secondary']
            fg = "white" if i == tab_idx else self.colors['fg']
            btn = tk.Button(nav_frame, text=lbl, command=lambda idx=i: switch_help(idx),
                        bg=bg, fg=fg,
                        font=("Segoe UI", 8), relief=tk.FLAT if i == tab_idx else tk.SOLID,
                        bd=1 if i != tab_idx else 0,
                        highlightbackground=self.colors['border'],
                        padx=8, pady=4, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=(0, 4))

        # Close button on right
        tk.Button(bottom_frame, text="Close (Esc)",
                command=win.destroy,
                bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                padx=20, pady=6, cursor="hand2").grid(row=0, column=1, sticky="e")

        # Bindings
        win.bind("<F1>", lambda e: win.destroy())
        win.bind("<Escape>", lambda e: win.destroy())
        
        return "break"

    def _show_about(self):
        messagebox.showinfo(
            "About BlockMeshAuto",
            "BlockMeshAuto v2.x\n"
            "OpenFOAM blockMesh GUI\n\n"
            "License: CC0 1.0 Universal\n"
            "F1 — Tab-specific help\n"
            "F11 — Toggle full-screen\n"
            "Ctrl+Z / Ctrl+Y — Undo / Redo"
        )

    #  BlockMesh import 

    def import_blockmesh(self):
        has_geometry = len(self.mesh_data.points) > 0
        if has_geometry:
            result = messagebox.askyesnocancel(
                "Import BlockMesh",
                "Importing a blockMeshDict will clear all existing geometry.\n\n"
                "Save current project before importing?",
                icon='warning'
            )
            if result is None:
                return
            elif result:
                self.save_to_json()

        success = import_blockmesh_file(self.mesh_data, self.root)
        if success:
            self._update_all_views()
            messagebox.showinfo("Import Successful",
                              f"Project imported: {self.mesh_data.project_name}")

    #  Notebook / tabs 

    def setup_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_project = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_2d      = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_edges   = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_grid    = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_3d      = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_export  = tk.Frame(self.notebook, bg=self.colors['bg'])

        self.notebook.add(self.tab_project, text="1. Project Settings")
        self.notebook.add(self.tab_2d,      text="2. Points & Connections")
        self.notebook.add(self.tab_edges,   text="3. Edge Editor")
        self.notebook.add(self.tab_grid,    text="4. Hex Blocks")
        self.notebook.add(self.tab_3d,      text="5. Hex View & Patches")
        self.notebook.add(self.tab_export,  text="6. Export blockMeshDict")

    def setup_tabs(self):
        self.project_settings = TabProjectSettings(self.tab_project, self.mesh_data)
        self.editor_2d        = Tab2DEditor(self.tab_2d, self.mesh_data)
        self.edge_editor      = Tab3EdgeEditor(self.tab_edges, self.mesh_data)
        self.hex_blocks       = TabHexBlockMaking(self.tab_grid, self.mesh_data)
        self.patches_3d       = Tab5HexPatches(self.tab_3d, self.mesh_data)
        self.export_tab       = TabExport(self.tab_export, self.mesh_data)

    #  File helpers 

    def get_temp_filename(self):
        safe_name = self.mesh_data.get_safe_project_name()
        return os.path.join(self.get_temp_dir(), f"{safe_name}_temp.json")

    def get_default_save_filename(self):
        safe_name = self.mesh_data.get_safe_project_name()
        return f"{safe_name}.json"

    #  Save / Load 

    def save_to_json(self):
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
                test_path = os.path.dirname(filename)
                if test_path and not os.path.exists(test_path):
                    os.makedirs(test_path, exist_ok=True)
                data = self.mesh_data.to_dict()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Project saved to {filename}")
            except PermissionError:
                messagebox.showerror("Permission Error",
                    f"Cannot save to {filename}: Permission denied.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def load_from_json(self):
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
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure: root must be an object")
                self.mesh_data.from_dict(data)
                self._last_safe_project_name = self.mesh_data.get_safe_project_name()
                self._update_all_views()
                messagebox.showinfo("Success", f"Project loaded from {filename}")
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON file: {str(e)}")
            except PermissionError:
                messagebox.showerror("Permission Error",
                    f"Cannot read {filename}: Permission denied.")
            except ValueError as e:
                messagebox.showerror("Data Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
                import traceback
                traceback.print_exc()

    #  View update 

    def _update_all_views(self):
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

    #  Auto-save (with rename cleanup) 

    def auto_save(self):
        try:
            if hasattr(self.project_settings, 'save_all_settings'):
                try:
                    self.project_settings.save_all_settings()
                except Exception as e:
                    if self.auto_save_error_count < 3:
                        print(f"Auto-save warning (settings): {e}")

            current_safe_name = self.mesh_data.get_safe_project_name()

            # Rename detection: delete the old temp file if the name changed
            if (self._last_safe_project_name and
                    self._last_safe_project_name != current_safe_name):
                old_temp = os.path.join(
                    self.get_temp_dir(),
                    f"{self._last_safe_project_name}_temp.json"
                )
                if os.path.exists(old_temp):
                    try:
                        os.remove(old_temp)
                        print(f"Auto-save: removed old temp file '{old_temp}'")
                    except Exception as e:
                        print(f"Auto-save: could not remove old temp file: {e}")

            self._last_safe_project_name = current_safe_name

            temp_file = self.get_temp_filename()
            temp_dir  = os.path.dirname(temp_file)
            os.makedirs(temp_dir, exist_ok=True)

            data = self.mesh_data.to_dict()
            temp_write_file = temp_file + ".tmp"
            with open(temp_write_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rename(temp_write_file, temp_file)
            self.auto_save_error_count = 0

        except PermissionError as e:
            self.auto_save_error_count += 1
            if self.auto_save_error_count <= 3:
                print(f"Auto-save permission error (attempt {self.auto_save_error_count}): {e}")
        except Exception as e:
            self.auto_save_error_count += 1
            if self.auto_save_error_count <= 3:
                print(f"Auto-save error (attempt {self.auto_save_error_count}): {e}")

    #  New project 

    def new_project(self):
        """Start a new project, fully clearing all tab state."""
        result = messagebox.askyesnocancel("New Project",
                                          "Save current project before starting new?")
        if result is None:
            return
        elif result:
            self.save_to_json()

        # Fresh data model
        self.mesh_data = MeshData()
        self._last_safe_project_name = self.mesh_data.get_safe_project_name()

        # Fresh history manager
        self.history_manager = HistoryManager(self.mesh_data, max_states=5)
        self.mesh_data.set_save_state_callback(self.history_manager.save_state)
        self.history_manager.set_update_callback(self._update_all_views)

        # Update simple top-level references
        self.project_settings.mesh_data = self.mesh_data
        self.editor_2d.mesh_data        = self.mesh_data
        self.edge_editor.mesh_data      = self.mesh_data
        self.hex_blocks.mesh_data       = self.mesh_data
        self.export_tab.mesh_data       = self.mesh_data

        # Tab 3: update viewer + edge model
        try:
            if hasattr(self.edge_editor, 'viewer') and self.edge_editor.viewer:
                self.edge_editor.viewer.mesh_data = self.mesh_data
            if hasattr(self.edge_editor, 'edge_editor'):
                inner = self.edge_editor.edge_editor
                if hasattr(inner, 'viewer') and inner.viewer:
                    inner.viewer.mesh_data = self.mesh_data
                if hasattr(inner, 'edge_model') and inner.edge_model:
                    inner.edge_model.mesh_data = self.mesh_data
        except Exception as e:
            print(f"Warning: Could not update tab3 nested references: {e}")

        # Tab 4: update viewer
        try:
            if hasattr(self.hex_blocks, 'viewer') and self.hex_blocks.viewer:
                self.hex_blocks.viewer.mesh_data = self.mesh_data
                self.hex_blocks.viewer._rebuild_coord_cache()
        except Exception as e:
            print(f"Warning: Could not update tab4 viewer: {e}")

        # Tab 5: reset() updates ALL nested references
        try:
            self.patches_3d.reset(self.mesh_data)
        except Exception as e:
            print(f"Warning: Could not reset tab5: {e}")

        # Refresh UI
        try:
            self.project_settings.update_display()
        except Exception:
            pass

        try:
            self.editor_2d.selected_points = []
            self.editor_2d.dual_view_layers = []
            self.editor_2d.dual_view_var.set(False)
            self.editor_2d.update_layer_list()
            self.editor_2d.update_dual_view_buttons()
            self.editor_2d.update_plot()
        except Exception:
            pass

        try:
            self.edge_editor._reset_creation()
            self.edge_editor._update_edge_list()
        except Exception:
            pass

        try:
            self.hex_blocks.refresh_layers()
            self.hex_blocks.update_block_list()
            if self.hex_blocks.viewer:
                self.hex_blocks.viewer.draw()
        except Exception:
            pass

        try:
            self.export_tab.update_summary()
        except Exception:
            pass

        messagebox.showinfo("New Project", "Started a new project")


def main():
    # Parse optional directory or .json file argument
    working_dir = None
    json_file = None
    args = sys.argv[1:]
    for arg in args:
        if arg in ('-h', '--help'):
            print("Usage: blockMeshAuto [path]")
            print("  path  Optional working directory OR a .json project file.")
            print("        Directory: if system/blockMeshDict exists, you will")
            print("                   be offered to auto-import it.")
            print("        JSON file: loads the project directly on startup.")
            sys.exit(0)
        if not arg.startswith('-'):
            abs_arg = os.path.abspath(arg)
            if os.path.isdir(abs_arg):
                working_dir = abs_arg
            elif os.path.isfile(abs_arg) and abs_arg.lower().endswith('.json'):
                json_file = abs_arg
                # Set working dir to the file's parent so auto-save goes there
                working_dir = os.path.dirname(abs_arg)
            else:
                print(f"Warning: '{arg}' is not a valid directory or .json file — ignoring.")

    root = tk.Tk()
    app = MeshBuilderApp(root, working_dir=working_dir)

    # If a JSON file was passed, load it after the window is ready
    if json_file:
        def _load_json_on_startup():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure: root must be an object")
                app.mesh_data.from_dict(data)
                app._last_safe_project_name = app.mesh_data.get_safe_project_name()
                app._update_all_views()
                app.root.title(f"BlockmeshAuto — {os.path.basename(json_file)}")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Load Error", f"Could not load '{json_file}':\n{e}")
        root.after(400, _load_json_on_startup)

    root.mainloop()


if __name__ == "__main__":
    main()