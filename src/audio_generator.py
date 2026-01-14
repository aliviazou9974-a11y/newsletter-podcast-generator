"""Audio generator using Google Cloud Text-to-Speech."""

import os
import json
from datetime import datetime
from google.cloud import texttospeech
from google.oauth2 import service_account


class AudioGenerator:
    """Generator for converting text to speech using Google Cloud TTS."""
    
    def __init__(self):
        """Initialize Google Cloud TTS client."""
        # Load credentials from environment
        creds_json = os.environ.get('GOOGLE_TTS_CREDENTIALS')
        if not creds_json:
            raise ValueError("GOOGLE_TTS_CREDENTIALS environment variable must be set")
        
        try:
            creds_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            self.client = texttospeech.TextToSpeechClient(credentials=credentials)
            print("✓ Google Cloud TTS initialized")
            
        except Exception as e:
            raise Exception(f"Failed to initialize TTS client: {str(e)}")
    
    def generate_podcast(
        self,
        script: str,
        output_path: str = None,
        voice_name: str = 'en-US-Neural2-J'
    ) -> str:
        """
        Convert podcast script to audio file.
        
        Args:
            script: The podcast script text
            output_path: Path to save MP3 file (default: auto-generated)
            voice_name: Google TTS voice name (default: en-US-Neural2-J male voice)
                       Options: en-US-Neural2-J (male), en-US-Neural2-F (female)
            
        Returns:
            Path to generated MP3 file
        """
        if not script:
            raise ValueError("Script is empty")
        
        # Generate output filename if not provided
        if not output_path:
            today = datetime.now().strftime("%Y-%m-%d")
            output_path = f"newsletter-podcast-{today}.mp3"
        
        print(f"Generating audio with voice '{voice_name}'...")
        print(f"Script length: {len(script)} characters ({len(script.split())} words)")
        
        try:
            # Configure synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=script)
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code='en-US',
                name=voice_name
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,  # Normal speed
                pitch=0.0,  # Normal pitch
            )
            
            # Perform text-to-speech
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio file
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✓ Podcast generated: {output_path} ({file_size_mb:.2f} MB)")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    def get_available_voices(self) -> list:
        """Get list of available Neural2 voices for en-US."""
        try:
            voices = self.client.list_voices(language_code='en-US')
            
            neural2_voices = [
                voice.name for voice in voices.voices
                if 'Neural2' in voice.name
            ]
            
            return neural2_voices
            
        except Exception as e:
            print(f"⚠ Failed to list voices: {str(e)}")
            return []
