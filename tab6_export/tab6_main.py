"""
Export Tab - Export to blockMeshDict format
Includes hex blocks, patches, and all mesh data
"""
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import os
import numpy as np


class TabExport:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the export interface"""
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(main_frame, text="Export blockMeshDict", 
                font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Summary frame
        summary_frame = tk.LabelFrame(main_frame, text="Mesh Summary", padx=10, pady=10)
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.summary_label = tk.Label(summary_frame, text="", justify=tk.LEFT,
                                     font=("Courier", 10))
        self.summary_label.pack(anchor=tk.W)
        
        # Hex Blocks summary
        self.hex_summary = tk.Label(summary_frame, text="", justify=tk.LEFT,
                                   font=("Courier", 10), fg="blue")
        self.hex_summary.pack(anchor=tk.W, pady=(10, 0))
        
        # Validation warnings
        self.validation_label = tk.Label(summary_frame, text="", justify=tk.LEFT,
                                        font=("Courier", 9), fg="red", wraplength=700)
        self.validation_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Button frame
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        # Preview button (new)
        tk.Button(btn_frame, text="👁 Preview", command=self.preview_blockmesh,
                 bg="lightyellow", font=("Arial", 10, "bold"), height=2).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Export button
        tk.Button(btn_frame, text="📄 Export blockMeshDict", command=self.export_blockmesh,
                 bg="lightgreen", font=("Arial", 10, "bold"), height=2).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Copy button
        tk.Button(btn_frame, text="📋 Copy to Clipboard", command=self.copy_to_clipboard,
                 bg="lightblue", font=("Arial", 10), height=2).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Quick preview text (always visible)
        preview_frame = tk.LabelFrame(main_frame, text="Quick Preview", padx=5, pady=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = tk.Scrollbar(preview_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_text = tk.Text(preview_frame, height=15, font=("Courier", 9),
                                   yscrollcommand=scroll.set, wrap=tk.NONE)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.preview_text.yview)
        
        # Update display
        self.update_summary()
        
    def update_summary(self):
        """Update the summary display"""
        total_points = self.mesh_data.get_total_points()
        total_layers = len(self.mesh_data.layers)
        total_hex_blocks = len(self.mesh_data.hex_blocks)
        total_patches = len(self.mesh_data.patches)
        
        summary_text = f"""Points:     {total_points}
