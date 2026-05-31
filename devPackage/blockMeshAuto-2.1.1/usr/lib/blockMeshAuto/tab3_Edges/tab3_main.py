"""
Tab 3: Edge Editor Main - Wrapper with method delegation
"""
from tab3_Edges.TabEdgeEditor import Tab3EdgeEditor as EdgeEditorCore


class Tab3EdgeEditor:
    """Wrapper that delegates all method calls to the inner edge_editor"""

    def __init__(self, parent_frame, mesh_data):
        self.parent = parent_frame
        self.mesh_data = mesh_data
        self.edge_editor = EdgeEditorCore(parent_frame, mesh_data)

    def __getattr__(self, name):
        """Delegate to inner edge_editor"""
        if name.startswith('_Tab3EdgeEditor__'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        if hasattr(self.edge_editor, name):
            return getattr(self.edge_editor, name)

        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def _update_edge_list(self):
        """Update edge list - exposed for main.py compatibility"""
        if hasattr(self.edge_editor, '_update_edge_list'):
            self.edge_editor._update_edge_list()
        elif hasattr(self.edge_editor, 'update_edge_list'):
            self.edge_editor.update_edge_list()

    def update_edge_list(self):
        """Update edge list - public method"""
        if hasattr(self.edge_editor, 'update_edge_list'):
            self.edge_editor.update_edge_list()
        elif hasattr(self.edge_editor, '_update_edge_list'):
            self.edge_editor._update_edge_list()

    def cleanup(self):
        if hasattr(self.edge_editor, 'cleanup'):
            self.edge_editor.cleanup()