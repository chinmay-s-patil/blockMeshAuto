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
        """Setup the Summary tab with modern dashboard-style statistics"""
        # Main container with padding
        main_frame = tk.Frame(self.tab_summary, bg=self.colors['secondary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        header_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="Mesh Statistics", 
                font=("Segoe UI", 18, "bold"),
                bg=self.colors['secondary'], fg=self.colors['accent']).pack(anchor=tk.W)
        
        tk.Label(header_frame, text="Overview of your CFD mesh configuration", 
                font=("Segoe UI", 10),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(5, 0))
        
        # Stats cards container (2x2 grid)
        self.cards_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        self.cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Configure grid weights
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        
        # Create card placeholders (will be populated in update_summary)
        self.stat_cards = {}
        card_configs = [
            ("vertices", "Vertices", self.colors['accent']),
            ("blocks", "Hex Blocks", self.colors['success']),
            ("cells", "Total Cells", self.colors['warning']),
            ("patches", "Patches", '#c586c0')  # Purple
        ]
        
        for i, (key, label, color) in enumerate(card_configs):
            row, col = divmod(i, 2)
            card = self._create_stat_card(self.cards_frame, label, "0", color)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stat_cards[key] = card
        
        # Detailed breakdown section
        details_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(details_frame, text="Detailed Breakdown", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(anchor=tk.W, pady=(0, 10))
        
        # Styled text container
        text_container = tk.Frame(details_frame, bg=self.colors['border'], bd=1)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_container, bg=self.colors['secondary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_text = tk.Text(text_container, 
                                 font=("Consolas", 10),
                                 bg=self.colors['text_bg'],
                                 fg=self.colors['text_fg'],
                                 relief=tk.FLAT,
                                 wrap=tk.WORD,
                                 yscrollcommand=scrollbar.set,
                                 padx=15, pady=15,
                                 height=12)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=self.stats_text.yview)
        
        # Bind mouse wheel for scrolling
        self.stats_text.bind("<MouseWheel>", self._on_mousewheel)
        self.stats_text.bind("<Button-4>", self._on_mousewheel_linux)
        self.stats_text.bind("<Button-5>", self._on_mousewheel_linux)
        
        # Configure text tags for styling
        self.stats_text.tag_configure("header", 
                                     foreground=self.colors['accent'], 
                                     font=("Consolas", 12, "bold"))
        self.stats_text.tag_configure("subheader", 
                                     foreground=self.colors['fg'],
                                     font=("Consolas", 11, "bold"))
        self.stats_text.tag_configure("label", 
                                     foreground=self.colors['fg'],
                                     font=("Consolas", 10))
        self.stats_text.tag_configure("value", 
                                     foreground=self.colors['success'], 
                                     font=("Consolas", 10, "bold"))
        self.stats_text.tag_configure("highlight", 
                                     foreground=self.colors['warning'],
                                     font=("Consolas", 11, "bold"))
        self.stats_text.tag_configure("separator", 
                                     foreground=self.colors['border'])
        self.stats_text.tag_configure("dim", 
                                     foreground='#808080',
                                     font=("Consolas", 10))
        
        # Refresh button at bottom
        btn_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        refresh_btn = tk.Button(btn_frame, text="⟳ Refresh Statistics", 
                               command=self.update_summary,
                               bg=self.colors['button_bg'], 
                               fg=self.colors['button_fg'],
                               font=("Segoe UI", 10, "bold"), 
                               relief=tk.FLAT,
                               activebackground=self.colors['button_active'],
                               cursor="hand2",
                               padx=20, pady=8)
        refresh_btn.pack(side=tk.RIGHT)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling on Windows/macOS"""
        self.stats_text.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"
        
    def _on_mousewheel_linux(self, event):
        """Handle mouse wheel scrolling on Linux"""
        if event.num == 4:
            self.stats_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.stats_text.yview_scroll(1, "units")
        return "break"
        
    def _create_stat_card(self, parent, label, value, color):
        """Create a modern stat card with color accent"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], padx=20, pady=20)
        
        # Color indicator bar at top
        indicator = tk.Frame(card, bg=color, height=3)
        indicator.pack(fill=tk.X, pady=(0, 12))
        
        # Label
        tk.Label(card, text=label, 
                font=("Segoe UI", 11),
                bg=self.colors['card_bg'], fg=self.colors['fg']).pack(anchor=tk.W)
        
        # Value (stored as attribute for updates)
        value_label = tk.Label(card, text=value, 
                              font=("Segoe UI", 28, "bold"),
                              bg=self.colors['card_bg'], fg=color)
        value_label.pack(anchor=tk.W, pady=(8, 0))
        card.value_label = value_label
        
        return card
        
    def update_summary(self):
        """Update the Summary tab with statistics - REFRESHES ALL DATA"""
        # Calculate statistics fresh from mesh_data
        total_cells = 0
        block_details = []
        
        for i, block in enumerate(self.mesh_data.hex_blocks):
            nx, ny, nz = block['divisions']
            cells = nx * ny * nz
            total_cells += cells
            block_details.append((i, nx, ny, nz, cells))
        
        total_points = self.mesh_data.get_total_points()
        total_blocks = len(self.mesh_data.hex_blocks)
        total_patches = len(self.mesh_data.patches)
        
        # Update stat cards with fresh data
        self.stat_cards['vertices'].value_label.config(text=f"{total_points:,}")
        self.stat_cards['blocks'].value_label.config(text=str(total_blocks))
        self.stat_cards['cells'].value_label.config(text=f"{total_cells:,}")
        self.stat_cards['patches'].value_label.config(text=str(total_patches))
        
        # Update detailed text with fresh data
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        
        def insert_line(text="", tag=None):
            self.stats_text.insert(tk.END, text + "\n", tag)
        
        # Project Configuration Section - Modern boxed style
        insert_line("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓", "separator")
        insert_line("┃" + " MESH CONFIGURATION".center(42) + "┃", "header")
        insert_line("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛", "separator")
        insert_line()
        
        # Two-column layout for config
        insert_line(f"  Project Name:     {self.mesh_data.project_name}", "label")
        self.stats_text.insert(tk.END, "\n", None)
        insert_line(f"  Unit System:      {self.mesh_data.unit_system}", "label")
        insert_line(f"  Scale Factor:     {self.mesh_data.get_scale_value()}", "label")
        insert_line(f"  Total Layers:     {len(self.mesh_data.layers)}", "label")
        insert_line()
        
        # Cell Distribution Section
        insert_line("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓", "separator")
        insert_line("┃" + " CELL DISTRIBUTION".center(42) + "┃", "subheader")
        insert_line("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫", "separator")
        
        if block_details:
            for i, nx, ny, nz, cells in block_details:
                insert_line(f"┃ Block {i:<2}                                 ┃", "label")
                insert_line(f"┃   Divisions: {nx:>3} × {ny:>3} × {nz:<3}            ┃", "dim")
                insert_line(f"┃   Cells:     {cells:>10,}                 ┃", "value")
                if i < len(block_details) - 1:
                    insert_line("┃                                          ┃", "separator")
            insert_line("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫", "separator")
            insert_line(f"┃ TOTAL: {total_cells:>10,} cells                   ┃", "highlight")
        else:
            insert_line("┃ No hex blocks defined                    ┃", "dim")
        
        insert_line("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛", "separator")
        insert_line()
        
        # Boundary Patches Section
        insert_line("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓", "separator")
        insert_line("┃" + " BOUNDARY PATCHES".center(42) + "┃", "subheader")
        insert_line("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫", "separator")
        
        if self.mesh_data.patches:
            patch_items = list(self.mesh_data.patches.items())
            for idx, (patch_name, patch_data) in enumerate(patch_items):
                if isinstance(patch_data, dict):
                    ptype = patch_data.get('type', 'unknown')
                    num_faces = len(patch_data.get('faces', []))
                else:
                    ptype = patch_data[1] if len(patch_data) > 1 else 'unknown'
                    num_faces = len(patch_data[2]) if len(patch_data) > 2 else 0
                
                insert_line(f"┃ {patch_name[:20]:<20} {ptype:<8} {num_faces:>3} faces  ┃", "value")
                if idx < len(patch_items) - 1:
                    insert_line("┃                                          ┃", "separator")
        else:
            insert_line("┃ No patches defined                       ┃", "dim")
        
        insert_line("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛", "separator")
        
        self.stats_text.config(state=tk.DISABLED)
        
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

        for i, block in enumerate(self.mesh_data.hex_blocks):
            nx, ny, nz = block['divisions']
            cells = nx * ny * nz
            total_cells += cells

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

        if total_cells > 0:
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

        self.stats_text.insert('1.0', ''.join(summary))
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
    
    def _build_face_id_mapping(self):
        """Build a mapping from face_id to vertex global indices"""
        face_id_to_vertices = {}

        if not hasattr(self.mesh_data, 'hex_blocks') or not self.mesh_data.hex_blocks:
            return face_id_to_vertices

        # Face definitions for a hex block (vertex indices for each face)
        face_definitions = [
            ("bottom", [0, 3, 2, 1]),  # Note: reversed for outward normal
            ("top", [4, 5, 6, 7]),
            ("front", [0, 1, 5, 4]),
            ("back", [3, 7, 6, 2]),
            ("left", [0, 4, 7, 3]),
            ("right", [1, 2, 6, 5])
        ]

        face_id = 0
        for block_idx, block in enumerate(self.mesh_data.hex_blocks):
            point_refs = block.get('point_refs', [])
            if len(point_refs) != 8:
                continue

            for face_name, face_vertex_indices in face_definitions:
                # Get the global point indices for this face
                face_global_indices = [point_refs[i] for i in face_vertex_indices]
                face_id_to_vertices[face_id] = face_global_indices
                face_id += 1

        return face_id_to_vertices

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

        # Build face ID to vertex indices mapping from hex blocks
        face_id_to_vertices = self._build_face_id_mapping()

        for patch_name, patch_data in self.mesh_data.patches.items():
            # Handle both dict and tuple formats
            if isinstance(patch_data, dict):
                patch_type = patch_data.get('type', 'patch')
                face_ids = patch_data.get('faces', [])
            else:
                patch_type = patch_data[1] if len(patch_data) > 1 else 'patch'
                face_ids = patch_data[2] if len(patch_data) > 2 else []

            lines.append(f"    {patch_name}")
            lines.append("    {")
            lines.append(f"        type {patch_type};")
            lines.append("        faces")
            lines.append("        (")

            # Convert face IDs to vertex indices
            for face_id in face_ids:
                if isinstance(face_id, (list, tuple)) and len(face_id) == 4:
                    # Already in vertex indices format (legacy)
                    lines.append(f"            ({face_id[0]} {face_id[1]} {face_id[2]} {face_id[3]})")
                elif isinstance(face_id, int) and face_id in face_id_to_vertices:
                    # Look up vertex indices from face ID
                    verts = face_id_to_vertices[face_id]
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