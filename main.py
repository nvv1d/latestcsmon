
from flask import Flask, render_template, request, jsonify
from sesame_ai import SesameAI, TokenManager, SesameWebSocket
import threading
import pyaudio
import queue
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global variables for audio handling
audio_queue = queue.Queue()
is_recording = False
ws = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_chat', methods=['POST'])
def start_chat():
    global ws
    try:
        character = request.json.get('character', 'Miles')
        api_client = SesameAI()
        token_manager = TokenManager(api_client)
        id_token = token_manager.get_valid_token()
        
        ws = SesameWebSocket(id_token=id_token, character=character)
        ws.connect()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_chat', methods=['POST'])
def stop_chat():
    global ws
    if ws:
        ws.disconnect()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
