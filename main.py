"""
Script principal para orquestrar a busca de metadados e dados da API Arteris.

Este script executa as seguintes etapas:
1. Carrega configurações da API do arquivo .env.
2. Busca a lista de DocTypes do módulo 'Arteris' usando api_client.
3. Para cada DocType, busca seus DocFields usando api_client.
4. Transforma os metadados coletados (DocTypes e DocFields) na estrutura
   de entidades JSON usando transformer.
5. Para cada DocType com DocFields, busca os dados reais correspondentes
   usando api_client.
6. Armazena os resultados em dicionários em memória e imprime exemplos.
"""

import get_doctypes 
from dotenv import load_dotenv
import json
import os

# Carrega variáveis de ambiente do arquivo .env na raiz do projeto
load_dotenv()

def main():

    hierarchical_entity = get_doctypes.get_hierarchical_doctype_structure()
    
    print("Estrutura hierárquica carregada:")
    print(hierarchical_entity)
    print("\nVerificando referências circulares...")
    try:
        json.dumps(hierarchical_entity)
        print("Nenhuma referência circular detectada.")
    except Exception as e:
        print(f"Erro de referência circular detectado: {e}")

    output_dir = "output"
    output_filename = "output_hierarchical.json"
    print(f"Path: {os.path.join(output_dir, output_filename)}")
    try:
        with open(os.path.join(output_dir, output_filename), "w", encoding="utf-8") as f:
            json.dump(hierarchical_entity, f, indent=4, ensure_ascii=False)
        print(f"\n************************")
        print(f"Arquivo {output_filename} salvo com sucesso em {output_dir}.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

# Ponto de entrada do script
if __name__ == "__main__":
    main()