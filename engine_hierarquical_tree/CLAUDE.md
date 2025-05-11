# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a system for building hierarchical tree structures from document type definitions (doctypes). The system is designed for contract management, asset tracking, and related business operations. The project consists of these main files:

1. `doctypes.json` - Contains detailed field definitions for various document types (doctypes) in a structured format
2. `specified_mapping.json` - Contains rules for mandatory parent-child relationships
3. `doctype_translations.json` - Contains translations of doctype keys to Portuguese for display in the hierarchical tree
4. `output_hierarchical.json` - Contains the generated hierarchical relationships between entities

The schemas define document types including Assets, Contracts, Measurements, Cities, Highways, and related entities with their respective fields and relationships.

## Project Architecture

The system is designed to represent hierarchical data structures with parent-child relationships. The key components include:

- **Document Types (Doctypes)**: Main entities like Assets, Contracts, etc.
- **Fields**: Properties of each doctype with specific data types (string, date, currency, etc.)
- **Relationships**: Parent-child mappings between doctypes, with the following priority:
  - Rules in specified_mapping.json (mandatory parent-child relationships) take precedence
  - "option" fields in doctypes.json (indicates a child doctype) are used if not overridden by specified_mapping.json
- **Hierarchical Structure**: Tree-like organization of entities and their fields using the anytree library
- **Priority Rules**: Items in specified_mapping.json are enforced as exclusive parent-child relationships that override any other relationships

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
            "path": "normalized_description", // Normalized description (lowercase, no accents, special chars as underscores)
            "dragandrop": true/false, // false for doctypes, true for fields
            "children": [ // DOCTYPE fields, or parent-child relationships via "option" or specified_mapping
                // Child entities follow the same structure with paths as parent_path.normalized_description
            ]
        }
    ]
}
```

## Development Tasks

### Working with the Hierarchical Tree Builder

To build the hierarchical tree:

```bash
# Install required packages
pip install anytree

# Run the script
python build_hierarchical_tree.py
```

The script follows these rules to build the hierarchical structure:

1. It processes the doctypes.json file to extract doctype definitions and their fields
2. The specified_mapping.json file defines mandatory parent-child relationships that take precedence
3. "option" fields in doctypes indicate potential child doctypes, which are only included if:
   - They don't have a mandatory parent defined in specified_mapping.json, or
   - The current doctype is their defined mandatory parent
4. Doctypes defined in specified_mapping.json will only appear as children of their specified parents,
   not as children of any other doctype even if referenced in "option" fields
5. Field types are mapped to hierarchical model types (string, numeric, date, etc.)
6. The doctype_translations.json file provides Portuguese translations for doctype names in the tree
7. Paths are generated using normalized descriptions, with each entity's path representing its full ancestry:
   - Root entities: `normalized_description`
   - Child entities: `parent_normalized_description.child_normalized_description`
   - Normalization removes accents, converts to lowercase, and replaces special characters with underscores
8. The resulting hierarchical structure is saved to output_hierarchical.json

### Working with JSON Files

To inspect or modify the JSON files:

```bash
# View the structure of the doctype definitions
jq -C . doctypes.json | less -R

# View the hierarchical structure
jq -C . output_hierarchical.json | less -R
```

### Python Script

The script provides several functions to help with building the hierarchical tree:

- `build_hierarchical_tree()`: Main function to build the tree structure
- `create_doctype_entity()`: Creates an entity for a doctype and its fields
- `process_doctype_fields()`: Processes fields of a doctype recursively
- `apply_specified_mapping()`: Applies parent-child relationships from specified_mapping.json

Example usage:

```python
import json
from build_hierarchical_tree import build_hierarchical_tree

# Build the hierarchical tree
hierarchical_data = build_hierarchical_tree()

# Save to output file
with open('output_hierarchical.json', 'w', encoding='utf-8') as f:
    json.dump(hierarchical_data, f, indent=4, ensure_ascii=False)
```