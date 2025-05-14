import json
import dcotyp_translate
import mappings
import os

def load_json_file(file_path):
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    """Save JSON data to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def build_tree(all_doctypes):
    """Main function to build the hierarchical tree structure"""

    specified_mapping = mappings.get_specific_mapping();
    translations = dcotyp_translate.get_translations()
    
    # Create hierarchical structure
    hierarchical_data = {"entities": []}
    
    # Create dictionaries for mandatory mappings from specified_mapping.json
    # This will override any option-based relationships
    mandatory_children = {}  # parent -> [children]
    mandatory_parents = {}   # child -> [parents]
    
    for mapping in specified_mapping:
        child = mapping["child"]
        parent = mapping["parent"]
        
        # Add to mandatory parents lookup
        if child not in mandatory_parents:
            mandatory_parents[child] = []
        mandatory_parents[child].append(parent)
        
        # Add to mandatory children lookup
        if parent not in mandatory_children:
            mandatory_children[parent] = []
        mandatory_children[parent].append(child)
    
    # Track which doctypes have been processed to avoid duplication
    processed_doctypes = set()
    
    # First, process doctypes that don't have mandatory parents
    # (they're either root nodes or will be added via options)
    for doctype_name in all_doctypes["all_doctypes"].keys():
        if doctype_name not in mandatory_parents and doctype_name not in processed_doctypes:
            entity = create_doctype_entity(
                doctype_name, 
                all_doctypes, 
                mandatory_parents, 
                mandatory_children,
                processed_doctypes,
                translations
            )
            hierarchical_data["entities"].append(entity)
    
    # Process any remaining doctypes that haven't been added yet
    for doctype_name in all_doctypes["all_doctypes"].keys():
        if doctype_name not in processed_doctypes:
            entity = create_doctype_entity(
                doctype_name, 
                all_doctypes, 
                mandatory_parents, 
                mandatory_children,
                processed_doctypes,
                translations
            )
            hierarchical_data["entities"].append(entity)
    
    # Apply mandatory mappings as the final step to ensure they take precedence
    apply_specified_mappings(hierarchical_data, specified_mapping, translations)

    update_all_paths(hierarchical_data)
    
    return hierarchical_data["entities"]

def create_doctype_entity(doctype_name, doctypes_data, mandatory_parents, mandatory_children, processed_doctypes, translations=None):
    """Create entity for a doctype including its fields and child doctypes"""
    # Mark this doctype as processed
    processed_doctypes.add(doctype_name)
    
    # Get the translated name if available
    doctype_key = doctype_name.replace(" ", "_")
    translated_name = translations.get(doctype_key, doctype_name) if translations else doctype_name
    
    # Create doctype entity with temporary path (will be properly set later)
    doctype_entity = {
        "key": doctype_key,
        "description": translated_name,
        "fieldname": doctype_name,
        "fieldname_data": "",
        "type": "doctype",
        "path": normalize_string(translated_name),  # Temporary path
        "dragandrop": False,
        "children": []
    }
    
    # First add all regular fields
    if doctype_name in doctypes_data["all_doctypes"]:
        for field in doctypes_data["all_doctypes"][doctype_name]:
            # Skip relationship fields for now, we'll handle them separately
            if field.get("options") is None or field.get("fieldtype") != "Table":
                field_type = map_field_type(field.get("fieldtype", ""))
                field_key = field.get("label", "").replace(" ", "_")
                
                field_entity = {
                    "key": field_key,
                    "description": field.get("label", ""),
                    "fieldname": field.get("fieldname", ""),
                    "fieldname_data": field.get("fieldname_data", ""),
                    "type": field_type,
                    "path": normalize_string(field.get('label', '')),  # Temporary path
                    "dragandrop": True,
                    "children": []
                }
                
                doctype_entity["children"].append(field_entity)
    
    # Now handle mandatory children based on specified_mapping.json
    if doctype_name in mandatory_children:
        for child_doctype in mandatory_children[doctype_name]:
            child_key = child_doctype.replace(" ", "_")
            
            # Skip if this child has already been added to this parent
            if any(child["key"] == child_key for child in doctype_entity["children"]):
                continue
                
            # Skip if this child doesn't exist in the doctypes data
            if child_doctype not in doctypes_data["all_doctypes"]:
                continue
            
            # Mark this child as processed
            processed_doctypes.add(child_doctype)
            
            # Get the translated name if available
            child_translated_name = translations.get(child_key, child_doctype) if translations else child_doctype
            
            # Create the child entity with temporary path
            child_entity = {
                "key": child_key,
                "description": child_translated_name,
                "fieldname": child_doctype,
                "fieldname_data": "",
                "type": "doctype",
                "path": normalize_string(child_translated_name),  # Temporary path
                "dragandrop": False,
                "children": []
            }
            
            # Process the child's fields
            process_doctype_fields(
                child_entity, 
                child_doctype, 
                doctypes_data, 
                normalize_string(child_translated_name),  # Temporary path
                mandatory_parents, 
                mandatory_children,
                processed_doctypes,
                translations
            )
            
            doctype_entity["children"].append(child_entity)
    
    # Now handle relationships based on options, but only if they aren't in mandatory relationships
    if doctype_name in doctypes_data["all_doctypes"]:
        for field in doctypes_data["all_doctypes"][doctype_name]:
            if field.get("options") is not None and field.get("fieldtype") == "Table":
                related_doctype = field.get("options")
                related_key = related_doctype.replace(" ", "_")
                
                # Skip if this related doctype doesn't exist
                if related_doctype not in doctypes_data["all_doctypes"]:
                    continue
                
                # Skip if this child already exists as a mandatory child (from specified_mapping)
                if (doctype_name in mandatory_children and 
                    related_doctype in mandatory_children[doctype_name]):
                    continue
                
                # Skip if this doctype has mandatory parents and current doctype is not one of them
                if (related_doctype in mandatory_parents and 
                    doctype_name not in mandatory_parents[related_doctype]):
                    continue
                
                # Mark this related doctype as processed
                processed_doctypes.add(related_doctype)
                
                # Get the translated name if available
                related_translated_name = translations.get(related_key, related_doctype) if translations else related_doctype
                
                # Create the child entity with temporary path
                child_entity = {
                    "key": related_key,
                    "description": related_translated_name,
                    "fieldname": related_doctype,
                    "fieldname_data": field.get("fieldname"),
                    "type": "doctype",
                    "path": normalize_string(related_translated_name),  # Temporary path
                    "dragandrop": False,
                    "children": []
                }
                
                # Process the child's fields
                process_doctype_fields(
                    child_entity, 
                    related_doctype, 
                    doctypes_data, 
                    normalize_string(related_translated_name),  # Temporary path
                    mandatory_parents, 
                    mandatory_children, 
                    processed_doctypes,
                    translations
                )
                
                doctype_entity["children"].append(child_entity)
    
    return doctype_entity

def process_doctype_fields(entity, doctype_name, doctypes_data, base_path, 
                          mandatory_parents, mandatory_children, processed_doctypes, translations=None):
    """Process all fields of a doctype recursively"""
    if doctype_name not in doctypes_data["all_doctypes"]:
        return
    
    # First add all regular fields
    for field in doctypes_data["all_doctypes"][doctype_name]:
        # Skip relationship fields for now, we'll handle them separately
        if field.get("options") is None or field.get("fieldtype") != "Table":
            field_type = map_field_type(field.get("fieldtype", ""))
            field_key = field.get("label", "").replace(" ", "_")
            
            field_entity = {
                "key": field_key,
                "description": field.get("label", ""),
                "fieldname": field.get("fieldname", ""),
                "fieldname_data": field.get("fieldname_data", ""),
                "type": field_type,
                "path": normalize_string(field.get('label', '')),  # Temporary path
                "dragandrop": True,
                "children": []
            }
            
            entity["children"].append(field_entity)
    
    # Now handle mandatory children based on specified_mapping.json
    if doctype_name in mandatory_children:
        for child_doctype in mandatory_children[doctype_name]:
            child_key = child_doctype.replace(" ", "_")
            
            # Skip if this child has already been added to this parent
            if any(child["key"] == child_key for child in entity["children"]):
                continue
                
            # Skip if this child doesn't exist in the doctypes data
            if child_doctype not in doctypes_data["all_doctypes"]:
                continue
            
            # Mark this child as processed
            processed_doctypes.add(child_doctype)
            
            # Get the translated name if available
            child_translated_name = translations.get(child_key, child_doctype) if translations else child_doctype
            
            # Create the child entity with temporary path
            child_entity = {
                "key": child_key,
                "description": child_translated_name,
                "fieldname": child_doctype,
                "fieldname_data": field.get("fieldname_data", ""),
                "type": "doctype",
                "path": normalize_string(child_translated_name),  # Temporary path
                "dragandrop": False,
                "children": []
            }
            
            # Process the child's fields
            process_doctype_fields(
                child_entity, 
                child_doctype, 
                doctypes_data, 
                normalize_string(child_translated_name),  # Temporary path
                mandatory_parents, 
                mandatory_children,
                processed_doctypes,
                translations
            )
            
            entity["children"].append(child_entity)
    
    # Now handle relationships based on options, but only if they aren't in mandatory relationships
    for field in doctypes_data["all_doctypes"][doctype_name]:
        if field.get("options") is not None and field.get("fieldtype") == "Table":
            related_doctype = field.get("options")
            related_key = related_doctype.replace(" ", "_")
            
            # Skip if this related doctype doesn't exist
            if related_doctype not in doctypes_data["all_doctypes"]:
                continue
            
            # Skip if this child already exists as a mandatory child (from specified_mapping)
            if (doctype_name in mandatory_children and 
                related_doctype in mandatory_children[doctype_name]):
                continue
            
            # Skip if this doctype has mandatory parents and current doctype is not one of them
            if (related_doctype in mandatory_parents and 
                doctype_name not in mandatory_parents[related_doctype]):
                continue
            
            # Skip if this child has already been added to this parent
            if any(child["key"] == related_key for child in entity["children"]):
                continue
            
            # Mark this related doctype as processed
            processed_doctypes.add(related_doctype)
            
            # Get the translated name if available
            related_translated_name = translations.get(related_key, related_doctype) if translations else related_doctype
            
            # Create the child entity with temporary path
            child_entity = {
                "key": related_key,
                "description": related_translated_name,
                "fieldname": related_doctype,
                "fieldname_data": field.get("fieldname_data", ""),
                "type": "doctype",
                "path": normalize_string(related_translated_name),  # Temporary path
                "dragandrop": False,
                "children": []
            }
            
            # Process the child's fields
            process_doctype_fields(
                child_entity, 
                related_doctype, 
                doctypes_data, 
                normalize_string(related_translated_name),  # Temporary path
                mandatory_parents, 
                mandatory_children, 
                processed_doctypes,
                translations
            )
            
            entity["children"].append(child_entity)

def map_field_type(fieldtype):
    """Map field types from doctypes to hierarchical model types"""
    type_mapping = {
        "Data": "string",
        "Date": "date",
        "Datetime": "datetime",
        "Int": "numeric",
        "Float": "numeric",
        "Currency": "numeric",
        "Check": "boolean",
        "Select": "select",
        "Long Text": "text",
        "Small Text": "text",
        "Text": "text",
        "Text Editor": "text",
        "Table": "doctype"  # Table represents a child doctype
    }
    
    return type_mapping.get(fieldtype, "string")  # Default to string if not found

def find_entity_by_key(entities, key):
    """Find an entity by its key in the hierarchical data"""
    for entity in entities:
        if entity["key"] == key:
            return entity
        
        # Check children recursively
        for child in entity.get("children", []):
            result = find_entity_in_children(child, key)
            if result:
                return result
    
    return None

def find_entity_in_children(entity, key):
    """Recursively search for an entity by key in children"""
    if entity["key"] == key:
        return entity
    
    for child in entity.get("children", []):
        result = find_entity_in_children(child, key)
        if result:
            return result
    
    return None

def apply_specified_mappings(hierarchical_data, specified_mapping, translations=None):
    """Apply specified parent-child mapping rules with priority over other relationships"""
    # Build mapping dictionaries for faster lookups
    child_to_parent_map = {}
    for mapping in specified_mapping:
        child = mapping["child"]
        parent = mapping["parent"]
        child_to_parent_map[child] = parent

    # First pass: Apply specified mappings at the root level
    # First, remove any children that have mandatory parents but are not under the right parent
    for mapping in specified_mapping:
        child_key = mapping["child"].replace(" ", "_")
        parent_key = mapping["parent"].replace(" ", "_")

        # Remove this child from any non-specified parent in the hierarchical_data
        for entity in hierarchical_data["entities"]:
            if entity["key"] != parent_key:  # Skip the actual parent
                # Remove the child from this entity's children if it exists
                entity["children"] = [child for child in entity["children"]
                                     if child["key"] != child_key]

                # Also check nested levels and remove the child if found
                remove_entity_from_children(entity["children"], child_key)

    # Now add the children to their correct parents according to specified_mapping
    for mapping in specified_mapping:
        child_key = mapping["child"].replace(" ", "_")
        parent_key = mapping["parent"].replace(" ", "_")

        # Find the parent and child entities
        parent_entity = find_entity_by_key(hierarchical_data["entities"], parent_key)
        child_entity = find_entity_by_key(hierarchical_data["entities"], child_key)

        # If both parent and child are found, make child a child of parent
        if parent_entity and child_entity:
            # Check if child already exists in parent's children
            child_exists = False
            for existing_child in parent_entity["children"]:
                if existing_child["key"] == child_key:
                    child_exists = True
                    break

            # If child doesn't exist in parent's children, add it
            if not child_exists:
                # Get the translated name if available
                child_translated_name = translations.get(child_key, mapping["child"]) if translations else mapping["child"]

                # Create a copy of the child entity and update its description
                child_copy = child_entity.copy()
                child_copy["description"] = child_translated_name

                # Temporary path (will be updated later)
                child_copy["path"] = normalize_string(child_translated_name)

                # Add the child to the parent's children
                parent_entity["children"].append(child_copy)

    # Second pass: Recursively enforce mappings for all levels of the hierarchy
    for entity in hierarchical_data["entities"]:
        enforce_specified_mappings_recursive(entity, specified_mapping, child_to_parent_map, translations)

    # Remove any root-level entities that should only be children based on specified_mapping
    children_to_remove = {mapping["child"].replace(" ", "_") for mapping in specified_mapping}
    hierarchical_data["entities"] = [entity for entity in hierarchical_data["entities"]
                                    if entity["key"] not in children_to_remove]

def enforce_specified_mappings_recursive(entity, specified_mapping, child_to_parent_map, translations=None):
    """
    Recursively enforce specified mappings at all levels of the hierarchy.
    This ensures that child entities respect their parent relationships at any depth.
    """
    if not entity.get("children"):
        return

    # Create a mapping of child fieldnames to their corresponding entity keys for faster lookup
    child_fieldname_to_key = {}
    for child in entity.get("children", []):
        if "fieldname" in child:
            child_fieldname_to_key[child["fieldname"]] = child["key"]

    # Check each child entity to see if it has children that should be remapped
    for child in entity.get("children", []):
        # Process each grandchild to see if it has a specific mapping
        grandchildren_to_move = []

        for i, grandchild in enumerate(child.get("children", [])):
            if "fieldname" not in grandchild:
                continue

            grandchild_name = grandchild["fieldname"]

            # If this grandchild has a specific parent mapping
            if grandchild_name in child_to_parent_map:
                # Get the proper parent for this grandchild
                proper_parent_name = child_to_parent_map[grandchild_name]
                proper_parent_key = proper_parent_name.replace(" ", "_")

                # If the current child is not the proper parent
                if child["fieldname"] != proper_parent_name:
                    # Find the proper parent entity within the current children
                    for potential_parent in entity.get("children", []):
                        if potential_parent.get("fieldname") == proper_parent_name:
                            # Mark this grandchild for moving to the proper parent
                            grandchildren_to_move.append((i, grandchild, potential_parent))
                            break

        # Now move the grandchildren to their proper parents
        # We process them in reverse order to avoid index shifting issues when removing
        for i, grandchild, proper_parent in sorted(grandchildren_to_move, reverse=True):
            # Check if the grandchild already exists in the proper parent
            exists = False
            for existing in proper_parent.get("children", []):
                if existing["key"] == grandchild["key"]:
                    exists = True
                    break

            if not exists:
                # Add to proper parent
                proper_parent.setdefault("children", []).append(grandchild)

            # Remove from current child
            if i < len(child.get("children", [])):
                child["children"].pop(i)

        # Recursively apply to this child's children
        enforce_specified_mappings_recursive(child, specified_mapping, child_to_parent_map, translations)

def remove_entity_from_children(children, key_to_remove):
    """Recursively remove entity with given key from children at any level"""
    if not children:
        return
    
    # Filter out the key_to_remove from each child's children
    for child in children:
        child["children"] = [c for c in child["children"] if c["key"] != key_to_remove]
        # Recursively check deeper levels
        remove_entity_from_children(child["children"], key_to_remove)

def normalize_string(s):
    """Normalize string for path usage by removing special characters and standardizing format"""
    if not s:
        return ""
    
    # Replace accented characters with non-accented equivalents
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    
    # Replace spaces and special characters with underscores
    import re
    s = re.sub(r'[^a-zA-Z0-9_]', '_', s)
    
    # Replace multiple underscores with single underscore
    s = re.sub(r'_{2,}', '_', s)
    
    # Remove leading and trailing underscores
    s = s.strip('_')
    
    # Convert to lowercase for consistency
    s = s.lower()
    
    return s

def update_all_paths(hierarchical_data):
    """Update all paths in the hierarchy to have the full parent-child chain"""
    # First update paths for root entities
    entities = hierarchical_data["entities"]
    for entity in entities:
        entity_path = normalize_string(entity["description"])
        entity["path"] = entity_path
        
        # Now recursively update all children paths
        update_child_paths(entity, entity_path)

def update_child_paths(parent_entity, parent_path):
    """Update all children paths to include the full parent-child chain"""
    for child in parent_entity.get("children", []):
        child_path = normalize_string(child["description"])
        child["path"] = f"{parent_path}.{child_path}"
        
        # Recursively update all descendants
        update_child_paths(child, child["path"])

def main():

    all_doctypes = load_json_file("output/all_doctypes.json")

    # Build the hierarchical tree
    hierarchical_data = build_tree(all_doctypes)
    
    # Update all paths to have the full parent-child hierarchy
    # update_all_paths(hierarchical_data)
    
    # Save the final result
    
    # Gravar all_doctypes em um arquivo JSON
    with open("output/hierarchical_data.json", "w", encoding="utf-8") as f:
        json.dump(hierarchical_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()