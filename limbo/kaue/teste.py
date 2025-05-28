import json
from collections import OrderedDict
import re


def carregar_arquivos():
    with open('formulas.json', encoding='utf-8') as f:
        formulas = json.load(f)
    with open('saida.json', encoding='utf-8') as f:
        saida = json.load(f)
    return formulas, saida


def gerar_mapeamento_caminhos(saida):
    mapeamento = OrderedDict()
    contador = 1

    def percorrer(nodes):
        nonlocal contador
        for node in nodes:
            caminho = node['path']
            if caminho not in mapeamento:
                mapeamento[caminho] = f"e{contador:05d}v"
                contador += 1
            
            # Also map paths using fieldname for better matching
            fieldname_path = f"{node.get('fieldname', '')}"
            if fieldname_path and fieldname_path not in mapeamento:
                mapeamento[fieldname_path] = mapeamento[caminho]
                
            for child in node.get('children', []):
                percorrer([child])

    percorrer(saida)
    return mapeamento


def normalize_key(s: str) -> str:
    """Remove caracteres não alfanuméricos e retorna lowercase."""
    return re.sub(r'[^0-9a-z]', '', s.lower())


# Overrides manuais para campos ambíguos
# Mapeamento direto entre o fieldname da fórmula e o caminho correto no JSON de saída
overrides = {
    # Mapeamentos corretos baseados na saída de debug
    'valortotalvigente': 'contrato.valor_total_do_contrato',
    'faturamentodireto': 'contrato.medicao_de_contrato_bm.faturamento_direto_ftd_na_fase_atual',
    'ftdacumulado': 'contrato.medicao_de_contrato_bm.valor_total_vigente',
    'saldo': 'contrato.medicao_de_contrato_bm.saldo_contratual_anterior_r',  # Corrigido aqui - adicionado aspas de fechamento
    'medicaoatual': 'contrato.medicao_de_contrato_bm.medicao_atual_a',
    'medicaoatualdescontoftd': 'contrato.medicao_de_contrato_bm.medicao_atual_com_desconto_de_ftd_b',
    'totalvigentemenosftd': 'contrato.medicao_de_contrato_bm.valor_total_vigente_com_desconto_de_ftd',
    'acumuladoatual': 'contrato.medicao_de_contrato_bm.medicao_acum_anterior',
    'saldopercentual': 'contrato.medicao_de_contrato_bm.saldo_contratual_percentual',  # Ajustado
    'descontoreidi': 'contrato.medicao_de_contrato_bm.desconto_do_reidi_c_3_65_b',
    
    # Adicionando paths explícitos para campos problemáticos
    'Contract Measurement SAP Order': 'contrato.medicao_de_contrato_bm.pedido_sap_de_bm',
    'Contract Measurement': 'contrato.medicao_de_contrato_bm',
}


def mapear_campos_formula(formulas):
    """Mapeia campos de fórmula para seus caminhos completos e cria estrutura hierárquica"""
    campo_para_modulo = {}
    campo_para_path_completo = {}
    
    # Constrói árvore de caminhos para ajudar a resolver ambiguidades
    paths_estrutura = {}
    
    for formula in formulas['data']['tableformulas']:
        campo = formula['groupfieldfieldname']
        modulo = formula['modulo']
        doctype = formula['groupfielddoctype']
        nome_formula = formula['formulafield']
        
        # Extrai caminho a partir do nome da fórmula
        if '▶︎' in nome_formula:
            partes = nome_formula.split('▶︎')
            if len(partes) >= 2:
                modelo = partes[0].strip()
                atributo = partes[1].strip()
                
                # Constrói um caminho estruturado
                caminho_completo = f"{modelo.lower().replace(' ', '_')}.{atributo.lower().replace(' ', '_')}"
                campo_para_path_completo[campo] = caminho_completo
                
                # Adiciona à estrutura de paths
                if modelo not in paths_estrutura:
                    paths_estrutura[modelo] = {}
                paths_estrutura[modelo][atributo] = campo
        
        # Mapeia campo para módulo
        campo_para_modulo[campo] = modulo
    
    return {
        'campo_para_modulo': campo_para_modulo,
        'campo_para_path': campo_para_path_completo,
        'estrutura': paths_estrutura
    }


