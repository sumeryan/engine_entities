import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod


@dataclass
class FieldData:
    """Represents a field with its path, type and value"""
    path: str
    type: str
    value: Any


@dataclass
class EngineDataItem:
    """Represents an engine data item"""
    id: str
    creation: str
    fields: List[FieldData] = field(default_factory=list)
    childs: List['EngineDataHead'] = field(default_factory=list)

    def to_dict(self, child_name: str = "childs") -> Dict[str, Any]:
        """Convert to dictionary with custom child name"""
        return {
            "id": self.id,
            "creation": self.creation,
            "fields": [{"path": f.path, "type": f.type, "value": f.value} for f in self.fields],
            child_name: [child.to_dict(child_name) for child in self.childs]
        }


@dataclass
class FormulaData:
    """Represents a formula configuration"""
    path: str
    value: str
    update: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "value": self.value,
            "update": self.update
        }


@dataclass
class EngineDataHead:
    """Represents the head of engine data structure"""
    path: str
    formulas: List[FormulaData] = field(default_factory=list)
    data: List[EngineDataItem] = field(default_factory=list)

    def to_dict(self, child_name: str = "childs") -> Dict[str, Any]:
        """Convert to dictionary with custom child name"""
        return {
            "path": self.path,
            "formulas": [f.to_dict() for f in self.formulas],
            "data": [item.to_dict(child_name) for item in self.data]
        }


class DefaultValueProvider:
    """Provides default values for different field types"""
    
    DEFAULT_VALUES = {
        "int": 0,
        "numeric": 0,
        "float": 0,
        "number": 0,
        "string": "",
        "boolean": False,
        "date": "1999-01-01",
        "datetime": "1999-01-01 00:00:00",
        "time": "00:00:00",
        "text": ""
    }
    
    DEFAULT_CREATION_DATE = "1999-01-01 00:00:00"
    
    @classmethod
    def get_default(cls, field_type: str) -> Any:
        """Get default value for field type"""
        return cls.DEFAULT_VALUES.get(field_type, "")


class PathManager:
    """Manages path references and replacements"""
    
    def __init__(self):
        self.paths: List[str] = []
        self._path_set: set = set()
    
    def add_path(self, path: str) -> None:
        """Add a path to the collection if not already present"""
        if path and path not in self._path_set:
            print(f"Adding path: {path}")
            self.paths.append(path)
            self._path_set.add(path)
    
    def generate_references(self) -> Dict[str, List[Dict[str, str]]]:
        """Generate reference mapping for all paths"""
        references = {}
        for index, path in enumerate(self.paths):
            references[f"e{index:05d}v"] = path
        
        return {"referencia": [references]}
    
    def replace_paths_with_references(self, data: Any, references: Dict) -> Any:
        """Replace all paths with their reference codes"""
        ref_dict = references["referencia"][0]
        
        # Sort by length to replace longer paths first
        sorted_refs = dict(sorted(ref_dict.items(), key=lambda x: len(x[1]), reverse=True))
        
        replacer = PathReplacer(sorted_refs)
        return replacer.replace(data)


class PathReplacer:
    """Handles path replacement logic"""
    
    def __init__(self, reference_dict: Dict[str, str]):
        self.reference_dict = reference_dict
    
    def replace(self, obj: Any) -> Any:
        """Recursively replace paths in object"""
        if isinstance(obj, list):
            return [self.replace(item) for item in obj]
        
        elif isinstance(obj, dict):
            if "value" in obj and "path" in obj and "update" in obj:
                # Handle formula objects
                obj["value"] = self._replace_in_formula(obj["value"])
            
            if "path" in obj:
                # Handle direct path replacement
                obj["path"] = self._replace_direct_path(obj["path"])
            
            # Recursively process nested structures
            for key in ["data", "childs", "fields", "formulas"]:
                if key in obj:
                    obj[key] = self.replace(obj[key])
        
        return obj
    
    def _replace_direct_path(self, path: str) -> str:
        """Replace exact path matches"""
        for code, original_path in self.reference_dict.items():
            if path == original_path:
                return code
        return path
    
    def _replace_in_formula(self, formula: str) -> str:
        """Replace paths within formula strings"""
        if not isinstance(formula, str):
            return formula
        
        result = formula
        for code, original_path in self.reference_dict.items():
            # Pattern to match whole words or with specific operators
            pattern = r'(^|\W)(' + re.escape(original_path) + r')(\W|$)'
            
            def replace_match(match):
                return match.group(1) + code + match.group(3)
            
            result = re.sub(pattern, replace_match, result)
        
        return result


