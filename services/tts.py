import requests
import base64
import logging
from typing import Optional

class TTSService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.voice_id = "9cd158e5-ad4d-4849-8fe7-3c72fe1598c6"
        self.url = "https://api.cartesia.ai/tts/bytes"
    
    def text_to_speech(self, text: str) -> Optional[str]:
        if not text or not self.api_key:
            return None

        text = text[:2000]  # Increased limit for longer TTS content if needed

        payload = {
            "model_id": "sonic-2",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": self.voice_id
            },
            "output_format": {
                "container": "mp3",
                "encoding": "mp3",
                "sample_rate": 44100
            }
        }

        headers = {
            "Cartesia-Version": "2024-06-10",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return audio_base64
            elif response.status_code == 402:
                # Credits exhausted - log and return special error
                logging.error(f"Cartesia TTS credits exhausted: {response.status_code} - {response.text}")
                return "CREDITS_EXHAUSTED"
            else:
                logging.error(f"Cartesia TTS error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.error(f"TTS error: {e}")
            return None
