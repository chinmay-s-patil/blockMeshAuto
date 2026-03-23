"""
Hex Block Making Tab - With embedded 3D viewer and 4 sub-tabs
Vertex Order for Hex Block (OpenFOAM standard):
    Bottom face (z=min): 0-1-2-3 (counter-clockwise when viewed from -z)
    Top face (z=max): 4-5-6-7 (counter-clockwise when viewed from +z)
    Vertical edges: 0-4, 1-5, 2-6, 3-7

DESIGN: Dark mode matching tab2 and tab3 with LabelFrame borders
Toggle switches for layer visibility

UPDATED for new data structure: Uses global point IDs
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import numpy as np
import math

from tab4_Hex.tab4_viewer import EmbeddedViewer
from tab4_Hex.tab4_hex_editor import HexBlockEditor
from tab4_Hex.tab4_utils import (
    auto_sort_hex_points,
    calculate_divisions_from_cell_size,
    get_block_vertices,
    validate_hex_points,
    get_next_hex_id,
    check_duplicate_hex
)


class ToggleSwitch(tk.Canvas):
    """Custom toggle switch widget"""
    def __init__(self, parent, width=44, height=22, bg='#252526', 
                 fg_on='#4ec9b0', fg_off='#3e3e42', 
                 toggle_bg='#1e1e1e', command=None, initial=True):
        super().__init__(parent, width=width, height=height, 
                        bg=bg, highlightthickness=0, cursor='hand2')
        self.width = width
        self.height = height
        self.fg_on = fg_on
        self.fg_off = fg_off
        self.toggle_bg = toggle_bg
        self.command = command
        self.state = initial
        self.padding = 2
        self.toggle_radius = (height - 2 * self.padding) // 2

        self.bind('<Button-1>', self._toggle)
        self.draw()

    def _toggle(self, event=None):
        self.state = not self.state
        self.draw()
        if self.command:
            self.command(self.state)

    def set_state(self, state):
        self.state = state
        self.draw()

    def get_state(self):
        return self.state

    def draw(self):
        self.delete('all')
        # Background (track)
        bg_color = self.fg_on if self.state else self.fg_off
        # Rounded rectangle background
        self.create_oval(self.padding, self.padding, 
                        self.padding + self.height - 2*self.padding, 
                        self.height - self.padding,
                        fill=bg_color, outline='')
        self.create_oval(self.width - self.padding - (self.height - 2*self.padding), 
                        self.padding,
                        self.width - self.padding, 
                        self.height - self.padding,
                        fill=bg_color, outline='')
        self.create_rectangle(self.padding + self.toggle_radius, self.padding,
                           self.width - self.padding - self.toggle_radius, 
                           self.height - self.padding,
                           fill=bg_color, outline='')

        # Toggle circle
        if self.state:
            x_pos = self.width - self.padding - self.toggle_radius
        else:
            x_pos = self.padding + self.toggle_radius
        self.create_oval(x_pos - self.toggle_radius + 2, self.padding + 2,
                        x_pos + self.toggle_radius - 2, self.height - self.padding - 2,
                        fill=self.toggle_bg, outline='')


class LayerToggleItem(tk.Frame):
    """Layer item with toggle switch"""
    def __init__(self, parent, layer_name, z_value, num_points, 
                 colors, toggle_command, initial_state=True):
        super().__init__(parent, bg=colors['secondary'])

        self.layer_name = layer_name
        self.colors = colors

        # Layer info label
        info_text = f"{layer_name} (z={z_value:.2f}, {num_points} pts)"
        self.label = tk.Label(self, text=info_text, 
                             font=("Segoe UI", 9), 
                             bg=colors['secondary'], 
                             fg=colors['fg'],
                             anchor='w')
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Toggle switch
        self.toggle = ToggleSwitch(self, width=44, height=22,
                                  bg=colors['secondary'],
                                  fg_on=colors['success'],
                                  fg_off=colors['border'],
                                  toggle_bg=colors['bg'],
                                  command=self._on_toggle,
                                  initial=initial_state)
        self.toggle.pack(side=tk.RIGHT, padx=(5, 0))

        self.toggle_command = toggle_command

    def _on_toggle(self, state):
        if self.toggle_command:
            self.toggle_command(self.layer_name, state)

    def set_toggle_state(self, state):
        self.toggle.set_state(state)


class ScrollableToggleFrame(tk.Frame):
    """Scrollable frame for toggle items"""
    def __init__(self, parent, colors, height=200):
        super().__init__(parent, bg=colors['secondary'])

        self.colors = colors

        # Canvas for scrolling
        self.canvas = tk.Canvas(self, bg=colors['secondary'], 
                               highlightthickness=0, height=height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self, orient="vertical", 
                                     command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Style scrollbar - DARK MODE
        self.scrollbar.config(
            bg=colors['secondary'],
            troughcolor=colors['bg'],
            activebackground=colors['accent']
        )

        # Frame inside canvas for content
        self.content_frame = tk.Frame(self.canvas, bg=colors['secondary'])
        self.content_window = self.canvas.create_window((0, 0), 
                                                       window=self.content_frame,
                                                       anchor="nw")

        # Bind events
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel binding
        self._bind_mousewheel()

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.content_window, width=event.width)

    def _bind_mousewheel(self):
        def on_mousewheel(event):
            bbox = self.canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > self.canvas.winfo_height():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"

        def scroll_up(event):
            bbox = self.canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > self.canvas.winfo_height():
                self.canvas.yview_scroll(-1, "units")

        def scroll_down(event):
            bbox = self.canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > self.canvas.winfo_height():
                self.canvas.yview_scroll(1, "units")

        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Button-4>", scroll_up)
        self.canvas.bind("<Button-5>", scroll_down)

    def clear(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def add_item(self, item):
        item.pack(fill=tk.X, pady=1, padx=2)


class TabHexBlockMaking:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data

        # Dark mode colors - MATCHING TAB2/TAB3
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f44747',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'button_active': '#1177bb',
            'border': '#3e3e42',
            'canvas_bg': '#1e1e1e',
            'grid': '#3e3e42',
            'axis': '#6e6e6e',
            'select_bg': '#0e639c',
            'add_bg': '#4ec9b0',
            'connect_bg': '#ce9178',
            'delete_bg': '#f44747',
            'text_bg': '#2d2d2d',
            'text_fg': '#d4d4d4',
            'disabled_bg': '#3e3e42',
            'disabled_fg': '#808080'
        }

        # Block management - use mesh_data.hex_blocks for persistence
        self.selected_points = []  # List of point IDs - PRESERVES ORDER
        self.current_block_idx = None
        self.editing_block_idx = None  # Track which block is being edited

        # Division settings
        self.division_mode = tk.StringVar(value="direct")
        self.nx_var = tk.IntVar(value=10)
        self.ny_var = tk.IntVar(value=10)
        self.nz_var = tk.IntVar(value=10)
        self.cell_size_var = tk.DoubleVar(value=1.0)
        self.sizing_mode = tk.StringVar(value="3d")
        self.single_div_dir = tk.StringVar(value="Z")
        self.grading_type = tk.StringVar(value="simpleGrading")
        self.grading_x = tk.DoubleVar(value=1.0)
        self.grading_y = tk.DoubleVar(value=1.0)
        self.grading_z = tk.DoubleVar(value=1.0)

        # Track division entry widgets for enabling/disabling
        self.div_entries = {}  # 'X': entry_widget, 'Y': entry_widget, 'Z': entry_widget

        # Layer visibility tracking
        self.layer_visibility = {}  # layer_name -> bool

        # Viewer
        self.viewer = None

        # Edit window reference
        self.edit_window = None

        # Layer toggle items
        self.layer_items = {}  # layer_name -> LayerToggleItem

        self.setup_ui()

    @property
    def hex_blocks(self):
        """Access hex blocks from mesh_data for compatibility"""
        blocks = []
        for block_id, block_data in self.mesh_data.hex_blocks.items():
            blocks.append({
                'point_refs': block_data.get('point_refs', []),
                'divisions': block_data.get('divisions', (1, 1, 1)),
                'grading_type': block_data.get('grading_type', 'simpleGrading'),
                'grading_params': block_data.get('grading_params', {'x': 1, 'y': 1, 'z': 1})
            })
        return blocks

    def setup_ui(self):
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left: 3D View (larger, centered)
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Unified Header
        header_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(header_frame, text="4. Hex Blocks", 
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Interactive 3D Hex Block Builder (Click points to select)", 
                 font=("Segoe UI", 10, "italic"), fg=self.colors['axis'],
                 bg=self.colors['bg']).pack(side=tk.LEFT, padx=15, pady=(4,0))

        # 3D Viewer Frame
        viewer_frame = tk.Frame(left_frame, bg=self.colors['canvas_bg'])
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initialize embedded viewer
        self.viewer = EmbeddedViewer(viewer_frame, self.mesh_data, self)

        # Right: Tabbed controls with scrolling - MATCHING TAB2/TAB3 STYLE
        right_container = tk.Frame(main_frame, width=350, bg=self.colors['secondary'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_container.pack_propagate(False)

        # Create canvas for scrolling
        right_canvas = tk.Canvas(right_container, bg=self.colors['secondary'], 
                                highlightthickness=0, width=330)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = tk.Scrollbar(right_container, orient="vertical", 
                                command=right_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure canvas scrolling
        right_canvas.configure(yscrollcommand=scrollbar.set)

        # Style the scrollbar - DARK MODE
        scrollbar.config(
            bg=self.colors['secondary'],
            troughcolor=self.colors['bg'],
            activebackground=self.colors['accent']
        )

        # Create frame inside canvas for controls
        right_frame = tk.Frame(right_canvas, bg=self.colors['secondary'], width=330)

        # Create window inside canvas
        controls_window = right_canvas.create_window((0, 0), window=right_frame, anchor="nw")

        # Update scrollregion function
        def update_scrollregion(event=None):
            right_canvas.update_idletasks()
            bbox = right_canvas.bbox("all")
            if bbox:
                right_canvas.configure(scrollregion=bbox)
            right_canvas.itemconfig(controls_window, width=right_canvas.winfo_width())

        # Bind to frame resize
        right_frame.bind("<Configure>", update_scrollregion)
        right_canvas.bind("<Configure>", update_scrollregion)

        # Mouse wheel scrolling
        def on_mousewheel(event):
            bbox = right_canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > right_canvas.winfo_height():
                right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"

        def scroll_up(event):
            bbox = right_canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > right_canvas.winfo_height():
                right_canvas.yview_scroll(-1, "units")

        def scroll_down(event):
            bbox = right_canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > right_canvas.winfo_height():
                right_canvas.yview_scroll(1, "units")

        def bind_mousewheel_to_all(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", scroll_up)
            widget.bind("<Button-5>", scroll_down)
            for child in widget.winfo_children():
                bind_mousewheel_to_all(child)

        # Store reference
        self._bind_mousewheel = bind_mousewheel_to_all

        # Bind to canvas, scrollbar, and container
        right_canvas.bind("<MouseWheel>", on_mousewheel)
        right_canvas.bind("<Button-4>", scroll_up)
        right_canvas.bind("<Button-5>", scroll_down)
        scrollbar.bind("<MouseWheel>", on_mousewheel)
        right_container.bind("<MouseWheel>", on_mousewheel)
        right_container.bind("<Button-4>", scroll_up)
        right_container.bind("<Button-5>", scroll_down)

        # Store references
        self.right_canvas = right_canvas
        self.right_scrollbar = scrollbar
        self.right_frame = right_frame

        # Notebook with dark styling
        style = ttk.Style()
        style.configure("TNotebook", background=self.colors['secondary'])
        style.configure("TNotebook.Tab", background=self.colors['secondary'],
                       foreground=self.colors['fg'])
        style.map("TNotebook.Tab", background=[("selected", self.colors['accent'])])

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.tab_layers = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_points = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_sizing = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_blocks = tk.Frame(self.notebook, bg=self.colors['secondary'])

        self.notebook.add(self.tab_layers, text="Layers")
        self.notebook.add(self.tab_points, text="Points")
        self.notebook.add(self.tab_sizing, text="Sizing")
        self.notebook.add(self.tab_blocks, text="Blocks")

        self._setup_layers_tab()
        self._setup_points_tab()
        self._setup_sizing_tab()
        self._setup_blocks_tab()

        # Bind mousewheel to all created widgets recursively
        bind_mousewheel_to_all(right_frame)

        # Force update scrollregion after everything is created
        right_frame.update_idletasks()
        update_scrollregion()

        # Initialize data
        self.refresh_layers()
        self.update_block_list()

        # Initial update of division UI state
        self.update_division_ui()

    def _setup_layers_tab(self):
        """Setup the Layers selection tab - DARK MODE STYLE with LabelFrame borders and Toggle Switches"""
        frame = tk.Frame(self.tab_layers, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === LAYER SELECTION LABELFRAME ===
        layers_frame = tk.LabelFrame(frame, text="Select Layers", 
                                     padx=8, pady=8,
                                     bg=self.colors['secondary'], 
                                     fg=self.colors['fg'],
                                     highlightbackground=self.colors['border'],
                                     highlightcolor=self.colors['secondary'],
                                     highlightthickness=1,
                                     font=("Segoe UI", 10, "bold"),
                                     labelanchor='nw')
        layers_frame.pack(fill=tk.BOTH, expand=True)

        # Description
        tk.Label(layers_frame, 
                text="Toggle layers ON to show in viewer:",
                font=("Segoe UI", 9), 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))

        # Scrollable frame for layer toggles
        self.layers_scroll_frame = ScrollableToggleFrame(layers_frame, self.colors, height=180)
        self.layers_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Control buttons frame
        btn_frame = tk.Frame(layers_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(btn_frame, text="All On", command=self._all_layers_on,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 font=("Segoe UI", 9), relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="All Off", command=self._all_layers_off,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 activebackground='#d63636',
                 font=("Segoe UI", 9), relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_layers,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 font=("Segoe UI", 9), relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Status label
        self.layer_status = tk.Label(layers_frame, 
                                     text="All layers visible",
                                     fg=self.colors['axis'], 
                                     bg=self.colors['secondary'],
                                     font=("Segoe UI", 9, "italic"))
        self.layer_status.pack(pady=(5, 0))

        # === VERTEX ORDER HELP LABELFRAME ===
        help_frame = tk.LabelFrame(frame, text="Vertex Selection Order", 
                                   padx=8, pady=8,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['secondary'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 10, "bold"),
                                   labelanchor='nw')
        help_frame.pack(pady=(10, 0), fill=tk.X)

        # Use a Text widget for proper formatting
        help_text_widget = tk.Text(help_frame, height=10, wrap=tk.WORD,
                                  bg=self.colors['secondary'], 
                                  fg=self.colors['fg'],
                                  font=("Courier", 8), relief=tk.FLAT,
                                  highlightthickness=0, padx=5, pady=5)
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, """
   7--------6   Select 4 points on BOTTOM
  /|       /|   layer (counter-clockwise 
 4--------5 |   looking down)
 | |      | |   Then 4 points on TOP layer  
 | 3------|-2   (counter-clockwise looking
 |/       |/    down)
 0--------1           