def processar_formulas(formulas, mapeamento):
    formulas_processadas = []
    
    # Constrói mapeamento de módulos para usar em caso de ambiguidade
    modulos_campos = mapear_campos_formula(formulas)
    
    # Adiciona mapeamentos para caminhos de módulo completos
    for formula in formulas['data']['tableformulas']:
        modulo = formula['modulo']
        doctype = formula['groupfielddoctype']
        if doctype not in mapeamento and doctype:
            # Se o doctype não estiver mapeado, cria um novo mapeamento
            novo_ref = f"e{len(mapeamento)+1:05d}v"
            mapeamento[doctype] = novo_ref
            print(f"[NOVO] Mapeamento para doctype: {doctype} como {novo_ref}")
    
    # Primeiro passo: processa cada fórmula individualmente
    for formula in formulas['data']['tableformulas']:
        expr = formula['formula']
        campo_destino = formula['groupfieldfieldname']
        nome_campo = formula['formulafield']
        doctype = formula['groupfielddoctype']
        
        # Define o caminho do path_ref
        if campo_destino in overrides:
            # Usa o override definido manualmente
            caminho_destino = overrides[campo_destino]
            if caminho_destino in mapeamento:
                path_ref = mapeamento[caminho_destino]
            else:
                # Se o caminho não existir no mapeamento, cria um novo
                path_ref = f"e{len(mapeamento)+1:05d}v"
                mapeamento[caminho_destino] = path_ref
                print(f"[NOVO] Criado mapeamento para '{caminho_destino}' como '{path_ref}'")
        elif doctype in mapeamento:
            # Usa o doctype como caminho base
            path_ref = mapeamento[doctype]
        else:
            # Tenta encontrar correspondência no mapeamento existente
            found = False
            for caminho, ref in mapeamento.items():
                # Verifica se o fieldname está contido no caminho
                campo_norm = normalize_key(campo_destino)
                caminho_norm = normalize_key(caminho)
                if campo_norm in caminho_norm:
                    path_ref = ref
                    found = True
                    break
            
            if not found:
                # Cria um novo mapeamento baseado no doctype ou no módulo
                if doctype:
                    novo_caminho = f"{doctype}.{campo_destino}"
                else:
                    novo_caminho = f"{modulo.lower().replace(' ', '_')}.{campo_destino}"
                    
                path_ref = f"e{len(mapeamento)+1:05d}v"
                mapeamento[novo_caminho] = path_ref
                print(f"[NOVO] Criado mapeamento para '{novo_caminho}' como '{path_ref}'")
        
        # Processa a expressão da fórmula substituindo os caminhos pelos refs
        expr_processada = expr
        
        # Substitui primeiro os caminhos mais longos para evitar substituições parciais incorretas
        for caminho, ref in sorted(mapeamento.items(), key=lambda x: len(x[0]), reverse=True):
            # Trata o caminho para correspondência na fórmula
            padrao_caminho = caminho.replace('▶︎', '.').replace(' ', '_').lower()
            
            # Tenta substituição exata
            if padrao_caminho in expr_processada.lower():
                expr_processada = re.sub(re.escape(padrao_caminho), ref, expr_processada, flags=re.IGNORECASE)
            
            # Substitui partes específicas do caminho (campos aninhados)
            if '.' in padrao_caminho:
                partes = padrao_caminho.split('.')
                for i in range(len(partes) - 1, 0, -1):  # Do mais específico para o mais geral
                    subcaminho = '.'.join(partes[-i:])
                    if len(subcaminho) > 5 and re.search(r'\b' + re.escape(subcaminho) + r'\b', expr_processada.lower()):
                        expr_processada = re.sub(r'\b' + re.escape(subcaminho) + r'\b', ref, expr_processada, flags=re.IGNORECASE)
        
        # Adiciona a fórmula processada à lista
        formulas_processadas.append({
            "path": path_ref,
            "value": expr_processada,
            "field_name": nome_campo,
            "original_expr": expr  # Guardamos a expressão original para debug
        })

    return formulas_processadas


