import json
import re


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

def search_fieldname_path(data, doctype_name, field_name):
    """
    Search doctype fieldname path
    """
    path = None

    def traverse(node, path = None):
        
        if path:
            return path

        # Adiciona o doctype atual se for do tipo 'doctype'
        if node.get("type") == "doctype" and node.get("fieldname") == doctype_name:
            # Percorre os filhos recursivamente
            for child in node.get("children", []):
                if child.get("fieldname") == field_name:
                    path = child.get("path")  
                    return path                
        else:
            for child in node.get("children", []):
                path = traverse(child, path)
        if path:
            return path

    # Inicia a recursão para cada nó na raiz
    for root in data:
        path = traverse(root, path)
        if path:
            return path

def data_to_engine(doctype_tree, formulas, all_doctype_data, childs_name = "childs"):
    """
    Load tree data map to engine
    """

    result = []
    paths = []
    doctypes_index = {}

    def add_path_to_list(path):
        if not path in paths:
            print(path)
            paths.append(path)        

    def get_doctype_data(doctype_name):
        print(f"Get doctype data: {doctype_name}")
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
                "creation": d["creation"],
                "fields": [],
                childs_name: []
            }

            # Percorre os nos
            for n in nodes:

                # Add path to list
                add_path_to_list(n["path"])
            
                # Doctype desce um nivel
                if n["type"] == "doctype":
                    if n["fieldname_data"]:
                        # Dado de mapeamento especifico
                        doctype_data_item = d[n["fieldname_data"]]
                        # if len(doctype_data_item) == 0:
                        #     continue
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

        # Sem dados, informar campos e null, para evitar ficar sem paths
        if len(doctype_data[index:]) == 0:

            engine_data_item = {
                "id": None,
                "creation": None,
                "fields": [],
                childs_name: []
            }

            # Percorre os nos
            for n in nodes:

                # Add path to list
                add_path_to_list(n["path"])
            
                # Doctype desce um nivel
                if n["type"] == "doctype":
                    # if n["fieldname_data"]:
                    #     # Dado de mapeamento especifico
                    #     doctype_data_item = d[n["fieldname_data"]]
                    #     if len(doctype_data_item) == 0:
                    #         continue
                    # else:
                    #     # Dado vinculado ao registro do doctype
                    #     doctype_data_item = get_doctype_data(n["fieldname"])

                    # Lista vazia
                    doctype_data_item = []

                    # Adiciona os registros ao cabeçalho
                    if len(engine_data_item) != 0:
                        head_data_item["data"].append(engine_data_item)
                    
                    # Zera os registros para evitar duplicidade
                    engine_data_item = {}

                    # Descce o nivel para carga
                    traverse_doctype(n, head_data_item, doctype_data_item, path, True)

                else:
                    # Cria o registro de dados
                    engine_data_item["fields"].append({
                        "path": n["path"],
                        "type": n["type"],
                        "value": None
                    })
            # Incluir dados mesmo que vazios
            if len(engine_data_item) != 0:
                head_data_item["data"].append(engine_data_item)

    def traverse_doctype(node, head_data_item = None, doctype_data = None, path = None, reset_index = False):

        # Add path to list
        add_path_to_list(node["path"])

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
            head_data_item["data"][-1][childs_name].append(new_head_data_item)
        
        traverse_doctype_data(node["children"], new_head_data_item, doctype_data, node["path"], reset_index)

        # Final da recursao
        if not head_data_item:
            result.append(new_head_data_item)

    def replace_paths(obj, references):
        """
        Replaces values in a complex JSON using the provided reference dictionary.
        
        Args:
            obj: The JSON object to be processed
            references: The JSON object containing the mapping in the format {"referencia": [{"e00100v": "asset", ...}]}
            
        Returns:
            The object with replaced values
        """
        ref_dict = references["referencia"][0]

        def replace_formulas(formulas):
            
            for f in formulas:
                # Replacements in formulas and other more complex strings
                words = f["value"].split()
                for i, word in enumerate(words):
                    if word in  original_path:
                        words[i] = code
                    elif original_path in word:
                        # Attempt to replace only complete occurrences
                        for operator in [' ', '(', ')', '+', '-', '*', '/', '=', ',', '==', '>=', '<=']:
                            word = word.replace(original_path + operator, code + operator)
                            word = word.replace(operator + original_path, operator + code)
                        words[i] = word
                
                return ' '.join(words)
        
        # Internal recursive function to make replacements
        def replace_recursive(item):  

            if isinstance(item, list):             
                for i in item:
                    replace_recursive(i)

            if "data" in item:
                for i in item["data"]:
                    replace_recursive(i)

            if childs_name in item:
                for i in item[childs_name]:
                    replace_recursive(i)          

            if "fields" in item:
                for i in item["fields"]:
                    replace_recursive(i)     

            if "formulas" in item:
                for i in item["formulas"]:
                    replace_recursive(i)             

            # Change paths values
            for code, original_path in ref_dict.items():            

                # Special handling for formula fields
                if "path" in item and "value" in item and "update" in item:

                    # Replace in the formula string (value)
                    if isinstance(item["value"], str):
                        value = item["value"]
                        
                        # Padrão para encontrar a palavra completa ou com operadores específicos
                        pattern = r'(^|\W)(' + re.escape(original_path) + r')(\W|$)'
                        
                        # Função para substituir mantendo os delimitadores
                        def replace_match(match):
                            prefix = match.group(1)  # Primeiro grupo (delimitador inicial ou início da string)
                            matched_word = match.group(2)  # Segundo grupo (a palavra que queremos substituir)
                            suffix = match.group(3)  # Terceiro grupo (delimitador final ou fim da string)
                            return prefix + code + suffix
                        
                        # Aplicar a substituição
                        value = re.sub(pattern, replace_match, value)
                        
                        # Atualizar o valor no item
                        item["value"] = value                    
                                    
                # Special case for the "path" field
                if "path" in item:
                    value = item["path"]
                    if value == original_path:
                        item["path"] = code

            return item
        
        # Recursive 
        return replace_recursive(obj)
        
    # Inicia a recursão para cada nó na raiz
    for root in doctype_tree:
        traverse_doctype(root)

    # Monta as referencias
    references = {
        "referencia": [{}]
    }
    for index, p in enumerate(paths):
        references["referencia"][0][f"e{index:05d}v"] = p

    # Substitui os paths pelas referencias
    # Ordena a lista paths
    sorted_items =  {"referencia": [dict(sorted(references["referencia"][0].items(), key=lambda x: len(x[1]), reverse=True))]}
    result_new_paths = replace_paths(result, sorted_items)
    
    # Monta o objeto final
    engine_data = {
        "referencia": references["referencia"],
        "dados": result_new_paths
    }

    return engine_data

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
    with open("output/hierarquical_doctypes.json", "r", encoding="utf-8") as file:
        doctype_tree = json.load(file)        

    # Load all_doctype_doc
    with open("data/all_doctypes.json", "r", encoding="utf-8") as file:
        all_doctype_data = json.load(file)        

    # Call the function with the loaded data
    engine_data = data_to_engine(doctype_tree, formulas, all_doctype_data, "data")
    save_json_file(engine_data, "output/tree_data.json")

    print("Dados gravados em output/tree_data.json")

    # # Print the result
    # print(json.dumps(doctypes_paths, indent=4, ensure_ascii=False))
