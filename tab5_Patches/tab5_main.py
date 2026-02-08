"""
Tab 5: 3D Hex Block View & Patch Assignment
Renders hex blocks with internal face hiding and allows patch assignment

FIXES:
- Initialize _rotate_start to prevent AttributeError
- Use middle mouse button (Button-2) for rotation instead of left
- Add Hide/Select mode toggle
- Fix patches data structure (dict instead of list)
- Added Show All button to unhide faces
- Fixed fit_all to properly calculate zoom
- Axes now in bottom right corner
- Added Patch Normals tab for editing face normals
- Added Patch Editor for editing existing patches
- Added Add button to add faces to existing patches without duplicates
"""
import tkinter as tk
from tkinter import messagebox, ttk
import math
import numpy as np


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
        
        # FIX: Initialize patches storage - convert old list format to dict if needed
        if not hasattr(self.mesh_data, 'patches'):
            self.mesh_data.patches = {}
        elif isinstance(self.mesh_data.patches, list):
            # Convert old list format to dict format
            old_patches = self.mesh_data.patches
            self.mesh_data.patches = {}
            for i, item in enumerate(old_patches):
                if isinstance(item, tuple) and len(item) >= 2:
                    name = item[0]
                    patch_type = item[1]
                    faces = item[2] if len(item) > 2 else []
                    self.mesh_data.patches[name] = {
                        'name': name,
                        'type': patch_type,
                        'faces': faces,
                        'parameters': {}
                    }
        
        # Renderer reference
        self.renderer = None
        self.panning = False
        self.pan_start = (0, 0)
        
        # FIX: Initialize rotation tracking to prevent AttributeError
        self._rotate_start = (0, 0)
        
        # FIX: Add hide mode tracking
        self.hide_mode = False  # False = Select mode, True = Hide mode
        
        # Reference to normals tab and patch editor
        self.normals_tab = None
        self.patch_editor_dialog = None  # Track open patch editor
        
        # Track currently selected faces for Add functionality
        self.currently_selected_faces = set()
        
        self.setup_ui()

    def setup_ui(self):
        """Create the tab UI"""
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D Canvas
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Hex Block View - Click faces to select/hide", 
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
        
        # FIX: Add mode toggle button
        self.mode_button = tk.Button(controls_frame, text="Mode: Select", 
                 command=self._toggle_mode,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f', width=12)
        self.mode_button.pack(side=tk.LEFT, padx=5)
        
        # FIX: Add Show All button to unhide faces
        self.show_all_button = tk.Button(controls_frame, text="Show All", 
                 command=self._show_all_faces,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold"), relief=tk.FLAT,
                 activebackground=self.colors['button_active'])
        self.show_all_button.pack(side=tk.LEFT, padx=5)
        
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
        
        # FIX: Updated instructions for middle mouse button
        tk.Label(controls_frame, 
                text="Left: Select/Hide | Middle: Rotate | Right: Pan | Scroll: Zoom",
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
        
        # Create Notebook for tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors['secondary'])
        style.configure("TNotebook.Tab", background=self.colors['secondary'],
                       foreground=self.colors['fg'])
        style.map("TNotebook.Tab", background=[("selected", self.colors['accent'])])
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.tab_patches = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_assignment = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_normals = tk.Frame(self.notebook, bg=self.colors['secondary'])
        
        self.notebook.add(self.tab_patches, text="Patches")
        self.notebook.add(self.tab_assignment, text="Assign")
        self.notebook.add(self.tab_normals, text="Normals")
        
        # Status section (in patches tab)
        self._setup_status_section(self.tab_patches)
        
        # Patch list panel (in patches tab) - UPDATED with add callback
        from tab5_Patches.tab5_patch_panels import PatchListPanel
        self.patch_list_panel = PatchListPanel(
            self.tab_patches, self.mesh_data, self.colors,
            on_select_callback=self._on_patch_selected,
            on_edit_callback=self._on_patch_edit,
            on_add_callback=self._on_patch_add  # NEW: Add callback
        )
        
        # Patch assignment panel (in assign tab)
        from tab5_Patches.tab5_patch_panels import PatchAssignmentPanel
        self.patch_panel = PatchAssignmentPanel(
            self.tab_assignment, self.mesh_data, self.colors,
            on_assign_callback=self._on_patch_assigned
        )
        
        # Patch normals tab (in normals tab)
        from tab5_Patches.tab5_patch_normals import PatchNormalsTab
        self.normals_tab = PatchNormalsTab(
            self.tab_normals, self.mesh_data, self.colors, self.renderer
        )
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Force update
        right_frame.update_idletasks()
        update_scrollregion()
        
        # Setup canvas bindings
        self._setup_canvas_bindings()
        
        # Initialize renderer
        self._init_renderer()
        
    # NEW: Handle Add button click - adds selected faces to existing patch
    def _on_patch_add(self, patch_name, patch_data):
        """Add selected faces to an existing patch (no duplicates)"""
        # Check if there are faces selected in the 3D view
        if not self.currently_selected_faces:
            messagebox.showwarning("Warning", "No faces selected in 3D view.\\nClick on faces to select them first.")
            return
        
        # Get current faces in the patch
        if isinstance(patch_data, dict):
            current_faces = set(patch_data.get('faces', []))
        else:
            current_faces = set(patch_data[2]) if len(patch_data) > 2 else set()
        
        # Calculate new faces to add (avoid duplicates)
        new_faces = self.currently_selected_faces - current_faces
        
        if not new_faces:
            messagebox.showinfo("Info", f"All selected faces are already in patch '{patch_name}'.\\nNo new faces to add.")
            return
        
        # Add new faces to the patch (using set union to avoid duplicates)
        updated_faces = current_faces | self.currently_selected_faces
        
        # Update the patch data
        if isinstance(patch_data, dict):
            patch_data['faces'] = list(updated_faces)
        else:
            # Convert tuple to dict if needed
            self.mesh_data.patches[patch_name] = {
                'name': patch_name,
                'type': patch_data[1] if len(patch_data) > 1 else 'patch',
                'faces': list(updated_faces),
                'parameters': {}
            }
        
        # Refresh the list
        self.patch_list_panel.refresh_list()
        
        # Clear renderer selection
        if self.renderer:
            self.renderer.selected_faces.clear()
            self.renderer.draw()
        
        # Clear tracking
        self.currently_selected_faces.clear()
        
        # Update status
        self._update_status()
        
        messagebox.showinfo("Success", 
                          f"Added {len(new_faces)} new face(s) to patch '{patch_name}'\\n"
                          f"Total faces in patch: {len(updated_faces)}")
        
    # Handle patch edit button click
    def _on_patch_edit(self, patch_name, patch_data):
        """Open the patch editor dialog"""
        from tab5_Patches.tab5_patch_editor import open_patch_editor
        
        # Close any existing editor
        if self.patch_editor_dialog:
            try:
                self.patch_editor_dialog.dialog.destroy()
            except:
                pass
        
        # Open new editor
        self.patch_editor_dialog = open_patch_editor(
            parent=self.parent,
            mesh_data=self.mesh_data,
            colors=self.colors,
            patch_name=patch_name,
            patch_data=patch_data,
            renderer=self.renderer,
            on_save_callback=self._on_patch_editor_save
        )
        
        # Override the renderer's click handler to work with the editor
        if self.renderer:
            self.renderer.patch_edit_mode = True
            
    # Handle patch editor save
    def _on_patch_editor_save(self):
        """Called when patch editor saves changes"""
        # Refresh the patch list
        if hasattr(self, 'patch_list_panel'):
            self.patch_list_panel.refresh_list()
        
        # Clear renderer selection
        if self.renderer:
            self.renderer.patch_edit_mode = False
            self.renderer.selected_faces.clear()
            self.renderer.draw()
        
        # Clear reference
        self.patch_editor_dialog = None
        
        # Update status
        self._update_status()
        
    def _on_tab_changed(self, event):
        """Handle tab change in notebook"""
        current_tab = self.notebook.index(self.notebook.select())
        
        # Tab indices: 0=Patches, 1=Assign, 2=Normals
        if current_tab == 2 and self.normals_tab:
            # Normals tab selected - enable patch edit mode
            if self.renderer:
                self.renderer.set_patch_edit_mode(True, self.normals_tab)
                self.normals_tab.renderer = self.renderer  # Update renderer reference
        else:
            # Other tab selected - disable patch edit mode (unless editor is open)
            if self.renderer and not self.patch_editor_dialog:
                self.renderer.set_patch_edit_mode(False)
                
    # FIX: Add mode toggle method
    def _toggle_mode(self):
        """Toggle between Select and Hide modes"""
        self.hide_mode = not self.hide_mode
        
        if self.hide_mode:
            self.mode_button.config(
                text="Mode: Hide",
                bg=self.colors['warning'],
                fg=self.colors['bg']
            )
        else:
            self.mode_button.config(
                text="Mode: Select",
                bg=self.colors['success'],
                fg=self.colors['bg']
            )

    # FIX: Add Show All method
    def _show_all_faces(self):
        """Show all faces that were hidden"""
        if self.renderer:
            self.renderer.show_all_faces()
            hidden_count = self.renderer.get_hidden_face_count()
            if hidden_count > 0:
                self.status_label.config(
                    text=f"Showed all hidden faces ({hidden_count} were hidden)",
                    fg=self.colors['success']
                )
            else:
                self.status_label.config(text="No hidden faces to show", fg=self.colors['fg'])

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
        # FIX: Left click for selection/hiding (no drag)
        self.canvas.bind("<Button-1>", self._on_face_click)
        
        # FIX: Middle mouse button (Button-2) for rotation
        self.canvas.bind("<Button-2>", self._on_middle_click)
        self.canvas.bind("<B2-Motion>", self._on_rotate)
        self.canvas.bind("<ButtonRelease-2>", self._on_rotate_end)
        
        # Right click for panning
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_pan)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)
        
        # Zoom
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-4>", self._on_zoom)
        self.canvas.bind("<Button-5>", self._on_zoom)
        
        # Resize
        self.canvas.bind("<Configure>", lambda e: self._draw())
        
    def _init_renderer(self):
        """Initialize the hex block renderer"""
        from tab5_Patches.tab5_hex_renderer import HexBlockRenderer
        self.renderer = HexBlockRenderer(self.canvas, self.mesh_data)
        self.renderer.on_selection_changed = self._on_face_selection_changed
        
        # Update normals tab with renderer reference
        if self.normals_tab:
            self.normals_tab.renderer = self.renderer
            
        self._update_status()
        self._draw()
        
    def _draw(self):
        """Redraw the 3D view"""
        if self.renderer:
            self.renderer.draw()
            
    # FIX: Separate click handler for face selection/hiding
    def _on_face_click(self, event):
        """Handle left click for face selection or hiding"""
        if not self.renderer:
            return
        
        # If patch editor is open, handle face selection for editor
        if self.patch_editor_dialog and self.renderer.patch_edit_mode:
            item = self.canvas.find_closest(event.x, event.y)[0]
            if item in self.renderer._polygon_to_face:
                face_id = self.renderer._polygon_to_face[item]
                self.patch_editor_dialog.toggle_face_selection(face_id)
            return
        
        # Let renderer handle the click normally
        # The renderer's click handler will be triggered through its canvas binding
        pass
    
    def _on_face_selection_changed(self, selected_faces):
        """Handle face selection change from renderer"""
        # Store the selected faces for Add functionality
        self.currently_selected_faces = selected_faces.copy()
        
        # FIX: In hide mode, hide selected faces instead of selecting them
        if self.hide_mode and self.renderer:
            # Hide the clicked faces
            for face_id in selected_faces:
                # Mark face as hidden
                for face in self.renderer.all_faces:
                    if face['face_id'] == face_id:
                        face['is_visible'] = False
            
            # Clear selection and redraw
            self.renderer.selected_faces.clear()
            self.renderer.draw()
            
            # Update hidden count
            hidden_count = self.renderer.get_hidden_face_count()
            self.status_label.config(
                text=f"Hide mode: {len(selected_faces)} faces hidden ({hidden_count} total hidden)",
                fg=self.colors['warning']
            )
        else:
            # Normal select mode
            self.patch_panel.set_selected_faces(selected_faces)
            self.selected_count_label.config(
                text="Selected faces: %d" % len(selected_faces)
            )
        
    # FIX: Middle mouse button handlers for rotation
    def _on_middle_click(self, event):
        """Handle middle mouse button press (start rotation)"""
        self._rotate_start = (event.x, event.y)
        
    def _on_rotate(self, event):
        """Handle rotation drag (middle mouse button)"""
        if not self.renderer:
            return
        
        dx = event.x - self._rotate_start[0]
        dy = event.y - self._rotate_start[1]
        
        self.renderer.rotation_y += dx * 0.5
        self.renderer.rotation_x -= dy * 0.5
        
        self._rotate_start = (event.x, event.y)
        self.renderer.draw()
        
    def _on_rotate_end(self, event):
        """Handle rotation end"""
        pass

    def _on_patch_assigned(self, patch_data):
        """Handle patch assignment"""
        if 'clear' in patch_data:
            if self.renderer:
                self.renderer.clear_selection()
            # Also clear our tracking
            self.currently_selected_faces.clear()
            return
        
        # Store patch in mesh_data (now a dict)
        patch_name = patch_data['name']
        
        # If patch exists, append faces (avoiding duplicates)
        if patch_name in self.mesh_data.patches:
            existing = self.mesh_data.patches[patch_name]
            existing_faces = set(existing.get('faces', []))
            new_faces = set(patch_data['faces'])
            # Use union to avoid duplicates
            existing['faces'] = list(existing_faces | new_faces)
        else:
            print(patch_name)
            self.mesh_data.patches[patch_name] = patch_data
        
        # Clear tracking
        self.currently_selected_faces.clear()
        
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
        num_blocks = len(getattr(self.mesh_data, 'hex_faces', []))
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
            
    def _fit_all(self):
        """Fit all blocks in view - FIXED to properly calculate zoom"""
        if not self.renderer or not self.renderer.all_faces:
            return
        
        # Calculate bounding box of all visible vertices
        all_verts = []
        for face in self.renderer.all_faces:
            if face['is_visible']:
                all_verts.extend(face['vertices'])
        
        if not all_verts:
            return
        
        verts = np.array(all_verts)
        min_coords = verts.min(axis=0)
        max_coords = verts.max(axis=0)
        
        # Calculate center of bounding box
        center = (min_coords + max_coords) / 2.0
        
        # Reset pan to center the view
        self.renderer.pan_x = 0
        self.renderer.pan_y = 0
        
        # Get canvas dimensions
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Calculate the bounding box dimensions
        bbox_size = max_coords - min_coords
        max_bbox_dim = np.max(bbox_size)
        
        if max_bbox_dim <= 0:
            return
        
        # Calculate zoom to fit the bounding box with 20% padding
        # The projection scale factor is 5 (from _project method)
        padding = 0.8  # 20% padding
        
        # Calculate zoom based on canvas size and bounding box
        # We want: max_bbox_dim * zoom * 5 <= min(canvas_w, canvas_h) * padding
        target_zoom_w = (canvas_w * padding) / (max_bbox_dim * 5)
        target_zoom_h = (canvas_h * padding) / (max_bbox_dim * 5)
        
        # Use the smaller zoom to ensure it fits in both dimensions
        self.renderer.zoom = min(target_zoom_w, target_zoom_h)
        
        # Clamp zoom to reasonable limits
        self.renderer.zoom = max(0.01, min(1000.0, self.renderer.zoom))
        
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