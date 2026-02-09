"""
Patch Editor Dialog for Tab 5
Allows editing patch name, type, and faces
"""
import tkinter as tk
from tkinter import messagebox, ttk


class PatchEditorDialog:
    """
    Dialog window for editing an existing patch.
    Allows changing name, boundary type, and selecting/deselecting faces.
    """

    def __init__(self, parent, mesh_data, colors, patch_name, patch_data, renderer, on_save_callback):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.original_name = patch_name
        self.patch_data = patch_data
        self.renderer = renderer
        self.on_save_callback = on_save_callback

        # Import patch config functions
        from tab5_Patches.tab5_patch_config import (
            get_patch_types, get_patch_info, get_parameters, is_custom
        )
        self.get_patch_types = get_patch_types
        self.get_patch_info = get_patch_info
        self.get_parameters = get_parameters
        self.is_custom = is_custom

        # State
        self.selected_faces = set(patch_data.get('faces', []))
        self.current_patch_type = tk.StringVar(value="patch")
        self.param_vars = {}
        self.custom_type_var = tk.StringVar(value="")

        # Track faces added from 3D view (for Add functionality)
        self.newly_added_faces = set()

        self.create_dialog()

    def create_dialog(self):
        """Create the edit dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Edit Patch: {self.original_name}")
        self.dialog.geometry("700x650")
        self.dialog.configure(bg=self.colors['bg'])

        # Make window stay on top but NOT modal (no grab_set)
        self.dialog.transient(self.parent)
        self.dialog.attributes('-topmost', True)

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        # Main container
        main_frame = tk.Frame(self.dialog, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(main_frame, text="Edit Patch", 
                font=("Arial", 16, "bold"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=(0, 15))

        # Split into left (settings) and right (face selection)
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # LEFT: Patch settings
        left_frame = tk.Frame(content_frame, bg=self.colors['secondary'], padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._setup_settings_panel(left_frame)

        # RIGHT: Face selection
        right_frame = tk.Frame(content_frame, bg=self.colors['secondary'], padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._setup_face_selection_panel(right_frame)

        # Bottom buttons
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Button(btn_frame, text="Save Changes", 
                 command=self._save_changes,
                 bg=self.colors['success'], 
                 fg=self.colors['bg'],
                 font=("Arial", 11, "bold"), 
                 relief=tk.FLAT,
                 activebackground='#3db89f',
                 height=2).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(btn_frame, text="Cancel", 
                 command=self._on_close,
                 bg=self.colors['error'], 
                 fg=self.colors['button_fg'],
                 font=("Arial", 10), 
                 relief=tk.FLAT,
                 activebackground='#d63636',
                 height=2).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Initialize values from existing patch
        self._load_patch_data()

        # Update renderer to highlight selected faces
        self._update_renderer_highlight()

    def _on_close(self):
        """Handle dialog close"""
        # Restore normal renderer view
        if self.renderer:
            self.renderer.patch_edit_mode = False
            self.renderer.selected_faces.clear()
            self.renderer.draw()

        # Notify callback
        if self.on_save_callback:
            self.on_save_callback()

        # Destroy dialog
        self.dialog.destroy()

    def _setup_settings_panel(self, parent):
        """Setup the patch settings panel"""
        tk.Label(parent, text="Patch Settings", 
                font=("Arial", 12, "bold"),
                bg=self.colors['secondary'], 
                fg=self.colors['accent']).pack(anchor=tk.W, pady=(0, 10))

        # Patch name
        name_frame = tk.Frame(parent, bg=self.colors['secondary'])
        name_frame.pack(fill=tk.X, pady=5)

        tk.Label(name_frame, text="Patch Name:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg'],
                font=("Arial", 9, "bold")).pack(anchor=tk.W)

        self.name_entry = tk.Entry(name_frame, 
                                  bg=self.colors['text_bg'],
                                  fg=self.colors['text_fg'],
                                  insertbackground=self.colors['fg'],
                                  font=("Arial", 10))
        self.name_entry.pack(fill=tk.X, pady=(5, 0))

        # Patch type
        type_frame = tk.Frame(parent, bg=self.colors['secondary'])
        type_frame.pack(fill=tk.X, pady=10)

        tk.Label(type_frame, text="Boundary Type:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg'],
                font=("Arial", 9, "bold")).pack(anchor=tk.W)

        patch_types = self.get_patch_types()
        self.type_combo = ttk.Combobox(type_frame, 
                                      textvariable=self.current_patch_type,
                                      values=patch_types,
                                      state="readonly",
                                      width=25)
        self.type_combo.pack(fill=tk.X, pady=(5, 0))
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # Description
        self.description_label = tk.Label(parent, 
                                         text="",
                                         font=("Arial", 8, "italic"),
                                         fg=self.colors['fg'],
                                         bg=self.colors['secondary'],
                                         wraplength=300,
                                         justify=tk.LEFT)
        self.description_label.pack(anchor=tk.W, pady=5)

        # Parameters frame
        self.params_frame = tk.LabelFrame(parent, 
                                         text="Parameters", 
                                         padx=5, 
                                         pady=5,
                                         bg=self.colors['secondary'],
                                         fg=self.colors['fg'],
                                         font=("Arial", 9, "bold"))
        self.params_frame.pack(fill=tk.X, pady=10)

        # Custom type frame
        self.custom_frame = tk.Frame(self.params_frame, 
                                    bg=self.colors['secondary'])

        tk.Label(self.custom_frame, 
                text="Custom Type:", 
                bg=self.colors['secondary'], 
                fg=self.colors['fg'],
                font=("Arial", 9)).pack(anchor=tk.W)

        self.custom_entry = tk.Entry(self.custom_frame, 
                                     textvariable=self.custom_type_var,
                                     bg=self.colors['text_bg'],
                                     fg=self.colors['text_fg'],
                                     insertbackground=self.colors['fg'],
                                     font=("Arial", 10))
        self.custom_entry.pack(fill=tk.X, pady=(5, 0))

        # Selected faces count
        self.faces_count_label = tk.Label(parent, 
                                         text="Selected Faces: 0",
                                         font=("Arial", 10, "bold"),
                                         fg=self.colors['success'],
                                         bg=self.colors['secondary'])
        self.faces_count_label.pack(anchor=tk.W, pady=(10, 0))

    def _setup_face_selection_panel(self, parent):
        """Setup the face selection panel with Add/Remove buttons"""
        tk.Label(parent, text="Face Selection", 
                font=("Arial", 12, "bold"),
                bg=self.colors['secondary'], 
                fg=self.colors['accent']).pack(anchor=tk.W, pady=(0, 10))

        # Instructions
        tk.Label(parent, 
                text="Click faces in the 3D view to select/deselect.\nSelected faces are highlighted in green.",
                font=("Arial", 8),
                fg=self.colors['fg'],
                bg=self.colors['secondary'],
                wraplength=280,
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        # Face list with scrollbar
        list_frame = tk.Frame(parent, bg=self.colors['border'], bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, bg=self.colors['secondary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.face_listbox = tk.Listbox(list_frame, 
                                      font=("Consolas", 9),
                                      bg=self.colors['text_bg'],
                                      fg=self.colors['text_fg'],
                                      selectbackground=self.colors['accent'],
                                      selectforeground=self.colors['button_fg'],
                                      yscrollcommand=scrollbar.set,
                                      relief=tk.FLAT)
        self.face_listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=self.face_listbox.yview)

        # NEW: Add and Remove buttons
        add_remove_frame = tk.Frame(parent, bg=self.colors['secondary'])
        add_remove_frame.pack(fill=tk.X, pady=10)

        tk.Button(add_remove_frame, 
                 text="➕ Add Selected from 3D",
                 command=self._add_selected_from_3d,
                 bg=self.colors['success'], 
                 fg=self.colors['bg'],
                 font=("Arial", 9, "bold"),
                 relief=tk.FLAT,
                 activebackground='#3db89f').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(add_remove_frame, 
                 text="➖ Remove Selected",
                 command=self._remove_selected_from_list,
                 bg=self.colors['error'], 
                 fg=self.colors['button_fg'],
                 font=("Arial", 9, "bold"),
                 relief=tk.FLAT,
                 activebackground='#d63636').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Buttons
        btn_frame = tk.Frame(parent, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, 
                 text="Select All Visible",
                 command=self._select_all_visible,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'],
                 font=("Arial", 9),
                 relief=tk.FLAT,
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(btn_frame, 
                 text="Clear All",
                 command=self._clear_all_faces,
                 bg=self.colors['error'],
                 fg=self.colors['button_fg'],
                 font=("Arial", 9),
                 relief=tk.FLAT,
                 activebackground='#d63636').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def _load_patch_data(self):
        """Load existing patch data into the form"""
        # Set name
        self.name_entry.insert(0, self.original_name)

        # Set type
        patch_type = self.patch_data.get('type', 'patch')

        # Check if it's a custom type
        standard_types = self.get_patch_types()
        if patch_type in standard_types:
            self.current_patch_type.set(patch_type)
        else:
            self.current_patch_type.set('custom')
            self.custom_type_var.set(patch_type)

        # Load parameters
        params = self.patch_data.get('parameters', {})
        for param_name, value in params.items():
            if param_name in self.param_vars:
                self.param_vars[param_name].set(value)

        # Update UI
        self._on_type_change()
        self._update_face_list()

    def _on_type_change(self, event=None):
        """Handle patch type change"""
        patch_type = self.current_patch_type.get()

        # Update description
        info = self.get_patch_info(patch_type)
        if info:
            desc = info.get("description", "No description")
            self.description_label.config(text=desc)
        else:
            self.description_label.config(text="")

        # Update parameters
        self._update_parameters()

    def _update_parameters(self):
        """Update parameter inputs based on patch type"""
        # Clear existing
        for widget in self.params_frame.winfo_children():
            if widget != self.custom_frame:
                widget.destroy()

        self.param_vars.clear()
        self.custom_frame.pack_forget()

        patch_type = self.current_patch_type.get()

        # Show custom input for custom type
        if self.is_custom(patch_type):
            self.custom_frame.pack(fill=tk.X, pady=5)
            return

        # Get parameters
        params = self.get_parameters(patch_type)

        if not params:
            tk.Label(self.params_frame, 
                    text="No additional parameters required",
                    font=("Arial", 8, "italic"),
                    fg=self.colors['axis'],
                    bg=self.colors['secondary']).pack(pady=10)
            return

        # Create inputs
        for param_name, param_info in params.items():
            row = tk.Frame(self.params_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=3)

            label_text = param_info.get("label", param_name)
            default_value = param_info.get("default", "")

            tk.Label(row, 
                    text=f"{label_text}:", 
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg'],
                    font=("Arial", 9),
                    width=15,
                    anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value=default_value)
            entry = tk.Entry(row, 
                           textvariable=var,
                           bg=self.colors['text_bg'],
                           fg=self.colors['text_fg'],
                           insertbackground=self.colors['fg'])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.param_vars[param_name] = var

    def _update_face_list(self):
        """Update the face listbox"""
        self.face_listbox.delete(0, tk.END)

        # Sort faces by ID
        sorted_faces = sorted(self.selected_faces)

        for face_id in sorted_faces:
            # Get face info from renderer if available
            face_info = self._get_face_info(face_id)
            self.face_listbox.insert(tk.END, face_info)

        # Update count
        self.faces_count_label.config(
            text=f"Selected Faces: {len(self.selected_faces)}",
            fg=self.colors['success'] if self.selected_faces else self.colors['warning']
        )

    def _get_face_info(self, face_id):
        """Get human-readable info for a face"""
        if self.renderer and hasattr(self.renderer, 'all_faces'):
            for face in self.renderer.all_faces:
                if face['face_id'] == face_id:
                    block_idx = face.get('block_idx', '?')
                    face_name = face.get('face_name', 'unknown')
                    return f"Face {face_id} (Block {block_idx}, {face_name})"
        return f"Face {face_id}"

    def _update_renderer_highlight(self):
        """Update renderer to highlight selected faces"""
        if self.renderer:
            self.renderer.selected_faces = self.selected_faces.copy()
            self.renderer.draw()

    def toggle_face_selection(self, face_id):
        """Toggle a face's selection state (called from renderer)"""
        if face_id in self.selected_faces:
            self.selected_faces.remove(face_id)
        else:
            self.selected_faces.add(face_id)

        self._update_face_list()
        self._update_renderer_highlight()

    def _add_selected_from_3d(self):
        """NEW: Add faces currently selected in 3D view to the patch"""
        if not self.renderer:
            return

        # Get faces selected in the 3D renderer
        faces_from_3d = self.renderer.selected_faces.copy()

        if not faces_from_3d:
            messagebox.showinfo("Info", "No faces selected in 3D view.\nClick on faces in the 3D view to select them first.")
            return

        # Add new faces (avoid duplicates)
        original_count = len(self.selected_faces)
        self.selected_faces.update(faces_from_3d)
        added_count = len(self.selected_faces) - original_count

        if added_count > 0:
            self._update_face_list()
            messagebox.showinfo("Success", f"Added {added_count} face(s) from 3D view.")
        else:
            messagebox.showinfo("Info", "All selected faces are already in this patch.")

    def _remove_selected_from_list(self):
        """NEW: Remove selected faces from the listbox/patch"""
        sel = self.face_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select faces in the list to remove them.")
            return

        # Get the face IDs to remove (need to map listbox index to face_id)
        # Since listbox is sorted, we can get the face_id from sorted list
        sorted_faces = sorted(self.selected_faces)
        faces_to_remove = [sorted_faces[i] for i in sel]

        # Remove from selected_faces
        for face_id in faces_to_remove:
            self.selected_faces.discard(face_id)

        self._update_face_list()
        self._update_renderer_highlight()

        messagebox.showinfo("Success", f"Removed {len(faces_to_remove)} face(s) from patch.")

    def _select_all_visible(self):
        """Select all visible faces"""
        if self.renderer and hasattr(self.renderer, 'all_faces'):
            for face in self.renderer.all_faces:
                if face.get('is_visible', True) and not face.get('is_internal', False):
                    self.selected_faces.add(face['face_id'])

        self._update_face_list()
        self._update_renderer_highlight()

    def _clear_all_faces(self):
        """Clear all face selections"""
        self.selected_faces.clear()
        self._update_face_list()
        self._update_renderer_highlight()

    def _save_changes(self):
        """Save the edited patch"""
        new_name = self.name_entry.get().strip()

        if not new_name:
            messagebox.showwarning("Warning", "Please enter a patch name")
            return

        if not self.selected_faces:
            messagebox.showwarning("Warning", "Please select at least one face")
            return

        # Get patch type
        patch_type = self.current_patch_type.get()

        if self.is_custom(patch_type):
            openfoam_type = self.custom_type_var.get().strip()
            if not openfoam_type:
                messagebox.showwarning("Warning", "Please enter a custom boundary type")
                return
        else:
            info = self.get_patch_info(patch_type)
            openfoam_type = info.get("openfoam_type", patch_type)

        # Get parameters
        params = {}
        for param_name, var in self.param_vars.items():
            params[param_name] = var.get()

        # Check for name collision (if name changed)
        if new_name != self.original_name and new_name in self.mesh_data.patches:
            if not messagebox.askyesno("Confirm", 
                                      f"Patch '{new_name}' already exists.\nOverwrite?"):
                return

        # Create updated patch data
        updated_patch = {
            'name': new_name,
            'type': openfoam_type,
            'faces': list(self.selected_faces),
            'parameters': params
        }

        # Remove old patch if name changed
        if new_name != self.original_name and self.original_name in self.mesh_data.patches:
            del self.mesh_data.patches[self.original_name]

        # Save to mesh_data
        self.mesh_data.patches[new_name] = updated_patch

        # Close dialog
        self._on_close()

        messagebox.showinfo("Success", f"Patch '{new_name}' updated successfully!")


def open_patch_editor(parent, mesh_data, colors, patch_name, patch_data, renderer, on_save_callback):
    """
    Open the patch editor dialog.

    Args:
        parent: Parent widget
        mesh_data: MeshData object
        colors: Color scheme dict
        patch_name: Name of patch to edit
        patch_data: Current patch data
        renderer: HexBlockRenderer instance for face selection
        on_save_callback: Function to call after saving
    """
    return PatchEditorDialog(parent, mesh_data, colors, patch_name, patch_data, renderer, on_save_callback)