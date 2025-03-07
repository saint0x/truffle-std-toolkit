import truffle
import replicate
import os
from typing import Optional

class WhisperSTT:
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Please set REPLICATE_API_TOKEN environment variable")
    
    @truffle.tool(
        description="Convert speech to text using Whisper API",
        icon="microphone"
    )
    @truffle.args(
        audio_file="Path to the audio file to transcribe",
        language="Optional: Specify the language of the audio (e.g., 'en', 'es')",
    )
    def TranscribeAudio(self, audio_file: str, language: Optional[str] = None) -> str:
        """
        Transcribes audio file to text using OpenAI's Whisper model via Replicate.
        """
        try:
            # Validate audio file exists
            if not os.path.exists(audio_file):
                return f"Error: Audio file not found at {audio_file}"
            
            # Initialize Whisper model
            model = "openai/whisper"
            
            # Prepare inputs
            inputs = {
                "audio": open(audio_file, "rb"),
            }
            if language:
                inputs["language"] = language
            
            # Run transcription
            output = replicate.run(
                model,
                input=inputs
            )
            
            return output["transcription"] if "transcription" in output else "Transcription failed"
            
        except Exception as e:
            return f"Error during transcription: {str(e)}"

if __name__ == "__main__":
    app = truffle.TruffleApp(WhisperSTT())
    app.launch() 