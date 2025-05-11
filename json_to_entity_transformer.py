"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

JSON to Entity Transformer Module.
This module provides functions to create a hierarchical entity structure from DocTypes metadata.
It's a bridge module that calls functions from json_to_hierarchical.py.
"""

# Import the main function from the json_to_hierarchical module
from json_to_hierarquical import create_hierarchical_doctype_structure

# This module acts as a bridge to maintain compatibility with older code that uses
# this module name rather than the actual implementation in json_to_hierarquical.py