# BlockMeshAuto

A powerful and intuitive GUI tool for creating OpenFOAM `blockMeshDict` files. Featuring 2D layer-based editing and real-time 3D visualization, it simplifies the process of manual mesh generation for OpenFOAM.

![BlockMeshAuto UI](https://via.placeholder.com/800x450/1e1e1e/d4d4d4?text=BlockMeshAuto+UI)

## 🚀 Features

- **Modular Workflow**: Six dedicated tabs for Project Settings, 2D Editing, Edge Definition, Hex Block Creation, Patch Assignment, and Export.
- **2D Layer-Based Editor**: Design your base profile with precision using multiple Z-planes.
- **Point & Connection Management**: Easily manage points and link them with straight lines, arcs, or splines.
- **3D Visualization**: Real-time 3D rendering of your mesh geometry and hex blocks.
- **Interactive Patch Assignment**: Assign boundary patches (walls, inlets, outlets) directly on the 3D model.
- **Project Persistence**: Save and load your work in a human-readable JSON format.
- **OpenFOAM Optimized**: Export clean, valid `blockMeshDict` files ready for use in your CFD simulations.
- **Dark Mode UI**: Professional, eyes-friendly interface designed for long engineering sessions.

## 🛠️ Installation

### Prerequisites

- **Python 3.10+**
- **pip** (Python package installer)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/chinmay-s-patil/blockMeshAuto.git
   cd blockMeshAuto
   ```

2. Install the required dependencies:
   ```bash
   pip install -r Code/requirements.txt
   ```

## 📖 Usage

Navigate to the `Code` directory and run the main application:

```bash
cd Code
python main.py
```

### Workflow Overview

1.  **Project Settings**: Set your project name, description, unit system, and sketch plane.
2.  **Points & Connections**: Create your 2D profile. Use layers for different Z-elevations.
3.  **Edge Editor**: Define curved edges (arcs, splines) between points.
4.  **Hex Blocks**: Build hexahedral blocks by selecting corresponding points on different layers.
5.  **Hex View & Patches**: Inspect your 3D mesh and assign boundary faces to named patches.
6.  **Export**: Review the generated `blockMeshDict` and save it to your OpenFOAM project.

## 📁 Project Structure

```text
BlockMeshAuto/
├── Code/
│   ├── main.py                # Application entry point
│   ├── mesh_data.py           # Core data management
│   ├── tab1_projectSettings/  # Tab 1 modules
│   ├── tab2_2DEditor/         # Tab 2 modules
│   ├── tab3_Edges/            # Tab 3 modules
│   ├── tab4_Hex/              # Tab 4 modules
│   ├── tab5_Patches/          # Tab 5 modules
│   ├── tab6_export/           # Tab 6 modules
│   ├── utils/                 # Shared utilities
│   └── requirements.txt       # Project dependencies
├── Examples/                  # Sample JSON projects
├── Trial Case/                # OpenFOAM test case
└── README.md                  # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.