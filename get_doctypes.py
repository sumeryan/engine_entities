"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

DocTypes Processing Module.
This module handles the retrieval and processing of DocTypes and their fields from the Arteris API.
It provides functionality to build a hierarchical structure of DocTypes.
"""

import api_client 
import os
import api_client_data
import json
import mappings
import engine_hierarquical_tree.hierarchical_tree

def get_main_doctypes_with_fields(api_base_url, api_token): 
    """
    Retrieves main DocTypes and their fields.
    
    Args:
        api_base_url (str): The base URL of the Arteris API.
        api_token (str): The API token for authentication.
        
    Returns:
        dict or None: A dictionary mapping DocType names to their fields,
                      or None if the retrieval fails.
    """

    doctypes_with_fields = {} 

    # Fetch main DocTypes
    all_doctypes = api_client.get_arteris_doctypes(api_base_url, api_token)
    if all_doctypes is None:
        return None # Return None to indicate failure

    # Fetch DocFields for each DocType
    for doc in all_doctypes:
        doctype_name = doc.get("name")
        docfields = api_client.get_docfields_for_doctype(api_base_url, api_token, doctype_name)
        if docfields is not None:
            doctypes_with_fields[doctype_name] = docfields
        else:
            doctypes_with_fields[doctype_name] = None # Mark error

    return doctypes_with_fields

def get_child_doctypes_with_fields(api_base_url, api_token): 
    """
    Retrieves child DocTypes and their fields.
    
    Args:
        api_base_url (str): The base URL of the Arteris API.
        api_token (str): The API token for authentication.
        
    Returns:
        dict or None: A dictionary mapping child DocType names to their fields,
                      or None if the retrieval fails.
    """

    doctypes_with_fields = {} 

    # Fetch child DocTypes
    all_doctypes_child = api_client.get_arteris_doctypes_child(api_base_url, api_token)
    if all_doctypes_child is None:
        return None # Return None to indicate failure

    # Fetch DocFields for each DocType
    for doc in all_doctypes_child:
        doctype_name = doc.get("name")
        docfields = api_client.get_docfields_for_doctype(api_base_url, api_token, doctype_name, True)
        if docfields is not None:
            doctypes_with_fields[doctype_name] = docfields
        else:
            doctypes_with_fields[doctype_name] = None # Mark error

    return doctypes_with_fields

def get_parent_mapping(doctypes_with_fields):
    """
    Maps child DocTypes to their respective parent DocTypes.
    
    Args:
        doctypes_with_fields (dict): Dictionary mapping DocType names to their fields.
        
    Returns:
        list: A list of dictionaries, each containing 'child', 'parent', and 'type' keys
              to define the relationship between DocTypes.
    """

    child_parent_mapping = [] # List to map child -> parent

    # Iterate over each DocType that can be a "Parent"
    for doctype_name, fields in doctypes_with_fields.items():
        if not fields:
            continue # Not an error, just no table fields

        # Iterate through the 'fields' list of dictionaries
        for f in fields:
            # Check if the item has a fieldname and if the fieldtype is "Table"
            # if (f.get("fieldtype") == "Table" or f.get("fieldtype") == "Link") f.get("fieldname") and f.get("options"): # Circular reference because of link
            if f.get("fieldname") and f.get("fieldtype") == "Table" and f.get("options"):
                child_parent_mapping.append(
                    {
                        "child": f.get("options"),
                        "parent": doctype_name,
                        "type": f.get("fieldtype")
                    }
                )

    return child_parent_mapping

def process_doctypes(): 
    """
    Processes DocTypes and their fields.
    
    Returns:
        dict: A dictionary containing main DocTypes, child DocTypes, all DocTypes,
              and parent-child mapping information.
    """

    # Get the base URL and token from environment variables
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    print("\n--- Starting DocTypes and Fields Mapping ---")
    print(f"Base URL: {api_base_url}")
    print(f"Token: {api_token}")

    # List to store DocTypes and their fields
    main_doctypes = get_main_doctypes_with_fields(api_base_url, api_token)

    # List to store child DocTypes and their fields
    child_doctypes = get_child_doctypes_with_fields(api_base_url, api_token)

    # Union of all DocTypes
    all_doctypes = main_doctypes.copy()
    all_doctypes.update(child_doctypes) # Update the dictionary with child DocTypes

    # remove where in ignore mapping
    ignore_mapping = mappings.get_ignore_mapping()
    for c in list(all_doctypes):
        if c in ignore_mapping:
            del all_doctypes[c]

    parents_mapping = get_parent_mapping(all_doctypes)

    return {
        "main_doctypes": main_doctypes,
        "child_doctypes": child_doctypes,
        "all_doctypes": all_doctypes,
        "parents_mapping": parents_mapping
    }

def get_data():
    """
    Retrieves data from the framework.
    
    Returns:
        list: A list of dictionaries containing DocType data.
    """

    # All doctypes
    all_doctypes = process_doctypes() 

    # Store main DocTypes in a separate dictionary
    # and remove them from the all_doctypes dictionary
    main_doctypes = mappings.get_main_data()

    # Remove main parent and child doctypes from all_doctypes
    for m in main_doctypes:
        m["doctype_with_fields"] = all_doctypes["all_doctypes"][m["doctype"]]
        del all_doctypes["all_doctypes"][m["doctype"]]
        # Move child main DocTypes to main_data_doctypes
        for c in m["childs"]:
            c["doctype_with_fields"] = all_doctypes["all_doctypes"][c["doctype"]]
            del all_doctypes["all_doctypes"][c["doctype"]]

    # Remove all files and folders from data folder
    clear_data("data")

    #---all_doctypes---
    # Get keys for all_doctypes
    all_doctype_data = []
    for d in all_doctypes["all_doctypes"]:
        result = get_doctype_keys_data(d)
        data, keys = result
        all_doctype_data.append({f"{d}": data})

    # ---main_doctypes---
    # Get keys for main_doctypes
    for m in main_doctypes:
        
        # RETORNAR APOS O TESTE DO STEERING
        # result = get_doctype_keys_data(m["doctype"])

        # REMOVER APOS O TESTE DO STEERING
        filter = f"[[\"{m["key"]}\",\"=\",\"{"0196b01a-2163-7cb2-93b9-c8b1342e3a4e"}\"]]"
        name = m["doctype"]
        result = get_doctype_keys_data(name,filter)
        data, keys = result
        all_doctype_data.append({f"{m["doctype"]}": data})

        for k in keys:

            # Create directory with key name in data
            key_dir = os.path.join("data", normalize_string(k))
            if not os.path.exists(key_dir):
                os.makedirs(key_dir)

            # Get keys for child doctype
            for c in m["childs"]:
                result = get_doctype_keys_data(c["doctype"],f"[[\"{c["key"]}\",\"=\",\"{k}\"]]")
                data, keys = result
                # Write data result for child with main key
                save_data(f"data/{normalize_string(k)}", data, c["doctype"])

                # REMOVER ASPOS O TESTE DO STEERING
                all_doctype_data.append({f"{c["doctype"]}": data})

    # Save all_doctype_data
    save_data("data", all_doctype_data, "all_doctypes")

    return all_doctype_data

def get_formula_data():
    result = get_doctype_keys_data("Formula Group")
    data, keys = result
    save_data("data",data, "Formula Group")

def get_doctype_keys_data(doctype_name, filters=None):
    """
    Retrieves keys and data for a specific DocType.
    """
    keys = get_doctype_keys(doctype_name, filters)
    data = get_doctype_data(keys, doctype_name)
    save_data("data", data, doctype_name)    
    return data, keys

def get_doctype_keys(doctype_name, filters=None):
    """
    Retrieves keys for all DocTypes.
    
    Returns:
        list: A list of keys for all DocTypes.
    """

    # Get the base URL and token from environment variables
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    # Get keys for all DocTypes
    keys = api_client_data.get_keys(api_base_url, api_token, doctype_name, filters)

    return keys

def clear_data(path):
    """
    Clears the data directory by removing all files and folders.
    
    Args:
        path (str): The path to the data directory.
    """
    # Remove all files and folders from data folder    
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

def save_data(path, data, filename):
    """
    Saves data to a JSON file.
    
    Args:
        data (list): The data to be saved.
        doctype_name (str): The name of the DocType.
    """
    # Save data to JSON file
    with open(f"{path}/{normalize_string(filename)}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_doctype_data(keys, doctype_name):
    """
    Retrieves data from the framework based on provided keys.
    """

    # Get the base URL and token from environment variables
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    doctype_data = []
    if keys:
        for k in keys:
            data = api_client_data.get_data_from_key(api_base_url, api_token, doctype_name, k)
            doctype_data.append(data)
    return doctype_data

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

def get_hierarchical_doctype_structure():
    """"
    Gets the hierarchical structure of DocTypes.
    
    Returns:
        dict: A JSON dictionary with the hierarchical structure.
    """

    print("\n--- Starting Internal Generation V2 ---")

    doctypes = process_doctypes() 

    all_doctypes={
        "all_doctypes": doctypes["all_doctypes"]
        }



    specific_map = json.loads(json.dumps(mappings.get_specific_mapping()))

    print("\n--- Creating hierarchical structure ---")
    hierarquical_json = engine_hierarquical_tree.hierarchical_tree.build_tree(
        all_doctypes,
        specific_map
    )

    # Gravar tree em um arquivo JSON
    with open("output/hierarquical_doctypes.json", "w", encoding="utf-8") as f:
        json.dump(hierarquical_json, f, indent=4, ensure_ascii=False)

    return hierarquical_json

if __name__ == "__main__":
    get_formula_data()