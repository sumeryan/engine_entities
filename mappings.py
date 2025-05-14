def get_specific_mapping():
    """
    Returns a specific mapping for the entity structure.
    This is a placeholder function that should be replaced with actual logic.
    """

    specific_mappings = [
        {"child": "Contract Adjustment", "parent": "Contract"},
        {"child": "Contract Adjustment Data", "parent": "Contract Adjustment"},
        {"child": "Contract Item", "parent": "Contract"},
        {"child": "Contract Measurement", "parent": "Contract"},
        # {"child": "Contract Measurement Asset", "parent": "Contract Measurement"},
        # {"child": "Contract Measurement City", "parent": "Contract Measurement"},
        #{"child": "Contract Measurement FTD", "parent": "Contract Measurement"},
        # {"child": "Contract Measurement Retention", "parent": "Contract Measurement"},
        # {"child": "Contract Measurement SAP Order", "parent": "Contract Measurement"},
        # {"child": "Contract Measurement Work Role", "parent": "Contract Measurement"},
        {"child": "Contract Measurement Record", "parent": "Contract"},
        # {"child": "Contract Measurement Record Asset", "parent": "Contract Measurement Record"},
        # {"child": "Contract Measurement Record Material", "parent": "Contract Measurement Record"},
        # {"child": "Contract Measurement Record Time", "parent": "Contract Measurement Record"},
        # {"child": "Contract Measurement Record Work Role", "parent": "Contract Measurement Record"},
        # {"child": "Contract Measurement Record Work Role", "parent": "Contract Measurement Record"}
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
        "Formula Group Field"
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
                {"doctype": "Contract Adjustment", "key": "contrato"},
                {"doctype": "Contract Item", "key": "contrato"},
                {"doctype": "Contract Measurement", "key": "contrato"},
                {"doctype": "Contract Measurement Record", "key": "contrato"},
            ]
        }
    ]

    return main_doctypes

