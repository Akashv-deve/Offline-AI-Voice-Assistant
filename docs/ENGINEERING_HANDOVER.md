# Embedded AI Voice Assistant
## Engineering Handover Document

**Platform:** Radxa Rock-5T (RK3588) + XMOS XVF3800 + Ollama + Whisper.cpp + Piper

---

# 1. Project Architecture

The pipeline flows from a physical hardware microphone array through the ALSA audio subsystem, into a localized Python AI environment, and finally back out as synthesized speech.

```text
                 [ USER ]
                    │
            "Alexa" Wake Word
                    │
          OpenWakeWord (Python)
                    │
             PyAudio / ALSA
                    │
      XMOS XVF3800 Microphone DSP
                    │
               I2S (Slave)
                    │
         RK3588 I2S Controller
                    │
                  ALSA
                    │
              Whisper.cpp
                    │
             Gemma (Ollama)
                    │
                  Piper
                    │
               output.wav
```

---

# 2. Hardware Specifications

| Component | Description |
|-----------|-------------|
| Host Board | Radxa Rock-5T (RK3588) |
| Audio DSP | XMOS XVF3800 (4-Microphone Array) |
| Communication | I2S (Audio Data), I2C (Control/Registers) |
| Original Controller | ESP32 (Physically Disabled / Bypassed) |

---

# 3. Audio Configuration (Working State)

When the hardware is fully synchronized, use the following configuration.

```
ALSA Device : plughw:4,0
Format      : S16_LE
Sample Rate : 16000 Hz
Channels    : 1 (Mono)
```

## Working Capture Command

```bash
arecord -D plughw:4,0 -f S16_LE -r 16000 -c 1 voice.wav
```

---

# 4. Critical Hardware Fixes & Troubleshooting

Several major issues were encountered during hardware bring-up. Always check these first if the audio pipeline stops working.

---

## A. BCLK Ratio Bug (DMA Starvation)

### Symptoms

- ALSA crashes immediately.
- `pcm_read:2221: read error: Input/output error`
- DMA starvation.
- Clock synchronization failure.

### Root Cause

The RK3588 I2S controller was using an incorrect Bit Clock (BCLK) Ratio. In one instance the driver contained a garbage value such as:

```
1374389568
```

instead of

```
64
```

This caused the I2S clock generator to become unstable.

### Fix

Check current BCLK ratio:

```bash
amixer -c 4 cget numid=1
```

If the value is not **64**, set it manually.

```bash
amixer -c 4 cset numid=1 64
```

Verify again.

```bash
amixer -c 4 cget numid=1
```

Expected output:

```
values=64
```

**Result**

Setting the BCLK Ratio to **64** permanently resolved:

- Input/output error
- DMA starvation
- Continuous recording failures

---

## B. XMOS Muted / Silent WAV Files

### Symptoms

- `arecord` runs normally.
- DATA1 remains completely flat.
- WAV file contains only zeros.

Example:

```
00 00 00 00
*
```

### Root Cause

Originally the ESP32 initialized the XMOS during boot.

After bypassing the ESP32, the XMOS remained powered but stayed in a muted standby state.

### Solution

Detect the XMOS device.

```bash
sudo i2cdetect -y 3
```

Expected address:

```
0x20
```

(Some board revisions may use **0x22**.)

Read registers.

```bash
sudo i2cdump -y 3 0x20
```

Company-specific IO Expander wake sequence:

```bash
sudo i2cset -y 4 0x20 0x06 0x00
sudo i2cset -y 4 0x20 0x02 0xFF
```

---

## C. Oscilloscope Verification

Always verify clocks while **arecord** is running.

Expected signals:

| Signal | Expected |
|---------|----------|
| MCLK | ~12 MHz |
| BCLK | Verified |
| LRCLK | ~16 kHz |
| DATA1 | Digital waveform (NOT FLAT) |

---

## D. Hexdump Verification

Inspect the recorded file.

```bash
hexdump -C voice.wav | head
```

Working recording:

```
31 00
15 00
2B 00
5A 00
8D 00
...
```

Changing values indicate real microphone samples.

If every value is

```
00 00
```

the XMOS is still outputting digital silence.

---

# 5. Device Tree Overview

Working overlay:

```
ubolt-i2s.dts
```

Important properties:

```
simple-audio-card
mclk-fs
bitclock-master
frame-master
```

Always create a backup before editing.

