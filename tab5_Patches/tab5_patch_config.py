"""
Patch Configuration System for OpenFOAM blockMesh
Defines general patch types and their specific sub-types with parameters
"""

PATCH_DEFINITIONS = {
    "wall": {
        "description": "Wall boundary",
        "sub_types": {
            "noSlip": {
                "description": "No-slip wall (zero velocity)",
                "fields": {
                    "U": {"type": "fixedValue", "value": "uniform (0 0 0)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "kqRWallFunction", "value": "uniform 0.1"},
                    "epsilon": {"type": "epsilonWallFunction", "value": "uniform 0.01"},
                    "nut": {"type": "nutkWallFunction", "value": "uniform 0"}
                }
            },
            "slip": {
                "description": "Slip wall (zero normal velocity, free tangential)",
                "fields": {
                    "U": {"type": "slip"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "zeroGradient"},
                    "epsilon": {"type": "zeroGradient"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "movingWall": {
                "description": "Moving wall with specified velocity",
                "fields": {
                    "U": {"type": "fixedValue", "value": "uniform (0 0 0)", "editable": True, "label": "Wall velocity (m/s)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "kqRWallFunction", "value": "uniform 0.1"},
                    "epsilon": {"type": "epsilonWallFunction", "value": "uniform 0.01"},
                    "nut": {"type": "nutkWallFunction", "value": "uniform 0"}
                }
            },
            "roughWall": {
                "description": "Rough wall with roughness height",
                "fields": {
                    "U": {"type": "fixedValue", "value": "uniform (0 0 0)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "kqRWallFunction", "value": "uniform 0.1"},
                    "epsilon": {"type": "epsilonWallFunction", "value": "uniform 0.01"},
                    "nut": {"type": "nutRoughWallFunction", "value": "uniform 0", "Ks": "uniform 0.0001", "Cs": "uniform 0.5", "editable": True, "label": "Roughness Ks (m)"}
                }
            }
        }
    },
    "patch": {
        "description": "Generic patch",
        "sub_types": {
            "zeroGradient": {
                "description": "Zero gradient for all fields",
                "fields": {
                    "U": {"type": "zeroGradient"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "zeroGradient"},
                    "epsilon": {"type": "zeroGradient"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "symmetry": {
                "description": "Symmetry plane",
                "fields": {
                    "U": {"type": "symmetry"},
                    "p": {"type": "symmetry"},
                    "k": {"type": "symmetry"},
                    "epsilon": {"type": "symmetry"},
                    "nut": {"type": "symmetry"}
                }
            },
            "empty": {
                "description": "Empty patch for 2D simulations",
                "fields": {
                    "U": {"type": "empty"},
                    "p": {"type": "empty"},
                    "k": {"type": "empty"},
                    "epsilon": {"type": "empty"},
                    "nut": {"type": "empty"}
                }
            }
        }
    },
    "inlet": {
        "description": "Inlet boundary",
        "sub_types": {
            "velocityInlet": {
                "description": "Fixed velocity inlet",
                "fields": {
                    "U": {"type": "fixedValue", "value": "uniform (0 0 0)", "editable": True, "label": "Inlet velocity (m/s)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "turbulentIntensityKineticEnergyInlet", "intensity": "0.05", "value": "uniform 0.1", "editable": True, "label": "Turbulence intensity"},
                    "epsilon": {"type": "turbulentMixingLengthDissipationRateInlet", "mixingLength": "0.01", "value": "uniform 0.01", "editable": True, "label": "Mixing length (m)"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "pressureInlet": {
                "description": "Fixed pressure inlet",
                "fields": {
                    "U": {"type": "zeroGradient"},
                    "p": {"type": "fixedValue", "value": "uniform 0", "editable": True, "label": "Inlet pressure (Pa)"},
                    "k": {"type": "zeroGradient"},
                    "epsilon": {"type": "zeroGradient"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "flowRateInlet": {
                "description": "Fixed flow rate inlet",
                "fields": {
                    "U": {"type": "flowRateInletVelocity", "volumetricFlowRate": "0.001", "value": "uniform (0 0 0)", "editable": True, "label": "Volumetric flow rate (m³/s)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "turbulentIntensityKineticEnergyInlet", "intensity": "0.05", "value": "uniform 0.1"},
                    "epsilon": {"type": "turbulentMixingLengthDissipationRateInlet", "mixingLength": "0.01", "value": "uniform 0.01"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            }
        }
    },
    "outlet": {
        "description": "Outlet boundary",
        "sub_types": {
            "pressureOutlet": {
                "description": "Fixed pressure outlet",
                "fields": {
                    "U": {"type": "zeroGradient"},
                    "p": {"type": "fixedValue", "value": "uniform 0", "editable": True, "label": "Outlet pressure (Pa)"},
                    "k": {"type": "zeroGradient"},
                    "epsilon": {"type": "zeroGradient"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "velocityOutlet": {
                "description": "Fixed velocity outlet",
                "fields": {
                    "U": {"type": "fixedValue", "value": "uniform (0 0 0)", "editable": True, "label": "Outlet velocity (m/s)"},
                    "p": {"type": "zeroGradient"},
                    "k": {"type": "zeroGradient"},
                    "epsilon": {"type": "zeroGradient"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            },
            "outflow": {
                "description": "Outflow (fully developed)",
                "fields": {
                    "U": {"type": "inletOutlet", "inletValue": "uniform (0 0 0)", "value": "uniform (0 0 0)"},
                    "p": {"type": "fixedValue", "value": "uniform 0", "editable": True, "label": "Outlet pressure (Pa)"},
                    "k": {"type": "inletOutlet", "inletValue": "uniform 0.1", "value": "uniform 0.1"},
                    "epsilon": {"type": "inletOutlet", "inletValue": "uniform 0.01", "value": "uniform 0.01"},
                    "nut": {"type": "calculated", "value": "uniform 0"}
                }
            }
        }
    },
    "cyclic": {
        "description": "Cyclic/periodic boundary",
        "sub_types": {
            "cyclic": {
                "description": "Standard cyclic (must have matching pair)",
                "fields": {
                    "U": {"type": "cyclic"},
                    "p": {"type": "cyclic"},
                    "k": {"type": "cyclic"},
                    "epsilon": {"type": "cyclic"},
                    "nut": {"type": "cyclic"}
                },
                "requires_pair": True,
                "editable": True,
                "label": "Matching cyclic patch name"
            },
            "cyclicAMI": {
                "description": "Arbitrary Mesh Interface cyclic",
                "fields": {
                    "U": {"type": "cyclicAMI"},
                    "p": {"type": "cyclicAMI"},
                    "k": {"type": "cyclicAMI"},
                    "epsilon": {"type": "cyclicAMI"},
                    "nut": {"type": "cyclicAMI"}
                },
                "requires_pair": True,
                "editable": True,
                "label": "Matching cyclicAMI patch name"
            }
        }
    },
    "custom": {
        "description": "Custom patch definition",
        "sub_types": {
            "fullyCustom": {
                "description": "Define all fields manually",
                "fields": {},
                "custom": True
            }
        }
    }
}


def get_general_types():
    """Get list of general patch types"""
    return list(PATCH_DEFINITIONS.keys())


def get_sub_types(general_type):
    """Get sub-types for a general patch type"""
    if general_type in PATCH_DEFINITIONS:
        return list(PATCH_DEFINITIONS[general_type]["sub_types"].keys())
    return []


def get_patch_config(general_type, sub_type):
    """Get configuration for a specific patch type"""
    if general_type in PATCH_DEFINITIONS:
        sub_types = PATCH_DEFINITIONS[general_type]["sub_types"]
        if sub_type in sub_types:
            return sub_types[sub_type]
    return None


def get_editable_fields(general_type, sub_type):
    """Get list of editable fields and their labels"""
    config = get_patch_config(general_type, sub_type)
    if not config:
        return []
    
    editable = []
    for field_name, field_config in config.get("fields", {}).items():
        if field_config.get("editable", False):
            editable.append({
                "field": field_name,
                "label": field_config.get("label", field_name),
                "value": field_config.get("value", ""),
                "type": field_config.get("type", "")
            })
    
    # Check if patch itself has editable properties
    if config.get("editable", False):
        editable.append({
            "field": "_patch_config",
            "label": config.get("label", "Configuration"),
            "value": "",
            "type": "patch_property"
        })
    
    return editable