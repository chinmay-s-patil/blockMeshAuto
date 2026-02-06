"""
Export Tab - blockMeshDict Export
"""
import tkinter as tk
from tkinter import messagebox, filedialog
from blockmesh_export import BlockMeshExporter


class TabExport:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Export to blockMeshDict", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Summary info
        info_text = tk.Text(main_frame, height=15, width=80)
        info_text.pack(pady=10)
        info_text.insert("1.0", "Summary:\n\n")
        info_text.insert("end", "This will generate an OpenFOAM blockMeshDict file.\n\n")
        info_text.insert("end", "Current mesh:\n")
        info_text.insert("end", f"  Layers: {len(self.mesh_data.layers)}\n")
        info_text.insert("end", f"  Total points: {sum(len(pts) for pts in self.mesh_data.points.values())}\n")
        info_text.insert("end", f"  Patches defined: {len(self.mesh_data.patches)}\n")
        info_text.config(state=tk.DISABLED)
        
        self.export_info = info_text
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Generate & Preview", command=self.preview_blockmesh,
                 bg="lightblue", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save to File", command=self.save_blockmesh,
                 bg="lightgreen", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        # Preview text
        self.preview_text = tk.Text(main_frame, height=20, width=100, font=("Courier", 9))
        scrollbar = tk.Scrollbar(main_frame, command=self.preview_text.yview)
        self.preview_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
    
    def update_summary(self):
        """Update the summary information"""
        self.export_info.config(state=tk.NORMAL)
        self.export_info.delete("1.0", tk.END)
        self.export_info.insert("1.0", "Summary:\n\n")
        self.export_info.insert("end", "This will generate an OpenFOAM blockMeshDict file.\n\n")
        self.export_info.insert("end", "Current mesh:\n")
        self.export_info.insert("end", f"  Layers: {len(self.mesh_data.layers)}\n")
        self.export_info.insert("end", f"  Total points: {sum(len(pts) for pts in self.mesh_data.points.values())}\n")
        self.export_info.insert("end", f"  Patches defined: {len(self.mesh_data.patches)}\n")
        self.export_info.config(state=tk.DISABLED)
    
    def preview_blockmesh(self):
        exporter = BlockMeshExporter(self.mesh_data)
        content = exporter.generate_blockmesh_dict()
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content)
        self.preview_text.config(state=tk.DISABLED)
        
        self.update_summary()
    
    def save_blockmesh(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("blockMeshDict", "blockMeshDict"), ("All files", "*.*")],
            initialfile="blockMeshDict"
        )
        
        if filename:
            exporter = BlockMeshExporter(self.mesh_data)
            exporter.save_to_file(filename)
            messagebox.showinfo("Success", f"Saved to {filename}")