from flask import Flask, render_template, request, jsonify
from sesame_ai import SesameAI, TokenManager, SesameWebSocket
import threading
import queue
import pyaudio
import numpy as np

app = Flask(__name__)

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize PyAudio with better error handling
audio = pyaudio.PyAudio()
input_stream = None
output_stream = None

def check_audio_devices():
    devices = []
    try:
        for i in range(audio.get_device_count()):
            try:
                device_info = audio.get_device_info_by_index(i)
                devices.append(device_info)
                app.logger.info(f"Found audio device {i}: {device_info['name']}")
            except:
                continue
        return len(devices) > 0
    except:
        return False

# Check if we're running in Replit environment
import os
is_replit = 'REPL_ID' in os.environ

# Check if audio devices are available
has_audio = check_audio_devices()
if not has_audio:
    app.logger.warning("No audio devices available in this environment")
    if is_replit:
        app.logger.info("Running in Replit environment - using mock audio mode")

# Global variables 
audio_queue = queue.Queue()
is_recording = False
ws = None

# Mock audio class for environments without audio devices
class MockAudioStream:
    def __init__(self, *args, **kwargs):
        pass
    
    def read(self, *args, **kwargs):
        import time
        time.sleep(0.1)  # Simulate audio processing delay
        return bytes(1024)  # Return empty audio buffer
    
    def write(self, *args, **kwargs):
        pass
    
    def stop_stream(self):
        pass
    
    def close(self):
        pass

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_chat', methods=['POST'])
def start_chat():
    global input_stream, output_stream, ws
    try:
        character = request.json.get('character', 'Miles')

        # Set up audio streams with error handling
        if has_audio:
            try:
                input_stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=None  # Let PyAudio choose best device
                )
                
                output_stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    output_device_index=None  # Let PyAudio choose best device
                )
            except OSError as e:
                app.logger.error(f"Failed to open audio streams: {e}")
                raise Exception("Audio device initialization failed. Please check your system's audio settings.")
        else:
            # Use mock audio streams in environments without audio devices
            app.logger.warning("Using mock audio streams (no real audio functionality)")
            input_stream = MockAudioStream()
            output_stream = MockAudioStream()

        api_client = SesameAI()
        token_manager = TokenManager(api_client)
        id_token = token_manager.get_valid_token()

        ws = SesameWebSocket(id_token=id_token, character=character)

        # Set up detailed audio status callbacks
        def on_connect():
            app.logger.info("Connected to chat service")
            app.logger.info(f"Audio sample rate: {ws.server_sample_rate}Hz")
            app.logger.info(f"Audio codec: {ws.audio_codec}")

        def on_disconnect():
            app.logger.info("Disconnected from chat service")
            app.logger.info("Audio streams closed")

        ws.set_connect_callback(on_connect)
        ws.set_disconnect_callback(on_disconnect)

        if ws.connect():
            app.logger.info(f"Connected to chat with {character}")
            return jsonify({
                'status': 'success',
                'message': f'Connected to {character}'
            })
        else:
            raise Exception("Failed to connect to chat service")

    except Exception as e:
        app.logger.error(f"Error in start_chat: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': 'Check console for more information'
        })

@app.route('/stop_chat', methods=['POST'])
def stop_chat():
    global ws
    if ws:
        ws.disconnect()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)