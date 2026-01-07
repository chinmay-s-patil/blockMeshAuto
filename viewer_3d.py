"""
3D visualization with rotation, zoom, and pan
Supports different sketch planes with correct axis orientation
"""
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class Viewer3D:
    def __init__(self, figure, mesh_data):
        self.fig = figure
        self.mesh_data = mesh_data
        self.ax = None
        self.selected_faces = set()
        self.face_patches = {}  # face_idx -> (name, type)
        self.pickable_faces = []
        
        self._init_3d_axis()
        
    def _init_3d_axis(self):
        """Initialize 3D axis with correct labels based on sketch plane"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self._set_axis_labels()
        
    def _set_axis_labels(self):
        """Set axis labels based on sketch plane"""
        plane = self.mesh_data.sketch_plane
        
        if plane == "XY":
            # Sketch on XY, extrude in Z
            # 3D view: X(horizontal) - Z(depth/back-front) - Y(vertical)
            self.ax.set_xlabel('X (horizontal)')
            self.ax.set_ylabel('Z (depth)')
            self.ax.set_zlabel('Y (vertical)')
        elif plane == "YZ":
            # Sketch on YZ, extrude in X
            # 3D view: Y(horizontal) - X(depth/back-front) - Z(vertical)
            self.ax.set_xlabel('Y (horizontal)')
            self.ax.set_ylabel('X (depth)')
            self.ax.set_zlabel('Z (vertical)')
        elif plane == "ZX":
            # Sketch on ZX, extrude in Y
            # 3D view: Z(horizontal) - Y(depth/back-front) - X(vertical)
            self.ax.set_xlabel('Z (horizontal)')
            self.ax.set_ylabel('Y (depth)')
            self.ax.set_zlabel('X (vertical)')
        
    def update_view(self):
        """Update the 3D visualization"""
        self.ax.clear()
        self._set_axis_labels()
        
        # Get all points with their 3D coordinates
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            for point_2d in self.mesh_data.points[layer]:
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                all_points.append(coords_3d)
        
        if not all_points:
            self.ax.text(0, 0, 0, "No points to display\nAdd points in Tab 2", 
                        ha='center', va='center', fontsize=12)
            return
        
        # Plot all points
        xs, ys, zs = zip(*all_points)
        self.ax.scatter(xs, ys, zs, c='red', marker='o', s=50, alpha=0.8)
        
        # Plot connections within each layer (horizontal edges)
        point_idx = 0
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            points_2d = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    
                    self.ax.plot([p1_3d[0], p2_3d[0]], 
                               [p1_3d[1], p2_3d[1]], 
                               [p1_3d[2], p2_3d[2]], 
                               'b-', linewidth=2, alpha=0.6)
        
        # Plot inter-layer connections (vertical edges)
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                p1_3d = self.mesh_data.get_3d_coords(layer1, self.mesh_data.points[layer1][idx1])
                p2_3d = self.mesh_data.get_3d_coords(layer2, self.mesh_data.points[layer2][idx2])
                
                self.ax.plot([p1_3d[0], p2_3d[0]], 
                           [p1_3d[1], p2_3d[1]], 
                           [p1_3d[2], p2_3d[2]], 
                           'g--', linewidth=2, alpha=0.7)
        
        # Auto-connect corresponding points between adjacent layers (if same number of points)
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            # Connect corresponding points if same count
            if len(points1) == len(points2):
                for j in range(len(points1)):
                    p1_3d = self.mesh_data.get_3d_coords(layer1, points1[j])
                    p2_3d = self.mesh_data.get_3d_coords(layer2, points2[j])
                    
                    self.ax.plot([p1_3d[0], p2_3d[0]], 
                               [p1_3d[1], p2_3d[1]], 
                               [p1_3d[2], p2_3d[2]], 
                               'gray', linewidth=1, alpha=0.3, linestyle=':')
        
        # Draw faces (quads) for patch selection
        self._draw_faces()
        
        # Set axis limits with some margin
        if xs and ys and zs:
            margin = 2
            x_range = max(xs) - min(xs)
            y_range = max(ys) - min(ys)
            z_range = max(zs) - min(zs)
            
            # Ensure minimum range
            x_range = max(x_range, 2)
            y_range = max(y_range, 2)
            z_range = max(z_range, 2)
            
            self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
            self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
            self.ax.set_zlim(min(zs) - margin, max(zs) + margin)
            
            # Equal aspect ratio
            max_range = max(x_range, y_range, z_range)
            mid_x = (max(xs) + min(xs)) / 2
            mid_y = (max(ys) + min(ys)) / 2
            mid_z = (max(zs) + min(zs)) / 2
            
            self.ax.set_xlim(mid_x - max_range/2 - margin, mid_x + max_range/2 + margin)
            self.ax.set_ylim(mid_y - max_range/2 - margin, mid_y + max_range/2 + margin)
            self.ax.set_zlim(mid_z - max_range/2 - margin, mid_z + max_range/2 + margin)
    
    def _draw_faces(self):
        """Draw mesh faces as polygons"""
        self.pickable_faces = []
        
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        # Horizontal faces within each layer
        for layer in layers_sorted:
            points_2d = self.mesh_data.points[layer]
            conns = self.mesh_data.connections[layer]
            
            # Try to detect quad faces from connections
            if len(points_2d) >= 4 and len(conns) >= 4:
                # Simple quad detection: assume first 4 points form a quad
                # In a real implementation, you'd detect cycles in the connection graph
                if len(points_2d) >= 4:
                    # Try different quad combinations
                    quads_to_try = [
                        [0, 1, 2, 3],
                        [0, 1, 3, 2],  # Different winding
                    ]
                    
                    for quad_indices in quads_to_try:
                        if all(idx < len(points_2d) for idx in quad_indices):
                            face_verts = [
                                self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[0]]),
                                self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[1]]),
                                self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[2]]),
                                self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[3]])
                            ]
                            
                            self.pickable_faces.append(face_verts)
                            face_idx = len(self.pickable_faces) - 1
                            
                            color = 'cyan' if face_idx in self.selected_faces else 'lightblue'
                            alpha = 0.7 if face_idx in self.selected_faces else 0.2
                            
                            poly = Poly3DCollection([face_verts], alpha=alpha, 
                                                   facecolor=color, edgecolor='black', linewidth=1)
                            self.ax.add_collection3d(poly)
                            break  # Only add one quad per layer for now
        
        # Vertical faces between layers
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            # Create vertical quads between corresponding edges
            num_points = min(len(points1), len(points2))
            if num_points >= 2:
                for j in range(num_points - 1):
                    # Check if there's a connection between j and j+1 in layer1
                    conn_exists = (j, j+1) in self.mesh_data.connections[layer1] or \
                                 (j+1, j) in self.mesh_data.connections[layer1]
                    
                    if conn_exists or len(points1) == len(points2):
                        face_verts = [
                            self.mesh_data.get_3d_coords(layer1, points1[j]),
                            self.mesh_data.get_3d_coords(layer1, points1[j+1]),
                            self.mesh_data.get_3d_coords(layer2, points2[j+1]),
                            self.mesh_data.get_3d_coords(layer2, points2[j])
                        ]
                        
                        self.pickable_faces.append(face_verts)
                        face_idx = len(self.pickable_faces) - 1
                        
                        color = 'yellow' if face_idx in self.selected_faces else 'lightgreen'
                        alpha = 0.7 if face_idx in self.selected_faces else 0.2
                        
                        poly = Poly3DCollection([face_verts], alpha=alpha,
                                               facecolor=color, edgecolor='black', linewidth=1)
                        self.ax.add_collection3d(poly)
                
                # Close the loop if it's a closed shape
                if num_points >= 3:
                    conn_exists = (num_points-1, 0) in self.mesh_data.connections[layer1] or \
                                 (0, num_points-1) in self.mesh_data.connections[layer1]
                    
                    if conn_exists or len(points1) == len(points2):
                        face_verts = [
                            self.mesh_data.get_3d_coords(layer1, points1[num_points-1]),
                            self.mesh_data.get_3d_coords(layer1, points1[0]),
                            self.mesh_data.get_3d_coords(layer2, points2[0]),
                            self.mesh_data.get_3d_coords(layer2, points2[num_points-1])
                        ]
                        
                        self.pickable_faces.append(face_verts)
                        face_idx = len(self.pickable_faces) - 1
                        
                        color = 'yellow' if face_idx in self.selected_faces else 'lightgreen'
                        alpha = 0.7 if face_idx in self.selected_faces else 0.2
                        
                        poly = Poly3DCollection([face_verts], alpha=alpha,
                                               facecolor=color, edgecolor='black', linewidth=1)
                        self.ax.add_collection3d(poly)
    
    def pick_face(self, x, y):
        """Pick a face based on mouse click (simplified)"""
        # Simplified face picking - cycles through faces
        if self.pickable_faces:
            # Get next unselected face, or toggle first selected
            for i in range(len(self.pickable_faces)):
                if i not in self.selected_faces:
                    self.selected_faces.add(i)
                    return i
            
            # All selected, so deselect first
            if self.selected_faces:
                first = min(self.selected_faces)
                self.selected_faces.remove(first)
                return first
        return None
    
    def clear_selection(self):
        """Clear all selected faces"""
        self.selected_faces.clear()
    
    def get_selected_faces(self):
        """Get list of selected face indices"""
        return list(self.selected_faces)
    
    def assign_patch_to_selected(self, patch_name, patch_type):
        """Assign patch info to selected faces"""
        for face_idx in self.selected_faces:
            self.face_patches[face_idx] = (patch_name, patch_type)