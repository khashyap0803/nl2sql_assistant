"""
Speech-to-Text Module (Placeholder for Whisper)
Will be enhanced once openai-whisper is installed
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class SpeechToText:
    """Speech recognition - placeholder implementation"""

    def __init__(self):
        """Initialize speech recognition"""
        print("⚠️  Whisper not yet installed - Speech recognition in placeholder mode")
        print("   Will be activated after installing: openai-whisper")
        self.enabled = False

    def listen(self, duration=5):
        """
        Record and transcribe audio

        Args:
            duration: Recording duration in seconds

        Returns:
            Transcribed text
        """
        if not self.enabled:
            print(f"🎤 Voice input not available yet")
            print("   Please install: pip install openai-whisper")
            return ""

        # Will be implemented after Whisper installation
        pass

    def transcribe_file(self, audio_path):
        """Transcribe audio file"""
        if not self.enabled:
            return ""
        pass


# Test function
def test_stt():
    """Test speech-to-text"""
    print("Testing Speech-to-Text...")
    stt = SpeechToText()
    print("✓ STT module loaded (awaiting Whisper installation)")


if __name__ == "__main__":
    test_stt()

