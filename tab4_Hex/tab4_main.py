"""
Hex Block Making Tab - With embedded 3D viewer and 4 sub-tabs
Vertex Order for Hex Block (OpenFOAM standard):
    Bottom face (z=min): 0-1-2-3 (counter-clockwise when viewed from -z)
    Top face (z=max): 4-5-6-7 (counter-clockwise when viewed from +z)
    Vertical edges: 0-4, 1-5, 2-6, 3-7

DESIGN: Dark mode matching tab2 and tab3 with LabelFrame borders
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import numpy as np
import math
from tab4_Hex.embedded_viewer import EmbeddedViewer


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
            'text_fg': '#d4d4d4'
        }
        
        # Block management - use mesh_data.hex_blocks for persistence
        self.selected_points = []  # List of global indices - PRESERVES ORDER
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
        
        # Viewer
        self.viewer = None
        
        # Edit window reference
        self.edit_window = None
        
        self.setup_ui()
        
    @property
    def hex_blocks(self):
        """Access hex blocks from mesh_data for persistence"""
        return self.mesh_data.hex_blocks
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View (larger, centered)
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Interactive 3D Hex Block Builder (Click points to select)",
                font=("Arial", 12, "bold"), bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=5)
        
        # 3D Viewer Frame
        viewer_frame = tk.Frame(left_frame, bg=self.colors['canvas_bg'])
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize embedded viewer
        self.viewer = EmbeddedViewer(viewer_frame, self.mesh_data, self)
        
        # Info label at bottom of viewer
        control_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="Mouse: Left-Rotate | Right-Pan | Scroll-Zoom | Click: Select | Order: Bottom CCW, Top CCW",
                font=("Arial", 9), fg=self.colors['fg'], bg=self.colors['bg']).pack(side=tk.LEFT, padx=10)
        
        # Right: Tabbed controls with scrolling - MATCHING TAB2/TAB3 STYLE
        right_container = tk.Frame(main_frame, width=380, bg=self.colors['secondary'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_container.pack_propagate(False)
        
        # Create canvas for scrolling
        right_canvas = tk.Canvas(right_container, bg=self.colors['secondary'], 
                                highlightthickness=0, width=360)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(right_container, orient="vertical", 
                                command=right_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas scrolling
        right_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Style the scrollbar
        scrollbar.config(
            bg=self.colors['secondary'],
            troughcolor=self.colors['bg'],
            activebackground=self.colors['accent']
        )
        
        # Create frame inside canvas for controls
        right_frame = tk.Frame(right_canvas, bg=self.colors['secondary'], width=360)
        
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
            right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        def bind_mousewheel_to_all(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", lambda e: right_canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: right_canvas.yview_scroll(1, "units"))
            for child in widget.winfo_children():
                bind_mousewheel_to_all(child)
        
        # Store reference
        self._bind_mousewheel = bind_mousewheel_to_all
        
        # Bind to canvas, scrollbar, and container
        right_canvas.bind("<MouseWheel>", on_mousewheel)
        right_canvas.bind("<Button-4>", lambda e: right_canvas.yview_scroll(-1, "units"))
        right_canvas.bind("<Button-5>", lambda e: right_canvas.yview_scroll(1, "units"))
        scrollbar.bind("<MouseWheel>", on_mousewheel)
        right_container.bind("<MouseWheel>", on_mousewheel)
        right_container.bind("<Button-4>", lambda e: right_canvas.yview_scroll(-1, "units"))
        right_container.bind("<Button-5>", lambda e: right_canvas.yview_scroll(1, "units"))
        
        # Store references
        self.right_canvas = right_canvas
        self.right_scrollbar = scrollbar
        self.right_frame = right_frame
        
        # Notebook with dark styling
        style = ttk.Style()
        style.theme_use('default')
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
        
        self.notebook.add(self.tab_layers, text="1. Layers")
        self.notebook.add(self.tab_points, text="2. Points")
        self.notebook.add(self.tab_sizing, text="3. Sizing")
        self.notebook.add(self.tab_blocks, text="4. Blocks")
        
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
        
    def _setup_layers_tab(self):
        """Setup the Layers selection tab - DARK MODE STYLE"""
        frame = tk.Frame(self.tab_layers, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Select Layers (Click to toggle)",
                font=("Arial", 11, "bold"), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Button(frame, text="🔄 Refresh Layers", command=self.refresh_layers,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_fg']).pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame, text="Click any layer to select/deselect (no Ctrl needed):",
                font=("Arial", 9), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        self.layer_listbox = tk.Listbox(frame, height=10, selectmode=tk.EXTENDED,
                                       exportselection=False,
                                       bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                                       selectbackground=self.colors['accent'],
                                       selectforeground=self.colors['button_fg'],
                                       highlightbackground=self.colors['border'],
                                       font=("Arial", 9))
        self.layer_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Custom binding for toggle selection without Ctrl
        self.layer_listbox.bind('<Button-1>', self._on_layer_click)
        self.layer_listbox.bind('<<ListboxSelect>>', self._on_layer_selection_changed)
        
        self.layer_status = tk.Label(frame, text="Select layers to visualize",
                                     fg=self.colors['axis'], bg=self.colors['secondary'],
                                     font=("Arial", 9, "italic"))
        self.layer_status.pack(pady=10)
        
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Select All", command=self._select_all_layers,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self._clear_all_layers,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 activebackground='#d63636',
                 font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Vertex Selection Order - NOW AS LABELFRAME with proper width
        help_frame = tk.LabelFrame(frame, text="Vertex Selection Order", 
                                   padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   font=("Arial", 9, "bold"))
        help_frame.pack(pady=10, fill=tk.X)
        
        # Use a Text widget instead of Label for proper wrapping
        help_text_widget = tk.Text(help_frame, height=12, wrap=tk.WORD,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  font=("Courier", 8), relief=tk.FLAT,
                                  highlightthickness=0, padx=5, pady=5)
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, """
   7--------6   Select 4 points on BOTTOM layer
  /|       /|   (counter-clockwise looking down)
 4--------5 |     
 | |      | |   Then 4 points on TOP layer  
 | 3------|-2   (counter-clockwise looking down)
 |/       |/          
 0--------1           
                      
