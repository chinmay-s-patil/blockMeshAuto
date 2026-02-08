"""
Export Tab - Export to blockMeshDict format
Redesigned with dark mode, better layout, and three tabs:
- Actions: Export buttons and quick preview
- Summary: Mesh statistics and cell counts
- Details: List of patches, hexes, and edges
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import numpy as np


class TabExport:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Dark mode colors - MATCHING OTHER TABS
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'accent': '#007acc',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f44747',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'button_active': '#1177bb',
            'border': '#3e3e42',
            'text_bg': '#2d2d2d',
            'text_fg': '#d4d4d4',
            'canvas_bg': '#1e1e1e',
            'grid': '#3e3e42'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the export interface with new layout"""
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(main_frame, text="Export to blockMeshDict", 
                font=("Arial", 16, "bold"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=(0, 15))
        
        # Main content area - split into left (preview) and right (tabs)
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # LEFT: Quick Preview (always visible)
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        preview_label = tk.Label(left_frame, text="Quick Preview", 
                                font=("Arial", 12, "bold"),
                                bg=self.colors['bg'], fg=self.colors['accent'])
        preview_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Preview text with dark theme
        preview_container = tk.Frame(left_frame, bg=self.colors['border'], bd=1)
        preview_container.pack(fill=tk.BOTH, expand=True)
        
        scroll_y = tk.Scrollbar(preview_container, bg=self.colors['secondary'])
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = tk.Scrollbar(preview_container, orient=tk.HORIZONTAL, bg=self.colors['secondary'])
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.preview_text = tk.Text(preview_container, 
                                   height=20, 
                                   font=("Consolas", 9),
                                   bg=self.colors['text_bg'],
                                   fg=self.colors['text_fg'],
                                   insertbackground=self.colors['fg'],
                                   yscrollcommand=scroll_y.set,
                                   xscrollcommand=scroll_x.set,
                                   wrap=tk.NONE,
                                   relief=tk.FLAT)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        scroll_y.config(command=self.preview_text.yview)
        scroll_x.config(command=self.preview_text.xview)
        
        # Refresh preview button below preview
        tk.Button(left_frame, text="Refresh Preview", 
                 command=self.update_preview,
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 font=("Arial", 9), 
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(fill=tk.X, pady=(10, 0))
        
        # RIGHT: Notebook with tabs
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Create styled notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors['secondary'])
        style.configure("TNotebook.Tab", 
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=("Arial", 9, "bold"))
        style.map("TNotebook.Tab", 
                 background=[("selected", self.colors['accent'])],
                 foreground=[("selected", self.colors['button_fg'])])
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_actions = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_summary = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_details = tk.Frame(self.notebook, bg=self.colors['secondary'])
        
        self.notebook.add(self.tab_actions, text="Actions")
        self.notebook.add(self.tab_summary, text="Summary")
        self.notebook.add(self.tab_details, text="Details")
        
        # Setup each tab
        self._setup_actions_tab()
        self._setup_summary_tab()
        self._setup_details_tab()
        
        # Initial update
        self.update_preview()
        self.update_summary()
        self.update_details()
        
    def _setup_actions_tab(self):
        """Setup the Actions tab with export buttons"""
        frame = tk.Frame(self.tab_actions, bg=self.colors['secondary'], padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(frame, text="Export Actions", 
                font=("Arial", 12, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 15))
        
        # Export buttons
        btn_configs = [
            ("Export to File", self.export_blockmesh, self.colors['success'], '#3db89f'),
            ("Copy to Clipboard", self.copy_to_clipboard, self.colors['accent'], self.colors['button_active']),
        ]
        
        for text, command, bg, active_bg in btn_configs:
            btn = tk.Button(frame, text=text, 
                           command=command,
                           bg=bg, 
                           fg=self.colors['button_fg'] if bg != self.colors['success'] else self.colors['bg'],
                           font=("Arial", 10, "bold"), 
                           relief=tk.FLAT,
                           activebackground=active_bg,
                           height=2)
            btn.pack(fill=tk.X, pady=5)
        
        # Separator
        tk.Frame(frame, bg=self.colors['border'], height=2).pack(fill=tk.X, pady=15)
        
        # Quick info
        tk.Label(frame, text="Mesh Info", 
                font=("Arial", 11, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 10))
        
        self.quick_info_label = tk.Label(frame, text="", 
                                        font=("Courier", 10),
                                        bg=self.colors['secondary'], 
                                        fg=self.colors['text_fg'],
                                        justify=tk.LEFT)
        self.quick_info_label.pack(anchor=tk.W)
        
        # Validation warnings
        self.validation_label = tk.Label(frame, text="", 
                                        font=("Arial", 9),
                                        fg=self.colors['warning'],
                                        bg=self.colors['secondary'],
                                        wraplength=300,
                                        justify=tk.LEFT)
        self.validation_label.pack(anchor=tk.W, pady=(15, 0))
        
    def _setup_summary_tab(self):
        """Setup the Summary tab with statistics"""
        frame = tk.Frame(self.tab_summary, bg=self.colors['secondary'], padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(frame, text="Mesh Statistics", 
                font=("Arial", 12, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 15))
        
        # Statistics display
        self.stats_text = tk.Text(frame, 
                                 font=("Consolas", 10),
                                 bg=self.colors['text_bg'],
                                 fg=self.colors['text_fg'],
                                 relief=tk.FLAT,
                                 height=15,
                                 wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.config(state=tk.DISABLED)
        
        # Refresh button
        tk.Button(frame, text="Refresh Statistics", 
                 command=self.update_summary,
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 font=("Arial", 9), 
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(fill=tk.X, pady=(10, 0))
        
    def _setup_details_tab(self):
        """Setup the Details tab with patches, hexes, edges lists"""
        frame = tk.Frame(self.tab_details, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for sub-tabs
        sub_notebook = ttk.Notebook(frame)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sub-tabs
        tab_patches = tk.Frame(sub_notebook, bg=self.colors['secondary'])
        tab_hexes = tk.Frame(sub_notebook, bg=self.colors['secondary'])
        tab_edges = tk.Frame(sub_notebook, bg=self.colors['secondary'])
        
        sub_notebook.add(tab_patches, text="Patches")
        sub_notebook.add(tab_hexes, text="Hex Blocks")
        sub_notebook.add(tab_edges, text="Edges")
        
        # Patches list
        self._create_list_view(tab_patches, "patches")
        
        # Hex blocks list
        self._create_list_view(tab_hexes, "hexes")
        
        # Edges list
        self._create_list_view(tab_edges, "edges")
        
    def _create_list_view(self, parent, list_type):
        """Create a list view with scrollbar for details"""
        container = tk.Frame(parent, bg=self.colors['secondary'])
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Header
        headers = {
            'patches': ('Patch Name', 'Type', 'Faces'),
            'hexes': ('Block #', 'Divisions', 'Cells'),
            'edges': ('Edge #', 'Type', 'Points')
        }
        
        header_frame = tk.Frame(container, bg=self.colors['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        for i, header in enumerate(headers.get(list_type, ('Item', 'Info'))):
            tk.Label(header_frame, text=header, 
                    font=("Arial", 9, "bold"),
                    bg=self.colors['secondary'], 
                    fg=self.colors['accent'],
                    width=15 if i == 0 else 12).pack(side=tk.LEFT)
        
        # List with scrollbar
        list_frame = tk.Frame(container, bg=self.colors['border'], bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, bg=self.colors['secondary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, 
                            font=("Consolas", 9),
                            bg=self.colors['text_bg'],
                            fg=self.colors['text_fg'],
                            selectbackground=self.colors['accent'],
                            selectforeground=self.colors['button_fg'],
                            yscrollcommand=scrollbar.set,
                            relief=tk.FLAT)
        listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=listbox.yview)
        
        # Store reference
        setattr(self, f'{list_type}_listbox', listbox)
        
        # Refresh button
        tk.Button(container, text="Refresh", 
                 command=lambda: self.update_details(),
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 font=("Arial", 8), 
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(fill=tk.X, pady=(5, 0))
        
    def update_preview(self):
        """Update the preview text - REFRESHES IN PLACE"""
        content = self.generate_blockmesh_dict()
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', content)
        
        # Also update quick info
        self._update_quick_info()
        self._update_validation()
        
    def _update_quick_info(self):
        """Update quick info in Actions tab"""
        total_points = self.mesh_data.get_total_points()
        total_layers = len(self.mesh_data.layers)
        total_hex_blocks = len(self.mesh_data.hex_blocks)
        total_patches = len(self.mesh_data.patches)
        
        info_text = f"""Points:     {total_points}
Layers:     {total_layers}
Hex Blocks: {total_hex_blocks}
Patches:    {total_patches}
Scale:      {self.mesh_data.get_scale_value()}
Units:      {self.mesh_data.unit_system}"""
        
        self.quick_info_label.config(text=info_text)
        
    def _update_validation(self):
        """Update validation warnings"""
        issues = self.validate_hex_blocks()
        if issues:
            self.validation_label.config(
                text="Warnings:\\n" + "\\n".join(f"  - {issue}" for issue in issues[:3])
            )
        else:
            self.validation_label.config(text="No validation issues", fg=self.colors['success'])
            
    def update_summary(self):
        """Update the Summary tab with statistics"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        
        # Calculate total cells
        total_cells = 0
        hex_details = []
        
        for i, block in enumerate(self.mesh_data.hex_blocks):
            nx, ny, nz = block['divisions']
            cells = nx * ny * nz
            total_cells += cells
            hex_details.append(f"Block {i}: {nx} x {ny} x {nz} = {cells:,} cells")
        
        # Build summary text
        summary = []
        summary.append("=" * 40)
        summary.append("MESH OVERVIEW")
        summary.append("=" * 40)
        summary.append("")
        summary.append(f"Total Vertices:     {self.mesh_data.get_total_points():,}")
        summary.append(f"Total Layers:       {len(self.mesh_data.layers)}")
        summary.append(f"Total Hex Blocks:   {len(self.mesh_data.hex_blocks)}")
        summary.append(f"Total Patches:      {len(self.mesh_data.patches)}")
        summary.append("")
        summary.append("=" * 40)
        summary.append("CELL COUNT")
        summary.append("=" * 40)
        summary.append("")
        
        if hex_details:
            for detail in hex_details:
                summary.append(detail)
            summary.append("")
            summary.append(f"{'-' * 40}")
            summary.append(f"TOTAL CELLS:        {total_cells:,}")
        else:
            summary.append("No hex blocks defined")
            
        summary.append("")
        summary.append("=" * 40)
        summary.append("SCALE & UNITS")
        summary.append("=" * 40)
        summary.append("")
        summary.append(f"Scale Factor:       {self.mesh_data.get_scale_value()}")
        summary.append(f"Unit System:        {self.mesh_data.unit_system}")
        summary.append(f"Project Name:       {self.mesh_data.project_name}")
        
        self.stats_text.insert('1.0', '\\n'.join(summary))
        self.stats_text.config(state=tk.DISABLED)
        
    def update_details(self):
        """Update the Details tab lists"""
        # Update patches list
        if hasattr(self, 'patches_listbox'):
            self.patches_listbox.delete(0, tk.END)
            if hasattr(self.mesh_data, 'patches'):
                for patch_name, patch_data in self.mesh_data.patches.items():
                    if isinstance(patch_data, dict):
                        ptype = patch_data.get('type', 'unknown')
                        num_faces = len(patch_data.get('faces', []))
                    else:
                        # Handle tuple format for backward compatibility
                        ptype = patch_data[1] if len(patch_data) > 1 else 'unknown'
                        num_faces = len(patch_data[2]) if len(patch_data) > 2 else 0
                    self.patches_listbox.insert(tk.END, f"{patch_name:<15} {ptype:<12} {num_faces}")
        
        # Update hexes list
        if hasattr(self, 'hexes_listbox'):
            self.hexes_listbox.delete(0, tk.END)
            for i, block in enumerate(self.mesh_data.hex_blocks):
                nx, ny, nz = block['divisions']
                cells = nx * ny * nz
                self.hexes_listbox.insert(tk.END, f"Block {i:<11} {nx}x{ny}x{nz:<6} {cells:,}")
        
        # Update edges list
        if hasattr(self, 'edges_listbox'):
            self.edges_listbox.delete(0, tk.END)
            # For now, show block edges as simple info
            for i, block in enumerate(self.mesh_data.hex_blocks):
                verts = block.get('vertices', [])
                self.edges_listbox.insert(tk.END, f"Block {i:<11} hex          {len(verts)} verts")
        
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
                issues.append(f"Block {i}: bottom face Z > top face Z")
            
            # Check for duplicate vertices
            if len(set(point_refs)) != 8:
                issues.append(f"Block {i}: has duplicate vertex references")
        
        return issues
    
    def generate_blockmesh_dict(self):
        """Generate the complete blockMeshDict content"""
        lines = []
        lines.append("/*--------------------------------*- C++ -*----------------------------------*\\\\")
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
        
        for patch_name, patch_data in self.mesh_data.patches.items():
            # Handle both dict and tuple formats
            if isinstance(patch_data, dict):
                patch_type = patch_data.get('type', 'patch')
                face_indices = patch_data.get('faces', [])
            else:
                patch_type = patch_data[1] if len(patch_data) > 1 else 'patch'
                face_indices = patch_data[2] if len(patch_data) > 2 else []
            
            lines.append(f"    {patch_name}")
            lines.append("    {")
            lines.append(f"        type {patch_type};")
            lines.append("        faces")
            lines.append("        (")
            
            for face in face_indices:
                if isinstance(face, (list, tuple)) and len(face) == 4:
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
        
        return '\\n'.join(lines)
    
    def export_blockmesh(self):
        """Export to blockMeshDict file"""
        if not self.mesh_data.hex_blocks:
            messagebox.showwarning("Warning", "No hex blocks defined! Create blocks in Tab 4 first.")
            return
        
        # Validate before export
        issues = self.validate_hex_blocks()
        if issues:
            result = messagebox.askyesno("Validation Warning", 
                                        "There are issues with your hex blocks:\\n\\n" + 
                                        "\\n".join(f"- {issue}" for issue in issues) +
                                        "\\n\\nExport anyway?")
            if not result:
                return
        
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
                messagebox.showinfo("Success", f"blockMeshDict exported to:\\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def copy_to_clipboard(self):
        """Copy content to clipboard"""
        content = self.generate_blockmesh_dict()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied", "blockMeshDict content copied to clipboard!")