Click in 3D view to select points (max 8).""")
        help_text_widget.config(state=tk.DISABLED)

    def _on_layer_toggle(self, layer_name, state):
        """Handle layer toggle"""
        self.layer_visibility[layer_name] = state
        self._update_visible_layers()

    def _update_visible_layers(self):
        """Update viewer with currently visible layers"""
        visible = [name for name, visible in self.layer_visibility.items() if visible]

        if self.viewer:
            self.viewer.set_visible_layers(visible)

        # Update status
        total = len(self.layer_visibility)
        showing = len(visible)
        if showing == total:
            self.layer_status.config(text="All layers visible", fg=self.colors['success'])
        elif showing == 0:
            self.layer_status.config(text="No layers visible", fg=self.colors['error'])
        else:
            self.layer_status.config(text=f"Showing {showing}/{total} layers", fg=self.colors['warning'])

    def _all_layers_on(self):
        """Turn all layers on"""
        for name in self.layer_visibility:
            self.layer_visibility[name] = True
        for name, item in self.layer_items.items():
            item.set_toggle_state(True)
        self._update_visible_layers()

    def _all_layers_off(self):
        """Turn all layers off"""
        for name in self.layer_visibility:
            self.layer_visibility[name] = False
        for name, item in self.layer_items.items():
            item.set_toggle_state(False)
        self._update_visible_layers()

    def _setup_points_tab(self):
        """Setup the Points selection tab - DARK MODE STYLE with LabelFrame"""
        frame = tk.Frame(self.tab_points, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        points_frame = tk.LabelFrame(frame, text="Point Selection", 
                                     padx=8, pady=8,
                                     bg=self.colors['secondary'], 
                                     fg=self.colors['fg'],
                                     highlightbackground=self.colors['border'],
                                     highlightcolor=self.colors['secondary'],
                                     highlightthickness=1,
                                     font=("Segoe UI", 10, "bold"),
                                     labelanchor='nw')
        points_frame.pack(fill=tk.BOTH, expand=True)

        info_text = """Click points in 3D view to toggle selection.
