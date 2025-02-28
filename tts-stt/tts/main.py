import os
import json
from typing import Optional, Dict, List, Union, BinaryIO
from datetime import datetime
from pathlib import Path
import requests
import truffle

class TTSTool:
    """Tool for text-to-speech conversion using ElevenLabs API."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.output_dir = os.path.expanduser(os.getenv("TTS_OUTPUT_DIR", "./audio_output"))
        self.default_voice = os.getenv("TTS_DEFAULT_VOICE", "Josh")
        self.default_model = os.getenv("TTS_MODEL", "eleven_multilingual_v2")
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> requests.Response:
        """Make a request to the ElevenLabs API."""
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        response = requests.request(
            method=method,
            url=f"{self.base_url}/{endpoint}",
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response

    @truffle.tool(
        description="List available voices",
        icon="mic"
    )
    def ListVoices(self) -> Dict[str, Union[bool, List[Dict[str, Any]]]]:
        """Get a list of available voices."""
        try:
            response = self._make_request("voices")
            voices = response.json()
            
            return {
                "success": True,
                "voices": [{
                    "voice_id": voice["voice_id"],
                    "name": voice["name"],
                    "category": voice.get("category", "unknown"),
                    "labels": voice.get("labels", {}),
                    "description": voice.get("description", ""),
                    "preview_url": voice.get("preview_url", "")
                } for voice in voices]
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Generate speech from text",
        icon="volume-2"
    )
    @truffle.args(
        text="Text to convert to speech",
        voice_id="Voice ID to use (defaults to TTS_DEFAULT_VOICE)",
        model_id="Model ID to use (defaults to TTS_MODEL)",
        stability="Voice stability (0.0-1.0)",
        similarity_boost="Voice similarity boost (0.0-1.0)",
        style="Speaking style (0.0-1.0)",
        use_speaker_boost="Whether to use speaker boost",
        filename="Custom filename for the output (optional)"
    )
    def GenerateSpeech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        stability: float = None,
        similarity_boost: float = None,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate speech from text using specified voice and parameters.
        Returns path to the generated audio file.
        """
        try:
            # Use default values from environment if not specified
            voice_id = voice_id or self.default_voice
            model_id = model_id or self.default_model
            stability = stability if stability is not None else float(os.getenv("TTS_STABILITY", "0.5"))
            similarity_boost = similarity_boost if similarity_boost is not None else float(os.getenv("TTS_SIMILARITY", "0.75"))

            # Prepare request data
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }

            # Generate speech
            response = self._make_request(
                f"text-to-speech/{voice_id}",
                method="POST",
                json=data,
                stream=True
            )

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"speech_{timestamp}.mp3"

            # Ensure filename has .mp3 extension
            if not filename.endswith('.mp3'):
                filename += '.mp3'

            # Save the audio file
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            return {
                "success": True,
                "file_path": file_path,
                "text": text,
                "voice_id": voice_id,
                "model_id": model_id,
                "settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Generate speech from a text file",
        icon="file-text"
    )
    @truffle.args(
        file_path="Path to the text file",
        chunk_size="Maximum characters per audio chunk (to handle long texts)",
        voice_id="Voice ID to use",
        add_timestamps="Whether to add timestamps to output filenames"
    )
    def GenerateSpeechFromFile(
        self,
        file_path: str,
        chunk_size: int = 5000,
        voice_id: Optional[str] = None,
        add_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Generate speech from a text file, handling long texts by chunking.
        Returns paths to all generated audio files.
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
                    filename = f"{base_filename}_part{i}_{timestamp}.mp3"
                else:
                    filename = f"{base_filename}_part{i}.mp3"

                result = self.GenerateSpeech(
                    text=chunk,
                    voice_id=voice_id,
                    filename=filename
                )
                
                if "error" in result:
                    return result
                
                results.append(result)

            return {
                "success": True,
                "total_chunks": len(chunks),
                "results": results,
                "source_file": file_path
            }
        except Exception as e:
            return {"error": str(e)}

    @truffle.tool(
        description="Get information about voice generation history",
        icon="clock"
    )
    def GetHistory(self) -> Dict[str, Any]:
        """Get information about voice generation history."""
        try:
            response = self._make_request("history")
            history = response.json()
            
            return {
                "success": True,
                "history": [{
                    "history_item_id": item["history_item_id"],
                    "text": item.get("text", ""),
                    "date": item.get("date", ""),
                    "voice_id": item.get("voice_id", ""),
                    "voice_name": item.get("voice_name", ""),
                    "character_count": item.get("character_count", 0),
                    "content_type": item.get("content_type", "")
                } for item in history.get("history", [])]
            }
        except Exception as e:
            return {"error": str(e)} 