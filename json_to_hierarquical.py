import unicodedata
import re

def normalize_string(text):
    """Normaliza uma string: substitui acentos por caracteres base (preservando maiúsculas/minúsculas)
       e substitui espaços/não alfanuméricos por underscore."""
    
    if not text:
        return text
    try:
        text_str = str(text)
        # Transliterar acentos para caracteres base (e.g., á -> a, Ç -> C)
        # NFKD decompõe caracteres como 'ç' em 'c' e um acento combinatório.
        nfkd_form = unicodedata.normalize('NFKD', text_str)
        # Remove os acentos combinatórios, preservando a letra base e sua caixa.
        sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # Substituir espaços e outros caracteres não alfanuméricos (exceto underscore) por underscore
        # O padrão \W corresponde a qualquer caractere que não seja letra, número ou underscore.
        # Aplicamos isso na string já sem acentos, mas com a caixa original preservada.
        normalized = re.sub(r'\W+', '_', sem_acentos)
        # Remover underscores múltiplos que podem ter sido criados
        normalized = re.sub(r'_+', '_', normalized)
        # Remover underscores no início ou fim, se houver
        normalized = normalized.strip('_')
        # Caso a string fique vazia (ex: só tinha caracteres não alfanuméricos), retorna um fallback.
        # Este fallback ainda usa lower() por simplicidade, mas a lógica principal preserva a caixa.
        if not normalized:
             normalized = re.sub(r'\s+', '_', text_str.lower()).strip('_') # Fallback simples
             if not normalized:
                 # Se ainda vazio, retorna um valor genérico para evitar string vazia
                 return "string_normalizada_fallback"
        return normalized
    except Exception as e:
        print(f"Erro ao normalizar string '{text}': {e}")
        # Em caso de erro inesperado, retorna uma versão simplificada (minúscula, espaços por _)
        return re.sub(r'\s+', '_', str(text).lower()).strip('_')

def map_field_type(field_type, key=None):
    """
    Mapeia tipos de campo do DocType para tipos genéricos.

    Args:
        field_type (str): Tipo de campo do DocType
        key (str, optional): Nome do campo, usado para campos especiais

    Returns:
        str: Tipo genérico (string, numeric, datetime, boolean, etc.)
    """

    # Mapeamento de tipos de campo para tipos genéricos
    type_mapping = {
        # Tipos de texto
        "Data": "string",
        "Small Text": "string",
        "Text": "string",
        "Text Editor": "string",
        "Code": "string",
        "Link": "string",
        "Select": "string",
        "Read Only": "string",

        # Tipos numéricos
        "Int": "numeric",
        "Float": "numeric",
        "Currency": "numeric",
        "Percent": "numeric",

        # Tipos de data/hora
        "Date": "datetime",
        "Datetime": "datetime",
        "Time": "datetime",

        # Tipos booleanos
        "Check": "boolean",

        # Outros tipos
        "Table": "table", # Mantido para referência, mas ignorado em process_attributes
        "Attach": "file",
        "Attach Image": "image",
        "Signature": "image",
        "Color": "string",
        "Geolocation": "geolocation"
    }

    # Campos especiais que têm tipos específicos
    special_fields = {
        "creation": "datetime",
        "modified": "datetime",
        "docstatus": "numeric",
        "idx": "numeric"
    }

    # Verificar se é um campo especial
    if field_type in type_mapping:
        return type_mapping[field_type]
    elif key in special_fields:
        return special_fields[key]
    else:
        # Retorna 'string' como padrão se o tipo não for mapeado
        return "string"

def process_attributes(fields_metadata):
    """
    Processa os atributos da entidade a partir dos metadados dos campos.

    Args:
        fields_metadata (list): Metadados dos campos
        is_child (bool): Indica se é uma entidade filha

    Returns:
        list: Lista de atributos processados (sem o campo 'value')
    """
    attributes = []

    # Processar cada campo nos metadados
    for field in fields_metadata:
        field_name = field.get("fieldname")
        field_type = field.get("fieldtype")
        field_hidden = field.get("hidden")

        # Ignorar campos do tipo Table (serão tratados como entidades separadas)
        if field_type == "Table":
            continue
        if field_hidden == 1: # Ignorar campos ocultos
            continue
        if field_name[:2] == "f_" or field_name[:3] == "fm_": # Ignorar campos de fórmula
            continue
        # Ignorar campos internos/específicos que não devem ser atributos diretos,
        # incluindo 'parent', que é tratado separadamente em create_entity.
        if field_name in [
            "name", 
            "owner", 
            "creation", 
            "modified", 
            "modified_by",
            "docstatus",
            "idx",
            "parentfield",
            "parenttype",
            "doctype",
            "parent"]: # Adicionado 'parent' à lista de ignorados
            continue

        # Mapear tipo de campo para tipo genérico
        generic_type = map_field_type(field_type, field_name)

        # Criar atributo sem o campo 'value'
        attribute = {
            "key": field_name,
            "type": generic_type,
            "description": normalize_string(field.get("label")) if field.get("label") else None
        }
        attributes.append(attribute)

    return attributes

