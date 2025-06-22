"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

API Client module for interacting with the Arteris API.
This module provides functions to fetch DocTypes and their fields from the Arteris API.
"""

from ast import Dict
import os
import requests
import json

class ArterisApi:
    """
    Class for interacting with the Arteris API.
    Provides methods to fetch DocTypes and their fields.
    """

    def __init__(self):
        """
        Initializes the ArterisApi instance with the base URL and API token.

        Args:
            api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
            api_token (str): The authorization token in the format 'token key:secret'.
        """
        self.api_token = os.getenv("ARTERIS_API_TOKEN")
        self.api_base_url = f"{os.getenv('ARTERIS_API_BASE_URL')}/resource"
        self.api_get_keys = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.engine.get_keys"

    def get_arteris_doctypes(self, child: bool = False):
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
        doctype_url = f"{self.api_base_url}/DocType"
        params = {
            "filters": json.dumps([
                ["module", "=", "Arteris"],
                ["istable", "=", "1"] if child else ["istable", "!=", "1"]
            ]),
            "limit_page_length": 0  
        }
        headers = {"Authorization": self.api_token}

        try:
            # print(f"Fetching DocTypes...")
            response = requests.get(doctype_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            # print("DocTypes list received successfully!", data)
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
        
    def get_docfields_for_doctype(self, doctype_name):
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

        docfield_url = f"{self.api_base_url}/DocType/{doctype_name}"
        params = {
            "limit_page_length": 0  
        }
                
        headers = {"Authorization": self.api_token}
        try:
            print(f"Fetching DocFields for: {doctype_name}...")
            response = requests.get(docfield_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            # print("JSON NOVO", data)
            # print(f"DocFields for {doctype_name} received successfully!")
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

    def get_keys_api(self, doctype_name: str, return_field: str, filters: Dict):
        """
        Fetches keys for a specific DocType from the Arteris API based on a filter.

        Args:
            doctype_name (str): The name of the DocType to fetch keys from (e.g., 'Asset').
            filter_name (str): The name of the filter field (e.g., 'status').
            filter_value (str): The value of the filter field (e.g., 'Active').

        Returns:
            list or None: A list of strings containing the key values of the DocType.
                        Returns None in case of an error in the request or JSON decoding.
        """
        resource_url = f"{self.api_get_keys}"
        params = {}
        body = {
            "doctype": doctype_name,
            "filters": filters,
            "return_field": return_field
        }
        headers = {"Authorization": self.api_token}

        try:
            response = requests.get(resource_url, headers=headers, params=params, json=body, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            keys = [k[return_field] for k in data.get("message", [])]
            # print("CHAVES", keys)
            # Returns the list of keys from the 'data' key of the JSON response
            return keys
        except requests.exceptions.RequestException as e:
            # Captures connection errors, timeouts, etc.
            return None
        except json.JSONDecodeError:
            # Captures error if the response is not valid JSON
            return None

    def get_keys(self, doctype_name, filters=None):
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
        resource_url = f"{self.api_base_url}/{doctype_name}"
        if filters:
            resource_url=f"{resource_url}?filters={filters}"
        
        params = {
            "limit_page_length": 0  
        }
        headers = {"Authorization": self.api_token}

        try:
            response = requests.get(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            keys = [item["name"] for item in data.get("data", [])]
            # print("CHAVES", keys)
            # Returns the list of keys from the 'data' key of the JSON response
            return keys
        except requests.exceptions.RequestException as e:
            # Captures connection errors, timeouts, etc.
            return None
        except json.JSONDecodeError:
            # Captures error if the response is not valid JSON
            return None

    def remove_properties_recursively(self, data, properties_to_remove):
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
                data[key] = self.remove_properties_recursively(value, properties_to_remove)
                
        elif isinstance(data, list):
            # Recursively processes all list items
            for i, item in enumerate(data):
                data[i] = self.remove_properties_recursively(item, properties_to_remove)
                
        return data

    def get_data_from_key(self, doctype_name, key):
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
        resource_url = f"{self.api_base_url}/{doctype_name}/{key}"
        # print("URL", resource_url)
        params = {
            "limit_page_length": 0  
        }
        headers = {"Authorization": self.api_token}

        try:
            # print(f"Fetching data for DocType '{doctype_name}' using key '{key}' at: {resource_url} ...")
            response = requests.get(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            # Checks if the response contains data
            if "data" in data:
                # print(f"Data for '{doctype_name}' with key '{key}' received successfully!")
                
                # Removes the specified properties recursively
                data_filtered = data["data"]
                properties_to_remove = [] #['owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parentfield', 'parenttype', 'is_group']
                
                # Applies recursive property removal
                data_filtered = self.remove_properties_recursively(data_filtered, properties_to_remove)
                
                return data_filtered
            else:
                # print(f"No data found for '{doctype_name}' with key '{key}'!")
                return None
        except requests.exceptions.RequestException as e:
            # Captures connection errors, timeouts, etc.
            print(f"Error fetching keys for {doctype_name}: {e}")
            return None
        except json.JSONDecodeError:
            # Captures error if the response is not valid JSON
            print(f"Error decoding keys JSON response for {doctype_name}.")
            return None    
