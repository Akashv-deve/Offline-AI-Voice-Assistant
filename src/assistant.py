import openwakeword
from openwakeword.model import Model
from openwakeword.utils import download_models
import pyaudio
import wave
import subprocess
import requests
import numpy as np
import re
import shutil
import subprocess
import os

# 1. Download required ONNX models if they are missing
download_models()

# CONFIGURATION
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Optional Smart Home API endpoint
# Replace with your own REST API endpoint if integrating smart-home devices.
FLUTTER_API_URL = "http://YOUR_SERVER_IP:8080/api/relays" 

def get_installed_model():
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        models = [m["name"] for m in response.json().get("models", [])]
        for m in models:
            if "gemma" in m.lower():
                print(f"-> Auto-detected Gemma model: {m}")
                return m
        if models:
            print(f"-> No direct Gemma tag found. Using fallback model: {models[0]}")
            return models[0]
    except Exception:
        print("-> Could not connect to Ollama to check models. Defaulting to 'gemma'")
    return "gemma"

GEMMA_MODEL = get_installed_model()

# 2. Initialize openWakeWord & PyAudio
oww_model = Model(wakeword_models=["alexa"], inference_framework="onnx") 
audio = pyaudio.PyAudio()

def open_mic_stream():
    # Hardcoded to your USB headset at Index 4
    return audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280, input_device_index=4)

stream = open_mic_stream()

def record_voice_native(duration_seconds=5):
    print("--- RECORDING YOUR VOICE ---")
    frames = []
    chunks = int((16000 / 1280) * duration_seconds)
    for _ in range(chunks):
        data = stream.read(1280, exception_on_overflow=False)
        frames.append(data)
        
    wf = wave.open("input.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

def trigger_relay(device_id, action):
    payload = {
        "device": device_id,
        "state": action
    }
    print(f"--- TRIGGERING RELAY: {device_id} -> {action} ---")
    try:
        response = requests.post(FLUTTER_API_URL, json=payload, timeout=2) 
        if response.status_code == 200:
            print("-> Success: Relay activated!")
            return True
        else:
            print(f"-> API Error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"-> Connection Error: Could not reach Flutter app - {e}")
        return False

def run_pipeline():
    print("--- TRANSCRIBING ---")
    transcription = subprocess.check_output(["./whisper.cpp/build/bin/whisper-cli", "-m", "./whisper.cpp/models/ggml-base.en.bin", "-f", "input.wav", "-nt"]).decode('utf-8').strip()
    print(f"You said: {transcription}")
    
    text_lower = transcription.lower()
    
    # === SMART HOME INTERCEPTOR ===
    # If it hears a command, trigger the API instantly instead of making Gemma think about it
    if "turn on" in text_lower or "turn off" in text_lower:
        action = "ON" if "turn on" in text_lower else "OFF"
        # You can map specific words to specific device IDs here if needed
        trigger_relay("demo_relay_1", action)
        gemma_text = f"Okay, I have turned {action.lower()} the relay."
        
    else:
        print("--- ASKING GEMMA ---")
        try:
            system_prompt = transcription + " (Please answer in 2 or 3 short sentences without any lists or special formatting)."
            response = requests.post(OLLAMA_URL, json={"model": GEMMA_MODEL, "prompt": system_prompt, "stream": False})
            gemma_text = response.json().get("response", "I encountered an error processing that request.")
        except Exception as e:
            gemma_text = "Error connecting to the Ollama server."
            
    print(f"Gemma: {gemma_text}")
    
    print("--- SPEAKING ---")
    clean_text = re.sub(r'[*_#`]', '', gemma_text) 
    safe_text = clean_text.replace("'", "").replace('"', "") 
    
    subprocess.run(f"echo '{safe_text}' | ./piper/piper --model en_US-lessac-medium.onnx --output_file output.wav", shell=True)
    print(f"\nSpeech saved to: {os.path.abspath('output.wav')}")

if shutil.which("aplay"):
    try:
        subprocess.run(
            ["aplay", "-D", "plughw:0,0", "output.wav"],
            check=False
        )
    except Exception as e:
        print(f"Playback skipped: {e}")
else:
    print("aplay not available.")

try:
    print("Listening for 'Alexa'...")
    while True:
        data = stream.read(1280, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        prediction = oww_model.predict(audio_data)
        
        # Bumped threshold to 0.65 to prevent static/background noise triggers
        if prediction["alexa"] > 0.65:
            print("Wake word detected!")
            
            record_voice_native(5)
            
            stream.stop_stream()
            stream.close()
            
            run_pipeline()
            
            stream = open_mic_stream()
            
            # Flush the hardware buffer to catch any lingering TTS echo
            for _ in range(15):
                stream.read(1280, exception_on_overflow=False)
                
            # Wipe the model's memory completely to prevent the ghost-trigger loop
            oww_model.reset()
            
            print("\nListening for 'Alexa'...")
            
except KeyboardInterrupt:
    try:
        stream.stop_stream()
        stream.close()
    except:
        pass
    audio.terminate()
