"""
3D View & Patches Tab - Patch Assignment using Plotly
"""
import tkinter as tk
from tkinter import messagebox
from viewer_3d import Viewer3D


class Tab3DPatches:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.face_selection_mode = False
        self.face_sel_mode_var = tk.BooleanVar(value=False)
        self.patch_type_var = tk.StringVar(value="wall")
        
        # Viewer
        self.viewer_3d = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View placeholder
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Mesh View", font=("Arial", 12, "bold")).pack()
        
        # Info label
        info_label = tk.Label(left_frame, 
                             text="Click 'Update 3D View' to load the visualization",
                             font=("Arial", 10, "italic"), fg="gray")
        info_label.pack(pady=10)
        
        # Placeholder for 3D view
        self.plot_frame = tk.Frame(left_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.plot_label = tk.Label(self.plot_frame, 
                                   text="3D View will appear here\n\nClick 'Update 3D View' button",
                                   font=("Arial", 12), fg="gray", bg="white")
        self.plot_label.pack(expand=True)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update 3D View", command=self.update_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(right_frame, text="📊 Open Interactive View", command=self.open_interactive_view,
                 bg="lightblue", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        self._setup_selection_mode(right_frame)
        self._setup_face_list(right_frame)
        self._setup_patch_assignment(right_frame)
        self._setup_patch_list(right_frame)
        
    def _setup_selection_mode(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Selection Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(mode_frame, text="Select faces from the list below,\nthen assign to a patch",
                font=("Arial", 9), fg="gray").pack(pady=5)
        
        self.face_count_label = tk.Label(mode_frame, text="Selected: 0 faces", 
                                         fg="blue", font=("Arial", 10, "bold"))
        self.face_count_label.pack(pady=5)
        
        tk.Button(mode_frame, text="Clear Selection", 
                 command=self.clear_face_selection).pack(fill=tk.X, pady=5)
    
    def _setup_face_list(self, parent):
        list_frame = tk.LabelFrame(parent, text="Available Faces (Ctrl+Click to multi-select)", 
                                  padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.face_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED,
                                       yscrollcommand=scrollbar.set,
                                       font=("Courier", 8))
        self.face_listbox.pack(fill=tk.BOTH, expand=True)
        self.face_listbox.bind('<<ListboxSelect>>', self.on_face_select)
        
        scrollbar.config(command=self.face_listbox.yview)
    
    def _setup_patch_assignment(self, parent):
        patch_frame = tk.LabelFrame(parent, text="Assign Patch", padx=10, pady=10)
        patch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(patch_frame, text="Patch Name:").pack(anchor=tk.W)
        self.patch_name_entry = tk.Entry(patch_frame)
        self.patch_name_entry.pack(fill=tk.X, pady=2)
        
        tk.Label(patch_frame, text="Patch Type:").pack(anchor=tk.W, pady=(10, 0))
        
        patch_types = ["wall", "patch", "symmetry", "symmetryPlane", "wedge", "empty", "cyclic"]
        for ptype in patch_types:
            tk.Radiobutton(patch_frame, text=ptype, variable=self.patch_type_var, 
                          value=ptype).pack(anchor=tk.W)
        
        tk.Button(patch_frame, text="Assign to Selected Faces", 
                 command=self.assign_patch, bg="lightblue",
                 font=("Arial", 10, "bold")).pack(fill=tk.X, pady=10)
    
    def _setup_patch_list(self, parent):
        list_frame = tk.LabelFrame(parent, text="Defined Patches", padx=10, pady=10)
        list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.patch_listbox = tk.Listbox(list_frame, height=6)
        self.patch_listbox.pack(fill=tk.X)
    
    def update_view(self):
        """Generate 3D visualization"""
        # Check if we have geometry
        all_points = []
        for layer in sorted(self.mesh_data.layers.keys(), key=lambda l: self.mesh_data.layers[l]):
            for x, y in self.mesh_data.points[layer]:
                all_points.append((x, y))
        
        if not all_points:
            messagebox.showinfo("No Geometry", 
                              "No points to display. Add geometry in Tab 2 first.")
            return
        
        # Create viewer
        self.viewer_3d = Viewer3D(self.plot_frame, self.mesh_data)
        fig = self.viewer_3d.update_view()
        
        # Update face listbox
        self.update_face_list()
        
        # Show message
        num_faces = len(self.viewer_3d.pickable_faces)
        self.plot_label.config(
            text=f"✓ {num_faces} faces loaded\n\n"
                 "Click 'Open Interactive View' button\n"
                 "to see the 3D visualization\n\n"
                 "Select faces from the list below"
        )
        
        messagebox.showinfo("View Updated", 
                          f"Loaded {num_faces} faces.\n\n"
                          "Click 'Open Interactive View' to see 3D visualization,\n"
                          "or select faces from the list below.")
    
    def update_face_list(self):
        """Update the face listbox"""
        self.face_listbox.delete(0, tk.END)
        
        if self.viewer_3d is None:
            return
        
        for i, face_verts in enumerate(self.viewer_3d.pickable_faces):
            # Calculate face center for description
            center_x = sum(v[0] for v in face_verts) / len(face_verts)
            center_y = sum(v[1] for v in face_verts) / len(face_verts)
            center_z = sum(v[2] for v in face_verts) / len(face_verts)
            
            line = f"Face {i:3d}: center=({center_x:6.2f}, {center_y:6.2f}, {center_z:6.2f})"
            self.face_listbox.insert(tk.END, line)
    
    def on_face_select(self, event):
        """Handle face selection from listbox"""
        if self.viewer_3d is None:
            return
        
        # Get all selected indices
        selected_indices = self.face_listbox.curselection()
        
        # Update viewer's selected faces
        self.viewer_3d.selected_faces = set(selected_indices)
        
        # Update count label
        self.face_count_label.config(text=f"Selected: {len(selected_indices)} faces")
    
    def open_interactive_view(self):
        """Open the Plotly figure in a browser"""
        if self.viewer_3d is None or self.viewer_3d.fig is None:
            messagebox.showwarning("No View", 
                                 "Click 'Update 3D View' first to generate the visualization")
            return
        
        # Show in browser
        self.viewer_3d.fig.show()
    
    def clear_face_selection(self):
        if self.viewer_3d:
            self.viewer_3d.clear_selection()
        self.face_listbox.selection_clear(0, tk.END)
        self.face_count_label.config(text="Selected: 0 faces")
    
    def assign_patch(self):
        name = self.patch_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Enter patch name")
            return
        
        if self.viewer_3d is None:
            messagebox.showwarning("Warning", "Update 3D view first")
            return
        
        patch_type = self.patch_type_var.get()
        selected = self.viewer_3d.get_selected_faces()
        
        if not selected:
            messagebox.showwarning("Warning", "No faces selected")
            return
        
        self.viewer_3d.assign_patch_to_selected(name, patch_type)
        self.mesh_data.add_patch(name, patch_type, selected)
        
        self.patch_listbox.insert(tk.END, f"{name} ({patch_type}) - {len(selected)} faces")
        self.patch_name_entry.delete(0, tk.END)
        self.clear_face_selection()
        
        messagebox.showinfo("Success", 
                          f"Assigned {len(selected)} faces to patch '{name}' ({patch_type})")