class FormulaProcessor:
    """Processes formulas for doctypes"""
    
    def __init__(self, formulas: List[Dict], field_path_finder):
        self.formulas = formulas
        self.field_path_finder = field_path_finder
    
    def get_doctype_formulas(self, doctype_name: str) -> List[FormulaData]:
        """Get all formulas for a specific doctype"""
        doctype_formulas = []
        
        # Extract table formulas
        table_formulas = self.formulas[0].get("tableformulas", [])
        
        for formula in table_formulas:
            if formula.get("groupfielddoctype") == doctype_name:
                path = self.field_path_finder(
                    formula["groupfielddoctype"],
                    formula["groupfieldfieldname"]
                )
                
                if path:
                    formula_data = FormulaData(
                        path=path,
                        value=formula["formula"],
                        update={
                            "doctype": formula["groupfielddoctype"],
                            "fieldname": formula["groupfieldfieldname"]
                        }
                    )
                    doctype_formulas.append(formula_data)
        
        return doctype_formulas


class FieldPathFinder:
    """Finds field paths in doctype tree"""
    
    def __init__(self, doctype_tree: List[Dict]):
        self.doctype_tree = doctype_tree
    
    def find(self, doctype_name: str, field_name: str) -> Optional[str]:
        """Find the path for a specific field in a doctype"""
        return self._search_recursive(self.doctype_tree, doctype_name, field_name)
    
    def _search_recursive(self, nodes: List[Dict], doctype_name: str, 
                         field_name: str, current_path: Optional[str] = None) -> Optional[str]:
        """Recursively search for field path"""
        for node in nodes:
            if node.get("type") == "doctype" and node.get("fieldname") == doctype_name:
                # Found the doctype, now search for the field
                for child in node.get("children", []):
                    if child.get("fieldname") == field_name:
                        return child.get("path")
            
            # Continue searching in children
            result = self._search_recursive(
                node.get("children", []), 
                doctype_name, 
                field_name, 
                current_path
            )
            if result:
                return result
        
        return None


class DoctypeIndexManager:
    """Manages doctype processing indices"""
    
    def __init__(self):
        self.indices: Dict[str, int] = {}
    
    def get_index(self, path: str, reset: bool = False) -> int:
        """Get current index for path"""
        if reset or path not in self.indices:
            self.indices[path] = 0
        return self.indices[path]
    
    def increment_index(self, path: str) -> None:
        """Increment index for path"""
        self.indices[path] = self.indices.get(path, 0) + 1