def construir_hierarquia(saida, mapeamento, formulas_processadas):
    dados = []

    # Agrupa fórmulas por path para acesso rápido
    formulas_por_path = {}
    for f in formulas_processadas:
        formulas_por_path.setdefault(f['path'], []).append({
            "value": f['value'],
            "field_name": f.get('field_name', '')  # Incluímos o nome do campo para debug
        })

    def construir_node(node):
        caminho_node = node['path']
        current = mapeamento.get(caminho_node)
        if not current:
            print(f"[AVISO] Caminho não mapeado: {caminho_node}")
            # Cria mapeamento na hora
            current = f"e{len(mapeamento)+1:05d}v"
            mapeamento[caminho_node] = current
        
        # obtém fórmulas desse nó
        formulas_node = formulas_por_path.get(current, [])
        
        # campos de dados: inclui descrição e todas as fórmulas como valores
        fields = []
        
        # campo original (descrição)
        fields.append({
            "path": current,
            "type": node.get('type', ''),
            "value": node.get('description', '')
        })
        
        # campos adicionais a partir de fórmulas
        for formula_info in formulas_node:
            fields.append({
                "path": current,
                "type": "formula",
                "value": formula_info["value"],
                "name": formula_info.get("field_name", "")  # Incluímos o nome para debug
            })
        
        # monta data
        data_no = [{
            "id": "0196c31f-2847-7a70-999a-66b6b8510709",
            "fields": fields
        }]
        
        # constrói filhos
        childs = [construir_node(ch) for ch in node.get('children', [])]
        
        # formulas específicas para este nó
        formulas_list = []
        for formula_info in formulas_node:
            formulas_list.append({
                "path": current,
                "value": formula_info["value"],
                "name": formula_info.get("field_name", "")  # Incluímos o nome para debug
            })
        
        return {
            "path": current,
            "formulas": formulas_list,
            "data": data_no,
            "childs": childs
        }

    for raiz in saida:
        dados.append(construir_node(raiz))
    
    return dados


def gerar_saida(mapeamento, dados):
    # Constrói lista de referência simples: ref -> path
    ref_dict = {ref: path for path, ref in mapeamento.items()}
    
    # Organiza as referências no formato esperado
    referencia = [ref_dict]

    return {
        "referencia": referencia,
        "dados": dados
    }


