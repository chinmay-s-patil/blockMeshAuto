"""
Hex Block 3D Renderer with Internal Face Detection and Patch Coloring Mode
FIXED: Memory leak from event bindings, added Show All for hidden faces, axes in bottom right
Added: Patch edit mode for normal editing
Added: Patch coloring mode - colors faces by their assigned patch
FIXED: Error handling for find_closest on empty canvas
FIXED: Safe dict access for all face and block data
FIXED: Camera-relative depth sorting for proper occlusion and face selection
"""
import tkinter as tk
import numpy as np
import math


class HexBlockRenderer:
    """
    Renders hex blocks in 3D with proper face visibility detection.
    Internal faces (faces shared between two blocks) are hidden.
    Supports patch coloring mode where each patch gets a unique color.
    """

    def __init__(self, canvas, mesh_data):
        self.canvas = canvas
        self.mesh_data = mesh_data

        # Colors for dark mode
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'grid': '#404040',
            'text': '#cccccc',
            'x_axis': '#ff4444',
            'y_axis': '#44ff44',
            'z_axis': '#4444ff',
            'selected': '#00ff00',
            'face_outline': '#888888',
            'face_fill': '#2a2a2a',
            'face_selected': '#4ec9b0',
            'face_hover': '#007acc'
        }

        # Patch coloring colors - distinct colors for each patch
        self.patch_colors = [
            '#e6194b',  # Red
            '#3cb44b',  # Green
            '#ffe119',  # Yellow
            '#4363d8',  # Blue
            '#f58231',  # Orange
            '#911eb4',  # Purple
            '#42d4f4',  # Cyan
            '#f032e6',  # Magenta
            '#bfef45',  # Lime
            '#fabed4',  # Pink
            '#469990',  # Teal
            '#dcbeff',  # Lavender
            '#9a6324',  # Brown
            '#fffac8',  # Beige
            '#800000',  # Maroon
            '#aaffc3',  # Mint
            '#808000',  # Olive
            '#ffd8b1',  # Apricot
            '#000075',  # Navy
            '#a9a9a9',  # Grey
        ]

        # Normal visualization colors
        self.normal_color = '#ffff00'  # Yellow
        self.flipped_normal_color = '#ff00ff'  # Magenta

        # View parameters
        self.rotation_x = 30
        self.rotation_y = -45
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Face data
        self.all_faces = []
        self.selected_faces = set()
        self.hovered_face = None

        # Cache
        self._face_cache_valid = False

        # FIX: Single canvas binding instead of per-face bindings
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

        # Store polygon IDs mapped to face IDs
        self._polygon_to_face = {}

        # Patch edit mode reference
        self.normals_tab = None
        self.patch_edit_mode = False

        # NEW: Patch coloring mode - DEFAULT ON
        self.patch_coloring_mode = True
        self._patch_color_map = {}  # Maps patch_name -> color
        self._face_to_patch_map = {}  # Maps face_id -> patch_name

    def _get_3d_coords_standard(self, global_idx):
        """Get 3D coordinates in standard (X, Y, Z) format"""
        layer, local_idx = self.mesh_data.get_layer_from_global_index(global_idx)
        if layer is None:
            return None
        point_2d = self.mesh_data.points[layer][local_idx]
        coords_raw = self.mesh_data.get_3d_coords(layer, point_2d)
        x, z, y = coords_raw
        return np.array([x, y, z])

    def _build_faces(self):
        """Build all faces from hex blocks and determine visibility"""
        if self._face_cache_valid:
            return

        self.all_faces = []

        # SAFE: Use getattr with default
        hex_blocks = getattr(self.mesh_data, 'hex_blocks', {})
        if not hex_blocks:
            self._face_cache_valid = True
            return

        # Face definitions for a hex block
        face_definitions = [
            ("bottom", [0, 3, 2, 1]),
            ("top", [4, 5, 6, 7]),
            ("front", [0, 1, 5, 4]),
            ("back", [3, 7, 6, 2]),
            ("left", [0, 4, 7, 3]),
            ("right", [1, 2, 6, 5])
        ]

        # Collect all faces
        face_list = []

        # FIX: Use .items() instead of enumerate() since hex_blocks is a dict
        for block_idx, block in hex_blocks.items():
            # SAFE: Use .get() for point_refs
            point_refs = block.get('point_refs', []) if isinstance(block, dict) else []

            if len(point_refs) != 8:
                continue

            # Compute vertices dynamically from point references
            vertices = []
            for global_idx in point_refs:
                coords = self.mesh_data.get_3d_coords_from_global(global_idx)
                if coords is None:
                    vertices = []
                    break
                vertices.append(coords)

            if len(vertices) != 8:
                continue

            for face_name, face_indices in face_definitions:
                face_verts = [vertices[i] for i in face_indices]
                face_global_indices = [point_refs[i] for i in face_indices]

                face_key = tuple(sorted(face_global_indices))

                face_list.append({
                    'block_idx': int(block_idx) if isinstance(block_idx, (int, str)) else 0,
                    'face_name': face_name,
                    'vertices': face_verts,
                    'global_indices': face_global_indices,
                    'face_key': face_key,
                    'face_id': len(face_list)
                })

        # Determine visibility (same as before)
        face_key_counts = {}
        for face in face_list:
            key = face['face_key']
            face_key_counts[key] = face_key_counts.get(key, 0) + 1

        # Build final face list
        for face in face_list:
            key = face['face_key']
            is_internal = face_key_counts.get(key, 0) > 1

            self.all_faces.append({
                'face_id': face['face_id'],
                'block_idx': face['block_idx'],
                'face_name': face['face_name'],
                'vertices': face['vertices'],
                'global_indices': face['global_indices'],
                'is_internal': is_internal,
                'is_visible': not is_internal,
                'center': np.mean(face['vertices'], axis=0)
            })

        # NEW: Build patch mapping for coloring
        self._build_patch_mapping()

        self._face_cache_valid = True

    def _build_patch_mapping(self):
        """Build mapping of faces to patches for coloring - FIXED to match by point IDs"""
        self._face_to_patch_map = {}
        self._patch_color_map = {}
        self._patch_point_set_map = {}  # Maps frozenset of point IDs -> patch_name

        if not hasattr(self.mesh_data, 'patches') or not self.mesh_data.patches:
            return

        # Assign colors to patches
        patch_names = list(self.mesh_data.patches.keys())
        for i, patch_name in enumerate(patch_names):
            self._patch_color_map[patch_name] = self.patch_colors[i % len(self.patch_colors)]

        # Build mapping from point ID set -> patch_name
        # This allows us to match faces even if face_ids don't match
        for patch_name, patch_data in self.mesh_data.patches.items():
            if not isinstance(patch_data, dict):
                continue

            faces = patch_data.get('faces', [])
            for face in faces:
                point_ids = None

                if isinstance(face, dict):
                    # New format: face has 'point_ids' key
                    point_ids = face.get('point_ids', [])
                    # Also try to get face_id for reference
                    face_id = face.get('face_id')
                    if face_id is not None and point_ids:
                        # Store by point set for matching
                        point_set = frozenset(point_ids)
                        self._patch_point_set_map[point_set] = patch_name
                elif isinstance(face, int):
                    # Legacy format: just a face ID - can't match without point IDs
                    pass

        # Now match renderer faces to patches by comparing point IDs
        for face in self.all_faces:
            face_id = face.get('face_id')
            if face_id is None:
                continue

            global_indices = face.get('global_indices', [])
            if len(global_indices) == 4:
                # Create a frozenset of the point IDs for matching
                point_set = frozenset(global_indices)

                # Check if this point set belongs to any patch
                if point_set in self._patch_point_set_map:
                    self._face_to_patch_map[face_id] = self._patch_point_set_map[point_set]

    def _get_camera_position(self):
        """
        Calculate the camera position in world space based on current rotation.
        The camera is positioned along the view direction at a large distance.
        This allows proper depth sorting from the camera's perspective.
        """
        # The view is constructed by rotating the world around the origin
        # We need to find where the camera is in world space

        # The view direction in view space is (0, 0, 1) - looking down +Z
        # We need to apply inverse rotations to get the world space direction
        rad_y = math.radians(self.rotation_y)
        rad_x = math.radians(self.rotation_x)

        # Start with view direction (0, 0, 1)
        # Apply inverse rotation Y (rotate by -rotation_y)
        cos_y, sin_y = math.cos(-rad_y), math.sin(-rad_y)
        x = sin_y * 1.0  # z component starts as 1
        z = cos_y * 1.0

        # Apply inverse rotation X (rotate by -rotation_x)
        cos_x, sin_x = math.cos(-rad_x), math.sin(-rad_x)
        y = z * sin_x
        z = z * cos_x

        # The camera is positioned far along this direction
        camera_distance = 1000.0
        camera_pos = np.array([x, y, z]) * camera_distance

        return camera_pos

    def _rotate_point(self, point):
        """Apply rotation to a 3D point"""
        x, y, z = point

        rad_x = math.radians(self.rotation_x)
        cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

        rad_y = math.radians(self.rotation_y)
        cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
        z, x = z * cos_y - x * sin_y, z * sin_y + x * cos_y

        return np.array([x, y, z])

    def _project(self, point_3d):
        """Project 3D point to 2D canvas coordinates"""
        rotated = self._rotate_point(point_3d)
        x, y = rotated[0], rotated[1]

        cx = self.canvas.winfo_width() / 2 + self.pan_x
        cy = self.canvas.winfo_height() / 2 + self.pan_y

        screen_x = cx + x * self.zoom * 5
        screen_y = cy - y * self.zoom * 5

        return screen_x, screen_y, rotated[2]

    def draw(self):
        """Draw all visible faces - with patch coloring support and proper camera-relative depth sorting"""
        # If in patch edit mode, don't draw normally
        if self.patch_edit_mode and self.normals_tab:
            self.normals_tab._redraw_canvas()
            return

        # FIX: Clear polygon mapping
        self._polygon_to_face.clear()

        # FIX: Delete all canvas items
        self.canvas.delete("all")

        # Build faces if needed
        self._build_faces()

        if not self.all_faces:
            self._draw_no_data_message()
            return

        # Calculate camera position in world space for proper depth sorting
        camera_pos = self._get_camera_position()

        # Filter visible faces and calculate camera-relative depth
        visible_faces = []
        for face in self.all_faces:
            if not face.get('is_visible', False):
                continue

            vertices = face.get('vertices', [])
            if not vertices:
                continue

            projected = []
            for vert in vertices:
                sx, sy, sz = self._project(vert)
                projected.append((sx, sy, sz))

            if not projected:
                continue

            # Calculate face center in world space
            face_center = np.mean(vertices, axis=0)

            # Calculate distance from camera to face center (true depth from camera)
            distance_to_camera = np.linalg.norm(face_center - camera_pos)

            visible_faces.append({
                **face,
                'projected': projected,
                'camera_distance': distance_to_camera
            })

        # Sort by camera distance - furthest faces first (painter's algorithm)
        # This ensures proper occlusion regardless of view angle
        visible_faces.sort(key=lambda f: f.get('camera_distance', 0), reverse=True)

        # Draw faces back-to-front
        for face in visible_faces:
            face_id = face.get('face_id')
            if face_id is None:
                continue
            projected = face.get('projected', [])
            if not projected:
                continue

            points = []
            for p in projected:
                points.extend([p[0], p[1]])

            # Determine color based on mode
            fill_color, outline_color, outline_width = self._get_face_colors(face_id)

            # Create polygon
            try:
                poly_id = self.canvas.create_polygon(
                    points,
                    fill=fill_color,
                    outline=outline_color,
                    width=outline_width,
                    stipple='gray50'
                )

                # Store mapping (polygon canvas ID -> face_id)
                self._polygon_to_face[poly_id] = face_id
            except Exception as e:
                print(f"Error creating polygon for face {face_id}: {e}")

        # Draw wireframe and axes
        self._draw_wireframe()
        self._draw_axes()

        # NEW: Draw patch legend if in patch coloring mode
        if self.patch_coloring_mode and self._patch_color_map:
            self._draw_patch_legend()

    def _get_face_colors(self, face_id):
        """Get fill, outline colors and outline width for a face"""
        # Selection takes priority
        if face_id in self.selected_faces:
            return self.colors['face_selected'], self.colors['selected'], 3

        if face_id == self.hovered_face:
            return self.colors['face_hover'], self.colors['selected'], 2

        # Patch coloring mode
        if self.patch_coloring_mode and face_id in self._face_to_patch_map:
            patch_name = self._face_to_patch_map[face_id]
            fill_color = self._patch_color_map.get(patch_name, self.colors['face_fill'])
            return fill_color, self.colors['face_outline'], 1

        # Default
        return self.colors['face_fill'], self.colors['face_outline'], 1

    def _draw_patch_legend(self):
        """Draw legend showing patch names and their colors - FIXED position top right"""
        # Position at top right instead of top left
        canvas_width = self.canvas.winfo_width()
        legend_x = canvas_width - 210  # 200px width + 10px margin from right
        legend_y = 10
        item_height = 20
        max_width = 200

        # Draw background
        num_patches = len(self._patch_color_map)
        if num_patches == 0:
            return

        bg_height = num_patches * item_height + 10

        try:
            # Semi-transparent background
            bg_id = self.canvas.create_rectangle(
                legend_x - 5, legend_y - 5,
                legend_x + max_width, legend_y + bg_height,
                fill='#1e1e1e',
                outline='#3e3e42',
                stipple='gray75'
            )

            # Title
            self.canvas.create_text(
                legend_x + 5, legend_y,
                text="Patches",
                anchor=tk.NW,
                fill='#ffffff',
                font=('Arial', 10, 'bold')
            )
            legend_y += 18

            # Each patch entry
            for patch_name, color in self._patch_color_map.items():
                # Color swatch
                self.canvas.create_rectangle(
                    legend_x, legend_y,
                    legend_x + 15, legend_y + 12,
                    fill=color,
                    outline='#ffffff'
                )

                # Patch name
                display_name = patch_name[:25] + '...' if len(patch_name) > 25 else patch_name
                self.canvas.create_text(
                    legend_x + 20, legend_y + 6,
                    text=display_name,
                    anchor=tk.W,
                    fill='#cccccc',
                    font=('Arial', 9)
                )

                legend_y += item_height

        except tk.TclError:
            pass

    def _on_canvas_click(self, event):
        """FIX: Camera-aware face selection - selects the front-most face at cursor position"""
        # If in patch edit mode, handle differently
        if self.patch_edit_mode and self.normals_tab:
            self._on_patch_edit_click(event, self.normals_tab)
            return

        # FIX: Handle empty canvas case
        try:
            # Check if there are any items on the canvas
            all_items = self.canvas.find_all()
            if not all_items:
                return

            # Find all polygons near the cursor (within a small radius)
            # This catches faces that might be overlapping at this screen position
            search_radius = 10
            items = self.canvas.find_overlapping(
                event.x - search_radius, event.y - search_radius,
                event.x + search_radius, event.y + search_radius
            )

            # Filter to only polygons that correspond to faces
            candidate_faces = []
            for item in items:
                if item in self._polygon_to_face:
                    face_id = self._polygon_to_face[item]
                    # Find the face data to get its camera distance
                    for face in self.all_faces:
                        if face.get('face_id') == face_id:
                            # Calculate current camera distance for this face
                            vertices = face.get('vertices', [])
                            if vertices:
                                face_center = np.mean(vertices, axis=0)
                                camera_pos = self._get_camera_position()
                                distance = np.linalg.norm(face_center - camera_pos)
                                candidate_faces.append((face_id, distance))
                            break

            if not candidate_faces:
                # Fallback to single closest item if no overlapping faces found
                closest = self.canvas.find_closest(event.x, event.y)
                if not closest:
                    return
                item = closest[0]
                if item in self._polygon_to_face:
                    face_id = self._polygon_to_face[item]
                    candidate_faces = [(face_id, 0)]
                else:
                    return

            # Select the face closest to camera (smallest distance)
            candidate_faces.sort(key=lambda x: x[1])
            face_id = candidate_faces[0][0]

            # Toggle selection
            if face_id in self.selected_faces:
                self.selected_faces.remove(face_id)
            else:
                self.selected_faces.add(face_id)

            self.draw()
            self._notify_selection_change()
        except (IndexError, tk.TclError) as e:
            # IndexError: find_closest returned empty tuple
            # TclError: canvas operation failed
            pass

    def _on_canvas_motion(self, event):
        """FIX: Single motion handler for hover effect with error handling"""
        # Skip hover in patch edit mode
        if self.patch_edit_mode:
            return

        try:
            # Check if there are any items on the canvas
            all_items = self.canvas.find_all()
            if not all_items:
                if self.hovered_face is not None:
                    self.hovered_face = None
                    self.draw()
                return

            closest = self.canvas.find_closest(event.x, event.y)
            if not closest:
                if self.hovered_face is not None:
                    self.hovered_face = None
                    self.draw()
                return
            item = closest[0]

            if item in self._polygon_to_face:
                new_hover = self._polygon_to_face[item]
                if new_hover != self.hovered_face:
                    self.hovered_face = new_hover
                    self.draw()
            else:
                if self.hovered_face is not None:
                    self.hovered_face = None
                    self.draw()
        except (IndexError, tk.TclError):
            pass

    def _draw_wireframe(self):
        """Draw wireframe edges of blocks"""
        # SAFE: Use getattr with default
        hex_blocks = getattr(self.mesh_data, 'hex_blocks', {})
        if not hex_blocks:
            return

        edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]

        for block_idx, block in hex_blocks.items():
            # SAFE: Use .get() for point_refs
            point_refs = block.get('point_refs', []) if isinstance(block, dict) else []
            if len(point_refs) != 8:
                continue

            # Get vertices from point references
            vertices = []
            for pid in point_refs:
                coords = self.mesh_data.get_3d_coords_from_global(pid)
                if coords:
                    vertices.append(coords)
                else:
                    vertices = []
                    break

            if len(vertices) != 8:
                continue

            for i, j in edges:
                p1 = vertices[i]
                p2 = vertices[j]

                sx1, sy1, sz1 = self._project(p1)
                sx2, sy2, sz2 = self._project(p2)

                if sz1 > -1000 or sz2 > -1000:
                    try:
                        self.canvas.create_line(
                            sx1, sy1, sx2, sy2,
                            fill=self.colors['face_outline'],
                            width=1
                        )
                    except tk.TclError:
                        pass

    def _draw_axes(self):
        """Draw coordinate axes in bottom right corner"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        # FIX: Move to bottom right corner
        center_x = w - 50
        center_y = h - 50
        length = 30

        x_vec = self._rotate_point([length, 0, 0])
        y_vec = self._rotate_point([0, length, 0])
        z_vec = self._rotate_point([0, 0, length])

        try:
            self.canvas.create_line(center_x, center_y, 
                                   center_x + x_vec[0], center_y - x_vec[1],
                                   fill=self.colors['x_axis'], width=3, arrow=tk.LAST)
            self.canvas.create_line(center_x, center_y, 
                                   center_x + y_vec[0], center_y - y_vec[1],
                                   fill=self.colors['y_axis'], width=3, arrow=tk.LAST)
            self.canvas.create_line(center_x, center_y, 
                                   center_x + z_vec[0], center_y - z_vec[1],
                                   fill=self.colors['z_axis'], width=3, arrow=tk.LAST)

            label_offset = 8
            self.canvas.create_text(center_x + x_vec[0] + label_offset, 
                                   center_y - x_vec[1] - label_offset,
                                   text="X", fill=self.colors['x_axis'], 
                                   font=('Arial', 10, 'bold'))
            self.canvas.create_text(center_x + y_vec[0] + label_offset, 
                                   center_y - y_vec[1] - label_offset,
                                   text="Y", fill=self.colors['y_axis'], 
                                   font=('Arial', 10, 'bold'))
            self.canvas.create_text(center_x + z_vec[0] + label_offset, 
                                   center_y - z_vec[1] - label_offset,
                                   text="Z", fill=self.colors['z_axis'], 
                                   font=('Arial', 10, 'bold'))
        except tk.TclError:
            pass

    def _draw_no_data_message(self):
        """Draw message when no hex blocks exist"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        try:
            self.canvas.create_text(
                w/2, h/2,
                text="No hex blocks to display\n\nCreate blocks in Tab 4 first",
                fill=self.colors['text'],
                font=('Arial', 14),
                justify=tk.CENTER
            )
        except tk.TclError:
            pass

    def _notify_selection_change(self):
        """Notify parent of selection change"""
        if hasattr(self, 'on_selection_changed') and callable(self.on_selection_changed):
            try:
                self.on_selection_changed(self.selected_faces.copy())
            except Exception as e:
                print(f"Error in selection change callback: {e}")

    def get_selected_face_data(self):
        """Get data for selected faces"""
        selected_data = []
        for face in self.all_faces:
            if face.get('face_id') in self.selected_faces:
                selected_data.append(face)
        return selected_data

    def clear_selection(self):
        """Clear all face selections"""
        self.selected_faces.clear()
        self.draw()

    def select_faces_by_block(self, block_idx):
        """Select all visible faces of a specific block"""
        for face in self.all_faces:
            if face.get('block_idx') == block_idx and face.get('is_visible', False):
                self.selected_faces.add(face.get('face_id'))
        self.draw()

    def invalidate_cache(self):
        """Invalidate face cache (call when blocks change)"""
        self._face_cache_valid = False
        self.all_faces = []
        self.selected_faces.clear()

    # FIX: Add method to show all hidden faces (unhide)
    def show_all_faces(self):
        """Show all faces that were hidden by the user"""
        for face in self.all_faces:
            # Only unhide faces that are not internal
            if not face.get('is_internal', False):
                face['is_visible'] = True
        self.draw()

    # FIX: Add method to get count of hidden faces
    def get_hidden_face_count(self):
        """Get the number of user-hidden faces"""
        count = 0
        for face in self.all_faces:
            if not face.get('is_internal', False) and not face.get('is_visible', True):
                count += 1
        return count

    # ============================================================
    # NEW: Patch Coloring Mode Controls
    # ============================================================

    def set_patch_coloring_mode(self, enabled):
        """Enable or disable patch coloring mode"""
        self.patch_coloring_mode = enabled
        self.invalidate_cache()  # Rebuild to update patch mapping
        self.draw()

    def toggle_patch_coloring(self):
        """Toggle patch coloring mode on/off"""
        self.patch_coloring_mode = not self.patch_coloring_mode
        self.draw()
        return self.patch_coloring_mode

    # ============================================================
    # NEW: Patch Edit Mode for Normal Editing
    # ============================================================

    def set_patch_edit_mode(self, enabled, normals_tab=None):
        """Enable or disable patch edit mode"""
        self.patch_edit_mode = enabled
        self.normals_tab = normals_tab
        self.draw()

    def draw_patch_edit_mode(self, patch_faces, normals_tab):
        """
        Draw scene in patch edit mode:
        - Selected patch faces are shown solid with normals
        - Other faces are shown as wireframe only
        """
        self._polygon_to_face.clear()
        self.canvas.delete("all")

        if not self.all_faces:
            self._build_faces()

        # Get set of face IDs in the patch
        patch_face_ids = {f.get('face_id') for f in patch_faces if f.get('face_id') is not None}

        # Calculate camera position for proper sorting
        camera_pos = self._get_camera_position()

        # Separate faces into patch faces and other faces
        patch_faces_render = []
        other_faces_render = []

        for face in self.all_faces:
            if not face.get('is_visible', True):
                continue

            vertices = face.get('vertices', [])
            if not vertices:
                continue

            projected = []
            for vert in vertices:
                sx, sy, sz = self._project(vert)
                projected.append((sx, sy, sz))

            if not projected:
                continue

            # Calculate face center in world space for camera-relative depth
            face_center = np.mean(vertices, axis=0)
            camera_distance = np.linalg.norm(face_center - camera_pos)

            render_data = {
                **face,
                'projected': projected,
                'camera_distance': camera_distance
            }

            if face.get('face_id') in patch_face_ids:
                patch_faces_render.append(render_data)
            else:
                other_faces_render.append(render_data)

        # Sort by camera distance for proper occlusion
        patch_faces_render.sort(key=lambda f: f.get('camera_distance', 0), reverse=True)
        other_faces_render.sort(key=lambda f: f.get('camera_distance', 0), reverse=True)

        # Draw other faces as wireframe (dashed lines)
        for face in other_faces_render:
            projected = face.get('projected', [])
            if not projected:
                continue
            points = [(projected[i][0], projected[i][1]) for i in range(len(projected))]

            # Draw wireframe outline
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                try:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill='#555555', width=1, dash=(2, 2)
                    )
                except tk.TclError:
                    pass

        # Draw patch faces solid
        for face in patch_faces_render:
            face_id = face.get('face_id')
            if face_id is None:
                continue
            projected = face.get('projected', [])
            if not projected:
                continue

            points = []
            for p in projected:
                points.extend([p[0], p[1]])

            # Determine if this face has flipped normal
            is_flipped = False
            for pf in patch_faces:
                if pf.get('face_id') == face_id:
                    is_flipped = pf.get('normal_flipped', False)
                    break

            # Color based on selection and flip state
            if face_id in self.selected_faces:
                fill_color = self.colors['face_selected']
                outline_color = self.colors['selected']
                outline_width = 3
            elif is_flipped:
                fill_color = '#663366'  # Purple tint for flipped faces
                outline_color = self.flipped_normal_color
                outline_width = 2
            else:
                fill_color = self.colors['face_fill']
                outline_color = self.colors['face_outline']
                outline_width = 1

            # Create polygon
            try:
                poly_id = self.canvas.create_polygon(
                    points,
                    fill=fill_color,
                    outline=outline_color,
                    width=outline_width,
                    stipple='gray50'
                )
                self._polygon_to_face[poly_id] = face_id
            except tk.TclError:
                pass

        # Draw wireframe for patch faces (edges)
        for face in patch_faces_render:
            projected = face.get('projected', [])
            if not projected:
                continue
            points = [(projected[i][0], projected[i][1]) for i in range(len(projected))]

            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                try:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=self.colors['face_outline'], width=2
                    )
                except tk.TclError:
                    pass

        # Draw normals
        if normals_tab:
            normals_tab.draw_normals(self.canvas)

        # Draw axes
        self._draw_axes()

        # Draw legend
        self._draw_patch_edit_legend()

    def _draw_patch_edit_legend(self):
        """Draw legend for patch edit mode"""
        legend_x = 10
        legend_y = 10

        # Legend items
        items = [
            (self.colors['face_fill'], "Patch Face"),
            ('#663366', "Flipped Normal"),
            (self.colors['face_selected'], "Selected"),
            ('#555555', "Other Faces (wireframe)")
        ]

        for color, text in items:
            try:
                self.canvas.create_rectangle(
                    legend_x, legend_y, legend_x + 15, legend_y + 15,
                    fill=color, outline='white'
                )
                self.canvas.create_text(
                    legend_x + 20, legend_y + 7,
                    text=text, anchor=tk.W,
                    fill=self.colors['text'], font=('Arial', 8)
                )
            except tk.TclError:
                pass
            legend_y += 20

    def _on_patch_edit_click(self, event, normals_tab):
        """Handle click in patch edit mode with error handling"""
        try:
            # Check if there are any items on the canvas
            all_items = self.canvas.find_all()
            if not all_items:
                return

            # Use camera-aware selection like main click handler
            search_radius = 10
            items = self.canvas.find_overlapping(
                event.x - search_radius, event.y - search_radius,
                event.x + search_radius, event.y + search_radius
            )

            candidate_faces = []
            for item in items:
                if item in self._polygon_to_face:
                    face_id = self._polygon_to_face[item]
                    for face in self.all_faces:
                        if face.get('face_id') == face_id:
                            vertices = face.get('vertices', [])
                            if vertices:
                                face_center = np.mean(vertices, axis=0)
                                camera_pos = self._get_camera_position()
                                distance = np.linalg.norm(face_center - camera_pos)
                                candidate_faces.append((face_id, distance))
                            break

            if not candidate_faces:
                closest = self.canvas.find_closest(event.x, event.y)
                if not closest:
                    return
                item = closest[0]
                if item in self._polygon_to_face:
                    face_id = self._polygon_to_face[item]
                    candidate_faces = [(face_id, 0)]
                else:
                    return

            # Select closest to camera
            candidate_faces.sort(key=lambda x: x[1])
            face_id = candidate_faces[0][0]

            # Try to handle in normals tab first (for flip mode)
            if normals_tab and normals_tab.handle_face_click(face_id):
                return

            # Otherwise toggle selection
            if face_id in self.selected_faces:
                self.selected_faces.remove(face_id)
            else:
                self.selected_faces.add(face_id)

            # Redraw
            if normals_tab and normals_tab.selected_patch_name:
                normals_tab._redraw_canvas()
            else:
                self.draw()
        except (IndexError, tk.TclError):
            pass


def create_hex_renderer(canvas, mesh_data):
    """Factory function to create a HexBlockRenderer"""
    return HexBlockRenderer(canvas, mesh_data)