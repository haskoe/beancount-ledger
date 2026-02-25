"""LLM client for interacting with llama-server."""

import base64
import json
import logging
import mimetypes
import requests
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with llama-server API."""
    
    def __init__(self, endpoint: str, timeout: int = 120):
        """
        Initialize LLM client.
        
        Args:
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.chat_url = f"{endpoint}/v1/chat/completions"
    
    def generate_text(
        self, 
        prompt: str, 
        image_path: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The text prompt
            image_path: Optional path to an image file (for vision models)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if request failed
        """
        try:
            messages = []
            
            if image_path:
                # For vision models, include the image as base64 data URL
                # Read and encode the image
                image_file = Path(image_path)
                mime_type, _ = mimetypes.guess_type(str(image_file))
                if not mime_type:
                    mime_type = "image/jpeg"  # Default fallback
                
                with open(image_file, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                
                data_url = f"data:{mime_type};base64,{image_data}"
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ],
                    "cache_prompt": False
                    })
            else:
                # Text-only request
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            logger.debug(f"Sending request to {self.chat_url}")
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            logger.debug(f"Received response: {len(content)} characters")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def extract_json(self, text: str, prompt_template: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured JSON data from text using LLM.
        
        Args:
            text: The text to analyze
            prompt_template: Prompt template with {text} placeholder
            
        Returns:
            Parsed JSON object or None if extraction failed
        """
        try:
            prompt = prompt_template.format(text=text)
            response = self.generate_text(prompt, temperature=0.0)
            
            if not response:
                return None
            
            # Try to extract JSON from the response
            # Sometimes the model includes markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {response[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            return None
