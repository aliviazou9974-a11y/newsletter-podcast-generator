"""AI processor for summarizing newsletters using Google Gemini."""

import os
from typing import List, Dict
from datetime import datetime

import google.generativeai as genai


class AIProcessor:
    """Processor for creating podcast scripts from newsletters using Gemini."""
    
    def __init__(self):
        """Initialize Gemini AI client."""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        genai.configure(api_key=api_key)

        # Use Gemini Pro for free tier (stable, widely available model)
        self.model = genai.GenerativeModel('gemini-pro')

        print("✓ Gemini AI initialized")
    
    def create_podcast_script(self, newsletters: List[Dict]) -> str:
        """
        Create a 30-minute podcast script from newsletters.
        
        Args:
            newsletters: List of newsletter dicts with subject, sender, body
            
        Returns:
            Podcast script as string (4000-5000 words for 30 minutes)
        """
        if not newsletters:
            raise ValueError("No newsletters provided")
        
        print(f"Creating podcast script from {len(newsletters)} newsletter(s)...")
        
        # Prepare newsletter content
        newsletter_content = self._format_newsletters(newsletters)
        
        # Create prompt
        prompt = self._create_prompt(newsletter_content)
        
        try:
            # Generate script
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8000,
                )
            )
            
            script = response.text.strip()
            
            word_count = len(script.split())
            print(f"✓ Podcast script generated ({word_count} words)")
            
            return script
            
        except Exception as e:
            raise Exception(f"Failed to generate podcast script: {str(e)}")
    
    def _format_newsletters(self, newsletters: List[Dict]) -> str:
        """Format newsletters for inclusion in prompt."""
        formatted = []
        
        for i, newsletter in enumerate(newsletters, 1):
            formatted.append(f"--- Newsletter {i} ---")
            formatted.append(f"From: {newsletter['sender']}")
            formatted.append(f"Subject: {newsletter['subject']}")
            formatted.append(f"Date: {newsletter.get('date', 'Unknown')}")
            formatted.append("")
            
            # Limit body length to avoid token limits
            body = newsletter['body']
            if len(body) > 10000:
                body = body[:10000] + "... [truncated]"
            
            formatted.append(body)
            formatted.append("")
            formatted.append("=" * 80)
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _create_prompt(self, newsletter_content: str) -> str:
        """Create prompt for Gemini."""
        today = datetime.now().strftime("%A, %B %d, %Y")
        
        prompt = f"""You are an engaging podcast host creating a morning news briefing for {today}.

I've received these newsletters today:

{newsletter_content}

Your task: Create an engaging, conversational 30-minute podcast script (approximately 4,000-5,000 words).

Guidelines:
1. **Opening** (1-2 minutes):
   - Warm, friendly greeting
   - Mention today's date
   - Brief preview of what topics you'll cover

2. **Main Content** (26-27 minutes):
   - Provide in-depth coverage of the most important and interesting topics from the newsletters
   - Group related topics together across different newsletters
   - Add context and analysis - don't just repeat what was written
   - Use smooth transitions between topics
   - Maintain a conversational, natural tone as if speaking to a friend
   - Include interesting details, insights, and implications
   - Vary your pacing - some topics deserve more time than others

3. **Closing** (1-2 minutes):
   - Comprehensive summary of key takeaways
   - Warm sign-off
   - Mention it's an automated briefing

Style notes:
- Write exactly as you would speak - use contractions, natural pauses, conversational phrases
- Include verbal transitions like "Now, moving on to...", "This is particularly interesting because...", "What's fascinating here is..."
- Add personality - occasional light humor or enthusiasm when appropriate
- Avoid overly formal or written language
- Don't mention that this is text or that you're an AI - speak as a podcast host

Format:
- Write the complete script ready for text-to-speech
- No special formatting, just natural speech
- No stage directions or sound effect notes
- Target length: 4,000-5,000 words for 30 minutes of speaking

Begin the podcast script:"""

        return prompt
    
    def create_notification_message(self, newsletters: List[Dict], podcast_file: str) -> str:
        """
        Create email body for podcast delivery.
        
        Args:
            newsletters: List of newsletters that were processed
            podcast_file: Name of the podcast file
            
        Returns:
            Email body text
        """
        today = datetime.now().strftime("%B %d, %Y")
        
        message = f"""Good morning!

Your daily newsletter podcast for {today} is ready. This 30-minute briefing covers the following newsletters:

"""
        
        for i, newsletter in enumerate(newsletters, 1):
            sender = newsletter['sender'].split('<')[0].strip()
            message += f"{i}. {newsletter['subject']}\n   From: {sender}\n\n"
        
        message += f"""
The podcast is attached as {podcast_file}.

Enjoy your listening!

---
This podcast was automatically generated by the newsletter-podcast-generator system.
"""
        
        return message
