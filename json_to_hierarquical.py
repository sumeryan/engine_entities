"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

JSON to Hierarchical Structure Transformer Module.
This module provides functions to transform DocTypes metadata into a hierarchical entity structure.
It handles string normalization, field type mapping, entity creation, and hierarchical relationship building.
"""

import unicodedata
import re
import specific_mapping

def normalize_string(text):
    """
    Normalizes a string: replaces accents with base characters (preserving case)
    and replaces spaces/non-alphanumeric characters with underscores.
    
    Args:
        text (str): The string to normalize.
        
    Returns:
        str: The normalized string.
    """
    
    if not text:
        return text
    try:
        text_str = str(text)
        # Transliterate accents to base characters (e.g., á -> a, Ç -> C)
        # NFKD decomposes characters like 'ç' into 'c' and a combining accent.
        nfkd_form = unicodedata.normalize('NFKD', text_str)
        # Remove combining accents, preserving the base letter and its case.
        sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # Replace spaces and other non-alphanumeric characters (except underscore) with underscore
        # The \W pattern matches any character that is not a letter, number, or underscore.
        # We apply this to the string without accents, but with the original case preserved.
        normalized = re.sub(r'\W+', '_', sem_acentos)
        # Remove multiple underscores that may have been created
        normalized = re.sub(r'_+', '_', normalized)
        # Remove underscores at the beginning or end, if any
        normalized = normalized.strip('_')
        # If the string becomes empty (e.g., it only had non-alphanumeric characters), return a fallback.
        # This fallback still uses lower() for simplicity, but the main logic preserves case.
        if not normalized:
             normalized = re.sub(r'\s+', '_', text_str.lower()).strip('_') # Simple fallback
             if not normalized:
                 # If still empty, return a generic value to avoid empty string
                 return "normalized_string_fallback"
        return normalized
    except Exception as e:
        print(f"Error normalizing string '{text}': {e}")
        # In case of unexpected error, return a simplified version (lowercase, spaces to _)
        return re.sub(r'\s+', '_', str(text).lower()).strip('_')

def map_field_type(field_type, key=None):
    """
    Maps DocType field types to generic types.

    Args:
        field_type (str): DocType field type
        key (str, optional): Field name, used for special fields

    Returns:
        str: Generic type (string, numeric, datetime, boolean, etc.)
    """

    # Mapping of field types to generic types
    type_mapping = {
        # Text types
        "Data": "string",
        "Small Text": "string",
        "Text": "string",
        "Text Editor": "string",
        "Code": "string",
        "Link": "string",
        "Select": "string",
        "Read Only": "string",

        # Numeric types
        "Int": "numeric",
        "Float": "numeric",
        "Currency": "numeric",
        "Percent": "numeric",

        # Date/time types
        "Date": "datetime",
        "Datetime": "datetime",
        "Time": "datetime",

        # Boolean types
        "Check": "boolean",

        # Other types
        "Table": "table", # Kept for reference, but ignored in process_attributes
        "Attach": "file",
        "Attach Image": "image",
        "Signature": "image",
        "Color": "string",
        "Geolocation": "geolocation"
    }

    # Special fields that have specific types
    special_fields = {
        "creation": "datetime",
        "modified": "datetime",
        "docstatus": "numeric",
        "idx": "numeric"
    }

    # Check if it's a special field
    if field_type in type_mapping:
        return type_mapping[field_type]
    elif key in special_fields:
        return special_fields[key]
    else:
        # Return 'string' as default if the type is not mapped
        return "string"

def process_attributes(fields_metadata):
    """
    Processes entity attributes from field metadata.

    Args:
        fields_metadata (list): Field metadata
        is_child (bool): Indicates if it's a child entity

    Returns:
        list: List of processed attributes (without the 'value' field)
    """
    attributes = []

    # Process each field in the metadata
    for field in fields_metadata:
        field_name = field.get("fieldname")
        field_type = field.get("fieldtype")
        field_hidden = field.get("hidden")

        # Ignore Table fields (will be treated as separate entities)
        if field_type == "Table":
            continue
        if field_hidden == 1: # Ignore hidden fields
            continue
        if field_name[:2] == "f_" or field_name[:3] == "fm_": # Ignore formula fields
            continue
        # Ignore internal/specific fields that should not be direct attributes,
        # including 'parent', which is handled separately in create_entity.
        if field_name in [
            "name", 
            "owner", 
            "creation", 
            "modified", 
            "modified_by",
            "docstatus",
            "idx",
            "parentfield",
            "parenttype",
            "doctype",
            "parent"]: # Added 'parent' to the ignored list
            continue

        # Map field type to generic type
        generic_type = map_field_type(field_type, field_name)

        # Create attribute without the 'value' field
        attribute = {
            "key": field_name,
            "type": generic_type,
            "description": normalize_string(field.get("label")) if field.get("label") else None
        }
        attributes.append(attribute)

    return attributes

def create_entity(
        doctype_name, 
        fields_metadata, 
        is_child=False, 
        parent_doctype=None):
    """
    Creates an entity from field metadata.

    Args:
        doctype_name (str): DocType name
        fields_metadata (list): DocType field metadata
        is_child (bool): Indicates if it's a child entity
        parent_doctype (str): Parent DocType name, if it's a child entity

    Returns:
        dict: Entity in the specified format
    """
    # Process attributes (without values)
    attributes = process_attributes(fields_metadata)

    # Add the 'name' attribute as the first item in the list
    attributes.insert(0, {"key": "name", "type": "string"})

    # Add 'parent' attribute explicitly for child entities
    if is_child and parent_doctype:
        # Check if the 'parent' attribute already exists (if it comes from metadata)
        parent_attr_exists = any(attr['key'] == 'parent' for attr in attributes)
        if not parent_attr_exists:
             attributes.append({
                 "key": "parent",
                 "type": "string", # Assuming the reference to the parent is a string (ID/name)
             })

    # Create relationships (only for child entities, pointing to the parent)
    relationships = []
    if is_child and parent_doctype:
        relationships.append({
            "sourceKey": "parent", # The key in the child entity that points to the parent
            "destinationEntity": parent_doctype, # The parent entity type
            "destinationKey": "name" # The key in the parent entity (usually 'name')
        })

    # Add relationships for Link fields
    for field in fields_metadata:
        if field.get("fieldtype") == "Link":
            field_name = field.get("fieldname")
            destination_entity = field.get("options")
            # Ignore links to Web Page or Report, or if there's no 'options'
            if destination_entity and destination_entity not in ["Web Page", "Report"]:
                 # Avoid adding duplicate relationship if it already exists (e.g., parent)
                 is_duplicate = any(
                     rel["sourceKey"] == field_name and rel["destinationEntity"] == destination_entity
                     for rel in relationships
                 )
                 if not is_duplicate:
                    relationships.append({
                        "sourceKey": field_name,
                        "destinationEntity": destination_entity,
                        "destinationKey": "name" # Assuming the destination key is 'name'
                    })

    # Create entity structure
    entity = {
        "entity": {
            "type": doctype_name,
            "description": normalize_string(doctype_name),
            "attributes": attributes,
            "relationships": relationships
        }
    }

    return entity

def process_fields_for_hierarchy(fields_metadata, all_doctypes_data, process_nested_relationships=True):
    """
    Processes field metadata for the hierarchical structure with controlled recursion.

    Args:
        fields_metadata (list): Field metadata for the current DocType.
        all_doctypes_data (dict): Complete dictionary {doctype_name: fields_metadata_list}.
        process_nested_relationships (bool): If True, processes Links/Tables at this level.
                                             If False, ignores Tables and treats Links as normal fields.

    Returns:
        list: List of nodes representing fields or linked DocTypes.
    """
    processed_nodes = []
    if not isinstance(fields_metadata, list):
        print(f"Warning: Invalid field metadata received by process_fields_for_hierarchy.")
        return processed_nodes

    for field in fields_metadata:
        if not isinstance(field, dict):
            continue

        field_name = field.get("fieldname")
        field_type = field.get("fieldtype")
        field_hidden = field.get("hidden")
        label = field.get("label")
        options = field.get("options")

        # --- Ignore irrelevant fields ---
        if not field_name or not field_type:
            continue
        if field_hidden == 1: # Ignore hidden fields
            continue
        if field_name.startswith("f_") or field_name.startswith("fm_"): # Ignore formula fields
            continue
        if field_name in ["owner", "creation", "modified", "modified_by",
                          "docstatus", "idx", "parentfield", "parenttype", "doctype",
                          "parent"]:
            continue

        # --- Conditional Processing Logic (Based on process_nested_relationships) ---

        # 1. Process Links at the main level?
        if field_type == "Link" and process_nested_relationships:
            destination_entity = options
            if destination_entity and destination_entity not in ["Web Page", "Report"]:
                # Get the linked DocType metadata
                linked_fields_metadata = all_doctypes_data.get(destination_entity, [])
                # Call recursively WITHOUT processing more nested relationships
                linked_fields = process_fields_for_hierarchy(
                    linked_fields_metadata, all_doctypes_data, process_nested_relationships=False
                )
                # Create node for the linked DocType
                normalized_description = normalize_string(destination_entity)
                linked_doctype_node = {
                    "key": normalized_description, # Key continues to use the normalized description
                    "description": destination_entity, # Description uses the original doctype name
                    "fieldname": destination_entity, # New fieldname property
                    "type": "doctype",
                    "children": linked_fields # Add the processed fields of the linked DocType
                }
                processed_nodes.append(linked_doctype_node)
                continue # Skip to the next field

        # 2. Ignore Tables if not at the main level?
        if field_type == "Table" and not process_nested_relationships:
            continue 
        
        # 3. Ignore Tables at the main level (will be handled by child_parent_mapping)
        if field_type == "Table" and process_nested_relationships:
             continue # Ignore tables at the main level

        # --- Default Logic for other fields (or Links/Tables not handled/ignored above) ---
        generic_type = map_field_type(field_type, field_name)
        normalized_label = normalize_string(label) if label else None

        field_node = {
            "key": normalized_label if normalized_label else field_name, # Key continues to use the normalized description
            "description": label if label else field_name, # Description uses the original label (or field_name)
            "fieldname": field_name, # New fieldname property
            "type": generic_type
        }
        
        processed_nodes.append(field_node)

    return processed_nodes

def add_paths_recursively(node, current_path=""):
    """
    Adiciona recursivamente a propriedade 'path' a cada nó na hierarquia.

    Args:
        node (dict): O nó atual a ser processado.
        current_path (str): O caminho acumulado até o nó pai.
    """
    if not isinstance(node, dict):
        return

    node_key = node.get("key")
    if not node_key:
        # Não é possível determinar o caminho sem uma chave
        return

    # Calcula o novo caminho para este nó
    new_path = f"{current_path}.{node_key}" if current_path else node_key
    # Adiciona o path apenas se não for um nó raiz (current_path existe)
    if current_path:
        node["path"] = new_path

    node["dragandrop"] = True # Adiciona a propriedade drag and drop

    # Processa os filhos recursivamente
    children = node.get("children")
    if isinstance(children, list):
        node["dragandrop"] = False
        node["path"] = new_path
        for child in children:
            add_paths_recursively(child, new_path)
            
def create_hierarchical_doctype_structure(doctypes_with_fields, child_parent_mapping):
    """
    Creates a hierarchical JSON structure of DocTypes and their fields (Refactored v2).

    Uses process_fields_for_hierarchy with controlled recursion.

    Args:
        doctypes_with_fields (dict): Dictionary {doctype_name: fields_metadata_list}.
        child_parent_mapping (list): List of dicts {"child": child_name, "parent": parent_name}.

    Returns:
        dict: Dictionary containing the root DocType nodes, with nested children (fields and DocTypes).
              Returns empty entities list in case of error in the main inputs.
    """
    visited_nodes = set()  # Initialize the set of visited nodes
    if visited_nodes is None:
        visited_nodes = set()  # Initialize the set of visited nodes if not provided
    
    if child_parent_mapping is None:
        child_parent_mapping = []

    nodes = {}
    child_doctypes = set()

    all_doctype_names = list(doctypes_with_fields.keys()) # For safe iteration if we modify the dict
    for doctype_name in all_doctype_names:
        if not doctype_name: 
            continue
        fields_metadata = doctypes_with_fields.get(doctype_name, [])

        if doctype_name not in nodes:
            normalized_description = normalize_string(doctype_name)
            nodes[doctype_name] = {
                "key": normalized_description, # Key continues to use the normalized description
                "description": doctype_name, # Description uses the original doctype name
                "fieldname": doctype_name, # New fieldname property
                "type": "doctype",
                "children": process_fields_for_hierarchy(fields_metadata, doctypes_with_fields, True)
            }
        else:
             # If the node already exists (created by mapping), process and add/update the fields
             current_children = nodes[doctype_name].get("children", [])
             processed_fields = process_fields_for_hierarchy(fields_metadata, doctypes_with_fields, True)
             # Avoid duplicating fields if the DocType is processed multiple times (unlikely, but safe)
             existing_field_keys = {child.get("key") for child in current_children if child.get("type") != "doctype"}
             for field_node in processed_fields:
                 if field_node.get("key") not in existing_field_keys:
                     current_children.append(field_node)
             nodes[doctype_name]["children"] = current_children


    # Process parent-child mapping to nest DocTypes ---
    # Ensure the relationships exist:
    # - Contract -> Contract Item
    # - Contract -> Contract Measurement
    # - Contract -> Contract Measurement Record
    specific_mappings = specific_mapping.get_specific_mapping()

    for mapping in specific_mappings:
        mapping_exists = any(
            m.get("child") == mapping["child"] and m.get("parent") == mapping["parent"]
            for m in child_parent_mapping if isinstance(m, dict)
        )
        if not mapping_exists:
            print(f"Info: Adding specific mapping {mapping}...")
            child_parent_mapping.append(mapping) # Directly modifies the list (or a copy if you prefer immutability)

    # Continue processing the mappings (including the added one, if applicable)
    for mapping in child_parent_mapping:
        if not isinstance(mapping, dict): continue

        child_name = mapping.get("child")
        parent_name = mapping.get("parent")        

        if not child_name or not parent_name:
            continue

        # Ensure parent and child nodes exist
        for name in [parent_name, child_name]:
            if name not in nodes:
                node_fields_metadata = doctypes_with_fields.get(name, [])
                normalized_description = normalize_string(name)
                nodes[name] = {
                    "key": normalized_description, # Key continues to use the normalized description
                    "description": name, # Description uses the original doctype/field name
                    "fieldname": name, # New fieldname property
                    "type": "doctype",
                    "children": process_fields_for_hierarchy(node_fields_metadata, doctypes_with_fields, True)
                }

        # Only if both nodes actually exist (were found or created)
        if parent_name in nodes and child_name in nodes:
            child_node_ref = nodes[child_name]
            if child_node_ref.get("name") in visited_nodes:
                continue
            parent_node_children = nodes[parent_name]["children"]

            is_already_child = any(child is child_node_ref for child in parent_node_children if isinstance(child, dict) and child.get("type") == "doctype")

            if not is_already_child:
                parent_node_children.append(child_node_ref)

            child_doctypes.add(child_name)

    for node in nodes.values():
        print(f"Info: Processing node '{node.get('description')}'...")
        # Check if it's a doctype node and has the 'children' key
        if isinstance(node, dict) and node.get("type") == "doctype" and "children" in node:
            children_list = node["children"]
            if isinstance(children_list, list):
                # Sort the 'children' list in-place
                # Sort key: 0 for fields (not doctype), 1 for doctypes
                children_list.sort(key=lambda child: 0 if isinstance(child, dict) and child.get("type") != "doctype" else 1)

    # Identify and collect root nodes
    root_nodes = []
    all_processed_doctypes = list(nodes.keys())

    for doctype_name in all_processed_doctypes:
        if doctype_name not in child_doctypes: # If not a child of anyone, it's a root
             root_nodes.append(nodes[doctype_name])

    # Add the 'path' property recursively 
    print("Info: Adding paths to root nodes...")
    print(f"Info: Found {len(root_nodes)} root nodes.")
    for root_node in root_nodes:
        print(f"Info: Adding path to root node '{root_node.get('description')}'...")
        add_paths_recursively(root_node) # Start recursion for each root

    return {"entities": root_nodes}
