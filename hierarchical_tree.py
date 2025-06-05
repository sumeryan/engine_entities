"""
Hierarchical Tree Builder - Refactored Version
This module builds hierarchical tree structures from doctype data.
"""

import json
import re
import unicodedata
import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
#from .get_doctypes import Mappings, Translations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an entity in the hierarchical tree"""
    key: str
    description: str
    fieldname: str
    fieldname_data: str = ""
    type: str = "doctype"
    path: str = ""
    dragandrop: bool = False
    children: List['Entity'] = field(default_factory=list)
    icon: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation"""

        field = { 
            "key": self.key,
            "description": self.description,
            "fieldname": self.fieldname,
            "fieldname_data": self.fieldname_data,
            "type": self.type,
            "path": self.path,
            "dragandrop": self.dragandrop,
            "icon": self.icon,
            "children": [child.to_dict() for child in self.children],
        }

        return field
 
    def add_child(self, child: 'Entity') -> None:
        """Add a child entity"""
        self.children.append(child)
    
    def has_child_with_key(self, key: str) -> bool:
        """Check if entity has a child with given key"""
        return any(child.key == key for child in self.children)
    
    def find_child_by_key(self, key: str) -> Optional['Entity']:
        """Find a child by its key"""
        for child in self.children:
            if child.key == key:
                return child
        return None
    
    def remove_child_by_key(self, key: str) -> None:
        """Remove a child by its key"""
        self.children = [child for child in self.children if child.key != key]


class StringNormalizer:
    """Handles string normalization for paths and keys"""
    
    @staticmethod
    def normalize(s: str) -> str:
        """Normalize string for path usage"""
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
    
    @staticmethod
    def create_key(name: str) -> str:
        """Create a key from a name"""
        return name.replace(" ", "_")


class FieldTypeMapper:
    """Maps field types from doctypes to hierarchical model types"""
    
    TYPE_MAPPING = {
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
        "Table": "doctype"
    }
    
    @classmethod
    def map_type(cls, fieldtype: str) -> str:
        """Map field type to hierarchical model type"""
        return cls.TYPE_MAPPING.get(fieldtype, "string")


class MappingManager:
    """Manages parent-child relationships and mappings"""
    
    def __init__(self, specified_mappings: List[Dict[str, str]]):
        self.specified_mappings = specified_mappings
        self.mandatory_children: Dict[str, List[str]] = {}
        self.mandatory_parents: Dict[str, List[str]] = {}
        self.child_to_parent_map: Dict[str, str] = {}
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build lookup tables for efficient access"""
        for mapping in self.specified_mappings:
            child = mapping["child"]
            parent = mapping["parent"]
            
            # Build parent lookup
            if child not in self.mandatory_parents:
                self.mandatory_parents[child] = []
            self.mandatory_parents[child].append(parent)
            
            # Build children lookup
            if parent not in self.mandatory_children:
                self.mandatory_children[parent] = []
            self.mandatory_children[parent].append(child)
            
            # Build child to parent map
            self.child_to_parent_map[child] = parent
    
    def has_mandatory_parent(self, child: str) -> bool:
        """Check if a child has mandatory parents"""
        return child in self.mandatory_parents
    
    def get_mandatory_parents(self, child: str) -> List[str]:
        """Get mandatory parents for a child"""
        return self.mandatory_parents.get(child, [])
    
    def get_mandatory_children(self, parent: str) -> List[str]:
        """Get mandatory children for a parent"""
        return self.mandatory_children.get(parent, [])
    
    def is_valid_optional_child(self, parent: str, child: str) -> bool:
        """Check if a child can be optionally added to a parent"""
        # If child has mandatory parents and current parent is not one of them
        if self.has_mandatory_parent(child) and parent not in self.mandatory_parents[child]:
            return False
        
        # If this child already exists as a mandatory child
        if child in self.get_mandatory_children(parent):
            return False
        
        return True
    
    def get_proper_parent(self, child: str) -> Optional[str]:
        """Get the proper parent for a child based on mappings"""
        return self.child_to_parent_map.get(child)
    
    def get_children_to_remove_from_root(self) -> Set[str]:
        """Get set of children that should not be at root level"""
        normalizer = StringNormalizer()
        return {normalizer.create_key(mapping["child"]) 
                for mapping in self.specified_mappings}