class DataTraverser:
    """Traverses and processes doctype data"""
    
    def __init__(
            self, 
            all_doctype_data: List[Dict], 
            path_manager: PathManager,
            formula_processor: FormulaProcessor, 
            child_name: str = "childs"):
        self.all_doctype_data = all_doctype_data
        self.path_manager = path_manager
        self.formula_processor = formula_processor
        self.child_name = child_name
        self.index_manager = DoctypeIndexManager()
        self.default_provider = DefaultValueProvider()
    
    def get_doctype_data(self, doctype_name: str) -> List[Dict]:
        """Get data for specific doctype"""
        print(f"Getting doctype data: {doctype_name}")
        for data_dict in self.all_doctype_data:
            if doctype_name in data_dict:
                return data_dict[doctype_name]
        return []
    
    def traverse_doctype(self, node: Dict, parent_head: Optional[EngineDataHead] = None,
                        doctype_data: Optional[List[Dict]] = None, 
                        reset_index: bool = False, 
                        parent_item: Optional[EngineDataItem] = None) -> Optional[EngineDataHead]:
        """Traverse and process a doctype node"""
        self.path_manager.add_path(node["path"])
        
        # Get doctype data if not provided
        if doctype_data is None:
            doctype_data = self.get_doctype_data(node["fieldname"])
        
        # Get formulas for this doctype
        formulas = self.formula_processor.get_doctype_formulas(node["fieldname"])
        
        # Create new head
        new_head = EngineDataHead(
            path=node["path"],
            formulas=formulas,
            data=[]
        )
        
        # Add to parent if exists
        if parent_head and parent_head.data:
            parent_head.data[-1].childs.append(new_head)
        
        # Process the doctype data
        self._process_doctype_data(
            node["children"], 
            new_head, 
            doctype_data, 
            node["path"], 
            reset_index
        )
        
        return new_head if parent_head is None else None
    
    def _process_doctype_data(self, nodes: List[Dict], head: EngineDataHead,
                             doctype_data: List[Dict], path: str, reset_index: bool):
        """Process data for a doctype"""
        index = self.index_manager.get_index(path, reset_index)
        
        if doctype_data and index < len(doctype_data):
            # Process actual data
            for data_item in doctype_data[index:]:
                self.index_manager.increment_index(path)
                engine_item = self._create_engine_item(nodes, data_item, head)
                if engine_item:
                    head.data.append(engine_item)
        else:
            # Create empty item with default values
            engine_item = self._create_empty_engine_item(nodes, head)
            if engine_item:
                head.data.append(engine_item)
    
    def _create_engine_item(self, nodes: List[Dict], data: Dict, 
                           head: EngineDataHead) -> Optional[EngineDataItem]:
        """Create an engine data item from doctype data"""
        engine_item = EngineDataItem(
            id=data.get("name", ""),
            creation=data.get("creation", self.default_provider.DEFAULT_CREATION_DATE)
        )
        
        for node in nodes:
            self.path_manager.add_path(node["path"])
            
            if node["type"] == "doctype":
                # Handle nested doctypes
                if node.get("fieldname_data"):
                    nested_data = data.get(node["fieldname_data"], [])
                else:
                    nested_data = self.get_doctype_data(node["fieldname"])
                
                # Add current item before processing children if it has any data
                if engine_item and (engine_item.fields or engine_item.id):
                    head.data.append(engine_item)
                
                # Clear engine_item to avoid duplication
                engine_item = None
                
                # Process nested doctype - pass current item as parent
                if engine_item:
                    self.traverse_doctype(node, head, nested_data, True, engine_item)
                else:
                    self.traverse_doctype(node, head, nested_data, True)
            else:
                # Handle regular fields
                if engine_item is not None:
                    value = data.get(node["fieldname"], None)
                    field_data = FieldData(
                        path=node["path"],
                        type=node["type"],
                        value=value
                    )
                    engine_item.fields.append(field_data)
        
        return engine_item
    
    def _create_empty_engine_item(self, nodes: List[Dict], 
                                 head: EngineDataHead) -> Optional[EngineDataItem]:
        """Create an empty engine item with default values"""
        engine_item = EngineDataItem(
            id="",
            creation=self.default_provider.DEFAULT_CREATION_DATE
        )
        
        for node in nodes:
            self.path_manager.add_path(node["path"])
            
            if node["type"] == "doctype":
                # Add current item before processing children if it has any data
                if engine_item and engine_item.fields:
                    head.data.append(engine_item)
                
                # Clear engine_item to avoid duplication
                engine_item = None
                
                # Process nested doctype with empty data
                self.traverse_doctype(node, head, [], True)
            else:
                # Add field with default value
                if engine_item is not None:
                    default_value = self.default_provider.get_default(node["type"])
                    field_data = FieldData(
                        path=node["path"],
                        type=node["type"],
                        value=default_value
                    )
                    engine_item.fields.append(field_data)
        
        return engine_item


