import sys
import os
import wave
import math
import struct
import unittest

# Ensure the HUKUM-Chatbot directory is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faster_whisper import WhisperModel

class TestVoicePipeline(unittest.TestCase):

    def setUp(self):
        # Create a synthetic 1-second 440Hz audio beep WAV file
        self.filename = "test_synthetic.wav"
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0
        
        with wave.open(self.filename, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            
            num_frames = int(sample_rate * duration)
            for i in range(num_frames):
                # Calculate sine wave value
                t = float(i) / sample_rate
                value = int(32767.0 * math.sin(2.0 * math.pi * frequency * t))
                data = struct.pack("<h", value)
                w.writeframes(data)

    def tearDown(self):
        # Clean up the synthetic wave file
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_whisper_transcription(self):
        # 1. Instantiate the model on CPU
        print("Initializing Whisper model...")
        model = WhisperModel("tiny", device="cpu", compute_type="float32")
        self.assertIsNotNone(model)
        
        # 2. Run transcription on the synthetic file
        print(f"Transcribing synthetic file {self.filename}...")
        segments, info = model.transcribe(self.filename, beam_size=5)
        
        # Convert segments to list to trigger generation
        segments_list = list(segments)
        print("Transcription finished!")
        print("Detected language:", info.language)
        print("Detected language probability:", info.language_probability)
        
        # Verify transcription didn't crash
        self.assertIsInstance(segments_list, list)

if __name__ == "__main__":
    unittest.main()
