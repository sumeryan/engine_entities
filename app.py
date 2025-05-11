"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Flask Web Application Module.
This module provides a web interface and API endpoints for the entity generation process.
It includes Flask routes, Socket.IO event handlers, and error handling.
"""

import os
import sys
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from flask_cors import CORS # Import CORS
from get_doctypes import get_hierarchical_doctype_structure

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "https://arteris-editor.meb.services",
    "http://localhost:5174"
]}})
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'uma-chave-secreta-padrao') # Use a secure secret key
# Change async_mode to 'threading' to avoid the need for eventlet/gevent
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*") # Allow CORS for SocketIO too (optional, but good to have)

# Configure CORS for Flask
# Allow requests specifically from http://localhost:3000 for Flask routes
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Global variable to store the generated JSON
generated_json_data = None

# --- Log Capture ---
class SocketIOHandler:
    """A handler to redirect prints to Socket.IO."""
    def write(self, message):
        # Emit the message only if it's not an empty string or just spaces/newlines
        if message.strip():
            socketio.emit('log_message', {'data': message.strip()})

    def flush(self):
        # Required by the stream interface, but doesn't do anything here
        pass

# Redirect stdout to our handler
original_stdout = sys.stdout
sys.stdout = SocketIOHandler()

import traceback # Add import at the top if it doesn't exist (already exists on line 149, but better to make sure)

# --- Helper Function for Generation ---
def _generate_entity_structure():
    """
    Helper function that encapsulates the search and transformation logic.
    Returns the entity structure or raises an exception in case of error.
    """
    print("--- Starting Internal Generation ---")
    # Get the base URL and token from environment variables
    api_base_url = os.getenv("ARTERIS_API_BASE_URL")
    api_token = os.getenv("ARTERIS_API_TOKEN")

    if not api_base_url or not api_token:
        error_msg = "Error: Environment variables ARTERIS_API_BASE_URL or ARTERIS_API_TOKEN not defined."
        print(error_msg)
        raise ValueError(error_msg) # Raise exception to be caught

    # Get entity structure
    print("--- Transforming Metadata to Entities ---")
    entity_structure = get_hierarchical_doctype_structure()

    print(f"Found {len(entity_structure.get('entities', []))} DocTypes in the Arteris module.")
    print("Entity structure generated successfully.")
    print("\n--- Internal Generation Completed ---")
    return entity_structure

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html')

@app.route('/get_generated_json')
def get_generated_json():
    """Returns the most recently generated JSON."""
    global generated_json_data
    if generated_json_data:
        # Returns the JSON as a JSON response to be processed by JS
        return jsonify(generated_json_data)
    else:
        return jsonify({"error": "No JSON has been generated yet."}), 404

@app.route('/api/generate_entity_structure', methods=['GET'])
def api_generate_entity_structure():
    """API endpoint to generate and return the entity structure."""
    try:
        entity_structure = _generate_entity_structure()
        # Returns directly the list of entities
        return jsonify(entity_structure.get('entities', []))
    except ValueError as e: # Configuration error
        return jsonify({"error": str(e)}), 400 # Bad Request
    except ConnectionError as e: # Error fetching data
        return jsonify({"error": str(e)}), 503 # Service Unavailable
    except Exception as e: # Other unexpected errors
        print(f"Unexpected error in API: {e}")
        traceback.print_exc() # Complete log on the server
        return jsonify({"error": "Internal server error generating structure."}), 500 # Internal Server Error

# --- Socket.IO Events ---
@socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    print("Client connected") # This will be sent via Socket.IO
    emit('log_message', {'data': 'Connected to server.'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections."""
    print("Client disconnected") # This will also be sent via Socket.IO

@socketio.on('start_generation')
def handle_start_generation(message): # message is not used, but kept for the event signature
    """Starts the entity generation process via Socket.IO."""
    global generated_json_data
    generated_json_data = None # Clear previous JSON
    emit('generation_started')
    print("--- Starting Entity Generation (via Socket.IO) ---") # Initial log

    try:
        # Call the refactored helper function
        entity_structure = _generate_entity_structure()
        generated_json_data = entity_structure # Store the generated JSON globally
        print("\n--- Generation Completed (via Socket.IO) ---")
        # Emit success and optionally the data (decided not to send large data via socket)
        emit('generation_complete', {'success': True})

    except (ValueError, ConnectionError) as e: # Catch specific errors thrown by the helper
        error_msg = f"Error during generation: {e}"
        print(error_msg)
        emit('generation_error', {'error': str(e)}) # Send specific error to client
    except Exception as e: # Catch other unexpected errors
        error_msg = f"Unexpected error during generation: {e}"
        print(error_msg)
        traceback.print_exc() # Complete log on the server
        emit('generation_error', {'error': "Internal server error."}) # Generic message
    finally:
        emit('generation_finished') # Signal the end, even with error

# --- Entry Point ---
if __name__ == '__main__':
    print("Starting Flask server with Socket.IO (threading mode)...")
    # Use socketio.run, which will now use the Flask/Werkzeug development server
    # with threading support for SocketIO.
    # Going back to port 5000, as per docker-compose mapping.
    socketio.run(app, host='0.0.0.0', port=8088, debug=True, allow_unsafe_werkzeug=True) # debug=True and allow_unsafe_werkzeug=True for development