```bash
cp ubolt-i2s.dts ubolt-i2s.dts.backup
```

Compare changes.

```bash
diff -u ubolt-i2s.dts.backup ubolt-i2s.dts
```

---

# 6. AI Software Layer

The AI pipeline runs entirely inside a Python Virtual Environment.

## Setup

```bash
cd ~/voice_assistant

python3 -m venv venv

source venv/bin/activate
```

Run assistant.

```bash
python3 assistant.py
```

Edit assistant.

```bash
nano assistant.py
```

If you receive

```
ModuleNotFoundError
```

you are using the wrong Python environment.

Locate available virtual environments.

```bash
find ~ -type f -path "*/bin/activate"
```

---

# 7. AI Pipeline

```
OpenWakeWord
        │
        ▼
PyAudio
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
output.wav
```

---

## OpenWakeWord

Detects the wake word:

```
Alexa
```

---

## Whisper.cpp

Executable:

```
whisper.cpp/build/bin/whisper-cli
```

Model:

```
ggml-base.en.bin
```

Locate executable.

```bash
find ~ -name whisper-cli
```

Locate model.

```bash
find ~ -name ggml-base.en.bin
```

---

## Gemma (Ollama)

Current model:

```
gemma3:1b
```

Start server.

```bash
ollama serve
```

List installed models.

```bash
ollama list
```

Run model.

```bash
ollama run gemma3:1b
```

---

## Piper

Produces:

```
output.wav
```

Verify.

```bash
ls -lh output.wav
```

Playback.

```bash
aplay -D plughw:0,0 output.wav
```

**Note**

The onboard 3.5 mm audio jack did not function because the ES8316 codec never initialized.

The generated WAV file is valid.

---

# 8. Quick Reference Command Cheat Sheet

## ALSA

List recording devices.

```bash
arecord -l
```

List playback devices.

```bash
aplay -l
```

List playback names.

```bash
aplay -L
```

List ALSA cards.

```bash
cat /proc/asound/cards
```

PCM information.

```bash
cat /proc/asound/pcm
```

Current hardware parameters.

```bash
cat /proc/asound/card4/pcm0c/sub0/hw_params
```

---

## System Debugging

Kernel log.

```bash
sudo dmesg
```

Clock summary.

```bash
sudo cat /sys/kernel/debug/clk/clk_summary
```

Scan I2C bus.

```bash
sudo i2cdetect -y 3
```

---

## Recording Tests

Mono.

```bash
arecord -D plughw:4,0 -f S16_LE -r 16000 -c 1 voice.wav
```

Stereo.

```bash
arecord -D plughw:4,0 -f S16_LE -r 16000 -c 2 demo.wav
```

Verify recording.

```bash
ls -lh voice.wav
```

Inspect samples.

```bash
hexdump -C voice.wav | head

```

Pin out configuration

"Physical pin = Rock5t"

1. I2S Audio Routing
Physical Pin	Rock 5T Function	μBolt Header (J13)	    Net	Description
12	         I2S2_SCLK_M1		PI_BCLK			Bit Clock
35	         I2S2_LRCK_M1		PLLR_CLK		Left/Right Clock (Frame Sync / Word Select)
38	         I2S2_SDI_M1		PI_DIN			Audio Data IN to Rock 5T
40		 I2S2_SDO_M1		PI_DOUT			Audio Data OUT from Rock 5T (for TTS)
2. I2C Routing
Physical Pin	Rock 5T Function	μBolt Header (J13)          Net	Description
15		I2C0_SDA_M1		SDA2			Secondary I2C Data
13		I2C0_SCL_M1		SCL2			Secondary I2C Clock
3. SPI Routing (XMOS / Flash Control)
Physical Pin	Rock 5T Function	μBolt Header (J13) Net	Description
19	         SPI0_MOSI_M2	PI_SPI_MOSI	Master Out Slave In
21	         SPI0_MISO_M2	PI_SPI_MISO	Master In Slave Out
23	         SPI0_CLK_M2	PI_SPI_CLK	SPI Clock
24	         SPI0_CS1_M2	PI_QSPI_CS_N	Chip Select for Flash (Active Low)
4. Power and Ground
Physical Pin	                 Rock 5T Function	μBolt Header (J13) Net
2, 4	           			+5.0V			PL_5V
1, 17	           			+3.3V			3V3
6, 9, 14, 20, 25, 30, 34, 39		GND			GND


# End of Document