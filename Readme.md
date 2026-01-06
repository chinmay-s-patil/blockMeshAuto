# OpenFOAM blockMesh Builder

A GUI tool for creating OpenFOAM `blockMeshDict` files with 2D layer-based editing and 3D visualization.

## Installation

### Ubuntu 24.04

```bash
pip install matplotlib numpy
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

## File Structure

```
mesh-builder/
├── main.py              # Main application GUI
├── mesh_data.py         # Data structures
├── blockmesh_export.py  # OpenFOAM export
├── viewer_3d.py         # 3D visualization
├── requirements.txt     # Dependencies
├── README.md           # This file
└── mesh_temp.json      # Auto-saved temporary file
```

## Features

✅ **Three editing modes**: Select, Add, Delete points  
✅ **Layer-based 2D editing** with multiple Z-planes  
✅ **Layer duplication** for quick geometry replication  
✅ **ISO mode** for linking points between layers  
✅ **Interactive 3D visualization** with pan/zoom/rotate  
✅ **Face selection toggle** for 3D patch assignment  
✅ **JSON save/load** for project persistence  
✅ **Auto-save** every 30 seconds  
✅ **Export to OpenFOAM blockMeshDict** format  

## Usage

Run the application:

```bash
python main.py
```

## Top Bar Controls

**💾 Save** - Save your project to JSON  
**📂 Load** - Load a project from JSON  
**🔄 New** - Start a new project (with save prompt)  

Projects are automatically saved to `mesh_temp.json` every 30 seconds.

## Workflow

### Tab 1: Points & Connections (2D Editor)

1. **Mode Selection** (3 modes with visual indicators)
   - **Select Mode** (Blue) - Click points to select them for connections
   - **Add Mode** (Green) - Click canvas to add new points
   - **Delete Mode** (Red) - Click points to delete them

2. **Layer Management**
   - Create multiple Z-layers using "Add"
   - "Duplicate" to copy current layer's geometry
   - "Remove" to delete a layer
   - Each layer represents a different Z-plane

3. **Normal Mode (Single Layer)**
   - Select a layer to work on
   - Add points by clicking or manual entry
   - Select 2 points → "Create Connection" to link them

4. **ISO Mode (Link Between Layers)**
   - Enable "Iso Mode (Link 2 Layers)" checkbox
   - Select exactly 2 layers from the layer list (hold Ctrl)
   - Both layers appear overlaid (red and blue)
   - Click points from either layer to select them
   - Green circles highlight selected points
   - "Create Connection" links points across layers
   - Green dashed lines show inter-layer connections

### Tab 2: 3D View & Patches

1. **3D Visualization**
   - Click "🔄 Update 3D View" to refresh
   - Toolbar controls:
     - **Pan**: Right-click and drag
     - **Zoom**: Scroll wheel
     - **Rotate**: Left-click and drag
   - Blue lines: horizontal connections (within layers)
   - Green dashed: inter-layer connections
   - Gray dotted: auto-connections between layers

2. **Face Selection**
   - Enable "Enable Face Selection" checkbox
   - Click on mesh faces to select them
   - Selected faces change color (cyan/yellow)
   - Multiple faces can be selected

3. **Patch Assignment**
   - Enter a patch name (e.g., "inlet", "outlet", "walls")
   - Select patch type:
     - `wall` - Solid wall boundary
     - `patch` - Generic patch
     - `symmetry` - Symmetry plane
     - `symmetryPlane` - Symmetry plane (newer syntax)
     - `wedge` - Axisymmetric wedge
     - `empty` - Empty boundary for 2D cases
     - `cyclic` - Cyclic boundary
   - Click "Assign to Selected Faces"
   - Patch appears in "Defined Patches" list

### Tab 3: Export blockMeshDict

1. **Preview**
   - Click "Generate & Preview" to see the blockMeshDict content
   - Review vertices, blocks, and boundary patches

2. **Save**
   - Click "Save to File" to export
   - Choose location and filename
   - Default name is `blockMeshDict`

## Keyboard Shortcuts

- **Ctrl + Click**: Multi-select layers in ISO mode
- **Tab**: Switch between sections
- **Mouse wheel**: Zoom in 3D view
- **Left-click drag**: Rotate 3D view
- **Right-click drag**: Pan 3D view

## Tips

- Start with Layer 0, add points and connections
- Use "Duplicate" to create parallel layers quickly
- Use ISO mode to link corresponding points between layers
- Enable "Face Selection" before clicking faces in 3D view
- Save your work frequently (auto-saves every 30 seconds)
- Load previous projects to continue editing

## Data Persistence

- **Auto-save**: Saves to `mesh_temp.json` every 30 seconds
- **Manual save**: Use 💾 Save button for named projects
- **JSON format**: Human-readable, easy to version control
- Stores: layers, points, connections, inter-layer links, patches

## OpenFOAM Integration

After exporting `blockMeshDict`:

1. Place it in your case's `system/` directory
2. Run `blockMesh` to generate the mesh
3. Check with `checkMesh`

```bash
blockMesh
checkMesh
```

## Troubleshooting

**ISO mode not working**: Make sure you've selected exactly 2 layers (Ctrl+Click)

**Points not visible in ISO mode**: Selected points show as large green circles

**Face selection not working**: Enable "Enable Face Selection" checkbox in Tab 2

**3D view empty**: Click "Update 3D View" after making changes in Tab 1

**Export fails**: Ensure you have at least 2 layers with matching point counts

## License

MIT License - Feel free to modify and distribute