"""
Dual View Connection Handler
Manages point selection and inter-layer connections in dual view mode
"""
import tkinter as tk
from tkinter import messagebox
import math


class DualViewConnectionHandler:
    """Handles point selection and connection creation in dual view mode"""
    
    def __init__(self, parent_tab):
        self.parent_tab = parent_tab
        self.mesh_data = parent_tab.mesh_data
        
        # Dual view selection state
        self.dual_selected_left = None   # Global index of point selected on left canvas
        self.dual_selected_right = None  # Global index of point selected on right canvas
        
        # Visual feedback
        self.left_selection_marker = None
        self.right_selection_marker = None
        
    def handle_dual_canvas_click(self, event, canvas_side):
        """
        Handle click on dual view canvas
        canvas_side: 0 for left, 1 for right
        """
        if not self.parent_tab.dual_view_mode:
            return
        
        if len(self.parent_tab.dual_view_layers) != 2:
            return
        
        # Get the correct canvas and layer
        if canvas_side == 0:
            canvas = self.parent_tab.canvas_left
            layer = self.parent_tab.dual_view_layers[0]
        else:
            canvas = self.parent_tab.canvas_right
            layer = self.parent_tab.dual_view_layers[1]
        
        # Convert click coordinates to world coordinates
        x, y = self.parent_tab.canvas_to_world(event.x, event.y, canvas)
        points = self.mesh_data.points[layer]
        
        # Find clicked point
        clicked_idx = None
        min_dist = float('inf')
        
        for local_idx, (px, py) in enumerate(points):
            dist = math.sqrt((px - x)**2 + (py - y)**2)
            if dist < 0.3:  # Click tolerance
                if dist < min_dist:
                    min_dist = dist
                    clicked_idx = local_idx
        
        if clicked_idx is not None:
            # Convert to global index
            global_idx = self.mesh_data.get_global_point_index(layer, clicked_idx)
            
            # Update selection based on which canvas was clicked
            if canvas_side == 0:  # Left canvas
                self.dual_selected_left = global_idx
                self._update_selection_display()
            else:  # Right canvas
                self.dual_selected_right = global_idx
                self._update_selection_display()
            
            # Update the parent's display
            self.parent_tab.update_plot()
    
    def _update_selection_display(self):
        """Update the selection status label"""
        left_text = f"Point {self.dual_selected_left}" if self.dual_selected_left is not None else "None"
        right_text = f"Point {self.dual_selected_right}" if self.dual_selected_right is not None else "None"
        
        status = f"Left: {left_text} | Right: {right_text}"
        
        if hasattr(self.parent_tab, 'dual_selection_label'):
            self.parent_tab.dual_selection_label.config(text=status)
            
            # Update button state
            if self.dual_selected_left is not None and self.dual_selected_right is not None:
                self.parent_tab.dual_connect_button.config(state=tk.NORMAL, bg='#4ec9b0')
            else:
                self.parent_tab.dual_connect_button.config(state=tk.DISABLED, bg='#3e3e42')
    
    def create_dual_connection(self):
        """Create an inter-layer connection between selected points"""
        if self.dual_selected_left is None or self.dual_selected_right is None:
            messagebox.showwarning("Selection Required", 
                                 "Please select one point from each layer first!")
            return
        
        if len(self.parent_tab.dual_view_layers) != 2:
            messagebox.showwarning("Dual View Error", 
                                 "Dual view must have exactly 2 layers selected")
            return
        
        # Get layer names and local indices
        layer_left, idx_left = self.mesh_data.get_layer_from_global_index(self.dual_selected_left)
        layer_right, idx_right = self.mesh_data.get_layer_from_global_index(self.dual_selected_right)
        
        # Verify they're from the correct layers
        if layer_left != self.parent_tab.dual_view_layers[0]:
            messagebox.showerror("Error", "Left point must be from the left layer!")
            return
        
        if layer_right != self.parent_tab.dual_view_layers[1]:
            messagebox.showerror("Error", "Right point must be from the right layer!")
            return
        
        # Check if connection already exists
        conn = (layer_left, idx_left, layer_right, idx_right)
        conn_reverse = (layer_right, idx_right, layer_left, idx_left)
        
        if conn in self.mesh_data.inter_layer_connections or conn_reverse in self.mesh_data.inter_layer_connections:
            messagebox.showinfo("Already Connected", 
                              "These points are already connected!")
            return
        
        # Create the inter-layer connection
        self.mesh_data.add_inter_layer_connection(layer_left, idx_left, layer_right, idx_right)
        
        # Clear selection
        self.clear_dual_selection()
        
        # Update display
        self.parent_tab.update_plot()
        
        # Show success message
        messagebox.showinfo("Connection Created", 
                          f"Connected {layer_left}[{idx_left}] ↔ {layer_right}[{idx_right}]")
    
    def clear_dual_selection(self):
        """Clear both dual view selections"""
        self.dual_selected_left = None
        self.dual_selected_right = None
        self._update_selection_display()
        self.parent_tab.update_plot()
    
    def draw_dual_selection_markers(self):
        """Draw selection markers on the dual view canvases"""
        if not self.parent_tab.dual_view_mode:
            return
        
        if not self.parent_tab.canvas_left or not self.parent_tab.canvas_right:
            return
        
        # Draw marker on left canvas
        if self.dual_selected_left is not None:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(self.dual_selected_left)
            if layer == self.parent_tab.dual_view_layers[0]:
                point_2d = self.mesh_data.points[layer][local_idx]
                cx, cy = self.parent_tab.world_to_canvas(point_2d[0], point_2d[1], 
                                                         self.parent_tab.canvas_left)
                
                # Draw a bright yellow circle around selected point
                r = 12
                self.parent_tab.canvas_left.create_oval(
                    cx-r, cy-r, cx+r, cy+r,
                    outline='yellow', width=3, tags='dual_selection'
                )
                # Draw crosshair
                self.parent_tab.canvas_left.create_line(
                    cx-r-5, cy, cx+r+5, cy,
                    fill='yellow', width=2, tags='dual_selection'
                )
                self.parent_tab.canvas_left.create_line(
                    cx, cy-r-5, cx, cy+r+5,
                    fill='yellow', width=2, tags='dual_selection'
                )
        
        # Draw marker on right canvas
        if self.dual_selected_right is not None:
            layer, local_idx = self.mesh_data.get_layer_from_global_index(self.dual_selected_right)
            if layer == self.parent_tab.dual_view_layers[1]:
                point_2d = self.mesh_data.points[layer][local_idx]
                cx, cy = self.parent_tab.world_to_canvas(point_2d[0], point_2d[1], 
                                                         self.parent_tab.canvas_right)
                
                # Draw a bright yellow circle around selected point
                r = 12
                self.parent_tab.canvas_right.create_oval(
                    cx-r, cy-r, cx+r, cy+r,
                    outline='yellow', width=3, tags='dual_selection'
                )
                # Draw crosshair
                self.parent_tab.canvas_right.create_line(
                    cx-r-5, cy, cx+r+5, cy,
                    fill='yellow', width=2, tags='dual_selection'
                )
                self.parent_tab.canvas_right.create_line(
                    cx, cy-r-5, cx, cy+r+5,
                    fill='yellow', width=2, tags='dual_selection'
                )
        
        # Draw connection line if both points selected
        if self.dual_selected_left is not None and self.dual_selected_right is not None:
            layer_left, idx_left = self.mesh_data.get_layer_from_global_index(self.dual_selected_left)
            layer_right, idx_right = self.mesh_data.get_layer_from_global_index(self.dual_selected_right)
            
            if (layer_left == self.parent_tab.dual_view_layers[0] and 
                layer_right == self.parent_tab.dual_view_layers[1]):
                
                point_left = self.mesh_data.points[layer_left][idx_left]
                point_right = self.mesh_data.points[layer_right][idx_right]
                
                cx_left, cy_left = self.parent_tab.world_to_canvas(
                    point_left[0], point_left[1], self.parent_tab.canvas_left)
                cx_right, cy_right = self.parent_tab.world_to_canvas(
                    point_right[0], point_right[1], self.parent_tab.canvas_right)
                
                # Get canvas dimensions to draw a line connecting across the gap
                # Note: This is approximate since canvases are side-by-side
                # We'll draw a visual indicator on each canvas instead
                
                # Arrow on left canvas pointing right
                canvas_width = self.parent_tab.canvas_left.winfo_width() or self.parent_tab.canvas_width // 2
                self.parent_tab.canvas_left.create_line(
                    cx_left, cy_left, canvas_width, cy_left,
                    fill='yellow', width=3, arrow=tk.LAST, dash=(5, 3),
                    tags='dual_selection'
                )
                
                # Arrow on right canvas pointing left
                self.parent_tab.canvas_right.create_line(
                    0, cy_right, cx_right, cy_right,
                    fill='yellow', width=3, arrow=tk.LAST, dash=(5, 3),
                    tags='dual_selection'
                )