"""Main orchestrator for newsletter-to-podcast generation."""

import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from gmail_client import GmailClient
from ai_processor import AIProcessor
from audio_generator import AudioGenerator


def main():
    """Main function to orchestrate podcast generation."""
    print("=" * 80)
    print("Newsletter Podcast Generator")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Get configuration from environment
        recipient_email = os.environ.get('RECIPIENT_EMAIL')
        if not recipient_email:
            raise ValueError("RECIPIENT_EMAIL environment variable must be set")
        
        newsletter_label = os.environ.get('NEWSLETTER_LABEL', 'newsletters-to-podcast')
        voice_name = os.environ.get('TTS_VOICE_NAME', 'en-US-Neural2-J')
        
        # Initialize clients
        print("Initializing services...")
        gmail_client = GmailClient()
        ai_processor = AIProcessor()
        audio_generator = AudioGenerator()
        print()
        
        # Fetch newsletters
        print("Fetching newsletters...")
        newsletters = gmail_client.fetch_newsletters(label_name=newsletter_label)
        print()
        
        if not newsletters:
            # Send notification that no newsletters were found
            print("No newsletters to process. Sending notification...")
            gmail_client.send_email_with_attachment(
                recipient=recipient_email,
                subject=f"No Newsletters Today - {datetime.now().strftime('%B %d, %Y')}",
                body="No new newsletters were found with the specified label today.\n\nEnjoy your day!",
                attachment_path=None
            )
            print("✓ Notification sent")
            return 0
        
        # Create podcast script
        print("Generating podcast script with AI...")
        script = ai_processor.create_podcast_script(newsletters)
        print()
        
        # Generate audio
        print("Converting script to audio...")
        podcast_file, usage_check = audio_generator.generate_podcast(
            script=script,
            voice_name=voice_name
        )
        print()

        # Create email body
        email_body = ai_processor.create_notification_message(newsletters, podcast_file)

        # Add usage warning to email if threshold exceeded
        if usage_check['percent'] >= AudioGenerator.WARNING_THRESHOLD_PCT:
            email_body += f"\n\n---\n⚠️ TTS Usage Alert:\n{usage_check['message']}\n"

        # Send podcast via email
        print("Sending podcast via email...")
        gmail_client.send_email_with_attachment(
            recipient=recipient_email,
            subject=f"Your Daily Newsletter Podcast - {datetime.now().strftime('%B %d, %Y')}",
            body=email_body,
            attachment_path=podcast_file
        )
        print()

        # Send separate alert email if critical threshold reached
        if usage_check['percent'] >= AudioGenerator.CRITICAL_THRESHOLD_PCT:
            print("⚠️ Sending critical usage alert...")
            gmail_client.send_email_with_attachment(
                recipient=recipient_email,
                subject="🚨 CRITICAL: TTS Free Tier Almost Exhausted",
                body=f"""CRITICAL ALERT: Your Text-to-Speech free tier usage is at {usage_check['percent']:.1f}%!

Current usage: {usage_check['current_usage']:,}/{usage_check['limit']:,} characters
Remaining: {usage_check['remaining']:,} characters

The system will automatically stop generating podcasts if you hit 100% to prevent charges.

Actions you can take:
1. Wait until next month (usage resets monthly)
2. Add a billing account and upgrade to paid tier
3. Reduce podcast length in the code

Monthly usage resets on: {datetime.now().strftime('%Y-%m-01')}

This is an automated alert from newsletter-podcast-generator.
""",
                attachment_path=None
            )
            print("✓ Critical alert sent")
        print()
        
        # Mark newsletters as processed
        print("Marking newsletters as processed...")
        message_ids = [n['id'] for n in newsletters]
        gmail_client.mark_as_processed(message_ids, source_label=newsletter_label)
        print()
        
        # Cleanup
        if os.path.exists(podcast_file):
            os.remove(podcast_file)
            print(f"✓ Cleaned up temporary file: {podcast_file}")
        
        print()
        print("=" * 80)
        print("✓ Podcast generation completed successfully!")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        return 1
        
    except Exception as e:
        print()
        print("=" * 80)
        print("✗ Error occurred:")
        print(str(e))
        print("=" * 80)
        
        # Try to send error notification
        try:
            recipient_email = os.environ.get('RECIPIENT_EMAIL')
            if recipient_email:
                gmail_client = GmailClient()
                gmail_client.send_email_with_attachment(
                    recipient=recipient_email,
                    subject=f"Podcast Generation Failed - {datetime.now().strftime('%B %d, %Y')}",
                    body=f"An error occurred while generating your podcast:\n\n{str(e)}\n\nPlease check the logs for more details.",
                    attachment_path=None
                )
                print("\n⚠ Error notification sent to recipient")
        except:
            pass
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
