import api_client 
import os
import json_to_hierarquical
import api_client_data

def get_main_doctypes_with_fields(api_base_url, api_token): 
    """
    Função para buscar os DocTypes principais e seus campos.
    """

    doctypes_with_fields = {} 

    # Buscar doctypes principais
    all_doctypes = api_client.get_arteris_doctypes(api_base_url, api_token)
    if all_doctypes is None:
        return None # Retorna None para indicar falha

    # Buscar os DocFields para cada DocType
    for doc in all_doctypes:
        doctype_name = doc.get("name")
        docfields = api_client.get_docfields_for_doctype(api_base_url, api_token, doctype_name)
        if docfields is not None:
            doctypes_with_fields[doctype_name] = docfields
        else:
            doctypes_with_fields[doctype_name] = None # Marca erro

    return doctypes_with_fields

def get_child_doctypes_with_fields(api_base_url, api_token): 
    """
    Função para buscar os DocTypes filhos e seus campos.
    """

    doctypes_with_fields = {} 

    # Buscar doctypes filhos
    all_doctypes_child = api_client.get_arteris_doctypes_child(api_base_url, api_token)
    if all_doctypes_child is None:
        return None # Retorna None para indicar falha

    # Buscar os DocFields para cada DocType
    for doc in all_doctypes_child:
        doctype_name = doc.get("name")
        docfields = api_client.get_docfields_for_doctype(api_base_url, api_token, doctype_name, True)
        if docfields is not None:
            doctypes_with_fields[doctype_name] = docfields
        else:
            doctypes_with_fields[doctype_name] = None # Marca erro

    return doctypes_with_fields

def get_parent_mapping(doctypes_with_fields):
    """
    Função para mapear os DocTypes filhos para seus respectivos pais.
    """

    child_parent_mapping = [] # Lista para mapear child -> parent

    # Itera sobre cada DocType que pode ser um "Parent"
    for doctype_name, fields in doctypes_with_fields.items():
        if not fields:
            continue # Não é um erro, apenas não tem campos de tabela

        # Percorre a lista de dicionários 'fields'
        for f in fields:
            # Verifica se o item tem um fieldname e se o fieldtype é "Table"
            # if (f.get("fieldtype") == "Table" or f.get("fieldtype") == "Link") f.get("fieldname") and f.get("options"): # Referencia curcular por conta do link
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
    Função para processar os DocTypes e seus campos.
    """

    # Obtém a URL base e o token das variáveis de ambiente
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    print("\n--- Iniciando Mapeamento de DocTypes e Fields ---")
    print(f"Base URL: {api_base_url}")
    print(f"Token: {api_token}")

    # Lista para armazenar os DocTypes e seus campos
    main_doctypes = get_main_doctypes_with_fields(api_base_url, api_token)

    # Lista para armazenar os DocTypes filhos e seus campos
    child_doctypes = get_child_doctypes_with_fields(api_base_url, api_token)

    # Uniao de todos os DocTypes
    all_doctypes = main_doctypes.copy()
    all_doctypes.update(child_doctypes) # Atualiza o dicionário com os DocTypes filhos

    parents_mapping = get_parent_mapping(all_doctypes)

    return {
        "main_doctypes": main_doctypes,
        "child_doctypes": child_doctypes,
        "all_doctypes": all_doctypes,
        "parents_mapping": parents_mapping
    }

def get_hierarchical_doctype_structure():
    """"
    Função para obter a estrutura hierárquica dos DocTypes.
    Retorna um dicionário JSON com a estrutura hierárquica.
    """

    print("\n--- Iniciando Geração Interna V2 ---")

    doctypes = process_doctypes() 

    print("\n--- Criar estrutura hierárquica ---")
    hierarquical_json = json_to_hierarquical.create_hierarchical_doctype_structure(
        doctypes["all_doctypes"],
        doctypes["parents_mapping"]
    )
    return hierarquical_json

def get_data():
    """
    Recurperar os dados do Framework
    """

    doctypes = process_doctypes() 

    # Obtém a URL base e o token das variáveis de ambiente
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    # Obtem os IDs dos DocTypes
    doctypes_with_keys = []
    for doctype in doctypes["main_doctypes"]:
        doctype_name = doctype.get("name")
        if doctype_name:
            keys = api_client.get_keys(api_base_url, api_token, doctype_name)
            doctypes_with_keys.append({"doctype": doctype_name, "keys": keys})


    # Obtem a lista de dados dos DocTypes
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
    