import pyvista as pv
from pyvista import examples

# Load a sample mesh
mesh = examples.load_airplane()

plotter = pv.Plotter()
plotter.add_mesh(mesh, pickable=True)
plotter.enable_path_picking()  # <-- Exactly what you want

# Callback for selection
def callback(face_index):
    print(f"Selected face: {face_index}")

plotter.enable_path_picking(callback=callback, show_message=True)
plotter.show()