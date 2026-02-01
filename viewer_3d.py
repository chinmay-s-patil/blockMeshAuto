"""
3D visualization using Plotly for better interactivity
Supports different sketch planes with correct axis orientation
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class Viewer3D:
    def __init__(self, parent_widget, mesh_data):
        self.parent = parent_widget
        self.mesh_data = mesh_data
        self.selected_faces = set()
        self.face_patches = {}  # face_idx -> (name, type)
        self.pickable_faces = []
        self.fig = None
        
    def _get_axis_labels(self):
        """Get axis labels based on sketch plane"""
        plane = self.mesh_data.sketch_plane
        
        if plane == "XY":
            return {
                'x': 'X (horizontal)',
                'y': 'Z (depth)',
                'z': 'Y (vertical)'
            }
        elif plane == "YZ":
            return {
                'x': 'Y (horizontal)',
                'y': 'X (depth)',
                'z': 'Z (vertical)'
            }
        elif plane == "ZX":
            return {
                'x': 'Z (horizontal)',
                'y': 'Y (depth)',
                'z': 'X (vertical)'
            }
        return {'x': 'X', 'y': 'Y', 'z': 'Z'}
        
    def update_view(self):
        """Update the 3D visualization using Plotly"""
        # Get all points with their 3D coordinates
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            for point_2d in self.mesh_data.points[layer]:
                coords_3d = self.mesh_data.get_3d_coords(layer, point_2d)
                all_points.append(coords_3d)
        
        if not all_points:
            # Create empty figure with message
            self.fig = go.Figure()
            self.fig.add_annotation(
                text="No points to display<br>Add points in Tab 2",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return self.fig
        
        # Create figure
        self.fig = go.Figure()
        
        # Plot all points
        xs, ys, zs = zip(*all_points)
        self.fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(size=6, color='red', opacity=0.8),
            name='Points',
            hoverinfo='text',
            text=[f'Point {i}' for i in range(len(xs))]
        ))
        
        # Plot connections within each layer (horizontal edges)
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            points_2d = self.mesh_data.points[layer]
            
            for conn in self.mesh_data.connections[layer]:
                if conn[0] < len(points_2d) and conn[1] < len(points_2d):
                    p1_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[0]])
                    p2_3d = self.mesh_data.get_3d_coords(layer, points_2d[conn[1]])
                    
                    self.fig.add_trace(go.Scatter3d(
                        x=[p1_3d[0], p2_3d[0]],
                        y=[p1_3d[1], p2_3d[1]],
                        z=[p1_3d[2], p2_3d[2]],
                        mode='lines',
                        line=dict(color='blue', width=4),
                        name=f'{layer} conn',
                        showlegend=False,
                        hoverinfo='text',
                        text=f'{layer}: {conn[0]}-{conn[1]}'
                    ))
        
        # Plot inter-layer connections (vertical edges)
        for layer1, idx1, layer2, idx2 in self.mesh_data.inter_layer_connections:
            if idx1 < len(self.mesh_data.points[layer1]) and idx2 < len(self.mesh_data.points[layer2]):
                p1_3d = self.mesh_data.get_3d_coords(layer1, self.mesh_data.points[layer1][idx1])
                p2_3d = self.mesh_data.get_3d_coords(layer2, self.mesh_data.points[layer2][idx2])
                
                self.fig.add_trace(go.Scatter3d(
                    x=[p1_3d[0], p2_3d[0]],
                    y=[p1_3d[1], p2_3d[1]],
                    z=[p1_3d[2], p2_3d[2]],
                    mode='lines',
                    line=dict(color='green', width=4, dash='dash'),
                    name='Inter-layer',
                    showlegend=False,
                    hoverinfo='text',
                    text=f'{layer1}[{idx1}] ↔ {layer2}[{idx2}]'
                ))
        
        # Auto-connect corresponding points between adjacent layers
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            if len(points1) == len(points2):
                for j in range(len(points1)):
                    # Check if already explicit
                    already_explicit = any(
                        (l1 == layer1 and i1 == j and l2 == layer2 and i2 == j) or
                        (l1 == layer2 and i1 == j and l2 == layer1 and i2 == j)
                        for l1, i1, l2, i2 in self.mesh_data.inter_layer_connections
                    )
                    
                    if not already_explicit:
                        p1_3d = self.mesh_data.get_3d_coords(layer1, points1[j])
                        p2_3d = self.mesh_data.get_3d_coords(layer2, points2[j])
                        
                        self.fig.add_trace(go.Scatter3d(
                            x=[p1_3d[0], p2_3d[0]],
                            y=[p1_3d[1], p2_3d[1]],
                            z=[p1_3d[2], p2_3d[2]],
                            mode='lines',
                            line=dict(color='gray', width=2, dash='dot'),
                            name='Auto-connect',
                            showlegend=False,
                            opacity=0.3,
                            hoverinfo='text',
                            text=f'{layer1}[{j}] → {layer2}[{j}] (auto)'
                        ))
        
        # Draw faces for patch selection
        self._draw_faces()
        
        # Get axis labels
        labels = self._get_axis_labels()
        
        # Update layout
        self.fig.update_layout(
            scene=dict(
                xaxis_title=labels['x'],
                yaxis_title=labels['y'],
                zaxis_title=labels['z'],
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode='closest',
            showlegend=True
        )
        
        return self.fig
    
    def _draw_faces(self):
        """Draw mesh faces as polygons"""
        self.pickable_faces = []
        
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        # Horizontal faces within each layer
        for layer in layers_sorted:
            points_2d = self.mesh_data.points[layer]
            
            if len(points_2d) >= 4:
                quad_indices = [0, 1, 2, 3]
                
                if all(idx < len(points_2d) for idx in quad_indices):
                    face_verts = [
                        self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[0]]),
                        self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[1]]),
                        self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[2]]),
                        self.mesh_data.get_3d_coords(layer, points_2d[quad_indices[3]])
                    ]
                    
                    self.pickable_faces.append(face_verts)
                    face_idx = len(self.pickable_faces) - 1
                    
                    xs = [v[0] for v in face_verts] + [face_verts[0][0]]
                    ys = [v[1] for v in face_verts] + [face_verts[0][1]]
                    zs = [v[2] for v in face_verts] + [face_verts[0][2]]
                    
                    color = 'cyan' if face_idx in self.selected_faces else 'lightblue'
                    opacity = 0.7 if face_idx in self.selected_faces else 0.2
                    
                    self.fig.add_trace(go.Mesh3d(
                        x=[v[0] for v in face_verts],
                        y=[v[1] for v in face_verts],
                        z=[v[2] for v in face_verts],
                        i=[0, 0],
                        j=[1, 2],
                        k=[2, 3],
                        color=color,
                        opacity=opacity,
                        name=f'Face {face_idx}',
                        showlegend=False,
                        hoverinfo='text',
                        text=f'Face {face_idx}: {layer}'
                    ))
        
        # Vertical faces between layers
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            points1 = self.mesh_data.points[layer1]
            points2 = self.mesh_data.points[layer2]
            
            num_points = min(len(points1), len(points2))
            if num_points >= 2:
                for j in range(num_points):
                    next_j = (j + 1) % num_points
                    
                    conn_exists = (j, next_j) in self.mesh_data.connections[layer1] or \
                                 (next_j, j) in self.mesh_data.connections[layer1]
                    
                    if conn_exists or len(points1) == len(points2):
                        face_verts = [
                            self.mesh_data.get_3d_coords(layer1, points1[j]),
                            self.mesh_data.get_3d_coords(layer1, points1[next_j]),
                            self.mesh_data.get_3d_coords(layer2, points2[next_j]),
                            self.mesh_data.get_3d_coords(layer2, points2[j])
                        ]
                        
                        self.pickable_faces.append(face_verts)
                        face_idx = len(self.pickable_faces) - 1
                        
                        color = 'yellow' if face_idx in self.selected_faces else 'lightgreen'
                        opacity = 0.7 if face_idx in self.selected_faces else 0.2
                        
                        self.fig.add_trace(go.Mesh3d(
                            x=[v[0] for v in face_verts],
                            y=[v[1] for v in face_verts],
                            z=[v[2] for v in face_verts],
                            i=[0, 0],
                            j=[1, 2],
                            k=[2, 3],
                            color=color,
                            opacity=opacity,
                            name=f'Face {face_idx}',
                            showlegend=False,
                            hoverinfo='text',
                            text=f'Face {face_idx}: {layer1}-{layer2} [{j}-{next_j}]'
                        ))
    
    def pick_face(self, face_idx):
        """Toggle face selection"""
        if face_idx in self.selected_faces:
            self.selected_faces.remove(face_idx)
        else:
            self.selected_faces.add(face_idx)
        return face_idx
    
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