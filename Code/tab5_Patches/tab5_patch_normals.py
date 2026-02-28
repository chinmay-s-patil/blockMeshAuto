"""
Patch Normals Tab for Tab 5
Allows visualization and flipping of face normals for patches
"""
import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np
import math


class PatchNormalsTab:
    """
    Tab for viewing and editing patch face normals.
    Shows only the selected patch with normal arrows, allows flipping normals.
    """
    
    def __init__(self, parent, mesh_data, colors, renderer):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.renderer = renderer  # Reference to the main HexBlockRenderer
        
        # State
        self.selected_patch_name = None
        self.patch_faces = []  # List of face data for the selected patch
        self.normal_arrows = []  # Store arrow canvas IDs
        self.flip_mode = False  # When True, clicking a face flips its normal
        
        # Normal visualization settings
        self.normal_length = 20  # Length of normal arrows in screen pixels
        self.normal_color = '#ffff00'  # Yellow for normals
        self.flipped_normal_color = '#ff00ff'  # Magenta for flipped normals
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the patch normals UI"""
        main_frame = tk.LabelFrame(self.parent, text="Patch Normals Editor", 
                                   padx=10, pady=10,
                                   bg=self.colors['secondary'],
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   font=("Arial", 10, "bold"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Instructions
        instructions = """Select a patch to view its faces and normals.
