"""
Hex Block Editor Dialog Module
Handles the edit block window with full division controls
"""
import tkinter as tk
from tkinter import messagebox
import numpy as np

from tab4_Hex.tab4_utils import calculate_divisions_from_cell_size, get_block_vertices


class HexBlockEditor:
    """Editor dialog for individual hex blocks with full controls"""

    def __init__(self, parent, colors, mesh_data, block_id, block_data, on_save_callback):
        self.parent = parent
        self.colors = colors
        self.mesh_data = mesh_data
        self.block_id = block_id
        self.block_data = block_data
        self.on_save_callback = on_save_callback

        # Division entry widgets for enabling/disabling
        self.div_entries = {}

        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit Block {block_id}")
        self.window.geometry("400x750")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(bg=self.colors['secondary'])

        self.setup_ui()

    def setup_ui(self):
        """Create the edit dialog UI"""
        frame = tk.Frame(self.window, padx=10, pady=10, bg=self.colors['secondary'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text=f"Editing Block {self.block_id}", 
                font=("Segoe UI", 12, "bold"), 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(pady=(0, 10))

        # === MESH TYPE SELECTION ===
        mesh_type_frame = tk.LabelFrame(frame, text="Mesh Type", 
                                        padx=5, pady=5,
                                        bg=self.colors['secondary'], 
                                        fg=self.colors['fg'],
                                        highlightbackground=self.colors['border'],
                                        font=("Segoe UI", 9, "bold"))
        mesh_type_frame.pack(fill=tk.X, pady=5)

        self.sizing_mode = tk.StringVar(value="3d")
        self.single_div_dir = tk.StringVar(value="Z")

        # Check if current block is 2D (has 1 division in any direction)
        current_divs = self.block_data.get('divisions', (1, 1, 1))
        if 1 in current_divs:
            self.sizing_mode.set("2d")
            if current_divs[0] == 1:
                self.single_div_dir.set("X")
            elif current_divs[1] == 1:
                self.single_div_dir.set("Y")
            else:
                self.single_div_dir.set("Z")

        tk.Radiobutton(mesh_type_frame, text="3D Mesh",
                      variable=self.sizing_mode, value="3d",
                      command=self.update_division_ui, font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg']).pack(anchor=tk.W)

        row2d = tk.Frame(mesh_type_frame, bg=self.colors['secondary'])
        row2d.pack(fill=tk.X, pady=2)
        tk.Radiobutton(row2d, text="2D Mesh (1 div in:",
                      variable=self.sizing_mode, value="2d",
                      command=self.update_division_ui, font=("Segoe UI", 9),
                      bg=self.colors['secondary'], fg=self.colors['fg'],
                      selectcolor=self.colors['bg']).pack(side=tk.LEFT)

        for direction in ["X", "Y", "Z"]:
            tk.Radiobutton(row2d, text=direction,
                          variable=self.single_div_dir, value=direction,
                          command=self.update_division_ui, font=("Segoe UI", 8),
                          bg=self.colors['secondary'], fg=self.colors['fg'],
                          selectcolor=self.colors['bg']).pack(side=tk.LEFT, padx=2)

        # === DIVISIONS ===
        div_frame = tk.LabelFrame(frame, text="Divisions", 
                                  padx=5, pady=5,
                                  bg=self.colors['secondary'], 
                                  fg=self.colors['fg'],
                                  highlightbackground=self.colors['border'],
                                  font=("Segoe UI", 9, "bold"))
        div_frame.pack(fill=tk.X, pady=5)

        nx, ny, nz = self.block_data.get('divisions', (1, 1, 1))

        self.nx_var = tk.IntVar(value=nx)
        self.ny_var = tk.IntVar(value=ny)
        self.nz_var = tk.IntVar(value=nz)

        for label, var, key in [("X divisions:", self.nx_var, 'X'),
                                ("Y divisions:", self.ny_var, 'Y'),
                                ("Z divisions:", self.nz_var, 'Z')]:
            row = tk.Frame(div_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=var,
                    bg=self.colors['text_bg'],
                    fg=self.colors['text_fg'], 
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border'],
                    disabledbackground=self.colors.get('disabled_bg', '#3e3e42'),
                    disabledforeground=self.colors.get('disabled_fg', '#808080'))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.div_entries[key] = entry

        # === AUTO-CALCULATE FROM CELL SIZE ===
        calc_frame = tk.LabelFrame(frame, text="Auto-Calculate from Cell Size", 
                                   padx=5, pady=5,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   font=("Segoe UI", 9, "bold"))
        calc_frame.pack(fill=tk.X, pady=5)

        self.cell_size_var = tk.DoubleVar(value=1.0)

        row = tk.Frame(calc_frame, bg=self.colors['secondary'])
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text="Cell size:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.cell_size_var, width=10,
                bg=self.colors['text_bg'],
                fg=self.colors['text_fg'],
                insertbackground=self.colors['fg'],
                highlightbackground=self.colors['border']).pack(side=tk.LEFT, padx=5)
        tk.Button(row, text="Calculate", command=self.calculate_from_cell_size,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

        # === GRADING ===
        grade_frame = tk.LabelFrame(frame, text="Grading", 
                                    padx=5, pady=5,
                                    bg=self.colors['secondary'], 
                                    fg=self.colors['fg'],
                                    highlightbackground=self.colors['border'],
                                    font=("Segoe UI", 9, "bold"))
        grade_frame.pack(fill=tk.X, pady=5)

        gp = self.block_data.get('grading_params', {'x': 1, 'y': 1, 'z': 1})

        self.gx_var = tk.DoubleVar(value=gp.get('x', 1))
        self.gy_var = tk.DoubleVar(value=gp.get('y', 1))
        self.gz_var = tk.DoubleVar(value=gp.get('z', 1))

        for label, var in [("X ratio:", self.gx_var),
                          ("Y ratio:", self.gy_var),
                          ("Z ratio:", self.gz_var)]:
            row = tk.Frame(grade_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=10, anchor=tk.W,
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg']).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var,
                    bg=self.colors['text_bg'],
                    fg=self.colors['text_fg'], 
                    insertbackground=self.colors['fg'],
                    highlightbackground=self.colors['border']).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Grading type
        tk.Label(frame, text="Grading Type:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg']).pack(anchor=tk.W, pady=(10, 0))
        self.grading_type_var = tk.StringVar(value=self.block_data.get('grading_type', 'simpleGrading'))
        tk.OptionMenu(frame, self.grading_type_var, "simpleGrading", "edgeGrading", "multiGrading").pack(fill=tk.X)

        # === BUTTONS ===
        btn_frame = tk.Frame(frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=15)

        tk.Button(btn_frame, text="💾 Save Changes", command=self.save_changes,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="👁 Highlight Vertices", command=self.highlight_vertices,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="❌ Cancel", command=self.window.destroy,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 relief=tk.FLAT).pack(fill=tk.X, pady=2)

        # === VERTICES INFO ===
        info_frame = tk.LabelFrame(frame, text="Current Vertices", 
                                   padx=5, pady=5,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   font=("Segoe UI", 9, "bold"))
        info_frame.pack(fill=tk.X, pady=5)

        self._update_vertices_info(info_frame)

        # Initial UI state update
        self.update_division_ui()

    def _update_vertices_info(self, parent_frame):
        """Update the vertices info display"""
        point_refs = self.block_data.get('point_refs', [])

        if len(point_refs) == 8:
            info_text = ""
            all_valid = True
            for i, point_id in enumerate(point_refs):
                point_data = self.mesh_data.get_point(point_id)
                if point_data:
                    info_text += f"{i}: ({point_data['x']:.2f}, {point_data['y']:.2f}, {point_data['z']:.2f})\n"
                else:
                    info_text += f"{i}: [INVALID - point {point_id} not found]\n"
                    all_valid = False

            if not all_valid:
                tk.Label(parent_frame, text="⚠ Some points no longer exist!", 
                        font=("Courier", 8, "bold"), fg=self.colors['error'],
                        bg=self.colors['secondary']).pack(anchor=tk.W, pady=(0, 5))
        else:
            info_text = f"[ERROR: Expected 8 point refs, found {len(point_refs)}]\n"

        text_widget = tk.Text(parent_frame, height=8, wrap=tk.WORD,
                            bg=self.colors['secondary'], 
                            fg=self.colors['fg'],
                            font=("Courier", 8), relief=tk.FLAT,
                            highlightthickness=0, padx=5, pady=5)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

        refs_text = f"Point refs: {point_refs}"
        tk.Label(parent_frame, text=refs_text, font=("Courier", 7), 
                fg=self.colors.get('axis', '#6e6e6e'), 
                bg=self.colors['secondary']).pack(anchor=tk.W, pady=(5, 0))

    def update_division_ui(self):
        """Update division entry states based on 2D/3D mode"""
        is_2d = self.sizing_mode.get() == "2d"
        disabled_dir = self.single_div_dir.get() if is_2d else None

        for direction, entry in self.div_entries.items():
            if is_2d and direction == disabled_dir:
                # Set to 1 and disable
                if direction == 'X':
                    self.nx_var.set(1)
                elif direction == 'Y':
                    self.ny_var.set(1)
                elif direction == 'Z':
                    self.nz_var.set(1)
                entry.config(state='disabled')
            else:
                entry.config(state='normal')

    def calculate_from_cell_size(self):
        """Calculate divisions based on cell size"""
        vertices = get_block_vertices(self.block_data, self.mesh_data)
        if vertices is None:
            messagebox.showerror("Error", "Could not get block vertices - some points may be missing")
            return

        cell_size = self.cell_size_var.get()
        if cell_size <= 0:
            messagebox.showerror("Error", "Cell size must be positive")
            return

        nx, ny, nz = calculate_divisions_from_cell_size(vertices, cell_size)

        # Apply 2D mode if selected
        if self.sizing_mode.get() == "2d":
            if self.single_div_dir.get() == "X":
                nx = 1
            elif self.single_div_dir.get() == "Y":
                ny = 1
            elif self.single_div_dir.get() == "Z":
                nz = 1

        self.nx_var.set(nx)
        self.ny_var.set(ny)
        self.nz_var.set(nz)

        messagebox.showinfo("Calculated", f"Divisions set to: {nx}×{ny}×{nz}")

    def save_changes(self):
        """Save the changes and close"""
        new_data = {
            'divisions': (self.nx_var.get(), self.ny_var.get(), self.nz_var.get()),
            'grading_params': {
                'x': self.gx_var.get(),
                'y': self.gy_var.get(),
                'z': self.gz_var.get()
            },
            'grading_type': self.grading_type_var.get()
        }

        self.on_save_callback(self.block_id, new_data)
        self.window.destroy()

    def highlight_vertices(self):
        """Highlight the block vertices in the viewer"""
        point_refs = self.block_data.get('point_refs', [])
        # This would need to communicate back to the main tab
        # For now, just show info
        messagebox.showinfo("Highlight", f"Block {self.block_id} has {len(point_refs)} vertices\nPoint IDs: {point_refs}")