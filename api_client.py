import requests
import json

def get_arteris_doctypes(api_base_url, api_token):
    """
    Busca todos os DocTypes da API Arteris que pertencem ao módulo 'Arteris' e não são do tipo Child Item .

    Args:
        api_base_url (str): A URL base da API de recursos (ex: 'https://host/api/resource').
        api_token (str): O token de autorização no formato 'token key:secret'.

    Returns:
        list or None: Uma lista de dicionários, onde cada dicionário representa um DocType
                      encontrado (contendo pelo menos a chave 'name').
                      Retorna None em caso de erro na requisição ou na decodificação JSON.
    """
    doctype_url = f"{api_base_url}/DocType"
    params = {
        # Filtra para buscar apenas DocTypes do módulo específico 'Arteris' e que não são tabelas (Child Item)
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"],["name","like","%Meas%"]])
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"],["name","=","Asset"]])
        "filters": json.dumps([["module", "=", "Arteris"],["istable","!=","1"]])
    }
    headers = {"Authorization": api_token}

    try:
        print(f"Buscando DocTypes ...")
        response = requests.get(doctype_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Lança HTTPError para respostas 4xx/5xx
        data = response.json()
        print("Lista de DocTypes recebida com sucesso!")
        # Retorna diretamente a lista contida na chave 'data' da resposta JSON
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        print(f"Erro ao buscar DocTypes da API: {e}")
        return None
    except json.JSONDecodeError:
        # Captura erro se a resposta não for um JSON válido
        print("Erro ao decodificar a resposta JSON dos DocTypes.")
        return None
    
def get_arteris_doctypes_child(api_base_url, api_token):
    """
    Busca todos os DocTypes da API Arteris que pertencem ao módulo 'Arteris' do tipo Child Item .

    Args:
        api_base_url (str): A URL base da API de recursos (ex: 'https://host/api/resource').
        api_token (str): O token de autorização no formato 'token key:secret'.

    Returns:
        list or None: Uma lista de dicionários, onde cada dicionário representa um DocType
                      encontrado (contendo pelo menos a chave 'name').
                      Retorna None em caso de erro na requisição ou na decodificação JSON.
    """

    doctype_url = f"{api_base_url}/DocType"
    params = {
        # Filtra para buscar apenas DocTypes do módulo específico 'Arteris' e que não são tabelas (Child Item)
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"],["name","like","%Meas%"]])
        # "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"],["name","=","Asset Operator"]])
        "filters": json.dumps([["module", "=", "Arteris"],["istable","=","1"]])
    }
    headers = {"Authorization": api_token}

    try:
        print(f"Buscando DocTypes ...")
        response = requests.get(doctype_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Lança HTTPError para respostas 4xx/5xx
        data = response.json()
        print("Lista de DocTypes recebida com sucesso!")
        # Retorna diretamente a lista contida na chave 'data' da resposta JSON
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        print(f"Erro ao buscar DocTypes da API: {e}")
        return None
    except json.JSONDecodeError:
        # Captura erro se a resposta não for um JSON válido
        print("Erro ao decodificar a resposta JSON dos DocTypes.")
        return None    

def get_docfields_for_doctype(api_base_url, api_token, doctype_name, child=False):
    """
    Busca os DocFields (metadados dos campos) para um DocType específico.

    Filtra para excluir campos do tipo 'Section Break' e 'Column Break' e
    seleciona apenas 'fieldname', 'label' e 'fieldtype'.

    Args:
        api_base_url (str): A URL base da API de recursos.
        api_token (str): O token de autorização.
        doctype_name (str): O nome do DocType para o qual buscar os campos.

    Returns:
        list or None: Uma lista de dicionários, onde cada dicionário representa um DocField
                      (contendo 'fieldname', 'label', 'fieldtype').
                      Retorna None em caso de erro na requisição ou na decodificação JSON.
                      Retorna uma lista vazia se nenhum campo for encontrado após os filtros.
    """

    docfield_url = f"{api_base_url}/DocField"
    params = {
        # Define quais campos do DocField queremos retornar
        # Se child=True adiciona "parent" aos fields
        "fields": json.dumps(["fieldname", "label", "fieldtype", "options", "hidden"] + (["parent"] if child else [])),
        # Define os filtros:
        "filters": json.dumps([
            ["parent", "=", doctype_name],          # Campo pertence ao DocType pai especificado
            ["fieldtype", "!=", "Section Break"], # Exclui quebras de seção
            ["fieldtype", "!=", "Column Break"],  # Exclui quebras de coluna
            ["fieldtype", "!=", "Tab Break"]
        ]),
        # Parâmetro 'parent' parece ser necessário pela API DocField,
        # mesmo já filtrando por 'parent' em 'filters'.
        "parent": "DocType"
    }
            
    headers = {"Authorization": api_token}

    try:
        print(f"Buscando DocFields para: {doctype_name}...")
        response = requests.get(docfield_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Lança HTTPError para respostas 4xx/5xx
        data = response.json()
        docfields = data.get("data", [])
        print(f"DocFields para {doctype_name} recebidos com sucesso!")
        # Retorna a lista de campos da chave 'data'
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        print(f"Erro ao buscar DocFields para {doctype_name}: {e}")
        return None
    except json.JSONDecodeError:
        # Captura erro se a resposta não for um JSON válido
        print(f"Erro ao decodificar a resposta JSON dos DocFields para {doctype_name}.")
        return None
