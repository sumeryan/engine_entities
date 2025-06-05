"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Flask Web Application Module.
This module provides a web interface and API endpoints for the entity generation process.
It includes Flask routes, Socket.IO event handlers, and error handling.
"""

import os
import sys
import json
import traceback

from flask import Flask, render_template, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

import get_doctypes
import hierarchical_tree
import engine_data

import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False  # Preserve insertion order in JSON
# Configure CORS for Flask routes
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "https://arteris-editor.meb.services",
    "http://localhost:5174"
]}})
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'uma-chave-secreta-padrao')
# Setup SocketIO with threading mode
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Redirect stdout to Socket.IO logs
class SocketIOHandler:
    def write(self, message):
        if message.strip():
            socketio.emit('log_message', {'data': message.strip()})
    def flush(self): pass
original_stdout = sys.stdout
sys.stdout = SocketIOHandler()

# Global store for generated JSON
generated_json_data = None

# Paths for saving intermediate JSON
OUTPUT_DIR = "output"
HIERARCHICAL_FILE = os.path.join(OUTPUT_DIR, "output_hierarchical.json")
DATA_MAP_FILE = 'data.json'

# --- Conversion helper functions ---
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
    children = [build_data_node(c, data_map) for c in node.get('children', [])]
    if children:
        data_node['childs'] = children
    return data_node

def collect_referencia(node, ref_dict):
    ref_dict[node['code']] = node.get('path', '')
    for child in node.get('children', []):
        collect_referencia(child, ref_dict)

def convert_hierarchical_to_teste(schema):
    # Assign unique codes
    for entry in schema:
        assign_codes(entry)
    # Build reference map
    ref_dict = {}
    for entry in schema:
        collect_referencia(entry, ref_dict)
    # Load optional data map
    data_map = {}
    if os.path.isfile(DATA_MAP_FILE):
        with open(DATA_MAP_FILE, 'r', encoding='utf-8') as f:
            data_map = json.load(f)
    # Build 'dados' tree
    dados = [build_data_node(entry, data_map) for entry in schema]
    # Return only referencia and dados, matching teste_YYYYMMDD.json
    return { 'referencia': [ref_dict], 'dados': dados }

# --- Internal generation helper ---
def _generate_entity_structure():
    # print("--- Starting Internal Generation ---")
    # api_base = os.getenv("ARTERIS_API_BASE_URL")
    # api_token = os.getenv("ARTERIS_API_TOKEN")
    # if not api_base or not api_token:
    #     msg = "Error: ARTERIS_API_BASE_URL or ARTERIS_API_TOKEN not defined"
    #     print(msg)
    #     raise ValueError(msg)
    # print("--- Transforming Metadata to Entities ---")

    # processor = get_doctypes.DoctypeProcessor()   
    # # Get formula data
    # processor.get_formula_data()
    
    # # Get hierarchical structure
    # struct = processor.get_hierarchical_structure()
        
    # print("Entity structure generated successfully.")
    # print("--- Internal Generation Completed ---")
    # return struct

    processor = get_doctypes.DoctypeProcessor()
    all_doctypes = processor.process_doctypes()

    # Build tree
    builder = hierarchical_tree.HierarchicalTreeBuilder()
    hierarchical_data = builder.build_tree(all_doctypes)

    return hierarchical_data

# --- Flask routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_generated_json')
def get_generated_json():
    global generated_json_data
    if generated_json_data:
        return jsonify(generated_json_data)
    return jsonify({'error': 'No JSON has been generated yet.'}), 404

@app.route('/api/update_formula', methods=['POST'])
def update_formula():
    data = request.json
    formula_id = data.get('formula_id')
    formula_value = data.get('formula_value')
    url = f"https://arteris.meb.services/api/resource/Formula%20Group%20Field/{formula_id}"
    headers = {
        'Authorization': 'token be2ff702de81b65:ba84415a14e57fd',
        'Content-Type': 'application/json',
    }
    payload = {"formula": formula_value}
    try:
        resp = requests.put(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error updating formula: {e}")
        raise

@app.route('/api/generate_entity_structure', methods=['GET'])
def api_generate_entity_structure():
    try:
        struct = _generate_entity_structure()
        return jsonify(struct)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except ConnectionError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Unexpected error in API: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal error.'}), 500

@app.route('/api/hierarchy', methods=['GET'])
def get_hierarchy():
    processor = get_doctypes.DoctypeProcessor()   
    hierarchical = processor.get_hierarchical_structure()
    return jsonify(hierarchical)

@app.route('/api/contracts', methods=['GET'])
def get_contracts():
    processor = get_doctypes.DoctypeProcessor()   
    keys = processor.get_keys('Contract')
    return jsonify(keys)

@app.route('/api/formulas', methods=['GET'])
def get_formulas():
    processor = get_doctypes.DoctypeProcessor()   
    formulas = processor.get_formula_data()
    return jsonify(formulas)

@app.route('/api/treedata', methods=['GET'])
def get_tree_data():
    contract = request.args.get('contract')
    if not contract:
        return jsonify({'error': 'Missing contract parameter'}), 400

    processor = get_doctypes.DoctypeProcessor()   
    formulas = processor.get_formula_data()
    data = processor.get_data(contract)
    # hierarchical = processor.get .hi(data["structure"])

    # Build engine data
    builder = engine_data.EngineDataBuilder(
        data["hierarchical"], 
        formulas, 
        data["data"], 
        "data",
        compact_mode=True
    )
    engine_data = builder.build()

    return jsonify(engine_data)

# --- Socket.IO handlers ---
@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('log_message', {'data': 'Connected to server.'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('start_generation')
def handle_start_generation(message):
    global generated_json_data
    generated_json_data = None
    emit('generation_started')
    print("--- Starting Entity Generation (via Socket.IO) ---")
    try:
        struct = _generate_entity_structure()
        generated_json_data = struct
        print("--- Generation Completed (via Socket.IO) ---")
        emit('generation_complete', {'success': True})
    except (ValueError, ConnectionError) as e:
        err = str(e)
        print(f"Error during generation: {err}")
        emit('generation_error', {'error': err})
    except Exception as e:
        print(f"Unexpected error during generation: {e}")
        traceback.print_exc()
        emit('generation_error', {'error': 'Internal server error.'})
    finally:
        emit('generation_finished')

# --- Entry point ---
if __name__ == '__main__':
    print("Starting Flask server with Socket.IO (threading mode)...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8088)),
        debug=True,
        allow_unsafe_werkzeug=True
    )
