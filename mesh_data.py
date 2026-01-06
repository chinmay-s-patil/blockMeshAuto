"""
Data structures for mesh builder
"""

class MeshData:
    def __init__(self):
        self.layers = {"Layer 0": 0.0}
        self.current_layer = "Layer 0"
        self.points = {"Layer 0": []}
        self.connections = {"Layer 0": []}
        self.inter_layer_connections = []  # [(layer1, idx1, layer2, idx2)]
        self.patches = []  # [(name, patch_type, face_indices)]
        
    def add_layer(self, name, z_value):
        self.layers[name] = z_value
        self.points[name] = []
        self.connections[name] = []
        
    def remove_layer(self, name):
        if name in self.layers:
            del self.layers[name]
            del self.points[name]
            del self.connections[name]
            
    def add_point(self, layer, x, y):
        self.points[layer].append((x, y))
        return len(self.points[layer]) - 1
    
    def remove_point(self, layer, idx):
        if 0 <= idx < len(self.points[layer]):
            # Remove point
            self.points[layer].pop(idx)
            # Update connections
            new_conns = []
            for conn in self.connections[layer]:
                c1, c2 = conn
                if c1 == idx or c2 == idx:
                    continue  # Skip connections involving deleted point
                # Adjust indices
                new_c1 = c1 if c1 < idx else c1 - 1
                new_c2 = c2 if c2 < idx else c2 - 1
                new_conns.append((new_c1, new_c2))
            self.connections[layer] = new_conns
            
    def add_connection(self, layer, idx1, idx2):
        conn = tuple(sorted([idx1, idx2]))
        if conn not in self.connections[layer]:
            self.connections[layer].append(conn)
    
    def add_inter_layer_connection(self, layer1, idx1, layer2, idx2):
        """Add a connection between points on different layers"""
        conn = (layer1, idx1, layer2, idx2)
        if conn not in self.inter_layer_connections:
            self.inter_layer_connections.append(conn)
            
    def get_all_3d_points(self):
        """Get all points with their 3D coordinates"""
        points_3d = []
        point_map = {}  # (layer, idx) -> global_idx
        
        global_idx = 0
        for layer in sorted(self.layers.keys(), key=lambda l: self.layers[l]):
            z = self.layers[layer]
            for local_idx, (x, y) in enumerate(self.points[layer]):
                points_3d.append((x, y, z))
                point_map[(layer, local_idx)] = global_idx
                global_idx += 1
                
        return points_3d, point_map
    
    def get_faces(self):
        """Get all quadrilateral faces for patch selection"""
        faces = []
        layers_sorted = sorted(self.layers.keys(), key=lambda l: self.layers[l])
        
        # Faces within each layer (horizontal)
        for layer in layers_sorted:
            conns = self.connections[layer]
            # Simple quad detection - look for 4-point cycles
            # This is simplified; real implementation needs proper face detection
            
        # Faces between layers (vertical)
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            # Match points between layers based on connections
            
        return faces
    
    def add_patch(self, name, patch_type, face_indices):
        self.patches.append((name, patch_type, face_indices))
        
    def clear_all(self):
        for layer in self.points:
            self.points[layer] = []
            self.connections[layer] = []
        self.patches = []
    
    def to_dict(self):
        """Convert mesh data to dictionary for JSON serialization"""
        return {
            "layers": self.layers,
            "current_layer": self.current_layer,
            "points": self.points,
            "connections": self.connections,
            "inter_layer_connections": self.inter_layer_connections,
            "patches": self.patches
        }
    
    def from_dict(self, data):
        """Load mesh data from dictionary"""
        self.layers = data.get("layers", {"Layer 0": 0.0})
        self.current_layer = data.get("current_layer", "Layer 0")
        self.points = data.get("points", {"Layer 0": []})
        self.connections = data.get("connections", {"Layer 0": []})
        self.inter_layer_connections = data.get("inter_layer_connections", [])
        self.patches = data.get("patches", [])