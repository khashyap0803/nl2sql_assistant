"""
Text-to-Speech Module
Converts text responses to speech output
"""

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️  pyttsx3 not installed - text-to-speech disabled")
    print("   To enable: pip install pyttsx3")


class TextToSpeech:
    """Text-to-speech converter using pyttsx3"""

    def __init__(self, rate=150, volume=0.9):
        """
        Initialize TTS engine

        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        if not PYTTSX3_AVAILABLE:
            self.enabled = False
            print("⚠️  Text-to-Speech disabled (pyttsx3 not installed)")
            return

        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            self.enabled = True
            print("✓ Text-to-Speech initialized")
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            self.enabled = False

    def speak(self, text: str):
        """
        Convert text to speech

        Args:
            text: Text to speak
        """
        if not self.enabled:
            # Silent mode - just log instead of speaking
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def set_rate(self, rate: int):
        """Set speech rate"""
        if self.enabled:
            self.engine.setProperty('rate', rate)

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        if self.enabled:
            self.engine.setProperty('volume', volume)


# Test function
def test_tts():
    """Test text-to-speech"""
    print("Testing Text-to-Speech...")
    tts = TextToSpeech()
    if tts.enabled:
        tts.speak("Hello, I am your NL2SQL assistant. Testing text to speech.")
        print("✓ TTS test complete")
    else:
        print("✓ TTS test complete (disabled mode)")


if __name__ == "__main__":
    test_tts()