Yellow arrows show current normal direction.
Click "Flip Normal Mode" then click a face to reverse its normal."""
        
        tk.Label(main_frame, text=instructions,
                font=("Arial", 9), justify=tk.LEFT,
                fg=self.colors['fg'], bg=self.colors['secondary'],
                wraplength=350).pack(anchor=tk.W, pady=(0, 10))
        
        # Patch selection dropdown
        patch_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        patch_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(patch_frame, text="Select Patch:",
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.patch_var = tk.StringVar(value="")
        self.patch_combo = ttk.Combobox(patch_frame, textvariable=self.patch_var,
                                       state="readonly", width=25)
        self.patch_combo.pack(side=tk.LEFT, padx=5)
        self.patch_combo.bind("<<ComboboxSelected>>", self._on_patch_selected)
        
        tk.Button(patch_frame, text="🔄 Refresh",
                 command=self._refresh_patch_list,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 font=("Arial", 8), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # Patch info
        self.patch_info_label = tk.Label(main_frame, text="No patch selected",
                                        font=("Arial", 9),
                                        fg=self.colors['axis'],
                                        bg=self.colors['secondary'])
        self.patch_info_label.pack(anchor=tk.W, pady=5)
        
        # Separator
        tk.Frame(main_frame, bg=self.colors['border'], height=2).pack(fill=tk.X, pady=10)
        
        # Normal editing section
        tk.Label(main_frame, text="Normal Editing",
                font=("Arial", 10, "bold"),
                fg=self.colors['fg'], bg=self.colors['secondary']).pack(anchor=tk.W)
        
        # Flip mode toggle button
        self.flip_button = tk.Button(main_frame, text="🔄 Flip Normal Mode: OFF",
                                    command=self._toggle_flip_mode,
                                    bg=self.colors['button_bg'], 
                                    fg=self.colors['button_fg'],
                                    font=("Arial", 10, "bold"), relief=tk.FLAT,
                                    activebackground=self.colors['button_active'])
        self.flip_button.pack(fill=tk.X, pady=10)
        
        # Normal visualization controls
        control_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="Arrow Length:",
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        self.arrow_length_var = tk.IntVar(value=self.normal_length)
        tk.Scale(control_frame, from_=10, to=50, orient=tk.HORIZONTAL,
                variable=self.arrow_length_var,
                command=self._on_arrow_length_changed,
                bg=self.colors['secondary'], fg=self.colors['fg'],
                highlightbackground=self.colors['secondary']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action buttons
        btn_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="✓ Apply Changes",
                 command=self._apply_changes,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 10, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f').pack(fill=tk.X, pady=2)
        
        tk.Button(btn_frame, text="⟲ Reset Normals",
                 command=self._reset_normals,
                 bg=self.colors['warning'], fg=self.colors['bg'],
                 font=("Arial", 9), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        
        tk.Button(btn_frame, text="✗ Close Editor",
                 command=self._close_editor,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9), relief=tk.FLAT).pack(fill=tk.X, pady=2)
        
        # Status
        self.status_label = tk.Label(main_frame, text="Ready",
                                    font=("Arial", 9, "italic"),
                                    fg=self.colors['success'],
                                    bg=self.colors['secondary'])
        self.status_label.pack(anchor=tk.W, pady=10)
        
        # Initialize patch list
        self._refresh_patch_list()
        
    def _refresh_patch_list(self):
        """Refresh the list of available patches"""
        patch_names = []
        if hasattr(self.mesh_data, 'patches') and self.mesh_data.patches:
            patch_names = list(self.mesh_data.patches.keys())
        
        self.patch_combo['values'] = patch_names
        
        if patch_names and not self.selected_patch_name:
            self.patch_var.set(patch_names[0])
            self._on_patch_selected()
            
    def _on_patch_selected(self, event=None):
        """Handle patch selection"""
        patch_name = self.patch_var.get()
        if not patch_name:
            return
            
        self.selected_patch_name = patch_name
        
        # Get patch data
        patch_data = self.mesh_data.patches.get(patch_name, {})
        faces_data = patch_data.get('faces', [])
        patch_normal = patch_data.get('Normal', 1)

        # FIXED: Handle new face format where faces are dicts with 'face_id'
        if faces_data and isinstance(faces_data[0], dict):
            # New format: extract face_ids from dicts
            face_ids = {f.get('face_id') for f in faces_data if isinstance(f, dict)}
        else:
            # Legacy format: face_ids are integers
            face_ids = set(faces_data)
        
        # Build face data for this patch
        self.patch_faces = []
        if self.renderer and hasattr(self.renderer, 'all_faces'):
            for face in self.renderer.all_faces:
                if face['face_id'] in face_ids:
                    # Store face with its normal state
                    face_copy = dict(face)
                    face_copy['normal_flipped'] = (patch_normal == -1)
                    if face_copy['normal_flipped']:
                        face_copy['vertices'] = face_copy['vertices'][::-1]
                    face_copy['original_vertices'] = face['vertices'].copy()
                    self.patch_faces.append(face_copy)
        
        self.patch_info_label.config(
            text=f"Patch: {patch_name} | Faces: {len(self.patch_faces)}"
        )
        
        self.status_label.config(
            text=f"Loaded {len(self.patch_faces)} faces for editing",
            fg=self.colors['success']
        )
        
        # Trigger redraw to show this patch
        self._redraw_canvas()
        
    def _toggle_flip_mode(self):
        """Toggle flip normal mode"""
        self.flip_mode = not self.flip_mode
        
        if self.flip_mode:
            self.flip_button.config(
                text="🔄 Flip Normal Mode: ON (Click face to flip)",
                bg=self.colors['warning']
            )
            self.status_label.config(
                text="Flip mode ON - Click on a face to reverse its normal",
                fg=self.colors['warning']
            )
        else:
            self.flip_button.config(
                text="🔄 Flip Normal Mode: OFF",
                bg=self.colors['button_bg']
            )
            self.status_label.config(
                text="Flip mode OFF",
                fg=self.colors['success']
            )
            
    def _on_arrow_length_changed(self, value):
        """Handle arrow length slider change"""
        self.normal_length = int(value)
        self._redraw_canvas()
        
    def calculate_face_normal(self, vertices):
        """
        Calculate face normal using cross product.
        vertices: list of 4 vertices defining the face (quad)
        Returns: normalized normal vector (numpy array)
        """
        if len(vertices) < 3:
            return np.array([0, 0, 1])
        
        # Use first 3 vertices to calculate normal
        v0 = np.array(vertices[0])
        v1 = np.array(vertices[1])
        v2 = np.array(vertices[2])
        
        # Two edge vectors
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        # Cross product gives normal
        normal = np.cross(edge1, edge2)
        
        # Normalize
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
        
        return normal
    
    def _project_point(self, point_3d):
        """Project 3D point to 2D canvas coordinates using renderer's projection"""
        if not self.renderer:
            return 0, 0
            
        # Use the renderer's projection method
        return self.renderer._project(point_3d)
    
    def _redraw_canvas(self):
        """Redraw the canvas showing only the selected patch with normals"""
        if not self.renderer:
            return
            
        # Clear normal arrows
        self.normal_arrows = []
        
        # Tell renderer to draw in "patch edit mode"
        # This will be handled by the main draw method
        self.renderer.draw_patch_edit_mode(self.patch_faces, self)
        
    def draw_normals(self, canvas):
        """Draw normal arrows for all faces in the patch"""
        for face in self.patch_faces:
            if not face.get('is_visible', True):
                continue
                
            vertices = face['vertices']
            
            # Calculate face center
            center = np.mean(vertices, axis=0)
            
            # Calculate normal
            normal = self.calculate_face_normal(vertices)
            
            # If normal is flipped, reverse it for display
            if face.get('normal_flipped', False):
                normal = -normal
                color = self.flipped_normal_color
            else:
                color = self.normal_color
            
            # Project center point
            cx, cy, cz = self._project_point(center)
            
            # Calculate arrow end point (in 3D)
            arrow_end_3d = center + normal * (self.normal_length / self.renderer.zoom / 5)
            ex, ey, ez = self._project_point(arrow_end_3d)
            
            # Draw arrow line
            arrow_id = canvas.create_line(
                cx, cy, ex, ey,
                fill=color, width=3, arrow=tk.LAST
            )
            self.normal_arrows.append(arrow_id)
            
            # Draw normal label
            mid_x = (cx + ex) / 2
            mid_y = (cy + ey) / 2
            label_id = canvas.create_text(
                mid_x, mid_y - 10,
                text="N", fill=color,
                font=('Arial', 8, 'bold')
            )
            self.normal_arrows.append(label_id)
            
    def flip_face_normal(self, face_id):
        """Flip the normals for the ENTIRE patch by reversing vertex order on all its faces"""
        # Determine if we are flipping to True or False based on the clicked face
        target_flip_state = True
        for face in self.patch_faces:
            if face['face_id'] == face_id:
                target_flip_state = not face.get('normal_flipped', False)
                break
                
        # Apply to all faces in the patch
        for face in self.patch_faces:
            if face.get('normal_flipped', False) != target_flip_state:
                face['normal_flipped'] = target_flip_state
                # Reverse vertex order to flip normal visually
                face['vertices'] = face['vertices'][::-1]
                
        self.status_label.config(
            text=f"Flipped normals for entire patch '{self.selected_patch_name}'",
            fg=self.colors['warning']
        )
        return True
        
    def handle_face_click(self, face_id):
        """Handle click on a face in the canvas"""
        if self.flip_mode and self.selected_patch_name:
            if self.flip_face_normal(face_id):
                self._redraw_canvas()
                return True
        return False
        
    def _apply_changes(self):
        """Apply normal changes to the mesh data"""
        if not self.selected_patch_name:
            messagebox.showwarning("Warning", "No patch selected")
            return
            
        # Update the patch data
        patch_data = self.mesh_data.patches.get(self.selected_patch_name, {})
        
        # Check if faces are flipped (since all faces match, we check any)
        is_flipped = any(face.get('normal_flipped', False) for face in self.patch_faces)
        
        # Set patch normal
        patch_data['Normal'] = -1 if is_flipped else 1
        
        self.status_label.config(
            text=f"Applied changes: Patch Normal set to {patch_data['Normal']}",
            fg=self.colors['success']
        )
        messagebox.showinfo("Success", 
                          f"Applied normal direction (Normal={patch_data['Normal']})\n"
                          f"for patch '{self.selected_patch_name}'")
                        
    def _reset_normals(self):
        """Reset all normals to their original state"""
        for face in self.patch_faces:
            if face.get('normal_flipped', False):
                face['normal_flipped'] = False
                face['vertices'] = face['original_vertices'].copy()
                
        self.status_label.config(
            text="Reset all normals to original state",
            fg=self.colors['success']
        )
        self._redraw_canvas()
        
    def _close_editor(self):
        """Close the patch normals editor and return to normal view"""
        self.selected_patch_name = None
        self.patch_faces = []
        self.flip_mode = False
        
        # Restore normal renderer view
        if self.renderer:
            self.renderer.draw()
            
        self.status_label.config(
            text="Editor closed - returned to normal view",
            fg=self.colors['fg']
        )