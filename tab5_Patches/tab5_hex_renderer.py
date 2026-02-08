"""
Hex Block 3D Renderer with Internal Face Detection
FIXED: Memory leak from event bindings, added Show All for hidden faces, axes in bottom right
Added: Patch edit mode for normal editing
"""
import tkinter as tk
import numpy as np
import math


class HexBlockRenderer:
    """
    Renders hex blocks in 3D with proper face visibility detection.
    Internal faces (faces shared between two blocks) are hidden.
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
        
        if not hasattr(self.mesh_data, 'hex_blocks') or not self.mesh_data.hex_blocks:
            self._face_cache_valid = True
            return
        
        # Face definitions for a hex block
        face_definitions = [
            ("bottom", [0, 3, 2, 1]),
            ("top", [4, 5, 6, 7]),
            ("front", [0, 1, 5, 4]),
            ("back", [2, 3, 7, 6]),
            ("left", [0, 4, 7, 3]),
            ("right", [1, 2, 6, 5])
        ]
        
        # Collect all faces
        face_list = []
        
        for block_idx, block in enumerate(self.mesh_data.hex_blocks):
            vertices = block.get('vertices', [])
            point_refs = block.get('point_refs', [])
            
            if len(vertices) != 8:
                continue
            
            for face_name, face_indices in face_definitions:
                face_verts = [vertices[i] for i in face_indices]
                face_global_indices = [point_refs[i] for i in face_indices]
                
                face_key = tuple(sorted(face_global_indices))
                
                face_list.append({
                    'block_idx': block_idx,
                    'face_name': face_name,
                    'vertices': face_verts,
                    'global_indices': face_global_indices,
                    'face_key': face_key,
                    'face_id': len(face_list)
                })
        
        # Determine visibility
        face_key_counts = {}
        for face in face_list:
            key = face['face_key']
            face_key_counts[key] = face_key_counts.get(key, 0) + 1
        
        # Build final face list
        for face in face_list:
            key = face['face_key']
            is_internal = face_key_counts[key] > 1
            
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
        
        self._face_cache_valid = True
    
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
        """Draw all visible faces - FIXED memory leak"""
        # If in patch edit mode, don't draw normally
        if self.patch_edit_mode and self.normals_tab:
            self.normals_tab._redraw_canvas()
            return
            
        # FIX: Clear polygon mapping
        self._polygon_to_face.clear()
        
        # FIX: Delete all canvas items (this removes the widgets but not the bindings)
        self.canvas.delete("all")
        
        # Build faces if needed
        self._build_faces()
        
        if not self.all_faces:
            self._draw_no_data_message()
            return
        
        # Filter visible faces
        visible_faces = []
        for face in self.all_faces:
            if not face['is_visible']:
                continue
            
            projected = []
            for vert in face['vertices']:
                sx, sy, sz = self._project(vert)
                projected.append((sx, sy, sz))
            
            avg_depth = sum(p[2] for p in projected) / len(projected)
            
            visible_faces.append({
                **face,
                'projected': projected,
                'avg_depth': avg_depth
            })
        
        # Sort by depth
        visible_faces.sort(key=lambda f: f['avg_depth'], reverse=True)
        
        # Draw faces
        for face in visible_faces:
            face_id = face['face_id']
            projected = face['projected']
            
            points = []
            for p in projected:
                points.extend([p[0], p[1]])
            
            # Determine color
            if face_id in self.selected_faces:
                fill_color = self.colors['face_selected']
                outline_color = self.colors['selected']
                outline_width = 3
            elif face_id == self.hovered_face:
                fill_color = self.colors['face_hover']
                outline_color = self.colors['selected']
                outline_width = 2
            else:
                fill_color = self.colors['face_fill']
                outline_color = self.colors['face_outline']
                outline_width = 1
            
            # FIX: Create polygon and map its ID to face_id
            poly_id = self.canvas.create_polygon(
                points,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                stipple='gray50'
            )
            
            # Store mapping (polygon canvas ID -> face_id)
            self._polygon_to_face[poly_id] = face_id
        
        # Draw wireframe and axes
        self._draw_wireframe()
        self._draw_axes()
    
    def _on_canvas_click(self, event):
        """FIX: Single canvas click handler using find_closest"""
        # If in patch edit mode, handle differently
        if self.patch_edit_mode and self.normals_tab:
            self._on_patch_edit_click(event, self.normals_tab)
            return
            
        # Find which polygon was clicked
        item = self.canvas.find_closest(event.x, event.y)[0]
        
        # Check if this polygon corresponds to a face
        if item in self._polygon_to_face:
            face_id = self._polygon_to_face[item]
            
            # Toggle selection
            if face_id in self.selected_faces:
                self.selected_faces.remove(face_id)
            else:
                self.selected_faces.add(face_id)
            
            self.draw()
            self._notify_selection_change()
    
    def _on_canvas_motion(self, event):
        """FIX: Single motion handler for hover effect"""
        # Skip hover in patch edit mode
        if self.patch_edit_mode:
            return
            
        try:
            item = self.canvas.find_closest(event.x, event.y)[0]
            
            if item in self._polygon_to_face:
                new_hover = self._polygon_to_face[item]
                if new_hover != self.hovered_face:
                    self.hovered_face = new_hover
                    self.draw()
            else:
                if self.hovered_face is not None:
                    self.hovered_face = None
                    self.draw()
        except:
            pass
    
    def _draw_wireframe(self):
        """Draw wireframe edges of blocks"""
        if not hasattr(self.mesh_data, 'hex_blocks'):
            return
        
        edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]
        
        for block in self.mesh_data.hex_blocks:
            vertices = block.get('vertices', [])
            if len(vertices) != 8:
                continue
            
            for i, j in edges:
                p1 = vertices[i]
                p2 = vertices[j]
                
                sx1, sy1, sz1 = self._project(p1)
                sx2, sy2, sz2 = self._project(p2)
                
                if sz1 > -1000 or sz2 > -1000:
                    self.canvas.create_line(
                        sx1, sy1, sx2, sy2,
                        fill=self.colors['face_outline'],
                        width=1
                    )
    
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
    
    def _draw_no_data_message(self):
        """Draw message when no hex blocks exist"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        self.canvas.create_text(
            w/2, h/2,
            text="No hex blocks to display\\n\\nCreate blocks in Tab 4 first",
            fill=self.colors['text'],
            font=('Arial', 14),
            justify=tk.CENTER
        )
    
    def _notify_selection_change(self):
        """Notify parent of selection change"""
        if hasattr(self, 'on_selection_changed'):
            self.on_selection_changed(self.selected_faces.copy())
    
    def get_selected_face_data(self):
        """Get data for selected faces"""
        selected_data = []
        for face in self.all_faces:
            if face['face_id'] in self.selected_faces:
                selected_data.append(face)
        return selected_data
    
    def clear_selection(self):
        """Clear all face selections"""
        self.selected_faces.clear()
        self.draw()
    
    def select_faces_by_block(self, block_idx):
        """Select all visible faces of a specific block"""
        for face in self.all_faces:
            if face['block_idx'] == block_idx and face['is_visible']:
                self.selected_faces.add(face['face_id'])
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
            if not face['is_internal']:
                face['is_visible'] = True
        self.draw()
    
    # FIX: Add method to get count of hidden faces
    def get_hidden_face_count(self):
        """Get the number of user-hidden faces"""
        count = 0
        for face in self.all_faces:
            if not face['is_internal'] and not face['is_visible']:
                count += 1
        return count

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
        patch_face_ids = {f['face_id'] for f in patch_faces}
        
        # Separate faces into patch faces and other faces
        patch_faces_render = []
        other_faces_render = []
        
        for face in self.all_faces:
            if not face.get('is_visible', True):
                continue
                
            projected = []
            for vert in face['vertices']:
                sx, sy, sz = self._project(vert)
                projected.append((sx, sy, sz))
            
            avg_depth = sum(p[2] for p in projected) / len(projected)
            
            render_data = {
                **face,
                'projected': projected,
                'avg_depth': avg_depth
            }
            
            if face['face_id'] in patch_face_ids:
                patch_faces_render.append(render_data)
            else:
                other_faces_render.append(render_data)
        
        # Sort by depth
        patch_faces_render.sort(key=lambda f: f['avg_depth'], reverse=True)
        other_faces_render.sort(key=lambda f: f['avg_depth'], reverse=True)
        
        # Draw other faces as wireframe (dashed lines)
        for face in other_faces_render:
            projected = face['projected']
            points = [(projected[i][0], projected[i][1]) for i in range(len(projected))]
            
            # Draw wireframe outline
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill='#555555', width=1, dash=(2, 2)
                )
        
        # Draw patch faces solid
        for face in patch_faces_render:
            face_id = face['face_id']
            projected = face['projected']
            
            points = []
            for p in projected:
                points.extend([p[0], p[1]])
            
            # Determine if this face has flipped normal
            is_flipped = False
            for pf in patch_faces:
                if pf['face_id'] == face_id:
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
            poly_id = self.canvas.create_polygon(
                points,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                stipple='gray50'
            )
            self._polygon_to_face[poly_id] = face_id
        
        # Draw wireframe for patch faces (edges)
        for face in patch_faces_render:
            projected = face['projected']
            points = [(projected[i][0], projected[i][1]) for i in range(len(projected))]
            
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=self.colors['face_outline'], width=2
                )
        
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
            self.canvas.create_rectangle(
                legend_x, legend_y, legend_x + 15, legend_y + 15,
                fill=color, outline='white'
            )
            self.canvas.create_text(
                legend_x + 20, legend_y + 7,
                text=text, anchor=tk.W,
                fill=self.colors['text'], font=('Arial', 8)
            )
            legend_y += 20

    def _on_patch_edit_click(self, event, normals_tab):
        """Handle click in patch edit mode"""
        item = self.canvas.find_closest(event.x, event.y)[0]
        
        if item in self._polygon_to_face:
            face_id = self._polygon_to_face[item]
            
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


def create_hex_renderer(canvas, mesh_data):
    """Factory function to create a HexBlockRenderer"""
    return HexBlockRenderer(canvas, mesh_data)