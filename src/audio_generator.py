"""Audio generator using Google Cloud Text-to-Speech."""

import os
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from google.cloud import texttospeech
from google.oauth2 import service_account
from pydub import AudioSegment


class AudioGenerator:
    """Generator for converting text to speech using Google Cloud TTS."""

    # Free tier limit for Neural2 voices: 1 million characters/month
    MONTHLY_CHAR_LIMIT = 1_000_000
    WARNING_THRESHOLD_PCT = 80  # Warn at 80% usage
    CRITICAL_THRESHOLD_PCT = 90  # Critical alert at 90% usage
    # Google TTS has a limit on sentence length - be conservative
    MAX_SENTENCE_LENGTH = 250

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

            # Initialize usage tracking
            self.usage_file = Path('tts_usage.json')
            self._load_usage()

            print("✓ Google Cloud TTS initialized")

        except Exception as e:
            raise Exception(f"Failed to initialize TTS client: {str(e)}")

    def _load_usage(self):
        """Load usage data from file."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    current_month = datetime.now().strftime("%Y-%m")

                    # Reset if new month
                    if data.get('month') != current_month:
                        self.usage_data = {
                            'month': current_month,
                            'characters_used': 0,
                            'requests': []
                        }
                    else:
                        self.usage_data = data
            except Exception as e:
                print(f"⚠ Failed to load usage data: {e}, resetting...")
                self._reset_usage()
        else:
            self._reset_usage()

    def _reset_usage(self):
        """Reset usage data for new month."""
        self.usage_data = {
            'month': datetime.now().strftime("%Y-%m"),
            'characters_used': 0,
            'requests': []
        }
        self._save_usage()

    def _save_usage(self):
        """Save usage data to file."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"⚠ Failed to save usage data: {e}")

    def _check_usage_limit(self, script_length: int) -> dict:
        """
        Check if generating audio would exceed free tier limits.

        Returns:
            dict with 'allowed', 'current_usage', 'would_be', 'percent', 'message'
        """
        current = self.usage_data['characters_used']
        would_be = current + script_length
        percent = (would_be / self.MONTHLY_CHAR_LIMIT) * 100

        result = {
            'allowed': would_be <= self.MONTHLY_CHAR_LIMIT,
            'current_usage': current,
            'would_be': would_be,
            'percent': percent,
            'limit': self.MONTHLY_CHAR_LIMIT,
            'remaining': self.MONTHLY_CHAR_LIMIT - current
        }

        if not result['allowed']:
            result['message'] = (
                f"🚨 FREE TIER LIMIT EXCEEDED! This request would use {would_be:,} "
                f"characters, exceeding the {self.MONTHLY_CHAR_LIMIT:,} monthly limit. "
                f"Current usage: {current:,} ({(current/self.MONTHLY_CHAR_LIMIT)*100:.1f}%)"
            )
        elif percent >= self.CRITICAL_THRESHOLD_PCT:
            result['message'] = (
                f"⚠️ CRITICAL: Approaching free tier limit! This request would reach "
                f"{percent:.1f}% of monthly quota. Current: {current:,}, "
                f"Would be: {would_be:,}/{self.MONTHLY_CHAR_LIMIT:,}"
            )
        elif percent >= self.WARNING_THRESHOLD_PCT:
            result['message'] = (
                f"⚠ Warning: {percent:.1f}% of monthly quota would be used. "
                f"Current: {current:,}, Would be: {would_be:,}/{self.MONTHLY_CHAR_LIMIT:,}"
            )
        else:
            result['message'] = (
                f"✓ Usage OK: {percent:.1f}% of quota. "
                f"Remaining: {self.MONTHLY_CHAR_LIMIT - would_be:,} characters"
            )

        return result

    def _record_usage(self, characters_used: int):
        """Record TTS usage."""
        self.usage_data['characters_used'] += characters_used
        self.usage_data['requests'].append({
            'timestamp': datetime.now().isoformat(),
            'characters': characters_used
        })
        self._save_usage()
        print(f"📊 Monthly TTS usage: {self.usage_data['characters_used']:,}/{self.MONTHLY_CHAR_LIMIT:,} "
              f"({(self.usage_data['characters_used']/self.MONTHLY_CHAR_LIMIT)*100:.1f}%)")
    
    def generate_podcast(
        self,
        script: str,
        output_path: str = None,
        voice_name: str = 'en-US-Neural2-J'
    ) -> tuple:
        """
        Convert podcast script to audio file.

        Args:
            script: The podcast script text
            output_path: Path to save MP3 file (default: auto-generated)
            voice_name: Google TTS voice name (default: en-US-Neural2-J male voice)
                       Options: en-US-Neural2-J (male), en-US-Neural2-F (female)

        Returns:
            Tuple of (output_path, usage_check_result)
        """
        if not script:
            raise ValueError("Script is empty")

        script_length = len(script)

        # Check usage limits BEFORE generating
        usage_check = self._check_usage_limit(script_length)
        print(f"\n{usage_check['message']}\n")

        # If would exceed limit, raise exception
        if not usage_check['allowed']:
            raise Exception(
                f"Cannot generate podcast: would exceed free tier limit. "
                f"Current usage: {usage_check['current_usage']:,}/{usage_check['limit']:,} characters "
                f"({usage_check['percent']:.1f}%). This request needs {script_length:,} characters. "
                f"Please wait until next month or upgrade to paid tier."
            )

        # Generate output filename if not provided
        if not output_path:
            today = datetime.now().strftime("%Y-%m-%d")
            output_path = f"newsletter-podcast-{today}.mp3"

        print(f"Generating audio with voice '{voice_name}'...")
        print(f"Script length: {script_length:,} characters ({len(script.split())} words)")

        try:
            # Split script into chunks if needed (TTS limit is 5000 bytes)
            chunks = self._split_script(script, max_bytes=4900)
            print(f"Split into {len(chunks)} chunk(s)")

            if len(chunks) == 1:
                # Single chunk - process normally
                response = self._synthesize_chunk(script, voice_name)
                with open(output_path, 'wb') as out:
                    out.write(response.audio_content)
            else:
                # Multiple chunks - synthesize each and concatenate
                temp_files = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"  Generating chunk {i}/{len(chunks)}...")
                    response = self._synthesize_chunk(chunk, voice_name)

                    # Save to temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_file.write(response.audio_content)
                    temp_file.close()
                    temp_files.append(temp_file.name)

                # Concatenate all chunks
                print(f"  Combining {len(temp_files)} audio chunks...")
                combined = AudioSegment.empty()
                for temp_file in temp_files:
                    chunk_audio = AudioSegment.from_mp3(temp_file)
                    combined += chunk_audio
                    os.unlink(temp_file)  # Clean up temp file

                # Export combined audio
                combined.export(output_path, format='mp3', bitrate='128k')

            # Record usage AFTER successful generation
            self._record_usage(script_length)

            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✓ Podcast generated: {output_path} ({file_size_mb:.2f} MB)")

            return output_path, usage_check

        except Exception as e:
            raise Exception(f"Failed to generate audio: {str(e)}")

    def _break_long_sentence(self, sentence: str) -> list:
        """
        Break a long sentence into smaller parts at natural punctuation points.
        Google TTS fails on sentences that are too long.
        """
        if len(sentence) <= self.MAX_SENTENCE_LENGTH:
            return [sentence]

        parts = []
        remaining = sentence

        while len(remaining) > self.MAX_SENTENCE_LENGTH:
            search_area = remaining[:self.MAX_SENTENCE_LENGTH]
            break_point = None

            # Try to break at natural punctuation: semicolon, colon, dash, comma
            # Look for the last occurrence of each, prefer stronger punctuation
            for punct in ['. ', '! ', '? ', '; ', ': ', ' - ', ' -- ', ', ', ' ']:
                last_pos = search_area.rfind(punct)
                # Accept break point if it's not too early (at least 1/4 into the text)
                if last_pos > self.MAX_SENTENCE_LENGTH // 4:
                    break_point = last_pos + len(punct)
                    break

            # If still no break point, force break at last space
            if break_point is None:
                last_space = search_area.rfind(' ')
                if last_space > 0:
                    break_point = last_space + 1
                else:
                    # No space at all - hard break (shouldn't happen with normal text)
                    break_point = self.MAX_SENTENCE_LENGTH

            part = remaining[:break_point].strip()
            if part:
                # Add period if the part doesn't end with sentence-ending punctuation
                if part[-1] not in '.!?':
                    # Remove trailing comma/semicolon before adding period
                    part = part.rstrip(',;:')
                    part += '.'
                parts.append(part)

            remaining = remaining[break_point:].strip()

        if remaining:
            parts.append(remaining)

        return parts

    def _preprocess_script(self, script: str) -> str:
        """
        Preprocess script to ensure all sentences are within TTS limits.
        Uses aggressive splitting to avoid Google TTS sentence length errors.
        """
        # First, normalize newlines and split on them
        script = script.replace('\r\n', '\n').replace('\r', '\n')

        # Split on sentence endings AND newlines
        # This pattern splits on .!? followed by space/newline, or just newlines
        segments = re.split(r'(?<=[.!?])\s+|\n+', script)

        processed = []
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            # If segment is short enough, keep it
            if len(segment) <= self.MAX_SENTENCE_LENGTH:
                processed.append(segment)
            else:
                # Break long segment into smaller parts
                parts = self._break_long_sentence(segment)
                processed.extend(parts)

        # Join and do a final safety check - split any remaining long segments
        result = ' '.join(processed)

        # Final pass: ensure no segment between periods is too long
        final_parts = []
        for part in result.split('. '):
            part = part.strip()
            if not part:
                continue
            if len(part) <= self.MAX_SENTENCE_LENGTH:
                final_parts.append(part)
            else:
                # Force break at word boundaries
                words = part.split()
                current = ""
                for word in words:
                    test = current + " " + word if current else word
                    if len(test) > self.MAX_SENTENCE_LENGTH:
                        if current:
                            final_parts.append(current.rstrip(',;:') + '.')
                        current = word
                    else:
                        current = test
                if current:
                    final_parts.append(current)

        return '. '.join(final_parts)

    def _split_script(self, script: str, max_bytes: int = 4900) -> list:
        """
        Split script into chunks that fit within TTS byte limit.
        First breaks long sentences, then splits at sentence boundaries.
        """
        # First, preprocess to break any long sentences
        script = self._preprocess_script(script)

        if len(script.encode('utf-8')) <= max_bytes:
            return [script]

        chunks = []
        current_chunk = ""

        # Split by sentences
        sentences = script.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')

        for sentence in sentences:
            test_chunk = current_chunk + sentence
            if len(test_chunk.encode('utf-8')) > max_bytes:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is still too long after preprocessing - force split at word boundary
                    words = sentence.split()
                    temp = ""
                    for word in words:
                        test = temp + " " + word if temp else word
                        if len(test.encode('utf-8')) > max_bytes:
                            if temp:
                                chunks.append(temp.strip())
                            temp = word
                        else:
                            temp = test
                    current_chunk = temp
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _synthesize_chunk(self, text: str, voice_name: str):
        """Synthesize a single text chunk."""
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code='en-US',
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )

        return self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

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
