"""
Simplified Patch Configuration for OpenFOAM blockMesh
Just the boundary types that go in blockMeshDict, no field conditions
"""

PATCH_DEFINITIONS = {
    "patch": {
        "description": "Generic boundary - default type for general boundaries",
        "openfoam_type": "patch"
    },
    "wall": {
        "description": "Solid wall - impermeable boundary",
        "openfoam_type": "wall"
    },
    "symmetryPlane": {
        "description": "Planar symmetry - legacy symmetry boundary (deprecated, use 'symmetry')",
        "openfoam_type": "symmetryPlane"
    },
    "symmetry": {
        "description": "General symmetry - mirror boundary condition",
        "openfoam_type": "symmetry"
    },
    "empty": {
        "description": "2D case - for 2D simulations (front/back faces)",
        "openfoam_type": "empty"
    },
    "wedge": {
        "description": "Axisymmetric - for axisymmetric cases",
        "openfoam_type": "wedge",
        "parameters": {
            "axis": {"label": "Axis of rotation (e.g., '(0 0 1)')", "default": "(0 0 1)"}
        }
    },
    "cyclic": {
        "description": "Periodic (conformal) - matching periodic boundaries",
        "openfoam_type": "cyclic",
        "parameters": {
            "neighbourPatch": {"label": "Neighbour patch name", "default": ""}
        }
    },
    "cyclicAMI": {
        "description": "Periodic (non-conformal) - arbitrary mesh interface periodic",
        "openfoam_type": "cyclicAMI",
        "parameters": {
            "neighbourPatch": {"label": "Neighbour patch name", "default": ""}
        }
    },
    "custom": {
        "description": "Custom type - manually specify the boundary type",
        "openfoam_type": "custom",
        "custom": True
    }
}


def get_patch_types():
    """Get list of available patch types"""
    return list(PATCH_DEFINITIONS.keys())


def get_patch_info(patch_type):
    """Get information about a patch type"""
    return PATCH_DEFINITIONS.get(patch_type, None)


def get_parameters(patch_type):
    """Get editable parameters for a patch type"""
    patch_info = PATCH_DEFINITIONS.get(patch_type, {})
    return patch_info.get("parameters", {})


def is_custom(patch_type):
    """Check if patch type is custom"""
    patch_info = PATCH_DEFINITIONS.get(patch_type, {})
    return patch_info.get("custom", False)