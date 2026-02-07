"""
Export to OpenFOAM blockMeshDict format
Uses sequential global point numbering as required by blockMesh
"""

class BlockMeshExporter:
    def __init__(self, mesh_data):
        self.mesh_data = mesh_data
        
    def generate_blockmesh_dict(self):
        """Generate blockMeshDict content"""
        vertices, vertex_map = self._get_vertices()
        blocks = self._get_blocks(vertex_map)
        patches = self._get_patches(vertex_map)
        
        # Get scale value from unit system
        scale_value = self.mesh_data.get_scale_value()
        
        output = []
        output.append("/*--------------------------------*- C++ -*----------------------------------*\\")
        output.append("| =========                 |                                                 |")
        output.append("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |")
        output.append("|  \\\\    /   O peration     | Version:  v2312                                 |")
        output.append("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |")
        output.append("|    \\\\/     M anipulation  |                                                 |")
        output.append("\\*---------------------------------------------------------------------------*/")
        output.append("FoamFile")
        output.append("{")
        output.append("    version     2.0;")
        output.append("    format      ascii;")
        output.append("    class       dictionary;")
        output.append("    object      blockMeshDict;")
        output.append("}")
        output.append("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //")
        output.append("")
        
        # Add unit information as comment
        unit_info = f"// Unit system: {self.mesh_data.unit_system}"
        if self.mesh_data.unit_system == "scientific":
            unit_info += f" (10^{self.mesh_data.unit_sci_exponent})"
        output.append(unit_info)
        output.append("")
        
        # Scale parameter with actual value
        output.append(f"scale   {scale_value};")
        output.append("")
        
        # Vertices - sequential numbering
        output.append("vertices")
        output.append("(")
        for idx, v in enumerate(vertices):
            output.append(f"    ({v[0]:.6f} {v[1]:.6f} {v[2]:.6f})  // Vertex {idx}")
        output.append(");")
        output.append("")
        
        # Blocks
        output.append("blocks")
        output.append("(")
        for block in blocks:
            output.append(f"    hex {block['vertices']} ({block['cells'][0]} {block['cells'][1]} {block['cells'][2]}) simpleGrading (1 1 1)")
        output.append(");")
        output.append("")
        
        # Edges (empty for now)
        output.append("edges")
        output.append("(")
        output.append(");")
        output.append("")
        
        # Boundary patches
        output.append("boundary")
        output.append("(")
        for patch in patches:
            output.append(f"    {patch['name']}")
            output.append("    {")
            output.append(f"        type {patch['type']};")
            output.append("        faces")
            output.append("        (")
            for face in patch['faces']:
                output.append(f"            {face}")
            output.append("        );")
            output.append("    }")
        output.append(");")
        output.append("")
        
        output.append("mergePatchPairs")
        output.append("(")
        output.append(");")
        output.append("")
        output.append("// ************************************************************************* //")
        
        return "\n".join(output)
    
    def _get_vertices(self):
        """Extract all unique vertices with sequential global numbering"""
        vertices = []
        vertex_map = {}  # (layer, local_idx) -> global_idx
        
        global_idx = 0
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        for layer in layers_sorted:
            z = self.mesh_data.layers[layer]
            for local_idx, (x, y) in enumerate(self.mesh_data.points[layer]):
                # Use actual 3D coordinates based on sketch plane
                coords_3d = self.mesh_data.get_3d_coords(layer, (x, y))
                # For blockMesh, we need actual XYZ, not the matplotlib display coords
                # Convert back from display coords to OpenFOAM coords
                if self.mesh_data.sketch_plane == "XY":
                    # Display: (X, Z, Y) -> OpenFOAM: (X, Y, Z)
                    vertices.append((coords_3d[0], coords_3d[2], coords_3d[1]))
                elif self.mesh_data.sketch_plane == "YZ":
                    # Display: (Z, X, Y) -> OpenFOAM: (X, Y, Z)
                    vertices.append((coords_3d[1], coords_3d[0], coords_3d[2]))
                elif self.mesh_data.sketch_plane == "ZX":
                    # Display: (Y, Z, X) -> OpenFOAM: (X, Y, Z)
                    vertices.append((coords_3d[2], coords_3d[0], coords_3d[1]))
                else:
                    vertices.append((x, y, z))
                
                vertex_map[(layer, local_idx)] = global_idx
                global_idx += 1
                
        return vertices, vertex_map
    
    def _get_blocks(self, vertex_map):
        """Generate blocks (hexahedral cells) using global sequential indices"""
        blocks = []
        
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        # For each pair of adjacent layers
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            # Simplified: assume first 4 points form a quad
            # In a real implementation, you'd detect quads from the connection topology
            if len(self.mesh_data.points[layer1]) >= 4 and len(self.mesh_data.points[layer2]) >= 4:
                # Use global sequential indices
                v0 = vertex_map[(layer1, 0)]
                v1 = vertex_map[(layer1, 1)]
                v2 = vertex_map[(layer1, 2)]
                v3 = vertex_map[(layer1, 3)]
                v4 = vertex_map[(layer2, 0)]
                v5 = vertex_map[(layer2, 1)]
                v6 = vertex_map[(layer2, 2)]
                v7 = vertex_map[(layer2, 3)]
                
                blocks.append({
                    'vertices': f"({v0} {v1} {v2} {v3} {v4} {v5} {v6} {v7})",
                    'cells': (10, 10, 10)  # Default cell divisions
                })
        
        return blocks
    
    def _get_patches(self, vertex_map):
        """Generate boundary patches using global sequential indices"""
        patches = []
        
        # Add user-defined patches
        for patch_name, patch_type, face_indices in self.mesh_data.patches:
            faces = []
            for face_idx in face_indices:
                # Convert face indices to global vertex indices
                # This is simplified - needs proper face to vertex mapping
                faces.append(f"(0 1 2 3)")  # Placeholder
            
            patches.append({
                'name': patch_name,
                'type': patch_type,
                'faces': faces
            })
        
        # If no patches defined, create default ones
        if not patches:
            patches.append({
                'name': 'defaultPatch',
                'type': 'patch',
                'faces': ['(0 1 2 3)']
            })
        
        return patches
    
    def save_to_file(self, filename="blockMeshDict"):
        """Save blockMeshDict to file"""
        content = self.generate_blockmesh_dict()
        with open(filename, 'w') as f:
            f.write(content)
        return filename