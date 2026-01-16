import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger

WHISPER_AVAILABLE = False
SOUNDDEVICE_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    logger.i("STT_INIT", "faster-whisper library loaded (GPU)")
except (ImportError, OSError, Exception) as e:
    logger.e("STT_INIT", f"faster-whisper not available: {e}")
    raise RuntimeError(f"STT is mandatory but faster-whisper failed: {e}")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError as e:
    logger.e("STT_INIT", f"sounddevice not installed: {e}")
    raise RuntimeError(f"STT is mandatory but sounddevice not available: {e}")


class SpeechToText:

    def __init__(self, model_name: str = "large-v3"):
        self.model = None
        self.model_name = model_name
        self.sample_rate = 16000
        self.enabled = False
        self.device = "cuda"
        self.compute_type = "float16"
        
        try:
            logger.i("STT_INIT", f"Loading Whisper {model_name} on GPU (CUDA)...")
            
            self.model = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            
            logger.i("STT_INIT", f"Whisper {model_name} loaded on GPU successfully")
            self.enabled = True
            
        except Exception as e:
            logger.e("STT_INIT", f"Failed to load Whisper on GPU: {e}")
            raise RuntimeError(f"STT is mandatory but GPU loading failed: {e}")

    def listen(self, duration: int = 5) -> str:
        if not self.enabled:
            logger.e("STT_LISTEN", "Whisper not enabled")
            return ""
        
        try:
            logger.i("STT_LISTEN", f"Recording for {duration} seconds...")
            
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            logger.i("STT_LISTEN", "Recording complete, transcribing on GPU...")
            
            audio_data = audio_data.flatten()
            
            segments, info = self.model.transcribe(
                audio_data,
                language="en",
                beam_size=5
            )
            
            transcribed_text = " ".join([segment.text for segment in segments]).strip()
            
            logger.i("STT_LISTEN", f"Transcription: '{transcribed_text}'")
            logger.d("STT_LISTEN", f"Language: {info.language}, Probability: {info.language_probability:.2f}")
            
            return transcribed_text
            
        except Exception as e:
            logger.e("STT_LISTEN", f"Transcription failed: {e}")
            return ""

    def transcribe_file(self, audio_path: str) -> str:
        if not self.enabled:
            logger.e("STT_FILE", "Whisper not enabled")
            return ""
        
        try:
            logger.i("STT_FILE", f"Transcribing file: {audio_path}")
            
            segments, info = self.model.transcribe(
                audio_path,
                language="en",
                beam_size=5
            )
            
            transcribed_text = " ".join([segment.text for segment in segments]).strip()
            
            logger.i("STT_FILE", f"Transcription: '{transcribed_text}'")
            
            return transcribed_text
            
        except Exception as e:
            logger.e("STT_FILE", f"File transcription failed: {e}")
            return ""

    def get_device(self) -> str:
        return "GPU (CUDA)" if self.enabled else "disabled"


def test_stt():
    print("=" * 60)
    print("Faster-Whisper Large-v3 Speech-to-Text Test (GPU)")
    print("=" * 60)
    
    try:
        print("Loading Whisper large-v3 on GPU...")
        stt = SpeechToText(model_name="large-v3")
        
        print(f"Whisper loaded on: {stt.get_device()}")
        print("\nSpeak now (5 seconds)...")
        text = stt.listen(duration=5)
        print(f"Transcription: {text}")
        
    except Exception as e:
        print(f"[ERROR] STT test failed: {e}")


if __name__ == "__main__":
    test_stt()
