"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Main Script Module.
This module orchestrates the fetching of metadata and data from the Arteris API.

This script performs the following steps:
1. Loads API configuration from the .env file.
2. Fetches the list of DocTypes from the 'Arteris' module using api_client.
3. For each DocType, fetches its DocFields using api_client.
4. Transforms the collected metadata (DocTypes and DocFields) into the entity
   JSON structure using transformer.
5. For each DocType with DocFields, fetches the corresponding real data
   using api_client.
6. Stores the results in in-memory dictionaries and prints examples.
"""

import get_doctypes 
from dotenv import load_dotenv
import json
import os

# Load environment variables from the .env file in the project root
load_dotenv()

def main():
    """
    Main function that orchestrates the process of fetching and transforming 
    DocTypes and their fields into a hierarchical entity structure.
    """
    # Get the hierarchical structure of DocTypes
    hierarchical_entity = get_doctypes.get_hierarchical_doctype_structure()
    
    print("Hierarchical structure loaded:")
    # print(hierarchical_entity)
    print("\nChecking for circular references...")
    try:
        json.dumps(hierarchical_entity)
        print("No circular references detected.")
    except Exception as e:
        print(f"Circular reference error detected: {e}")

    # Save the hierarchical structure to a JSON file
    output_dir = "output"
    output_filename = "output_hierarchical.json"
    print(f"Path: {os.path.join(output_dir, output_filename)}")
    try:
        with open(os.path.join(output_dir, output_filename), "w", encoding="utf-8") as f:
            json.dump(hierarchical_entity, f, indent=4, ensure_ascii=False)
        print(f"\n************************")
        print(f"File {output_filename} saved successfully in {output_dir}.")
    except Exception as e:
        print(f"Error saving the file: {e}")

# Script entry point
if __name__ == "__main__":
    main()