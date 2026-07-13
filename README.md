# Offline AI Voice Assistant

An embedded offline AI voice assistant built on the **Radxa Rock-5T (RK3588)** using an **XMOS XVF3800 microphone array**, **Whisper.cpp**, **Gemma (Ollama)**, **Piper TTS**, and **OpenWakeWord**.

The project demonstrates an end-to-end offline voice assistant pipeline, from microphone capture to speech recognition, LLM inference, and speech synthesis, while also documenting the low-level Linux audio debugging required to bring up custom I2S hardware.

---

# Features

- Completely offline voice assistant
- Wake word detection using OpenWakeWord
- Speech-to-Text using Whisper.cpp
- Local LLM inference using Gemma via Ollama
- Text-to-Speech using Piper
- ALSA audio capture
- XMOS XVF3800 microphone array
- RK3588 (Radxa Rock-5T) platform
- Engineering handover documentation
- Hardware debugging notes

---

# Hardware

Host Board

- Radxa Rock-5T (RK3588)

Audio DSP

- XMOS XVF3800

Communication

- I2S
- I2C

Operating System

- Debian Linux

---

# Software Stack

- Python
- OpenWakeWord
- PyAudio
- Whisper.cpp
- Ollama
- Gemma 3 1B
- Piper
- ALSA

---

# Repository Structure

```
Offline-AI-Voice-Assistant
│
├── assets
├── docs
│   └── ENGINEERING_HANDOVER.md
├── images
├── media
├── src
│   └── assistant.py
├── README.md
├── requirements.txt
└── .gitignore
```

---

# Project Pipeline

```
User Speech
      │
      ▼
OpenWakeWord
      │
      ▼
PyAudio
      │
      ▼
XMOS XVF3800
      │
      ▼
ALSA Audio Capture
      │
      ▼
Whisper.cpp
      │
      ▼
Gemma (Ollama)
      │
      ▼
Piper
      │
      ▼
Generated Speech
```

---

# Media

Repository contains

- Hardware photographs
- Oscilloscope captures
- Voice assistant demonstration video
- Example input audio
- Example output audio

---

# Engineering Challenges

During development several hardware and Linux audio issues were solved.

- ALSA Input/Output errors
- DMA starvation
- Incorrect BCLK ratio
- XMOS standby after ESP32 bypass
- I2S synchronization
- Device Tree configuration
- Manual I2C wake-up sequence
- ALSA mixer configuration
- Hexdump verification
- Oscilloscope debugging

Complete details are available in

```
docs/ENGINEERING_HANDOVER.md
```

---

# Technologies Used

- Embedded Linux
- ALSA
- Device Tree
- I2C
- I2S
- Python
- Whisper.cpp
- Ollama
- Gemma
- Piper
- OpenWakeWord

---

# Future Improvements

- Noise suppression
- Better wake word models
- Speaker output integration
- Streaming conversations
- GPIO integration
- Edge optimization

---

# Disclaimer

This repository contains only the work completed as part of the software integration and debugging process.

Company proprietary firmware, hardware design files, confidential source code, and sensitive information have been intentionally excluded.

---

# Author

Akash V

Computer Science Engineering Student

Embedded AI | Edge AI | Linux | Python | IoT