"""
Patch Assignment Panel for Tab 5
Hierarchical patch type selection with custom parameter inputs
"""
import tkinter as tk
from tkinter import messagebox, ttk


class PatchAssignmentPanel:
    """
    Panel for assigning patches to selected faces.
    Supports hierarchical patch types (general -> specific) with custom inputs.
    """
    
    def __init__(self, parent, mesh_data, colors, on_assign_callback):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.on_assign_callback = on_assign_callback
        
        # Import patch definitions
        from tab5_Patches.tab5_patch_config import (
            get_general_types, get_sub_types, get_editable_fields, get_patch_config
        )
        self.get_general_types = get_general_types
        self.get_sub_types = get_sub_types
        self.get_editable_fields = get_editable_fields
        self.get_patch_config = get_patch_config
        
        # State
        self.selected_faces = []
        self.current_general_type = tk.StringVar(value="wall")
        self.current_sub_type = tk.StringVar(value="noSlip")
        self.custom_values = {}
        
        self.setup_ui()
        self._update_sub_types()
        
    def setup_ui(self):
        """Create the patch assignment UI"""
        # Main frame
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
        
        # General type dropdown
        type_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        type_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(type_frame, text="General Type:", 
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9)).pack(side=tk.LEFT)
        
        general_types = self.get_general_types()
        self.general_combo = ttk.Combobox(type_frame, 
                                         textvariable=self.current_general_type,
                                         values=general_types,
                                         state="readonly",
                                         width=15)
        self.general_combo.pack(side=tk.LEFT, padx=5)
        self.general_combo.bind("<<ComboboxSelected>>", self._on_general_type_change)
        
        # Sub-type dropdown
        sub_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        sub_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(sub_frame, text="Specific Type:", 
                bg=self.colors['secondary'], fg=self.colors['fg'],
                font=("Arial", 9)).pack(side=tk.LEFT)
        
        self.sub_combo = ttk.Combobox(sub_frame, 
                                     textvariable=self.current_sub_type,
                                     state="readonly",
                                     width=20)
        self.sub_combo.pack(side=tk.LEFT, padx=5)
        self.sub_combo.bind("<<ComboboxSelected>>", self._on_sub_type_change)
        
        # Description label
        self.description_label = tk.Label(main_frame, 
                                         text="Select a patch type",
                                         font=("Arial", 8, "italic"),
                                         fg=self.colors['axis'],
                                         bg=self.colors['secondary'],
                                         wraplength=250)
        self.description_label.pack(anchor=tk.W, pady=5)
        
        # Custom parameters frame
        self.params_frame = tk.LabelFrame(main_frame, text="Parameters", 
                                         padx=5, pady=5,
                                         bg=self.colors['secondary'],
                                         fg=self.colors['fg'],
                                         highlightbackground=self.colors['border'])
        self.params_frame.pack(fill=tk.X, pady=5)
        
        # Dynamic parameter inputs will be added here
        self.param_widgets = {}
        
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
        self._update_sub_types()
        
    def _on_general_type_change(self, event=None):
        """Handle general type change"""
        self._update_sub_types()
        
    def _on_sub_type_change(self, event=None):
        """Handle sub-type change"""
        self._update_parameters()
        self._update_description()
        
    def _update_sub_types(self):
        """Update sub-type dropdown based on general type"""
        general_type = self.current_general_type.get()
        sub_types = self.get_sub_types(general_type)
        
        self.sub_combo['values'] = sub_types
        if sub_types:
            self.current_sub_type.set(sub_types[0])
        
        self._update_parameters()
        self._update_description()
        
    def _update_description(self):
        """Update description label"""
        general = self.current_general_type.get()
        sub = self.current_sub_type.get()
        
        config = self.get_patch_config(general, sub)
        if config:
            desc = config.get("description", "No description available")
            self.description_label.config(text=desc)
        else:
            self.description_label.config(text="Select a patch type")
            
    def _update_parameters(self):
        """Update parameter inputs based on selection"""
        # Clear existing widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        self.param_widgets.clear()
        
        general = self.current_general_type.get()
        sub = self.current_sub_type.get()
        
        editable_fields = self.get_editable_fields(general, sub)
        
        if not editable_fields:
            tk.Label(self.params_frame, 
                    text="No parameters required for this patch type",
                    font=("Arial", 8, "italic"),
                    fg=self.colors['axis'],
                    bg=self.colors['secondary']).pack(pady=5)
            return
        
        # Create input fields for each editable parameter
        for field_info in editable_fields:
            field_name = field_info['field']
            label_text = field_info['label']
            default_value = field_info['value']
            
            row = tk.Frame(self.params_frame, bg=self.colors['secondary'])
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{label_text}:", 
                    bg=self.colors['secondary'], 
                    fg=self.colors['fg'],
                    font=("Arial", 8),
                    width=20,
                    anchor=tk.W).pack(side=tk.LEFT)
            
            # Create appropriate input based on field type
            if 'velocity' in label_text.lower() or 'vector' in str(default_value):
                # Vector input (x y z)
                var = tk.StringVar(value=str(default_value).replace('uniform ', ''))
                entry = tk.Entry(row, textvariable=var,
                               bg=self.colors['text_bg'],
                               fg=self.colors['text_fg'],
                               insertbackground=self.colors['fg'],
                               highlightbackground=self.colors['border'],
                               width=15)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.param_widgets[field_name] = var
            else:
                # Scalar input
                var = tk.StringVar(value=str(default_value).replace('uniform ', ''))
                entry = tk.Entry(row, textvariable=var,
                               bg=self.colors['text_bg'],
                               fg=self.colors['text_fg'],
                               insertbackground=self.colors['fg'],
                               highlightbackground=self.colors['border'],
                               width=15)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.param_widgets[field_name] = var
    
    def set_selected_faces(self, face_ids):
        """Update selected faces from external source"""
        self.selected_faces = list(face_ids)
        self.selection_label.config(
            text=f"Selected: {len(self.selected_faces)} face(s)",
            fg=self.colors['success'] if self.selected_faces else self.colors['warning']
        )
        
    def _assign_patch(self):
        """Assign current patch configuration to selected faces"""
        if not self.selected_faces:
            messagebox.showwarning("Warning", "No faces selected")
            return
        
        patch_name = self.patch_name_entry.get().strip()
        if not patch_name:
            messagebox.showwarning("Warning", "Please enter a patch name")
            return
        
        # Check if patch name already exists
        if hasattr(self.mesh_data, 'patches') and patch_name in self.mesh_data.patches:
            if not messagebox.askyesno("Confirm", 
                                      f"Patch '{patch_name}' already exists.\\n"
                                      "Add faces to existing patch?"):
                return
        
        # Build patch configuration
        general_type = self.current_general_type.get()
        sub_type = self.current_sub_type.get()
        
        patch_config = self.get_patch_config(general_type, sub_type)
        if not patch_config:
            messagebox.showerror("Error", "Invalid patch configuration")
            return
        
        # Get custom values
        custom_params = {}
        for field_name, var in self.param_widgets.items():
            custom_params[field_name] = var.get()
        
        # Create patch data
        patch_data = {
            'name': patch_name,
            'general_type': general_type,
            'sub_type': sub_type,
            'faces': self.selected_faces.copy(),
            'config': patch_config,
            'custom_params': custom_params
        }
        
        # Notify callback
        if self.on_assign_callback:
            self.on_assign_callback(patch_data)
        
        messagebox.showinfo("Success", 
                          f"Assigned {len(self.selected_faces)} faces to patch '{patch_name}'\\n"
                          f"Type: {general_type}/{sub_type}")
        
    def _clear_selection(self):
        """Clear face selection"""
        self.selected_faces = []
        self.selection_label.config(text="Selected: 0 faces", fg=self.colors['warning'])
        if self.on_assign_callback:
            self.on_assign_callback({'clear': True})


