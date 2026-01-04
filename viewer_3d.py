"""
3D visualization with rotation, zoom, and pan
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
        """Initialize 3D axis"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
    def update_view(self):
        """Update the 3D visualization"""
        self.ax.clear()
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        points_3d, point_map = self.mesh_data.get_all_3d_points()
        
        if not points_3d:
            return
        
        # Plot points
        xs, ys, zs = zip(*points_3d)
        self.ax.scatter(xs, ys, zs, c='red', marker='o', s=50)
        
        # Plot connections within each layer
        for layer in self.mesh_data.layers:
            z = self.mesh_data.layers[layer]
            for conn in self.mesh_data.connections[layer]:
                p1 = self.mesh_data.points[layer][conn[0]]
                p2 = self.mesh_data.points[layer][conn[1]]
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [z, z], 'b-', linewidth=1)
        
        # Plot connections between layers (vertical)
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            # Connect corresponding points (by index)
            num_points = min(len(self.mesh_data.points[layer1]), 
                           len(self.mesh_data.points[layer2]))
            for j in range(num_points):
                p1 = self.mesh_data.points[layer1][j]
                p2 = self.mesh_data.points[layer2][j]
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [z1, z2], 'g--', linewidth=1, alpha=0.5)
        
        # Draw faces (quads)
        self._draw_faces(point_map)
        
        # Set axis limits
        if xs and ys and zs:
            margin = 2
            self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
            self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
            self.ax.set_zlim(min(zs) - margin, max(zs) + margin)
    
    def _draw_faces(self, point_map):
        """Draw mesh faces as polygons"""
        self.pickable_faces = []
        
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        # Horizontal faces (within layers)
        for layer in layers_sorted:
            z = self.mesh_data.layers[layer]
            points = self.mesh_data.points[layer]
            
            # Try to find quad faces from connections
            # Simplified: if we have 4 points forming a cycle
            if len(points) >= 4 and len(self.mesh_data.connections[layer]) >= 4:
                # Example quad (0,1,2,3)
                face_verts = [
                    (points[0][0], points[0][1], z),
                    (points[1][0], points[1][1], z),
                    (points[2][0], points[2][1], z),
                    (points[3][0], points[3][1], z)
                ]
                self.pickable_faces.append(face_verts)
                
                # Draw face
                face_idx = len(self.pickable_faces) - 1
                color = 'cyan' if face_idx in self.selected_faces else 'lightblue'
                alpha = 0.7 if face_idx in self.selected_faces else 0.3
                
                poly = Poly3DCollection([face_verts], alpha=alpha, 
                                       facecolor=color, edgecolor='black', linewidth=1)
                self.ax.add_collection3d(poly)
        
        # Vertical faces (between layers)
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            z1 = self.mesh_data.layers[layer1]
            z2 = self.mesh_data.layers[layer2]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            # Create vertical quads between corresponding edges
            num_points = min(len(points1), len(points2))
            for j in range(num_points - 1):
                face_verts = [
                    (points1[j][0], points1[j][1], z1),
                    (points1[j+1][0], points1[j+1][1], z1),
                    (points2[j+1][0], points2[j+1][1], z2),
                    (points2[j][0], points2[j][1], z2)
                ]
                self.pickable_faces.append(face_verts)
                
                face_idx = len(self.pickable_faces) - 1
                color = 'yellow' if face_idx in self.selected_faces else 'lightgreen'
                alpha = 0.7 if face_idx in self.selected_faces else 0.3
                
                poly = Poly3DCollection([face_verts], alpha=alpha,
                                       facecolor=color, edgecolor='black', linewidth=1)
                self.ax.add_collection3d(poly)
    
    def pick_face(self, x, y):
        """Pick a face based on mouse click (simplified)"""
        # This is a simplified version - proper picking requires ray casting
        # For now, just toggle selection of faces in order
        if self.pickable_faces:
            # Cycle through faces on click
            next_face = len(self.selected_faces) % len(self.pickable_faces)
            if next_face in self.selected_faces:
                self.selected_faces.remove(next_face)
            else:
                self.selected_faces.add(next_face)
            return next_face
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