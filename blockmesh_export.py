"""
Export to OpenFOAM blockMeshDict format
"""

class BlockMeshExporter:
    def __init__(self, mesh_data):
        self.mesh_data = mesh_data
        
    def generate_blockmesh_dict(self):
        """Generate blockMeshDict content"""
        vertices, vertex_map = self._get_vertices()
        blocks = self._get_blocks(vertex_map)
        patches = self._get_patches(vertex_map)
        
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
        output.append("scale   1;")
        output.append("")
        
        # Vertices
        output.append("vertices")
        output.append("(")
        for v in vertices:
            output.append(f"    ({v[0]:.6f} {v[1]:.6f} {v[2]:.6f})")
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
        """Extract all unique vertices"""
        vertices = []
        vertex_map = {}
        
        idx = 0
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            z = self.mesh_data.layers[layer]
            for local_idx, (x, y) in enumerate(self.mesh_data.points[layer]):
                vertices.append((x, y, z))
                vertex_map[(layer, local_idx)] = idx
                idx += 1
                
        return vertices, vertex_map
    
    def _get_blocks(self, vertex_map):
        """Generate blocks (hexahedral cells)"""
        blocks = []
        
        # For a proper blockMesh, we need to identify hexahedral blocks
        # This is a simplified version - assumes structured connectivity
        layers_sorted = sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l])
        
        # Example: If we have connections forming quads in each layer
        # and matching quads in adjacent layers, we can form hex blocks
        
        for i in range(len(layers_sorted) - 1):
            layer1 = layers_sorted[i]
            layer2 = layers_sorted[i + 1]
            
            # Simplified: assume first 4 points form a quad
            if len(self.mesh_data.points[layer1]) >= 4 and len(self.mesh_data.points[layer2]) >= 4:
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
        """Generate boundary patches"""
        patches = []
        
        # Add user-defined patches
        for patch_name, patch_type, face_indices in self.mesh_data.patches:
            faces = []
            for face_idx in face_indices:
                # Convert face indices to vertex indices
                # This is simplified
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