Click in 3D view to select points (max 8).""")
        help_text_widget.config(state=tk.DISABLED)  # Make read-only
    
    def _on_layer_click(self, event):
        """Toggle layer selection on single click without requiring Ctrl"""
        index = self.layer_listbox.nearest(event.y)
        if self.layer_listbox.selection_includes(index):
            self.layer_listbox.selection_clear(index)
        else:
            self.layer_listbox.selection_set(index)
        return "break"
    
    def _on_layer_selection_changed(self, event=None):
        """Update viewer when layer selection changes"""
        if not self.viewer:
            return
            
        selected_indices = self.layer_listbox.curselection()
        selected_layers = []
        
        for i in selected_indices:
            layer_text = self.layer_listbox.get(i)
            layer_name = layer_text.split(' (')[0]
            selected_layers.append(layer_name)
        
        self.viewer.set_visible_layers(selected_layers)
        
        if selected_layers:
            self.layer_status.config(text=f"Showing {len(selected_layers)} layer(s)", fg=self.colors['success'])
        else:
            self.layer_status.config(text="No layers selected - showing all", fg=self.colors['axis'])
    
    def _select_all_layers(self):
        self.layer_listbox.select_set(0, tk.END)
        self._on_layer_selection_changed()
    
    def _clear_all_layers(self):
        self.layer_listbox.selection_clear(0, tk.END)
        self._on_layer_selection_changed()
        
    def _setup_points_tab(self):
        """Setup the Points selection tab - DARK MODE STYLE"""
        frame = tk.Frame(self.tab_points, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Point Selection (Global Numbers)",
                font=("Arial", 11, "bold"), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        info_text = """Click points in 3D view to toggle selection.
Select exactly 8 points (4 from bottom layer, 4 from top layer).

