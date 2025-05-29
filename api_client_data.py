"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

API Client Data module for fetching entity data from the Arteris API.
This module provides functions to retrieve entity keys and data from the Arteris API.
"""

import requests
import json

def get_keys(api_base_url, api_token, doctype_name, filters=None):
    """
    Fetches the keys of a specific DocType from the Arteris API.
    
    Args:
        api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
        api_token (str): The authorization token in the format 'token key:secret'.
        doctype_name (str): The name of the DocType to fetch keys from (e.g., 'Asset').
        
    Returns:
        list or None: A list of strings containing the key values of the DocType.
                      Returns None in case of an error in the request or JSON decoding.
    """
    resource_url = f"{api_base_url}/{doctype_name}"
    if filters:
        resource_url=f"{resource_url}?filters={filters}"
    
    params = {}
    headers = {"Authorization": api_token}

    try:
        response = requests.get(resource_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        keys = [item["name"] for item in data.get("data", [])]
        print("CHAVES", keys)
        # Returns the list of keys from the 'data' key of the JSON response
        return keys
    except requests.exceptions.RequestException as e:
        # Captures connection errors, timeouts, etc.
        return None
    except json.JSONDecodeError:
        # Captures error if the response is not valid JSON
        return None

def remove_properties_recursively(data, properties_to_remove):
    """
    Recursively removes specified properties from a JSON object.
    
    Args:
        data: The JSON object from which to remove properties.
        properties_to_remove: List of properties to be removed.
        
    Returns:
        The JSON object with the properties removed.
    """
    if isinstance(data, dict):
        # Removes properties from the current dictionary
        for prop in properties_to_remove:
            if prop in data:
                del data[prop]
        
        # Recursively processes all dictionary values
        for key, value in list(data.items()):
            data[key] = remove_properties_recursively(value, properties_to_remove)
            
    elif isinstance(data, list):
        # Recursively processes all list items
        for i, item in enumerate(data):
            data[i] = remove_properties_recursively(item, properties_to_remove)
            
    return data

def get_data_from_key(api_base_url, api_token, doctype_name, key):
    """
    Fetches data for a specific DocType from the Arteris API using a key.
    
    Args:
        api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
        api_token (str): The authorization token in the format 'token key:secret'.
        doctype_name (str): The name of the DocType to fetch data from (e.g., 'Asset').
        key (str): The key of the DocType to fetch data for.
        
    Returns:
        A JSON object containing the DocType data or None in case of error.
        The following properties are removed from the returned JSON (including in nested objects):
        'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx'
    """
    resource_url = f"{api_base_url}/{doctype_name}/{key}"
    print("URLLL", resource_url)
    params = {}
    headers = {"Authorization": api_token}

    try:
        print(f"Fetching data for DocType '{doctype_name}' using key '{key}' at: {resource_url} ...")
        response = requests.get(resource_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        # Checks if the response contains data
        if "data" in data:
            print(f"Data for '{doctype_name}' with key '{key}' received successfully!")
            
            # Removes the specified properties recursively
            data_filtered = data["data"]
            properties_to_remove = [] #['owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parentfield', 'parenttype', 'is_group']
            
            # Applies recursive property removal
            data_filtered = remove_properties_recursively(data_filtered, properties_to_remove)
            
            return data_filtered
        else:
            print(f"No data found for '{doctype_name}' with key '{key}'!")
            return None
    except requests.exceptions.RequestException as e:
        # Captures connection errors, timeouts, etc.
        print(f"Error fetching keys for {doctype_name}: {e}")
        return None
    except json.JSONDecodeError:
        # Captures error if the response is not valid JSON
        print(f"Error decoding keys JSON response for {doctype_name}.")
        return None    