"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

API Client module for interacting with the Arteris API.
This module provides functions to fetch DocTypes and their fields from the Arteris API.
"""

import requests
import json

def get_arteris_doctypes(api_base_url, api_token):
    """
    Fetches all DocTypes from the Arteris API that belong to the 'Arteris' module and are not Child Items.

    Args:
        api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
        api_token (str): The authorization token in the format 'token key:secret'.

    Returns:
        list or None: A list of dictionaries, where each dictionary represents a DocType
                      found (containing at least the 'name' key).
                      Returns None in case of an error in the request or JSON decoding.
    """
    doctype_url = f"{api_base_url}/DocType"
    params = {
        # Filter to fetch only DocTypes from the specific 'Arteris' module that are not tables (Child Item)
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"],["name","like","%Meas%"]])
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"],["name","=","Asset"]])
        "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"]])
    }
    headers = {"Authorization": api_token}

    try:
        print(f"Fetching DocTypes...")
        response = requests.get(doctype_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        print("DocTypes list received successfully!")
        # Returns directly the list contained in the 'data' key of the JSON response
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captures connection errors, timeouts, etc.
        print(f"Error fetching DocTypes from API: {e}")
        return None
    except json.JSONDecodeError:
        # Captures error if the response is not valid JSON
        print("Error decoding DocTypes JSON response.")
        return None
    
def get_arteris_doctypes_child(api_base_url, api_token):
    """
    Fetches all DocTypes from the Arteris API that belong to the 'Arteris' module and are Child Items.

    Args:
        api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
        api_token (str): The authorization token in the format 'token key:secret'.

    Returns:
        list or None: A list of dictionaries, where each dictionary represents a DocType
                      found (containing at least the 'name' key).
                      Returns None in case of an error in the request or JSON decoding.
    """

    doctype_url = f"{api_base_url}/DocType"
    params = {
        # Filter to fetch only DocTypes from the specific 'Arteris' module that are tables (Child Item)
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"],["name","like","%Meas%"]])
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"],["name","=","Asset Operator"]])
        "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"]])
    }
    headers = {"Authorization": api_token}

    try:
        print(f"Fetching DocTypes...")
        response = requests.get(doctype_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        print("DocTypes list received successfully!")
        # Returns directly the list contained in the 'data' key of the JSON response
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captures connection errors, timeouts, etc.
        print(f"Error fetching DocTypes from API: {e}")
        return None
    except json.JSONDecodeError:
        # Captures error if the response is not valid JSON
        print("Error decoding DocTypes JSON response.")
        return None    

def get_docfields_for_doctype(api_base_url, api_token, doctype_name, child=False):
    """
    Fetches DocFields (field metadata) for a specific DocType.

    Filters to exclude fields of type 'Section Break' and 'Column Break' and
    selects only 'fieldname', 'label', and 'fieldtype'.

    Args:
        api_base_url (str): The base URL of the resource API.
        api_token (str): The authorization token.
        doctype_name (str): The name of the DocType for which to fetch fields.
        child (bool, optional): Indicates if the DocType is a Child Item. Defaults to False.

    Returns:
        list or None: A list of dictionaries, where each dictionary represents a DocField
                      (containing 'fieldname', 'label', 'fieldtype').
                      Returns None in case of an error in the request or JSON decoding.
                      Returns an empty list if no fields are found after filtering.
    """

    docfield_url = f"{api_base_url}/DocField"
    params = {
        # Define which DocField fields we want to return
        # If child=True adds "parent" to fields
        "fields": json.dumps(["fieldname", "label", "fieldtype", "options", "hidden"] + (["parent"] if child else [])),
        # Define filters:
        "filters": json.dumps([
            ["parent", "=", doctype_name],        # Field belongs to the specified parent DocType
            ["fieldtype", "!=", "Section Break"], # Excludes section breaks
            ["fieldtype", "!=", "Column Break"],  # Excludes column breaks
            ["fieldtype", "!=", "Tab Break"]      # Excludes tab breaks
        ]),
        # 'parent' parameter seems to be necessary for the DocField API,
        # even though we're already filtering by 'parent' in 'filters'.
        "parent": "DocType"
    }
            
    headers = {"Authorization": api_token}

    try:
        print(f"Fetching DocFields for: {doctype_name}...")
        response = requests.get(docfield_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        docfields = data.get("data", [])
        print(f"DocFields for {doctype_name} received successfully!")
        # Returns the list of fields from the 'data' key
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captures connection errors, timeouts, etc.
        print(f"Error fetching DocFields for {doctype_name}: {e}")
        return None
    except json.JSONDecodeError:
        # Captures error if the response is not valid JSON
        print(f"Error decoding DocFields JSON response for {doctype_name}.")
        return None