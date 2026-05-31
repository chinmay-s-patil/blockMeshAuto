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

        # Edges for curved geometry - Stores actual edge data from TabEdgeEditor
        # Structure: {"Edge num: int": {"type": str, "start": id/tuple, "end": id/tuple, "intermediate": id/list/tuple}}
        self.edges = {}
        self.next_edge_id = 1

        # Hex blocks reference 8 point IDs (or fewer for wedges/etc)
        # Structure: {"Hex num: int": {"Points": [id0, id1, ..., id7]}}
        self.hex_blocks = {}
        self.next_block_id = 1

        # Patches reference face IDs with their 4 point IDs
        # Structure: {"Patch name: str": {"type": str, "faces": [{"face_id": int, "point_ids": [id1, id2, id3, id4]}, ...], "Normal": int}}
        self.patches = {}

        # Specs - Project settings
        # Structure: {"sketch_plane": str, "project_name": str, "project_description": str, 
        #             "unit_system": str, "unit_sci_exponent": str}
        self.sketch_plane = "XY"  # XY, YZ, or ZX
        self.project_name = "Untitled Project"
        self.project_description = ""
        self.unit_system = "m"  # m, cm, mm, or scientific
        self.unit_sci_exponent = "0"  # For scientific notation: 10^n
        self.scale = 1.0  # blockMeshDict scale factor (convertToMeters)

        # Hook for HistoryManager to save state
        self.save_state_callback = None

        # Initialize default layer
        self._init_default()

    def set_save_state_callback(self, callback):
        """Register the method to store an undo history point"""
        self.save_state_callback = callback

    def save_state(self):
        """Helper to invoke the undo history save"""
        if self.save_state_callback:
            self.save_state_callback()

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
            layer_data = self.layers.get(layer, {})
            z = layer_data.get("z", 0.0)

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
                layer_data = self.layers[layer]
                point_refs = layer_data.get("point_refs", [])
                if point_id not in point_refs:
                    point_refs.append(point_id)
                    layer_data["point_refs"] = point_refs

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
            point_refs = layer_data.get("point_refs", [])
            if point_id in point_refs:
                point_refs.remove(point_id)
                layer_data["point_refs"] = point_refs

        # Remove from all connections (and delete connections involving this point)
        conns_to_delete = []
        for conn_id, conn in self.connections.items():
            if conn.get("point1") == point_id or conn.get("point2") == point_id:
                conns_to_delete.append(conn_id)
        for conn_id in conns_to_delete:
            if conn_id in self.connections:
                del self.connections[conn_id]

        # Remove from all edges
        edges_to_delete = []
        for edge_id, edge_data in self.edges.items():
            # Check start, end, and intermediate points
            has_point = False
            if edge_data.get("start") == point_id:
                has_point = True
            if edge_data.get("end") == point_id:
                has_point = True
            intermediate = edge_data.get("intermediate")
            if isinstance(intermediate, int) and intermediate == point_id:
                has_point = True
            elif isinstance(intermediate, list) and point_id in intermediate:
                has_point = True
            if has_point:
                edges_to_delete.append(edge_id)

        for edge_id in edges_to_delete:
            if edge_id in self.edges:
                del self.edges[edge_id]

        # Remove from all hex blocks (and delete blocks that become invalid)
        blocks_to_delete = []
        for block_id, block_data in self.hex_blocks.items():
            block_point_refs = block_data.get("point_refs", [])
            if point_id in block_point_refs:
                # Remove the point ref
                block_point_refs.remove(point_id)
                block_data["point_refs"] = block_point_refs
                # Mark for deletion if less than 4 points (can't form a valid cell)
                if len(block_point_refs) < 4:
                    blocks_to_delete.append(block_id)
        for block_id in blocks_to_delete:
            if block_id in self.hex_blocks:
                del self.hex_blocks[block_id]

        # Remove from all patches
        for patch_name, patch_data in self.patches.items():
            patch_faces = patch_data.get("faces", [])
            # Check each face's point_ids for this point
            for face in patch_faces:
                if isinstance(face, dict) and 'point_ids' in face:
                    if point_id in face['point_ids']:
                        face['point_ids'].remove(point_id)

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
                "x": point_data.get("X", 0),
                "y": point_data.get("Y", 0),
                "z": point_data.get("Z", 0)
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
            layer_data = self.layers[name]
            layer_data["z"] = float(z_value)
            # Also update Z coordinate of all points in this layer
            for point_id in layer_data.get("point_refs", []):
                self.update_point(point_id, z=z_value)
            return True
        return False

    def get_layer_z(self, name):
        """Get Z value of a layer."""
        layer_data = self.layers.get(name, {})
        return layer_data.get("z", 0.0)

    def add_point_to_layer(self, point_id, layer_name):
        """Add an existing point reference to a layer."""
        if layer_name not in self.layers or str(point_id) not in self.points:
            return False

        layer_data = self.layers[layer_name]
        point_refs = layer_data.get("point_refs", [])
        if point_id not in point_refs:
            point_refs.append(point_id)
            layer_data["point_refs"] = point_refs
            # Update point Z to match layer
            z = layer_data.get("z", 0.0)
            self.update_point(point_id, z=z)

        return True

    def remove_point_from_layer(self, point_id, layer_name):
        """Remove a point reference from a layer (doesn't delete point)."""
        if layer_name in self.layers:
            layer_data = self.layers[layer_name]
            point_refs = layer_data.get("point_refs", [])
            if point_id in point_refs:
                point_refs.remove(point_id)
                layer_data["point_refs"] = point_refs
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
            if conn.get("point1") == p1 and conn.get("point2") == p2:
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

    def add_edge(self, edge_type, start, end, intermediate=None):
        """
        Add an edge definition matching TabEdgeEditor format.
        edge_type: "arc", "spline", "polyLine", "line"
        start: point ID (int) or coordinate tuple (x, y, z)
        end: point ID (int) or coordinate tuple (x, y, z)
        intermediate: point ID, list of point IDs, or coordinate tuple(s)
        """
        edge_id = self.next_edge_id
        edge_data = {
            "type": edge_type,
            "start": start,
            "end": end
        }
        if intermediate is not None:
            edge_data["intermediate"] = intermediate

        self.edges[str(edge_id)] = edge_data
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

        refs = block_data.get("point_refs", [])
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

    def add_patch(self, name, patch_type, face_data, normal=1):
        """
        Add a patch with type and face data.
        face_data: list of dicts with 'face_id' and 'point_ids' (4 point IDs per face)
        normal: direction (1 or -1)
        """
        # Validate all point IDs exist
        for face in face_data:
            if isinstance(face, dict) and 'point_ids' in face:
                for pid in face['point_ids']:
                    if str(pid) not in self.points:
                        return False

        self.patches[name] = {
            "type": patch_type,
            "faces": face_data,  # List of dicts with face_id and point_ids
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
            patch_data = self.patches[name]
            patch_data["type"] = new_type
            return True
        return False

    # =========================================================================
    # UTILITY / EXPORT
    # =========================================================================

    def get_scale_value(self):
        """Get the numerical scale value for blockMeshDict export"""
        # If scale is explicitly set, use it (from imported blockMeshDict)
        if hasattr(self, 'scale') and self.scale is not None:
            return self.scale

        # Otherwise derive from unit system
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
        safe_name = re.sub(r'[<>\":/\\|?*]', '_', self.project_name)
        safe_name = safe_name.strip('. ')
        if not safe_name:
            safe_name = "untitled_project"
        return safe_name

    def get_all_points_list(self):
        """Get points as a list ordered by ID for blockMeshDict export."""
        sorted_ids = sorted(self.points.keys(), key=lambda x: int(x))
        return [(self.points[pid].get("X", 0), self.points[pid].get("Y", 0), self.points[pid].get("Z", 0)) 
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

    def get_3d_coords_from_global(self, global_idx):
        """Get 3D coordinates for a global point ID.
        Returns (x, y, z) tuple or None if point doesn't exist."""
        point_data = self.points.get(str(global_idx))
        if point_data:
            return (point_data.get("X", 0), point_data.get("Y", 0), point_data.get("Z", 0))
        return None

    def get_layer_from_global_index(self, global_idx):
        """Find which layer contains a given point ID.
        Returns (layer_name, local_index) or (None, None) if not found."""
        for layer_name, layer_data in self.layers.items():
            point_refs = layer_data.get("point_refs", [])
            if global_idx in point_refs:
                local_idx = point_refs.index(global_idx)
                return layer_name, local_idx
        return None, None

    def get_3d_coords(self, layer_name, point_2d):
        """Get 3D coordinates for a point in a layer.
        point_2d can be an index or a dict with x, y.
        Returns (x, y, z) tuple."""
        # If point_2d is an index, look up in layer's point_refs
        if isinstance(point_2d, int):
            layer_data = self.layers.get(layer_name)
            if layer_data:
                point_refs = layer_data.get("point_refs", [])
                if point_2d < len(point_refs):
                    point_id = point_refs[point_2d]
                    return self.get_3d_coords_from_global(point_id)
        # If point_2d is a dict with x, y
        elif isinstance(point_2d, dict):
            z = self.get_layer_z(layer_name)
            return (point_2d.get("x", 0), point_2d.get("y", 0), z)
        return (0, 0, 0)

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
    # SERIALIZATION - FIXED for proper patch face export
    # =========================================================================

    def _format_point_ref(self, ref):
        """Format a point reference (int or tuple) for JSON"""
        if isinstance(ref, int):
            return str(ref)
        elif isinstance(ref, (list, tuple)) and len(ref) == 3:
            return f"({ref[0]},{ref[1]},{ref[2]})"
        return str(ref)

    def _parse_point_ref(self, ref_str):
        """Parse a point reference from JSON string"""
        ref_str = ref_str.strip()
        if ref_str.startswith("(") and ref_str.endswith(")"):
            # Parse coordinate tuple
            try:
                coords = ref_str[1:-1].split(",")
                if len(coords) == 3:
                    return (float(coords[0]), float(coords[1]), float(coords[2]))
            except:
                pass
        # Try as integer point ID
        try:
            return int(ref_str)
        except:
            return ref_str

    def to_dict(self):
        """Convert to dictionary for JSON serialization - matches new_data_structure.json"""
        try:
            return self._to_dict_internal()
        except Exception as e:
            import traceback
            print(f"ERROR in to_dict: {e}")
            traceback.print_exc()
            raise

    def _to_dict_internal(self):
        """Internal method for to_dict with error handling"""
        # Convert points to the format: "Point num: int (Point 1)": {"X": float, "Y": float, "Z": float}
        points_dict = {}
        for point_id, point_data in self.points.items():
            points_dict[f"Point {point_id}"] = {
                "X": point_data.get("X", 0),
                "Y": point_data.get("Y", 0),
                "Z": point_data.get("Z", 0)
            }

        # Convert layers to the format: "Layer Name: int": {"Points (Ref)": "1, 2..."}
        layers_dict = {}
        for layer_name, layer_data in self.layers.items():
            point_refs = layer_data.get("point_refs", [])
            point_refs_str = ", ".join([str(p) for p in point_refs])
            layers_dict[layer_name] = {
                "Points (Ref)": point_refs_str
            }

        # Convert connections to the format: "Connection num: int": {"Point 1": id, "Point 2": id}
        connections_dict = {}
        for conn_id, conn_data in self.connections.items():
            connections_dict[f"Connection {conn_id}"] = {
                "Point 1": conn_data.get("point1", 0),
                "Point 2": conn_data.get("point2", 0)
            }

        # Convert edges to the format: "Edge num: int": {"type": str, "Points": "start, end, intermediate..."}
        # The Points field contains: start_point, end_point, and any intermediate points
        edges_dict = {}
        for edge_id, edge_data in self.edges.items():
            # Build points list: start, end, then intermediate(s)
            points_list = []

            # Add start point
            start = edge_data.get("start")
            if start is not None:
                points_list.append(self._format_point_ref(start))

            # Add end point
            end = edge_data.get("end")
            if end is not None:
                points_list.append(self._format_point_ref(end))

            # Add intermediate point(s)
            intermediate = edge_data.get("intermediate")
            if intermediate is not None:
                if isinstance(intermediate, list):
                    for pt in intermediate:
                        points_list.append(self._format_point_ref(pt))
                else:
                    points_list.append(self._format_point_ref(intermediate))

            point_refs_str = ", ".join(points_list)

            edges_dict[f"Edge {edge_id}"] = {
                "type": edge_data.get("type", "line"),
                "Points": point_refs_str
            }

        # Convert hex blocks to the format: "Hex num: int": {"Points": "Point 1, Point 2, ..."}
        hexes_dict = {}
        for block_id, block_data in self.hex_blocks.items():
            point_refs = block_data.get("point_refs", [])
            point_refs_str = ", ".join([f"Point {p}" for p in point_refs])
            hexes_dict[f"Hex {block_id}"] = {
                "Points": point_refs_str
            }

        # CRITICAL FIX: Convert patches to store 4 point IDs per face
        # Format: "Patch name: str": {"type": str, "Points": "(p1 p2 p3 p4), (p5 p6 p7 p8)...", "Normal": int}
        patches_dict = {}
        for patch_name, patch_data in self.patches.items():
            # SAFETY: Skip if patch_data is None
            if patch_data is None:
                print(f"WARNING: Patch '{patch_name}' has None data, skipping")
                continue

            # SAFETY: Ensure patch_data is a dict
            if not isinstance(patch_data, dict):
                print(f"WARNING: Patch '{patch_name}' is not a dict (type: {type(patch_data)}), skipping")
                continue

            faces = patch_data.get("faces", [])

            # SAFETY: Ensure faces is a list
            if faces is None:
                print(f"WARNING: Patch '{patch_name}' has None faces, using empty list")
                faces = []

            # Build string of 4 point IDs per face: "(0 4 7 3), (1 5 6 2)"
            face_strs = []
            missing_point_ids = []
            for i, face in enumerate(faces):
                if isinstance(face, dict) and 'point_ids' in face:
                    pids = face['point_ids']
                    # SAFETY: Check pids is not None and has 4 elements
                    if pids is not None and len(pids) == 4:
                        face_strs.append(f"{pids[0]} {pids[1]} {pids[2]} {pids[3]}")
                    else:
                        missing_point_ids.append(f"face[{i}]: pids={pids}")
                elif isinstance(face, int):
                    # Legacy format: just a face ID - can't convert without renderer
                    face_strs.append(f"(face_{face})")
                    missing_point_ids.append(f"face[{i}]: legacy int format")
                else:
                    missing_point_ids.append(f"face[{i}]: type={type(face)}")

            # Debug output if faces are missing point_ids
            if missing_point_ids and face_strs:
                print(f"DEBUG: Patch '{patch_name}' has {len(missing_point_ids)} faces missing point_ids (saved {len(face_strs)})")
            elif missing_point_ids:
                print(f"WARNING: Patch '{patch_name}' has no faces with valid point_ids!")
                print(f"  Missing: {missing_point_ids[:3]}...")

            faces_str = ", ".join(face_strs)

            patches_dict[patch_name] = {
                "type": patch_data.get("type", "patch"),
                "Points": faces_str,  # Now contains "p1 p2 p3 p4, p5 p6 p7 p8" format!
                "Normal": patch_data.get("Normal", 1)
            }

        # Specs section
        specs_dict = {
            "sketch_plane": self.sketch_plane,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "unit_system": self.unit_system,
            "unit_sci_exponent": self.unit_sci_exponent,
            "scale": getattr(self, 'scale', 1.0)
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
                    "X": float(point_data.get("X", 0)),
                    "Y": float(point_data.get("Y", 0)),
                    "Z": float(point_data.get("Z", 0))
                }
                if point_id > max_point_id:
                    max_point_id = point_id
            except Exception as e:
                print(f"Error loading point {point_key}: {e}")
                continue
        self.next_point_id = max_point_id + 1 if max_point_id > 0 else 1

        # Load Layers
        layers_data = data.get("Layers", {})
        for layer_name, layer_data in layers_data.items():
            point_refs_str = layer_data.get("Points (Ref)", "")
            point_refs = []
            if point_refs_str:
                try:
                    point_refs = [int(p.strip()) for p in point_refs_str.split(",") if p.strip()]
                except Exception as e:
                    print(f"Error parsing layer {layer_name} point refs: {e}")
                    point_refs = []
            # Extract Z from first point if available
            z_value = 0.0
            if point_refs:
                first_point = self.points.get(str(point_refs[0]))
                if first_point:
                    z_value = first_point.get("Z", 0.0)
            self.layers[layer_name] = {
                "z": z_value,
                "point_refs": point_refs if point_refs else []
            }

        # Load Connections
        connections_data = data.get("Connections", {})
        max_conn_id = 0
        for conn_key, conn_data in connections_data.items():
            try:
                conn_id = int(conn_key.replace("Connection ", ""))
                self.connections[str(conn_id)] = {
                    "point1": int(conn_data.get("Point 1", 0)),
                    "point2": int(conn_data.get("Point 2", 0))
                }
                if conn_id > max_conn_id:
                    max_conn_id = conn_id
            except Exception as e:
                print(f"Error loading connection {conn_key}: {e}")
                continue
        self.next_connection_id = max_conn_id + 1 if max_conn_id > 0 else 1

        # Load Edges - NEW FORMAT with start, end, intermediate
        edges_data = data.get("Edges", {})
        max_edge_id = 0
        for edge_key, edge_data in edges_data.items():
            try:
                edge_id = int(edge_key.replace("Edge ", ""))

                points_str = edge_data.get("Points", "")
                points_list = []

                # Parse points string: "1, 2, (1.5,2.5,0)" or "(0,0,0), (1,0,0), (0.5,0.5,0)"
                if points_str:
                    # Split carefully handling tuples with commas inside
                    parts = []
                    current = ""
                    depth = 0
                    for char in points_str:
                        if char == '(':
                            depth += 1
                            current += char
                        elif char == ')':
                            depth -= 1
                            current += char
                        elif char == ',' and depth == 0:
                            parts.append(current.strip())
                            current = ""
                        else:
                            current += char
                    if current.strip():
                        parts.append(current.strip())

                    for part in parts:
                        points_list.append(self._parse_point_ref(part))

                # Build edge data
                edge_dict = {"type": edge_data.get("type", "line")}

                if len(points_list) >= 2:
                    edge_dict["start"] = points_list[0]
                    edge_dict["end"] = points_list[1]

                    if len(points_list) > 2:
                        remaining = points_list[2:]
                        # Store single intermediate as scalar, multiple as list
                        edge_dict["intermediate"] = remaining[0] if len(remaining) == 1 else remaining

                self.edges[str(edge_id)] = edge_dict
                if edge_id > max_edge_id:
                    max_edge_id = edge_id

            except Exception as e:
                print(f"Error loading edge {edge_key}: {e}")
                continue
        self.next_edge_id = max_edge_id + 1 if max_edge_id > 0 else 1

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
            except Exception as e:
                print(f"Error loading hex {hex_key}: {e}")
                continue
        self.next_block_id = max_block_id + 1 if max_block_id > 0 else 1

        # CRITICAL FIX: Load Patches with proper face point IDs
        # Format: "Points": "(0 4 7 3), (1 5 6 2)" - 4 point IDs per face
        # Format: "Points": "15 1 3 17, 18 19 20 21" or "(15 1 3 17), (18 19 20 21)" - 4 point IDs per face
        patches_data = data.get("Patches", {})
        for patch_name, patch_data in patches_data.items():
            try:
                points_str = patch_data.get("Points", "")

                # Parse faces with 4 point IDs each: "15 1 3 17, 18 19 20 21"
                face_data = []
                if points_str:
                    # Find all tuples of 4 numbers
                    import re
                    # Match pattern like "15 1 3 17" or "(15, 1, 3, 17)"
                    face_matches = re.findall(r'\(?(\d+)[\s,]+(\d+)[\s,]+(\d+)[\s,]+(\d+)\)?', points_str)

                    for match in face_matches:
                        p1, p2, p3, p4 = map(int, match)
                        face_data.append({
                            'face_id': len(face_data),  # Generate new face ID
                            'point_ids': [p1, p2, p3, p4]  # Store the 4 point IDs!
                        })

                self.patches[patch_name] = {
                    "type": patch_data.get("type", "patch"),
                    "faces": face_data,  # Now contains proper face data with 4 point IDs each
                    "Normal": patch_data.get("Normal", 1)
                }
            except Exception as e:
                print(f"Error loading patch {patch_name}: {e}")
                continue

        # Load Specs
        specs_data = data.get("Specs", {})
        self.sketch_plane = specs_data.get("sketch_plane", "XY")
        self.project_name = specs_data.get("project_name", "Untitled Project")
        self.project_description = specs_data.get("project_description", "")
        self.unit_system = specs_data.get("unit_system", "m")
        self.unit_sci_exponent = specs_data.get("unit_sci_exponent", "0")
        self.scale = specs_data.get("scale", 1.0)

        # Set current layer
        if self.layers:
            self.current_layer = list(self.layers.keys())[0]
        else:
            self._init_default()