Layers:     {total_layers}
Hex Blocks: {total_hex_blocks}
Patches:    {total_patches}
Scale:      {self.mesh_data.get_scale_value()}
Units:      {self.mesh_data.unit_system}"""
        
        self.summary_label.config(text=summary_text)
        
        # Hex blocks details
        if total_hex_blocks > 0:
            hex_text = "\nHex Blocks:\n"
            for i, block in enumerate(self.mesh_data.hex_blocks):
                nx, ny, nz = block['divisions']
                hex_text += f"  Block {i}: {nx}×{ny}×{nz} cells\n"
            self.hex_summary.config(text=hex_text)
        else:
            self.hex_summary.config(text="\nNo hex blocks defined yet")
        
        # Run validation
        issues = self.validate_hex_blocks()
        if issues:
            self.validation_label.config(text="⚠️ Warnings:\n" + "\n".join(f"  • {issue}" for issue in issues))
        else:
            self.validation_label.config(text="")
        
        # Update preview
        self.update_preview()
    
    def validate_hex_blocks(self):
        """Check if hex blocks have valid vertex ordering"""
        issues = []
        for i, block in enumerate(self.mesh_data.hex_blocks):
            verts = block.get('vertices', [])
            point_refs = block.get('point_refs', [])
            
            if len(verts) != 8:
                issues.append(f"Block {i}: has {len(verts)} vertices, expected 8")
                continue
            
            if len(point_refs) != 8:
                issues.append(f"Block {i}: has {len(point_refs)} point refs, expected 8")
                continue
            
            # Check if bottom face is actually below top face
            z_bottom = [v[2] for v in verts[0:4]]
            z_top = [v[2] for v in verts[4:8]]
            
            if max(z_bottom) > min(z_top):
                issues.append(f"Block {i}: bottom face Z > top face Z - vertices may be twisted!")
            
            # Check for duplicate vertices
            if len(set(point_refs)) != 8:
                issues.append(f"Block {i}: has duplicate vertex references")
        
        return issues
    
    def update_preview(self):
        """Update the preview text"""
        content = self.generate_blockmesh_dict()
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', content)
    
    def preview_blockmesh(self):
        """Open a larger preview window"""
        preview_window = tk.Toplevel(self.parent)
        preview_window.title("blockMeshDict Preview")
        preview_window.geometry("900x700")
        
        # Make it modal
        preview_window.transient(self.parent)
        preview_window.grab_set()
        
        # Title
        tk.Label(preview_window, text="blockMeshDict Preview", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Info frame
        info_frame = tk.Frame(preview_window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(info_frame, text=f"Project: {self.mesh_data.project_name}", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Label(info_frame, text=f"Blocks: {len(self.mesh_data.hex_blocks)}", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Label(info_frame, text=f"Vertices: {self.mesh_data.get_total_points()}", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Scrolled text for content
        text_widget = scrolledtext.ScrolledText(preview_window, wrap=tk.NONE, 
                                               font=("Courier", 10), 
                                               bg='#f5f5f5', fg='#333333')
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Insert content
        content = self.generate_blockmesh_dict()
        text_widget.insert('1.0', content)
        text_widget.config(state=tk.DISABLED)  # Read-only
        
        # Button frame
        btn_frame = tk.Frame(preview_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="📋 Copy to Clipboard", 
                 command=lambda: self._copy_from_preview(text_widget),
                 bg="lightblue", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📄 Export to File...", 
                 command=lambda: [preview_window.destroy(), self.export_blockmesh()],
                 bg="lightgreen", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Close", 
                 command=preview_window.destroy,
                 bg="salmon", font=("Arial", 10)).pack(side=tk.RIGHT, padx=5)
        
        # Validation warnings in preview
        issues = self.validate_hex_blocks()
        if issues:
            warn_frame = tk.LabelFrame(preview_window, text="⚠️ Validation Warnings", 
                                      fg="red", padx=10, pady=5)
            warn_frame.pack(fill=tk.X, padx=10, pady=5, before=text_widget)
            
            for issue in issues:
                tk.Label(warn_frame, text=f"• {issue}", fg="red", 
                        font=("Arial", 9), justify=tk.LEFT).pack(anchor=tk.W)
    
    def _copy_from_preview(self, text_widget):
        """Copy content from preview window"""
        content = text_widget.get('1.0', tk.END)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")
    
    def generate_blockmesh_dict(self):
        """Generate the complete blockMeshDict content"""
        lines = []
        lines.append("/*--------------------------------*- C++ -*----------------------------------*\\")
        lines.append("| =========                 |                                                 |")
        lines.append("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |")
        lines.append("|  \\\\    /   O peration     | Version:  v2012                                 |")
        lines.append("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |")
        lines.append("|    \\\\/     M anipulation  |                                                 |")
        lines.append("\\*---------------------------------------------------------------------------*/")
        lines.append("FoamFile")
        lines.append("{")
        lines.append("    version     2.0;")
        lines.append("    format      ascii;")
        lines.append("    class       dictionary;")
        lines.append("    object      blockMeshDict;")
        lines.append("}")
        lines.append("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //")
        lines.append("")
        
        # Scale
        scale = self.mesh_data.get_scale_value()
        lines.append(f"scale   {scale};")
        lines.append("")
        
        # Vertices
        lines.append("vertices")
        lines.append("(")
        
        # Get all points in order
        points_3d, point_map = self.mesh_data.get_all_3d_points()
        
        for i, coords in enumerate(points_3d):
            x, y, z = coords
            lines.append(f"    ( {x:.6f} {y:.6f} {z:.6f} )  // point {i}")
        
        lines.append(");")
        lines.append("")
        
        # Blocks (hex blocks)
        lines.append("blocks")
        lines.append("(")
        
        for i, block in enumerate(self.mesh_data.hex_blocks):
            point_refs = block.get('point_refs', [])
            if len(point_refs) != 8:
                continue
            
            p = point_refs
            lines.append(f"    hex ({p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]} {p[7]})")
            
            nx, ny, nz = block['divisions']
            grading_type = block.get('grading_type', 'simpleGrading')
            grading_params = block.get('grading_params', {'x': 1.0, 'y': 1.0, 'z': 1.0})
            
            if grading_type == 'simpleGrading':
                gx = grading_params.get('x', 1.0)
                gy = grading_params.get('y', 1.0)
                gz = grading_params.get('z', 1.0)
                lines.append(f"        ({nx} {ny} {nz})")
                lines.append(f"        simpleGrading ({gx} {gy} {gz})")
            else:
                lines.append(f"        ({nx} {ny} {nz})")
                lines.append(f"        {grading_type} (1 1 1)")
            
            lines.append(f"        // Block {i}")
        
        lines.append(");")
        lines.append("")
        
        # Edges
        lines.append("edges")
        lines.append("(")
        lines.append(");")
        lines.append("")
        
        # Patches
        lines.append("boundary")
        lines.append("(")
        
        for patch_name, patch_type, face_indices in self.mesh_data.patches:
            lines.append(f"    {patch_name}")
            lines.append("    {")
            lines.append(f"        type {patch_type};")
            lines.append("        faces")
            lines.append("        (")
            
            for face in face_indices:
                if len(face) == 4:
                    lines.append(f"            ({face[0]} {face[1]} {face[2]} {face[3]})")
            
            lines.append("        );")
            lines.append("    }")
        
        lines.append(");")
        lines.append("")
        
        # Merge patch pairs
        lines.append("mergePatchPairs")
        lines.append("(")
        lines.append(");")
        lines.append("")
        lines.append("// ************************************************************************* //")
        
        return '\n'.join(lines)
    
    def export_blockmesh(self):
        """Export to blockMeshDict file"""
        if not self.mesh_data.hex_blocks:
            messagebox.showwarning("Warning", "No hex blocks defined! Create blocks in Tab 3 first.")
            return
        
        # Validate before export
        issues = self.validate_hex_blocks()
        if issues:
            result = messagebox.askyesno("Validation Warning", 
                                        "There are issues with your hex blocks:\n\n" + 
                                        "\n".join(f"• {issue}" for issue in issues) +
                                        "\n\nExport anyway?")
            if not result:
                return
        
        default_name = self.mesh_data.get_safe_project_name()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".dict",
            filetypes=[("blockMeshDict", "blockMeshDict"), ("Dictionary files", "*.dict"), ("All files", "*.*")],
            initialfile="blockMeshDict"
        )
        
        if filename:
            try:
                content = self.generate_blockmesh_dict()
                with open(filename, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"blockMeshDict exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def copy_to_clipboard(self):
        """Copy content to clipboard"""
        content = self.generate_blockmesh_dict()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied", "blockMeshDict content copied to clipboard!")