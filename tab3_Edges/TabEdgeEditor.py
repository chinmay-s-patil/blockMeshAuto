"""
Tab 3: Edge Editor - Define splines, arcs, and polyLines for blockMeshDict edges
"""
import tkinter as tk
from tkinter import messagebox, ttk
import math
import numpy as np


class TabEdgeEditor:

    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data

        # Dark mode colors
        self.colors = {
            'bg': '#1e1e1e', 'fg': '#d4d4d4', 'secondary': '#252526',
            'accent': '#007acc', 'success': '#4ec9b0', 'warning': '#ce9178',
            'error': '#f44747', 'button_bg': '#0e639c', 'button_fg': '#ffffff',
            'button_active': '#1177bb', 'border': '#3e3e42', 'canvas_bg': '#1e1e1e',
            'grid': '#3e3e42', 'axis': '#6e6e6e', 'select_bg': '#0e639c',
            'add_bg': '#4ec9b0', 'connect_bg': '#ce9178', 'delete_bg': '#f44747',
            'text_bg': '#2d2d2d', 'text_fg': '#d4d4d4'
        }

        if not hasattr(self.mesh_data, 'edges'):
            self.mesh_data.edges = []

        self.selected_points = []  # Can contain int or tuple (x,y,z)
        self.current_edge_type = tk.StringVar(value='arc')
        self.editing_edge_idx = None
        self.spline_points = []
        self.viewer = None
        
        # Manual point entry
        self.manual_coords = [tk.DoubleVar(value=0.0) for _ in range(3)]

        self.setup_ui()
        self.parent.after(100, self._auto_fit)

    def _auto_fit(self):
        if self.viewer:
            self.viewer.fit_all()

    def setup_ui(self):
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Edge Editor - Select points to define curved edges",
                font=("Arial", 12, "bold"), bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=5)

        viewer_frame = tk.Frame(left_frame, bg=self.colors['canvas_bg'])
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        from tab3_Edges.embedded_viewer import EmbeddedViewer
        self.viewer = EmbeddedViewer(viewer_frame, self.mesh_data, self)
        self._override_viewer_draw()

        control_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=5)

        self.info_label = tk.Label(control_frame, 
                                  text="Step 1: Select start point | Mode: Arc",
                                  font=("Arial", 10, "bold"), fg=self.colors['accent'],
                                  bg=self.colors['bg'])
        self.info_label.pack(side=tk.LEFT, padx=10)

        # Right panel with scrolling
        right_container = tk.Frame(main_frame, width=400, bg=self.colors['secondary'])
        right_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_container.pack_propagate(False)

        right_canvas = tk.Canvas(right_container, bg=self.colors['secondary'], 
                                highlightthickness=0, width=380)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(right_container, orient="vertical", 
                                command=right_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.configure(yscrollcommand=scrollbar.set)

        right_frame = tk.Frame(right_canvas, bg=self.colors['secondary'], width=380)
        controls_window = right_canvas.create_window((0, 0), window=right_frame, anchor="nw")

        def update_scrollregion(event=None):
            right_canvas.update_idletasks()
            bbox = right_canvas.bbox("all")
            if bbox:
                right_canvas.configure(scrollregion=bbox)
            right_canvas.itemconfig(controls_window, width=right_canvas.winfo_width())

        right_frame.bind("<Configure>", update_scrollregion)
        right_canvas.bind("<Configure>", update_scrollregion)
        self.right_frame = right_frame

        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors['secondary'])
        style.configure("TNotebook.Tab", background=self.colors['secondary'],
                       foreground=self.colors['fg'])
        style.map("TNotebook.Tab", background=[("selected", self.colors['accent'])])

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_create = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_manage = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_edit = tk.Frame(self.notebook, bg=self.colors['secondary'])

        self.notebook.add(self.tab_create, text="1. Create Edge")
        self.notebook.add(self.tab_manage, text="2. Manage Edges")
        self.notebook.add(self.tab_edit, text="3. Edit Edge")

        self._setup_create_tab()
        self._setup_manage_tab()
        self._setup_edit_tab()
        self._update_ui_state()

    def _override_viewer_draw(self):
        original_draw = self.viewer.draw
        def draw_with_edges():
            original_draw()
            self._draw_edges()
        self.viewer.draw = draw_with_edges

    def _draw_edges(self):
        for edge in self.mesh_data.edges:
            self._draw_single_edge(edge)
        self._draw_preview_edge()

    def _draw_single_edge(self, edge):
        edge_type = edge.get('type', 'line')
        start_coords = self._get_point_coords(edge['start'])
        end_coords = self._get_point_coords(edge['end'])
        
        if start_coords is None or end_coords is None:
            return
            
        sx1, sy1, _ = self.viewer._project(np.array(start_coords))
        sx2, sy2, _ = self.viewer._project(np.array(end_coords))
        
        if edge_type == 'line':
            self.viewer.canvas.create_line(sx1, sy1, sx2, sy2, fill='#ff00ff', width=3, dash=(5, 3))
        
        elif edge_type == 'arc':
            intermediate = edge.get('intermediate')
            if intermediate:
                mid_coords = self._get_point_coords(intermediate)
                points = self._calculate_arc_through_three_points(start_coords, mid_coords, end_coords)
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='#00ffff', width=3)
                mix, miy, _ = self.viewer._project(np.array(mid_coords))
                self.viewer.canvas.create_oval(mix-4, miy-4, mix+4, miy+4, fill='yellow', outline='white')
        
        elif edge_type == 'spline':
            intermediate = edge.get('intermediate', [])
            if intermediate:
                all_points = [start_coords] + [self._get_point_coords(p) for p in intermediate] + [end_coords]
                spline_points = self._calculate_spline_points(all_points)
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in spline_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='#ffaa00', width=3)
        
        elif edge_type == 'polyLine':
            intermediate = edge.get('intermediate', [])
            if intermediate:
                all_points = [start_coords] + [self._get_point_coords(p) for p in intermediate] + [end_coords]
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in all_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='#00ffaa', width=3)
        
        self.viewer.canvas.create_oval(sx1-6, sy1-6, sx1+6, sy1+6, fill='green', outline='white', width=2)
        self.viewer.canvas.create_oval(sx2-6, sy2-6, sx2+6, sy2+6, fill='red', outline='white', width=2)

    def _draw_preview_edge(self):
        if len(self.selected_points) == 0:
            return
            
        for i, idx in enumerate(self.selected_points):
            coords = self._get_point_coords(idx)
            if coords:
                sx, sy, _ = self.viewer._project(np.array(coords))
                colors = ['yellow', 'orange', 'cyan']
                color = colors[i] if i < len(colors) else 'white'
                r = 8
                self.viewer.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=color, outline='white', width=2)
                labels = ['S', 'E', 'M']
                label = labels[i] if i < len(labels) else f"P{i+1}"
                # FIX 2: Offset labels to avoid overlap with point numbers
                offset_x = 20 if i % 2 == 0 else -20
                self.viewer.canvas.create_text(sx + offset_x, sy-20, text=label, fill=color, font=('Arial', 10, 'bold'))
        
        if len(self.selected_points) >= 2:
            start = self._get_point_coords(self.selected_points[0])
            end = self._get_point_coords(self.selected_points[1])
            edge_type = self.current_edge_type.get()
            
            if edge_type == 'arc' and len(self.selected_points) == 3:
                mid = self._get_point_coords(self.selected_points[2])
                points = self._calculate_arc_through_three_points(start, mid, end)
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='cyan', width=2, dash=(4, 2))
            
            elif edge_type == 'spline' and self.spline_points:
                all_points = [start] + [self._get_point_coords(p) for p in self.spline_points] + [end]
                spline_points = self._calculate_spline_points(all_points)
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in spline_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='orange', width=2, dash=(4, 2))
            
            elif edge_type == 'polyLine' and self.spline_points:
                all_points = [start] + [self._get_point_coords(p) for p in self.spline_points] + [end]
                screen_points = [(self.viewer._project(np.array(p))[0], self.viewer._project(np.array(p))[1]) for p in all_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(screen_points[i][0], screen_points[i][1],
                                                  screen_points[i+1][0], screen_points[i+1][1],
                                                  fill='lightgreen', width=2, dash=(4, 2))

    def _calculate_spline_points(self, control_points, num_segments=50):
        """
        FIX 3: True Catmull-Rom spline for OpenFOAM/blockMesh compatibility.
        Interpolates smoothly through all control points.
        """
        if len(control_points) < 2:
            return control_points
        
        points = [np.array(p) for p in control_points]
        n = len(points)
        
        if n == 2:
            return [tuple(points[0]), tuple(points[1])]
        
        result = []
        
        for i in range(n - 1):
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(n - 1, i + 2)]
            
            for j in range(num_segments + 1):
                t = j / num_segments
                t2 = t * t
                t3 = t2 * t
                
                # Catmull-Rom spline matrix
                point = 0.5 * (
                    (2 * p1) +
                    (-p0 + p2) * t +
                    (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                    (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
                
                result.append(tuple(point))
        
        # Remove duplicates
        filtered = [result[0]]
        for i in range(1, len(result)):
            if not np.allclose(result[i], result[i-1], atol=1e-10):
                filtered.append(result[i])
        
        return filtered

    def _calculate_arc_through_three_points(self, p1, p2, p3, num_segments=30):
        """Calculate arc passing through three points (start, mid, end)"""
        A, B, C = np.array(p1), np.array(p2), np.array(p3)
        
        a, b, c = np.linalg.norm(C - B), np.linalg.norm(C - A), np.linalg.norm(B - A)
        
        if abs(a + b - c) < 1e-10 or abs(a + c - b) < 1e-10 or abs(b + c - a) < 1e-10:
            return [p1, p3]
        
        s = (a + b + c) / 2
        area = math.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))
        
        if area < 1e-10:
            return [p1, p3]
        
        R = a * b * c / (4 * area)
        denom = a**2 * (b**2 + c**2 - a**2) + b**2 * (a**2 + c**2 - b**2) + c**2 * (a**2 + b**2 - c**2)
        
        if abs(denom) < 1e-10:
            return [p1, p3]
        
        alpha = a**2 * (b**2 + c**2 - a**2) / denom
        beta = b**2 * (a**2 + c**2 - b**2) / denom
        gamma = c**2 * (a**2 + b**2 - c**2) / denom
        
        center = alpha * A + beta * B + gamma * C
        
        def angle_from_center(point):
            v = np.array(point) - center
            return math.atan2(v[1], v[0])
        
        angle1, angle2, angle3 = angle_from_center(A), angle_from_center(B), angle_from_center(C)
        
        def normalize_angle(a):
            while a < 0: a += 2 * math.pi
            while a >= 2 * math.pi: a -= 2 * math.pi
            return a
        
        a1, a2, a3 = normalize_angle(angle1), normalize_angle(angle2), normalize_angle(angle3)
        
        going_ccw = a1 < a2 < a3 if a1 < a3 else not (a3 < a2 < a1)
        
        if going_ccw:
            total_angle = a3 - a1 if a3 > a1 else (2 * math.pi - a1) + a3
        else:
            total_angle = -(a1 - a3 if a1 > a3 else (2 * math.pi - a3) + a1)
        
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            angle = angle1 + t * total_angle
            x = center[0] + R * math.cos(angle)
            y = center[1] + R * math.sin(angle)
            z = A[2] + t * (C[2] - A[2])
            points.append((x, y, z))
        
        return points

    def _get_point_coords(self, point_ref):
        """Get coordinates from int index or tuple"""
        if isinstance(point_ref, int):
            layer, local_idx = self.mesh_data.get_layer_from_global_index(point_ref)
            if layer is None:
                return None
            point_2d = self.mesh_data.points[layer][local_idx]
            return self.mesh_data.get_3d_coords_standard(layer, point_2d)
        return point_ref

    def _setup_create_tab(self):
        frame = tk.Frame(self.tab_create, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        type_frame = tk.LabelFrame(frame, text="Edge Type", padx=10, pady=10,
                                   bg=self.colors['secondary'], fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'])
        type_frame.pack(fill=tk.X, pady=(0, 10))

        for edge_type, label in [('arc', 'Arc (3 points on arc)'), 
                                  ('spline', 'Spline (smooth curve)'),
                                  ('polyLine', 'PolyLine (straight segments)'),
                                  ('line', 'Line (straight)')]:
            tk.Radiobutton(type_frame, text=label, variable=self.current_edge_type,
                          value=edge_type, command=self._on_edge_type_changed,
                          font=("Arial", 10), bg=self.colors['secondary'],
                          fg=self.colors['fg'], selectcolor=self.colors['bg'],
                          activebackground=self.colors['secondary'],
                          activeforeground=self.colors['accent']).pack(anchor=tk.W, pady=2)

        # Manual Point Entry Section (moved higher for visibility)
        manual_entry_frame = tk.LabelFrame(frame, text="Manual Point Entry", padx=10, pady=10,
                                          bg=self.colors['secondary'], fg=self.colors['fg'],
                                          highlightbackground=self.colors['border'])
        manual_entry_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(manual_entry_frame, text="Enter coordinates (X, Y, Z):", 
                font=("Arial", 9), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 5))
        
        coord_frame = tk.Frame(manual_entry_frame, bg=self.colors['secondary'])
        coord_frame.pack(fill=tk.X, pady=5)
        
        for i, label in enumerate(['X:', 'Y:', 'Z:']):
            col_frame = tk.Frame(coord_frame, bg=self.colors['secondary'])
            col_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            tk.Label(col_frame, text=label, bg=self.colors['secondary'], 
                    fg=self.colors['fg'], width=3).pack(side=tk.LEFT)
            entry = tk.Entry(col_frame, textvariable=self.manual_coords[i], width=12,
                    bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                    insertbackground=self.colors['fg'])
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            # Allow Enter key to add point
            entry.bind('<Return>', lambda e: self._add_manual_point())
        
        # Buttons for manual entry
        manual_btn_frame = tk.Frame(manual_entry_frame, bg=self.colors['secondary'])
        manual_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(manual_btn_frame, text="Set as Start Point", 
                 command=lambda: self._enter_point_manually('start'),
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(manual_btn_frame, text="Set as End Point", 
                 command=lambda: self._enter_point_manually('end'),
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(manual_btn_frame, text="Add Intermediate", 
                 command=self._add_manual_point,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.config_frame = tk.LabelFrame(frame, text="Configuration", padx=10, pady=10,
                                         bg=self.colors['secondary'], fg=self.colors['fg'],
                                         highlightbackground=self.colors['border'])
        self.config_frame.pack(fill=tk.X, pady=10)

        self.arc_config = tk.Frame(self.config_frame, bg=self.colors['secondary'])
        tk.Label(self.arc_config, text="Arc passes through 3 points:", 
                font=("Arial", 10, "bold"), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(anchor=tk.W)
        tk.Label(self.arc_config, text="1. Start point (green)", 
                bg=self.colors['secondary'], fg=self.colors['success']).pack(anchor=tk.W, padx=10)
        tk.Label(self.arc_config, text="2. End point (red)", 
                bg=self.colors['secondary'], fg=self.colors['error']).pack(anchor=tk.W, padx=10)
        tk.Label(self.arc_config, text="3. Mid point on arc (yellow)", 
                bg=self.colors['secondary'], fg=self.colors['warning']).pack(anchor=tk.W, padx=10)

        self.spline_config = tk.Frame(self.config_frame, bg=self.colors['secondary'])
        tk.Label(self.spline_config, text="Intermediate Points:", 
                font=("Arial", 10, "bold"), bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(anchor=tk.W)

        self.spline_listbox = tk.Listbox(self.spline_config, height=6,
                                        bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                                        selectbackground=self.colors['accent'])
        self.spline_listbox.pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(self.spline_config, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Point (Click 3D)", command=self._add_spline_point,
                 bg=self.colors['add_bg'], fg=self.colors['bg'],
                 font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Remove Selected", command=self._remove_spline_point,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Clear All", command=self._clear_spline_points,
                 bg=self.colors['warning'], fg=self.colors['bg'],
                 font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        status_frame = tk.LabelFrame(frame, text="Selection Status", padx=10, pady=10,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'])
        status_frame.pack(fill=tk.X, pady=10)

        self.status_label = tk.Label(status_frame, text="Select start point", 
                                    font=("Courier", 10), justify=tk.LEFT,
                                    bg=self.colors['secondary'], fg=self.colors['success'])
        self.status_label.pack(anchor=tk.W)

        action_frame = tk.Frame(frame, bg=self.colors['secondary'])
        action_frame.pack(fill=tk.X, pady=20)

        tk.Button(action_frame, text="✓ Create Edge", command=self._create_edge,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 11, "bold"), height=2).pack(fill=tk.X, pady=2)
        tk.Button(action_frame, text="✗ Cancel / Reset", command=self._reset_creation,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 10)).pack(fill=tk.X, pady=2)

        # Help section with proper title
        help_frame = tk.LabelFrame(frame, text="Instructions", padx=10, pady=10,
                                  bg=self.colors['secondary'], fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'])
        help_frame.pack(fill=tk.X, pady=10)
        
        help_text = """How to create edges:
1. Select edge type above
2. For start/end points, either:
   • Click points in 3D view, OR
   • Enter coordinates manually and click "Set as Start/End"
3. For arc: select a third point ON the arc (not center)
4. For spline/polyLine: add intermediate points
   (click in 3D or use "Add Intermediate" button)
5. Click "Create Edge" when ready"""
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                fg=self.colors['fg'], justify=tk.LEFT,
                bg=self.colors['secondary']).pack(anchor=tk.W)

    def _setup_manage_tab(self):
        frame = tk.Frame(self.tab_manage, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame, text="Defined Edges", font=("Arial", 11, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W)

        list_frame = tk.Frame(frame, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.edge_listbox = tk.Listbox(list_frame, font=("Courier", 10),
                                       yscrollcommand=scroll.set, 
                                       bg=self.colors['text_bg'], 
                                       fg=self.colors['text_fg'],
                                       selectbackground=self.colors['accent'])
        self.edge_listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.edge_listbox.yview)
        self.edge_listbox.bind('<<ListboxSelect>>', self._on_edge_select)

        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Edit Selected", command=self._edit_selected_edge,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'], width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete Selected", command=self._delete_edge,
                 bg=self.colors['error'], fg=self.colors['button_fg'], width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete All", command=self._delete_all_edges,
                 bg=self.colors['delete_bg'], fg=self.colors['button_fg'], width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Highlight", command=self._highlight_edge,
                 bg=self.colors['accent'], fg=self.colors['button_fg'], width=12).pack(side=tk.LEFT, padx=2)

        self.edge_details = tk.Label(frame, text="", font=("Courier", 9),
                                    justify=tk.LEFT, fg=self.colors['fg'],
                                    bg=self.colors['secondary'])
        self.edge_details.pack(anchor=tk.W, pady=10)

        self._update_edge_list()

    def _setup_edit_tab(self):
        frame = tk.Frame(self.tab_edit, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame, text="Edit Edge", font=("Arial", 14, "bold"),
                bg=self.colors['secondary'], fg=self.colors['accent']).pack(pady=10)

        self.edit_info_label = tk.Label(frame, text="Select an edge from Manage tab first",
                                       font=("Arial", 10), bg=self.colors['secondary'],
                                       fg=self.colors['warning'])
        self.edit_info_label.pack(pady=5)

        type_frame = tk.Frame(frame, bg=self.colors['secondary'])
        type_frame.pack(fill=tk.X, pady=5)
        tk.Label(type_frame, text="Edge Type:", bg=self.colors['secondary'],
                fg=self.colors['fg']).pack(side=tk.LEFT)
        self.edit_type_label = tk.Label(type_frame, text="None", 
                                       font=("Arial", 10, "bold"),
                                       bg=self.colors['secondary'], fg=self.colors['accent'])
        self.edit_type_label.pack(side=tk.LEFT, padx=5)

        points_frame = tk.LabelFrame(frame, text="End Points", padx=10, pady=10,
                                    bg=self.colors['secondary'], fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'])
        points_frame.pack(fill=tk.X, pady=5)

        tk.Label(points_frame, text="Start:", bg=self.colors['secondary'],
                fg=self.colors['fg']).grid(row=0, column=0, sticky=tk.W)
        self.edit_start_var = tk.StringVar(value="-")
        tk.Label(points_frame, textvariable=self.edit_start_var,
                bg=self.colors['secondary'], fg=self.colors['success']).grid(row=0, column=1, sticky=tk.W)
        tk.Button(points_frame, text="Change (Click)", command=lambda: self._change_edit_point('start'),
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).grid(row=0, column=2, padx=5)
        tk.Button(points_frame, text="Change (Manual)", command=lambda: self._change_edit_point_manual('start'),
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).grid(row=0, column=3, padx=5)

        tk.Label(points_frame, text="End:", bg=self.colors['secondary'],
                fg=self.colors['fg']).grid(row=1, column=0, sticky=tk.W)
        self.edit_end_var = tk.StringVar(value="-")
        tk.Label(points_frame, textvariable=self.edit_end_var,
                bg=self.colors['secondary'], fg=self.colors['error']).grid(row=1, column=1, sticky=tk.W)
        tk.Button(points_frame, text="Change (Click)", command=lambda: self._change_edit_point('end'),
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).grid(row=1, column=2, padx=5)
        tk.Button(points_frame, text="Change (Manual)", command=lambda: self._change_edit_point_manual('end'),
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).grid(row=1, column=3, padx=5)

        self.edit_intermediate_frame = tk.LabelFrame(frame, text="Intermediate Points", 
                                                     padx=10, pady=10,
                                                     bg=self.colors['secondary'], 
                                                     fg=self.colors['fg'],
                                                     highlightbackground=self.colors['border'])
        self.edit_intermediate_frame.pack(fill=tk.X, pady=5)

        self.edit_intermediate_listbox = tk.Listbox(self.edit_intermediate_frame, height=6,
                                                    bg=self.colors['text_bg'],
                                                    fg=self.colors['text_fg'],
                                                    selectbackground=self.colors['accent'])
        self.edit_intermediate_listbox.pack(fill=tk.X, pady=5)

        edit_btn_frame = tk.Frame(self.edit_intermediate_frame, bg=self.colors['secondary'])
        edit_btn_frame.pack(fill=tk.X)
        tk.Button(edit_btn_frame, text="Add Point (Click)", command=self._edit_add_point,
                 bg=self.colors['add_bg'], fg=self.colors['bg']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(edit_btn_frame, text="Add Point (Manual)", command=self._edit_add_point_manual,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(edit_btn_frame, text="Remove Selected", command=self._edit_remove_point,
                 bg=self.colors['error'], fg=self.colors['button_fg']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(edit_btn_frame, text="Clear All", command=self._edit_clear_points,
                 bg=self.colors['warning'], fg=self.colors['bg']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=20)

        tk.Button(btn_frame, text="💾 Save Changes", command=self._save_edit_changes,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 11, "bold")).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Cancel", command=self._cancel_edit,
                 bg=self.colors['secondary'], fg=self.colors['fg']).pack(fill=tk.X, pady=2)

        self.editing_edge_idx = None
        self.editing_edge_data = None

    def _on_edge_type_changed(self):
        self._update_ui_state()
        self._reset_creation()

    def _update_ui_state(self):
        edge_type = self.current_edge_type.get()
        self.arc_config.pack_forget()
        self.spline_config.pack_forget()

        if edge_type == 'arc':
            self.arc_config.pack(fill=tk.X)
            self.info_label.config(text="Step 1: Select start point | Mode: Arc (3 points)")
        elif edge_type in ['spline', 'polyLine']:
            self.spline_config.pack(fill=tk.X)
            self.info_label.config(text=f"Step 1: Select start point | Mode: {edge_type}")
        else:
            self.info_label.config(text="Step 1: Select start point | Mode: Line")

        self.viewer.draw()

    def on_selection_changed(self, selected_list):
        edge_type = self.current_edge_type.get()

        if hasattr(self, '_changing_point_type') and self._changing_point_type:
            if len(selected_list) > 0:
                new_point = selected_list[-1]
                if self._changing_point_type == 'start':
                    self.editing_edge_data['start'] = new_point
                    self.edit_start_var.set(f"Point {new_point}")
                elif self._changing_point_type == 'end':
                    self.editing_edge_data['end'] = new_point
                    self.edit_end_var.set(f"Point {new_point}")
                self._changing_point_type = None
                self.edit_info_label.config(text="Point updated. Click Save to apply.", 
                                           fg=self.colors['success'])
                self.viewer.draw()
            return

        if len(self.selected_points) == 0:
            if len(selected_list) > 0:
                self.selected_points.append(selected_list[-1])
                self.status_label.config(text=f"Start: {self.selected_points[0]}\nSelect end point")
                self.info_label.config(text="Step 2: Select end point")

        elif len(self.selected_points) == 1:
            if len(selected_list) > 1:
                end_point = selected_list[-1]
                if end_point != self.selected_points[0]:
                    self.selected_points.append(end_point)

                    if edge_type == 'arc':
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nSelect mid point on arc")
                        self.info_label.config(text="Step 3: Select a point ON the arc (not center)")
                    elif edge_type in ['spline', 'polyLine']:
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nAdd intermediate points")
                        self.info_label.config(text="Step 3: Add intermediate points (optional)")
                    else:
                        self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nReady to create")
                        self.info_label.config(text="Ready: Click Create Edge")

        elif len(self.selected_points) == 2 and edge_type == 'arc':
            if len(selected_list) > 2:
                third_point = selected_list[-1]
                if third_point not in self.selected_points:
                    self.selected_points.append(third_point)
                    self.status_label.config(text=f"Start: {self.selected_points[0]}\nEnd: {self.selected_points[1]}\nMid: {self.selected_points[2]}\nReady to create")
                    self.info_label.config(text="Ready: Click Create Edge")

        elif edge_type in ['spline', 'polyLine']:
            new_point = selected_list[-1]
            existing_points = set()
            for p in self.selected_points:
                if isinstance(p, int):
                    existing_points.add(p)
            for p in self.spline_points:
                if isinstance(p, int):
                    existing_points.add(p)
            
            if isinstance(new_point, int) and new_point in existing_points:
                return
                
            self.spline_points.append(new_point)
            self._update_spline_listbox()

        self.viewer.draw()

    def _enter_point_manually(self, point_type):
        """Enter a point manually using coordinates"""
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)
            
            if point_type == 'start':
                if len(self.selected_points) == 0:
                    self.selected_points.append(point)
                    self.status_label.config(text=f"Start: ({x:.2f}, {y:.2f}, {z:.2f})\nSelect end point")
                    self.info_label.config(text="Step 2: Select end point")
                else:
                    self.selected_points[0] = point
                    self.status_label.config(text=f"Start: ({x:.2f}, {y:.2f}, {z:.2f})\n" + 
                                           (f"End: set" if len(self.selected_points) > 1 else "Select end point"))
            elif point_type == 'end':
                if len(self.selected_points) == 1:
                    self.selected_points.append(point)
                    edge_type = self.current_edge_type.get()
                    if edge_type == 'arc':
                        self.status_label.config(text=f"Start: set\nEnd: ({x:.2f}, {y:.2f}, {z:.2f})\nSelect mid point on arc")
                        self.info_label.config(text="Step 3: Select a point ON the arc (not center)")
                    elif edge_type in ['spline', 'polyLine']:
                        self.status_label.config(text=f"Start: set\nEnd: ({x:.2f}, {y:.2f}, {z:.2f})\nAdd intermediate points")
                        self.info_label.config(text="Step 3: Add intermediate points (optional)")
                    else:
                        self.status_label.config(text=f"Start: set\nEnd: ({x:.2f}, {y:.2f}, {z:.2f})\nReady to create")
                        self.info_label.config(text="Ready: Click Create Edge")
                elif len(self.selected_points) >= 2:
                    self.selected_points[1] = point
                    self.status_label.config(text=f"Start: set\nEnd: ({x:.2f}, {y:.2f}, {z:.2f})\nReady to create")
            
            self.viewer.draw()
            messagebox.showinfo("Point Set", f"Point set to ({x:.2f}, {y:.2f}, {z:.2f})")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _add_manual_point(self):
        """Add a manual point to spline/intermediate points"""
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)
            
            self.spline_points.append(point)
            self._update_spline_listbox()
            self.viewer.draw()
            messagebox.showinfo("Point Added", f"Intermediate point added: ({x:.2f}, {y:.2f}, {z:.2f})")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _create_edge(self):
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need at least start and end points")
            return

        edge_type = self.current_edge_type.get()
        edge = {
            'type': edge_type,
            'start': self.selected_points[0],
            'end': self.selected_points[1]
        }

        if edge_type == 'arc':
            if len(self.selected_points) < 3:
                messagebox.showwarning("Warning", "Arc requires 3 points: start, end, and a point on the arc")
                return
            edge['intermediate'] = self.selected_points[2]

        elif edge_type in ['spline', 'polyLine']:
            edge['intermediate'] = self.spline_points.copy()

        self.mesh_data.edges.append(edge)
        
        # Remove straight connection only if both are int indices
        if isinstance(self.selected_points[0], int) and isinstance(self.selected_points[1], int):
            self._remove_straight_connection(self.selected_points[0], self.selected_points[1])

        messagebox.showinfo("Success", f"{edge_type} edge created!")
        self._reset_creation()
        self._update_edge_list()

    def _reset_creation(self):
        self.selected_points = []
        self.spline_points = []
        self._update_spline_listbox()
        self.status_label.config(text="Select start point")
        self._update_ui_state()
        self.viewer.clear_selection()

    def _update_spline_listbox(self):
        self.spline_listbox.delete(0, tk.END)
        for i, pt in enumerate(self.spline_points):
            if isinstance(pt, int):
                coords = self._get_point_coords(pt)
                self.spline_listbox.insert(tk.END, f"{i+1}. Point {pt}: ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})")
            else:
                self.spline_listbox.insert(tk.END, f"{i+1}. Manual: ({pt[0]:.2f}, {pt[1]:.2f}, {pt[2]:.2f})")

    def _add_spline_point(self):
        messagebox.showinfo("Info", "Click a point in the 3D view to add to the spline")

    def _remove_spline_point(self):
        if self.spline_points:
            self.spline_points.pop()
            self._update_spline_listbox()
            self.viewer.draw()

    def _clear_spline_points(self):
        self.spline_points = []
        self._update_spline_listbox()
        self.viewer.draw()

    def _update_edge_list(self):
        self.edge_listbox.delete(0, tk.END)
        for i, edge in enumerate(self.mesh_data.edges):
            edge_type = edge['type']
            start = edge['start']
            end = edge['end']
            
            def fmt_point(p):
                if isinstance(p, int):
                    return f"P{p}"
                return f"({p[0]:.1f},{p[1]:.1f},{p[2]:.1f})"
            
            extra = ""
            if edge_type == 'arc' and 'intermediate' in edge:
                mid = edge['intermediate']
                if isinstance(mid, int):
                    extra = f" via P{mid}"
                else:
                    extra = f" via manual"
            elif edge_type in ['spline', 'polyLine'] and 'intermediate' in edge:
                extra = f" +{len(edge['intermediate'])} pts"
            self.edge_listbox.insert(tk.END, f"Edge {i}: {edge_type} ({fmt_point(start)} → {fmt_point(end)}{extra})")

    def _on_edge_select(self, event):
        sel = self.edge_listbox.curselection()
        if sel:
            idx = sel[0]
            edge = self.mesh_data.edges[idx]
            
            def fmt_point(p):
                if isinstance(p, int):
                    return f"Point {p}"
                return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"
            
            details = f"Type: {edge['type']}\nStart: {fmt_point(edge['start'])}\nEnd: {fmt_point(edge['end'])}"
            if 'intermediate' in edge:
                if isinstance(edge['intermediate'], list):
                    details += f"\nIntermediate: {len(edge['intermediate'])} points"
                else:
                    details += f"\nMid point: {fmt_point(edge['intermediate'])}"
            self.edge_details.config(text=details)

    def _edit_selected_edge(self):
        sel = self.edge_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an edge to edit")
            return

        idx = sel[0]
        self.editing_edge_idx = idx
        self.editing_edge_data = dict(self.mesh_data.edges[idx])

        self.notebook.select(self.tab_edit)

        edge = self.editing_edge_data
        self.edit_type_label.config(text=edge['type'].upper())
        
        def fmt_point(p):
            if isinstance(p, int):
                return f"Point {p}"
            return f"Manual ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"
        
        self.edit_start_var.set(fmt_point(edge['start']))
        self.edit_end_var.set(fmt_point(edge['end']))

        self.edit_intermediate_listbox.delete(0, tk.END)
        if 'intermediate' in edge:
            intermediate = edge['intermediate']
            if isinstance(intermediate, list):
                for i, pt in enumerate(intermediate):
                    self.edit_intermediate_listbox.insert(tk.END, f"{i+1}. {fmt_point(pt)}")
            else:
                self.edit_intermediate_listbox.insert(tk.END, f"1. {fmt_point(intermediate)}")

        self.edit_info_label.config(text=f"Editing Edge {idx}. Make changes and save.",
                                   fg=self.colors['accent'])
        self.viewer.draw()

    def _change_edit_point(self, point_type):
        self._changing_point_type = point_type
        self.edit_info_label.config(text=f"Click a point in 3D view to set as new {point_type} point",
                                   fg=self.colors['warning'])

    def _change_edit_point_manual(self, point_type):
        """Change point using manual entry in edit mode"""
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)
            
            if point_type == 'start':
                self.editing_edge_data['start'] = point
                self.edit_start_var.set(f"Manual ({x:.2f}, {y:.2f}, {z:.2f})")
            elif point_type == 'end':
                self.editing_edge_data['end'] = point
                self.edit_end_var.set(f"Manual ({x:.2f}, {y:.2f}, {z:.2f})")
            
            self.edit_info_label.config(text=f"{point_type.capitalize()} point updated. Click Save to apply.",
                                       fg=self.colors['success'])
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _edit_add_point(self):
        messagebox.showinfo("Info", "Click a point in 3D view to add")

    def _edit_add_point_manual(self):
        """Add manual point in edit mode"""
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)
            
            if 'intermediate' not in self.editing_edge_data:
                self.editing_edge_data['intermediate'] = []
            
            if isinstance(self.editing_edge_data['intermediate'], int):
                self.editing_edge_data['intermediate'] = [self.editing_edge_data['intermediate']]
            
            self.editing_edge_data['intermediate'].append(point)
            self._refresh_edit_listbox()
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _edit_remove_point(self):
        sel = self.edit_intermediate_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        if 'intermediate' in self.editing_edge_data:
            intermediate = self.editing_edge_data['intermediate']
            if isinstance(intermediate, list):
                if idx < len(intermediate):
                    intermediate.pop(idx)
            else:
                self.editing_edge_data.pop('intermediate')

        self._refresh_edit_listbox()

    def _edit_clear_points(self):
        if 'intermediate' in self.editing_edge_data:
            self.editing_edge_data.pop('intermediate')
        self._refresh_edit_listbox()

    def _refresh_edit_listbox(self):
        self.edit_intermediate_listbox.delete(0, tk.END)
        
        def fmt_point(p):
            if isinstance(p, int):
                return f"Point {p}"
            return f"Manual ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"
        
        if 'intermediate' in self.editing_edge_data:
            intermediate = self.editing_edge_data['intermediate']
            if isinstance(intermediate, list):
                for i, pt in enumerate(intermediate):
                    self.edit_intermediate_listbox.insert(tk.END, f"{i+1}. {fmt_point(pt)}")
            else:
                self.edit_intermediate_listbox.insert(tk.END, f"1. {fmt_point(intermediate)}")

    def _save_edit_changes(self):
        if self.editing_edge_idx is None:
            return

        self.mesh_data.edges[self.editing_edge_idx] = self.editing_edge_data
        messagebox.showinfo("Success", "Edge updated!")
        self._update_edge_list()
        self.notebook.select(self.tab_manage)
        self.viewer.draw()

    def _cancel_edit(self):
        self.editing_edge_idx = None
        self.editing_edge_data = None
        self._changing_point_type = None
        self.notebook.select(self.tab_manage)
        self.edit_info_label.config(text="Select an edge from Manage tab first",
                                   fg=self.colors['warning'])

    def _delete_edge(self):
        sel = self.edge_listbox.curselection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete selected edge?"):
            idx = sel[0]
            del self.mesh_data.edges[idx]
            self._update_edge_list()
            self.edge_details.config(text="")
            self.viewer.draw()

    def _delete_all_edges(self):
        if not self.mesh_data.edges:
            return
        if messagebox.askyesno("Confirm", "Delete all edges?"):
            self.mesh_data.edges = []
            self._update_edge_list()
            self.edge_details.config(text="")
            self.viewer.draw()

    def _highlight_edge(self):
        sel = self.edge_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        edge = self.mesh_data.edges[idx]
        points_to_select = []
        
        if isinstance(edge['start'], int):
            points_to_select.append(edge['start'])
        if isinstance(edge['end'], int):
            points_to_select.append(edge['end'])
        if 'intermediate' in edge:
            intermediate = edge['intermediate']
            if isinstance(intermediate, list):
                for pt in intermediate:
                    if isinstance(pt, int):
                        points_to_select.append(pt)
            else:
                if isinstance(intermediate, int):
                    points_to_select.append(intermediate)
        
        self.viewer.set_selection(points_to_select)

    def _remove_straight_connection(self, global_idx1, global_idx2):
        layer1, local1 = self.mesh_data.get_layer_from_global_index(global_idx1)
        layer2, local2 = self.mesh_data.get_layer_from_global_index(global_idx2)

        if layer1 == layer2:
            conn = tuple(sorted([local1, local2]))
            if conn in self.mesh_data.connections[layer1]:
                self.mesh_data.connections[layer1].remove(conn)
        else:
            conn = (layer1, local1, layer2, local2)
            if hasattr(self.mesh_data, 'inter_layer_connections') and conn in self.mesh_data.inter_layer_connections:
                self.mesh_data.inter_layer_connections.remove(conn)

    def cleanup(self):
        if self.viewer:
            self.viewer.close()