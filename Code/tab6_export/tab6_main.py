"""
Export Tab - Export to blockMeshDict format
Redesigned with dark mode, better layout, and three tabs:
- Actions: Export buttons and quick preview
- Summary: Mesh statistics and cell counts (IMPROVED!)
- Details: List of patches, hexes, and edges
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import sys
import numpy as np

# Import the new components
# sys.path.insert(0, os.path.dirname(__file__))
from tab6_export.stat_card import StatCard
from tab6_export.details_panel import MeshDetailsPanel, InfoBox


class TabExport:
    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        
        # Dark mode colors - MATCHING OTHER TABS
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'secondary': '#252526',
            'card_bg': '#2d2d30',
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
            'grid': '#3e3e42',
            'axis': '#6e6e6e'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the export interface with new layout"""
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout the main split: right panel first, then left panel
        
        # RIGHT: Notebook with tabs
        right_frame = tk.Frame(main_frame, bg=self.colors['bg'], width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # LEFT: Main viewing area
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Unified Header inside left frame
        header_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header_frame, text="6. Generate blockMeshDict", 
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Review setup and export OpenFOAM configuration", 
                 font=("Segoe UI", 10, "italic"), fg=self.colors['axis'],
                 bg=self.colors['bg']).pack(side=tk.LEFT, padx=15, pady=(4,0))
                 
        # Status indicator (moved into the new header_frame)
        self.status_label = tk.Label(header_frame, text="● Ready", 
                                     font=("Segoe UI", 10),
                                     bg=self.colors['bg'], fg=self.colors['success'])
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Content frame for text area inside left frame
        content_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # LEFT: Quick Preview (always visible) - now inside the new content_frame
        preview_header = tk.Frame(content_frame, bg=self.colors['bg'])
        preview_header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(preview_header, text="📄 Quick Preview", 
                font=("Segoe UI", 13, "bold"),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(side=tk.LEFT)
        
        # Line count indicator
        self.line_count_label = tk.Label(preview_header, text="0 lines", 
                                         font=("Segoe UI", 9),
                                         bg=self.colors['bg'], fg=self.colors['fg'])
        self.line_count_label.pack(side=tk.RIGHT)
        
        # Preview text with dark theme
        preview_container = tk.Frame(content_frame, bg=self.colors['border'], bd=1)
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
        btn_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="🔄 Refresh Preview", 
                 command=self.update_preview,
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 font=("Segoe UI", 9, "bold"), 
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active'],
                 cursor="hand2",
                 padx=15, pady=6).pack(side=tk.LEFT)
        
        # Create styled notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors['secondary'], borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       font=("Segoe UI", 10, "bold"),
                       padding=[15, 8])
        style.map("TNotebook.Tab", 
                 background=[("selected", self.colors['accent'])],
                 foreground=[("selected", self.colors['button_fg'])])
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_actions = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_summary = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.tab_details = tk.Frame(self.notebook, bg=self.colors['secondary'])
        
        self.notebook.add(self.tab_actions, text="⚡ Actions")
        self.notebook.add(self.tab_summary, text="📊 Summary")
        self.notebook.add(self.tab_details, text="📋 Details")
        
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
                font=("Segoe UI", 13, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 15))
        
        # Export buttons with icons
        btn_configs = [
            ("💾 Export to File", self.export_blockmesh, self.colors['success'], '#3db89f'),
            ("📋 Copy to Clipboard", self.copy_to_clipboard, self.colors['accent'], self.colors['button_active']),
        ]
        
        for text, command, bg, active_bg in btn_configs:
            btn = tk.Button(frame, text=text, 
                           command=command,
                           bg=bg, 
                           fg=self.colors['button_fg'] if bg != self.colors['success'] else self.colors['bg'],
                           font=("Segoe UI", 11, "bold"), 
                           relief=tk.FLAT,
                           activebackground=active_bg,
                           cursor="hand2",
                           padx=20,
                           pady=12)
            btn.pack(fill=tk.X, pady=5)
        
        # Separator
        tk.Frame(frame, bg=self.colors['border'], height=2).pack(fill=tk.X, pady=20)
        
        # Quick info box
        info_box = InfoBox(frame, "Quick Stats", self.colors['accent'], self.colors)
        info_box.pack(fill=tk.X, pady=(0, 15))
        
        self.quick_info_frame = info_box.content_frame
        self._create_quick_info_labels()
        
        # Validation warnings
        self.validation_label = tk.Label(frame, text="", 
                                        font=("Segoe UI", 9),
                                        fg=self.colors['warning'],
                                        bg=self.colors['secondary'],
                                        wraplength=300,
                                        justify=tk.LEFT)
        self.validation_label.pack(anchor=tk.W, pady=(15, 0))
        
    def _create_quick_info_labels(self):
        """Create the quick info labels in the info box"""
        self.quick_info_labels = {}
        
        info_items = [
            ("points", "Points", "0"),
            ("layers", "Layers", "0"),
            ("blocks", "Hex Blocks", "0"),
            ("patches", "Patches", "0"),
            ("scale", "Scale", "1.0"),
            ("units", "Units", "m")
        ]
        
        for key, label, default in info_items:
            row = tk.Frame(self.quick_info_frame, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=label + ":",
                    font=('Segoe UI', 10),
                    bg=self.colors['card_bg'],
                    fg=self.colors['fg'],
                    anchor=tk.W).pack(side=tk.LEFT)
            
            value_label = tk.Label(row, text=default,
                                  font=('Segoe UI', 10, 'bold'),
                                  bg=self.colors['card_bg'],
                                  fg=self.colors['accent'],
                                  anchor=tk.E)
            value_label.pack(side=tk.RIGHT)
            
            self.quick_info_labels[key] = value_label
    
    def _setup_summary_tab(self):
        """Setup the improved Summary tab with modern dashboard-style statistics"""
        # Main scrollable container
        main_container = tk.Frame(self.tab_summary, bg=self.colors['secondary'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview,
                                bg=self.colors['secondary'])
        
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        self._summary_canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Constrain inner frame width to canvas width (fixes horizontal cutoff)
        def _on_canvas_configure(event):
            canvas.itemconfig(self._summary_canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Pack canvas and scrollbar
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mousewheel only when this tab is active (not bind_all)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            return "break"
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel_linux)
        canvas.bind("<Button-5>", _on_mousewheel_linux)
        
        # Main content frame with reduced padding to fit column
        content_frame = tk.Frame(scrollable_frame, bg=self.colors['secondary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header section (compact)
        header_frame = tk.Frame(content_frame, bg=self.colors['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(header_frame, text="Mesh Statistics", 
                font=("Segoe UI", 14, "bold"),
                bg=self.colors['secondary'], fg=self.colors['accent']).pack(anchor=tk.W)
        
        tk.Label(header_frame, text="CFD mesh configuration overview", 
                font=("Segoe UI", 9),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(2, 0))
        
        # Stats cards container (2x2 grid)
        cards_container = tk.Frame(content_frame, bg=self.colors['secondary'])
        cards_container.pack(fill=tk.X, pady=(0, 15))
        
        # Configure grid
        cards_container.grid_columnconfigure(0, weight=1, uniform="card")
        cards_container.grid_columnconfigure(1, weight=1, uniform="card")
        
        # Create stat cards with icons and colors
        card_configs = [
            ("vertices", "Total Vertices", "0", "●", self.colors['accent']),
            ("blocks", "Hex Blocks", "0", "■", self.colors['success']),
            ("cells", "Total Cells", "0", "▦", self.colors['warning']),
            ("patches", "Boundary Patches", "0", "▨", '#c586c0')
        ]
        
        self.stat_cards = {}
        for i, (key, label, value, icon, color) in enumerate(card_configs):
            row, col = divmod(i, 2)
            card = StatCard(cards_container, label, value, icon, color, self.colors)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.stat_cards[key] = card
        
        # Project info section
        project_box = InfoBox(content_frame, "Project Configuration", self.colors['accent'], self.colors)
        project_box.pack(fill=tk.X, pady=(0, 10))
        self.project_info_frame = project_box.content_frame
        
        # Mesh details panel
        self.details_panel = MeshDetailsPanel(content_frame, self.colors)
        self.details_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Refresh button at bottom
        btn_container = tk.Frame(content_frame, bg=self.colors['secondary'])
        btn_container.pack(fill=tk.X, pady=(5, 0))
        
        refresh_btn = tk.Button(btn_container, text="⟳ Refresh All Statistics", 
                               command=self.update_summary,
                               bg=self.colors['button_bg'], 
                               fg=self.colors['button_fg'],
                               font=("Segoe UI", 10, "bold"), 
                               relief=tk.FLAT,
                               activebackground=self.colors['button_active'],
                               cursor="hand2",
                               padx=15, pady=8)
        refresh_btn.pack(side=tk.RIGHT)

        
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
                    font=("Segoe UI", 9, "bold"),
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
        tk.Button(container, text="⟳ Refresh", 
                 command=lambda: self.update_details(),
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 font=("Segoe UI", 9, "bold"), 
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active'],
                 cursor="hand2",
                 padx=15, pady=5).pack(fill=tk.X, pady=(5, 0))
        
    def update_preview(self):
        """Update the preview text"""
        content = self.generate_blockmesh_dict()
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', content)
        
        # Update line count
        line_count = content.count('\n') + 1
        self.line_count_label.config(text=f"{line_count} lines")
        
        # Update quick info
        self._update_quick_info()
        self._update_validation()
        
    def _update_quick_info(self):
        """Update quick info in Actions tab"""
        total_points = len(self.mesh_data.points)
        total_layers = len(self.mesh_data.layers)
        total_hex_blocks = len(self.mesh_data.hex_blocks)
        total_patches = len(self.mesh_data.patches)
        scale = self.mesh_data.get_scale_value()
        units = self.mesh_data.unit_system
        
        if hasattr(self, 'quick_info_labels'):
            self.quick_info_labels['points'].config(text=str(total_points))
            self.quick_info_labels['layers'].config(text=str(total_layers))
            self.quick_info_labels['blocks'].config(text=str(total_hex_blocks))
            self.quick_info_labels['patches'].config(text=str(total_patches))
            self.quick_info_labels['scale'].config(text=str(scale))
            self.quick_info_labels['units'].config(text=units)
        
    def _update_validation(self):
        """Update validation warnings"""
        issues = self.validate_hex_blocks()
        if issues:
            self.validation_label.config(
                text="⚠️ Warnings:\n" + "\n".join(f"  • {issue}" for issue in issues[:3]),
                fg=self.colors['warning']
            )
            self.status_label.config(text="● Warning", fg=self.colors['warning'])
        else:
            self.validation_label.config(text="✓ No validation issues", fg=self.colors['success'])
            self.status_label.config(text="● Ready", fg=self.colors['success'])
            
    def update_summary(self):
        """Update the Summary tab with comprehensive statistics"""
        # Calculate statistics
        total_cells = 0
        block_details = []
        
        for block_id, block in self.mesh_data.hex_blocks.items():
            i = int(block_id) - 1  # Convert to 0-based index for display
            nx, ny, nz = block.get('divisions', (1, 1, 1))
            cells = nx * ny * nz
            total_cells += cells
            block_details.append((i, nx, ny, nz, cells, block_id))
        
        total_points = len(self.mesh_data.points)
        total_blocks = len(self.mesh_data.hex_blocks)
        total_patches = len(self.mesh_data.patches)
        
        # Update stat cards
        self.stat_cards['vertices'].update_value(f"{total_points:,}")
        self.stat_cards['blocks'].update_value(str(total_blocks))
        self.stat_cards['cells'].update_value(f"{total_cells:,}")
        self.stat_cards['patches'].update_value(str(total_patches))
        
        # Update project info
        for widget in self.project_info_frame.winfo_children():
            widget.destroy()
        
        project_items = [
            ("Project Name", self.mesh_data.project_name),
            ("Unit System", self.mesh_data.unit_system),
            ("Scale Factor", f"{self.mesh_data.get_scale_value()}"),
            ("Sketch Plane", self.mesh_data.sketch_plane),
            ("Total Layers", str(len(self.mesh_data.layers)))
        ]
        
        for label, value in project_items:
            row = tk.Frame(self.project_info_frame, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=label + ":",
                    font=('Segoe UI', 10),
                    bg=self.colors['card_bg'],
                    fg=self.colors['fg'],
                    anchor=tk.W).pack(side=tk.LEFT)
            
            tk.Label(row, text=str(value),
                    font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['card_bg'],
                    fg=self.colors['accent'],
                    anchor=tk.E).pack(side=tk.RIGHT)
        
        # Update details panel
        self.details_panel.clear()
        
        # Mesh Overview Section
        self.details_panel.insert_section_header("MESH OVERVIEW", "📐")
        self.details_panel.insert_key_value("Total Vertices", f"{total_points:,}")
        self.details_panel.insert_key_value("Hex Blocks", total_blocks)
        self.details_panel.insert_key_value("Total Cells", f"{total_cells:,}")
        self.details_panel.insert_key_value("Boundary Patches", total_patches)
        
        # Cell Distribution Section
        if block_details:
            self.details_panel.insert_section_header("CELL DISTRIBUTION", "⚡")
            
            for i, nx, ny, nz, cells, block_id in block_details:
                self.details_panel.insert_line()
                self.details_panel.insert(f"  Block {i}", "subsection")
                self.details_panel.insert_line()
                self.details_panel.insert_key_value("Divisions", f"{nx} × {ny} × {nz}", indent=1)
                self.details_panel.insert_key_value("Total Cells", f"{cells:,}", indent=1)
                
                # Show grading if not uniform
                if block_id in self.mesh_data.hex_blocks:
                    grading = self.mesh_data.hex_blocks[block_id].get('grading_params', {})
                    gx = grading.get('x', 1.0)
                    gy = grading.get('y', 1.0)
                    gz = grading.get('z', 1.0)
                    
                    if gx != 1.0 or gy != 1.0 or gz != 1.0:
                        self.details_panel.insert_key_value("Grading", f"({gx}, {gy}, {gz})", indent=1)
        
        # Boundary Patches Section
        if self.mesh_data.patches:
            self.details_panel.insert_section_header("BOUNDARY PATCHES", "🔲")
            
            for patch_name, patch_data in self.mesh_data.patches.items():
                if isinstance(patch_data, dict):
                    ptype = patch_data.get('type', 'unknown')
                    num_faces = len(patch_data.get('faces', []))
                else:
                    ptype = patch_data[1] if len(patch_data) > 1 else 'unknown'
                    num_faces = len(patch_data[2]) if len(patch_data) > 2 else 0
                
                self.details_panel.insert_line()
                self.details_panel.insert(f"  {patch_name}", "subsection")
                self.details_panel.insert_line()
                self.details_panel.insert_key_value("Type", ptype, indent=1)
                self.details_panel.insert_key_value("Faces", num_faces, indent=1)
        
        # Quality Metrics
        if total_cells > 0:
            self.details_panel.insert_section_header("QUALITY METRICS", "✓")
            avg_cells_per_block = total_cells / max(1, total_blocks)
            self.details_panel.insert_key_value("Avg Cells/Block", f"{avg_cells_per_block:.1f}")
            
            if total_patches > 0:
                self.details_panel.insert_key_value("Blocks/Patch Ratio", f"{total_blocks / total_patches:.2f}")
        
        self.details_panel.finalize()
        
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
                        ptype = patch_data[1] if len(patch_data) > 1 else 'unknown'
                        num_faces = len(patch_data[2]) if len(patch_data) > 2 else 0
                    self.patches_listbox.insert(tk.END, f"{patch_name:<15} {ptype:<12} {num_faces}")
        
        # Update hexes list
        if hasattr(self, 'hexes_listbox'):
            self.hexes_listbox.delete(0, tk.END)
            for block_id, block in self.mesh_data.hex_blocks.items():
                i = int(block_id)
                nx, ny, nz = block.get('divisions', (1, 1, 1))
                cells = nx * ny * nz
                self.hexes_listbox.insert(tk.END, f"Block {i:<11} {nx}×{ny}×{nz:<6} {cells:,}")
        
        # Update edges list
        if hasattr(self, 'edges_listbox'):
            self.edges_listbox.delete(0, tk.END)
            for block_id, block in self.mesh_data.hex_blocks.items():
                i = int(block_id)
                point_refs = block.get('point_refs', [])
                self.edges_listbox.insert(tk.END, f"Block {i:<11} hex          {len(point_refs)} verts")
        
    def validate_hex_blocks(self):
        """Check if hex blocks have valid vertex ordering"""
        issues = []
        for block_id, block in self.mesh_data.hex_blocks.items():
            i = int(block_id)
            point_refs = block.get('point_refs', [])
            # Get vertices from point_refs
            verts = []
            for pid in point_refs:
                pt = self.mesh_data.get_point(pid)
                if pt:
                    verts.append((pt['x'], pt['y'], pt['z']))
            
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
    
    def _build_face_id_mapping(self):
        """Build a mapping from face_id to vertex global indices"""
        face_id_to_vertices = {}

        if not hasattr(self.mesh_data, 'hex_blocks') or not self.mesh_data.hex_blocks:
            return face_id_to_vertices

        # Face definitions for a hex block (OpenFOAM standard)
        face_definitions = [
            ("bottom", [0, 3, 2, 1]),
            ("top", [4, 5, 6, 7]),
            ("front", [0, 1, 5, 4]),
            ("back", [3, 7, 6, 2]),
            ("left", [0, 4, 7, 3]),
            ("right", [1, 2, 6, 5])
        ]

        face_id = 0
        for block_id, block in self.mesh_data.hex_blocks.items():
            point_refs = block.get('point_refs', [])
            if len(point_refs) != 8:
                continue

            for face_name, face_vertex_indices in face_definitions:
                face_global_indices = [point_refs[i] for i in face_vertex_indices]
                face_id_to_vertices[face_id] = face_global_indices
                face_id += 1

        return face_id_to_vertices

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
        
        points_3d = self.mesh_data.get_all_points_list()
        point_map = self.mesh_data.get_point_index_map()
        
        for i, coords in enumerate(points_3d):
            x, y, z = coords
            lines.append(f"    ( {x:.6f} {y:.6f} {z:.6f} )  // point {i}")
        
        lines.append(");")
        lines.append("")
        
        # Blocks
        lines.append("blocks")
        lines.append("(")

        for i, block in enumerate(self.mesh_data.hex_blocks.values()):
            point_refs = block.get('point_refs', [])
            if len(point_refs) != 8:
                continue

            # Translate global point IDs -> 0-based vertex indices
            p = [point_map.get(int(pid), int(pid)) for pid in point_refs]
            lines.append(f"    hex ({p[0]} {p[1]} {p[2]} {p[3]} {p[4]} {p[5]} {p[6]} {p[7]})")

            nx, ny, nz = block.get('divisions', (1, 1, 1))
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

        face_id_to_vertices = self._build_face_id_mapping()

        for patch_name, patch_data in self.mesh_data.patches.items():
            if isinstance(patch_data, dict):
                patch_type = patch_data.get('type', 'patch')
                raw_faces = patch_data.get('faces', [])
            else:
                patch_type = patch_data[1] if len(patch_data) > 1 else 'patch'
                raw_faces = patch_data[2] if len(patch_data) > 2 else []

            lines.append(f"    {patch_name}")
            lines.append("    {")
            lines.append(f"        type {patch_type};")
            lines.append("        faces")
            lines.append("        (")

            for face_entry in raw_faces:
                if isinstance(face_entry, dict):
                    # New format: {'face_id': int, 'point_ids': [id, id, id, id]}
                    point_ids = face_entry.get('point_ids')
                    if point_ids and len(point_ids) == 4:
                        # Translate global point IDs -> 0-based vertex indices
                        verts = [point_map.get(int(pid), int(pid)) for pid in point_ids]
                        lines.append(f"            ({verts[0]} {verts[1]} {verts[2]} {verts[3]})")
                    else:
                        # Fallback: try to look up by face_id
                        face_id = face_entry.get('face_id')
                        if face_id is not None and face_id in face_id_to_vertices:
                            verts = face_id_to_vertices[face_id]
                            lines.append(f"            ({verts[0]} {verts[1]} {verts[2]} {verts[3]})")
                elif isinstance(face_entry, (list, tuple)) and len(face_entry) == 4:
                    # Legacy direct vertex list
                    lines.append(f"            ({face_entry[0]} {face_entry[1]} {face_entry[2]} {face_entry[3]})")
                elif isinstance(face_entry, int) and face_entry in face_id_to_vertices:
                    verts = face_id_to_vertices[face_entry]
                    lines.append(f"            ({verts[0]} {verts[1]} {verts[2]} {verts[3]})")

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
            messagebox.showwarning("Warning", "No hex blocks defined! Create blocks in Tab 4 first.")
            return
        
        # Validate before export
        issues = self.validate_hex_blocks()
        if issues:
            result = messagebox.askyesno("Validation Warning", 
                                        "There are issues with your hex blocks:\n\n" + 
                                        "\n".join(f"- {issue}" for issue in issues) +
                                        "\n\nExport anyway?")
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
                messagebox.showinfo("Success", f"✓ blockMeshDict exported to:\n{filename}")
                self.status_label.config(text="● Exported", fg=self.colors['success'])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                self.status_label.config(text="● Error", fg=self.colors['error'])
    
    def copy_to_clipboard(self):
        """Copy content to clipboard"""
        content = self.generate_blockmesh_dict()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
        messagebox.showinfo("Copied", "✓ blockMeshDict content copied to clipboard!")
        self.status_label.config(text="● Copied", fg=self.colors['success'])