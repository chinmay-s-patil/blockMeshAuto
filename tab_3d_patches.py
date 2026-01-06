"""
3D View & Patches Tab - Patch Assignment
"""
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from viewer_3d import Viewer3D


class Tab3DPatches:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.face_selection_mode = False
        self.face_sel_mode_var = tk.BooleanVar(value=False)
        self.patch_type_var = tk.StringVar(value="wall")
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: 3D View
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="3D Mesh View", font=("Arial", 12, "bold")).pack()
        
        self.fig_3d = Figure(figsize=(8, 7))
        self.viewer_3d = Viewer3D(self.fig_3d, self.mesh_data)
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(left_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
        toolbar.update()
        
        self.canvas_3d.mpl_connect('button_press_event', self.on_3d_click)
        
        # Right: Controls
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        tk.Button(right_frame, text="🔄 Update 3D View", command=self.update_view,
                 bg="lightgreen", font=("Arial", 11, "bold")).pack(fill=tk.X, padx=5, pady=5)
        
        self._setup_selection_mode(right_frame)
        self._setup_face_selection(right_frame)
        self._setup_patch_assignment(right_frame)
        self._setup_patch_list(right_frame)
        
    def _setup_selection_mode(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Selection Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Checkbutton(mode_frame, text="Enable Face Selection", 
                      variable=self.face_sel_mode_var, 
                      command=self.toggle_face_selection_mode,
                      font=("Arial", 10, "bold")).pack()
        
        self.face_mode_label = tk.Label(mode_frame, text="Face selection disabled", 
                                        font=("Arial", 9), fg="gray")
        self.face_mode_label.pack(pady=5)
    
    def _setup_face_selection(self, parent):
        info_frame = tk.LabelFrame(parent, text="Face Selection", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="Click faces to select", font=("Arial", 9, "italic")).pack()
        self.face_count_label = tk.Label(info_frame, text="Selected: 0 faces", fg="blue")
        self.face_count_label.pack(pady=5)
        
        tk.Button(info_frame, text="Clear Selection", command=self.clear_face_selection).pack(fill=tk.X)
    
    def _setup_patch_assignment(self, parent):
        patch_frame = tk.LabelFrame(parent, text="Assign Patch", padx=10, pady=10)
        patch_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        tk.Label(patch_frame, text="Patch Name:").pack(anchor=tk.W)
        self.patch_name_entry = tk.Entry(patch_frame)
        self.patch_name_entry.pack(fill=tk.X, pady=2)
        
        tk.Label(patch_frame, text="Patch Type:").pack(anchor=tk.W, pady=(10, 0))
        
        patch_types = ["wall", "patch", "symmetry", "symmetryPlane", "wedge", "empty", "cyclic"]
        for ptype in patch_types:
            tk.Radiobutton(patch_frame, text=ptype, variable=self.patch_type_var, 
                          value=ptype).pack(anchor=tk.W)
        
        tk.Button(patch_frame, text="Assign to Selected Faces", 
                 command=self.assign_patch, bg="lightblue").pack(fill=tk.X, pady=10)
    
    def _setup_patch_list(self, parent):
        list_frame = tk.LabelFrame(parent, text="Defined Patches", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.patch_listbox = tk.Listbox(list_frame)
        self.patch_listbox.pack(fill=tk.BOTH, expand=True)
    
    def update_view(self):
        self.viewer_3d.mesh_data = self.mesh_data
        self.viewer_3d.update_view()
        self.canvas_3d.draw()
    
    def toggle_face_selection_mode(self):
        self.face_selection_mode = self.face_sel_mode_var.get()
        if self.face_selection_mode:
            self.face_mode_label.config(text="Face selection enabled - Click faces!", fg="green")
        else:
            self.face_mode_label.config(text="Face selection disabled", fg="gray")
    
    def on_3d_click(self, event):
        if event.inaxes != self.viewer_3d.ax:
            return
        
        if not self.face_selection_mode:
            return
        
        face_idx = self.viewer_3d.pick_face(event.xdata, event.ydata)
        if face_idx is not None:
            self.face_count_label.config(text=f"Selected: {len(self.viewer_3d.selected_faces)} faces")
            self.update_view()
    
    def clear_face_selection(self):
        self.viewer_3d.clear_selection()
        self.face_count_label.config(text="Selected: 0 faces")
        self.update_view()
    
    def assign_patch(self):
        name = self.patch_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Enter patch name")
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