Select exactly 8 points (4 from bottom layer, 4 from top layer).

ORDER MATTERS for hex block:
Bottom layer: 0→1→2→3 (counter-clockwise, viewed from below)
Top layer: 4→5→6→7 (counter-clockwise, viewed from above)"""

        tk.Label(points_frame, text=info_text, font=("Segoe UI", 9), 
                justify=tk.LEFT, 
                fg=self.colors['fg'], 
                bg=self.colors['secondary']).pack(anchor=tk.W, pady=(5, 10))

        self.point_status = tk.Label(points_frame, text="Selected: 0/8 points",
                                     fg=self.colors['success'], 
                                     bg=self.colors['secondary'],
                                     font=("Segoe UI", 10, "bold"))
        self.point_status.pack(pady=5)

        list_frame = tk.LabelFrame(points_frame, text="Selected Points", 
                                   padx=5, pady=5,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['secondary'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 9, "bold"),
                                   labelanchor='nw')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.point_list = tk.Listbox(list_frame, height=12, font=("Courier", 9),
                                     yscrollcommand=scroll.set, 
                                     bg=self.colors['text_bg'], 
                                     fg=self.colors['text_fg'],
                                     selectbackground=self.colors['accent'],
                                     selectforeground=self.colors['button_fg'])
        self.point_list.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.point_list.yview)

        btn_frame = tk.LabelFrame(points_frame, text="Visibility Controls", 
                                  padx=5, pady=5,
                                  bg=self.colors['secondary'], 
                                  fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'],
                                  highlightcolor=self.colors['secondary'],
                                  highlightthickness=1,
                                  font=("Segoe UI", 9, "bold"),
                                  labelanchor='nw')
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Hide Selected", command=self.hide_selected,
                 bg=self.colors['warning'], fg=self.colors['bg'],
                 font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show Only Selected", command=self.show_only_selected,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show All Points", command=self.show_all,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Clear Selection", command=self.clear_point_selection,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Segoe UI", 9, "bold"), relief=tk.FLAT).pack(fill=tk.X, pady=2)

    def _setup_sizing_tab(self):
        """Setup the Sizing/Grading tab with 2D mode grey-out support"""
        frame = tk.Frame(self.tab_sizing, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === DIVISION MODE LABELFRAME ===
        div_frame = tk.LabelFrame(frame, text="Division Mode", 
                                  padx=8, pady=8,
                                  bg=self.colors['secondary'], 
                                  fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'],
                                  highlightcolor=self.colors['secondary'],
                                  highlightthickness=1,
                                  font=("Segoe UI", 10, "bold"),
                                  labelanchor='nw')
        div_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Radiobutton(div_frame, text="Direct (specify number of cells)",
                      variable=self.division_mode, value="direct",
                      command=self.update_division_ui, font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)
        tk.Radiobutton(div_frame, text="Cell Size (auto-calculate)",
                      variable=self.division_mode, value="cell_size",
                      command=self.update_division_ui, font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)

        # Direct divisions inputs
        self.direct_frame = tk.Frame(frame, bg=self.colors['secondary'])

        for label, var, key in [("X divisions:", self.nx_var, 'X'),
                                  ("Y divisions:", self.ny_var, 'Y'),
                                  ("Z divisions:", self.nz_var, 'Z')]:
            row = tk.Frame(self.direct_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                    font=("Segoe UI", 9), 
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=var, width=10,
                    font=("Segoe UI", 9), 
                    bg=self.colors['text_bg'],
                    fg=self.colors['text_fg'], 
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border'],
                    disabledbackground=self.colors['disabled_bg'],
                    disabledforeground=self.colors['disabled_fg'])
            entry.pack(side=tk.LEFT, padx=5)
            self.div_entries[key] = entry

        # Cell size mode inputs
        self.cellsize_frame = tk.Frame(frame, bg=self.colors['secondary'])

        row = tk.Frame(self.cellsize_frame, bg=self.colors['secondary'])
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text="Target cell size:", width=15, anchor=tk.W,
                font=("Segoe UI", 9), 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.cell_size_var, width=10,
                font=("Segoe UI", 9), 
                bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], 
                insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(side=tk.LEFT, padx=5)

        # === MESH TYPE LABELFRAME ===
        mode_frame = tk.LabelFrame(frame, text="Mesh Type", 
                                   padx=8, pady=8,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['secondary'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 10, "bold"),
                                   labelanchor='nw')
        mode_frame.pack(fill=tk.X, pady=(10, 10))

        tk.Radiobutton(mode_frame, text="3D Mesh",
                      variable=self.sizing_mode, value="3d",
                      command=self.update_division_ui, font=("Segoe UI", 9), 
                      bg=self.colors['secondary'], 
                      fg=self.colors['fg'], 
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)

        row2d = tk.Frame(mode_frame, bg=self.colors['secondary'])
        row2d.pack(fill=tk.X, pady=5)
        tk.Radiobutton(row2d, text="2D Mesh (1 div in:",
                      variable=self.sizing_mode, value="2d",
                      command=self.update_division_ui, font=("Segoe UI", 9), 
                      bg=self.colors['secondary'], 
                      fg=self.colors['fg'], 
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(side=tk.LEFT)

        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(row2d, text=direction,
                          variable=self.single_div_dir, value=direction,
                          command=self.update_division_ui, font=("Segoe UI", 8), 
                          bg=self.colors['secondary'], 
                          fg=self.colors['fg'], 
                          selectcolor=self.colors['bg'],
                          activebackground=self.colors['secondary'],
                          activeforeground=self.colors['accent']).pack(side=tk.LEFT, padx=2)

        # === GRADING LABELFRAME ===
        grade_frame = tk.LabelFrame(frame, text="Grading", 
                                    padx=8, pady=8,
                                    bg=self.colors['secondary'], 
                                    fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightcolor=self.colors['secondary'],
                                    highlightthickness=1,
                                    font=("Segoe UI", 10, "bold"),
                                    labelanchor='nw')
        grade_frame.pack(fill=tk.X, pady=10)

        tk.Label(grade_frame, text="simpleGrading:", 
                font=("Segoe UI", 9, "bold"),
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)

        for label, var in [("X ratio:", self.grading_x),
                          ("Y ratio:", self.grading_y),
                          ("Z ratio:", self.grading_z)]:
            row = tk.Frame(grade_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=10, anchor=tk.W,
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=8,
                    bg=self.colors['text_bg'], 
                    fg=self.colors['text_fg'],
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border']).pack(side=tk.LEFT)

        # Automake Toggle
        self.automake_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Automake (Auto-sort 8 points & create)", 
                       variable=self.automake_var, font=("Segoe UI", 9, "bold"),
                       bg=self.colors['secondary'], fg=self.colors['fg'],
                       selectcolor=self.colors['bg'],
                       activebackground=self.colors['secondary'],
                       activeforeground=self.colors['accent']).pack(anchor=tk.W, pady=(10, 0))

        # Create button
        tk.Button(frame, text="Create Hex Block", command=self.create_hex_block,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f',
                 activeforeground=self.colors['bg']).pack(fill=tk.X, pady=(5, 20))

        self.update_division_ui()

    def _setup_blocks_tab(self):
        """Setup the Blocks management tab with Edit All button"""
        frame = tk.Frame(self.tab_blocks, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === CREATED BLOCKS LABELFRAME ===
        blocks_frame = tk.LabelFrame(frame, text="Created Blocks", 
                                     padx=8, pady=8,
                                     bg=self.colors['secondary'], 
                                     fg=self.colors['fg'],
                                     highlightbackground=self.colors['border'],
                                     highlightcolor=self.colors['secondary'],
                                     highlightthickness=1,
                                     font=("Segoe UI", 10, "bold"),
                                     labelanchor='nw')
        blocks_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = tk.Frame(blocks_frame, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.block_listbox = tk.Listbox(list_frame, font=("Courier", 9),
                                        yscrollcommand=scroll.set, 
                                        bg=self.colors['text_bg'], 
                                        fg=self.colors['text_fg'],
                                        selectbackground=self.colors['accent'],
                                        selectforeground=self.colors['button_fg'])
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scroll.config(command=self.block_listbox.yview)

        btn_frame = tk.Frame(blocks_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=1)

        tk.Button(btn_frame, text="Delete", command=self.delete_block,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 activebackground='#d63636', width=6, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg=self.colors['delete_bg'], fg=self.colors['button_fg'],
                 activebackground='#d63636', width=7, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_frame, text="Edit", command=self.edit_block,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'], width=6, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🧹 Cleanup", command=self.cleanup_invalid_hexes,
                 bg=self.colors['warning'], fg=self.colors['bg'],
                 activebackground='#d63636', width=8, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        # === EDIT ALL HEXES BUTTON ===
        edit_all_btn = tk.Button(blocks_frame, text="✏️ Edit All Hexes", 
                                command=self.edit_all_hexes,
                                bg=self.colors['accent'], fg=self.colors['button_fg'],
                                font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                                activebackground=self.colors['button_active'])
        edit_all_btn.pack(fill=tk.X, pady=(10, 5))

        # Block info display
        info_frame = tk.LabelFrame(blocks_frame, text="Block Info", 
                                   padx=5, pady=5,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['secondary'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 9, "bold"),
                                   labelanchor='nw')
        info_frame.pack(fill=tk.X, pady=10)

        self.block_info = tk.Label(info_frame, text="", 
                                  font=("Segoe UI", 9), 
                                  justify=tk.LEFT, 
                                  fg=self.colors['fg'],
                                  bg=self.colors['secondary'])
        self.block_info.pack(anchor=tk.W)

    def update_division_ui(self):
        """Show/hide division inputs based on mode and handle 2D grey-out"""
        # Show/hide based on division mode
        self.direct_frame.pack_forget()
        self.cellsize_frame.pack_forget()

        if self.division_mode.get() == "direct":
            self.direct_frame.pack(fill=tk.X, pady=(10, 10))
        else:
            self.cellsize_frame.pack(fill=tk.X, pady=(10, 10))

        # Handle 2D mode grey-out
        is_2d = self.sizing_mode.get() == "2d"
        disabled_dir = self.single_div_dir.get() if is_2d else None

        # Update entry states
        for direction, entry in self.div_entries.items():
            if is_2d and direction == disabled_dir:
                # Grey out this direction - set to 1 and disable
                if direction == 'X':
                    self.nx_var.set(1)
                elif direction == 'Y':
                    self.ny_var.set(1)
                elif direction == 'Z':
                    self.nz_var.set(1)
                entry.config(state='disabled')
            else:
                entry.config(state='normal')

    def edit_all_hexes(self):
        """Open dialog to edit all hex blocks at once"""
        if not self.mesh_data.hex_blocks:
            messagebox.showwarning("Warning", "No hex blocks to edit")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit All Hex Blocks")
        dialog.geometry("400x500")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.configure(bg=self.colors['secondary'])

        frame = tk.Frame(dialog, padx=15, pady=15, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Batch Update All Hex Blocks", 
                font=("Segoe UI", 12, "bold"), 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(pady=(0, 10))

        # Mode selection
        mode_frame = tk.LabelFrame(frame, text="Update Mode", 
                                   padx=8, pady=8,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 10, "bold"))
        mode_frame.pack(fill=tk.X, pady=5)

        update_mode = tk.StringVar(value="cell_size")

        tk.Radiobutton(mode_frame, text="Set divisions from cell size",
                      variable=update_mode, value="cell_size",
                      font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg']).pack(anchor=tk.W)
        tk.Radiobutton(mode_frame, text="Set fixed divisions",
                      variable=update_mode, value="fixed",
                      font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg']).pack(anchor=tk.W)

        # Cell size input
        cell_frame = tk.LabelFrame(frame, text="Cell Size Settings", 
                                   padx=8, pady=8,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightthickness=1,
                                   font=("Segoe UI", 10, "bold"))
        cell_frame.pack(fill=tk.X, pady=5)

        cell_size_var = tk.DoubleVar(value=1.0)
        tk.Label(cell_frame, text="Target cell size:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        tk.Entry(cell_frame, textvariable=cell_size_var,
                bg=self.colors['text_bg'],
                fg=self.colors['text_fg'],
                insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)

        # Fixed divisions input
        fixed_frame = tk.LabelFrame(frame, text="Fixed Divisions", 
                                    padx=8, pady=8,
                                    bg=self.colors['secondary'], 
                                    fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightthickness=1,
                                    font=("Segoe UI", 10, "bold"))
        fixed_frame.pack(fill=tk.X, pady=5)

        nx_var = tk.IntVar(value=10)
        ny_var = tk.IntVar(value=10)
        nz_var = tk.IntVar(value=10)

        for label, var in [("X divisions:", nx_var),
                          ("Y divisions:", ny_var),
                          ("Z divisions:", nz_var)]:
            row = tk.Frame(fixed_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10,
                    bg=self.colors['text_bg'],
                    fg=self.colors['text_fg'],
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border']).pack(side=tk.LEFT, padx=5)

        # 2D mode option
        is_2d_var = tk.BooleanVar(value=False)
        div_2d_var = tk.StringVar(value="Z")

        tk.Checkbutton(frame, text="Apply as 2D mesh (1 division in direction):", 
                      variable=is_2d_var,
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'],
                      font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(10, 0))

        dir_frame = tk.Frame(frame, bg=self.colors['secondary'])
        dir_frame.pack(fill=tk.X)
        for d in ["X", "Y", "Z"]:
            tk.Radiobutton(dir_frame, text=d, variable=div_2d_var, value=d,
                          bg=self.colors['secondary'], fg=self.colors['fg'],
                          selectcolor=self.colors['bg']).pack(side=tk.LEFT, padx=5)

        # Preview
        preview_label = tk.Label(frame, text=f"Will update {len(self.mesh_data.hex_blocks)} block(s)",
                                bg=self.colors['secondary'], 
                                fg=self.colors['success'],
                                font=("Segoe UI", 10, "bold"))
        preview_label.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)

        def apply_changes():
            self.mesh_data.save_state()

            updated = 0
            for block_id, block_data in self.mesh_data.hex_blocks.items():
                vertices = get_block_vertices(block_data, self.mesh_data)
                if vertices is None:
                    continue

                if update_mode.get() == "cell_size":
                    nx, ny, nz = calculate_divisions_from_cell_size(vertices, cell_size_var.get())
                else:
                    nx, ny, nz = nx_var.get(), ny_var.get(), nz_var.get()

                # Apply 2D mode if checked
                if is_2d_var.get():
                    if div_2d_var.get() == "X":
                        nx = 1
                    elif div_2d_var.get() == "Y":
                        ny = 1
                    elif div_2d_var.get() == "Z":
                        nz = 1

                block_data['divisions'] = (nx, ny, nz)
                updated += 1

            self.update_block_list()
            if self.viewer:
                self.viewer.draw()

            dialog.destroy()
            messagebox.showinfo("Success", f"Updated {updated} block(s)")

        tk.Button(btn_frame, text="✓ Apply to All", command=apply_changes,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(fill=tk.X, pady=2)

    def refresh_layers(self):
        """Refresh layer list with toggle switches"""
        self.layers_scroll_frame.clear()
        self.layer_items.clear()

        sorted_layers = sorted(self.mesh_data.layers.items(), 
                              key=lambda x: x[1].get('z', 0))

        for name, layer_data in sorted_layers:
            if name not in self.layer_visibility:
                self.layer_visibility[name] = True

        for name, layer_data in sorted_layers:
            z = layer_data.get('z', 0)
            num_points = len(layer_data.get('point_refs', []))

            item = LayerToggleItem(
                self.layers_scroll_frame.content_frame,
                name, z, num_points,
                self.colors,
                self._on_layer_toggle,
                self.layer_visibility.get(name, True)
            )
            self.layers_scroll_frame.add_item(item)
            self.layer_items[name] = item

        self._update_visible_layers()

    def reset_view(self):
        """Reset 3D view"""
        if self.viewer:
            self.viewer.reset_view()

    def refresh_view(self):
        """Refresh 3D visualization"""
        if self.viewer:
            self.viewer.refresh()

    def on_selection_changed(self, selected_list):
        """Called by viewer when points are clicked"""
        self.selected_points = list(selected_list)

        if len(self.selected_points) == 8 and getattr(self, 'automake_var', None) and self.automake_var.get():
            self.selected_points = auto_sort_hex_points(self.selected_points, self.mesh_data)
            self.viewer.selected_points = self.selected_points.copy()

            self.update_point_list()
            self.point_status.config(text=f"Selected: 8/8 points (Automake)")

            self.create_hex_block()
            return

        self.update_point_list()
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")

    def update_point_list(self):
        """Update the points listbox - PRESERVES ORDER"""
        self.point_list.delete(0, tk.END)
        for i, point_id in enumerate(self.selected_points):
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                layer_name = None
                for l_name, l_data in self.mesh_data.layers.items():
                    if point_id in l_data.get('point_refs', []):
                        layer_name = l_name
                        break

                coords = (point_data['x'], point_data['y'], point_data['z'])
                layer_text = layer_name if layer_name else "unknown"
                self.point_list.insert(tk.END,
                    f"[{i}] Point {point_id}: {layer_text} "
                    f"({coords[0]:.2f},{coords[1]:.2f},{coords[2]:.2f})")

    def hide_selected(self):
        """Hide selected points"""
        if self.viewer:
            self.viewer.hide_selected()

    def show_only_selected(self):
        """Show only selected points"""
        if self.viewer:
            self.viewer.show_only_selected()

    def show_all(self):
        """Show all points"""
        if self.viewer:
            self.viewer.show_all()

    def clear_point_selection(self):
        """Clear point selection"""
        self.selected_points = []
        if self.viewer:
            self.viewer.clear_selection()
        self.update_point_list()
        self.point_status.config(text="Selected: 0/8 points")

    def create_hex_block(self):
        """Create a hexahedral block from selected points"""
        # Auto-sort 8 points into proper order before validation
        if len(self.selected_points) == 8:
            pts = []
            all_valid = True
            for pid in self.selected_points:
                p = self.mesh_data.get_point(pid)
                if p:
                    pts.append((pid, p['x'], p['y'], p['z']))
                else:
                    all_valid = False

            if all_valid and len(pts) == 8:
                pts.sort(key=lambda p: p[3])
                bottom = pts[0:4]
                top = pts[4:8]

                def sort_quad(quad):
                    cx = sum(p[1] for p in quad) / 4
                    cy = sum(p[2] for p in quad) / 4
                    return sorted(quad, key=lambda p: math.atan2(p[2] - cy, p[1] - cx))

                bottom = sort_quad(bottom)
                top = sort_quad(top)

                original_order = self.selected_points.copy()
                self.selected_points = [p[0] for p in bottom + top]

                if self.selected_points != original_order:
                    if self.viewer:
                        self.viewer.selected_points = self.selected_points.copy()
                    self.update_point_list()

        # Validate exactly 8 unique points
        is_valid, error_msg = validate_hex_points(self.selected_points)
        if not is_valid:
            messagebox.showwarning("Warning", error_msg)
            return

        # Check for duplicate hex
        duplicate_id = check_duplicate_hex(self.selected_points, self.mesh_data.hex_blocks)
        if duplicate_id is not None:
            messagebox.showerror("Error", 
                f"A hex block with these 8 points already exists!\n"
                f"Duplicate of: Hex {duplicate_id}\n"
                f"Cannot create duplicate hex blocks.")
            return

        # Validate points come from exactly 2 layers
        layers_used = {}
        for point_id in self.selected_points:
            for l_name, l_data in self.mesh_data.layers.items():
                if point_id in l_data.get('point_refs', []):
                    layers_used[point_id] = l_name
                    break

        unique_layers = set(layers_used.values())
        if len(unique_layers) != 2:
            messagebox.showerror("Error", "Points must come from exactly 2 layers (4 bottom, 4 top)")
            return

        # Validate layer order
        vertices = []
        for point_id in self.selected_points:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                vertices.append((point_data['x'], point_data['y'], point_data['z']))

        if len(vertices) != 8:
            messagebox.showerror("Error", "Could not retrieve all point coordinates")
            return

        z_bottom = [v[2] for v in vertices[0:4]]
        z_top = [v[2] for v in vertices[4:8]]

        if max(z_bottom) > min(z_top):
            messagebox.showerror("Error", 
                "First 4 points must be on the bottom layer (lower Z),\n"
                "and last 4 points must be on the top layer (higher Z)")
            return

        # Calculate divisions
        if self.division_mode.get() == "direct":
            nx, ny, nz = self.nx_var.get(), self.ny_var.get(), self.nz_var.get()
        else:
            cell_size = self.cell_size_var.get()
            nx, ny, nz = calculate_divisions_from_cell_size(vertices, cell_size)

        # Apply 2D mode
        if self.sizing_mode.get() == "2d":
            if self.single_div_dir.get() == "X":
                nx = 1
            elif self.single_div_dir.get() == "Y":
                ny = 1
            elif self.single_div_dir.get() == "Z":
                nz = 1

        self.mesh_data.save_state()

        block_id = get_next_hex_id(self.mesh_data.hex_blocks)

        self.mesh_data.hex_blocks[block_id] = {
            'point_refs': list(self.selected_points),
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {
                'x': self.grading_x.get(),
                'y': self.grading_y.get(),
                'z': self.grading_z.get()
            }
        }

        existing_ids = [int(k) for k in self.mesh_data.hex_blocks.keys() if str(k).isdigit()]
        if existing_ids:
            self.mesh_data.next_block_id = max(existing_ids) + 1
        else:
            self.mesh_data.next_block_id = 1

        self.update_block_list()
        self.clear_point_selection()
        if self.viewer:
            self.viewer.draw()
        messagebox.showinfo("Success", f"Hex Block {block_id} created!\n\n"
                        f"Vertex order: 0-1-2-3 (bottom), 4-5-6-7 (top)\n"
                        f"Divisions: {nx}×{ny}×{nz}\n"
                        f"Grading: ({self.grading_x.get()}, {self.grading_y.get()}, {self.grading_z.get()})")

    def update_block_list(self):
        """Update block list display - shows warnings for invalid blocks"""
        self.block_listbox.delete(0, tk.END)
        sorted_blocks = sorted(self.mesh_data.hex_blocks.items(), 
                              key=lambda x: int(x[0]) if str(x[0]).isdigit() else 999999)
        for idx, (block_id, block_data) in enumerate(sorted_blocks):
            point_refs = block_data.get('point_refs', [])
            nx, ny, nz = block_data.get('divisions', (1, 1, 1))
            grading = block_data.get('grading_type', 'simpleGrading')

            if len(point_refs) != 8:
                display_text = f"Block {block_id}: INVALID ({len(point_refs)} points)"
                self.block_listbox.insert(tk.END, display_text)
                self.block_listbox.itemconfig(idx, {'fg': '#ff4444'})
            else:
                self.block_listbox.insert(tk.END, f"Block {block_id}: {nx}×{ny}×{nz}, {grading}")

    def on_block_select(self, event):
        """Handle block selection"""
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
            block_ids = list(self.mesh_data.hex_blocks.keys())
            if self.current_block_idx < len(block_ids):
                block_id = block_ids[self.current_block_idx]
                block = self.mesh_data.hex_blocks[block_id]
                point_refs = block.get('point_refs', [])
                info = f"Points: {len(point_refs)}\nDivisions: {block.get('divisions', (1,1,1))}\nGrading: {block.get('grading_params', {})}"
                self.block_info.config(text=info)

                if self.viewer and point_refs:
                    self.viewer.set_selection(list(point_refs))

    def edit_block(self):
        """Open edit dialog for selected block using the separate editor module"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block to edit first")
            return

        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()

        block_ids = list(self.mesh_data.hex_blocks.keys())
        if self.current_block_idx >= len(block_ids):
            messagebox.showerror("Error", "Block not found")
            return

        block_id = block_ids[self.current_block_idx]
        block = self.mesh_data.hex_blocks[block_id]
        self.editing_block_idx = self.current_block_idx

        # Use the separate editor class
        editor = HexBlockEditor(self.parent, self.colors, self.mesh_data, 
                               block_id, block, self._on_block_edited)
        self.edit_window = editor.window

    def _on_block_edited(self, block_id, new_data):
        """Callback when a block is edited"""
        self.mesh_data.save_state()
        self.mesh_data.hex_blocks[block_id].update(new_data)
        self.update_block_list()
        if self.viewer:
            self.viewer.draw()
        messagebox.showinfo("Success", "Block updated!")

    def cleanup_invalid_hexes(self):
        """Remove hex blocks that don't have exactly 8 points"""
        invalid_ids = []
        for block_id, block_data in list(self.mesh_data.hex_blocks.items()):
            point_refs = block_data.get('point_refs', [])
            if len(point_refs) != 8:
                invalid_ids.append(block_id)

        if invalid_ids:
            self.mesh_data.save_state()
            for block_id in invalid_ids:
                del self.mesh_data.hex_blocks[block_id]
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
            messagebox.showinfo("Cleanup", f"Removed {len(invalid_ids)} invalid hex blocks (did not have 8 points).")
            return len(invalid_ids)
        return 0

    def delete_block(self):
        """Delete selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return

        block_ids = list(self.mesh_data.hex_blocks.keys())
        if self.current_block_idx >= len(block_ids):
            messagebox.showerror("Error", "Block not found")
            return

        block_id = block_ids[self.current_block_idx]

        if messagebox.askyesno("Confirm", "Delete block?"):
            self.mesh_data.save_state()
            del self.mesh_data.hex_blocks[block_id]
            self.current_block_idx = None
            self.block_info.config(text="")
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()

    def clear_all_blocks(self):
        """Clear all blocks"""
        if not self.mesh_data.hex_blocks:
            return
        if messagebox.askyesno("Confirm", "Delete all blocks?"):
            self.mesh_data.save_state()
            self.mesh_data.hex_blocks.clear()
            self.current_block_idx = None
            self.block_info.config(text="")
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()

    def get_hex_blocks(self):
        """Get all hex blocks"""
        return self.mesh_data.hex_blocks

    def get_block_vertices(self, block_idx):
        """Get current 3D vertices for a block from its point references"""
        block_ids = list(self.mesh_data.hex_blocks.keys())
        if block_idx < 0 or block_idx >= len(block_ids):
            return None

        block_id = block_ids[block_idx]
        block = self.mesh_data.hex_blocks[block_id]
        return get_block_vertices(block, self.mesh_data)

    def cleanup(self):
        """Call when closing"""
        if self.viewer:
            self.viewer.close()
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()