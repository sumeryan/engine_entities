"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

DocTypes Processing Module.
This module handles the retrieval and processing of DocTypes and their fields from the Arteris API.
It provides functionality to build a hierarchical structure of DocTypes.
"""

import api_client 
import os
import json_to_hierarquical
import api_client_data

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

    parents_mapping = get_parent_mapping(all_doctypes)

    return {
        "main_doctypes": main_doctypes,
        "child_doctypes": child_doctypes,
        "all_doctypes": all_doctypes,
        "parents_mapping": parents_mapping
    }

def get_hierarchical_doctype_structure():
    """"
    Gets the hierarchical structure of DocTypes.
    
    Returns:
        dict: A JSON dictionary with the hierarchical structure.
    """

    print("\n--- Starting Internal Generation V2 ---")

    doctypes = process_doctypes() 

    print("\n--- Creating hierarchical structure ---")
    hierarquical_json = json_to_hierarquical.create_hierarchical_doctype_structure(
        doctypes["all_doctypes"],
        doctypes["parents_mapping"]
    )
    return hierarquical_json

def get_data():
    """
    Retrieves data from the framework.
    
    Returns:
        list: A list of dictionaries containing DocType data.
    """

    doctypes = process_doctypes() 

    # Get the base URL and token from environment variables
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    # Get DocType IDs
    doctypes_with_keys = []
    for doctype in doctypes["main_doctypes"]:
        doctype_name = doctype.get("name")
        if doctype_name:
            keys = api_client.get_keys(api_base_url, api_token, doctype_name)
            doctypes_with_keys.append({"doctype": doctype_name, "keys": keys})


    # Get list of DocType data
    all_doctype_data = []
    for doctype in doctypes_with_keys:
        doctype_name = doctype.get("doctype")
        keys = doctype.get("keys")
        if keys:
            for key in keys:
                data = api_client_data.get_data_from_key(api_base_url, api_token, doctype_name, key)
                if data:
                    all_doctype_data.append({"doctype": doctype_name, "key": key, "data": data})

    return all_doctype_data