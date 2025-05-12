# Hierarchical Tree Builder

Powered by Renoir  
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

## Overview

This repository contains a system for building hierarchical tree structures from document type definitions (doctypes). The system is designed for contract management, asset tracking, and related business operations.

## Key Components

- **Document Types (Doctypes)**: Main entities like Assets, Contracts, etc.
- **Fields**: Properties of each doctype with specific data types (string, date, currency, etc.)
- **Relationships**: Parent-child mappings between doctypes, with prioritized rules
- **Hierarchical Structure**: Tree-like organization of entities and their fields

## Main Files

1. `doctypes.json` - Contains detailed field definitions for various document types
2. `specified_mapping.json` - Contains rules for mandatory parent-child relationships
3. `doctype_translations.json` - Contains translations of doctype keys to Portuguese
4. `output_hierarchical.json` - Contains the generated hierarchical relationships
5. `build_hierarchical_tree.py` - Python script that builds the hierarchical structure

## Hierarchical Model Structure

The hierarchical model follows this structure:

```json
{
    "entities": [
        {
            "key": "[DOCTYPE NAME]",
            "description": "[DOCTYPE NAME OR FIELD LABEL]",
            "fieldname": "[NULL FOR DOCTYPE, FIELDNAME FOR FIELDS]",
            "type": "[doctype FOR DOCTYPE; string, numeric, date, datetime, boolean, select OR text FOR FIELDS]",
            "path": "normalized_description",
            "dragandrop": true/false,
            "children": [
                // Child entities follow the same structure
                // Paths are formed as parent_path.normalized_description
            ]
        }
    ]
}
```

## Hierarchical Tree Building Rules

1. Process doctypes from `doctypes.json` to extract definitions and fields
2. Apply mandatory parent-child relationships from `specified_mapping.json` with priority
3. Use "option" fields to identify potential child doctypes with these conditions:
   - They don't have a mandatory parent in `specified_mapping.json`, or
   - The current doctype is their defined mandatory parent
4. Map field types appropriately (string, numeric, date, etc.)
5. Apply translations from `doctype_translations.json` when available
6. Generate normalized paths for easy traversal:
   - Root entities: `normalized_description`
   - Child entities: `parent_normalized_description.child_normalized_description`
7. Save the resulting structure to `output_hierarchical.json`

## Usage

To build the hierarchical tree:

```bash
# Install required packages
pip install anytree

# Run the script
python build_hierarchical_tree.py
```

## Development

The main script (`build_hierarchical_tree.py`) provides several functions:

- `build_hierarchical_tree()`: Main function to build the tree structure
- `create_doctype_entity()`: Creates an entity for a doctype and its fields
- `process_doctype_fields()`: Processes fields of a doctype recursively
- `apply_specified_mapping()`: Applies parent-child relationships from mapping
- `normalize_string()`: Normalizes strings for path creation
- `update_all_paths()`: Updates paths to include full parent-child chains
- `doctype_to_hierarquical()`: Main entry point for conversion process

Example usage:

```python
import json
from build_hierarchical_tree import doctype_to_hierarquical

# Load doctypes and mappings
with open('doctypes.json', 'r', encoding='utf-8') as f:
    doctypes = json.load(f)

with open('specified_mapping.json', 'r', encoding='utf-8') as f:
    mappings = json.load(f)

# Build the hierarchical tree
hierarchical_data = doctype_to_hierarquical(doctypes, mappings)

# Save to output file
with open('output_hierarchical.json', 'w', encoding='utf-8') as f:
    json.dump(hierarchical_data, f, indent=4, ensure_ascii=False)
```