import json


def map_all_paths(data):    
    """
    Returns a list of doctypes and their paths from a hierarchical structure.
    :param data: Hierarchical list of doctypes.
    :return: List of dictionaries with 'doctype' and 'paths'.
    """
    result = []

    def traverse(node, current_path, doctype):
        # Adiciona o doctype atual se for do tipo 'doctype'

        if node.get("path") in result:
            result[node.get("path")].append(doctype)
        else:
            result[node.get("path")] = [doctype]

        # Percorre os filhos recursivamente
        for child in node.get("children", []):
            traverse(child, current_path + [node["fieldname"]], node.get("fieldname"))

    # Inicia a recursão para cada nó na raiz
    for root in data:
        traverse(root, [], root["fieldname"])

    with open("output/map_all_paths.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    return result


def map_doctype_paths(data):    
    """
    Returns a list of doctypes and their paths from a hierarchical structure.
    :param data: Hierarchical list of doctypes.
    :return: List of dictionaries with 'doctype' and 'paths'.
    """
    result = []

    def traverse(node, current_path):
        # Adiciona o doctype atual se for do tipo 'doctype'
        if node.get("type") == "doctype":
            result.append({"doctype": node["fieldname"], "paths": [node["path"]]})

        # Percorre os filhos recursivamente
        for child in node.get("children", []):
            traverse(child, current_path + [node["fieldname"]])

    # Inicia a recursão para cada nó na raiz
    for root in data:
        traverse(root, [])

    with open("output/map_doctype_paths.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    return result

def search_fieldname_path(data, doctype_name, field_name = None):
    """
    Search doctype fieldname path
    """
    def traverse(node, current_path):

        if field_name:
            if node.get("fieldname") == field_name:
                return node.get("path") 

        # Adiciona o doctype atual se for do tipo 'doctype'
        if node.get("type") == "doctype" and node.get("fieldname") == doctype_name:
            # Percorre os filhos recursivamente
            for child in node.get("children", []):
                traverse(child, current_path + [node["fieldname"]], field_name)

    # Inicia a recursão para cada nó na raiz
    for root in data:
        traverse(root, [])

def data_to_engine(doctype_tree, formulas, all_doctype_data):
    """
    Load tree data map to engine
    """

    result = []
    doctypes_index = {}

    def get_doctype_data(doctype_name):
        # Get doctype data
        for d in all_doctype_data:
            if doctype_name in d:
                doctype_data = d[doctype_name]
        return doctype_data

    def traverse_doctype_data(nodes, head_data_item, doctype_data, path, reset_index):

        doctypes_index.setdefault(path, 0)
        if reset_index:
            doctypes_index[path] = 0
        index = doctypes_index[path]

        # Percorre os nos de campos da tree
        for d in doctype_data[index:]:

            # Armazena o indice da lista
            doctypes_index[path] += 1
            
            # Cabeçalho do registro
            engine_data_item = {
                "id": d["name"],
                "fields": [],
                "data": []
            }

            # Percorre os nos
            for n in nodes:
            
                # Doctype desce um nivel
                if n["type"] == "doctype":
                    if n["fieldname_data"]:
                        # Dado de mapeamento especifico
                        doctype_data_item = d[n["fieldname_data"]]
                        if len(doctype_data_item) == 0:
                            continue
                    else:
                        # Dado vinculado ao registro do doctype
                        doctype_data_item = get_doctype_data(n["fieldname"])

                    # Adiciona os registros ao cabeçalho
                    if len(engine_data_item) != 0:
                        head_data_item["data"].append(engine_data_item)
                    
                    # Zera os registros para evitar duplicidade
                    engine_data_item = {}

                    # Descce o nivel para carga
                    traverse_doctype(n, head_data_item, doctype_data_item, path, True)

                else:
                    # Previne dados não existentes
                    if n["fieldname"] in d:
                        value = d[n["fieldname"]]
                    else:
                        value = None
                    # Cria o registro de dados
                    engine_data_item["fields"].append({
                        "path": n["path"],
                        "type": n["type"],
                        "value": value
                    })

            # Se houverem dados adicona ao cabeçalho
            if len(engine_data_item) != 0:
                head_data_item["data"].append(engine_data_item)


    def traverse_doctype(node, head_data_item = None, doctype_data = None, path = None, reset_index = False):
        
        # Get doctype data
        if not doctype_data:
            doctype_data = get_doctype_data(node["fieldname"])

        doctype_formulas = []
        # Recupera as formulas para o doctype
        for f in formulas[0]["tableformulas"]:
            if f["groupfielddoctype"]==node["fieldname"]:
                doctype_formulas.append(f)

        # Cria a lista de formulas para o cabeçalho de dados
        engine_formulas = []
        for f in doctype_formulas:

            # Reupera o path para o campo da formula
            path = search_fieldname_path(doctype_tree, f["groupfielddoctype"], f["groupfieldfieldname"])

            # Estrutura de formulas do cabecalho
            engine_formulas.append(
                {
                    "path": path,
                    "value":  f["formula"],
                    "update": {
                        "doctype": f["groupfielddoctype"],
                        "fieldname": f["groupfieldfieldname"]
                    }                            
                }
            )

        # Inicializa cabeçalho
        new_head_data_item = {
            "path": node.get("path"),
            "formulas": engine_formulas,
            "data":[]
        }

        if head_data_item:
            # Filho do ultimo registro
            head_data_item["data"][-1]["data"].append(new_head_data_item)
        
        traverse_doctype_data(node["children"], new_head_data_item, doctype_data, node["path"], reset_index)

        # Final da recursao
        if not head_data_item:
            result.append(new_head_data_item)
            save_json_file(result, "output/tree_data.json")

    # Inicia a recursão para cada nó na raiz
    for root in doctype_tree:
        traverse_doctype(root)

    return result    

def save_json_file(data, file_path):
    """Save JSON data to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    import json

    # Load the hierarchical doctypes JSON file
    with open("data/formula_group.json", "r", encoding="utf-8") as file:
        formulas = json.load(file)

    # Load the hierarchical doctypes JSON file
    with open("output/hierarchical_data.json", "r", encoding="utf-8") as file:
        doctype_tree = json.load(file)        

    # Load all_doctype_doc
    with open("data/all_doctypes.json", "r", encoding="utf-8") as file:
        all_doctype_data = json.load(file)        

    # Call the function with the loaded data
    doctypes_paths = data_to_engine(doctype_tree, formulas, all_doctype_data)

    # Print the result
    print(json.dumps(doctypes_paths, indent=4, ensure_ascii=False))
