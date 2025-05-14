import json

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

if __name__ == "__main__":
    import json

    # Load the hierarchical doctypes JSON file
    with open("output/hierarquical_doctypes.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Call the function with the loaded data
    doctypes_paths = map_doctype_paths(data)

    # Print the result
    print(json.dumps(doctypes_paths, indent=4, ensure_ascii=False))
