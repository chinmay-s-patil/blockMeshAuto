"""
Tab 5: Hex Block 3D View & Patch Assignment

This module provides:
- 3D rendering of hex blocks with internal face detection
- Hierarchical patch type selection (general -> specific)
- Face picking and patch assignment
- Patch normal editing
- Patch editor for modifying existing patches
"""

from .tab5_main import Tab5HexPatches
from .tab5_patch_config import (
    PATCH_DEFINITIONS,
    get_patch_types,
    get_patch_info,
    get_parameters,
    is_custom
)
from .tab5_hex_renderer import HexBlockRenderer
from .tab5_patch_panels import PatchAssignmentPanel, PatchListPanel
from .tab5_patch_normals import PatchNormalsTab
from .tab5_patch_editor import PatchEditorDialog, open_patch_editor

__all__ = [
    'Tab5HexPatches',
    'PATCH_DEFINITIONS',
    'get_patch_types',
    'get_patch_info',
    'get_parameters',
    'is_custom',
    'HexBlockRenderer',
    'PatchAssignmentPanel',
    'PatchListPanel',
    'PatchNormalsTab',
    'PatchEditorDialog',
    'open_patch_editor'
]