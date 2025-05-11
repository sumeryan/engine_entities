import requests
import json

def get_keys(api_base_url, api_token, doctype_name):
    """
    Busca as chaves de um DocType específico na API Arteris.
    Args:
        api_base_url (str): A URL base da API de recursos (ex: 'https://host/api/resource').
        api_token (str): O token de autorização no formato 'token key
        doctype_name (str): O nome do DocType do qual buscar as chaves (ex: 'Asset').
    Returns:
        list or None: Uma lista de strings contendo os valores das chaves do DocType.
                      Retorna None em caso de erro na requisição ou na decodificação JSON.
    """
    resource_url = f"{api_base_url}/{doctype_name}"
    params = {}
    headers = {"Authorization": api_token}

    try:
        response = requests.get(resource_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Lança HTTPError para respostas 4xx/5xx
        data = response.json()
        keys = [item["name"] for item in data.get("data", [])]
        # Retorna a lista de chaves contida na chave 'data' da resposta JSON
        return keys
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        return None
    except json.JSONDecodeError:
        # Captura erro se a resposta não for um JSON válido
        return None

def remove_properties_recursively(data, properties_to_remove):
    """
    Remove propriedades especificadas de um objeto JSON recursivamente.
    
    Args:
        data: O objeto JSON do qual remover as propriedades.
        properties_to_remove: Lista de propriedades a serem removidas.
        
    Returns:
        O objeto JSON com as propriedades removidas.
    """
    if isinstance(data, dict):
        # Remove as propriedades do dicionário atual
        for prop in properties_to_remove:
            if prop in data:
                del data[prop]
        
        # Processa recursivamente todos os valores do dicionário
        for key, value in list(data.items()):
            data[key] = remove_properties_recursively(value, properties_to_remove)
            
    elif isinstance(data, list):
        # Processa recursivamente todos os itens da lista
        for i, item in enumerate(data):
            data[i] = remove_properties_recursively(item, properties_to_remove)
            
    return data

def get_data_from_key(api_base_url, api_token, doctype_name, key):
    """
    Busca os dados de um DocType específico na API Arteris usando uma chave.
    Args:
        api_base_url (str): A URL base da API de recursos (ex: 'https://host/api/resource').
        api_token (str): O token de autorização no formato 'token key
        doctype_name (str): O nome do DocType do qual buscar os dados (ex: 'Asset').
        key (str): A chave do DocType para buscar os dados.
    Returns:
        Um JSON contendo os dados do DocType ou None em caso de erro.
        As seguintes propriedades são removidas do JSON retornado (incluindo em objetos aninhados):
        'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx'
    """
    resource_url = f"{api_base_url}/{doctype_name}/{key}"
    params = {}
    headers = {"Authorization": api_token}

    try:
        print(f"Buscando dados para DocType '{doctype_name}' usando a chave '{key}' em: {resource_url} ...")
        response = requests.get(resource_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Lança HTTPError para respostas 4xx/5xx
        data = response.json()
        # Verifica se a resposta contém dados
        if "data" in data:
            print(f"Dados para '{doctype_name}' com chave '{key}' recebidos com sucesso!")
            
            # Remove as propriedades especificadas recursivamente
            data_filtered = data["data"]
            properties_to_remove = ['owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parentfield' , 'parenttype', 'is_group']
            
            # Aplica a remoção recursiva de propriedades
            data_filtered = remove_properties_recursively(data_filtered, properties_to_remove)
            
            return data_filtered
        else:
            print(f"Nenhum dado encontrado para '{doctype_name}' com chave '{key}'!")
            return None
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        print(f"Erro ao buscar chaves para {doctype_name}: {e}")
        return None
    except json.JSONDecodeError:
        # Captura erro se a resposta não for um JSON válido
        print(f"Erro ao decodificar a resposta JSON das chaves para {doctype_name}.")
        return None    