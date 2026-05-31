"""
Dual View Connection Handler - UPDATED for new data structure
Manages point selection and inter-layer connections in dual view mode
Uses global point IDs directly
"""
import tkinter as tk
from tkinter import messagebox
import math


class DualViewConnectionHandler:
    """Handles point selection and connection creation in dual view mode"""
    
    def __init__(self, parent_tab):
        self.parent_tab = parent_tab
        self.mesh_data = parent_tab.mesh_data
        
        # Dual view selection state - store point IDs directly
        self.dual_selected_left = None   # Point ID selected on left canvas
        self.dual_selected_right = None  # Point ID selected on right canvas
        
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
            layer_name = self.parent_tab.dual_view_layers[0]
        else:
            canvas = self.parent_tab.canvas_right
            layer_name = self.parent_tab.dual_view_layers[1]
        
        # Convert click coordinates to world coordinates
        x, y = self.parent_tab.canvas_to_world(event.x, event.y, canvas)
        
        # Get points in this layer
        layer_data = self.mesh_data.layers.get(layer_name, {})
        point_refs = layer_data.get('point_refs', [])
        
        # Find clicked point by checking all points in layer
        clicked_point_id = None
        min_dist = float('inf')
        
        for point_id in point_refs:
            point_data = self.mesh_data.get_point(point_id)
            if point_data:
                px, py = point_data['x'], point_data['y']
                dist = math.sqrt((px - x)**2 + (py - y)**2)
                if dist < 0.3:  # Click tolerance
                    if dist < min_dist:
                        min_dist = dist
                        clicked_point_id = point_id
        
        if clicked_point_id is not None:
            # Update selection based on which canvas was clicked
            if canvas_side == 0:  # Left canvas
                self.dual_selected_left = clicked_point_id
            else:  # Right canvas
                self.dual_selected_right = clicked_point_id
            
            self._update_selection_display()
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
        
        # Verify points belong to correct layers
        left_layer = self.parent_tab.dual_view_layers[0]
        right_layer = self.parent_tab.dual_view_layers[1]
        
        left_layer_data = self.mesh_data.layers.get(left_layer, {})
        right_layer_data = self.mesh_data.layers.get(right_layer, {})
        
        if self.dual_selected_left not in left_layer_data.get('point_refs', []):
            messagebox.showerror("Error", "Left point must be from the left layer!")
            return
        
        if self.dual_selected_right not in right_layer_data.get('point_refs', []):
            messagebox.showerror("Error", "Right point must be from the right layer!")
            return
        
        # Check if connection already exists
        for conn_id, conn_data in self.mesh_data.connections.items():
            p1 = conn_data.get('point1')
            p2 = conn_data.get('point2')
            if (p1 == self.dual_selected_left and p2 == self.dual_selected_right) or \
               (p1 == self.dual_selected_right and p2 == self.dual_selected_left):
                messagebox.showinfo("Already Connected", 
                                  f"Points {self.dual_selected_left} and {self.dual_selected_right} are already connected!")
                return
        
        # Create the connection
        self.mesh_data.add_connection(self.dual_selected_left, self.dual_selected_right)
        
        # Clear selection
        self.clear_dual_selection()
        
        # Update display
        self.parent_tab.update_plot()
        
        # Show success message
        messagebox.showinfo("Connection Created", 
                          f"Connected Point {self.dual_selected_left} ↔ Point {self.dual_selected_right}")
    
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
            point_data = self.mesh_data.get_point(self.dual_selected_left)
            if point_data:
                cx, cy = self.parent_tab.world_to_canvas(
                    point_data['x'], point_data['y'], 
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
            point_data = self.mesh_data.get_point(self.dual_selected_right)
            if point_data:
                cx, cy = self.parent_tab.world_to_canvas(
                    point_data['x'], point_data['y'], 
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
        
        # Draw connection line preview if both points selected
        if self.dual_selected_left is not None and self.dual_selected_right is not None:
            left_data = self.mesh_data.get_point(self.dual_selected_left)
            right_data = self.mesh_data.get_point(self.dual_selected_right)
            
            if left_data and right_data:
                cx_left, cy_left = self.parent_tab.world_to_canvas(
                    left_data['x'], left_data['y'], 
                    self.parent_tab.canvas_left)
                cx_right, cy_right = self.parent_tab.world_to_canvas(
                    right_data['x'], right_data['y'], 
                    self.parent_tab.canvas_right)
                
                # Arrow on left canvas pointing right
                canvas_width = self.parent_tab.canvas_left.winfo_width() or self.parent_tab.canvas_width // 2
                self.parent_tab.canvas_left.create_line(
                    cx_left, cy_left, canvas_width - 10, cy_left,
                    fill='yellow', width=3, arrow=tk.LAST, dash=(5, 3),
                    tags='dual_selection'
                )
                
                # Arrow on right canvas pointing left
                self.parent_tab.canvas_right.create_line(
                    10, cy_right, cx_right, cy_right,
                    fill='yellow', width=3, arrow=tk.LAST, dash=(5, 3),
                    tags='dual_selection'
                )
