import os
import sys
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from flask_cors import CORS # Importar CORS
# import eventlet # REMOVIDO: Não usaremos eventlet por enquanto

# Garante que o eventlet seja usado
# eventlet.monkey_patch() # REMOVIDO: Monkey-patching pode causar o RecursionError

# Importa as funções dos módulos existentes
from get_doctypes import process_arteris_doctypes
from api_client_data import get_keys, get_data_from_key
from json_to_entity_transformer import create_hierarchical_doctype_structure

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "https://arteris-editor.meb.services"
]}})
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'uma-chave-secreta-padrao') # Use uma chave secreta segura
# Mudando async_mode para 'threading' para evitar a necessidade de eventlet/gevent
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*") # Permitir CORS para SocketIO também (opcional, mas bom ter)

# Configurar CORS para Flask
# Permitir requisições especificamente de http://localhost:3000 para as rotas Flask
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Variável global para armazenar o JSON gerado
generated_json_data = None

# --- Captura de Logs ---
class SocketIOHandler:
    """Um manipulador para redirecionar prints para o Socket.IO."""
    def write(self, message):
        # Emite a mensagem apenas se não for uma string vazia ou apenas espaços/newlines
        if message.strip():
            socketio.emit('log_message', {'data': message.strip()})

    def flush(self):
        # Necessário pela interface de stream, mas não faz nada aqui
        pass

# Redireciona stdout para o nosso handler
original_stdout = sys.stdout
sys.stdout = SocketIOHandler()

import traceback # Adicionar import no topo se não existir (já existe na linha 149, mas melhor garantir)

# --- Função Auxiliar para Geração ---
def _generate_entity_structure():
    """
    Função auxiliar que encapsula a lógica de busca e transformação.
    Retorna a estrutura de entidades ou lança uma exceção em caso de erro.
    """
    print("--- Iniciando Geração Interna ---")
    # Obtém a URL base e o token das variáveis de ambiente
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    if not api_base_url or not api_token:
        error_msg = "Erro: Variáveis de ambiente ARTERIS_API_BASE_URL ou ARTERIS_API_TOKEN não definidas."
        print(error_msg)
        raise ValueError(error_msg) # Lança exceção para ser capturada

    # --- Etapa 1: Processar DocTypes e Fields ---
    print("--- Buscando DocTypes e Fields ---")
    all_doctypes, child_parent_mapping, doctypes_with_fields = process_arteris_doctypes(api_base_url, api_token)

    if all_doctypes is None:
         error_msg = "Falha ao buscar DocTypes."
         print(error_msg)
         raise ConnectionError(error_msg) # Lança exceção específica

    print("\n--- Busca de Metadados concluída ---")

    # --- Etapa 2: Transformar em Entidades ---
    print("--- Transformando Metadados em Entidades ---")
    entity_structure = create_hierarchical_doctype_structure(
        doctypes_with_fields,
        child_parent_mapping
    )

    print(f"Encontrados {len(entity_structure.get('entities', []))} DocTypes no módulo Arteris.")
    print("Estrutura de entidades gerada com sucesso.")
    print("\n--- Geração Interna Concluída ---")
    return entity_structure

# --- Rotas Flask ---
@app.route('/')
def index():
    """Renderiza a página inicial."""
    return render_template('index.html')

@app.route('/get_generated_json')
def get_generated_json():
    """Retorna o JSON gerado mais recentemente."""
    global generated_json_data
    if generated_json_data:
        # Retorna o JSON como uma resposta JSON para ser processado pelo JS
        return jsonify(generated_json_data)
    else:
        return jsonify({"error": "Nenhum JSON foi gerado ainda."}), 404

@app.route('/api/generate_entity_structure', methods=['GET'])
def api_generate_entity_structure():
    """Endpoint da API para gerar e retornar a estrutura de entidades."""
    try:
        entity_structure = _generate_entity_structure()
        # Retorna diretamente a lista de entidades
        return jsonify(entity_structure.get('entities', []))
    except ValueError as e: # Erro de configuração
        return jsonify({"error": str(e)}), 400 # Bad Request
    except ConnectionError as e: # Erro ao buscar dados
        return jsonify({"error": str(e)}), 503 # Service Unavailable
    except Exception as e: # Outros erros inesperados
        print(f"Erro inesperado na API: {e}")
        traceback.print_exc() # Log completo no servidor
        return jsonify({"error": "Erro interno do servidor ao gerar estrutura."}), 500 # Internal Server Error

# --- Eventos Socket.IO ---
@socketio.on('connect')
def handle_connect():
    """Lida com novas conexões de clientes."""
    print("Cliente conectado") # Isso será enviado via Socket.IO
    emit('log_message', {'data': 'Conectado ao servidor.'})

@socketio.on('disconnect')
def handle_disconnect():
    """Lida com desconexões de clientes."""
    print("Cliente desconectado") # Isso também será enviado via Socket.IO

@socketio.on('start_generation')
def handle_start_generation(message): # message não é usado, mas mantido pela assinatura do evento
    """Inicia o processo de geração de entidades via Socket.IO."""
    global generated_json_data
    generated_json_data = None # Limpa o JSON anterior
    emit('generation_started')
    print("--- Iniciando Geração de Entidades (via Socket.IO) ---") # Log inicial

    try:
        # Chama a função auxiliar refatorada
        entity_structure = _generate_entity_structure()
        generated_json_data = entity_structure # Armazena o JSON gerado globalmente
        print("\n--- Geração Concluída (via Socket.IO) ---")
        # Emite sucesso e opcionalmente os dados (decidi não enviar dados grandes via socket)
        emit('generation_complete', {'success': True})

    except (ValueError, ConnectionError) as e: # Captura erros específicos lançados pela helper
        error_msg = f"Erro durante a geração: {e}"
        print(error_msg)
        emit('generation_error', {'error': str(e)}) # Envia erro específico ao cliente
    except Exception as e: # Captura outros erros inesperados
        error_msg = f"Erro inesperado durante a geração: {e}"
        print(error_msg)
        traceback.print_exc() # Log completo no servidor
        emit('generation_error', {'error': "Erro interno do servidor."}) # Mensagem genérica
    finally:
        emit('generation_finished') # Sinaliza o fim, mesmo com erro

# --- Ponto de Entrada ---
if __name__ == '__main__':
    print("Iniciando servidor Flask com Socket.IO (modo threading)...")
    # Usa socketio.run, que agora usará o servidor de desenvolvimento do Flask/Werkzeug
    # com suporte a threading para SocketIO.
    # Voltando para a porta 5000, conforme mapeamento do docker-compose.
    socketio.run(app, host='0.0.0.0', port=8088, debug=True, allow_unsafe_werkzeug=True) # debug=True e allow_unsafe_werkzeug=True para desenvolvimento
    