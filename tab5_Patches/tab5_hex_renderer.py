"""
Hex Block 3D Renderer with Internal Face Detection
Renders hex blocks and hides internal faces (faces shared between blocks)
Similar to OpenFOAM blockMesh behavior
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
        
        # View parameters
        self.rotation_x = 30
        self.rotation_y = -45
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Face data
        self.all_faces = []  # List of all visible faces with metadata
        self.selected_faces = set()
        self.hovered_face = None
        
        # Cache
        self._face_cache = None
        
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
        """
        Build all faces from hex blocks and determine visibility.
        Internal faces (shared between blocks) are marked as hidden.
        """
        self.all_faces = []
        
        if not hasattr(self.mesh_data, 'hex_blocks') or not self.mesh_data.hex_blocks:
            return
        
        # Face definitions for a hex block (vertex indices for each face)
        # OpenFOAM vertex order: 0-1-2-3 bottom, 4-5-6-7 top
        face_definitions = [
            ("bottom", [0, 3, 2, 1]),  # z-min
            ("top", [4, 5, 6, 7]),     # z-max
            ("front", [0, 1, 5, 4]),   # y-min
            ("back", [2, 3, 7, 6]),    # y-max
            ("left", [0, 4, 7, 3]),    # x-min
            ("right", [1, 2, 6, 5])    # x-max
        ]
        
        # Collect all faces with their vertex coordinates
        face_list = []
        
        for block_idx, block in enumerate(self.mesh_data.hex_blocks):
            vertices = block.get('vertices', [])
            point_refs = block.get('point_refs', [])
            
            if len(vertices) != 8:
                continue
            
            for face_name, face_indices in face_definitions:
                # Get vertex coordinates for this face
                face_verts = [vertices[i] for i in face_indices]
                face_global_indices = [point_refs[i] for i in face_indices]
                
                # Create a unique key for this face based on vertex global indices
                # Sort to handle different winding orders
                face_key = tuple(sorted(face_global_indices))
                
                face_list.append({
                    'block_idx': block_idx,
                    'face_name': face_name,
                    'vertices': face_verts,
                    'global_indices': face_global_indices,
                    'face_key': face_key,
                    'face_id': len(face_list)
                })
        
        # Determine face visibility
        # A face is internal if it appears exactly twice (shared between two blocks)
        face_key_counts = {}
        for face in face_list:
            key = face['face_key']
            face_key_counts[key] = face_key_counts.get(key, 0) + 1
        
        # Build final face list with visibility
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
    
    def _rotate_point(self, point):
        """Apply rotation to a 3D point"""
        x, y, z = point
        
        # Rotate around X axis
        rad_x = math.radians(self.rotation_x)
        cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
        
        # Rotate around Y axis
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
        """Draw all visible faces"""
        self.canvas.delete("all")
        
        # Rebuild faces if needed
        if self._face_cache is None:
            self._build_faces()
            self._face_cache = True
        
        if not self.all_faces:
            self._draw_no_data_message()
            return
        
        # Filter visible faces and calculate depth
        visible_faces = []
        for face in self.all_faces:
            if not face['is_visible']:
                continue
            
            # Project all vertices
            projected = []
            for vert in face['vertices']:
                sx, sy, sz = self._project(vert)
                projected.append((sx, sy, sz))
            
            # Calculate average depth for painter's algorithm
            avg_depth = sum(p[2] for p in projected) / len(projected)
            
            visible_faces.append({
                **face,
                'projected': projected,
                'avg_depth': avg_depth
            })
        
        # Sort by depth (back to front)
        visible_faces.sort(key=lambda f: f['avg_depth'], reverse=True)
        
        # Draw faces
        for face in visible_faces:
            face_id = face['face_id']
            projected = face['projected']
            
            # Create polygon points
            points = []
            for p in projected:
                points.extend([p[0], p[1]])
            
            # Determine color based on selection state
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
            
            # Draw the face
            poly_id = self.canvas.create_polygon(
                points,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                stipple='gray50',
                tags=f"face_{face_id}"
            )
            
            # Store face ID for click detection
            self.canvas.tag_bind(f"face_{face_id}", "<Button-1>", 
                                lambda e, fid=face_id: self._on_face_click(fid))
            self.canvas.tag_bind(f"face_{face_id}", "<Enter>", 
                                lambda e, fid=face_id: self._on_face_enter(fid))
            self.canvas.tag_bind(f"face_{face_id}", "<Leave>", 
                                lambda e: self._on_face_leave())
        
        # Draw wireframe overlay for block edges
        self._draw_wireframe()
        
        # Draw axes
        self._draw_axes()
    
    def _draw_wireframe(self):
        """Draw wireframe edges of blocks"""
        if not hasattr(self.mesh_data, 'hex_blocks'):
            return
        
        edges = [
            (0,1), (1,2), (2,3), (3,0),  # Bottom face
            (4,5), (5,6), (6,7), (7,4),  # Top face
            (0,4), (1,5), (2,6), (3,7)   # Vertical edges
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
                
                # Only draw if at least one point is in front
                if sz1 > -1000 or sz2 > -1000:
                    self.canvas.create_line(
                        sx1, sy1, sx2, sy2,
                        fill=self.colors['face_outline'],
                        width=1
                    )
    
    def _draw_axes(self):
        """Draw coordinate axes"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        center_x = 50
        center_y = h - 50
        length = 30
        
        x_vec = self._rotate_point([length, 0, 0])
        y_vec = self._rotate_point([0, length, 0])
        z_vec = self._rotate_point([0, 0, length])
        
        # X axis - Red
        self.canvas.create_line(center_x, center_y, 
                               center_x + x_vec[0], center_y - x_vec[1],
                               fill=self.colors['x_axis'], width=3, arrow=tk.LAST)
        # Y axis - Green
        self.canvas.create_line(center_x, center_y, 
                               center_x + y_vec[0], center_y - y_vec[1],
                               fill=self.colors['y_axis'], width=3, arrow=tk.LAST)
        # Z axis - Blue
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
    
    def _on_face_click(self, face_id):
        """Handle face click"""
        if face_id in self.selected_faces:
            self.selected_faces.remove(face_id)
        else:
            self.selected_faces.add(face_id)
        self.draw()
        self._notify_selection_change()
    
    def _on_face_enter(self, face_id):
        """Handle mouse enter on face"""
        self.hovered_face = face_id
        self.draw()
    
    def _on_face_leave(self):
        """Handle mouse leave on face"""
        self.hovered_face = None
        self.draw()
    
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
        self._face_cache = None
        self.all_faces = []
        self.selected_faces.clear()


def create_hex_renderer(canvas, mesh_data):
    """Factory function to create a HexBlockRenderer"""
    return HexBlockRenderer(canvas, mesh_data)