class EntityFactory:
    """Factory for creating different types of entities"""
    
    def __init__(self, normalizer: StringNormalizer, 
                 type_mapper: FieldTypeMapper,
                 translations: Optional[Dict[str, str]] = None):
        self.normalizer = normalizer
        self.type_mapper = type_mapper
        self.translations = translations or {}
    
    def create_doctype_entity(self, 
                              doctype_name: str, 
                              fieldname_data: str = "",
                              is_root: bool = False) -> Entity:
        """Create a doctype entity"""
        doctype_key = self.normalizer.create_key(doctype_name)
        translated_name = self.translations.get(doctype_key, doctype_name)
        
        entity = Entity(
            key=doctype_key,
            description=translated_name,
            fieldname=doctype_name,
            fieldname_data=fieldname_data,
            type="doctype",
            path=self.normalizer.normalize(translated_name),
            dragandrop=False,
            icon="text"
        )
        
        # Add default key field for all doctype entities
        entity.add_child(self.create_key_field())

        return entity
    
    def create_key_field(self) -> Entity:
        """Create the default key field"""
        return Entity(
            key="chave",
            description="Chave do registro",
            fieldname="name",
            type="key",
            path=self.normalizer.normalize("Chave do registro"),
            dragandrop=True,
            icon="key"
        )
    
    def create_field_entity(self, field_data: Dict[str, Any]) -> Entity:
        """Create a field entity from field data"""
        field_type = self.type_mapper.map_type(field_data.get("fieldtype", ""))
        field_label = field_data.get("label", "")
        field_key = self.normalizer.create_key(field_label)
        field_icon = self.apply_icon(field_data.get("fieldtype", ""))
        
        return Entity(
            key=field_key,
            description=field_label,
            fieldname=field_data.get("fieldname", ""),
            fieldname_data=field_data.get("fieldname_data", ""),
            type=field_type,
            path=self.normalizer.normalize(field_label),
            dragandrop=True,
            icon=field_icon
        )
    

    def apply_icon(self, type: str) -> str:
        # Map fieldtype to icon using a dictionary for elegance and maintainability
        icon_map = {
            "Link": "key",
            "Float": "number",
            "Currency": "money",
            "Int": "integer",
            "Data": "text",
            "Select": "text",
            "Date": "calendar",
            "Datetime": "calendar",
        }

        icon = icon_map.get(type)

        if not icon:
            icon = "text"  # Default icon if no match found

        return icon


class PathManager:
    """Manages path updates in the hierarchical structure"""
    
    def __init__(self, normalizer: StringNormalizer):
        self.normalizer = normalizer
    
    def update_all_paths(self, entities: List[Entity]) -> None:
        """Update all paths in the hierarchy"""
        for entity in entities:
            entity.path = self.normalizer.normalize(entity.description)
            self._update_child_paths(entity, entity.path)
    
    def _update_child_paths(self, parent: Entity, parent_path: str) -> None:
        """Recursively update child paths"""
        for child in parent.children:
            child_path = self.normalizer.normalize(child.description)
            child.path = f"{parent_path}.{child_path}"
            self._update_child_paths(child, child.path)


class EntityTreeNavigator:
    """Navigates and searches entities in the tree"""
    
    @staticmethod
    def find_entity_by_key(entities: List[Entity], key: str) -> Optional[Entity]:
        """Find an entity by its key in the tree"""
        for entity in entities:
            if entity.key == key:
                return entity
            
            # Search in children
            result = EntityTreeNavigator._find_in_children(entity, key)
            if result:
                return result
        
        return None
    
    @staticmethod
    def _find_in_children(parent: Entity, key: str) -> Optional[Entity]:
        """Recursively search for entity in children"""
        for child in parent.children:
            if child.key == key:
                return child
            
            result = EntityTreeNavigator._find_in_children(child, key)
            if result:
                return result
        
        return None
    
    @staticmethod
    def remove_entity_from_tree(entities: List[Entity], key: str) -> None:
        """Remove entity with given key from anywhere in the tree"""
        for entity in entities:
            entity.remove_child_by_key(key)
            EntityTreeNavigator._remove_from_children(entity, key)
    
    @staticmethod
    def _remove_from_children(parent: Entity, key: str) -> None:
        """Recursively remove entity from children"""
        for child in parent.children:
            child.remove_child_by_key(key)
            EntityTreeNavigator._remove_from_children(child, key)


