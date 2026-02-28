"""
Tab 3 Edge Model - Data model and operations for edges
"""


class EdgeModel:
    """Manages edge data operations"""

    def __init__(self, mesh_data):
        self.mesh_data = mesh_data
        self._ensure_edges_dict()

    def _ensure_edges_dict(self):
        """Ensure mesh_data.edges is a dict (not a list)"""
        if not hasattr(self.mesh_data, 'edges'):
            self.mesh_data.edges = {}
        elif isinstance(self.mesh_data.edges, list):
            edge_dict = {}
            for i, edge in enumerate(self.mesh_data.edges):
                edge_dict[str(i + 1)] = edge
            self.mesh_data.edges = edge_dict

    def get_all_edges(self):
        """Get all edges as a list of (edge_id, edge_data) tuples"""
        return [(k, v) for k, v in sorted(self.mesh_data.edges.items(), 
                                          key=lambda x: int(x[0]))]

    def get_edge(self, edge_id):
        """Get a single edge by ID"""
        return self.mesh_data.edges.get(str(edge_id))

    def add_edge(self, edge_data):
        """Add a new edge and return its ID"""
        existing_ids = [int(k) for k in self.mesh_data.edges.keys()]
        next_id = max(existing_ids, default=0) + 1
        self.mesh_data.edges[str(next_id)] = edge_data
        return next_id

    def update_edge(self, edge_id, edge_data):
        """Update an existing edge"""
        self.mesh_data.edges[str(edge_id)] = edge_data

    def delete_edge(self, edge_id):
        """Delete an edge by ID"""
        edge_id_str = str(edge_id)
        if edge_id_str in self.mesh_data.edges:
            del self.mesh_data.edges[edge_id_str]
            return True
        return False

    def delete_all_edges(self):
        """Delete all edges"""
        self.mesh_data.edges.clear()

    def format_point(self, p):
        """Format a point for display"""
        if isinstance(p, int):
            return f"Point {p}"
        return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"

    def get_edge_display_text(self, edge_id, edge_data):
        """Get display text for an edge"""
        edge_type = edge_data.get('type', 'line')
        start = edge_data.get('start')
        end = edge_data.get('end')

        def fmt_point(p):
            if isinstance(p, int):
                return f"P{p}"
            return f"({p[0]:.1f},{p[1]:.1f},{p[2]:.1f})"

        extra = ""
        if edge_type == 'arc' and 'intermediate' in edge_data:
            mid = edge_data['intermediate']
            if isinstance(mid, int):
                extra = f" via P{mid}"
            else:
                extra = f" via manual"
        elif edge_type in ['spline', 'polyLine'] and 'intermediate' in edge_data:
            intermediate = edge_data['intermediate']
            if isinstance(intermediate, list):
                extra = f" +{len(intermediate)} pts"

        return f"Edge {edge_id}: {edge_type} ({fmt_point(start)} → {fmt_point(end)}{extra})"

    def get_edge_details_text(self, edge_data):
        """Get detailed text for an edge"""
        def fmt_point(p):
            if isinstance(p, int):
                return f"Point {p}"
            return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"

        details = f"Type: {edge_data.get('type', 'line')}"
        details += f"\nStart: {fmt_point(edge_data.get('start'))}"
        details += f"\nEnd: {fmt_point(edge_data.get('end'))}"

        if 'intermediate' in edge_data:
            intermediate = edge_data['intermediate']
            if isinstance(intermediate, list):
                details += f"\nIntermediate: {len(intermediate)} points"
            else:
                details += f"\nMid point: {fmt_point(intermediate)}"

        return details

    def get_edges_for_json(self):
        """Get edges as a list for JSON serialization"""
        edges_list = []
        for edge_id, edge_data in sorted(self.mesh_data.edges.items(), key=lambda x: int(x[0])):
            edge_copy = dict(edge_data)
            edge_copy['id'] = edge_id
            edges_list.append(edge_copy)
        return edges_list

    def load_edges_from_json(self, edges_list):
        """Load edges from JSON list"""
        self.mesh_data.edges = {}
        for edge_data in edges_list:
            edge_id = str(edge_data.pop('id', None))
            if edge_id and edge_id != 'None':
                self.mesh_data.edges[edge_id] = edge_data
            else:
                # Generate new ID if missing
                self.add_edge(edge_data)