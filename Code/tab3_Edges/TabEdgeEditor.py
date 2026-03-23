"""
Tab 3: Edge Editor - Define splines, arcs, and polyLines for blockMeshDict edges
Refactored with professional UI design
"""
import tkinter as tk
from tkinter import messagebox
import numpy as np

from tab3_Edges.tab3_edge_math import (
    calculate_arc_through_three_points, 
    calculate_spline_points,
    calculate_arc_center_from_radius,
    calculate_arc_midpoint
)
from tab3_Edges.tab3_edge_ui import EdgeEditorUI
from tab3_Edges.tab3_edge_model import EdgeModel


class Tab3EdgeEditor:
    """Main edge editor class with professional UI"""

    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.edge_model = EdgeModel(mesh_data)

        # Refined dark mode color palette
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#e0e0e0',
            'secondary': '#252526',
            'accent': '#007acc',
            'accent_hover': '#0098ff',
            'success': '#28a745',
            'success_hover': '#34ce57',
            'warning': '#ffc107',
            'warning_hover': '#ffcd39',
            'error': '#dc3545',
            'error_hover': '#e4606d',
            'button_bg': '#0e639c',
            'button_fg': '#ffffff',
            'button_active': '#1177bb',
            'border': '#3e3e42',
            'canvas_bg': '#1e1e1e',
            'text_bg': '#2d2d30',
            'text_fg': '#cccccc',
            'axis': '#6e6e6e'
        }

        self.selected_points = []
        self.current_edge_type = tk.StringVar(value='arc')
        self.editing_edge_idx = None
        self.editing_edge_data = None
        self.spline_points = []
        self.viewer = None

        self.manual_coords = [tk.DoubleVar(value=0.0) for _ in range(3)]
        self._waiting_for_center = False
        self._changing_point_type = None
        self._arc_point_selection_mode = None
        self._chosen_arc_point = None
        self._chosen_center_point = None
        self._radius_arc_options = None
        self._radius_side_selected = None

        # Setup callbacks
        callbacks = {
            'on_edge_type_changed': self._on_edge_type_changed,
            'add_manual_point': self._add_manual_point,
            'enter_point_manually': self._enter_point_manually,
            'add_spline_point': self._add_spline_point,
            'remove_spline_point': self._remove_spline_point,
            'clear_spline_points': self._clear_spline_points,
            'create_edge': self._create_edge,
            'reset_creation': self._reset_creation,
            'on_edge_select': self._on_edge_select,
            'edit_selected_edge': self._edit_selected_edge,
            'delete_edge': self._delete_edge,
            'delete_all_edges': self._delete_all_edges,
            'highlight_edge': self._highlight_edge,
            'change_edit_point': self._change_edit_point,
            'change_edit_point_manual': self._change_edit_point_manual,
            'edit_add_point': self._edit_add_point,
            'edit_add_point_manual': self._edit_add_point_manual,
            'edit_remove_point': self._edit_remove_point,
            'edit_clear_points': self._edit_clear_points,
            'save_edit_changes': self._save_edit_changes,
            'cancel_edit': self._cancel_edit,
            'use_center_point': self._use_center_point,
            'calc_mid_from_radius': self._calc_mid_from_radius,
            # Arc point selection callbacks
            'choose_arc_point': self._choose_arc_point,
            'use_chosen_arc_point': self._use_chosen_arc_point,
            'set_arc_point_manual': self._set_arc_point_manual,
            'choose_center_point': self._choose_center_point,
            'use_chosen_center': self._use_chosen_center,
            'set_center_manual': self._set_center_manual,
            # Radius side selection callbacks
            'preview_radius_arcs': self._preview_radius_arcs,
            'select_side_a': self._select_side_a,
            'select_side_b': self._select_side_b,
            'use_selected_radius_arc': self._use_selected_radius_arc,
            # Point list for spline/polyline dropdowns
            'get_points': self._get_point_list,
            'set_spline_endpoints': self._set_spline_endpoints,
        }

        # Build UI
        self.ui = EdgeEditorUI(parent_frame, self.colors, callbacks)
        viewer_frame, controls_frame = self.ui.setup_main_ui()

        self.ui.setup_create_tab(self.current_edge_type, self.manual_coords)
        self.ui.setup_manage_tab()
        self.ui.setup_edit_tab()

        # Populate point dropdowns now that UI exists
        self.ui.refresh_point_combos()

        # Create viewer
        from tab3_Edges.tab3_viewer import EmbeddedViewer
        self.viewer = EmbeddedViewer(viewer_frame, self.mesh_data, self)
        self._override_viewer_draw()

        # Initialize
        self._update_ui_state()
        self.parent.after(100, self._auto_fit)

    def _auto_fit(self):
        if self.viewer:
            self.viewer.fit_all()

    def _override_viewer_draw(self):
        original_draw = self.viewer.draw
        def draw_with_edges():
            original_draw()
            self._draw_edges()
        self.viewer.draw = draw_with_edges

    def _draw_edges(self):
        for edge_id, edge in self.edge_model.get_all_edges():
            self._draw_single_edge(edge)
        self._draw_preview_edge()

    def _hide_connection(self, p1, p2):
        """Mark connection between two points as hidden (has edge)"""
        if not hasattr(self, '_hidden_connections'):
            self._hidden_connections = set()
        for conn_id, conn in self.mesh_data.connections.items():
            if ((conn['point1'] == p1 and conn['point2'] == p2) or
                (conn['point1'] == p2 and conn['point2'] == p1)):
                self._hidden_connections.add(conn_id)
                break

    def _get_hidden_connections(self):
        """Get set of connection IDs that should be hidden (have edges)"""
        if not hasattr(self, '_hidden_connections'):
            self._hidden_connections = set()
        # Refresh - check all edges
        self._hidden_connections.clear()
        for edge_id, edge in self.edge_model.get_all_edges():
            start = edge.get('start')
            end = edge.get('end')
            if start is not None and end is not None:
                for conn_id, conn in self.mesh_data.connections.items():
                    if ((conn['point1'] == start and conn['point2'] == end) or
                        (conn['point1'] == end and conn['point2'] == start)):
                        self._hidden_connections.add(conn_id)
        return self._hidden_connections

    def _draw_single_edge(self, edge):
        edge_type = edge.get('type', 'line')
        start_coords = self._get_point_coords(edge['start'])
        end_coords = self._get_point_coords(edge['end'])

        if start_coords is None or end_coords is None:
            return

        sx1, sy1, _ = self.viewer._project(np.array(start_coords))
        sx2, sy2, _ = self.viewer._project(np.array(end_coords))

        if edge_type == 'line':
            self.viewer.canvas.create_line(sx1, sy1, sx2, sy2, 
                                          fill='#00ff00', width=4)  # Green, solid, thicker
        
            # Hide connection for this edge
            self._hide_connection(edge['start'], edge['end'])

        elif edge_type == 'arc':
            intermediate = edge.get('intermediate')
            if intermediate:
                mid_coords = self._get_point_coords(intermediate)
                points = calculate_arc_through_three_points(start_coords, mid_coords, end_coords)
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='#00ff00', width=4)  # Green arc
                mix, miy, _ = self.viewer._project(np.array(mid_coords))
                self.viewer.canvas.create_oval(mix-4, miy-4, mix+4, miy+4, 
                                              fill='#00ff00', outline='white', width=2)

        elif edge_type == 'spline':
            intermediate = edge.get('intermediate', [])
            if intermediate:
                all_points = ([start_coords] + 
                            [self._get_point_coords(p) for p in intermediate] + 
                            [end_coords])
                spline_pts = calculate_spline_points(all_points)
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in spline_pts]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='#00ff00', width=4)  # Green spline

        elif edge_type == 'polyLine':
            intermediate = edge.get('intermediate', [])
            if intermediate:
                all_points = ([start_coords] + 
                            [self._get_point_coords(p) for p in intermediate] + 
                            [end_coords])
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in all_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='#00ff00', width=4)  # Green polyLine

        # Endpoints
        self.viewer.canvas.create_oval(sx1-6, sy1-6, sx1+6, sy1+6, 
                                      fill='green', outline='white', width=2)
        self.viewer.canvas.create_oval(sx2-6, sy2-6, sx2+6, sy2+6, 
                                      fill='red', outline='white', width=2)

    def _draw_preview_edge(self):
        if len(self.selected_points) == 0:
            return

        for i, idx in enumerate(self.selected_points):
            coords = self._get_point_coords(idx)
            if coords:
                sx, sy, _ = self.viewer._project(np.array(coords))
                colors = ['#ffd700', '#ff8c00', '#00ced1']
                color = colors[i] if i < len(colors) else 'white'
                r = 8
                self.viewer.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, 
                                              fill=color, outline='white', width=2)
                labels = ['S', 'E', 'M']
                label = labels[i] if i < len(labels) else f"P{i+1}"
                offset_x = 20 if i % 2 == 0 else -20
                self.viewer.canvas.create_text(sx + offset_x, sy-20, text=label, 
                                              fill=color, font=('Segoe UI', 10, 'bold'))

        # Draw radius arc previews if available
        if hasattr(self, '_radius_arc_options') and self._radius_arc_options and len(self.selected_points) >= 2:
            start = self._get_point_coords(self.selected_points[0])
            end = self._get_point_coords(self.selected_points[1])

            # Draw Side A preview (cyan)
            if self._radius_arc_options.get('A') and self._radius_arc_options['A']['mid']:
                mid_a = self._radius_arc_options['A']['mid']
                points_a = calculate_arc_through_three_points(start, mid_a, end)
                screen_points_a = [(self.viewer._project(np.array(p))[0], 
                                   self.viewer._project(np.array(p))[1]) for p in points_a]
                # Dashed cyan for preview
                for i in range(len(screen_points_a) - 1):
                    self.viewer.canvas.create_line(
                        screen_points_a[i][0], screen_points_a[i][1],
                        screen_points_a[i+1][0], screen_points_a[i+1][1],
                        fill='#00ffff', width=2, dash=(4, 4))
                # Label
                mid_x = screen_points_a[len(screen_points_a)//2][0]
                mid_y = screen_points_a[len(screen_points_a)//2][1]
                self.viewer.canvas.create_text(mid_x, mid_y-15, text="A", 
                                              fill='#00ffff', font=('Segoe UI', 12, 'bold'))

            # Draw Side B preview (magenta)
            if self._radius_arc_options.get('B') and self._radius_arc_options['B']['mid']:
                mid_b = self._radius_arc_options['B']['mid']
                points_b = calculate_arc_through_three_points(start, mid_b, end)
                screen_points_b = [(self.viewer._project(np.array(p))[0], 
                                   self.viewer._project(np.array(p))[1]) for p in points_b]
                # Dashed magenta for preview
                for i in range(len(screen_points_b) - 1):
                    self.viewer.canvas.create_line(
                        screen_points_b[i][0], screen_points_b[i][1],
                        screen_points_b[i+1][0], screen_points_b[i+1][1],
                        fill='#ff00ff', width=2, dash=(4, 4))
                # Label
                mid_x = screen_points_b[len(screen_points_b)//2][0]
                mid_y = screen_points_b[len(screen_points_b)//2][1]
                self.viewer.canvas.create_text(mid_x, mid_y-15, text="B", 
                                              fill='#ff00ff', font=('Segoe UI', 12, 'bold'))

        if len(self.selected_points) >= 2:
            start = self._get_point_coords(self.selected_points[0])
            end = self._get_point_coords(self.selected_points[1])
            edge_type = self.current_edge_type.get()

            if edge_type == 'arc' and len(self.selected_points) == 3:
                mid = self._get_point_coords(self.selected_points[2])
                points = calculate_arc_through_three_points(start, mid, end)
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='cyan', width=2, dash=(4, 2))

            elif edge_type == 'spline' and self.spline_points:
                all_points = ([start] + 
                            [self._get_point_coords(p) for p in self.spline_points] + 
                            [end])
                spline_pts = calculate_spline_points(all_points)
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in spline_pts]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='orange', width=2, dash=(4, 2))

            elif edge_type == 'polyLine' and self.spline_points:
                all_points = ([start] + 
                            [self._get_point_coords(p) for p in self.spline_points] + 
                            [end])
                screen_points = [(self.viewer._project(np.array(p))[0], 
                                 self.viewer._project(np.array(p))[1]) for p in all_points]
                for i in range(len(screen_points) - 1):
                    self.viewer.canvas.create_line(
                        screen_points[i][0], screen_points[i][1],
                        screen_points[i+1][0], screen_points[i+1][1],
                        fill='lightgreen', width=2, dash=(4, 2))

    def _get_point_coords(self, point_ref):
        if isinstance(point_ref, int):
            point_data = self.mesh_data.get_point(point_ref)
            if point_data:
                return (point_data['x'], point_data['y'], point_data['z'])
            return None
        return point_ref

    def _on_edge_type_changed(self):
        self._update_ui_state()
        self._reset_creation()

    def _update_ui_state(self):
        edge_type = self.current_edge_type.get()

        # Hide all config frames first
        self.ui.arc_config.pack_forget()
        self.ui.spline_config.pack_forget()

        if edge_type == 'arc':
            self.ui.arc_config.pack(fill=tk.X, pady=5)
            self.ui.info_label.config(text="Select start point (Arc mode)")
        elif edge_type in ['spline', 'polyLine']:
            self.ui.spline_config.pack(fill=tk.X, pady=5)
            self.ui.refresh_point_combos()  # Update dropdowns with latest points
            self.ui.info_label.config(text=f"Use dropdowns to set Start/End, click 3D view for intermediate points")
        else:
            self.ui.info_label.config(text="Select start point (Line mode)")

        if self.viewer:
            self.viewer.draw()

    def on_selection_changed(self, selected_list):
        edge_type = self.current_edge_type.get()

        # Handle edit mode point changing
        if self._changing_point_type:
            if len(selected_list) > 0:
                new_point = selected_list[-1]
                if self._changing_point_type == 'start':
                    self.editing_edge_data['start'] = new_point
                    self.ui.edit_start_var.set(f"Point {new_point}" if isinstance(new_point, int) else f"({new_point[0]:.2f}, ...)")
                elif self._changing_point_type == 'end':
                    self.editing_edge_data['end'] = new_point
                    self.ui.edit_end_var.set(f"Point {new_point}" if isinstance(new_point, int) else f"({new_point[0]:.2f}, ...)")
                self._changing_point_type = None
                self.ui.edit_info_label.config(text="Point updated. Click Save to apply.", 
                                               fg=self.colors['success'])
                self.viewer.draw()
            return

        # Handle arc point selection mode (NEW)
        if hasattr(self, '_arc_point_selection_mode') and self._arc_point_selection_mode:
            if len(selected_list) > 0:
                point_id = selected_list[-1]
                if self._arc_point_selection_mode == 'arc_point':
                    self._chosen_arc_point = point_id
                    self.ui.arc_point_var.set(f"Point {point_id}")
                elif self._arc_point_selection_mode == 'center':
                    self._chosen_center_point = point_id
                    self.ui.arc_center_var.set(f"Point {point_id}")
                self._arc_point_selection_mode = None
                self.ui.info_label.config(text="Point selected. Click 'Use This Point' to apply.")
            return

        # Handle arc center point selection
        if self._waiting_for_center:
            if len(selected_list) > 0:
                center_point = selected_list[-1]
                center_coords = self._get_point_coords(center_point)
                if center_coords and len(self.selected_points) >= 2:
                    start_coords = self._get_point_coords(self.selected_points[0])
                    end_coords = self._get_point_coords(self.selected_points[1])
                    if start_coords and end_coords:
                        mid_point = calculate_arc_midpoint(start_coords, end_coords, center_coords)
                        self.selected_points.append(mid_point)
                        self._update_status()
                        self.viewer.draw()
                self._waiting_for_center = False
            return

        # Normal point selection flow
        if len(self.selected_points) == 0:
            if len(selected_list) > 0:
                self.selected_points.append(selected_list[-1])
                self._update_status()

        elif len(self.selected_points) == 1:
            if len(selected_list) > 1:
                end_point = selected_list[-1]
                if end_point != self.selected_points[0]:
                    self.selected_points.append(end_point)
                    self._update_status()

        elif len(self.selected_points) == 2 and edge_type == 'arc':
            if len(selected_list) > 2:
                third_point = selected_list[-1]
                if third_point not in self.selected_points:
                    self.selected_points.append(third_point)
                    self._update_status()

        elif edge_type in ['spline', 'polyLine']:
            new_point = selected_list[-1]
            existing = set()
            for p in self.selected_points + self.spline_points:
                if isinstance(p, int):
                    existing.add(p)

            if isinstance(new_point, int) and new_point in existing:
                return

            self.spline_points.append(new_point)
            self._update_spline_listbox()
            self._update_status()

        self.viewer.draw()

    def _update_status(self):
        """Update the status label based on current selection"""
        edge_type = self.current_edge_type.get()
        n = len(self.selected_points)

        if n == 0:
            text = "Ready - Select start point"
            info = "Select start point"
        elif n == 1:
            text = f"Start: {self._fmt_point(self.selected_points[0])}"
            info = "Select end point"
        elif n == 2:
            text = (f"Start: {self._fmt_point(self.selected_points[0])} \n"
                   f"End: {self._fmt_point(self.selected_points[1])} \n")
            if edge_type == 'arc':
                info = "Select mid point or use Arc Helper"
            elif edge_type in ['spline', 'polyLine']:
                text += f"Intermediate: {len(self.spline_points)} points"
                info = "Add intermediate points or click Create"
            else:
                info = "Ready to create"
        elif n == 3 and edge_type == 'arc':
            text = (f"Start: {self._fmt_point(self.selected_points[0])} \n"
                   f"End: {self._fmt_point(self.selected_points[1])} \n"
                   f"Mid: {self._fmt_point(self.selected_points[2])} \n")
            info = "Ready to create"
        else:
            text = f"Selected: {n} points"
            info = "Ready"

        self.ui.status_label.config(text=text)
        self.ui.info_label.config(text=info)

    def _fmt_point(self, p):
        if isinstance(p, int):
            return f"Point {p}"
        return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"

    def _use_center_point(self):
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need start and end points first")
            return
        self._waiting_for_center = True
        self.ui.info_label.config(text="Click the center point")

    def _calc_mid_from_radius(self, radius, side):
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need start and end points first")
            return

        start_coords = self._get_point_coords(self.selected_points[0])
        end_coords = self._get_point_coords(self.selected_points[1])

        if not start_coords or not end_coords:
            return

        center = calculate_arc_center_from_radius(start_coords, end_coords, radius, side)
        if center is None:
            messagebox.showerror("Error", f"Radius {radius} is too small")
            return

        mid_point = calculate_arc_midpoint(start_coords, end_coords, center)
        self.selected_points.append(mid_point)
        self._update_status()
        self.viewer.draw()

    def _enter_point_manually(self, point_type):
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)

            if point_type == 'start':
                if len(self.selected_points) == 0:
                    self.selected_points.append(point)
                else:
                    self.selected_points[0] = point
            elif point_type == 'end':
                if len(self.selected_points) == 1:
                    self.selected_points.append(point)
                elif len(self.selected_points) >= 2:
                    self.selected_points[1] = point

            self._update_status()
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _add_manual_point(self):
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)

            self.spline_points.append(point)
            self._update_spline_listbox()
            self._update_status()
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _get_point_list(self):
        """Return list of point choice strings for combo boxes."""
        choices = []
        for pid_str, pdata in sorted(self.mesh_data.points.items(), key=lambda x: int(x[0])):
            x = pdata.get('X', pdata.get('x', 0))
            y = pdata.get('Y', pdata.get('y', 0))
            z = pdata.get('Z', pdata.get('z', 0))
            choices.append(f"{pid_str}: ({x:.2f}, {y:.2f}, {z:.2f})")
        return choices

    def _set_spline_endpoints(self):
        """Apply start and end point selections from the combo dropdowns."""
        start_sel = self.ui.spline_start_var.get() if self.ui.spline_start_var else ""
        end_sel   = self.ui.spline_end_var.get()   if self.ui.spline_end_var   else ""
        if not start_sel or not end_sel:
            messagebox.showwarning("Warning", "Select both Start and End points from the dropdowns")
            return
        try:
            start_id = int(start_sel.split(':')[0].strip())
            end_id   = int(end_sel.split(':')[0].strip())
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid point selection")
            return
        # Set selected_points: index 0 = start, 1 = end
        if len(self.selected_points) == 0:
            self.selected_points = [start_id, end_id]
        else:
            self.selected_points[0:2] = [start_id, end_id]
        self._update_status()
        if self.viewer:
            self.viewer.draw()



    def _create_edge(self):
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need at least start and end points")
            return

        self.mesh_data.save_state()
        
        edge_type = self.current_edge_type.get()
        edge = {
            'type': edge_type,
            'start': self.selected_points[0],
            'end': self.selected_points[1]
        }

        if edge_type == 'arc':
            if len(self.selected_points) < 3:
                messagebox.showwarning("Warning", "Arc requires 3 points")
                return
            edge['intermediate'] = self.selected_points[2]

        elif edge_type in ['spline', 'polyLine']:
            edge['intermediate'] = self.spline_points.copy()

        self.edge_model.add_edge(edge)
        messagebox.showinfo("Success", f"{edge_type} edge created!")
        self._reset_creation()
        self._update_edge_list()

    def _reset_creation(self):
        self.selected_points = []
        self.spline_points = []
        self._update_spline_listbox()
        self._update_status()
        self.viewer.clear_selection()

    def _update_spline_listbox(self):
        self.ui.spline_listbox.delete(0, tk.END)
        for i, pt in enumerate(self.spline_points):
            if isinstance(pt, int):
                coords = self._get_point_coords(pt)
                self.ui.spline_listbox.insert(tk.END, 
                    f"{i+1}. Point {pt}: ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})")
            else:
                self.ui.spline_listbox.insert(tk.END, 
                    f"{i+1}. ({pt[0]:.2f}, {pt[1]:.2f}, {pt[2]:.2f})")

    def _add_spline_point(self):
        messagebox.showinfo("Info", "Click a point in the 3D view to add")

    def _remove_spline_point(self):
        if self.spline_points:
            self.spline_points.pop()
            self._update_spline_listbox()
            self._update_status()
            self.viewer.draw()

    def _clear_spline_points(self):
        self.spline_points = []
        self._update_spline_listbox()
        self._update_status()
        self.viewer.draw()

    def _update_edge_list(self):
        """Update the edge listbox - PUBLIC METHOD"""
        self.ui.edge_listbox.delete(0, tk.END)
        for edge_id, edge in self.edge_model.get_all_edges():
            display_text = self.edge_model.get_edge_display_text(edge_id, edge)
            self.ui.edge_listbox.insert(tk.END, display_text)

    def _on_edge_select(self, event=None):
        sel = self.ui.edge_listbox.curselection()
        if sel:
            idx = sel[0]
            edges = self.edge_model.get_all_edges()
            if idx < len(edges):
                edge_id, edge = edges[idx]
                details = self.edge_model.get_edge_details_text(edge)
                self.ui.edge_details.config(text=details, fg=self.colors['fg'])

    def _edit_selected_edge(self):
        sel = self.ui.edge_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an edge to edit")
            return

        idx = sel[0]
        edges = self.edge_model.get_all_edges()
        if idx >= len(edges):
            return

        edge_id, edge = edges[idx]
        self.editing_edge_idx = edge_id
        self.editing_edge_data = dict(edge)

        self.ui.notebook.select(self.ui.tab_edit)

        self.ui.edit_type_label.config(text=edge.get('type', 'line').upper())

        def fmt_point(p):
            if isinstance(p, int):
                return f"Point {p}"
            return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"

        self.ui.edit_start_var.set(fmt_point(edge.get('start')))
        self.ui.edit_end_var.set(fmt_point(edge.get('end')))

        self.ui.edit_intermediate_listbox.delete(0, tk.END)
        if 'intermediate' in edge:
            intermediate = edge['intermediate']
            if isinstance(intermediate, list):
                for i, pt in enumerate(intermediate):
                    self.ui.edit_intermediate_listbox.insert(tk.END, f"{i+1}. {fmt_point(pt)}")
            else:
                self.ui.edit_intermediate_listbox.insert(tk.END, f"1. {fmt_point(intermediate)}")

        self.ui.edit_info_label.config(text=f"Editing Edge {edge_id}",
                                       fg=self.colors['accent'])
        self.viewer.draw()

    def _change_edit_point(self, point_type):
        self._changing_point_type = point_type
        self.ui.edit_info_label.config(text=f"Click a point in 3D view for {point_type}",
                                       fg=self.colors['warning'])

    def _change_edit_point_manual(self, point_type):
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)

            if point_type == 'start':
                self.editing_edge_data['start'] = point
                self.ui.edit_start_var.set(f"({x:.2f}, {y:.2f}, {z:.2f})")
            elif point_type == 'end':
                self.editing_edge_data['end'] = point
                self.ui.edit_end_var.set(f"({x:.2f}, {y:.2f}, {z:.2f})")

            self.ui.edit_info_label.config(text="Point updated. Click Save to apply.",
                                           fg=self.colors['success'])
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _edit_add_point(self):
        messagebox.showinfo("Info", "Click a point in 3D view to add")

    def _edit_add_point_manual(self):
        try:
            x = self.manual_coords[0].get()
            y = self.manual_coords[1].get()
            z = self.manual_coords[2].get()
            point = (x, y, z)

            if 'intermediate' not in self.editing_edge_data:
                self.editing_edge_data['intermediate'] = []

            if isinstance(self.editing_edge_data['intermediate'], int):
                self.editing_edge_data['intermediate'] = [self.editing_edge_data['intermediate']]

            self.editing_edge_data['intermediate'].append(point)
            self._refresh_edit_listbox()
            self.viewer.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid coordinates: {e}")

    def _edit_remove_point(self):
        sel = self.ui.edit_intermediate_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        if 'intermediate' in self.editing_edge_data:
            intermediate = self.editing_edge_data['intermediate']
            if isinstance(intermediate, list):
                if idx < len(intermediate):
                    intermediate.pop(idx)
            else:
                self.editing_edge_data.pop('intermediate')

        self._refresh_edit_listbox()

    def _edit_clear_points(self):
        if 'intermediate' in self.editing_edge_data:
            self.editing_edge_data.pop('intermediate')
        self._refresh_edit_listbox()

    def _refresh_edit_listbox(self):
        self.ui.edit_intermediate_listbox.delete(0, tk.END)

        def fmt_point(p):
            if isinstance(p, int):
                return f"Point {p}"
            return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"

        if 'intermediate' in self.editing_edge_data:
            intermediate = self.editing_edge_data['intermediate']
            if isinstance(intermediate, list):
                for i, pt in enumerate(intermediate):
                    self.ui.edit_intermediate_listbox.insert(tk.END, f"{i+1}. {fmt_point(pt)}")
            else:
                self.ui.edit_intermediate_listbox.insert(tk.END, f"1. {fmt_point(intermediate)}")

    def _save_edit_changes(self):
        if self.editing_edge_idx is None:
            return

        self.mesh_data.save_state()
        
        self.edge_model.update_edge(self.editing_edge_idx, self.editing_edge_data)
        messagebox.showinfo("Success", "Edge updated!")
        self._update_edge_list()
        self.ui.notebook.select(self.ui.tab_manage)
        self.viewer.draw()

    def _cancel_edit(self):
        self.editing_edge_idx = None
        self.editing_edge_data = None
        self._changing_point_type = None
        self.ui.notebook.select(self.ui.tab_manage)
        self.ui.edit_info_label.config(text="Select an edge from Manage tab",
                                       fg=self.colors['warning'])

    def _delete_edge(self):
        sel = self.ui.edge_listbox.curselection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete selected edge?"):
            self.mesh_data.save_state()
            idx = sel[0]
            edges = self.edge_model.get_all_edges()
            if idx < len(edges):
                edge_id, _ = edges[idx]
                self.edge_model.delete_edge(edge_id)
                self._update_edge_list()
                self.ui.edge_details.config(text="Select an edge to view details", 
                                           fg='#888888')
                self.viewer.draw()

    def _delete_all_edges(self):
        if not self.edge_model.get_all_edges():
            return
        if messagebox.askyesno("Confirm", "Delete all edges?"):
            self.mesh_data.save_state()
            self.edge_model.delete_all_edges()
            self._update_edge_list()
            self.ui.edge_details.config(text="Select an edge to view details",
                                       fg='#888888')
            self.viewer.draw()

    def _highlight_edge(self):
        sel = self.ui.edge_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        edges = self.edge_model.get_all_edges()
        if idx >= len(edges):
            return

        edge_id, edge = edges[idx]
        points_to_select = []

        if isinstance(edge.get('start'), int):
            points_to_select.append(edge['start'])
        if isinstance(edge.get('end'), int):
            points_to_select.append(edge['end'])
        if 'intermediate' in edge:
            intermediate = edge['intermediate']
            if isinstance(intermediate, list):
                for pt in intermediate:
                    if isinstance(pt, int):
                        points_to_select.append(pt)
            else:
                if isinstance(intermediate, int):
                    points_to_select.append(intermediate)

        self.viewer.set_selection(points_to_select)


    # NEW: Radius side selection methods
    def _preview_radius_arcs(self):
        """Calculate and preview both arc options for the given radius"""
        if len(self.selected_points) < 2:
            messagebox.showwarning("Warning", "Need start and end points first")
            return

        radius = self.ui.radius_var.get()
        start_coords = self._get_point_coords(self.selected_points[0])
        end_coords = self._get_point_coords(self.selected_points[1])

        if not start_coords or not end_coords:
            return

        # Calculate both centers
        center_a = calculate_arc_center_from_radius(start_coords, end_coords, radius, 1)
        center_b = calculate_arc_center_from_radius(start_coords, end_coords, radius, -1)

        if center_a is None and center_b is None:
            messagebox.showerror("Error", f"Radius {radius} is too small for the distance between points")
            return

        # Store both options
        self._radius_arc_options = {
            'A': {'center': center_a, 'mid': calculate_arc_midpoint(start_coords, end_coords, center_a) if center_a else None},
            'B': {'center': center_b, 'mid': calculate_arc_midpoint(start_coords, end_coords, center_b) if center_b else None}
        }

        self._radius_side_selected = None
        self.ui.radius_side_var.set("Both arcs previewed. Click 'Select Side A' or 'Select Side B'")
        self.ui.selected_side_var.set("No side selected")

        # Redraw to show preview
        self.viewer.draw()

    def _select_side_a(self):
        """Select side A (radio button behavior)"""
        if not hasattr(self, '_radius_arc_options') or not self._radius_arc_options or self._radius_arc_options['A']['mid'] is None:
            messagebox.showwarning("Warning", "Click 'Preview' first")
            return
        self._radius_side_selected = 'A'
        self.ui.selected_side_var.set("Side A selected")
        self.ui.radius_side_var.set("Side A selected - arc will bulge in direction A")

    def _select_side_b(self):
        """Select side B (radio button behavior) - deselects A"""
        if not hasattr(self, '_radius_arc_options') or not self._radius_arc_options or self._radius_arc_options['B']['mid'] is None:
            messagebox.showwarning("Warning", "Click 'Preview' first")
            return
        self._radius_side_selected = 'B'
        self.ui.selected_side_var.set("Side B selected")
        self.ui.radius_side_var.set("Side B selected - arc will bulge in direction B")

    def _use_selected_radius_arc(self):
        """Use the selected side's arc"""
        if not hasattr(self, '_radius_side_selected') or self._radius_side_selected is None:
            messagebox.showwarning("Warning", "Please select Side A or Side B first")
            return

        mid_point = self._radius_arc_options[self._radius_side_selected]['mid']
        if mid_point is None:
            messagebox.showerror("Error", "Selected side is not available (radius may be too small)")
            return

        # Add as third point
        if len(self.selected_points) == 2:
            self.selected_points.append(mid_point)
        else:
            self.selected_points[2] = mid_point

        self._update_status()
        self.viewer.draw()
        messagebox.showinfo("Success", f"Arc from Side {self._radius_side_selected} applied!")

    # NEW: Arc point selection workflow methods
    def _choose_arc_point(self):
        """Start choosing a point for arc mid-point"""
        self._arc_point_selection_mode = 'arc_point'
        self.ui.arc_point_var.set("Click a point in 3D view...")
        self.ui.info_label.config(text="Click a point in 3D view for arc mid-point")

    def _use_chosen_arc_point(self):
        """Use the currently chosen arc point"""
        if hasattr(self, '_chosen_arc_point') and self._chosen_arc_point is not None:
            if len(self.selected_points) >= 2:
                # Add as third point (mid-point)
                if len(self.selected_points) == 2:
                    self.selected_points.append(self._chosen_arc_point)
                else:
                    self.selected_points[2] = self._chosen_arc_point
                self._update_status()
                self.viewer.draw()
                self.ui.arc_point_var.set(f"Point {self._chosen_arc_point}")
            else:
                messagebox.showwarning("Warning", "Need start and end points first")
        else:
            messagebox.showwarning("Warning", "No point selected. Click 'Choose Point' first.")

    def _set_arc_point_manual(self):
        """Set arc point from manual entry"""
        try:
            point_id = int(self.ui.arc_manual_point_var.get())
            if str(point_id) not in self.mesh_data.points:
                messagebox.showerror("Error", f"Point {point_id} does not exist")
                return
            self._chosen_arc_point = point_id
            self.ui.arc_point_var.set(f"Point {point_id} (manual)")
        except ValueError:
            messagebox.showerror("Error", "Invalid Point ID")

    def _choose_center_point(self):
        """Start choosing a center point for arc"""
        self._arc_point_selection_mode = 'center'
        self.ui.arc_center_var.set("Click a point in 3D view...")
        self.ui.info_label.config(text="Click a point in 3D view for arc center")

    def _use_chosen_center(self):
        """Use the chosen center point to calculate arc mid-point"""
        if hasattr(self, '_chosen_center_point') and self._chosen_center_point is not None:
            if len(self.selected_points) >= 2:
                center_coords = self._get_point_coords(self._chosen_center_point)
                start_coords = self._get_point_coords(self.selected_points[0])
                end_coords = self._get_point_coords(self.selected_points[1])

                if center_coords and start_coords and end_coords:
                    mid_point = calculate_arc_midpoint(start_coords, end_coords, center_coords)
                    if len(self.selected_points) == 2:
                        self.selected_points.append(mid_point)
                    else:
                        self.selected_points[2] = mid_point
                    self._update_status()
                    self.viewer.draw()
                    self.ui.arc_center_var.set(f"Point {self._chosen_center_point}")
            else:
                messagebox.showwarning("Warning", "Need start and end points first")
        else:
            messagebox.showwarning("Warning", "No center selected. Click 'Choose Center' first.")

    def _set_center_manual(self):
        """Set center point from manual entry"""
        try:
            point_id = int(self.ui.arc_manual_center_var.get())
            if str(point_id) not in self.mesh_data.points:
                messagebox.showerror("Error", f"Point {point_id} does not exist")
                return
            self._chosen_center_point = point_id
            self.ui.arc_center_var.set(f"Point {point_id} (manual)")
        except ValueError:
            messagebox.showerror("Error", "Invalid Point ID")

    def get_edges_data(self):
        """Get edges data for JSON serialization"""
        return self.edge_model.get_edges_for_json()
    
    def load_edges_data(self, edges_list):
        """Load edges data from JSON"""
        self.edge_model.load_edges_from_json(edges_list)
        self._update_edge_list()
        if self.viewer:
            self.viewer.draw()
    
    def ensure_edges_initialized(self):
        """Ensure mesh_data.edges is initialized as a dict"""
        if not hasattr(self.mesh_data, 'edges'):
            self.mesh_data.edges = {}
        elif isinstance(self.mesh_data.edges, list):
            # Convert list to dict
            edge_dict = {}
            for i, edge in enumerate(self.mesh_data.edges):
                edge_dict[str(i + 1)] = edge
            self.mesh_data.edges = edge_dict
            
    def cleanup(self):
        if self.viewer:
            self.viewer.close()

    # Public methods for external access
    def refresh(self):
        if self.viewer:
            self.viewer.refresh()

    def update_edge_list(self):
        self._update_edge_list()