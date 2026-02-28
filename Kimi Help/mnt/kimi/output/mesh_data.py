"""
Data structures for mesh builder - UPDATED to match new_data_structure.json
All geometry references global points by ID. Points store actual coordinates.
Specs section contains project settings.
"""

class MeshData:
    def __init__(self):
        # Global point storage - single source of truth for coordinates
        # Structure: {"Point num: int": {"X": float, "Y": float, "Z": float}}
        self.points = {}
        self.next_point_id = 1  # Auto-increment for new points
        self.available_point_ids = []  # Pool of recycled IDs from deleted points
        
        # Layers reference points by ID
        # Structure: {"Layer Name: int": {"Points (Ref)": [point_id, ...]}}
        self.layers = {}
        self.current_layer = None
        
        # Connections reference point IDs
        # Structure: {"Connection num: int": {"Point 1": id, "Point 2": id}}
        self.connections = {}
        self.next_connection_id = 1
        
        # Edges for curved geometry
        # Structure: {"Edge num: int": {"type": str, "Points": [id, ...], "Input Points": [(x,y,z), ...]}}
        self.edges = {}
        self.next_edge_id = 1
        
        # Hex blocks reference 8 point IDs (or fewer for wedges/etc)
        # Structure: {"Hex num: int": {"Points": [id0, id1, ..., id7]}}
        self.hex_blocks = {}
        self.next_block_id = 1
        
        # Patches reference point IDs and have a type
        # Structure: {"Patch name: str": {"type": str, "Points": [id, ...], "Normal": int}}
        self.patches = {}
        
        # Specs - Project settings
        # Structure: {"sketch_plane": str, "project_name": str, "project_description": str, 
        #             "unit_system": str, "unit_sci_exponent": str}
        self.sketch_plane = "XY"  # XY, YZ, or ZX
        self.project_name = "Untitled Project"
        self.project_description = ""
        self.unit_system = "m"  # m, cm, mm, or scientific
        self.unit_sci_exponent = "0"  # For scientific notation: 10^n
        
        # Initialize default layer
        self._init_default()
    
    def _init_default(self):
        """Initialize with a default layer"""
        self.add_layer("Layer 0", 0.0)
        self.current_layer = "Layer 0"
    
    # =========================================================================
    # POINT OPERATIONS
    # =========================================================================
    
    def add_point(self, x, y, z=None, layer=None):
        """
        Add a new point to global storage and optionally to a layer.
        Returns the new point_id.
        Uses recycled IDs if available, otherwise creates new ID.
        """
        if z is None:
            # Get Z from layer if not specified
            if layer is None:
                layer = self.current_layer
            z = self.layers.get(layer, {}).get("z", 0.0)
        
        # Use recycled ID if available, otherwise use next_point_id
        if self.available_point_ids:
            point_id = self.available_point_ids.pop(0)  # Get smallest available ID
        else:
            point_id = self.next_point_id
            self.next_point_id += 1
        
        self.points[str(point_id)] = {
            "X": float(x),
            "Y": float(y),
            "Z": float(z)
        }
        
        # Add to layer if specified
        if layer is not None:
            if layer in self.layers:
                if point_id not in self.layers[layer]["point_refs"]:
                    self.layers[layer]["point_refs"].append(point_id)
        
        return point_id
    
    def remove_point(self, point_id):
        """
        Remove a point from global storage and all references.
        Returns True if removed, False if not found.
        Adds the ID to available_point_ids for recycling.
        """
        point_id_str = str(point_id)
        if point_id_str not in self.points:
            return False
        
        # Remove from all layers
        for layer_name, layer_data in self.layers.items():
            if point_id in layer_data["point_refs"]:
                layer_data["point_refs"].remove(point_id)
        
        # Remove from all connections (and delete connections involving this point)
        conns_to_delete = []
        for conn_id, conn_data in self.connections.items():
            if conn_data["point1"] == point_id or conn_data["point2"] == point_id:
                conns_to_delete.append(conn_id)
        for conn_id in conns_to_delete:
            del self.connections[conn_id]
        
        # Remove from all edges
        for edge_id, edge_data in self.edges.items():
            if point_id in edge_data["point_refs"]:
                edge_data["point_refs"].remove(point_id)
        
        # Remove from all hex blocks (and delete blocks that become invalid)
        blocks_to_delete = []
        for block_id, block_data in self.hex_blocks.items():
            if point_id in block_data["point_refs"]:
                # Remove the point ref
                block_data["point_refs"].remove(point_id)
                # Mark for deletion if less than 4 points (can't form a valid cell)
                if len(block_data["point_refs"]) < 4:
                    blocks_to_delete.append(block_id)
        for block_id in blocks_to_delete:
            del self.hex_blocks[block_id]
        
        # Remove from all patches
        for patch_name, patch_data in self.patches.items():
            if point_id in patch_data["point_refs"]:
                patch_data["point_refs"].remove(point_id)
        
        # Finally, remove the point itself
        del self.points[point_id_str]
        
        # Add ID to available pool for recycling (if not already there)
        if point_id not in self.available_point_ids:
            self.available_point_ids.append(point_id)
            self.available_point_ids.sort()  # Keep sorted for consistent behavior
        
        return True
    
    def get_point(self, point_id):
        """Get point coordinates by ID. Returns dict or None."""
        point_data = self.points.get(str(point_id))
        if point_data:
            return {
                "x": point_data["X"],
                "y": point_data["Y"],
                "z": point_data["Z"]
            }
        return None
    
    def update_point(self, point_id, x=None, y=None, z=None):
        """Update point coordinates. Only updates provided values."""
        point_id_str = str(point_id)
        if point_id_str not in self.points:
            return False
        
        if x is not None:
            self.points[point_id_str]["X"] = float(x)
        if y is not None:
            self.points[point_id_str]["Y"] = float(y)
        if z is not None:
            self.points[point_id_str]["Z"] = float(z)
        
        return True
    
    # =========================================================================
    # LAYER OPERATIONS
    # =========================================================================
    
    def add_layer(self, name, z_value):
        """Add a new layer. Z is stored here, points reference by ID."""
        self.layers[name] = {
            "z": float(z_value),
            "point_refs": []
        }
        return name
    
    def remove_layer(self, name):
        """Remove a layer. Points are NOT deleted, just dereferenced."""
        if name in self.layers:
            del self.layers[name]
            if self.current_layer == name:
                # Switch to another layer if available
                if self.layers:
                    self.current_layer = list(self.layers.keys())[0]
                else:
                    self.current_layer = None
            return True
        return False
    
    def set_layer_z(self, name, z_value):
        """Update Z value of a layer. Points keep their IDs."""
        if name in self.layers:
            self.layers[name]["z"] = float(z_value)
            # Also update Z coordinate of all points in this layer
            for point_id in self.layers[name]["point_refs"]:
                self.update_point(point_id, z=z_value)
            return True
        return False
    
    def get_layer_z(self, name):
        """Get Z value of a layer."""
        return self.layers.get(name, {}).get("z")
    
    def add_point_to_layer(self, point_id, layer_name):
        """Add an existing point reference to a layer."""
        if layer_name not in self.layers or str(point_id) not in self.points:
            return False
        
        if point_id not in self.layers[layer_name]["point_refs"]:
            self.layers[layer_name]["point_refs"].append(point_id)
            # Update point Z to match layer
            z = self.layers[layer_name]["z"]
            self.update_point(point_id, z=z)
        
        return True
    
    def remove_point_from_layer(self, point_id, layer_name):
        """Remove a point reference from a layer (doesn't delete point)."""
        if layer_name in self.layers:
            if point_id in self.layers[layer_name]["point_refs"]:
                self.layers[layer_name]["point_refs"].remove(point_id)
                return True
        return False
    
    # =========================================================================
    # CONNECTION OPERATIONS
    # =========================================================================
    
    def add_connection(self, point1_id, point2_id):
        """Add a connection between two points."""
        if str(point1_id) not in self.points or str(point2_id) not in self.points:
            return None
        
        # Ensure consistent ordering (lower ID first)
        p1, p2 = sorted([point1_id, point2_id])
        
        # Check if exists
        for conn_id, conn in self.connections.items():
            if conn["point1"] == p1 and conn["point2"] == p2:
                return conn_id  # Already exists
        
        conn_id = self.next_connection_id
        self.connections[str(conn_id)] = {
            "point1": p1,
            "point2": p2
        }
        self.next_connection_id += 1
        return conn_id
    
    def remove_connection(self, conn_id):
        """Remove a connection."""
        conn_id_str = str(conn_id)
        if conn_id_str in self.connections:
            del self.connections[conn_id_str]
            return True
        return False
    
    # =========================================================================
    # EDGE OPERATIONS
    # =========================================================================
    
    def add_edge(self, edge_type, point_refs, input_points=None):
        """
        Add an edge definition.
        edge_type: "arc", "spline", "polyLine", etc.
        point_refs: list of point IDs that define the edge
        input_points: list of (x,y,z) tuples for control points
        """
        # Validate all point refs exist
        for pid in point_refs:
            if str(pid) not in self.points:
                return None
        
        edge_id = self.next_edge_id
        self.edges[str(edge_id)] = {
            "type": edge_type,
            "point_refs": list(point_refs),
            "input_points": input_points if input_points else []
        }
        self.next_edge_id += 1
        return edge_id
    
    def remove_edge(self, edge_id):
        """Remove an edge."""
        edge_id_str = str(edge_id)
        if edge_id_str in self.edges:
            del self.edges[edge_id_str]
            return True
        return False
    
    # =========================================================================
    # HEX BLOCK OPERATIONS
    # =========================================================================
    
    def add_hex_block(self, point_refs):
        """
        Add a hex block with references to 8 points (or fewer for wedges).
        point_refs: list of 8 point IDs in OpenFOAM vertex order:
            0-3: bottom face (CCW from below)
            4-7: top face (CCW from above)
        """
        # Validate
        if len(point_refs) < 4:
            return None  # Need at least 4 points for a tet/wedge
        
        for pid in point_refs:
            if str(pid) not in self.points:
                return None
        
        block_id = self.next_block_id
        self.hex_blocks[str(block_id)] = {
            "point_refs": list(point_refs)
        }
        self.next_block_id += 1
        return block_id
    
    def remove_hex_block(self, block_id):
        """Remove a hex block."""
        block_id_str = str(block_id)
        if block_id_str in self.hex_blocks:
            del self.hex_blocks[block_id_str]
            return True
        return False
    
    def get_hex_block_vertices(self, block_id):
        """Get actual coordinates for a hex block's points."""
        block_data = self.hex_blocks.get(str(block_id))
        if not block_data:
            return None
        
        refs = block_data["point_refs"]
        vertices = []
        for pid in refs:
            pt = self.get_point(pid)
            if pt:
                vertices.append((pt["x"], pt["y"], pt["z"]))
            else:
                vertices.append(None)  # Missing point
        return vertices
    
    # =========================================================================
    # PATCH OPERATIONS
    # =========================================================================
    
    def add_patch(self, name, patch_type, point_refs, normal=1):
        """
        Add a patch with type and point references.
        point_refs: list of point IDs that form the patch faces
        normal: direction (1 or -1)
        """
        # Validate all points exist
        for pid in point_refs:
            if str(pid) not in self.points:
                return False
        
        self.patches[name] = {
            "type": patch_type,
            "point_refs": list(point_refs),
            "Normal": normal
        }
        return True
    
    def remove_patch(self, name):
        """Remove a patch."""
        if name in self.patches:
            del self.patches[name]
            return True
        return False
    
    def update_patch_type(self, name, new_type):
        """Change patch type."""
        if name in self.patches:
            self.patches[name]["type"] = new_type
            return True
        return False
    
    # =========================================================================
    # UTILITY / EXPORT
    # =========================================================================
    
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
        # FIXED: Use raw string with correct pattern to replace invalid filename characters
        # Pattern matches: < > : " / \ | ? *
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', self.project_name)
        safe_name = safe_name.strip('. ')
        if not safe_name:
            safe_name = "untitled_project"
        return safe_name
    
    def get_all_points_list(self):
        """Get points as a list ordered by ID for blockMeshDict export."""
        sorted_ids = sorted(self.points.keys(), key=lambda x: int(x))
        return [(self.points[pid]["X"], self.points[pid]["Y"], self.points[pid]["Z"]) 
                for pid in sorted_ids]
        
    def get_total_points(self):
        """Get total number of points"""
        return len(self.points)

    def get_all_3d_points(self):
        """Get all points as 3D coordinates - alias for get_all_points_list for compatibility"""
        return self.get_all_points_list(), self.get_point_index_map()


    def get_point_index_map(self):
        """Get mapping from point_id to 0-based index for export."""
        sorted_ids = sorted(self.points.keys(), key=lambda x: int(x))
        return {int(pid): idx for idx, pid in enumerate(sorted_ids)}
    
    def clear_all(self):
        """Clear all geometry while keeping project settings."""
        self.points.clear()
        self.layers.clear()
        self.connections.clear()
        self.edges.clear()
        self.hex_blocks.clear()
        self.patches.clear()
        
        # Reset counters
        self.next_point_id = 1
        self.next_connection_id = 1
        self.next_edge_id = 1
        self.next_block_id = 1
        
        # Clear recycled IDs
        self.available_point_ids.clear()
        
        # Re-init default
        self._init_default()
    
    # =========================================================================
    # SERIALIZATION - Matches new_data_structure.json exactly
    # =========================================================================
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization - matches new_data_structure.json"""
        # Convert points to the format: "Point num: int (Point 1)": {"X": float, "Y": float, "Z": float}
        points_dict = {}
        for point_id, point_data in self.points.items():
            points_dict[f"Point {point_id}"] = {
                "X": point_data["X"],
                "Y": point_data["Y"],
                "Z": point_data["Z"]
            }
        
        # Convert layers to the format: "Layer Name: int": {"Points (Ref)": "1, 2..."}
        layers_dict = {}
        for layer_name, layer_data in self.layers.items():
            point_refs_str = ", ".join([str(p) for p in layer_data["point_refs"]])
            layers_dict[layer_name] = {
                "Points (Ref)": point_refs_str
            }
        
        # Convert connections to the format: "Connection num: int": {"Point 1": id, "Point 2": id}
        connections_dict = {}
        for conn_id, conn_data in self.connections.items():
            connections_dict[f"Connection {conn_id}"] = {
                "Point 1": conn_data["point1"],
                "Point 2": conn_data["point2"]
            }
        
        # Convert edges to the format: "Edge num: int": {"type": str, "Points": "1, 2,...", "Input Points": "(X,Y,Z), ..."}
        edges_dict = {}
        for edge_id, edge_data in self.edges.items():
            point_refs_str = ", ".join([str(p) for p in edge_data["point_refs"]])
            input_points_str = ", ".join([f"({p[0]},{p[1]},{p[2]})" for p in edge_data["input_points"]]) if edge_data["input_points"] else ""
            edges_dict[f"Edge {edge_id}"] = {
                "type": edge_data["type"],
                "Points": point_refs_str,
                "Input Points": input_points_str
            }
        
        # Convert hex blocks to the format: "Hex num: int": {"Points": "Point 1, Point 2, ..."}
        hexes_dict = {}
        for block_id, block_data in self.hex_blocks.items():
            point_refs_str = ", ".join([f"Point {p}" for p in block_data["point_refs"]])
            hexes_dict[f"Hex {block_id}"] = {
                "Points": point_refs_str
            }
        
        # Convert patches to the format: "Patch name: str": {"type": str, "Points": "Point 1, Point 2...", "Normal": int}
        patches_dict = {}
        for patch_name, patch_data in self.patches.items():
            point_refs_str = ", ".join([f"Point {p}" for p in patch_data["point_refs"]])
            patches_dict[patch_name] = {
                "type": patch_data["type"],
                "Points": point_refs_str,
                "Normal": patch_data.get("Normal", 1)
            }
        
        # Specs section
        specs_dict = {
            "sketch_plane": self.sketch_plane,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "unit_system": self.unit_system,
            "unit_sci_exponent": self.unit_sci_exponent
        }
        
        return {
            "Points": points_dict,
            "Layers": layers_dict,
            "Connections": connections_dict,
            "Edges": edges_dict,
            "Hexes": hexes_dict,
            "Patches": patches_dict,
            "Specs": specs_dict
        }
    
    def from_dict(self, data):
        """Load from dictionary - matches new_data_structure.json"""
        # Clear existing data
        self.points.clear()
        self.layers.clear()
        self.connections.clear()
        self.edges.clear()
        self.hex_blocks.clear()
        self.patches.clear()
        
        # Reset counters
        self.next_point_id = 1
        self.next_connection_id = 1
        self.next_edge_id = 1
        self.next_block_id = 1
        
        # Clear recycled IDs
        self.available_point_ids.clear()
        
        # Load Points
        points_data = data.get("Points", {})
        max_point_id = 0
        for point_key, point_data in points_data.items():
            # Parse "Point X" to get ID
            try:
                point_id = int(point_key.replace("Point ", ""))
                self.points[str(point_id)] = {
                    "X": float(point_data["X"]),
                    "Y": float(point_data["Y"]),
                    "Z": float(point_data["Z"])
                }
                if point_id > max_point_id:
                    max_point_id = point_id
            except:
                continue
        self.next_point_id = max_point_id + 1
        
        # Load Layers
        layers_data = data.get("Layers", {})
        for layer_name, layer_data in layers_data.items():
            point_refs_str = layer_data.get("Points (Ref)", "")
            point_refs = []
            if point_refs_str:
                try:
                    point_refs = [int(p.strip()) for p in point_refs_str.split(",") if p.strip()]
                except:
                    point_refs = []
            # Extract Z from first point if available
            z_value = 0.0
            if point_refs:
                first_point = self.points.get(str(point_refs[0]))
                if first_point:
                    z_value = first_point["Z"]
            self.layers[layer_name] = {
                "z": z_value,
                "point_refs": point_refs
            }
        
        # Load Connections
        connections_data = data.get("Connections", {})
        max_conn_id = 0
        for conn_key, conn_data in connections_data.items():
            try:
                conn_id = int(conn_key.replace("Connection ", ""))
                self.connections[str(conn_id)] = {
                    "point1": int(conn_data["Point 1"]),
                    "point2": int(conn_data["Point 2"])
                }
                if conn_id > max_conn_id:
                    max_conn_id = conn_id
            except:
                continue
        self.next_connection_id = max_conn_id + 1
        
        # Load Edges
        edges_data = data.get("Edges", {})
        max_edge_id = 0
        for edge_key, edge_data in edges_data.items():
            try:
                edge_id = int(edge_key.replace("Edge ", ""))
                point_refs_str = edge_data.get("Points", "")
                point_refs = []
                if point_refs_str:
                    point_refs = [int(p.strip()) for p in point_refs_str.split(",") if p.strip()]
                
                input_points_str = edge_data.get("Input Points", "")
                input_points = []
                if input_points_str:
                    # Parse "(X,Y,Z)" format
                    import re
                    matches = re.findall(r"\(([^)]+)\)", input_points_str)
                    for match in matches:
                        coords = [float(c.strip()) for c in match.split(",")]
                        if len(coords) == 3:
                            input_points.append(tuple(coords))
                
                self.edges[str(edge_id)] = {
                    "type": edge_data.get("type", "polyLine"),
                    "point_refs": point_refs,
                    "input_points": input_points
                }
                if edge_id > max_edge_id:
                    max_edge_id = edge_id
            except:
                continue
        self.next_edge_id = max_edge_id + 1
        
        # Load Hexes
        hexes_data = data.get("Hexes", {})
        max_block_id = 0
        for hex_key, hex_data in hexes_data.items():
            try:
                block_id = int(hex_key.replace("Hex ", ""))
                points_str = hex_data.get("Points", "")
                point_refs = []
                if points_str:
                    # Parse "Point 1, Point 2, ..." format
                    import re
                    matches = re.findall(r"Point (\d+)", points_str)
                    point_refs = [int(m) for m in matches]
                
                self.hex_blocks[str(block_id)] = {
                    "point_refs": point_refs
                }
                if block_id > max_block_id:
                    max_block_id = block_id
            except:
                continue
        self.next_block_id = max_block_id + 1
        
        # Load Patches
        patches_data = data.get("Patches", {})
        for patch_name, patch_data in patches_data.items():
            points_str = patch_data.get("Points", "")
            point_refs = []
            if points_str:
                import re
                matches = re.findall(r"Point (\d+)", points_str)
                point_refs = [int(m) for m in matches]
            
            self.patches[patch_name] = {
                "type": patch_data.get("type", "patch"),
                "point_refs": point_refs,
                "Normal": patch_data.get("Normal", 1)
            }
        
        # Load Specs
        specs_data = data.get("Specs", {})
        self.sketch_plane = specs_data.get("sketch_plane", "XY")
        self.project_name = specs_data.get("project_name", "Untitled Project")
        self.project_description = specs_data.get("project_description", "")
        self.unit_system = specs_data.get("unit_system", "m")
        self.unit_sci_exponent = specs_data.get("unit_sci_exponent", "0")
        
        # Set current layer
        if self.layers:
            self.current_layer = list(self.layers.keys())[0]
        else:
            self._init_default()
