"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

DocTypes Processing Module - Refactored Version
This module handles the retrieval and processing of DocTypes and their fields from the Arteris API.
It provides functionality to build a hierarchical structure of DocTypes.
"""

import json
import os
import re
import shutil
import unicodedata
import logging
from .hierarchical_tree import HierarchicalTreeBuilder
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from .engine_data import EngineDataBuilder
from .arteris_frappe import ArterisApi


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Field:
    """Represents a field in a DocType"""
    fieldname: str
    label: Optional[str] = None
    fieldtype: Optional[str] = None
    options: Optional[str] = None
    hidden: Optional[bool] = None
    parent: Optional[str] = None
    creation: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Field':
        """Create Field from dictionary"""
        
        # Special handling for Table fields
        # data["fieldtype"] = "Table"
        data["options"] = data.get("options", "")
        return cls(
            fieldname=data.get("fieldname", ""),
            label=data.get("label"),
            fieldtype=data.get("fieldtype"),
            options=data.get("options"),
            hidden=data.get("hidden"),
            parent=data.get("parent"),
            creation=data.get("creation")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ParentMapping:
    """Represents a parent-child relationship between DocTypes"""
    child: str
    parent: str
    type: str


class StringNormalizer:
    """Handles string normalization"""
    
    @staticmethod
    def normalize(s: str) -> str:
        """Normalize string for file/path usage"""
        if not s:
            return ""
        
        # Remove accents
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
        
        # Replace special characters with underscores
        s = re.sub(r'[^a-zA-Z0-9_]', '_', s)
        
        # Replace multiple underscores with single
        s = re.sub(r'_{2,}', '_', s)
        
        # Remove leading/trailing underscores
        s = s.strip('_')
        
        # Convert to lowercase
        return s.lower()


class FieldFilter:
    """Filters fields based on business rules"""
    
    EXCLUDED_FIELDTYPES = {"Section Break", "Column Break", "Tab Break", ""}
    EXCLUDED_FIELDNAMES = {"lft", "rgt", "old_parent"}
    
    @classmethod
    def should_include(cls, field_data: Dict[str, Any]) -> bool:
        """Check if field should be included"""
        # Exclude screen fields
        if field_data.get("fieldtype") in cls.EXCLUDED_FIELDTYPES:
            return False
        
        # Exclude tree view fields
        fieldname = field_data.get("fieldname", "")
        if fieldname in cls.EXCLUDED_FIELDNAMES or fieldname.startswith("parent_"):
            return False
        
        return True


class ArterisApiClient:
    """Wrapper for Arteris API operations"""
    
    def __init__(self):
        self.arteris_api = ArterisApi()
    
    def get_main_doctypes(self) -> Optional[List[Dict]]:
        """Get main doctypes from API"""
        try:
            return self.arteris_api.get_arteris_doctypes(child=False)
        except Exception as e:
            logger.error(f"Failed to get main doctypes: {e}")
            return None
    
    def get_child_doctypes(self) -> Optional[List[Dict]]:
        """Get child doctypes from API"""
        try:
            return self.arteris_api.get_arteris_doctypes(child=True)
        except Exception as e:
            logger.error(f"Failed to get child doctypes: {e}")
            return None
    
    def get_docfields(self, doctype_name: str) -> Optional[Dict]:
        """Get fields for a doctype"""
        try:
            return self.arteris_api.get_docfields_for_doctype(doctype_name)
        except Exception as e:
            logger.error(f"Failed to get fields for {doctype_name}: {e}")
            return None
    
    def get_keys(self, doctype_name: str, filters: Optional[str] = None) -> List[str]:
        """Get keys for a doctype"""
        try:
            return self.arteris_api.get_keys(doctype_name, filters)
        except Exception as e:
            logger.error(f"Failed to get keys for {doctype_name}: {e}")
            return []
    
    def get_data_by_key(self, doctype_name: str, key: str) -> Optional[Dict]:
        """Get data for a specific key"""
        try:
            return self.arteris_api.get_data_from_key(doctype_name, key)
        except Exception as e:
            logger.error(f"Failed to get data for {doctype_name}:{key}: {e}")
            return None


class DataManager:
    """Manages file I/O operations"""
    
    def __init__(self, normalizer: StringNormalizer):
        self.normalizer = normalizer
    
    def save_json(self, path: str, data: Any, filename: str):
        """Save data to JSON file"""
        try:
            os.makedirs(path, exist_ok=True)
            normalized_filename = self.normalizer.normalize(filename)
            file_path = os.path.join(path, f"{normalized_filename}.json")
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Saved data to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save data to {path}/{filename}: {e}")
            raise
    
    def clear_directory(self, path: str):
        """Clear all files in directory"""
        try:
            if os.path.exists(path):
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                logger.info(f"Cleared directory: {path}")
        except Exception as e:
            logger.error(f"Failed to clear directory {path}: {e}")
            raise
    
    def create_directory(self, path: str):
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise


class DoctypeFieldExtractor:
    """Extracts and processes doctype fields"""
    
    def __init__(self, field_filter: FieldFilter):
        self.field_filter = field_filter
    
    def extract_fields(self, docfields: Dict) -> List[Field]:
        """Extract fields from docfields response"""
        fields = []
        
        for field_data in docfields.get("fields", []):
            if self.field_filter.should_include(field_data):
                field = Field.from_dict(field_data)
                fields.append(field)
        
        return fields


class ParentMappingExtractor:
    """Extracts parent-child relationships between doctypes"""
    
    def extract_mappings(self, doctypes_with_fields: Dict[str, List[Dict]]) -> List[ParentMapping]:
        """Extract parent-child mappings from doctype fields"""
        mappings = []
        
        for doctype_name, fields in doctypes_with_fields.items():
            if not fields:
                continue
                
            for field in fields:
                if (field.get("fieldtype") == "Table" and 
                    field.get("fieldname") and 
                    field.get("options")):
                    
                    mapping = ParentMapping(
                        child=field["options"],
                        parent=doctype_name,
                        type=field["fieldtype"]
                    )
                    mappings.append(mapping)
        
        return mappings


class DoctypeDataRetriever:
    """Retrieves actual data for doctypes"""
    
    def __init__(self, api_client: ArterisApiClient, data_manager: DataManager):
        self.api_client = api_client
        self.data_manager = data_manager
    
    def get_doctype_data(self, doctype_name: str, filters: Optional[str] = None) -> Tuple[List[Dict], List[str]]:
        """Get data and keys for a doctype"""
        keys = self.api_client.get_keys(doctype_name, filters)
        data = []
        
        if keys:
            for key in keys:
                doc_data = self.api_client.get_data_by_key(doctype_name, key)
                if doc_data:
                    data.append(doc_data)
        
        return data, keys
    
    def save_doctype_data(self, path: str, data: List[Dict], doctype_name: str):
        """Save doctype data to file"""
        self.data_manager.save_json(path, data, doctype_name)


class Mappings:
    
    def get_specific_mapping(self):
        """
        Returns a specific mapping for the entity structure.
        This is a placeholder function that should be replaced with actual logic.
        """

        specific_mappings = [
            {"child": "Contract Adjustment", "parent": "Contract"},
            {"child": "Contract Item", "parent": "Contract"},
            {"child": "Contract Measurement", "parent": "Contract","filters":[{"medicaovigente":"sim"}]},
            {"child": "Contract Measurement Record", "parent": "Contract","filters":[{"medicaovigente":"sim"}]},
        ]

        # Placeholder for specific mapping logic
        return specific_mappings


    def get_ignore_mapping(self):
        """
        Returns a specific mapping for the entity structure.
        This is a placeholder function that should be replaced with actual logic.
        """

        ignore_mappings = [
            "Formula",
            "Formula Template",
            "Formula Group",
            "Formula Fields",
            "Formula Template",
            "Formula Group Field",
            "Formula Group Template",
            "Asset Config Kartado",
            "Contract Item Config Kartado",
            "Integration Record Keys",
            "Item Config Kartado",
            "Integration Inconsistency",
            "Integration Record",
            "Depth Period Setting",
            "TestPut",
            "TestPutChild",
            "Work Role Config Kartado",
        ]

        # Placeholder for specific mapping logic
        return ignore_mappings

    def get_main_data(self):
        """
        Return main data for the entity structure.
        """

        main_doctypes = [
            {
                "doctype": "Contract",
                "key": "name",
                "childs": [
                    {   
                        "doctype": "Contract Adjustment", 
                        "key": "contrato"
                    },
                    {   
                        "doctype": "Contract Item", 
                        "key": "contrato"
                    },
                    {   "doctype": "Contract Measurement", 
                        "key": "contrato",
                        "filters": [{"field":"medicaovigente", "value": "Sim"}]
                    },
                    {
                        "doctype": "Contract Measurement Record", 
                        "key": "contrato",
                        "filters": [{"field":"medicaovigente", "value": "Sim"}]
                    }
                ]
            }
        ]

        return main_doctypes    


class Translations:
    def get_translations(self):
        return{
            "Asset": "Ativos",
            "Category": "Categorias",
            "City": "Cidades",
            "Contract": "Contratos",
            "Contract_Item": "Itens",
            "Contract_Measurement": "Bol. de medição",
            "Contract_Measurement_Record": "Registros de BM.",
            "Contract_Adjustment": "Reajustes",
            "Contract_Item_Highway": "Rodovias",
            "Contract_Item_Order": "Ped. SAP",
            "Contract_Item_Asset": "Ativos",
            "Contract_Item_Work_Role": "Funções",
            "Contract_Item_City": "Cidades",
            "Contract_Measurement_Asset": "Ativos",
            "Contract_Measurement_Work_Role": "Funções",
            "Contract_Measurement_Record_Material": "Materiais",
            "Contract_Measurement_Record_Asset": "Ativos",
            "Contract_Measurement_Record_Work_Role": "Funções",
            "Contract_Adjustment_Data": "Dados do reajuste",
            "Contracted_Company": "Empresa contratada",
            "Highway": "Rodovias",
            "Highway_City": "Cidades",
            "Holiday": "Feriados",
            "Item_Classification": "Classificação de itens",
            "Material": "Materiais",
            "Person": "Pessoa",
            "Contract_Measurement_City": "Cidades",
            "Contract_Measurement_FTD": "Fat. direto",
            "Contract_Measurement_SAP_Order": "Ped. SAP",
            "Work_Role": "Funções",
            "Contract_Measurement_Record_Log": "Relatórios",
            "Contract_Measurement_Record_Resource": "Recursos",
            "Contract_Measurement_Item": "Itens",
            "Contract_Measurement_Record_Time": "Apontamentos de horas",
            "Contract_Item_Type": "Tipos de itens",
            "Item": "Modelos de itens",
            "Unit": "Unidades",
            "Subsidiary": "Concessionárias",
            "SAP_Order_Highway": "Rodovias",
            "SAP_Order_Period": "Linhas",
            "Item Group": "Grupos de itens",
            "Item_Sub_Group": "Subgrupos de itens",

        }    


class DoctypeRetriever:
    """Retrieves doctypes and their fields"""
    
    def __init__(self, api_client: ArterisApiClient, field_extractor: DoctypeFieldExtractor, mappings: Mappings):
        self.api_client = api_client
        self.field_extractor = field_extractor
        self.mappings = mappings
    
    def get_doctypes_with_fields(self, doctype_list: List[Dict]) -> Dict[str, List[Dict]]:
        """Get doctypes with their fields"""
        doctypes_with_fields = {}
        
        for doc in doctype_list:
            doctype_name = doc.get("name")
            if not doctype_name:
                continue
                
            docfields = self.api_client.get_docfields(doctype_name)
            if docfields:
                fields = self.field_extractor.extract_fields(docfields)
                doctypes_with_fields[doctype_name] = [f.to_dict() for f in fields]
        
        return doctypes_with_fields
    
    def get_all_doctypes(self) -> Dict[str, Any]:
        """Get all doctypes (main and child) with fields"""
        logger.info("Retrieving main doctypes...")
        main_list = self.api_client.get_main_doctypes()
        main_doctypes = self.get_doctypes_with_fields(main_list) if main_list else {}
        
        logger.info("Retrieving child doctypes...")
        child_list = self.api_client.get_child_doctypes()
        child_doctypes = self.get_doctypes_with_fields(child_list) if child_list else {}
        
        # Combine all doctypes
        all_doctypes = {**main_doctypes, **child_doctypes}
        
        # Remove ignored doctypes
        ignore_list = self.mappings.get_ignore_mapping()
        for ignored in ignore_list:
            all_doctypes.pop(ignored, None)
        
        return {
            "main_doctypes": main_doctypes,
            "child_doctypes": child_doctypes,
            "all_doctypes": all_doctypes
        }


class DoctypeProcessor:
    """Main processor for doctype operations"""
    
    def __init__(self):
        # Initialize components
        self.normalizer = StringNormalizer()
        self.api_client = ArterisApiClient()
        self.data_manager = DataManager(self.normalizer)
        self.field_filter = FieldFilter()
        self.field_extractor = DoctypeFieldExtractor(self.field_filter)
        self.mapping_extractor = ParentMappingExtractor()
        self.data_retriever = DoctypeDataRetriever(self.api_client, self.data_manager)
        self.translations = Translations()
        self.mappings = Mappings()
        self.doctype_retriever = DoctypeRetriever(self.api_client, self.field_extractor, self.mappings)
        self.hierarchical_tree = HierarchicalTreeBuilder(self.translations, self.mappings)
    
    def get_keys(self, doctype_name: str, filters: Optional[str] = None) -> List[str]:
        """Get keys for a specific doctype"""
        logger.info(f"Retrieving keys for doctype: {doctype_name}")
        return self.api_client.get_keys(doctype_name, filters)

    def process_doctypes(self) -> Dict[str, Any]:
        """Process all doctypes and return structured data"""
        logger.info("Starting DocTypes and Fields Mapping...")
        
        # Get all doctypes
        doctype_data = self.doctype_retriever.get_all_doctypes()
        
        # Extract parent mappings
        parent_mappings = self.mapping_extractor.extract_mappings(
            doctype_data["all_doctypes"]
        )
        
        # Add parent mappings to result
        doctype_data["parents_mapping"] = [
            {"child": m.child, "parent": m.parent, "type": m.type}
            for m in parent_mappings
        ]
        
        return doctype_data
        
    def get_hierarchical_structure(self) -> List[Dict]:
        """Retrieve and save all doctype data"""
        logger.info("Starting data retrieval...")
        
        # Get doctype structure
        all_doctypes = self.process_doctypes()
        
        # # Get main data configuration
        # main_doctypes = mappings.get_main_data()
        
        # # Enrich main doctypes with field information
        # for main in main_doctypes:
        #     main["doctype_with_fields"] = all_doctypes["all_doctypes"].pop(main["doctype"], [])
            
        #     for child in main.get("childs", []):
        #         child["doctype_with_fields"] = all_doctypes["all_doctypes"].pop(child["doctype"], [])
        
        # Get hierarchical structure
        hierarchical = self.hierarchical_tree.build_tree(all_doctypes)

        # Apply icons to hierarchical structure
        # for r in hierarchical:
        #     r["icon"] == self.apply_icon(r)
        
        return hierarchical
    
    def get_default_data(self, using_cached_data = False) -> List[Dict]:
        """Retrieve default data for all doctypes"""
        logger.info("Starting data retrieval for default doctypes...")
        
        # Check if cached data exists
        if not using_cached_data or not os.path.isfile("data/all_doctypes_data.json") or not os.path.isfile("data/all_doctypes_structure.json"):

            # Get doctype structure
            all_doctype_structure = self.process_doctypes()

            # Get main data configuration
            main_doctypes = self.mappings.get_main_data()
            
            # Enrich main doctypes with field information
            for main in main_doctypes:
                all_doctype_structure["main_doctypes"].pop(main["doctype"], [])
                
                for child in main.get("childs", []):
                    all_doctype_structure["main_doctypes"].pop(child["doctype"], [])

            # Remove ignored doctypes
            ignore_list = self.mappings.get_ignore_mapping()
            for ignored in ignore_list:
                all_doctype_structure["main_doctypes"].pop(ignored, None)
                        
            # Collect all doctype data
            all_doctype_data = []
            
            # Process remaining doctypes
            for doctype_name in all_doctype_structure["main_doctypes"]:
                data, _ = self.data_retriever.get_doctype_data(doctype_name)
                all_doctype_data.append({doctype_name: data})
            
            # write all_doctypes_structure to file
            self.data_manager.save_json("data", all_doctype_data, "all_doctypes_data")
            # write all_doctypes_datato file
            self.data_manager.save_json("data", all_doctype_structure, "all_doctypes_strutucture")
        
        else:
            logger.info("Using cached data from data/all_doctypes_data.json")
            with open("data/all_doctypes_data.json", "r", encoding="utf-8") as f:
                all_doctype_data = json.load(f)
            with open("data/all_doctypes_strtucture.json", "r", encoding="utf-8") as f:
                all_doctype_structure = json.load(f)

        return {
            "data": all_doctype_data, 
            "structure": all_doctype_structure["all_doctypes"]
        }

    
    def get_data(self, main_id: str) -> List[Dict]:
        """Retrieve and save all doctype data"""
        logger.info("Starting data retrieval...")
        
        # Check all_doctypes.json file, if not exists, get default data
        if not os.path.isfile("data/all_doctypes_data.json") or not os.path.isfile("data/all_doctypes_strutucture.json"):
            result = self.get_default_data(using_cached_data=False)
            all_doctype_structure = result["structure"]
            all_doctype_data = result["data"]
        else:
            logger.info("Using cached data from data/all_doctypes_data.json")
            with open("data/all_doctypes_data.json", "r", encoding="utf-8") as f:
                all_doctype_data = json.load(f)
            with open("data/all_doctypes_strutucture.json", "r", encoding="utf-8") as f:
                all_doctype_structure = json.load(f)

        # Get main data configuration
        main_doctypes = self.mappings.get_main_data()
                                
        # Process main doctypes
        for main in main_doctypes:
            # Apply filter if main_id provided
            filters = None

            filters = f'[["{main["key"]}","=","{main_id}"]]'
            
            data, keys = self.data_retriever.get_doctype_data(main["doctype"], filters)
            all_doctype_data.append({main["doctype"]: data})
            
            # Process child doctypes for each key
            for key in keys:
                for child in main.get("childs", []):
                    child_filter = f'["{child["key"]}","=","{key}"]'
                    if "filters" in child:
                        for filter in child["filters"]:
                            child_filter += f',["{filter["field"]}","=","{filter["value"]}"]'
                    child_data, _ = self.data_retriever.get_doctype_data(
                        child["doctype"], 
                        f'[{child_filter}]'
                    )
                    all_doctype_data.append({child["doctype"]: child_data})

        
        # Save all doctype data
        self.data_manager.save_json("data", all_doctype_data, f"all_doctype_data_{main_id}")

        # Get hierarchical structure
        hierarchical = self.hierarchical_tree.build_tree(all_doctype_structure)
        
        return {
            "data": all_doctype_data,
            "structure": all_doctype_structure,
            "hierarchical": hierarchical
        }
    
    def get_formula_data(self, using_cached_data = False) -> List[Dict]:
        """Retrieve formula group data"""
        logger.info("Retrieving formula data...")

        # Check if cached data exists
        if not using_cached_data or not os.path.isfile("data/formula_group.json"):
            data, _ = self.data_retriever.get_doctype_data("Formula Group")
            self.data_retriever.save_doctype_data("data", data, "formula_group")

        with open("data/formula_group.json", "r", encoding="utf-8") as f:
            return json.load(f)
        
    def get_contracts(self) -> List[Dict]:
        """Retrieve contract data"""
        logger.info("Retrieving contract data...")

        keys = self.get_keys("Contract", filters='[["contratoencerrado","=",null]]')

        return keys


def main():
    """Main entry point"""
    try:
        processor = DoctypeProcessor()
        
        #processor.get_default_data(using_cached_data=True)

        # Uncomment to get data for specific contract
        contract_data = processor.get_data("0196b01a-2163-7cb2-93b9-c8b1342e3a4e")

        formulas = processor.get_formula_data(using_cached_data=True)

         # Get formula to contract
        group_formula = [item for item in contract_data['data'] if 'Contract' in item][0]['Contract'][0]['grupoformulas']

        # Filter formulas based on group
        contract_formula = [f for f in formulas if f.get("name") in group_formula]    

        # Build engine data
        builder = EngineDataBuilder(
            contract_data['hierarchical'], 
            contract_formula, 
            contract_data['data'], 
            "data",
            compact_mode=True
        )
        engine_data = builder.build()

        # save engine data to tree_data.json
        processor.data_manager.save_json("data", engine_data, "tree_data")

        # # Get formula data
        # processor.get_formula_data()
        
        # # Get hierarchical structure
        # processor.get_hierarchical_structure()
                
        # logger.info("Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()