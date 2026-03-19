"""
Tab 5: 3D Hex Block View & Patch Assignment
============================================
Uses the PyVista/VTK offscreen renderer (tab5_pyvista_renderer.py).

Changes from original:
  • self.canvas → self.viewer_frame (tk.Frame hosting the VTK canvas)
  • Control bar is a proper tk.Frame (no canvas .place() overlays)
  • Opacity toggle button wired to renderer.toggle_opacity()
  • Legend is a tkinter overlay in the renderer – no VTK text actors
"""

import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np


class Tab5HexPatches:

    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data

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
            'canvas_bg': '#1e1e1e',
            'axis': '#6e6e6e',
            'text_bg': '#2d2d2d',
            'text_fg': '#d4d4d4',
        }

        if not hasattr(self.mesh_data, 'patches'):
            self.mesh_data.patches = {}
        elif isinstance(self.mesh_data.patches, list):
            old = self.mesh_data.patches
            self.mesh_data.patches = {}
            for item in old:
                if isinstance(item, tuple) and len(item) >= 2:
                    self.mesh_data.patches[item[0]] = {
                        'name': item[0], 'type': item[1],
                        'faces': item[2] if len(item) > 2 else [],
                        'parameters': {},
                    }

        self.renderer = None
        self.hide_mode = False
        self.normals_tab = None
        self.patch_editor_dialog = None

        self.setup_ui()

    # ── UI ────────────────────────────────────────────────────────────────

    def setup_ui(self) -> None:
        main_frame = tk.Frame(self.parent, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ── LEFT: 3-D area ───────────────────────────────────────────────
        left_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header = tk.Frame(left_frame, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text="5. Patches & Assignment",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Label(header,
                 text="3D Hex Block View – click faces to select / hide",
                 font=("Segoe UI", 10, "italic"),
                 fg=self.colors['axis'], bg=self.colors['bg']).pack(
                     side=tk.LEFT, padx=15, pady=(4, 0))

        # Control bar
        ctrl = tk.Frame(left_frame, bg=self.colors['secondary'],
                        highlightthickness=1,
                        highlightbackground=self.colors['border'])
        ctrl.pack(fill=tk.X, pady=(0, 2))

        bkw = dict(font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                   activeforeground=self.colors['button_fg'])

        self.patch_coloring_button = tk.Button(
            ctrl, text="🎨 Patches: ON",
            command=self._toggle_patch_coloring,
            bg=self.colors['success'], fg=self.colors['bg'],
            activebackground='#3db89f', width=14, **bkw)
        self.patch_coloring_button.pack(side=tk.LEFT, padx=4, pady=3)

        self.mode_button = tk.Button(
            ctrl, text="Mode: Select",
            command=self._toggle_mode,
            bg=self.colors['button_bg'], fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'], width=12, **bkw)
        self.mode_button.pack(side=tk.LEFT, padx=4, pady=3)

        # ── Opacity toggle ────────────────────────────────────────────────
        self.opacity_button = tk.Button(
            ctrl, text="◑ Translucent",
            command=self._toggle_opacity,
            bg='#5a4a6a', fg=self.colors['button_fg'],
            activebackground='#7a5a8a', width=14, **bkw)
        self.opacity_button.pack(side=tk.LEFT, padx=4, pady=3)

        tk.Button(ctrl, text="Show All",
                  command=self._show_all_faces,
                  bg=self.colors['accent'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  **bkw).pack(side=tk.LEFT, padx=4, pady=3)

        tk.Button(ctrl, text="Reset View",
                  command=self._reset_view,
                  bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  **bkw).pack(side=tk.LEFT, padx=4, pady=3)

        tk.Button(ctrl, text="Fit All",
                  command=self._fit_all,
                  bg=self.colors['success'], fg=self.colors['bg'],
                  activebackground='#3db89f',
                  **bkw).pack(side=tk.LEFT, padx=4, pady=3)

        tk.Button(ctrl, text="🔄 Refresh",
                  command=self._refresh_view,
                  bg=self.colors['accent'], fg=self.colors['button_fg'],
                  activebackground=self.colors['button_active'],
                  **bkw).pack(side=tk.LEFT, padx=4, pady=3)

        tk.Label(ctrl,
                 text="L-click/drag: select  |  M-drag: rotate  |  R-drag: pan  |  Scroll: zoom",
                 font=("Segoe UI", 8), fg=self.colors['axis'],
                 bg=self.colors['secondary']).pack(side=tk.RIGHT, padx=8)

        # VTK viewer frame
        self.viewer_frame = tk.Frame(left_frame, bg=self.colors['canvas_bg'],
                                     highlightthickness=1,
                                     highlightbackground=self.colors['border'])
        self.viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── RIGHT: scrollable control panel ──────────────────────────────
        right_container = tk.Frame(main_frame, width=350,
                                   bg=self.colors['secondary'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_container.pack_propagate(False)

        right_canvas = tk.Canvas(right_container, bg=self.colors['secondary'],
                                 highlightthickness=0, width=330)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(right_container, orient="vertical",
                                 command=right_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(bg=self.colors['secondary'],
                         troughcolor=self.colors['bg'],
                         activebackground=self.colors['accent'])

        right_frame = tk.Frame(right_canvas, bg=self.colors['secondary'],
                               width=330)
        cw = right_canvas.create_window((0, 0), window=right_frame,
                                        anchor="nw")

        def _on_cfg(event=None):
            right_canvas.update_idletasks()
            bbox = right_canvas.bbox("all")
            if bbox:
                right_canvas.configure(scrollregion=bbox)
            right_canvas.itemconfig(cw, width=right_canvas.winfo_width())

        right_frame.bind("<Configure>", _on_cfg)
        right_canvas.bind("<Configure>", _on_cfg)

        def _mw(event):
            if right_canvas.bbox("all"):
                right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        right_canvas.bind("<MouseWheel>", _mw)

        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors['secondary'])
        style.configure("TNotebook.Tab",
                        background=self.colors['secondary'],
                        foreground=self.colors['fg'])
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors['accent'])])

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_patches    = tk.Frame(self.notebook,
                                       bg=self.colors['secondary'])
        self.tab_assignment = tk.Frame(self.notebook,
                                       bg=self.colors['secondary'])
        self.tab_normals    = tk.Frame(self.notebook,
                                       bg=self.colors['secondary'])

        self.notebook.add(self.tab_patches,    text="Patches")
        self.notebook.add(self.tab_assignment, text="Assign")
        self.notebook.add(self.tab_normals,    text="Normals")

        self._setup_status_section(self.tab_patches)

        from tab5_Patches.tab5_patch_panels import PatchListPanel
        self.patch_list_panel = PatchListPanel(
            self.tab_patches, self.mesh_data, self.colors,
            on_select_callback=self._on_patch_selected,
            on_edit_callback=self._on_patch_edit,
        )

        from tab5_Patches.tab5_patch_panels import PatchAssignmentPanel
        self.patch_panel = PatchAssignmentPanel(
            self.tab_assignment, self.mesh_data, self.colors,
            on_assign_callback=self._on_patch_assigned,
            renderer=self.renderer,
        )

        from tab5_Patches.tab5_patch_normals import PatchNormalsTab
        self.normals_tab = PatchNormalsTab(
            self.tab_normals, self.mesh_data, self.colors, self.renderer)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        right_frame.update_idletasks()
        _on_cfg()

        self._init_renderer()

    # ── status ────────────────────────────────────────────────────────────

    def _setup_status_section(self, parent) -> None:
        sf = tk.LabelFrame(parent, text="Status", padx=10, pady=10,
                           bg=self.colors['secondary'], fg=self.colors['fg'],
                           highlightbackground=self.colors['border'],
                           highlightcolor=self.colors['accent'],
                           font=("Arial", 10, "bold"))
        sf.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = tk.Label(sf, text="Ready",
                                     font=("Arial", 10),
                                     fg=self.colors['success'],
                                     bg=self.colors['secondary'])
        self.status_label.pack(anchor=tk.W)

        self.block_count_label = tk.Label(sf, text="Blocks: 0",
                                          font=("Arial", 9),
                                          fg=self.colors['fg'],
                                          bg=self.colors['secondary'])
        self.block_count_label.pack(anchor=tk.W, pady=(5, 0))

        self.face_count_label = tk.Label(sf, text="Visible faces: 0",
                                         font=("Arial", 9),
                                         fg=self.colors['fg'],
                                         bg=self.colors['secondary'])
        self.face_count_label.pack(anchor=tk.W)

        self.selected_count_label = tk.Label(sf, text="Selected faces: 0",
                                             font=("Arial", 9, "bold"),
                                             fg=self.colors['accent'],
                                             bg=self.colors['secondary'])
        self.selected_count_label.pack(anchor=tk.W)

    # ── renderer init ─────────────────────────────────────────────────────

    def _init_renderer(self) -> None:
        from tab5_Patches.tab5_pyvista_renderer import HexBlockRenderer
        self.renderer = HexBlockRenderer(self.viewer_frame, self.mesh_data)
        self.renderer.on_selection_changed = self._on_face_selection_changed

        if self.normals_tab:
            self.normals_tab.renderer = self.renderer
        if hasattr(self, 'patch_panel') and self.patch_panel:
            self.patch_panel.renderer = self.renderer

        self._update_status()
        self.renderer.draw()

    # ── toolbar callbacks ─────────────────────────────────────────────────

    def _toggle_patch_coloring(self) -> None:
        if not self.renderer:
            return
        enabled = self.renderer.toggle_patch_coloring()
        if enabled:
            self.patch_coloring_button.config(
                text="🎨 Patches: ON",
                bg=self.colors['success'], fg=self.colors['bg'])
        else:
            self.patch_coloring_button.config(
                text="🎨 Patches: OFF",
                bg=self.colors['button_bg'], fg=self.colors['button_fg'])

    def _toggle_mode(self) -> None:
        self.hide_mode = not self.hide_mode
        if self.hide_mode:
            self.mode_button.config(text="Mode: Hide",
                                    bg=self.colors['warning'],
                                    fg=self.colors['bg'])
        else:
            self.mode_button.config(text="Mode: Select",
                                    bg=self.colors['button_bg'],
                                    fg=self.colors['button_fg'])

    def _toggle_opacity(self) -> None:
        if not self.renderer:
            return
        opaque = self.renderer.toggle_opacity()
        if opaque:
            self.opacity_button.config(text="● Opaque",
                                       bg='#2a5a2a', fg='#aaffaa')
        else:
            self.opacity_button.config(text="◑ Translucent",
                                       bg='#5a4a6a', fg=self.colors['button_fg'])

    def _show_all_faces(self) -> None:
        if self.renderer:
            self.renderer.show_all_faces()
            n = self.renderer.get_hidden_face_count()
            self.status_label.config(
                text=f"Showed all hidden faces ({n} were hidden)",
                fg=self.colors['success'])

    def _reset_view(self) -> None:
        if self.renderer:
            self.renderer.reset_view()

    def _fit_all(self) -> None:
        if self.renderer:
            self.renderer.fit_all()

    def _refresh_view(self) -> None:
        if self.renderer:
            self.renderer.invalidate_cache()
            self.renderer._build_faces()
            self._update_status()
            self.renderer.draw()

    # ── selection / face callbacks ────────────────────────────────────────

    def _on_face_selection_changed(self, selected_faces: set) -> None:
        if self.hide_mode and self.renderer:
            for fid in selected_faces:
                for face in self.renderer.all_faces:
                    if face.get('face_id') == fid:
                        face['is_visible'] = False
            self.renderer.selected_faces.clear()
            self.renderer.draw()
            hidden = self.renderer.get_hidden_face_count()
            self.status_label.config(
                text=f"Hide mode: {hidden} faces hidden",
                fg=self.colors['warning'])
        else:
            self.patch_panel.set_selected_faces(selected_faces)
            self.selected_count_label.config(
                text=f"Selected faces: {len(selected_faces)}")

    # ── patch editor ──────────────────────────────────────────────────────

    def _on_patch_edit(self, patch_name, patch_data) -> None:
        from tab5_Patches.tab5_patch_editor import open_patch_editor
        if self.patch_editor_dialog:
            try:
                self.patch_editor_dialog.dialog.destroy()
            except Exception:
                pass
        if self.renderer:
            self.renderer.set_click_override(self._route_click_to_editor)
        self.patch_editor_dialog = open_patch_editor(
            parent=self.parent, mesh_data=self.mesh_data,
            colors=self.colors, patch_name=patch_name,
            patch_data=patch_data, renderer=self.renderer,
            on_save_callback=self._on_patch_editor_save,
        )
        if self.renderer:
            self.renderer.patch_edit_mode = True

    def _route_click_to_editor(self, face_id: int) -> None:
        if self.patch_editor_dialog:
            try:
                self.patch_editor_dialog.toggle_face_selection(face_id)
            except Exception:
                pass

    def _on_patch_editor_save(self) -> None:
        if hasattr(self, 'patch_list_panel'):
            self.patch_list_panel.refresh_list()
        if self.renderer:
            self.renderer.patch_edit_mode = False
            self.renderer.set_click_override(None)
            self.renderer.selected_faces.clear()
            self.renderer.invalidate_cache()
            self.renderer.draw()
        self.patch_editor_dialog = None
        self._update_status()

    def _on_tab_changed(self, event) -> None:
        idx = self.notebook.index(self.notebook.select())
        if idx == 2 and self.normals_tab and self.renderer:
            self.renderer.set_patch_edit_mode(True, self.normals_tab)
            self.normals_tab.renderer = self.renderer
        else:
            if self.renderer and not self.patch_editor_dialog:
                self.renderer.set_patch_edit_mode(False)

    # ── patch assignment ──────────────────────────────────────────────────

    def _on_patch_assigned(self, patch_data: dict) -> None:
        if 'clear' in patch_data:
            if self.renderer:
                self.renderer.clear_selection()
            return

        patch_name = patch_data.get('name')
        if not patch_name:
            messagebox.showwarning("Warning", "Patch name is missing")
            return

        self.mesh_data.save_state()
        mode = patch_data.get('mode', 'overwrite')

        if patch_name in self.mesh_data.patches and mode == 'append':
            existing  = self.mesh_data.patches[patch_name]
            ex_faces  = existing.get('faces', [])
            ex_ids    = {(f.get('face_id') if isinstance(f, dict) else f)
                         for f in ex_faces}
            merged    = list(ex_faces)
            for face in patch_data.get('faces', []):
                fid = face.get('face_id') if isinstance(face, dict) else face
                if fid not in ex_ids:
                    merged.append(face)
                    ex_ids.add(fid)
            existing['faces'] = merged
        else:
            store = {k: v for k, v in patch_data.items() if k != 'mode'}
            self.mesh_data.patches[patch_name] = store

        self.patch_list_panel.refresh_list()
        if self.renderer:
            self.renderer.invalidate_cache()
            self.renderer.clear_selection()
        self._update_status()

    def _on_patch_selected(self, patch_name, patch_data,
                           highlight_faces=None) -> None:
        if highlight_faces and self.renderer:
            # Use highlight_faces() which validates ids and builds geometry first
            face_ids = [f for f in highlight_faces if f is not None]
            self.renderer.highlight_faces(face_ids)
            self.patch_panel.set_selected_faces(face_ids)
            self.selected_count_label.config(
                text=f"Selected faces: {len(face_ids)}")

    # ── status ────────────────────────────────────────────────────────────

    def _update_status(self) -> None:
        num_blocks = len(getattr(self.mesh_data, 'hex_blocks', {}))
        self.block_count_label.config(text=f"Blocks: {num_blocks}")

        if self.renderer:
            visible = sum(1 for f in self.renderer.all_faces
                          if f.get('is_visible', False))
            self.face_count_label.config(text=f"Visible faces: {visible}")

        num_patches = len(getattr(self.mesh_data, 'patches', {}))
        self.status_label.config(
            text=f"Ready – {num_patches} patches defined",
            fg=self.colors['success'])