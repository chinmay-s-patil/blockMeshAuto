import copy

class HistoryManager:
    def __init__(self, mesh_data, max_states=5):
        self.mesh_data = mesh_data
        self.max_states = max_states
        self.undo_stack = []
        self.redo_stack = []
        self.update_callback = None

    def set_update_callback(self, callback):
        """Callback triggered after an undo or redo to refresh the UI."""
        self.update_callback = callback

    def save_state(self):
        """Save the current state to the undo stack and clear the redo stack."""
        # Deep copy to ensure distinct states
        state = copy.deepcopy(self.mesh_data.to_dict())
        self.undo_stack.append(state)
        
        # Enforce maximum history limit
        if len(self.undo_stack) > self.max_states:
            self.undo_stack.pop(0)
            
        self.redo_stack.clear()

    def undo(self):
        """Revert to the previous state if available."""
        if not self.undo_stack:
            return False
            
        # Save current state for redo
        current_state = copy.deepcopy(self.mesh_data.to_dict())
        self.redo_stack.append(current_state)
        
        # Pop the last state and apply it
        previous_state = self.undo_stack.pop()
        self.mesh_data.from_dict(previous_state)
        
        # Notify application to refresh UI
        if self.update_callback:
            self.update_callback()
            
        return True

    def redo(self):
        """Reapply a previously undone state if available."""
        if not self.redo_stack:
            return False
            
        # Save current state for undo
        current_state = copy.deepcopy(self.mesh_data.to_dict())
        self.undo_stack.append(current_state)
        
        # Pop the next state and apply it
        next_state = self.redo_stack.pop()
        self.mesh_data.from_dict(next_state)
        
        # Notify application to refresh UI
        if self.update_callback:
            self.update_callback()
            
        return True
