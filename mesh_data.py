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
        
        # Project settings
        self.sketch_plane = "XY"  # XY, YZ, or ZX
        self.project_name = "Untitled Project"
        self.project_description = ""
        
        # Unit system
        self.unit_system = "m"  # m, cm, mm, or scientific
        self.unit_sci_exponent = "0"  # For scientific notation: 10^n
        
    def get_scale_value(self):
        """Get the numerical scale value for blockMeshDict"""
        if self.unit_system == "m":
            return 1.0
        elif self.unit_system == "cm":
            return 0.01
        elif self.unit_system == "mm":
            return 0.001
        elif self.unit_system == "scientific":
            try:
                exp = float(self.unit_sci_exponent)
                return 10**exp
            except:
                return 1.0
        else:
            return 1.0
    
    def get_safe_project_name(self):
        """Get a filesystem-safe version of the project name"""
        import re
        # Remove/replace invalid filename characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', self.project_name)
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip('. ')
        # If empty after cleaning, use default
        if not safe_name:
            safe_name = "untitled_project"
        return safe_name
        
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
    
    def get_global_point_index(self, layer, local_idx):
        """Convert layer-local point index to global sequential index"""
        global_idx = 0
        layers_sorted = sorted(self.layers.keys(), key=lambda l: self.layers[l])
        
        for lyr in layers_sorted:
            if lyr == layer:
                return global_idx + local_idx
            global_idx += len(self.points[lyr])
        
        return -1  # Not found
    
    def get_layer_from_global_index(self, global_idx):
        """Get layer and local index from global sequential index"""
        current_idx = 0
        layers_sorted = sorted(self.layers.keys(), key=lambda l: self.layers[l])
        
        for layer in layers_sorted:
            num_points = len(self.points[layer])
            if global_idx < current_idx + num_points:
                local_idx = global_idx - current_idx
                return layer, local_idx
            current_idx += num_points
        
        return None, -1
    
    def get_3d_coords(self, layer, point_2d):
        """Convert 2D sketch coords to 3D based on sketch plane"""
        x, y = point_2d
        z = self.layers[layer]
        
        if self.sketch_plane == "XY":
            # X-horizontal, Y-vertical, Z-depth
            return (x, z, y)  # Returns (X, Z, Y) for matplotlib
        elif self.sketch_plane == "YZ":
            # Y-horizontal, Z-vertical, X-depth
            return (z, x, y)  # Returns (X=depth, Z=Y, Y=Z)
        elif self.sketch_plane == "ZX":
            # Z-horizontal, X-vertical, Y-depth
            return (y, z, x)  # Returns (X=Z, Z=X, Y=depth)
        
        return (x, z, y)  # Default XY
    
    def get_3d_coords_from_global(self, global_idx):
        """Get 3D coordinates from global point index"""
        layer, local_idx = self.get_layer_from_global_index(global_idx)
        if layer is None:
            return None
        
        point_2d = self.points[layer][local_idx]
        return self.get_3d_coords(layer, point_2d)
            
    def get_all_3d_points(self):
        """Get all points with their 3D coordinates in sequential order"""
        points_3d = []
        point_map = {}  # (layer, local_idx) -> global_idx
        
        global_idx = 0
        layers_sorted = sorted(self.layers.keys(), key=lambda l: self.layers[l])
        
        for layer in layers_sorted:
            for local_idx, point_2d in enumerate(self.points[layer]):
                coords_3d = self.get_3d_coords(layer, point_2d)
                points_3d.append(coords_3d)
                point_map[(layer, local_idx)] = global_idx
                global_idx += 1
                
        return points_3d, point_map
    
    def get_total_points(self):
        """Get total number of points across all layers"""
        return sum(len(pts) for pts in self.points.values())
    
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
        """Clear all geometry while keeping project settings"""
        for layer in self.points:
            self.points[layer] = []
            self.connections[layer] = []
        self.inter_layer_connections = []
        self.patches = []
    
    def to_dict(self):
        """Convert mesh data to dictionary for JSON serialization"""
        return {
            "layers": self.layers,
            "current_layer": self.current_layer,
            "points": self.points,
            "connections": self.connections,
            "inter_layer_connections": self.inter_layer_connections,
            "patches": self.patches,
            "sketch_plane": self.sketch_plane,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "unit_system": self.unit_system,
            "unit_sci_exponent": self.unit_sci_exponent
        }
    
    def from_dict(self, data):
        """Load mesh data from dictionary"""
        self.layers = data.get("layers", {"Layer 0": 0.0})
        self.current_layer = data.get("current_layer", "Layer 0")
        self.points = data.get("points", {"Layer 0": []})
        self.connections = data.get("connections", {"Layer 0": []})
        self.inter_layer_connections = data.get("inter_layer_connections", [])
        self.patches = data.get("patches", [])
        self.sketch_plane = data.get("sketch_plane", "XY")
        self.project_name = data.get("project_name", "Untitled Project")
        self.project_description = data.get("project_description", "")
        self.unit_system = data.get("unit_system", "m")
        self.unit_sci_exponent = data.get("unit_sci_exponent", "0")