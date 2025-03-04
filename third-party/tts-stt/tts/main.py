import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import requests
import truffle
import replicate

class KokoroTTS:
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Please set REPLICATE_API_TOKEN environment variable")
        
        # Initialize configuration from environment variables
        self.output_dir = os.path.expanduser(os.getenv("TTS_OUTPUT_DIR", "./tts_output"))
        self.default_voice = os.getenv("TTS_DEFAULT_VOICE", "v2/en_speaker_6")
        self.model_version = os.getenv("TTS_MODEL_VERSION", "jaaari/kokoro-82m")
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    @truffle.tool(
        description="Convert text to speech using Kokoro API",
        icon="speaker"
    )
    @truffle.args(
        text="Text to convert to speech",
        voice="Optional: Voice preset to use",
        output_file="Optional: Custom filename for the output (should end with .wav)"
    )
    def SynthesizeSpeech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converts text to speech using Kokoro TTS model via Replicate.
        Returns information about the generated audio.
        """
        try:
            # Use default voice if none specified
            voice = voice or self.default_voice
            
            # Generate filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"speech_{timestamp}.wav"
            
            # Ensure filename has .wav extension
            if not output_file.endswith('.wav'):
                output_file += '.wav'
            
            # Prepare inputs
            inputs = {
                "text": text,
                "voice_preset": voice
            }
            
            # Run synthesis
            output = replicate.run(
                self.model_version,
                input=inputs
            )
            
            if output and isinstance(output, list) and len(output) > 0:
                # Get the audio URL
                audio_url = output[0]
                
                # Download the audio file
                file_path = os.path.join(self.output_dir, output_file)
                response = requests.get(audio_url)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "text": text,
                    "voice": voice,
                    "model": self.model_version
                }
            else:
                return {
                    "success": False,
                    "error": "Speech synthesis failed - no output received"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @truffle.tool(
        description="Generate speech from a text file",
        icon="file-text"
    )
    @truffle.args(
        file_path="Path to the text file",
        chunk_size="Maximum characters per audio chunk (to handle long texts)",
        voice="Optional: Voice preset to use",
        add_timestamps="Whether to add timestamps to output filenames"
    )
    def GenerateSpeechFromFile(
        self,
        file_path: str,
        chunk_size: int = 5000,
        voice: Optional[str] = None,
        add_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Generate speech from a text file, handling long texts by chunking.
        Returns information about all generated audio files.
        """
        try:
            # Read the text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Get base filename
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            
            # Split text into chunks if needed
            chunks = []
            current_chunk = ""
            
            for sentence in text.split('. '):
                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + '. '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + '. '
            
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Generate speech for each chunk
            results = []
            for i, chunk in enumerate(chunks, 1):
                if add_timestamps:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{base_filename}_part{i}_{timestamp}.wav"
                else:
                    filename = f"{base_filename}_part{i}.wav"

                result = self.SynthesizeSpeech(
                    text=chunk,
                    voice=voice,
                    output_file=filename
                )
                results.append(result)

            return {
                "success": True,
                "total_chunks": len(chunks),
                "results": results,
                "source_file": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    app = truffle.TruffleApp(KokoroTTS())
    app.launch() 