def create_entity(
        doctype_name, 
        fields_metadata, 
        is_child=False, 
        parent_doctype=None):
    """
    Cria uma entidade a partir dos metadados dos campos.

    Args:
        doctype_name (str): Nome do DocType
        fields_metadata (list): Metadados dos campos do DocType
        is_child (bool): Indica se é uma entidade filha
        parent_doctype (str): Nome do DocType pai, se for uma entidade filha

    Returns:
        dict: Entidade no formato especificado
    """
    # Processar atributos (sem valores)
    attributes = process_attributes(fields_metadata)

    # Adiciona o atributo 'name' como primeiro item da lista
    attributes.insert(0, {"key": "name", "type": "string"})

    # Adicionar atributo 'parent' explicitamente para entidades filhas
    if is_child and parent_doctype:
        # Verifica se o atributo 'parent' já existe (caso venha dos metadados)
        parent_attr_exists = any(attr['key'] == 'parent' for attr in attributes)
        if not parent_attr_exists:
             attributes.append({
                 "key": "parent",
                 "type": "string", # Assumindo que a referência ao pai é uma string (ID/nome)
             })

    # Criar relacionamentos (apenas para entidades filhas, apontando para o pai)
    relationships = []
    if is_child and parent_doctype:
        relationships.append({
            "sourceKey": "parent", # A chave na entidade filha que aponta para o pai
            "destinationEntity": parent_doctype, # O tipo da entidade pai
            "destinationKey": "name" # A chave na entidade pai (geralmente 'name')
        })

    # Adicionar relacionamentos para campos do tipo Link
    for field in fields_metadata:
        if field.get("fieldtype") == "Link":
            field_name = field.get("fieldname")
            destination_entity = field.get("options")
            # Ignorar links para Web Page ou Report, ou se não houver 'options'
            if destination_entity and destination_entity not in ["Web Page", "Report"]:
                 # Evitar adicionar relacionamento duplicado se já existir (ex: parent)
                 is_duplicate = any(
                     rel["sourceKey"] == field_name and rel["destinationEntity"] == destination_entity
                     for rel in relationships
                 )
                 if not is_duplicate:
                    relationships.append({
                        "sourceKey": field_name,
                        "destinationEntity": destination_entity,
                        "destinationKey": "name" # Assumindo que a chave de destino é 'name'
                    })

    # Criar estrutura da entidade
    entity = {
        "entity": {
            "type": doctype_name,
            "description": normalize_string(doctype_name),
            "attributes": attributes,
            "relationships": relationships
        }
    }

    return entity