class DoctypeProcessor:
    """Processes doctypes and builds entities"""
    
    def __init__(self, entity_factory: EntityFactory, 
                 mapping_manager: MappingManager,
                 doctypes_data: Dict[str, Any]):
        self.entity_factory = entity_factory
        self.mapping_manager = mapping_manager
        self.doctypes_data = doctypes_data
        self.processed_doctypes: Set[str] = set()
    
    def process_doctype(self, 
                        doctype_name: str, 
                        fieldname_data: str = "",
                        is_root: bool = False) -> Optional[Entity]:
        """Process a single doctype and return its entity"""
        if doctype_name in self.processed_doctypes:
            return None
        
        if doctype_name not in self.doctypes_data.get("all_doctypes", {}):
            return None
        
        self.processed_doctypes.add(doctype_name)
        
        # Create entity
        entity = self.entity_factory.create_doctype_entity(doctype_name, fieldname_data, is_root)
        
        # Add fields
        self._add_regular_fields(entity, doctype_name)
        
        # Add mandatory children
        self._add_mandatory_children(entity, doctype_name)
        
        # Add optional relationships
        self._add_optional_relationships(entity, doctype_name)
        
        return entity
    
    def _add_regular_fields(self, entity: Entity, doctype_name: str) -> None:
        """Add regular (non-relationship) fields to entity"""
        fields = self.doctypes_data["all_doctypes"].get(doctype_name, [])
        
        for field in fields:
            # Skip relationship fields
            if field.get("fieldtype") == "Table":
                continue
            
            field_entity = self.entity_factory.create_field_entity(field)
            entity.add_child(field_entity)
    
    def _add_mandatory_children(self, entity: Entity, doctype_name: str) -> None:
        """Add mandatory children based on mappings"""
        mandatory_children = self.mapping_manager.get_mandatory_children(doctype_name)
        
        for child_name in mandatory_children:
            if entity.has_child_with_key(self.entity_factory.normalizer.create_key(child_name)):
                continue
            
            child_entity = self.process_doctype(child_name)
            if child_entity:
                entity.add_child(child_entity)
    
    def _add_optional_relationships(self, entity: Entity, doctype_name: str) -> None:
        """Add optional relationships based on field options"""
        fields = self.doctypes_data["all_doctypes"].get(doctype_name, [])
        
        for field in fields:
            if field.get("fieldtype") != "Table" or not field.get("options"):
                continue
            
            related_doctype = field["options"]
            
            # Check if this is a valid optional relationship
            if not self.mapping_manager.is_valid_optional_child(doctype_name, related_doctype):
                continue
            
            # Check if already added
            related_key = self.entity_factory.normalizer.create_key(related_doctype)
            if entity.has_child_with_key(related_key):
                continue
            
            # Process the related doctype
            child_entity = self.process_doctype(related_doctype, field.get("fieldname", ""))
            if child_entity:
                entity.add_child(child_entity)


class MappingEnforcer:
    """Enforces specified mappings on the tree structure"""
    
    def __init__(self, mapping_manager: MappingManager, 
                 navigator: EntityTreeNavigator,
                 normalizer: StringNormalizer):
        self.mapping_manager = mapping_manager
        self.navigator = navigator
        self.normalizer = normalizer
    
    def enforce_mappings(self, entities: List[Entity]) -> None:
        """Enforce all specified mappings on the tree"""
        # First, remove misplaced children
        self._remove_misplaced_children(entities)
        
        # Then, add children to correct parents
        self._add_children_to_correct_parents(entities)
        
        # Recursively enforce mappings
        for entity in entities:
            self._enforce_mappings_recursive(entity)
    
    def _remove_misplaced_children(self, entities: List[Entity]) -> None:
        """Remove children that are under wrong parents"""
        for mapping in self.mapping_manager.specified_mappings:
            child_key = self.normalizer.create_key(mapping["child"])
            parent_key = self.normalizer.create_key(mapping["parent"])
            
            # Remove child from any non-specified parent
            for entity in entities:
                if entity.key != parent_key:
                    entity.remove_child_by_key(child_key)
                    self.navigator._remove_from_children(entity, child_key)
    
    def _add_children_to_correct_parents(self, entities: List[Entity]) -> None:
        """Add children to their correct parents according to mappings"""
        for mapping in self.mapping_manager.specified_mappings:
            child_key = self.normalizer.create_key(mapping["child"])
            parent_key = self.normalizer.create_key(mapping["parent"])
            
            parent = self.navigator.find_entity_by_key(entities, parent_key)
            child = self.navigator.find_entity_by_key(entities, child_key)
            
            if parent and child and not parent.has_child_with_key(child_key):
                parent.add_child(child)
    
    def _enforce_mappings_recursive(self, entity: Entity) -> None:
        """Recursively enforce mappings at all levels"""
        # Process grandchildren that need to be moved
        for child in entity.children[:]:  # Use slice to avoid modification during iteration
            grandchildren_to_move = []
            
            for grandchild in child.children[:]:
                proper_parent_name = self.mapping_manager.get_proper_parent(grandchild.fieldname)
                
                if proper_parent_name and child.fieldname != proper_parent_name:
                    # Find proper parent among siblings
                    for sibling in entity.children:
                        if sibling.fieldname == proper_parent_name:
                            grandchildren_to_move.append((grandchild, sibling))
                            break
            
            # Move grandchildren to proper parents
            for grandchild, proper_parent in grandchildren_to_move:
                if not proper_parent.has_child_with_key(grandchild.key):
                    proper_parent.add_child(grandchild)
                child.remove_child_by_key(grandchild.key)
        
        # Recurse into children
        for child in entity.children:
            self._enforce_mappings_recursive(child)