class EngineDataBuilder:
    """Main class for building engine data structure"""
    
    def __init__(
            self, 
            doctype_tree: List[Dict], 
            formulas: List[Dict],
            all_doctype_data: List[Dict], 
            child_name: str = "childs"):
        
        self.doctype_tree = doctype_tree
        self.formulas = formulas
        self.all_doctype_data = all_doctype_data
        self.child_name = child_name
        
        # Initialize components
        self.path_manager = PathManager()
        self.field_finder = FieldPathFinder(doctype_tree)
        self.formula_processor = FormulaProcessor(formulas, self.field_finder.find)
        self.traverser = DataTraverser(
            all_doctype_data, 
            self.path_manager, 
            self.formula_processor,
            child_name
        )
    
    def build(self) -> Dict[str, Any]:
        """Build the complete engine data structure"""
        result = []
        
        self.unique_formuals = self.extract_formulas_paths()

        # Process each root node
        for root in self.doctype_tree:
            head = self.traverser.traverse_doctype(root)
            if head:
                result.append(head)
        
        # Generate references
        references = self.path_manager.generate_references()
        
        # Convert to dict format
        result_dicts = [head.to_dict(self.child_name) for head in result]
        
        # Replace paths with references
        sorted_refs = {
            "referencia": [
                dict(sorted(references["referencia"][0].items(), 
                           key=lambda x: len(x[1]), reverse=True))
            ]
        }
        result_with_refs = self.path_manager.replace_paths_with_references(
            result_dicts, 
            sorted_refs
        )
        
        # Build final structure
        return {
            "referencia": references["referencia"],
            "data": result_with_refs
        }
    
    def extract_formulas_paths(self) -> List[str]:
        """Extract unique paths from formulas"""
        # Padrão regex para encontrar caminhos com qualquer identificador inicial
        # Aceita letras, números, underscore no identificador inicial e nos segmentos do path
        path_pattern = r'[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9_\.]+[a-zA-Z0-9_]'
        
        formulas = "\n".join([
            item["formula"]                                 # ← o que queremos guardar
            for group in self.formulas                      # ← cada “Formula Group”
            for item in group.get("tableformulas", [])      # ← cada linha de fórmula
            if "formula" in item                            # ← segurança contra chaves ausentes
        ])

        # Encontra todos os caminhos na fórmula
        paths = re.findall(path_pattern, formulas)
        
        # Remove duplicatas mantendo a ordem
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)

        # Find fields formulas in the formulas
        for group in self.formulas:
            for item in group.get("tableformulas", []):
                if "groupfielddoctype" in item and "groupfieldfieldname" in item:
                    # Add the path for the field in the unique paths if not already present
                    path = self.field_finder.find(
                        item["groupfielddoctype"], 
                        item["groupfieldfieldname"]
                    )
                    if path and path not in unique_paths:
                        unique_paths.append(path)
        
        return unique_paths


class FileManager:
    """Handles file I/O operations"""
    
    @staticmethod
    def load_json(file_path: str) -> Any:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON from {file_path}: {e}")
    
    @staticmethod
    def save_json(data: Any, file_path: str) -> None:
        """Save data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save JSON to {file_path}: {e}")
        
def main():
    """Main entry point"""
    try:
        # Load required data
        formulas = FileManager.load_json("data/formula_group.json")
        doctype_tree = FileManager.load_json("output/hierarquical_doctypes.json")
        all_doctype_data = FileManager.load_json("data/all_doctypes.json")

        # Build engine data
        builder = EngineDataBuilder(
            doctype_tree, 
            formulas, 
            all_doctype_data, 
            "data"
        )
        engine_data = builder.build()
        
        # Save result
        FileManager.save_json(engine_data, "output/tree_data_refactored.json")
        
        print("Dados gravados em output/tree_data_refactored.json")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()