def process_fields_for_hierarchy(fields_metadata, all_doctypes_data, process_nested_relationships=True):
    """
    Processa metadados de campos para a estrutura hierárquica com recursão controlada.

    Args:
        fields_metadata (list): Metadados dos campos do DocType atual.
        all_doctypes_data (dict): Dicionário completo {doctype_name: fields_metadata_list}.
        process_nested_relationships (bool): Se True, processa Links/Tabelas neste nível.
                                             Se False, ignora Tabelas e trata Links como campos normais.

    Returns:
        list: Lista de nós representando campos ou DocTypes vinculados.
    """
    processed_nodes = []
    if not isinstance(fields_metadata, list):
        print(f"Aviso: Metadados de campos inválidos recebidos por process_fields_for_hierarchy.")
        return processed_nodes

    for field in fields_metadata:
        if not isinstance(field, dict):
            continue

        field_name = field.get("fieldname")
        field_type = field.get("fieldtype")
        field_hidden = field.get("hidden")
        label = field.get("label")
        options = field.get("options")

        # --- Ignorar campos irrelevantes ---
        if not field_name or not field_type:
            continue
        if field_hidden == 1: # Ignorar campos ocultos
            continue
        if field_name.startswith("f_") or field_name.startswith("fm_"): # Ignorar campos de fórmula
            continue
        if field_name in ["owner", "creation", "modified", "modified_by",
                          "docstatus", "idx", "parentfield", "parenttype", "doctype",
                          "parent"]:
            continue

        # --- Lógica de Processamento Condicional (Baseada em process_nested_relationships) ---

        # 1. Processar Links no nível principal?
        if field_type == "Link" and process_nested_relationships:
            destination_entity = options
            if destination_entity and destination_entity not in ["Web Page", "Report"]:
                # Obter metadados do DocType vinculado
                linked_fields_metadata = all_doctypes_data.get(destination_entity, [])
                # Chamar recursivamente SEM processar mais relações aninhadas
                linked_fields = process_fields_for_hierarchy(
                    linked_fields_metadata, all_doctypes_data, process_nested_relationships=False
                )
                # Criar nó para o DocType vinculado
                normalized_description = normalize_string(destination_entity)
                linked_doctype_node = {
                    "key": normalized_description, # Key continua usando a descrição normalizada
                    "description": destination_entity, # Description usa o nome original do doctype
                    "fieldname": destination_entity, # Nova propriedade fieldname
                    "type": "doctype",
                    "children": linked_fields # Adiciona os campos processados do DocType vinculado
                }
                processed_nodes.append(linked_doctype_node)
                continue # Pula para o próximo field

        # 2. Ignorar Tabelas se não estiver no nível principal?
        if field_type == "Table" and not process_nested_relationships:
            continue 
        
        # 3. Ignorar Tabelas no nível principal (serão tratadas pelo child_parent_mapping)
        if field_type == "Table" and process_nested_relationships:
             continue # Ignora tabelas no nível principal

        # --- Lógica Padrão para outros campos (ou Links/Tabelas não tratados/ignorados acima) ---
        generic_type = map_field_type(field_type, field_name)
        normalized_label = normalize_string(label) if label else None

        field_node = {
            "key": normalized_label if normalized_label else field_name, # Key continua usando a descrição normalizada
            "description": label if label else field_name, # Description usa o label original (ou field_name)
            "fieldname": field_name, # Nova propriedade fieldname
            "type": generic_type
        }
        
        processed_nodes.append(field_node)

    return processed_nodes

def add_paths_recursively(node, current_path="", visited_nodes=None):
    """
    Adiciona recursivamente a propriedade 'path' a cada nó na hierarquia.

    Args:
        node (dict): O nó atual a ser processado.
        current_path (str): O caminho acumulado até o nó pai.
    """

    if visited_nodes is None:
        visited_nodes = set()  # Inicializa o conjunto de nós visitados se não for fornecido

    # Removida a declaração global de visited_nodes
    if "name" not in node:
        return

    node_name = node.get("name")

    if node_name in visited_nodes:
        return
    visited_nodes.add(node_name)
    if not isinstance(node, dict):
        return

    node_key = node.get("key")
    if not node_key:
        return # Não é possível determinar o caminho sem uma chave

    # Calcula o novo caminho para este nó
    new_path = f"{current_path}.{node_key}" if current_path else node_key

    # Adiciona o path apenas se não for um nó raiz (current_path existe)
    if current_path:
        node["path"] = new_path

    # Processa os filhos recursivamente
    children = node.get("children")
    if isinstance(children, list):
        for child in children:
            add_paths_recursively(child, new_path, visited_nodes)

