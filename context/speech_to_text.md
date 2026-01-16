# speech_to_text.py - Voice Recognition Module

## File Location
```
nl2sql_assistant/src/voice/speech_to_text.py
```

## Purpose
This module provides **GPU-accelerated speech-to-text** using Faster-Whisper Large-v3. It:
- Records audio from microphone
- Transcribes speech to text using GPU
- Supports both live recording and file transcription

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SpeechToText                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │  sounddevice    │    │     Faster-Whisper              ││
│  │  (Recording)    │    │     (Transcription)             ││
│  │                 │    │                                 ││
│  │ - Microphone    │───>│ - Large-v3 model                ││
│  │ - 16kHz audio   │    │ - GPU (CUDA)                    ││
│  │ - numpy array   │    │ - CTranslate2 backend           ││
│  └─────────────────┘    └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencies

```python
import sys, os
import numpy as np

from faster_whisper import WhisperModel   # GPU-accelerated Whisper
import sounddevice as sd                   # Audio recording

from src.utils.logger import logger
```

### Why These Libraries?

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **faster-whisper** | Transcription | 4x faster than OpenAI Whisper |
| **sounddevice** | Recording | Cross-platform, simple API |
| **numpy** | Audio buffer | Required by Whisper |

---

## Global Availability Checks

```python
WHISPER_AVAILABLE = False
SOUNDDEVICE_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    raise RuntimeError(f"STT is mandatory but faster-whisper failed: {e}")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError as e:
    raise RuntimeError(f"STT is mandatory but sounddevice not available: {e}")
```

### Why Raise Instead of Fail Silently?
- Speech-to-text is a core feature
- User expects voice input to work
- Early failure with clear message

---

## Class: SpeechToText

### Constructor

```python
def __init__(self, model_name: str = "large-v3"):
    self.model = None
    self.model_name = model_name
    self.sample_rate = 16000      # Whisper requires 16kHz
    self.enabled = False
    self.device = "cuda"          # GPU only
    self.compute_type = "float16" # FP16 for GPU efficiency
    
    try:
        logger.i("STT_INIT", f"Loading Whisper {model_name} on GPU...")
        
        self.model = WhisperModel(
            model_name,
            device=self.device,
            compute_type=self.compute_type
        )
        
        logger.i("STT_INIT", f"Whisper {model_name} loaded successfully")
        self.enabled = True
        
    except Exception as e:
        raise RuntimeError(f"GPU loading failed: {e}")
```

#### Model Parameters:

| Parameter | Value | Reason |
|-----------|-------|--------|
| **model_name** | large-v3 | Best accuracy |
| **device** | cuda | GPU acceleration |
| **compute_type** | float16 | Efficient GPU inference |
| **sample_rate** | 16000 | Whisper's expected input |

#### Why large-v3?

| Model | Size | Accuracy | Speed |
|-------|------|----------|-------|
| tiny | 39M | Low | Fastest |
| base | 74M | Okay | Fast |
| small | 244M | Good | Medium |
| medium | 769M | Better | Slower |
| **large-v3** | 1.55B | **Best** | Slow |

We use large-v3 because:
- Accuracy is critical for SQL query understanding
- GPU acceleration makes it fast enough
- ~3-4 seconds for 5 second audio

---

### Method: `listen(duration)`

Records audio and transcribes to text.

```python
def listen(self, duration: int = 5) -> str:
    if not self.enabled:
        return ""
    
    try:
        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),  # samples = seconds * rate
            samplerate=self.sample_rate,
            channels=1,                          # Mono
            dtype=np.float32
        )
        sd.wait()  # Block until recording complete
        
        # Flatten to 1D array
        audio_data = audio_data.flatten()
        
        # Transcribe with GPU
        segments, info = self.model.transcribe(
            audio_data,
            language="en",
            beam_size=5
        )
        
        # Combine segments
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        
        return transcribed_text
        
    except Exception as e:
        logger.e("STT_LISTEN", f"Transcription failed: {e}")
        return ""
```

#### Audio Recording Details:

```
┌──────────────────────────────────────────┐
│ sd.rec(samples, samplerate, channels)    │
├──────────────────────────────────────────┤
│ samples = duration × sample_rate         │
│         = 5 seconds × 16000 Hz           │
│         = 80,000 samples                 │
│                                          │
│ Output: numpy array (80000, 1)           │
│ dtype: float32 (-1.0 to 1.0)             │
└──────────────────────────────────────────┘
```

#### Transcription Parameters:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **language** | "en" | English (faster than auto-detect) |
| **beam_size** | 5 | Search width (accuracy vs speed) |

---

### Method: `transcribe_file(audio_path)`

Transcribes pre-recorded audio files.

```python
def transcribe_file(self, audio_path: str) -> str:
    if not self.enabled:
        return ""
    
    try:
        segments, info = self.model.transcribe(
            audio_path,       # File path instead of array
            language="en",
            beam_size=5
        )
        
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        return transcribed_text
        
    except Exception as e:
        logger.e("STT_FILE", f"File transcription failed: {e}")
        return ""
```

#### Supported Formats:
- WAV
- MP3
- M4A
- FLAC
- OGG

---

### Method: `get_device()`

Returns current device status.

```python
def get_device(self) -> str:
    return "GPU (CUDA)" if self.enabled else "disabled"
```

---

## Usage in Application

### In main_window.py:

```python
from src.voice.speech_to_text import SpeechToText

# Initialize
stt = SpeechToText()  # Loads large-v3 on GPU

# Record and transcribe
if stt.enabled:
    text = stt.listen(duration=5)
    print(f"You said: {text}")
    # text = "show total sales by region"
```

### In VoiceWorker (threaded):

```python
class VoiceWorker(QThread):
    def run(self):
        text = self.stt.listen(duration=5)
        self.finished.emit(text)
```

---

## File Relationships

```
speech_to_text.py
    │
    ├──> External: faster-whisper library
    │        └── CTranslate2 + CUDA
    │
    ├──> External: sounddevice library
    │        └── PortAudio (system)
    │
    ├──> used by src/gui/main_window.py
    │
    └──> imports from src/utils/logger.py
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Model load time | ~5-10 seconds | First time only |
| 5 second audio | ~3-4 seconds | GPU transcription |
| VRAM usage | ~2-3 GB | large-v3 model |
| Accuracy | ~95%+ | For clear English |

---

## Faster-Whisper vs OpenAI Whisper

| Feature | OpenAI Whisper | Faster-Whisper |
|---------|----------------|----------------|
| Backend | PyTorch | CTranslate2 |
| Speed | 1x | **4x** |
| Memory | High | **50% less** |
| GPU Support | CUDA | CUDA + TensorRT |
| Quantization | No | INT8, FP16 |
| Dependencies | PyTorch | Lighter |

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| No GPU | Exception at init |
| Model not found | Auto-downloads |
| No microphone | Returns "" |
| No speech detected | Returns "" |
| Recording error | Logs, returns "" |

---

## Design Decisions

| Decision | Why |
|----------|-----|
| large-v3 model | Best accuracy for query understanding |
| GPU only | Required for acceptable speed |
| float16 | Memory efficient on GPU |
| 5 second default | Enough for typical queries |
| English only | Faster, project scope |
| Raise on init fail | STT is core feature |