class HierarchicalTreeBuilder:
    """Main class for building hierarchical tree structures"""
    
    def __init__(self, translations, mappings):
        self.normalizer = StringNormalizer()
        self.type_mapper = FieldTypeMapper()
        self.path_manager = PathManager(self.normalizer)
        self.navigator = EntityTreeNavigator()
        self.translations = translations
        self.mappings = mappings
        
    def build_tree(self, all_doctypes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build the hierarchical tree structure"""
        # Get configurations
        specified_mappings = self.mappings.get_specific_mapping()
        translations = self.translations.get_translations()
        
        # Initialize components
        mapping_manager = MappingManager(specified_mappings)
        entity_factory = EntityFactory(self.normalizer, self.type_mapper, translations)
        doctype_processor = DoctypeProcessor(entity_factory, mapping_manager, all_doctypes)
        mapping_enforcer = MappingEnforcer(mapping_manager, self.navigator, self.normalizer)
        
        # Build initial tree
        entities = self._build_initial_tree(all_doctypes, mapping_manager, doctype_processor)
        
        # Enforce mappings
        mapping_enforcer.enforce_mappings(entities)
        
        # Remove children from root that should only be children
        entities = self._remove_children_from_root(entities, mapping_manager)
        
        # Update all paths
        self.path_manager.update_all_paths(entities)
        
        # Convert to dictionary format
        return [entity.to_dict() for entity in entities]
    
    def _build_initial_tree(self, all_doctypes: Dict[str, Any], 
                           mapping_manager: MappingManager,
                           doctype_processor: DoctypeProcessor) -> List[Entity]:
        """Build the initial tree structure"""
        entities = []
        
        # Process root doctypes (those without mandatory parents)
        for doctype_name in all_doctypes.get("all_doctypes", {}).keys():
            if not mapping_manager.has_mandatory_parent(doctype_name):
                entity = doctype_processor.process_doctype(doctype_name, is_root=True)
                if entity:
                    entities.append(entity)
        
        # Process any remaining doctypes
        for doctype_name in all_doctypes.get("all_doctypes", {}).keys():
            if doctype_name not in doctype_processor.processed_doctypes:
                entity = doctype_processor.process_doctype(doctype_name, is_root=True)
                if entity:
                    entities.append(entity)
        
        return entities
    
    def _remove_children_from_root(self, entities: List[Entity], 
                                  mapping_manager: MappingManager) -> List[Entity]:
        """Remove entities from root that should only be children"""
        children_to_remove = mapping_manager.get_children_to_remove_from_root()
        return [entity for entity in entities if entity.key not in children_to_remove]


class FileManager:
    """Handles file I/O operations"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {e}")
            raise
    
    @staticmethod
    def save_json(data: Any, file_path: str) -> None:
        """Save data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved data to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON to {file_path}: {e}")
            raise


# def main():
#     """Main entry point"""
#     try:

#         processor = get_doctypes.DoctypeProcessor()
#         all_doctypes = processor.process_doctypes()

#         # Build tree
#         builder = HierarchicalTreeBuilder()
#         hierarchical_data = builder.build_tree(all_doctypes)
        
#         # Save result
#         FileManager.save_json(hierarchical_data, "output/hierarquical_doctypes_refactored.json")
        
#         logger.info("Hierarchical tree built successfully!")
        
#     except Exception as e:
#         logger.error(f"Error building hierarchical tree: {e}")
#         raise


# if __name__ == "__main__":
#     main()