def create_hierarchical_doctype_structure(doctypes_with_fields, child_parent_mapping):
    visited_nodes = set()  # Inicializa o conjunto de nós visitados
    if visited_nodes is None:
        visited_nodes = set()  # Inicializa o conjunto de nós visitados se não for fornecido
    """
    Cria uma estrutura JSON hierárquica de DocTypes e seus campos (Refatorada v2).

    Utiliza _process_fields_for_hierarchy com recursão controlada.

    Args:
        doctypes_with_fields (dict): Dicionário {doctype_name: fields_metadata_list}.
        child_parent_mapping (list): Lista de dicts {"child": child_name, "parent": parent_name}.

    Returns:
        list: Lista contendo os nós DocType raiz, com filhos (campos e DocTypes) aninhados.
              Retorna lista vazia em caso de erro nos inputs principais.
    """
    
    if child_parent_mapping is None:
        child_parent_mapping = []

    nodes = {}
    child_doctypes = set()

    all_doctype_names = list(doctypes_with_fields.keys()) # Para iteração segura se modificarmos o dict
    for doctype_name in all_doctype_names:
        if not doctype_name: 
            continue
        fields_metadata = doctypes_with_fields.get(doctype_name, [])

        if doctype_name not in nodes:
            normalized_description = normalize_string(doctype_name)
            nodes[doctype_name] = {
                "key": normalized_description, # Key continua usando a descrição normalizada
                "description": doctype_name, # Description usa o nome original do doctype
                "fieldname": doctype_name, # Nova propriedade fieldname
                "type": "doctype",
                "children": process_fields_for_hierarchy(fields_metadata, doctypes_with_fields, True)
            }
        else:
             # Se o nó já existe (criado por mapeamento), processa e adiciona/atualiza os campos
             current_children = nodes[doctype_name].get("children", [])
             processed_fields = process_fields_for_hierarchy(fields_metadata, doctypes_with_fields, True)
             # Evita duplicar campos se o DocType for processado múltiplas vezes (improvável, mas seguro)
             existing_field_keys = {child.get("key") for child in current_children if child.get("type") != "doctype"}
             for field_node in processed_fields:
                 if field_node.get("key") not in existing_field_keys:
                     current_children.append(field_node)
             nodes[doctype_name]["children"] = current_children


    # Processar mapeamento pai-filho para aninhar DocTypes ---
    # Garante que as relações existam:
    # - Contract -> Contract Item
    # - Contract -> Contract Measurement
    # - Contract -> Contract Measurement Record
    specific_mapping = {"child": "Contract Item", "parent": "Contract"}
    specific_mapping = {"child": "Contract Measurement", "parent": "Contract"}
    specific_mapping = {"child": "Contract Measurement Record", "parent": "Contract"}
    mapping_exists = any(
        m.get("child") == specific_mapping["child"] and m.get("parent") == specific_mapping["parent"]
        for m in child_parent_mapping if isinstance(m, dict)
    )
    if not mapping_exists:
        child_parent_mapping.append(specific_mapping) # Modifica a lista diretamente (ou uma cópia se preferir imutabilidade)

    # Continua o processamento dos mapeamentos (incluindo o adicionado, se for o caso)
    for mapping in child_parent_mapping:
        if not isinstance(mapping, dict): continue

        child_name = mapping.get("child")
        parent_name = mapping.get("parent")        

        if not child_name or not parent_name:
            continue

        # Garante que nós pai e filho existam
        for name in [parent_name, child_name]:
            if name not in nodes:
                node_fields_metadata = doctypes_with_fields.get(name, [])
                normalized_description = normalize_string(name)
                nodes[name] = {
                    "key": normalized_description, # Key continua usando a descrição normalizada
                    "description": name, # Description usa o nome original do doctype/campo
                    "fieldname": name, # Nova propriedade fieldname
                    "type": "doctype",
                    "children": process_fields_for_hierarchy(node_fields_metadata, doctypes_with_fields, True)
                }

        # Apenas se ambos os nós realmente existem (foram encontrados ou criados)
        if parent_name in nodes and child_name in nodes:
            child_node_ref = nodes[child_name]
            if child_node_ref.get("name") in visited_nodes:
                continue
            parent_node_children = nodes[parent_name]["children"]

            is_already_child = any(child is child_node_ref for child in parent_node_children if isinstance(child, dict) and child.get("type") == "doctype")

            if not is_already_child:
                parent_node_children.append(child_node_ref)

            child_doctypes.add(child_name)

    for node in nodes.values():
        print(f"Info: Processando nó '{node.get('description')}'...")
        # Verifica se é um nó doctype e se possui a chave 'children'
        if isinstance(node, dict) and node.get("type") == "doctype" and "children" in node:
            children_list = node["children"]
            if isinstance(children_list, list):
                # Ordena a lista 'children' in-place
                # Chave de ordenação: 0 para campos (não doctype), 1 para doctypes
                children_list.sort(key=lambda child: 0 if isinstance(child, dict) and child.get("type") != "doctype" else 1)

    # Identificar e coletar nós raiz
    root_nodes = []
    all_processed_doctypes = list(nodes.keys())

    for doctype_name in all_processed_doctypes:
        if doctype_name not in child_doctypes: # Se não for filho de ninguém, é raiz
             root_nodes.append(nodes[doctype_name])

    # Adicionar a propriedade 'path' recursivamente 
    for root_node in root_nodes:
        add_paths_recursively(root_node) # Inicia a recursão para cada raiz

    return {"entities": root_nodes}


