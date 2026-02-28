"""
BlockMeshDict Importer Utility
Parses OpenFOAM blockMeshDict files and imports them into the mesh builder data structure.
"""
import re
import tkinter as tk
from tkinter import messagebox, filedialog


class BlockMeshImporter:
    """Parses blockMeshDict files and converts to MeshData format"""

    def __init__(self, mesh_data):
        self.mesh_data = mesh_data
        self.errors = []
        self.warnings = []

    def _extract_section_paren(self, content, keyword):
        """Extract content from a keyword section like vertices(...), blocks(...), faces(...)
        Handles nested parentheses properly."""
        pattern = rf'{keyword}\s*\('
        match = re.search(pattern, content)
        if not match:
            return None

        start = match.end()  # Position right after the opening '('

        # Find the matching closing paren by counting
        depth = 1
        pos = start
        while depth > 0 and pos < len(content):
            if content[pos] == '(':
                depth += 1
            elif content[pos] == ')':
                depth -= 1
            pos += 1

        if depth == 0:
            return content[start:pos-1]  # Exclude the final ')'
        return None

    def _extract_patches(self, boundary_content):
        """Extract individual patches from boundary section"""
        patches = []

        pos = 0
        while pos < len(boundary_content):
            # Find next patch name (word followed by opening brace)
            match = re.search(r'(\w+)\s*\{', boundary_content[pos:])
            if not match:
                break

            patch_name = match.group(1)
            start = pos + match.end()  # Position after opening brace

            # Find matching closing brace
            depth = 1
            brace_pos = start
            while depth > 0 and brace_pos < len(boundary_content):
                if boundary_content[brace_pos] == '{':
                    depth += 1
                elif boundary_content[brace_pos] == '}':
                    depth -= 1
                brace_pos += 1

            if depth == 0:
                patch_content = boundary_content[start:brace_pos-1]
                patches.append((patch_name, patch_content))
                pos = brace_pos
            else:
                break

        return patches

    def import_file(self, filepath):
        """
        Import a blockMeshDict file.
        Returns True if successful, False otherwise.
        """
        self.errors = []
        self.warnings = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        # Parse the file
        try:
            parsed_data = self._parse_blockmesh_dict(content)
        except Exception as e:
            self.errors.append(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return False

        if not parsed_data:
            self.errors.append("No valid data found in file")
            return False

        # Clear existing mesh data
        self.mesh_data.clear_all()

        # Import vertices as points - KEEP ORIGINAL COORDINATES, don't apply scale
        vertices = parsed_data.get('vertices', [])
        if not vertices:
            self.errors.append("No vertices found in file")
            return False

        # Create points (vertices become global points) - NO SCALE APPLIED
        point_id_map = {}  # Maps vertex index (0-based) to global point ID
        for i, coords in enumerate(vertices):
            if len(coords) >= 3:
                # Keep original coordinates - scale is stored separately
                x, y, z = coords[0], coords[1], coords[2]
                point_id = self.mesh_data.add_point(x, y, z, layer=None)
                point_id_map[i] = point_id

        # Create a single layer for all points (use Z coordinate)
        if point_id_map:
            # Get unique Z values to create layers
            z_values = {}
            for vert_idx, point_id in point_id_map.items():
                coords = vertices[vert_idx]
                z = round(coords[2], 6)  # NO SCALE APPLIED
                if z not in z_values:
                    z_values[z] = []
                z_values[z].append(point_id)

            # Create layers for each unique Z
            layer_names = []
            for z in sorted(z_values.keys()):
                layer_name = f"Layer {len(layer_names)}"
                self.mesh_data.add_layer(layer_name, z)
                # Add points to this layer
                for point_id in z_values[z]:
                    self.mesh_data.add_point_to_layer(point_id, layer_name)
                layer_names.append(layer_name)

            # Set current layer
            if layer_names:
                self.mesh_data.current_layer = layer_names[0]

        # Import blocks as hex blocks
        blocks = parsed_data.get('blocks', [])
        for block in blocks:
            vertex_indices = block.get('vertices', [])
            if len(vertex_indices) == 8:
                # Map vertex indices to point IDs
                point_refs = []
                valid = True
                for vi in vertex_indices:
                    if vi in point_id_map:
                        point_refs.append(point_id_map[vi])
                    else:
                        valid = False
                        self.warnings.append(f"Block references undefined vertex {vi}")
                        break

                if valid and len(point_refs) == 8:
                    # Create hex block with divisions and grading info
                    block_data = {
                        'point_refs': point_refs,
                        'divisions': block.get('divisions', (1, 1, 1)),
                        'grading_type': block.get('grading_type', 'simpleGrading'),
                        'grading_params': block.get('grading_params', {'x': 1.0, 'y': 1.0, 'z': 1.0})
                    }
                    block_id = self.mesh_data.add_hex_block(point_refs)
                    # Store additional block data
                    if block_id:
                        self.mesh_data.hex_blocks[str(block_id)].update(block_data)

        # Import edges (curved edges)
        edges = parsed_data.get('edges', [])
        for edge in edges:
            edge_type = edge.get('type', 'line')
            start_idx = edge.get('start')
            end_idx = edge.get('end')

            if start_idx in point_id_map and end_idx in point_id_map:
                start_id = point_id_map[start_idx]
                end_id = point_id_map[end_idx]

                # Handle intermediate points
                intermediate = edge.get('intermediate', [])
                if isinstance(intermediate, list):
                    # Map vertex indices to point IDs for intermediate points
                    mapped_intermediate = []
                    for idx in intermediate:
                        if idx in point_id_map:
                            mapped_intermediate.append(point_id_map[idx])
                    intermediate = mapped_intermediate[0] if len(mapped_intermediate) == 1 else mapped_intermediate

                self.mesh_data.add_edge(edge_type, start_id, end_id, intermediate)

        # Import patches
        patches = parsed_data.get('patches', [])
        for patch in patches:
            patch_name = patch.get('name', 'unnamed')
            patch_type = patch.get('type', 'patch')
            faces = patch.get('faces', [])

            # Convert faces to new format with point_ids
            face_data = []
            for face in faces:
                if len(face) == 4:
                    # Map vertex indices to point IDs
                    point_ids = []
                    valid = True
                    for vi in face:
                        if vi in point_id_map:
                            point_ids.append(point_id_map[vi])
                        else:
                            valid = False
                            self.warnings.append(f"Patch '{patch_name}' face references undefined vertex {vi}")
                            break

                    if valid and len(point_ids) == 4:
                        face_data.append({
                            'face_id': len(face_data),
                            'point_ids': point_ids
                        })

            if face_data:
                self.mesh_data.add_patch(patch_name, patch_type, face_data, normal=1)

        # UPDATE SCALE IN PROJECT SETTINGS - don't apply it to coordinates
        scale = parsed_data.get('scale', 1.0)
        self.mesh_data.scale = scale

        # Convert scale to appropriate unit system display
        if scale == 1.0:
            self.mesh_data.unit_system = "m"
            self.mesh_data.unit_sci_exponent = "0"
        elif scale == 0.001:
            self.mesh_data.unit_system = "mm"
            self.mesh_data.unit_sci_exponent = "-3"
        elif scale == 0.01:
            self.mesh_data.unit_system = "cm"
            self.mesh_data.unit_sci_exponent = "-2"
        elif scale == 1000:
            self.mesh_data.unit_system = "scientific"
            self.mesh_data.unit_sci_exponent = "3"
        else:
            # Try to convert to scientific notation
            import math
            if scale > 0:
                exp = math.log10(scale)
                if exp == int(exp):
                    self.mesh_data.unit_system = "scientific"
                    self.mesh_data.unit_sci_exponent = str(int(exp))
                else:
                    self.mesh_data.unit_system = "scientific"
                    self.mesh_data.unit_sci_exponent = f"{exp:.2f}"

        # Update project name based on filename
        import os
        basename = os.path.basename(filepath)
        self.mesh_data.project_name = f"Imported: {basename}"

        # Show summary
        summary = f"Import Summary:\n"
        summary += f"- Vertices: {len(vertices)}\n"
        summary += f"- Scale: {scale} (stored in project settings)\n"
        summary += f"- Layers created: {len(z_values) if 'z_values' in dir() else 0}\n"
        summary += f"- Hex blocks: {len(blocks)}\n"
        summary += f"- Curved edges: {len(edges)}\n"
        summary += f"- Patches: {len(patches)}\n"

        if self.warnings:
            summary += f"\nWarnings ({len(self.warnings)}):\n"
            for w in self.warnings[:5]:
                summary += f"- {w}\n"
            if len(self.warnings) > 5:
                summary += f"... and {len(self.warnings) - 5} more\n"

        messagebox.showinfo("Import Complete", summary)
        return True

    def _parse_blockmesh_dict(self, content):
        """Parse the blockMeshDict file content"""
        data = {
            'scale': 1.0,
            'vertices': [],
            'blocks': [],
            'edges': [],
            'patches': []
        }

        # Remove C++ style comments (// to end of line)
        lines = []
        for line in content.split('\n'):
            # Remove inline comments
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line)

        content = '\n'.join(lines)

        # Extract scale (convertToMeters or scale)
        scale_match = re.search(r'(convertToMeters|scale)\s+([0-9.eE+-]+)', content)
        if scale_match:
            data['scale'] = float(scale_match.group(2))

        # Extract vertices using balanced parentheses
        vertices_str = self._extract_section_paren(content, 'vertices')
        if vertices_str:
            # Find all (x y z) tuples - handle extra whitespace
            vertex_pattern = r'\(\s*([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*\)'
            for match in re.finditer(vertex_pattern, vertices_str):
                x, y, z = float(match.group(1)), float(match.group(2)), float(match.group(3))
                data['vertices'].append((x, y, z))

        # Extract blocks using balanced parentheses
        blocks_str = self._extract_section_paren(content, 'blocks')
        if blocks_str:
            # Parse each hex block - handle varying whitespace
            # Pattern: hex (8 vertex indices) (3 divisions) simpleGrading (3 grading values)
            block_pattern = r'hex\s*\(\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s+(\d+)\s*\)\s*(simpleGrading|edgeGrading)\s*\(\s*([^)]+)\s*\)'
            for match in re.finditer(block_pattern, blocks_str):
                vertices = [int(match.group(i)) for i in range(1, 9)]
                divisions = (int(match.group(9)), int(match.group(10)), int(match.group(11)))
                grading_type = match.group(12)

                # Parse grading params
                grading_str = match.group(13)
                grading_values = [float(x) for x in re.findall(r'[0-9.eE+-]+', grading_str)]
                if len(grading_values) >= 3:
                    grading_params = {'x': grading_values[0], 'y': grading_values[1], 'z': grading_values[2]}
                else:
                    grading_params = {'x': 1.0, 'y': 1.0, 'z': 1.0}

                data['blocks'].append({
                    'vertices': vertices,
                    'divisions': divisions,
                    'grading_type': grading_type,
                    'grading_params': grading_params
                })

        # Extract edges using balanced parentheses
        edges_str = self._extract_section_paren(content, 'edges')
        if edges_str and edges_str.strip():
            # Pattern: arc v1 v2 (x y z) or spline v1 v2 ((x1 y1 z1) (x2 y2 z2) ...)
            edge_patterns = [
                (r'arc\s+(\d+)\s+(\d+)\s*\(([^)]+)\)', 'arc'),
                (r'spline\s+(\d+)\s+(\d+)\s*\(([^)]+)\)', 'spline'),
                (r'polyLine\s+(\d+)\s+(\d+)\s*\(([^)]+)\)', 'polyLine'),
                (r'BSpline\s+(\d+)\s+(\d+)\s*\(([^)]+)\)', 'BSpline')
            ]

            for pattern, edge_type in edge_patterns:
                for match in re.finditer(pattern, edges_str):
                    start = int(match.group(1))
                    end = int(match.group(2))
                    points_str = match.group(3)

                    # Parse intermediate points
                    intermediate = []
                    point_matches = re.findall(r'\(([^)]+)\)', points_str)
                    for pm in point_matches:
                        coords = [float(x) for x in pm.split()]
                        if len(coords) == 3:
                            intermediate.append(tuple(coords))

                    if not intermediate:
                        # Try single point format (for arc)
                        coords = [float(x) for x in points_str.split()]
                        if len(coords) == 3:
                            intermediate = tuple(coords)

                    data['edges'].append({
                        'type': edge_type,
                        'start': start,
                        'end': end,
                        'intermediate': intermediate
                    })

        # Extract boundary patches using balanced braces
        boundary_str = self._extract_section_paren(content, 'boundary')
        if boundary_str:
            # Extract individual patches
            patches = self._extract_patches(boundary_str)

            for patch_name, patch_content in patches:
                # Extract type
                type_match = re.search(r'type\s+(\w+)', patch_content)
                patch_type = type_match.group(1) if type_match else 'patch'

                # Extract faces using balanced parentheses
                faces_str = self._extract_section_paren(patch_content, 'faces')

                faces = []
                if faces_str:
                    # Parse individual faces
                    for face_match in re.finditer(r'\(\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\)', faces_str):
                        face = [int(face_match.group(i)) for i in range(1, 5)]
                        faces.append(face)

                if faces:
                    data['patches'].append({
                        'name': patch_name,
                        'type': patch_type,
                        'faces': faces
                    })

        return data

    def get_errors(self):
        """Return list of errors from last import"""
        return self.errors

    def get_warnings(self):
        """Return list of warnings from last import"""
        return self.warnings


# Standalone import function for use in main.py
def import_blockmesh_file(mesh_data, parent_window=None):
    """
    Show file dialog and import a blockMeshDict file.
    Returns True if import was successful.
    """
    filepath = filedialog.askopenfilename(
        parent=parent_window,
        title="Import blockMeshDict File",
        filetypes=[
            ("blockMeshDict files", "blockMeshDict"),
            ("Dictionary files", "*.dict"),
            ("All files", "*.*")
        ]
    )

    if not filepath:
        return False

    importer = BlockMeshImporter(mesh_data)
    success = importer.import_file(filepath)

    if not success:
        errors = importer.get_errors()
        error_msg = "Import failed:\n\n" + "\n".join(errors)
        messagebox.showerror("Import Error", error_msg)

    return success