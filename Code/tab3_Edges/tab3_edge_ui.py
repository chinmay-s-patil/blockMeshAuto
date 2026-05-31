
import tkinter as tk
from tkinter import ttk


class EdgeEditorUI:
    """Professional UI for edge editor matching overall design style"""

    def __init__(self, parent, colors, callbacks):
        self.parent = parent
        self.colors = colors
        self.callbacks = callbacks
        # Widget refs set during setup
        self.notebook = None
        self.tab_create = None
        self.tab_manage = None
        self.tab_edit = None
        self.info_label = None
        self.arc_config = None
        self.spline_config = None
        self.config_frame = None
        # Arc widgets
        self.arc_point_var = None
        self.arc_point_label = None
        self.arc_center_var = None
        self.arc_center_label = None
        self.arc_manual_point_var = None
        self.arc_manual_center_var = None
        self.arc_notebook = None
        self.radius_var = None
        self.radius_side_var = None
        self.selected_side_var = None
        # Spline/polyline widgets
        self.spline_start_var = None
        self.spline_end_var = None
        self.spline_start_combo = None
        self.spline_end_combo = None
        self.spline_listbox = None
        # Status / manage / edit
        self.status_label = None
        self.edge_listbox = None
        self.edge_details = None
        self.edit_info_label = None
        self.edit_type_label = None
        self.edit_start_var = None
        self.edit_end_var = None
        self.edit_intermediate_frame = None
        self.edit_intermediate_listbox = None

    # 
    # Main frame setup
    # 
    def setup_main_ui(self):
        """Setup main UI – viewer on left, right-panel tabs on right"""
        main_container = tk.Frame(self.parent, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Right panel first so viewer expands into remaining space
        controls_container = tk.Frame(main_container, bg=self.colors['secondary'], width=360)
        controls_container.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(5, 0))
        controls_container.pack_propagate(False)

        # Left viewer container
        viewer_container = tk.Frame(main_container, bg=self.colors['bg'])
        viewer_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header in viewer container
        header = tk.Frame(viewer_container, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text="3. Edge Editor", font=("Segoe UI", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Label(header, text="Create and manage curved edges",
                 font=("Segoe UI", 10, "italic"), fg=self.colors['axis'],
                 bg=self.colors['bg']).pack(side=tk.LEFT, padx=15, pady=(4, 0))

        # 3D viewer canvas area
        viewer_frame = tk.Frame(viewer_container, bg=self.colors['canvas_bg'],
                                highlightbackground=self.colors['border'],
                                highlightthickness=1)
        viewer_frame.pack(fill=tk.BOTH, expand=True)

        # Status bar at bottom of viewer
        self.info_label = tk.Label(viewer_container,
                                   text="Select start point",
                                   font=("Consolas", 9),
                                   bg=self.colors['secondary'],
                                   fg=self.colors['success'],
                                   anchor=tk.W)
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        #  Notebook (right panel) 
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Edge.TNotebook",
                        background=self.colors['secondary'],
                        borderwidth=0)
        style.configure("Edge.TNotebook.Tab",
                        background=self.colors['secondary'],
                        foreground=self.colors['fg'],
                        padding=[14, 7],
                        font=("Segoe UI", 9, "bold"))
        style.map("Edge.TNotebook.Tab",
                  background=[("selected", self.colors['accent']),
                               ("active", self.colors['button_active'])],
                  foreground=[("selected", "white"),
                               ("active", "white")])
        # Remove dotted focus ring
        style.layout('Edge.TNotebook.Tab', [
            ('Notebook.tab', {'sticky': 'nswe', 'children': [
                ('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [
                    ('Notebook.label', {'side': 'top', 'sticky': ''})
                ]})
            ]})
        ])

        self.notebook = ttk.Notebook(controls_container, style="Edge.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_create = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_manage = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_edit = tk.Frame(self.notebook, bg=self.colors['secondary'])

        self.notebook.add(self.tab_create, text="  Create  ")
        self.notebook.add(self.tab_manage, text="  Manage  ")
        self.notebook.add(self.tab_edit, text="  Edit  ")

        return viewer_frame, controls_container

    # 
    # Helpers
    # 
    def _section(self, parent, title, pady=5):
        """LabelFrame with border going through the title text, matching overall app style."""
        lf = tk.LabelFrame(parent, text=f"  {title}  ",
                           bg=self.colors['secondary'],
                           fg=self.colors['fg'],
                           font=("Segoe UI", 9, "bold"),
                           relief=tk.GROOVE,
                           bd=1,
                           labelanchor='nw')
        lf.pack(fill=tk.X, padx=8, pady=pady)
        inner = tk.Frame(lf, bg=self.colors['secondary'])
        inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        return inner

    def _btn(self, parent, text, command, bg_key='button_bg', width=None, side=tk.LEFT, pady=2, small=False):
        """Styled flat button."""
        font_size = 8 if small else 9
        btn = tk.Button(parent, text=text, command=command or (lambda: None),
                        bg=self.colors[bg_key],
                        fg=self.colors['button_fg'] if bg_key not in ('success', 'warning', 'error') else (
                            self.colors['bg'] if bg_key == 'success' else 'black' if bg_key == 'warning' else 'white'),
                        font=("Segoe UI", font_size, "bold"),
                        relief=tk.FLAT,
                        cursor='hand2',
                        padx=6 if small else 10,
                        pady=3,
                        width=width)
        btn.pack(side=side, padx=3, pady=pady)
        hover = self.colors.get(bg_key + '_hover', self.colors.get('button_active', '#1177bb'))
        btn.bind('<Enter>', lambda e, b=btn: b.config(bg=hover))
        btn.bind('<Leave>', lambda e, b=btn, k=bg_key: b.config(bg=self.colors[k]))
        return btn

    def _get_point_choices(self):
        """Ask the controller for current point list. Returns list like ['1: (0.00, 0.00, 0.00)', ...]"""
        get_fn = self.callbacks.get('get_points')
        if get_fn:
            return get_fn()
        return []

    def refresh_point_combos(self):
        """Refresh spline start/end combo boxes with current mesh points."""
        choices = self._get_point_choices()
        for combo in [self.spline_start_combo, self.spline_end_combo]:
            if combo:
                combo['values'] = choices

    # 
    # CREATE TAB
    # 
    def setup_create_tab(self, current_edge_type_var, manual_coords):
        """Setup Create Edge tab – compact layout that doesn't overflow."""
        self.manual_coords = manual_coords

        outer = tk.Frame(self.tab_create, bg=self.colors['secondary'])
        outer.pack(fill=tk.BOTH, expand=True)

        #  Edge Type section 
        type_inner = self._section(outer, "Edge Type", pady=(8, 4))

        edge_types = [
            ('arc',      'Arc',      'Through 3 points'),
            ('spline',   'Spline',   'Smooth curve'),
            ('polyLine', 'PolyLine', 'Straight segments'),
            ('line',     'Line',     'Straight (default)'),
        ]
        for val, name, desc in edge_types:
            row = tk.Frame(type_inner, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=1)
            tk.Radiobutton(row, variable=current_edge_type_var, value=val,
                           command=self.callbacks.get('on_edge_type_changed'),
                           bg=self.colors['secondary'], fg=self.colors['accent'],
                           selectcolor=self.colors['bg'],
                           activebackground=self.colors['secondary'],
                           font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            tk.Label(row, text=name, font=("Segoe UI", 9, "bold"),
                     bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=(4, 0))
            tk.Label(row, text=desc, font=("Segoe UI", 8),
                     bg=self.colors['secondary'], fg='#888888').pack(side=tk.LEFT, padx=(8, 0))

        #  Configuration section (dynamic) 
        # The config_frame is the LabelFrame; we switch arc_config / spline_config inside it
        self.config_frame = tk.LabelFrame(outer, text="  Configuration  ",
                                          bg=self.colors['secondary'],
                                          fg=self.colors['fg'],
                                          font=("Segoe UI", 9, "bold"),
                                          relief=tk.GROOVE, bd=1,
                                          labelanchor='nw')
        self.config_frame.pack(fill=tk.X, padx=8, pady=(4, 4))

        # Arc config panel
        self._build_arc_config(self.config_frame)

        # Spline/PolyLine config panel
        self._build_spline_config(self.config_frame, manual_coords)

        #  Status 
        status_inner = self._section(outer, "Status", pady=(4, 4))
        self.status_label = tk.Label(status_inner, text="Ready – Select start point",
                                     font=("Consolas", 9),
                                     bg=self.colors['secondary'],
                                     fg=self.colors['success'],
                                     justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W)

        #  Action buttons 
        action = tk.Frame(outer, bg=self.colors['secondary'])
        action.pack(fill=tk.X, padx=8, pady=(4, 8))
        self._btn(action, "✓ Create Edge", self.callbacks.get('create_edge'), 'success', width=16)
        self._btn(action, "✗ Reset", self.callbacks.get('reset_creation'), 'error', width=10)

    #  Arc panels 
    def _build_arc_config(self, parent):
        self.arc_config = tk.Frame(parent, bg=self.colors['secondary'])

        # Instructions (compact)
        inst = tk.Frame(self.arc_config, bg=self.colors['secondary'])
        inst.pack(fill=tk.X, padx=8, pady=(6, 2))
        for text, color in [("● 1. Start point", self.colors['success']),
                             ("● 2. End point",   self.colors['error']),
                             ("● 3. Mid/arc point", self.colors['warning'])]:
            tk.Label(inst, text=text, font=("Segoe UI", 8),
                     bg=self.colors['secondary'], fg=color).pack(anchor=tk.W)

        # Arc helper notebook
        helper_lf = tk.LabelFrame(self.arc_config, text="  Arc Helper  ",
                                   bg=self.colors['secondary'],
                                   fg=self.colors['fg'],
                                   font=("Segoe UI", 8, "bold"),
                                   relief=tk.GROOVE, bd=1,
                                   labelanchor='nw')
        helper_lf.pack(fill=tk.X, padx=8, pady=6)

        self.arc_notebook = ttk.Notebook(helper_lf, style="Edge.TNotebook")
        self.arc_notebook.pack(fill=tk.X, padx=4, pady=4)

        #  Tab: Point on Arc 
        tab1 = tk.Frame(self.arc_notebook, bg=self.colors['secondary'])
        self.arc_notebook.add(tab1, text="Point")

        self.arc_point_var = tk.StringVar(value="None selected")
        tk.Label(tab1, text="Selected Point:", bg=self.colors['secondary'],
                 fg=self.colors['fg'], font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, padx=6, pady=(6, 0))
        self.arc_point_label = tk.Label(tab1, textvariable=self.arc_point_var,
                                        bg=self.colors['secondary'], fg=self.colors['accent'],
                                        font=("Consolas", 9, "bold"))
        self.arc_point_label.pack(anchor=tk.W, padx=6, pady=(1, 4))

        r1 = tk.Frame(tab1, bg=self.colors['secondary'])
        r1.pack(fill=tk.X, padx=6, pady=2)
        self._btn(r1, "🎯 Choose Point", self.callbacks.get('choose_arc_point'), 'accent', small=True)
        self._btn(r1, "✓ Use This Point", self.callbacks.get('use_chosen_arc_point'), 'success', small=True)

        # Manual entry inside Point tab
        self.arc_manual_point_var = tk.StringVar()
        r2 = tk.Frame(tab1, bg=self.colors['secondary'])
        r2.pack(fill=tk.X, padx=6, pady=(2, 6))
        tk.Label(r2, text="Or Point ID:", bg=self.colors['secondary'],
                 fg='#888888', font=("Segoe UI", 8)).pack(side=tk.LEFT)
        tk.Entry(r2, textvariable=self.arc_manual_point_var, width=7,
                 bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                 font=("Consolas", 9), relief=tk.FLAT,
                 highlightbackground=self.colors['border'],
                 highlightthickness=1).pack(side=tk.LEFT, padx=(4, 4))
        self._btn(r2, "Set", self.callbacks.get('set_arc_point_manual'), 'button_bg', small=True)

        #  Tab: Center 
        tab2 = tk.Frame(self.arc_notebook, bg=self.colors['secondary'])
        self.arc_notebook.add(tab2, text="Center")

        self.arc_center_var = tk.StringVar(value="None selected")
        tk.Label(tab2, text="Center Point:", bg=self.colors['secondary'],
                 fg=self.colors['fg'], font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, padx=6, pady=(6, 0))
        self.arc_center_label = tk.Label(tab2, textvariable=self.arc_center_var,
                                         bg=self.colors['secondary'], fg=self.colors['warning'],
                                         font=("Consolas", 9, "bold"))
        self.arc_center_label.pack(anchor=tk.W, padx=6, pady=(1, 4))

        r3 = tk.Frame(tab2, bg=self.colors['secondary'])
        r3.pack(fill=tk.X, padx=6, pady=2)
        self._btn(r3, "🎯 Choose Center", self.callbacks.get('choose_center_point'), 'warning', small=True)
        self._btn(r3, "✓ Use This Center", self.callbacks.get('use_chosen_center'), 'success', small=True)

        self.arc_manual_center_var = tk.StringVar()
        r4 = tk.Frame(tab2, bg=self.colors['secondary'])
        r4.pack(fill=tk.X, padx=6, pady=(2, 6))
        tk.Label(r4, text="Or Point ID:", bg=self.colors['secondary'],
                 fg='#888888', font=("Segoe UI", 8)).pack(side=tk.LEFT)
        tk.Entry(r4, textvariable=self.arc_manual_center_var, width=7,
                 bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                 font=("Consolas", 9), relief=tk.FLAT,
                 highlightbackground=self.colors['border'],
                 highlightthickness=1).pack(side=tk.LEFT, padx=(4, 4))
        self._btn(r4, "Set", self.callbacks.get('set_center_manual'), 'button_bg', small=True)

        #  Tab: Radius 
        tab3 = tk.Frame(self.arc_notebook, bg=self.colors['secondary'])
        self.arc_notebook.add(tab3, text="Radius")

        rf = tk.Frame(tab3, bg=self.colors['secondary'])
        rf.pack(fill=tk.X, padx=6, pady=6)
        tk.Label(rf, text="Radius:", bg=self.colors['secondary'],
                 fg=self.colors['fg'], font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.radius_var = tk.DoubleVar(value=1.0)
        tk.Entry(rf, textvariable=self.radius_var, width=8,
                 bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                 font=("Arial", 9), relief=tk.FLAT,
                 highlightbackground=self.colors['border'],
                 highlightthickness=1).pack(side=tk.LEFT, padx=5)
        self._btn(rf, "Preview", self.callbacks.get('preview_radius_arcs'), 'accent', small=True)

        side_lf = tk.LabelFrame(tab3, text="  Select Side  ",
                                 bg=self.colors['secondary'], fg=self.colors['fg'],
                                 font=("Segoe UI", 8, "bold"),
                                 relief=tk.GROOVE, bd=1, labelanchor='nw')
        side_lf.pack(fill=tk.X, padx=6, pady=4)

        self.radius_side_var = tk.StringVar(value="Click 'Preview' to see both options")
        tk.Label(side_lf, textvariable=self.radius_side_var,
                 bg=self.colors['secondary'], fg='#888888',
                 font=("Segoe UI", 8), wraplength=290).pack(pady=4)

        sb = tk.Frame(side_lf, bg=self.colors['secondary'])
        sb.pack(fill=tk.X, pady=3)
        self._btn(sb, "🎯 Side A", self.callbacks.get('select_side_a'), 'success', small=True)
        self._btn(sb, "🎯 Side B", self.callbacks.get('select_side_b'), 'warning', small=True)

        self.selected_side_var = tk.StringVar(value="No side selected")
        tk.Label(side_lf, textvariable=self.selected_side_var,
                 bg=self.colors['secondary'], fg=self.colors['accent'],
                 font=("Consolas", 9, "bold")).pack(anchor=tk.W, padx=6, pady=(2, 4))

        self._btn(tab3, "✓ Use This Arc",
                  self.callbacks.get('use_selected_radius_arc'), 'success', width=15, side=tk.TOP)

    #  Spline / PolyLine panels 
    def _build_spline_config(self, parent, manual_coords):
        self.spline_config = tk.Frame(parent, bg=self.colors['secondary'])

        #  Start / End point selectors (predefined points) 
        endpts_lf = tk.LabelFrame(self.spline_config, text="  Start & End Points  ",
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   font=("Segoe UI", 8, "bold"),
                                   relief=tk.GROOVE, bd=1, labelanchor='nw')
        endpts_lf.pack(fill=tk.X, padx=8, pady=(6, 4))

        def _make_point_row(container, label_text, var_holder_attr):
            row = tk.Frame(container, bg=self.colors['secondary'])
            row.pack(fill=tk.X, padx=6, pady=3)
            tk.Label(row, text=label_text, font=("Segoe UI", 8, "bold"),
                     bg=self.colors['secondary'], fg=self.colors['fg'],
                     width=6, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar()
            combo = ttk.Combobox(row, textvariable=var, state='readonly',
                                 font=("Consolas", 8), width=22)
            combo.pack(side=tk.LEFT, padx=(4, 0))
            btn = tk.Button(row, text="↺", font=("Segoe UI", 9), relief=tk.FLAT,
                            bg=self.colors['button_bg'], fg='white', padx=4,
                            cursor='hand2',
                            command=self.refresh_point_combos)
            btn.pack(side=tk.LEFT, padx=2)
            return var, combo

        self.spline_start_var, self.spline_start_combo = _make_point_row(endpts_lf, "Start:", 'spline_start_var')
        self.spline_end_var,   self.spline_end_combo   = _make_point_row(endpts_lf, "End:",   'spline_end_var')

        set_row = tk.Frame(endpts_lf, bg=self.colors['secondary'])
        set_row.pack(fill=tk.X, padx=6, pady=(2, 6))
        self._btn(set_row, "Set Start & End",
                  self.callbacks.get('set_spline_endpoints'), 'accent', small=True)

        #  Intermediate Points 
        inter_lf = tk.LabelFrame(self.spline_config, text="  Intermediate Points  ",
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  font=("Segoe UI", 8, "bold"),
                                  relief=tk.GROOVE, bd=1, labelanchor='nw')
        inter_lf.pack(fill=tk.X, padx=8, pady=4)

        list_frame = tk.Frame(inter_lf, bg=self.colors['secondary'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        list_frame.pack(fill=tk.X, padx=6, pady=(4, 2))
        self.spline_listbox = tk.Listbox(list_frame, height=4,
                                         bg=self.colors['text_bg'],
                                         fg=self.colors['text_fg'],
                                         font=("Consolas", 8),
                                         relief=tk.FLAT,
                                         selectbackground=self.colors['accent'],
                                         selectforeground='white')
        self.spline_listbox.pack(fill=tk.X, padx=1, pady=1)

        sb_row = tk.Frame(inter_lf, bg=self.colors['secondary'])
        sb_row.pack(fill=tk.X, padx=6, pady=(2, 6))
        self._btn(sb_row, "Add Click",   self.callbacks.get('add_spline_point'),   'success', small=True)
        self._btn(sb_row, "Remove Last", self.callbacks.get('remove_spline_point'),'warning',  small=True)
        self._btn(sb_row, "Clear",       self.callbacks.get('clear_spline_points'), 'error',   small=True)

        #  Manual Point Entry (inside config) 
        man_lf = tk.LabelFrame(self.spline_config, text="  Manual Point Entry  ",
                                bg=self.colors['secondary'], fg=self.colors['fg'],
                                font=("Segoe UI", 8, "bold"),
                                relief=tk.GROOVE, bd=1, labelanchor='nw')
        man_lf.pack(fill=tk.X, padx=8, pady=(4, 6))

        coord_row = tk.Frame(man_lf, bg=self.colors['secondary'])
        coord_row.pack(fill=tk.X, padx=6, pady=(4, 2))
        for i, (lbl, var) in enumerate(zip(['X', 'Y', 'Z'], manual_coords)):
            tk.Label(coord_row, text=lbl + ":", bg=self.colors['secondary'],
                     fg=self.colors['fg'], font=("Segoe UI", 8, "bold"),
                     width=2).grid(row=0, column=i * 2, padx=2)
            ent = tk.Entry(coord_row, textvariable=var, width=7,
                           bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                           font=("Consolas", 8), relief=tk.FLAT,
                           highlightbackground=self.colors['border'],
                           highlightthickness=1)
            ent.grid(row=0, column=i * 2 + 1, padx=2)
            ent.bind('<Return>', lambda e: (self.callbacks.get('add_manual_point') or (lambda: None))())

        mr = tk.Frame(man_lf, bg=self.colors['secondary'])
        mr.pack(fill=tk.X, padx=6, pady=(2, 6))
        self._btn(mr, "Add Manual Point",
                  self.callbacks.get('add_manual_point'), 'accent', small=True)

    # 
    # MANAGE TAB
    # 
    def setup_manage_tab(self):
        """Setup Manage tab – edge list and details taking full height."""
        outer = tk.Frame(self.tab_manage, bg=self.colors['secondary'])
        outer.pack(fill=tk.BOTH, expand=True)

        # Edge list section takes most of the height
        list_lf = tk.LabelFrame(outer, text="  Defined Edges  ",
                                 bg=self.colors['secondary'], fg=self.colors['fg'],
                                 font=("Segoe UI", 9, "bold"),
                                 relief=tk.GROOVE, bd=1, labelanchor='nw')
        list_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(10, 4))

        lb_frame = tk.Frame(list_lf, bg=self.colors['secondary'],
                            highlightbackground=self.colors['border'],
                            highlightthickness=1)
        lb_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 2))

        self.edge_listbox = tk.Listbox(lb_frame, height=10,
                                       bg=self.colors['text_bg'],
                                       fg=self.colors['text_fg'],
                                       font=("Consolas", 9),
                                       relief=tk.FLAT,
                                       selectbackground=self.colors['accent'],
                                       selectforeground='white')
        sb = tk.Scrollbar(lb_frame, orient=tk.VERTICAL, command=self.edge_listbox.yview)
        self.edge_listbox.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.edge_listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.edge_listbox.bind('<<ListboxSelect>>',
                               self.callbacks.get('on_edge_select', lambda e: None))

        btn_row = tk.Frame(list_lf, bg=self.colors['secondary'])
        btn_row.pack(fill=tk.X, padx=6, pady=(4, 8))
        self._btn(btn_row, "Edit",       self.callbacks.get('edit_selected_edge'), 'accent',   small=True)
        self._btn(btn_row, "Delete",     self.callbacks.get('delete_edge'),        'error',    small=True)
        self._btn(btn_row, "Delete All", self.callbacks.get('delete_all_edges'),   'warning',  small=True)
        self._btn(btn_row, "Highlight",  self.callbacks.get('highlight_edge'),     'success',  small=True)

        # Details section
        det_lf = tk.LabelFrame(outer, text="  Edge Details  ",
                                bg=self.colors['secondary'], fg=self.colors['fg'],
                                font=("Segoe UI", 9, "bold"),
                                relief=tk.GROOVE, bd=1, labelanchor='nw')
        det_lf.pack(fill=tk.X, padx=8, pady=(4, 10))

        self.edge_details = tk.Label(det_lf,
                                     text="Select an edge to view details",
                                     font=("Consolas", 8),
                                     bg=self.colors['secondary'],
                                     fg='#888888',
                                     justify=tk.LEFT,
                                     wraplength=310)
        self.edge_details.pack(anchor=tk.W, padx=8, pady=6)

    # 
    # EDIT TAB
    # 
    def setup_edit_tab(self):
        """Setup Edit tab – fills available height evenly."""
        outer = tk.Frame(self.tab_edit, bg=self.colors['secondary'])
        outer.pack(fill=tk.BOTH, expand=True)

        # Status banner
        self.edit_info_label = tk.Label(outer,
                                        text="Select an edge from Manage tab",
                                        font=("Segoe UI", 9, "bold"),
                                        bg=self.colors['secondary'],
                                        fg=self.colors['warning'])
        self.edit_info_label.pack(pady=(10, 4))

        # Type display
        tf = tk.Frame(outer, bg=self.colors['secondary'])
        tf.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(tf, text="Type:", bg=self.colors['secondary'],
                 fg=self.colors['fg'], font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.edit_type_label = tk.Label(tf, text="—",
                                        bg=self.colors['secondary'],
                                        fg=self.colors['accent'],
                                        font=("Segoe UI", 9, "bold"))
        self.edit_type_label.pack(side=tk.LEFT, padx=8)

        # Endpoints section
        ep_lf = tk.LabelFrame(outer, text="  Endpoints  ",
                               bg=self.colors['secondary'], fg=self.colors['fg'],
                               font=("Segoe UI", 9, "bold"),
                               relief=tk.GROOVE, bd=1, labelanchor='nw')
        ep_lf.pack(fill=tk.X, padx=8, pady=(6, 4))

        for label, attr, color, pt_type in [
            ("Start:", "edit_start_var", self.colors['success'], 'start'),
            ("End:",   "edit_end_var",   self.colors['error'],   'end')
        ]:
            row = tk.Frame(ep_lf, bg=self.colors['secondary'])
            row.pack(fill=tk.X, padx=6, pady=4)
            tk.Label(row, text=label, bg=self.colors['secondary'],
                     fg=color, font=("Segoe UI", 9, "bold"), width=6).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            tk.Label(row, textvariable=var, bg=self.colors['secondary'],
                     fg=self.colors['fg'], font=("Consolas", 8)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            btn_frame = tk.Frame(row, bg=self.colors['secondary'])
            btn_frame.pack(side=tk.RIGHT)
            _pt = pt_type
            self._btn(btn_frame, "Click",
                      lambda pt=_pt: (self.callbacks.get('change_edit_point') or (lambda x: None))(pt),
                      'accent', small=True)
            self._btn(btn_frame, "Manual",
                      lambda pt=_pt: (self.callbacks.get('change_edit_point_manual') or (lambda x: None))(pt),
                      'button_bg', small=True)

        # Intermediate points section
        self.edit_intermediate_frame = tk.LabelFrame(outer, text="  Intermediate Points  ",
                                                      bg=self.colors['secondary'], fg=self.colors['fg'],
                                                      font=("Segoe UI", 9, "bold"),
                                                      relief=tk.GROOVE, bd=1, labelanchor='nw')
        self.edit_intermediate_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        lc = tk.Frame(self.edit_intermediate_frame, bg=self.colors['secondary'],
                      highlightbackground=self.colors['border'], highlightthickness=1)
        lc.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 2))
        self.edit_intermediate_listbox = tk.Listbox(lc, height=5,
                                                    bg=self.colors['text_bg'],
                                                    fg=self.colors['text_fg'],
                                                    font=("Consolas", 8),
                                                    relief=tk.FLAT,
                                                    selectbackground=self.colors['accent'],
                                                    selectforeground='white')
        self.edit_intermediate_listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        ibr = tk.Frame(self.edit_intermediate_frame, bg=self.colors['secondary'])
        ibr.pack(fill=tk.X, padx=6, pady=(2, 8))
        self._btn(ibr, "Add Click",   self.callbacks.get('edit_add_point'),        'success', small=True)
        self._btn(ibr, "Add Manual",  self.callbacks.get('edit_add_point_manual'), 'accent',  small=True)
        self._btn(ibr, "Remove",      self.callbacks.get('edit_remove_point'),     'warning', small=True)
        self._btn(ibr, "Clear",       self.callbacks.get('edit_clear_points'),     'error',   small=True)

        # Save / Cancel
        action = tk.Frame(outer, bg=self.colors['secondary'])
        action.pack(fill=tk.X, padx=8, pady=(4, 10))
        self._btn(action, "💾 Save Changes", self.callbacks.get('save_edit_changes'), 'success', width=15)
        self._btn(action, "Cancel",          self.callbacks.get('cancel_edit'),       'error',   width=10)