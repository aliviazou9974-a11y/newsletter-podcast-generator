"""Gmail client for fetching and managing newsletter emails."""

import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailClient:
    """Client for interacting with Gmail API."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self):
        """Initialize Gmail client with credentials."""
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using environment variables."""
        try:
            # Load credentials from environment variable
            creds_json = os.environ.get('GMAIL_CREDENTIALS')
            token_json = os.environ.get('GMAIL_TOKEN')
            
            if not creds_json or not token_json:
                raise ValueError("GMAIL_CREDENTIALS and GMAIL_TOKEN must be set")
            
            # Parse credentials
            creds_info = json.loads(creds_json)
            token_info = json.loads(token_json)
            
            # Create credentials object
            creds = Credentials(
                token=token_info.get('token'),
                refresh_token=token_info.get('refresh_token'),
                token_uri=creds_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=creds_info.get('client_id'),
                client_secret=creds_info.get('client_secret'),
                scopes=self.SCOPES
            )
            
            # Refresh if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            print("✓ Gmail authentication successful")
            
        except Exception as e:
            raise Exception(f"Failed to authenticate with Gmail: {str(e)}")
    
    def fetch_newsletters(self, label_name: str = 'newsletters-to-podcast') -> List[Dict]:
        """
        Fetch unread emails with specified label from last 24 hours.

        Args:
            label_name: Gmail label to filter by

        Returns:
            List of newsletter dicts with id, subject, sender, body, date
        """
        try:
            newsletters = []

            # Get label ID
            label_id = self._get_label_id(label_name)
            if not label_id:
                print(f"⚠ Label '{label_name}' not found. Please create it in Gmail.")
                return newsletters

            # Calculate date for 24 hours ago (Gmail format: YYYY/MM/DD)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')

            # Search for messages: unread, with label, from last 24 hours only
            query = f'label:{label_name} is:unread after:{yesterday}'
            print(f"Searching for: {query}")

            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print(f"No unread newsletters found with label '{label_name}'")
                return newsletters
            
            print(f"Found {len(messages)} newsletter(s) to process")
            
            # Fetch full message details
            for msg in messages:
                try:
                    message = self._retry_api_call(
                        lambda: self.service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()
                    )
                    
                    newsletter = self._parse_message(message)
                    if newsletter:
                        newsletters.append(newsletter)
                    
                except Exception as e:
                    print(f"⚠ Failed to fetch message {msg['id']}: {str(e)}")
                    continue
            
            return newsletters
            
        except Exception as e:
            raise Exception(f"Failed to fetch newsletters: {str(e)}")
    
    def _get_label_id(self, label_name: str) -> Optional[str]:
        """Get label ID by name."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']
            
            return None
            
        except Exception as e:
            print(f"⚠ Failed to get labels: {str(e)}")
            return None
    
    def _parse_message(self, message: Dict) -> Optional[Dict]:
        """Parse Gmail message into newsletter dict."""
        try:
            headers = message['payload']['headers']
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract body
            body = self._get_message_body(message['payload'])
            
            if not body:
                return None
            
            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date_str,
                'body': body
            }
            
        except Exception as e:
            print(f"⚠ Failed to parse message: {str(e)}")
            return None
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract text body from message payload."""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        # Fallback to HTML if no plain text
                        html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        body = self._strip_html(html)
                elif 'parts' in part:
                    # Recursive for nested parts
                    body = self._get_message_body(part)
                    if body:
                        break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            if payload.get('mimeType') == 'text/html':
                body = self._strip_html(body)
        
        return body.strip()
    
    def _strip_html(self, html: str) -> str:
        """Simple HTML tag stripper."""
        import re
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        html = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)
        return html.strip()
    
    def mark_as_processed(self, message_ids: List[str], source_label: str = 'newsletters-to-podcast'):
        """
        Mark newsletters as processed by removing source label and adding processed label.
        
        Args:
            message_ids: List of message IDs to mark
            source_label: Label to remove
        """
        try:
            # Get or create labels
            source_label_id = self._get_label_id(source_label)
            processed_label_id = self._get_or_create_label('podcast-processed')
            
            if not source_label_id or not processed_label_id:
                raise ValueError("Failed to get label IDs")
            
            for msg_id in message_ids:
                try:
                    # Modify labels
                    self._retry_api_call(
                        lambda: self.service.users().messages().modify(
                            userId='me',
                            id=msg_id,
                            body={
                                'removeLabelIds': [source_label_id, 'UNREAD'],
                                'addLabelIds': [processed_label_id]
                            }
                        ).execute()
                    )
                    
                except Exception as e:
                    print(f"⚠ Failed to mark message {msg_id} as processed: {str(e)}")
            
            print(f"✓ Marked {len(message_ids)} newsletter(s) as processed")
            
        except Exception as e:
            raise Exception(f"Failed to mark newsletters as processed: {str(e)}")
    
    def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID or create if doesn't exist."""
        # Check if exists
        label_id = self._get_label_id(label_name)
        if label_id:
            return label_id
        
        # Create new label
        try:
            label = self.service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            
            print(f"✓ Created label '{label_name}'")
            return label['id']
            
        except Exception as e:
            raise Exception(f"Failed to create label '{label_name}': {str(e)}")
    
    def send_email_with_attachment(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None
    ):
        """
        Send email with optional audio attachment.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachment_path: Path to audio file to attach
        """
        try:
            message = MIMEMultipart()
            message['to'] = recipient
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    audio = MIMEAudio(f.read(), _subtype='mpeg')
                    audio.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(attachment_path)
                    )
                    message.attach(audio)
            
            # Send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self._retry_api_call(
                lambda: self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            )
            
            print(f"✓ Email sent to {recipient}")
            
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
    
    def _retry_api_call(self, func, max_retries: int = 3):
        """Retry API call with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except HttpError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"⚠ API call failed, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
