import get_doctypes
from dotenv import load_dotenv
import json
import os
from datetime import datetime
import api_client_data  # caso queira usar data.json mapping

# Load environment variables from the .env file in the project root
load_dotenv()

# Paths and filenames
OUTPUT_DIR = "output"
HIERARCHICAL_FILE = os.path.join(OUTPUT_DIR, "output_hierarchical.json")
DATA_FILE = os.path.join(OUTPUT_DIR, "output_hierarchical.json")
DATA_MAP_FILE = 'data.json'  # opcional

# Funções de conversão para o novo JSON de saída
def assign_codes(node, counter=[1]):
    code = f"e{counter[0]:05d}v"
    node['code'] = code
    counter[0] += 1
    for child in node.get('children', []):
        assign_codes(child, counter)

def build_data_node(node, data_map):
    code = node['code']
    data_node = {
        'path': code,
        'formulas': [],
        'data': data_map.get(code, [])
    }
    childs = [build_data_node(child, data_map) for child in node.get('children', [])]
    if childs:
        data_node['childs'] = childs
    return data_node

def collect_referencia(node, ref_dict):
    ref_dict[node['code']] = node.get('path', '')
    for child in node.get('children', []):
        collect_referencia(child, ref_dict)

def convert_hierarchical_to_teste():
    # Carrega o JSON hierárquico
    with open(HIERARCHICAL_FILE, 'r', encoding='utf-8') as f:
        wrapper = json.load(f)
        # Trata casos onde o JSON é uma lista (antigo) ou um dict {'entities': [...]}
        if isinstance(wrapper, dict) and 'entities' in wrapper:
            schema = wrapper['entities']
        elif isinstance(wrapper, list):
            schema = wrapper
        else:
            raise ValueError(f"Formato inesperado em {HIERARCHICAL_FILE}: deve ser lista ou conter 'entities'.")

    # Carrega mapping de dados
    data_map = {}
    if os.path.isfile(DATA_MAP_FILE):
        with open(DATA_MAP_FILE, 'r', encoding='utf-8') as f:
            data_map = json.load(f)

    # Atribui códigos
    for entry in schema:
        assign_codes(entry)

    # Monta referencias
    ref_dict = {}
    for entry in schema:
        collect_referencia(entry, ref_dict)

    # Monta lista de dados
    dados = [build_data_node(entry, data_map) for entry in schema]

    # Estrutura final
    test_output = {
        'referencia': [ref_dict],
        'dados': dados
    }

    # Grava novo JSON com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'teste_{timestamp}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_output, f, ensure_ascii=False, indent=4)
    print(f"Novo JSON de saída gerado: {output_file}")


def main():
    """
    Função principal que gera a hierarquia e em seguida converte para o formato teste_
    """

    doctypes = get_doctypes.get_data()

    with open("data/", 'w', encoding='utf-8') as f:
        json.dump(doctypes, f, indent=4, ensure_ascii=False)

    # # Gera hierarquia
    # hierarchical_entity = get_doctypes.get_hierarchical_doctype_structure()

    # print("Hierarchical structure loaded:")
    # print("Checking for circular references...")
    # try:
    #     json.dumps(hierarchical_entity)
    #     print("No circular references detected.")
    # except Exception as e:
    #     print(f"Circular reference error detected: {e}")

    # # Garante diretório de saída
    # os.makedirs(OUTPUT_DIR, exist_ok=True)

    # # Salva hierarquia
    # with open(HIERARCHICAL_FILE, 'w', encoding='utf-8') as f:
    #     json.dump(hierarchical_entity, f, indent=4, ensure_ascii=False)
    # print(f"Arquivo hierárquico salvo em: {HIERARCHICAL_FILE}")

    # # Converte e gera novo JSON de saída
    # convert_hierarchical_to_teste()


if __name__ == "__main__":
    main()
