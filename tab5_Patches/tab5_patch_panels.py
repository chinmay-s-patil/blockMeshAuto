"""
Simplified Patch Assignment Panel for Tab 5
Just blockMesh boundary types, no complex field definitions
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext


class PatchAssignmentPanel:
    """
    Simplified panel for assigning blockMesh boundary types to faces.
    """

    def __init__(self, parent, mesh_data, colors, on_assign_callback):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.on_assign_callback = on_assign_callback

        # Import simplified patch config
        from tab5_Patches.tab5_patch_config import (
            get_patch_types, get_patch_info, get_parameters, is_custom
        )
        self.get_patch_types = get_patch_types
        self.get_patch_info = get_patch_info
        self.get_parameters = get_parameters
        self.is_custom = is_custom

        # State
        self.selected_faces = []
        self.current_patch_type = tk.StringVar(value="patch")
        self.param_vars = {}
        self.custom_type_var = tk.StringVar(value="")

        self.setup_ui()
        self._update_parameters()

    def setup_ui(self):
        """Create the patch assignment UI"""
        main_frame = tk.LabelFrame(self.parent, text="Patch Assignment", 
                                   padx=10, pady=10,
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   font=("Arial", 10, "bold"))
        main_frame.pack(fill=tk.X, padx=5, pady=5)

        # Selected faces indicator
        self.selection_label = tk.Label(main_frame, 
                                       text="Selected: 0 faces",
                                       font=("Arial", 10, "bold"),
                                       fg=self.colors['success'],
                                       bg=self.colors['secondary'])
        self.selection_label.pack(anchor=tk.W, pady=(0, 10))

        # Patch name
        name_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        name_frame.pack(fill=tk.X, pady=5)

        tk.Label(name_frame, text="Patch Name:", 
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        self.patch_name_entry = tk.Entry(name_frame, 
                                        bg=self.colors['text_bg'],
                                        fg=self.colors['text_fg'],
                                        insertbackground=self.colors['fg'],
                                        highlightbackground=self.colors['border'],
                                        font=("Arial", 10))
        self.patch_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Patch type dropdown
        type_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        type_frame.pack(fill=tk.X, pady=5)

        tk.Label(type_frame, text="Type:", 
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        patch_types = self.get_patch_types()
        self.type_combo = ttk.Combobox(type_frame, 
                                      textvariable=self.current_patch_type,
                                      values=patch_types,
                                      state="readonly",
                                      width=20)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # Description label
        self.description_label = tk.Label(main_frame, 
                                         text="",
                                         font=("Arial", 8, "italic"),
                                         fg=self.colors['fg'],
                                         bg=self.colors['secondary'],
                                         wraplength=350,
                                         justify=tk.LEFT)
        self.description_label.pack(anchor=tk.W, pady=5)

        # Parameters frame
        self.params_frame = tk.LabelFrame(main_frame, text="Parameters", 
                                         padx=5, pady=5,
                                         bg=self.colors['secondary'],
                                         fg=self.colors['fg'],
                                         highlightbackground=self.colors['border'])
        self.params_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Custom type frame (hidden by default)
        self.custom_frame = tk.Frame(self.params_frame, bg=self.colors['secondary'])

        tk.Label(self.custom_frame, text="Custom Type:", 
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))

        self.custom_entry = tk.Entry(self.custom_frame, 
                                     textvariable=self.custom_type_var,
                                     bg=self.colors['text_bg'],
                                     fg=self.colors['text_fg'],
                                     insertbackground=self.colors['fg'],
                                     highlightbackground=self.colors['border'],
                                     font=("Arial", 10))
        self.custom_entry.pack(fill=tk.X)

        tk.Label(self.custom_frame, 
                text="Enter any OpenFOAM boundary type (e.g., 'pressureInletOutletVelocity')",
                font=("Arial", 8, "italic"),
                fg=self.colors['axis'],
                bg=self.colors['secondary'],
                wraplength=300).pack(anchor=tk.W, pady=(5, 0))

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="✓ Assign to Selected Faces", 
                 command=self._assign_patch,
                 bg=self.colors['success'], fg=self.colors['bg'],
                 font=("Arial", 10, "bold"), relief=tk.FLAT,
                 activebackground='#3db89f').pack(fill=tk.X, pady=2)

        tk.Button(btn_frame, text="✗ Clear Selection", 
                 command=self._clear_selection,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 font=("Arial", 9), relief=tk.FLAT,
                 activebackground='#d63636').pack(fill=tk.X, pady=2)

        # Initialize
        self._update_description()
        self._update_parameters()

    def _on_type_change(self, event=None):
        """Handle patch type change"""
        self._update_description()
        self._update_parameters()

    def _update_description(self):
        """Update description label"""
        patch_type = self.current_patch_type.get()
        info = self.get_patch_info(patch_type)

        if info:
            desc = info.get("description", "No description")
            self.description_label.config(text=desc)
        else:
            self.description_label.config(text="")

    def _update_parameters(self):
        """Update parameter inputs based on patch type"""
        # Clear existing parameter widgets
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

        # Get parameters for this type
        params = self.get_parameters(patch_type)

        if not params:
            tk.Label(self.params_frame, 
                    text="No additional parameters required",
                    font=("Arial", 8, "italic"),
                    fg=self.colors['axis'],
                    bg=self.colors['secondary']).pack(pady=10)
            return

        # Create parameter inputs
        for param_name, param_info in params.items():
            row = tk.Frame(self.params_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=3)

            label_text = param_info.get("label", param_name)
            default_value = param_info.get("default", "")

            tk.Label(row, text=f"{label_text}:", 
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg'],
                    font=("Arial", 9),
                    width=20,
                    anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value=default_value)
            entry = tk.Entry(row, textvariable=var,
                           bg=self.colors['text_bg'],
                           fg=self.colors['text_fg'],
                           insertbackground=self.colors['fg'],
                           highlightbackground=self.colors['border'])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.param_vars[param_name] = var

    def set_selected_faces(self, face_ids):
        """Update selected faces from external source"""
        self.selected_faces = list(face_ids)
        self.selection_label.config(
            text=f"Selected: {len(self.selected_faces)} face(s)",
            fg=self.colors['success'] if self.selected_faces else self.colors['warning']
        )

    def _assign_patch(self):
        """Assign patch to selected faces"""
        if not self.selected_faces:
            messagebox.showwarning("Warning", "No faces selected")
            return

        patch_name = self.patch_name_entry.get().strip()
        if not patch_name:
            messagebox.showwarning("Warning", "Please enter a patch name")
            return

        # Get patch type
        patch_type = self.current_patch_type.get()

        # For custom type, use the custom entry
        if self.is_custom(patch_type):
            openfoam_type = self.custom_type_var.get().strip()
            if not openfoam_type:
                messagebox.showwarning("Warning", "Please enter a custom boundary type")
                return
        else:
            info = self.get_patch_info(patch_type)
            openfoam_type = info.get("openfoam_type", patch_type)

        # Get parameter values
        params = {}
        for param_name, var in self.param_vars.items():
            params[param_name] = var.get()

        # Check if patch exists
        if hasattr(self.mesh_data, 'patches') and patch_name in self.mesh_data.patches:
            if not messagebox.askyesno("Confirm", 
                                      f"Patch '{patch_name}' already exists.\n"
                                      "Add faces to existing patch?"):
                return

        # Create patch data
        patch_data = {
            'name': patch_name,
            'type': openfoam_type,
            'faces': self.selected_faces.copy(),
            'parameters': params
        }

        # Notify callback
        if self.on_assign_callback:
            self.on_assign_callback(patch_data)

        messagebox.showinfo("Success", 
                          f"Assigned {len(self.selected_faces)} faces to patch '{patch_name}'\n"
                          f"Type: {openfoam_type}")

    def _clear_selection(self):
        """Clear face selection"""
        self.selected_faces = []
        self.selection_label.config(text="Selected: 0 faces", fg=self.colors['warning'])
        if self.on_assign_callback:
            self.on_assign_callback({'clear': True})


class PatchListPanel:
    """Panel for displaying and managing defined patches"""

    def __init__(self, parent, mesh_data, colors, on_select_callback, on_edit_callback=None):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.on_select_callback = on_select_callback
        self.on_edit_callback = on_edit_callback

        self.setup_ui()

    def setup_ui(self):
        """Create the patch list UI"""
        main_frame = tk.LabelFrame(self.parent, text="Defined Patches", 
                                   padx=10, pady=10,
                                   bg=self.colors['secondary'],
                                   fg=self.colors['fg'],
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   font=("Arial", 10, "bold"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Listbox with scrollbar
        list_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.patch_listbox = tk.Listbox(list_frame, 
                                       font=("Courier", 9),
                                       yscrollcommand=scrollbar.set,
                                       bg=self.colors['text_bg'],
                                       fg=self.colors['text_fg'],
                                       selectbackground=self.colors['accent'],
                                       selectforeground=self.colors['button_fg'],
                                       highlightbackground=self.colors['border'])
        self.patch_listbox.pack(fill=tk.BOTH, expand=True)
        self.patch_listbox.bind('<<ListboxSelect>>', self._on_patch_select)

        scrollbar.config(command=self.patch_listbox.yview)

        # Info label
        self.info_label = tk.Label(main_frame, text="",
                                  font=("Arial", 8),
                                  fg=self.colors['fg'],
                                  bg=self.colors['secondary'],
                                  justify=tk.LEFT,
                                  wraplength=350)
        self.info_label.pack(anchor=tk.W, pady=5)

        # Buttons - REMOVED Add button, only Edit, Delete, Highlight, Refresh
        btn_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=5)

        # Edit button
        tk.Button(btn_frame, text="Edit", 
                 command=self._edit_patch,
                 bg=self.colors['accent'], 
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(btn_frame, text="Delete", 
                 command=self._delete_patch,
                 bg=self.colors['error'], 
                 fg=self.colors['button_fg'],
                 activebackground='#d63636').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(btn_frame, text="Highlight", 
                 command=self._highlight_patch,
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Button(btn_frame, text="Refresh", 
                 command=self.refresh_list,
                 bg=self.colors['button_bg'], 
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def refresh_list(self):
        """Refresh the patch list"""
        self.patch_listbox.delete(0, tk.END)

        if not hasattr(self.mesh_data, 'patches'):
            return

        for patch_name, patch_data in self.mesh_data.patches.items():
            if isinstance(patch_data, dict):
                num_faces = len(patch_data.get('faces', []))
                patch_type = patch_data.get('type', 'unknown')
            else:
                # Handle tuple format
                num_faces = len(patch_data[2]) if len(patch_data) > 2 else 0
                patch_type = patch_data[1] if len(patch_data) > 1 else 'unknown'

            display_text = f"{patch_name}: {patch_type} ({num_faces} faces)"
            self.patch_listbox.insert(tk.END, display_text)

    def _on_patch_select(self, event):
        """Handle patch selection"""
        sel = self.patch_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        if hasattr(self.mesh_data, 'patches'):
            patch_names = list(self.mesh_data.patches.keys())
            if idx < len(patch_names):
                patch_name = patch_names[idx]
                patch_data = self.mesh_data.patches[patch_name]

                # Show info
                info = f"Name: {patch_name}\n"
                if isinstance(patch_data, dict):
                    info += f"Type: {patch_data.get('type', 'unknown')}\n"
                    info += f"Faces: {len(patch_data.get('faces', []))}"
                    params = patch_data.get('parameters', {})
                else:
                    info += f"Type: {patch_data[1] if len(patch_data) > 1 else 'unknown'}\n"
                    info += f"Faces: {len(patch_data[2]) if len(patch_data) > 2 else 0}"
                    params = {}

                if params:
                    info += "\nParameters:"
                    for k, v in params.items():
                        info += f"\n  {k}: {v}"

                self.info_label.config(text=info)

                # Notify callback
                if self.on_select_callback:
                    self.on_select_callback(patch_name, patch_data)

    def _edit_patch(self):
        """Open patch editor for selected patch"""
        sel = self.patch_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a patch to edit")
            return

        idx = sel[0]
        if hasattr(self.mesh_data, 'patches'):
            patch_names = list(self.mesh_data.patches.keys())
            if idx < len(patch_names):
                patch_name = patch_names[idx]
                patch_data = self.mesh_data.patches[patch_name]

                # Call the edit callback
                if self.on_edit_callback:
                    self.on_edit_callback(patch_name, patch_data)
                else:
                    messagebox.showinfo("Info", "Edit functionality not configured")

    def _delete_patch(self):
        """Delete selected patch"""
        sel = self.patch_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a patch to delete")
            return

        idx = sel[0]
        if hasattr(self.mesh_data, 'patches'):
            patch_names = list(self.mesh_data.patches.keys())
            if idx < len(patch_names):
                patch_name = patch_names[idx]
                if messagebox.askyesno("Confirm", f"Delete patch '{patch_name}'?"):
                    del self.mesh_data.patches[patch_name]
                    self.refresh_list()
                    self.info_label.config(text="")

    def _highlight_patch(self):
        """Highlight faces of selected patch"""
        sel = self.patch_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        if hasattr(self.mesh_data, 'patches'):
            patch_names = list(self.mesh_data.patches.keys())
            if idx < len(patch_names):
                patch_name = patch_names[idx]
                patch_data = self.mesh_data.patches[patch_name]

                if isinstance(patch_data, dict):
                    faces = patch_data.get('faces', [])
                else:
                    faces = patch_data[2] if len(patch_data) > 2 else []

                if self.on_select_callback:
                    self.on_select_callback(patch_name, patch_data, highlight_faces=faces)