import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import requests
import truffle
import replicate

class DalleImageGenerator:
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Please set REPLICATE_API_TOKEN environment variable")
        
        # Initialize configuration from environment variables
        self.output_dir = os.path.expanduser(os.getenv("IMAGE_OUTPUT_DIR", "./image_output"))
        self.model_version = os.getenv("IMAGE_MODEL_VERSION", "stability-ai/dall-e")
        self.default_size = os.getenv("IMAGE_SIZE", "1024x1024")
        self.default_quality = os.getenv("IMAGE_QUALITY", "standard")
        self.default_style = os.getenv("IMAGE_STYLE", "vivid")
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    @truffle.tool(
        description="Generate an image using DALL-E",
        icon="image"
    )
    @truffle.args(
        prompt="Detailed description of the image to generate",
        size="Optional: Image size (1024x1024 or 512x512)",
        quality="Optional: Image quality (standard or hd)",
        style="Optional: Image style (vivid or natural)",
        output_file="Optional: Custom filename for the output (should end with .png)"
    )
    def GenerateImage(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an image using DALL-E based on the provided prompt.
        Returns information about the generated image.
        """
        try:
            # Use default values if not specified
            size = size or self.default_size
            quality = quality or self.default_quality
            style = style or self.default_style
            
            # Generate filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"image_{timestamp}.png"
            
            # Ensure filename has .png extension
            if not output_file.endswith('.png'):
                output_file += '.png'
            
            # Prepare inputs
            inputs = {
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "style": style
            }
            
            # Run image generation
            output = replicate.run(
                self.model_version,
                input=inputs
            )
            
            if output and isinstance(output, list) and len(output) > 0:
                # Get the image URL
                image_url = output[0]
                
                # Download the image file
                file_path = os.path.join(self.output_dir, output_file)
                response = requests.get(image_url)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "prompt": prompt,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "model": self.model_version
                }
            else:
                return {
                    "success": False,
                    "error": "Image generation failed - no output received"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @truffle.tool(
        description="Generate multiple variations of an image",
        icon="images"
    )
    @truffle.args(
        prompt="Detailed description of the image to generate",
        num_variations="Number of variations to generate (1-4)",
        size="Optional: Image size (1024x1024 or 512x512)",
        quality="Optional: Image quality (standard or hd)",
        style="Optional: Image style (vivid or natural)"
    )
    def GenerateVariations(
        self,
        prompt: str,
        num_variations: int = 1,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates multiple variations of an image using DALL-E.
        Returns information about all generated images.
        """
        try:
            # Validate number of variations
            num_variations = max(1, min(4, num_variations))
            
            # Use default values if not specified
            size = size or self.default_size
            quality = quality or self.default_quality
            style = style or self.default_style
            
            # Generate base filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"image_variations_{timestamp}"
            
            # Generate images
            results = []
            for i in range(num_variations):
                output_file = f"{base_filename}_{i+1}.png"
                result = self.GenerateImage(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    output_file=output_file
                )
                results.append(result)
            
            return {
                "success": True,
                "total_variations": num_variations,
                "results": results,
                "prompt": prompt,
                "settings": {
                    "size": size,
                    "quality": quality,
                    "style": style
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @truffle.tool(
        description="Generate an image with specific dimensions",
        icon="ruler"
    )
    @truffle.args(
        prompt="Detailed description of the image to generate",
        width="Width of the image in pixels",
        height="Height of the image in pixels",
        quality="Optional: Image quality (standard or hd)",
        style="Optional: Image style (vivid or natural)"
    )
    def GenerateCustomSize(
        self,
        prompt: str,
        width: int,
        height: int,
        quality: Optional[str] = None,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an image with custom dimensions using DALL-E.
        Returns information about the generated image.
        """
        try:
            # Validate dimensions
            if width < 256 or width > 1024 or height < 256 or height > 1024:
                return {
                    "success": False,
                    "error": "Dimensions must be between 256 and 1024 pixels"
                }
            
            # Use default values if not specified
            quality = quality or self.default_quality
            style = style or self.default_style
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"image_custom_{width}x{height}_{timestamp}.png"
            
            # Generate image
            result = self.GenerateImage(
                prompt=prompt,
                size=f"{width}x{height}",
                quality=quality,
                style=style,
                output_file=output_file
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    app = truffle.TruffleApp(DalleImageGenerator())
    app.launch() 