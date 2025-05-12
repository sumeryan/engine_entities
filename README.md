# Engine Entities

A Python application to extract entity metadata from Arteris API and generate hierarchical entity structure.

## Description

This project connects to the Arteris API to extract DocType metadata and transforms it into a hierarchical entity structure. The application provides both a command-line interface and a web interface with WebSocket support for real-time progress updates.

## Features

- Extract DocTypes and their fields from Arteris API
- Create hierarchical entity structure from metadata
- Generate JSON output file
- Web interface with real-time progress updates via WebSockets
- API endpoints for accessing generated data
- Docker support for easy deployment

## Project Structure

- **Main Components:**
  - `app.py`: Flask web application with Socket.IO support
  - `main.py`: CLI entry point for entity generation
  - `get_doctypes.py`: Functions to process and retrieve DocTypes
  - `api_client.py`: API client for Arteris DocTypes
  - `api_client_data.py`: API client for Arteris data

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`:
  - requests
  - python-dotenv
  - Flask
  - Flask-SocketIO
  - Flask-CORS

## Configuration

Create a `.env` file in the project root with the following variables:
```
ARTERIS_API_BASE_URL=https://your-api.com/api/resource
ARTERIS_API_TOKEN=token your_api_key:your_api_secret
FLASK_SECRET_KEY=your_secure_secret_key
```

## Usage

### CLI Mode

Run the script to generate the entity structure JSON file:

```bash
python main.py
```

This will:
1. Connect to the Arteris API
2. Fetch DocTypes and their fields
3. Create a hierarchical structure
4. Save the result to `output/output_hierarchical.json`

### Web Interface

Start the Flask application:

```bash
python app.py
```

This will start a web server at http://localhost:8088 with:
- Real-time progress updates via WebSockets
- API endpoints for entity generation

### Docker Deployment

Build and run with Docker Compose:

```bash
docker-compose up
```

## API Endpoints

- `GET /`: Web interface
- `GET /api/generate_entity_structure`: Generate and return entity structure
- `GET /get_generated_json`: Get the most recently generated JSON

## Error Handling

The application includes comprehensive error handling for:
- API connection issues
- Missing environment variables
- JSON processing errors

## Notes

The application normalizes entity names and attributes by:
- Removing accents
- Replacing non-alphanumeric characters with underscores
- Handling special cases and invalid strings