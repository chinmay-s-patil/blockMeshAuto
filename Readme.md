# <p align="center">BlockMeshAuto v2.0</p>

<p align="center">
  <img src="BlockMeshLogo.png" alt="BlockMeshAuto Logo" width="200"/>
</p>

<p align="center">
  <strong>The Ultimate GUI for OpenFOAM blockMesh Generation</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0-blue.svg" alt="Version 2.0"/>
  <img src="https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg" alt="License CC0 1.0"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/UI-Dark_Mode-blueviolet.svg" alt="Dark Mode UI"/>
</p>

---

## 🌟 What's New in 2.0?

BlockMeshAuto 2.0 is a massive leap forward, transitioning from a basic editor to a professional-grade engineering tool. I've completely overhauled the core and added features that make mesh generation faster and more reliable.

### 🚀 Major Highlights

- **📂 Variable-Aware Import**: Already have a `blockMeshDict`? Import it directly! The parser now supports dictionary-defined variables (e.g., `$x1`, `$x2`), making it fully compatible with parameterized OpenFOAM setups.
- **🕒 Full History System**: Made a mistake? **Undo/Redo (Ctrl+Z / Ctrl+Y)** is now fully supported. Experiment with your designs with the confidence that you can always go back.
- **🖥️ Fullscreen Mode (F11)**: Maximize your workspace with a single keystroke. A dedicated F11 toggle for a distraction-free mesh building experience.
- **💎 Optimized Data Structure**: I've completely rewritten how data is stored. Your project JSONs are now clean, human-readable, and significantly smaller.
- **🎨 Advanced 3D Visualization**: 
  - **Internal Face Detection**: Automatically hides internal faces, showing only what matters.
  - **Patch Coloring**: Color-coded patch legend for instant boundary verification.
  - **Lasso & Box Selection**: High-speed vertex selection in the Hex Blocks tab using interactive selection tools.

---

## ✨ Features

- **Modular Workflow**: 6 dedicated tabs guide you from project setup to 2D sketching, edge definition, hex block creation, and patch assignment.
- **2D Layer-Based Editor**: Design complex profiles with precision using multiple Z-plane layers.
- **Point & Connection Logic**: Manage global points as a single source of truth, ensuring perfect connectivity across blocks.
- **Interactive Patch Assignment**: Assign boundary faces directly on the 3D model with a single click.
- **⚙️ Automake Toggle**: Speed up block creation with the Automake feature—automatically sort 8 points and generate hex blocks.
- **OpenFOAM Optimized**: Export clean, standard-compliant `blockMeshDict` files ready for CFD simulation.
- **Professional Dark Mode**: A sleek, high-contrast, professional-grade interface with refined scrolling and borderless dashboard components.

---

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
2. Install dependencies:
   ```bash
   pip install -r Code/requirements.txt
   ```

---

## 📖 Usage

Run the main application from the `Code` directory:
```bash
cd Code
python main.py
```

### The 6-Step Workflow
1. **Project Settings**: Define units, project name, and coordinate system.
2. **Points & Connections**: Draft your 2D geometry on different layers.
3. **Edge Editor**: Convert straight lines to arcs or splines for curved boundaries.
4. **Hex Blocks**: Group points to form 3D blocks with grading and division controls.
5. **Hex View & Patches**: Inspect your 3D mesh and assign faces to named patches.
6. **Export**: Preview and save your final `blockMeshDict`.

---

## 📁 Project Structure

```text
BlockMeshAuto/
├── Code/
│   ├── main.py                # Application entry point
│   ├── mesh_data.py           # Re-engineered v2.0 Data Layer
│   ├── tab1_projectSettings/  # Project Configuration
│   ├── tab2_2DEditor/         # 2D Sketching Module
│   ├── tab3_Edges/            # Curved Edge Module
│   ├── tab4_Hex/              # Block Generation Module
│   ├── tab5_Patches/          # 3D Renderer & Patch Editor
│   ├── tab6_export/           # OpenFOAM Export Module
│   └── utils/                 # Importer, History Manager, etc.
├── Examples/                  # Sample v2.0 projects
├── Trial Case/                # Integrated OpenFOAM test case
└── README.md                  # You are here
```

---

## 🤝 Contributing
Contributions are welcome! If you have ideas for 3.0 or found a bug, please reach out to me. As a Mechanical/Aerospace Engineer, I am not yet fully aquianted with github pull requests and issues. I aplogize for the inconvinence.

## Contact
Email: [patil.chinmay3031@gmail.com](mailto:patil.chinmay3031@gmail.com)
Linkedin: [Chinmay Patil](https://www.linkedin.com/in/chinmay-shashikant-patil/)

## 📄 License
This project is licensed under the CC0 1.0 Universal License - see the [LICENSE](LICENSE) file for details.
