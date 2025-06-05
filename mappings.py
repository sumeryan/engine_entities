def get_specific_mapping():
    """
    Returns a specific mapping for the entity structure.
    This is a placeholder function that should be replaced with actual logic.
    """

    specific_mappings = [
        {"child": "Contract Adjustment", "parent": "Contract"},
        {"child": "Contract Item", "parent": "Contract"},
        {"child": "Contract Measurement", "parent": "Contract","filters":[{"medicaovigente":"sim"}]},
        {"child": "Contract Measurement Record", "parent": "Contract","filters":[{"medicaovigente":"sim"}]},
    ]

    # Placeholder for specific mapping logic
    return specific_mappings


def get_ignore_mapping():
    """
    Returns a specific mapping for the entity structure.
    This is a placeholder function that should be replaced with actual logic.
    """

    ignore_mappings = [
        "Formula",
        "Formula Template",
        "Formula Group",
        "Formula Fields",
        "Formula Template",
        "Formula Group Field",
        "Formula Group Template",
        "Asset Config Kartado",
        "Contract Item Config Kartado",
        "Integration Record Keys",
        "Item Config Kartado",
        "Integration Inconsistency",
        "Integration Record",
        "Depth Period Setting",
        "TestPut",
        "TestPutChild",
        "Work Role Config Kartado",
    ]

    # Placeholder for specific mapping logic
    return ignore_mappings

def get_main_data():
    """
    Return main data for the entity structure.
    """

    main_doctypes = [
        {
            "doctype": "Contract",
            "key": "name",
            "childs": [
                {   
                    "doctype": "Contract Adjustment", 
                    "key": "contrato"
                },
                {   
                    "doctype": "Contract Item", 
                    "key": "contrato"
                },
                {   "doctype": "Contract Measurement", 
                    "key": "contrato",
                    "filters": [{"field":"medicaovigente", "value": "Sim"}]
                },
                {
                    "doctype": "Contract Measurement Record", 
                    "key": "contrato",
                    "filters": [{"field":"medicaovigente", "value": "Sim"}]
                }
            ]
        }
    ]

    return main_doctypes

