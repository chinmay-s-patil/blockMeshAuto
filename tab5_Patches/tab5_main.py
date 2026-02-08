"""
Tab 5: 3D Hex Block View & Patch Assignment
Renders hex blocks with internal face hiding and allows patch assignment
"""
import tkinter as tk
from tkinter import messagebox
import math


class Tab5HexPatches:
    """
    Tab for viewing hex blocks in 3D and assigning patches to faces.
    Internal faces (shared between blocks) are automatically hidden.
    """
    
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Dark mode colors - MATCHING OTHER TABS
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
            'text_bg': '#2d2d2d',
            'text_fg': '#d4d4d4'
        }
        
        # Initialize patches storage if not exists
        if not hasattr(self.mesh_data, 'patches'):
            self.mesh_data.patches = {}
        
        # Renderer reference
        self.renderer = None
        self.panning = False
        self.pan_start = (0, 0)
        
        self.setup_ui()

    def setup_ui(self):
        """Create the tab UI"""
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D Canvas
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Hex Block View - Click faces to select", 
                font=("Arial", 12, "bold"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=5)
        
        # Canvas for 3D rendering
        self.canvas = tk.Canvas(left_frame, 
                               bg=self.colors['canvas_bg'],
                               highlightthickness=1,
                               highlightbackground=self.colors['border'])
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas controls frame
        controls_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        controls_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(controls_frame, text="Reset View", 
                 command=self._reset_view,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls_frame, text="Refresh", 
                 command=self._refresh_view,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls_frame, text="Fit All", 
                 command=self._fit_all,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f').pack(side=tk.LEFT, padx=5)
        
        tk.Label(controls_frame, 
                text="Left: Select | Right: Pan | Scroll: Zoom | Drag: Rotate",
                font=("Arial", 9), fg=self.colors['fg'], 
                bg=self.colors['bg']).pack(side=tk.LEFT, padx=10)

        # Right: Controls with scrolling
        right_container = tk.Frame(main_frame, width=400, 
                                  bg=self.colors['secondary'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_container.pack_propagate(False)
        
        # Scrollable canvas for right panel
        right_canvas = tk.Canvas(right_container, 
                                bg=self.colors['secondary'],
                                highlightthickness=0, width=380)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(right_container, orient="vertical",
                                command=right_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(bg=self.colors['secondary'],
                        troughcolor=self.colors['bg'],
                        activebackground=self.colors['accent'])
        
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
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", lambda e: right_canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: right_canvas.yview_scroll(1, "units"))
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(right_frame)
        right_canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Status section
        self._setup_status_section(right_frame)
        
        # Patch assignment panel
        from tab5_Patches.tab5_patch_panels import PatchAssignmentPanel
        self.patch_panel = PatchAssignmentPanel(
            right_frame, self.mesh_data, self.colors,
            on_assign_callback=self._on_patch_assigned
        )
        
        # Patch list panel
        from tab5_Patches.tab5_patch_panels import PatchListPanel
        self.patch_list_panel = PatchListPanel(
            right_frame, self.mesh_data, self.colors,
            on_select_callback=self._on_patch_selected
        )
        
        # Force update
        right_frame.update_idletasks()
        update_scrollregion()
        
        # Setup canvas bindings
        self._setup_canvas_bindings()
        
        # Initialize renderer
        self._init_renderer()
        
    # Part 4 - Status section and canvas bindings

    def _setup_status_section(self, parent):
        """Setup the status/info section"""
        status_frame = tk.LabelFrame(parent, text="Status", 
                                    padx=10, pady=10,
                                    bg=self.colors['secondary'],
                                    fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    highlightcolor=self.colors['accent'],
                                    font=("Arial", 10, "bold"))
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(status_frame, 
                                    text="Ready",
                                    font=("Arial", 10),
                                    fg=self.colors['success'],
                                    bg=self.colors['secondary'])
        self.status_label.pack(anchor=tk.W)
        
        self.block_count_label = tk.Label(status_frame,
                                         text="Blocks: 0",
                                         font=("Arial", 9),
                                         fg=self.colors['fg'],
                                         bg=self.colors['secondary'])
        self.block_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.face_count_label = tk.Label(status_frame,
                                        text="Visible faces: 0",
                                        font=("Arial", 9),
                                        fg=self.colors['fg'],
                                        bg=self.colors['secondary'])
        self.face_count_label.pack(anchor=tk.W)
        
        self.selected_count_label = tk.Label(status_frame,
                                            text="Selected faces: 0",
                                            font=("Arial", 9, "bold"),
                                            fg=self.colors['accent'],
                                            bg=self.colors['secondary'])
        self.selected_count_label.pack(anchor=tk.W)
        
    def _setup_canvas_bindings(self):
        """Setup mouse bindings for canvas interaction"""
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_rotate)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_pan)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-4>", self._on_zoom)
        self.canvas.bind("<Button-5>", self._on_zoom)
        self.canvas.bind("<Configure>", lambda e: self._draw())
        
    def _init_renderer(self):
        """Initialize the hex block renderer"""
        from tab5_Patches.tab5_hex_renderer import HexBlockRenderer
        self.renderer = HexBlockRenderer(self.canvas, self.mesh_data)
        self.renderer.on_selection_changed = self._on_face_selection_changed
        self._update_status()
        self._draw()
        
    def _draw(self):
        """Redraw the 3D view"""
        if self.renderer:
            self.renderer.draw()
            
    def _on_face_selection_changed(self, selected_faces):
        """Handle face selection change from renderer"""
        self.patch_panel.set_selected_faces(selected_faces)
        self.selected_count_label.config(
            text="Selected faces: %d" % len(selected_faces)
        )
        
    # Part 5 - Patch callbacks and view controls

    def _on_patch_assigned(self, patch_data):
        """Handle patch assignment"""
        if 'clear' in patch_data:
            if self.renderer:
                self.renderer.clear_selection()
            return
        
        # Store patch in mesh_data
        patch_name = patch_data['name']
        if not hasattr(self.mesh_data, 'patches'):
            self.mesh_data.patches = {}
        
        # If patch exists, append faces
        if patch_name in self.mesh_data.patches:
            existing = self.mesh_data.patches[patch_name]
            existing_faces = set(existing.get('faces', []))
            new_faces = set(patch_data['faces'])
            existing['faces'] = list(existing_faces | new_faces)
        else:
            self.mesh_data.patches[patch_name] = patch_data
        
        # Update UI
        self.patch_list_panel.refresh_list()
        if self.renderer:
            self.renderer.clear_selection()
        self._update_status()
        
    def _on_patch_selected(self, patch_name, patch_data, highlight_faces=None):
        """Handle patch selection from list"""
        if highlight_faces and self.renderer:
            self.renderer.selected_faces = set(highlight_faces)
            self.renderer.draw()
            self.patch_panel.set_selected_faces(highlight_faces)
            self.selected_count_label.config(
                text="Selected faces: %d" % len(highlight_faces)
            )
            
    def _update_status(self):
        """Update status labels"""
        num_blocks = len(getattr(self.mesh_data, 'hex_blocks', []))
        self.block_count_label.config(text="Blocks: %d" % num_blocks)
        
        if self.renderer:
            visible_faces = sum(1 for f in self.renderer.all_faces if f['is_visible'])
            self.face_count_label.config(text="Visible faces: %d" % visible_faces)
        
        num_patches = len(getattr(self.mesh_data, 'patches', {}))
        self.status_label.config(text="Ready - %d patches defined" % num_patches)
        
    def _reset_view(self):
        """Reset camera view"""
        if self.renderer:
            self.renderer.rotation_x = 30
            self.renderer.rotation_y = -45
            self.renderer.zoom = 1.0
            self.renderer.pan_x = 0
            self.renderer.pan_y = 0
            self.renderer.draw()
            
    def _refresh_view(self):
        """Refresh the view (rebuild face cache)"""
        if self.renderer:
            self.renderer.invalidate_cache()
            self.renderer._build_faces()
            self._update_status()
            self.renderer.draw()
            
    # Part 6 - Fit all and mouse handlers

    def _fit_all(self):
        """Fit all blocks in view"""
        if not self.renderer or not self.renderer.all_faces:
            return
        
        # Calculate bounding box of all vertices
        all_verts = []
        for face in self.renderer.all_faces:
            all_verts.extend(face['vertices'])
        
        if not all_verts:
            return
        
        import numpy as np
        verts = np.array(all_verts)
        min_coords = verts.min(axis=0)
        max_coords = verts.max(axis=0)
        
        # Reset pan
        self.renderer.pan_x = 0
        self.renderer.pan_y = 0
        
        # Calculate zoom to fit
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        max_range = np.max(max_coords - min_coords)
        if max_range > 0:
            self.renderer.zoom = min(canvas_w, canvas_h) / (max_range * 3)
        
        self.renderer.draw()
        
    def _on_left_click(self, event):
        """Handle left click - selection is handled by renderer"""
        self._rotate_start = (event.x, event.y)
        
    def _on_rotate(self, event):
        """Handle rotation drag"""
        if not self.renderer:
            return
        
        dx = event.x - self._rotate_start[0]
        dy = event.y - self._rotate_start[1]
        
        self.renderer.rotation_y += dx * 0.5
        self.renderer.rotation_x -= dy * 0.5
        
        self._rotate_start = (event.x, event.y)
        self.renderer.draw()
        
    def _on_right_click(self, event):
        """Handle right click (pan start)"""
        self.panning = True
        self.pan_start = (event.x, event.y)
        
    def _on_pan(self, event):
        """Handle pan drag"""
        if not self.panning or not self.renderer:
            return
        
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        
        self.renderer.pan_x += dx
        self.renderer.pan_y += dy
        
        self.pan_start = (event.x, event.y)
        self.renderer.draw()
        
    def _on_pan_end(self, event):
        """Handle pan end"""
        self.panning = False
        
    def _on_zoom(self, event):
        """Handle zoom"""
        if not self.renderer:
            return
        
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.renderer.zoom *= 1.1
        else:
            self.renderer.zoom *= 0.9
        
        self.renderer.zoom = max(0.01, min(1000.0, self.renderer.zoom))
        self.renderer.draw()