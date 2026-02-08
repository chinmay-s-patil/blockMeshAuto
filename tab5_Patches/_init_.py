"""
Tab 5: Hex Block 3D View & Patch Assignment

This module provides:
- 3D rendering of hex blocks with internal face detection
- Hierarchical patch type selection (general -> specific)
- Face picking and patch assignment
"""

from .tab5_main import Tab5HexPatches
from .tab5_patch_config import (
    PATCH_DEFINITIONS,
    get_general_types,
    get_sub_types,
    get_patch_config,
    get_editable_fields
)
from .tab5_hex_renderer import HexBlockRenderer
from .tab5_patch_panels import PatchAssignmentPanel, PatchListPanel

__all__ = [
    'Tab5HexPatches',
    'PATCH_DEFINITIONS',
    'get_general_types',
    'get_sub_types', 
    'get_patch_config',
    'get_editable_fields',
    'HexBlockRenderer',
    'PatchAssignmentPanel',
    'PatchListPanel'
]