ORDER MATTERS for hex block:
Bottom layer: 0→1→2→3 (counter-clockwise, viewed from below)
Top layer: 4→5→6→7 (counter-clockwise, viewed from above)"""
        
        tk.Label(frame, text=info_text, font=("Arial", 9), justify=tk.LEFT, 
                fg=self.colors['fg'], bg=self.colors['secondary']).pack(anchor=tk.W, pady=(0, 10))
        
        self.point_status = tk.Label(frame, text="Selected: 0/8 points",
                                     fg=self.colors['success'], bg=self.colors['secondary'],
                                     font=("Arial", 10, "bold"))
        self.point_status.pack(pady=5)
        
        # Selected points list
        list_frame = tk.Frame(frame, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_list = tk.Listbox(list_frame, height=15, font=("Courier", 9),
                                     yscrollcommand=scroll.set, 
                                     bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                                     selectbackground=self.colors['accent'],
                                     selectforeground=self.colors['button_fg'])
        self.point_list.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.point_list.yview)
        
        # Control buttons
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Hide Selected", command=self.hide_selected,
                 bg=self.colors['warning'], fg=self.colors['bg'],
                 font=("Arial", 9, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show Only Selected", command=self.show_only_selected,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Show All Points", command=self.show_all,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 9, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Clear Selection", command=self.clear_point_selection,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold")).pack(fill=tk.X, pady=2)
        
    def _setup_sizing_tab(self):
        """Setup the Sizing/Grading tab - DARK MODE STYLE"""
        frame = tk.Frame(self.tab_sizing, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Cell Sizing & Grading",
                font=("Arial", 11, "bold"), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 10))
        
        # Division mode
        div_frame = tk.LabelFrame(frame, text="Division Mode", padx=10, pady=10,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'],
                                  highlightcolor=self.colors['accent'])
        div_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(div_frame, text="Direct (specify number of cells)",
                      variable=self.division_mode, value="direct",
                      command=self.update_division_ui, font=("Arial", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)
        tk.Radiobutton(div_frame, text="Cell Size (auto-calculate)",
                      variable=self.division_mode, value="cell_size",
                      command=self.update_division_ui, font=("Arial", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)
        
        # Direct divisions inputs
        self.direct_frame = tk.Frame(frame, bg=self.colors['secondary'])
        
        for label, var in [("X divisions:", self.nx_var),
                          ("Y divisions:", self.ny_var),
                          ("Z divisions:", self.nz_var)]:
            row = tk.Frame(self.direct_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                    font=("Arial", 9), bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10,
                    font=("Arial", 9), bg=self.colors['text_bg'],
                    fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border']).pack(side=tk.LEFT, padx=5)
        
        # Cell size mode inputs
        self.cellsize_frame = tk.Frame(frame, bg=self.colors['secondary'])
        
        row = tk.Frame(self.cellsize_frame, bg=self.colors['secondary'])
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text="Target cell size:", width=15, anchor=tk.W,
                font=("Arial", 9), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.cell_size_var, width=10,
                font=("Arial", 9), bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(side=tk.LEFT, padx=5)
        
        # 2D/3D mode
        mode_frame = tk.LabelFrame(frame, text="Mesh Type", padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'])
        mode_frame.pack(fill=tk.X, pady=(10, 10))
        
        tk.Radiobutton(mode_frame, text="3D Mesh",
                      variable=self.sizing_mode, value="3d",
                      font=("Arial", 9), bg=self.colors['secondary'], 
                      fg=self.colors['fg'], selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(anchor=tk.W)
        
        row2d = tk.Frame(mode_frame, bg=self.colors['secondary'])
        row2d.pack(fill=tk.X, pady=5)
        tk.Radiobutton(row2d, text="2D Mesh (1 div in:",
                      variable=self.sizing_mode, value="2d",
                      font=("Arial", 9), bg=self.colors['secondary'], 
                      fg=self.colors['fg'], selectcolor=self.colors['bg'],
                      activebackground=self.colors['secondary'],
                      activeforeground=self.colors['accent']).pack(side=tk.LEFT)
        
        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(row2d, text=direction,
                          variable=self.single_div_dir, value=direction,
                          font=("Arial", 8), bg=self.colors['secondary'], 
                          fg=self.colors['fg'], selectcolor=self.colors['bg'],
                          activebackground=self.colors['secondary'],
                          activeforeground=self.colors['accent']).pack(side=tk.LEFT, padx=2)
        
        # Grading section
        grade_frame = tk.LabelFrame(frame, text="Grading", padx=10, pady=10,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightcolor=self.colors['accent'])
        grade_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(grade_frame, text="simpleGrading:", font=("Arial", 9, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W)
        
        for label, var in [("X ratio:", self.grading_x),
                          ("Y ratio:", self.grading_y),
                          ("Z ratio:", self.grading_z)]:
            row = tk.Frame(grade_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=10, anchor=tk.W,
                    bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=8,
                    bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border']).pack(side=tk.LEFT)
        
        # Create button
        tk.Button(frame, text="Create Hex Block", command=self.create_hex_block,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 11, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f',
                 activeforeground=self.colors['bg']).pack(fill=tk.X, pady=20)
        
        self.update_division_ui()
        
    def _setup_blocks_tab(self):
        """Setup the Blocks management tab - DARK MODE STYLE"""
        frame = tk.Frame(self.tab_blocks, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Created Blocks",
                font=("Arial", 11, "bold"), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 10))
        
        list_frame = tk.Frame(frame, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.block_listbox = tk.Listbox(list_frame, font=("Courier", 9),
                                        yscrollcommand=scroll.set, 
                                        bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                                        selectbackground=self.colors['accent'],
                                        selectforeground=self.colors['button_fg'])
        self.block_listbox.pack(fill=tk.BOTH, expand=True)
        self.block_listbox.bind('<<ListboxSelect>>', self.on_block_select)
        scroll.config(command=self.block_listbox.yview)
        
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_block,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 activebackground='#d63636', width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_blocks,
                 bg=self.colors['delete_bg'], fg=self.colors['button_fg'],
                 activebackground='#d63636', width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit Selected", command=self.edit_block,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'], width=12).pack(side=tk.LEFT, padx=2)
        
        # Block info display
        self.block_info = tk.Label(frame, text="", font=("Arial", 9), 
                                  justify=tk.LEFT, fg=self.colors['fg'],
                                  bg=self.colors['secondary'])
        self.block_info.pack(anchor=tk.W, pady=10)
    
    def update_division_ui(self):
        """Show/hide division inputs based on mode"""
        self.direct_frame.pack_forget()
        self.cellsize_frame.pack_forget()
        
        if self.division_mode.get() == "direct":
            self.direct_frame.pack(fill=tk.X, pady=(10, 10))
        else:
            self.cellsize_frame.pack(fill=tk.X, pady=(10, 10))
    
    def refresh_layers(self):
        """Refresh layer list"""
        self.layer_listbox.delete(0, tk.END)
        for name, z in sorted(self.mesh_data.layers.items(), key=lambda x: x[1]):
            num_points = len(self.mesh_data.points[name])
            self.layer_listbox.insert(tk.END, f"{name} (z={z}, {num_points} pts)")
        
        self.layer_listbox.select_set(0, tk.END)
        self._on_layer_selection_changed()
        
    def reset_view(self):
        """Reset 3D view"""
        if self.viewer:
            self.viewer.reset_view()
    
    def refresh_view(self):
        """Refresh 3D visualization"""
        if self.viewer:
            self.viewer.refresh()
    
    def on_selection_changed(self, selected_list):
        """Called by viewer when points are clicked - PRESERVES ORDER"""
        self.selected_points = list(selected_list)
        self.update_point_list()
        self.point_status.config(text=f"Selected: {len(self.selected_points)}/8 points")
    
    def update_point_list(self):
        """Update the points listbox - PRESERVES ORDER"""
        self.point_list.delete(0, tk.END)
        for i, global_idx in enumerate(self.selected_points):
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            point_2d = self.mesh_data.points[layer][local_idx]
            coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
            self.point_list.insert(tk.END,
                f"[{i}] Point {global_idx}: {layer}[{local_idx}] "
                f"({coords_3d[0]:.2f},{coords_3d[1]:.2f},{coords_3d[2]:.2f})")
    
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
    
    def _get_3d_coords_standard(self, global_idx):
        """
        Get 3D coordinates in standard (X, Y, Z) format.
        mesh_data.get_3d_coords returns (X, Z, Y) for XY plane.
        """
        layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
        point_2d = self.mesh_data.points[layer][local_idx]
        coords_raw = self.mesh_data.get_3d_coords(layer, point_2d)
        x, z, y = coords_raw
        return (x, y, z)
    
    def create_hex_block(self):
        """Create a hexahedral block from selected points - PRESERVES ORDER"""
        if len(self.selected_points) != 8:
            messagebox.showwarning("Warning", f"Need exactly 8 points, have {len(self.selected_points)}")
            return
        
        vertices = []
        layers_used = set()
        
        for global_idx in self.selected_points:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
            layers_used.add(layer)
            coords_3d = self._get_3d_coords_standard(global_idx)
            vertices.append(coords_3d)
        
        if len(layers_used) != 2:
            messagebox.showerror("Error", "Points must come from exactly 2 layers (4 bottom, 4 top)")
            return
        
        # Validate: first 4 should be bottom layer (lower Z), last 4 should be top
        z_bottom = [v[2] for v in vertices[0:4]]
        z_top = [v[2] for v in vertices[4:8]]
        
        if max(z_bottom) > min(z_top):
            messagebox.showerror("Error", 
                "First 4 points must be on the bottom layer (lower Z),\\n"
                "and last 4 points must be on the top layer (higher Z)")
            return
        
        # Calculate divisions
        if self.division_mode.get() == "direct":
            nx, ny, nz = self.nx_var.get(), self.ny_var.get(), self.nz_var.get()
        else:
            cell_size = self.cell_size_var.get()
            nx, ny, nz = self._calculate_divisions(vertices, cell_size)
        
        # Apply 2D mode
        if self.sizing_mode.get() == "2d":
            if self.single_div_dir.get() == "X":
                nx = 1
            elif self.single_div_dir.get() == "Y":
                ny = 1
            elif self.single_div_dir.get() == "Z":
                nz = 1
        
        block = {
            'vertices': vertices,
            'point_refs': list(self.selected_points),
            'divisions': (nx, ny, nz),
            'grading_type': self.grading_type.get(),
            'grading_params': {'x': self.grading_x.get(),
                             'y': self.grading_y.get(),
                             'z': self.grading_z.get()}
        }
        
        self.mesh_data.hex_blocks.append(block)
        self.update_block_list()
        self.clear_point_selection()
        if self.viewer:
            self.viewer.draw()
        messagebox.showinfo("Success", f"Hex Block created!\\n\\n"
                           f"Vertex order: 0-1-2-3 (bottom), 4-5-6-7 (top)\\n"
                           f"Divisions: {nx}×{ny}×{nz}\\n"
                           f"Grading: ({self.grading_x.get()}, {self.grading_y.get()}, {self.grading_z.get()})")
    
    def _calculate_divisions(self, vertices, cell_size):
        """Calculate divisions from cell size using OpenFOAM edge definitions"""
        x_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(0,1), (3,2), (4,5), (7,6)]]
        y_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(1,2), (0,3), (5,6), (4,7)]]
        z_edges = [np.linalg.norm(np.array(vertices[i]) - np.array(vertices[j]))
                   for i, j in [(0,4), (1,5), (2,6), (3,7)]]
        
        nx = max(1, int(round(np.mean(x_edges) / cell_size)))
        ny = max(1, int(round(np.mean(y_edges) / cell_size)))
        nz = max(1, int(round(np.mean(z_edges) / cell_size)))
        return nx, ny, nz
    
    def update_block_list(self):
        """Update block list display"""
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.mesh_data.hex_blocks):
            nx, ny, nz = block['divisions']
            grading = block['grading_type']
            self.block_listbox.insert(tk.END, f"Block {i}: {nx}×{ny}×{nz}, {grading}")
    
    def on_block_select(self, event):
        """Handle block selection"""
        sel = self.block_listbox.curselection()
        if sel:
            self.current_block_idx = sel[0]
            block = self.mesh_data.hex_blocks[self.current_block_idx]
            verts = block['vertices']
            info = f"Vertices: {len(verts)}\\nDivisions: {block['divisions']}\\nGrading: {block['grading_params']}"
            self.block_info.config(text=info)
            
            if self.viewer and block.get('point_refs'):
                self.viewer.set_selection(list(block['point_refs']))
    
    def edit_block(self):
        """Open edit dialog for selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block to edit first")
            return
        
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()
        
        block = self.mesh_data.hex_blocks[self.current_block_idx]
        self.editing_block_idx = self.current_block_idx
        
        # Create edit window with dark mode
        self.edit_window = tk.Toplevel(self.parent)
        self.edit_window.title(f"Edit Block {self.current_block_idx}")
        self.edit_window.geometry("350x550")
        self.edit_window.transient(self.parent)
        self.edit_window.grab_set()
        self.edit_window.configure(bg=self.colors['secondary'])
        
        # Create form
        frame = tk.Frame(self.edit_window, padx=10, pady=10, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Editing Block {self.current_block_idx}", 
                font=("Arial", 12, "bold"), bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(pady=(0, 10))
        
        # Divisions
        div_frame = tk.LabelFrame(frame, text="Divisions", padx=5, pady=5,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'])
        div_frame.pack(fill=tk.X, pady=5)
        
        nx, ny, nz = block['divisions']
        
        tk.Label(div_frame, text="X divisions:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        nx_var = tk.IntVar(value=nx)
        tk.Entry(div_frame, textvariable=nx_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        tk.Label(div_frame, text="Y divisions:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        ny_var = tk.IntVar(value=ny)
        tk.Entry(div_frame, textvariable=ny_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        tk.Label(div_frame, text="Z divisions:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        nz_var = tk.IntVar(value=nz)
        tk.Entry(div_frame, textvariable=nz_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        # Grading
        grade_frame = tk.LabelFrame(frame, text="Grading", padx=5, pady=5,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'])
        grade_frame.pack(fill=tk.X, pady=5)
        
        gp = block['grading_params']
        
        tk.Label(grade_frame, text="X ratio:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        gx_var = tk.DoubleVar(value=gp['x'])
        tk.Entry(grade_frame, textvariable=gx_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        tk.Label(grade_frame, text="Y ratio:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        gy_var = tk.DoubleVar(value=gp['y'])
        tk.Entry(grade_frame, textvariable=gy_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        tk.Label(grade_frame, text="Z ratio:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W)
        gz_var = tk.DoubleVar(value=gp['z'])
        tk.Entry(grade_frame, textvariable=gz_var, bg=self.colors['text_bg'],
                fg=self.colors['text_fg'], insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(fill=tk.X)
        
        # Grading type
        tk.Label(frame, text="Grading Type:", bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(10, 0))
        grading_type_var = tk.StringVar(value=block['grading_type'])
        tk.OptionMenu(frame, grading_type_var, "simpleGrading", "edgeGrading", "multiGrading").pack(fill=tk.X)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=20)
        
        def save_changes():
            block['divisions'] = (nx_var.get(), ny_var.get(), nz_var.get())
            block['grading_params'] = {
                'x': gx_var.get(),
                'y': gy_var.get(),
                'z': gz_var.get()
            }
            block['grading_type'] = grading_type_var.get()
            
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
            self.edit_window.destroy()
            messagebox.showinfo("Success", "Block updated!")
        
        def highlight_vertices():
            if self.viewer and block.get('point_refs'):
                self.viewer.set_selection(list(block['point_refs']))
                self.notebook.select(self.tab_points)
        
        tk.Button(btn_frame, text="💾 Save Changes", command=save_changes,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 10, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="👁 Highlight Vertices", command=highlight_vertices,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="❌ Cancel", command=self.edit_window.destroy,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(fill=tk.X, pady=2)
        
        # Show current vertices info
        info_frame = tk.LabelFrame(frame, text="Current Vertices", padx=5, pady=5,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'])
        info_frame.pack(fill=tk.X, pady=5)
        
        verts = block['vertices']
        info_text = ""
        for i, v in enumerate(verts):
            info_text += f"{i}: ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})\\n"
        tk.Label(info_frame, text=info_text, font=("Courier", 8), justify=tk.LEFT,
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W)
    
    def delete_block(self):
        """Delete selected block"""
        if self.current_block_idx is None:
            messagebox.showwarning("Warning", "Select a block first")
            return
        if messagebox.askyesno("Confirm", "Delete block?"):
            del self.mesh_data.hex_blocks[self.current_block_idx]
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
            self.mesh_data.hex_blocks.clear()
            self.current_block_idx = None
            self.block_info.config(text="")
            self.update_block_list()
            if self.viewer:
                self.viewer.draw()
    
    def get_hex_blocks(self):
        """Get all hex blocks"""
        return self.mesh_data.hex_blocks
    
    def cleanup(self):
        """Call when closing"""
        if self.viewer:
            self.viewer.close()
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.destroy()