def debug_mapeamentos(formulas, mapeamento):
    """Função auxiliar para depuração dos mapeamentos de fórmulas."""
    print("\n=== MAPEAMENTOS DE FÓRMULAS ===")
    
    # Primeiro mostra os mapeamentos existentes
    for formula in formulas['data']['tableformulas']:
        campo = formula['groupfieldfieldname']
        modulo = formula['modulo']
        doctype = formula['groupfielddoctype']
        encontrado = False
        
        # Verifica nos overrides primeiro
        if campo in overrides:
            caminho_override = overrides[campo]
            if caminho_override in mapeamento:
                ref = mapeamento[caminho_override]
                print(f"Campo: {campo} (Módulo: {modulo}, DocType: {doctype})")
                print(f"  → Mapeado por override para: {caminho_override} ({ref})")
                encontrado = True
            else:
                print(f"Campo: {campo} (Módulo: {modulo}, DocType: {doctype})")
                print(f"  ✗ Override configurado mas caminho não encontrado: {caminho_override}")
                print(f"    Caminhos disponíveis:")
                for path in mapeamento.keys():
                    if any(subcaminho in path.lower() for subcaminho in caminho_override.lower().split('.')):
                        print(f"    - {path}")
                encontrado = True
        
        # Se não encontrado nos overrides, busca no mapeamento normal
        if not encontrado:
            for caminho, ref in mapeamento.items():
                # Busca por correspondência mais específica
                if campo.lower() in caminho.lower() or normalize_key(campo) in normalize_key(caminho):
                    print(f"Campo: {campo} (Módulo: {modulo}, DocType: {doctype})")
                    print(f"  → Mapeado para: {caminho} ({ref})")
                    encontrado = True
                    break
            
            # Se ainda não encontrou, verifica pelo doctype
            if not encontrado and doctype in mapeamento:
                ref = mapeamento[doctype]
                print(f"Campo: {campo} (Módulo: {modulo}, DocType: {doctype})")
                print(f"  → Mapeado pelo DocType para: {doctype} ({ref})")
                encontrado = True
            
            if not encontrado:
                print(f"Campo: {campo} (Módulo: {modulo}, DocType: {doctype})")
                print(f"  ✗ Não mapeado - Será criado um novo mapeamento")
    
    # Mostra referências cruzadas entre caminhos e referências
    print("\n=== REFERÊNCIAS CRUZADAS ===")
    caminho_para_ref = {}
    for caminho, ref in sorted(mapeamento.items()):
        if ref in caminho_para_ref:
            print(f"ALERTA: Referência duplicada {ref} para:")
            print(f"  - {caminho_para_ref[ref]}")
            print(f"  - {caminho}")
        else:
            caminho_para_ref[ref] = caminho


if __name__ == '__main__':
    print("Iniciando processamento de fórmulas...")
    formulas, saida = carregar_arquivos()
    
    # Gera mapeamento inicial de caminhos
    print("Gerando mapeamento de caminhos...")
    mapeamento = gerar_mapeamento_caminhos(saida)
    
    # Extrai estrutura de campos e fórmulas
    print("Extraindo estrutura de campos e fórmulas...")
    mapeamento_formula = mapear_campos_formula(formulas)
    
    # Adiciona mapeamentos estruturais ao mapeamento principal
    for campo, path in mapeamento_formula['campo_para_path'].items():
        if campo in overrides:
            continue  # Pula campos que já têm override definido
        if path not in mapeamento:
            melhor_match = None
            # Busca o melhor match parcial
            for caminho in mapeamento:
                # Verifica se alguma parte do path está no caminho
                partes_path = path.split('.')
                for parte in partes_path:
                    if parte and len(parte) > 3 and parte in caminho.lower():
                        melhor_match = caminho
                        break
                if melhor_match:
                    break
            
            if melhor_match:
                # Usa o mapeamento do melhor match
                mapeamento[path] = mapeamento[melhor_match]
                print(f"[AUTO] Mapeamento para '{path}' usando match parcial de '{melhor_match}'")
    
    # Depuração dos mapeamentos
    debug_mapeamentos(formulas, mapeamento)
    
    # Processa as fórmulas
    print("\nProcessando fórmulas...")
    formulas_processadas = processar_formulas(formulas, mapeamento)
    
    # Constrói hierarquia de dados
    print("Construindo hierarquia de dados...")
    dados = construir_hierarquia(saida, mapeamento, formulas_processadas)
    
    # Gera saída final
    resultado = gerar_saida(mapeamento, dados)
    
    # Salva resultado
    print("Salvando resultado...")
    with open('saida_final.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    # Mostra algumas estatísticas
    print("\n=== ESTATÍSTICAS ===")
    print(f"Total de mapeamentos: {len(mapeamento)}")
    print(f"Total de fórmulas processadas: {len(formulas_processadas)}")
    print(f"Total de nós na hierarquia: {sum(1 for _ in saida)}")
    
    print("\nProcessamento concluído! Verifique saida_final.json")