class PatchListPanel:
    """Panel for displaying and managing defined patches"""
    
    def __init__(self, parent, mesh_data, colors, on_select_callback):
        self.parent = parent
        self.mesh_data = mesh_data
        self.colors = colors
        self.on_select_callback = on_select_callback
        
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
                                  wraplength=250)
        self.info_label.pack(anchor=tk.W, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Delete", 
                 command=self._delete_patch,
                 bg=self.colors['error'], fg=self.colors['button_fg'],
                 activebackground='#d63636').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(btn_frame, text="Highlight", 
                 command=self._highlight_patch,
                 bg=self.colors['accent'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(btn_frame, text="Refresh", 
                 command=self.refresh_list,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active']).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
    def refresh_list(self):
        """Refresh the patch list"""
        self.patch_listbox.delete(0, tk.END)
        
        if not hasattr(self.mesh_data, 'patches'):
            return
        
        for patch_name, patch_data in self.mesh_data.patches.items():
            num_faces = len(patch_data.get('faces', []))
            general_type = patch_data.get('general_type', 'unknown')
            sub_type = patch_data.get('sub_type', 'unknown')
            
            display_text = f"{patch_name}: {general_type}/{sub_type} ({num_faces} faces)"
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
                info = f"Name: {patch_name}\\n"
                info += f"Type: {patch_data.get('general_type', 'unknown')}/{patch_data.get('sub_type', 'unknown')}\\n"
                info += f"Faces: {len(patch_data.get('faces', []))}"
                self.info_label.config(text=info)
                
                # Notify callback
                if self.on_select_callback:
                    self.on_select_callback(patch_name, patch_data)
                    
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
                faces = patch_data.get('faces', [])
                
                if self.on_select_callback:
                    self.on_select_callback(patch_name, patch_data, highlight_faces=faces)