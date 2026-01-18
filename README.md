# Newsletter Podcast Generator

Automated system that converts your Gmail newsletters into AI-generated podcasts delivered daily at 8 AM.

## Features

- 📧 Fetches newsletters from Gmail using label-based filtering
- 🤖 Uses Google Gemini AI to create intelligent 30-minute podcast summaries
- 🎙️ Converts to high-quality audio using Google Cloud Text-to-Speech
- ✉️ Emails the MP3 to your inbox automatically
- 🏷️ Manages Gmail labels to prevent re-processing
- ☁️ Runs on GitHub Actions (free tier, cloud-based)
- 💰 Uses only free-tier services (zero cost)

## Prerequisites

- Gmail account
- Google Cloud account (free tier)
- GitHub account
- Basic familiarity with terminal/command line

## Setup Instructions

### 1. Google Cloud Project Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "newsletter-podcast")
3. Enable the following APIs:
   - Gmail API
   - Cloud Text-to-Speech API
4. Note your project ID

### 2. Gmail API Setup

1. In Google Cloud Console, go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Configure consent screen if prompted:
   - User Type: External
   - App name: "Newsletter Podcast Generator"
   - Add your email as test user
4. Create OAuth 2.0 Client ID:
   - Application type: Desktop app
   - Name: "Newsletter Podcast Desktop"
5. Download the credentials JSON file
6. Save it as `credentials/gmail_credentials.json`

### 3. Generate Gmail Refresh Token

You need to generate a refresh token for Gmail API access. Run this script locally:

```python
# generate_gmail_token.py
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials/gmail_credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    'token': creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'scopes': creds.scopes
}

with open('credentials/gmail_token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("✓ Token saved to credentials/gmail_token.json")
```

Run it:
```bash
pip install google-auth-oauthlib
python scripts/generate_gmail_token.py
```

This will open a browser for authentication. Complete the flow to generate `credentials/gmail_token.json`.

### 4. Google Cloud Text-to-Speech Setup

1. In Google Cloud Console, go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**:
   - Name: "newsletter-podcast-tts"
   - Role: Cloud Text-to-Speech User
3. Click **Create Key** > JSON
4. Download and save as `credentials/tts_credentials.json`

### 5. Google Gemini API Setup

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Get API Key**
3. Create API key for your Google Cloud project
4. Copy the API key (starts with `AIza...`)

### 6. Gmail Label Setup

1. Open Gmail in your browser
2. Create a new label called `newsletters-to-podcast`
3. (Optional) Set up filters to automatically apply this label to your newsletters

### 7. GitHub Repository Setup

The repository is already created at:
https://github.com/aliviazou9974-a11y/newsletter-podcast-generator

### 8. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings > Secrets and variables > Actions**
3. Click **New repository secret** for each:

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `GMAIL_CREDENTIALS` | Content of `credentials/gmail_credentials.json` | Copy entire JSON file content |
| `GMAIL_TOKEN` | Content of `credentials/gmail_token.json` | Copy entire JSON file content |
| `GEMINI_API_KEY` | Your Gemini API key | From Google AI Studio |
| `GOOGLE_TTS_CREDENTIALS` | Content of `credentials/tts_credentials.json` | Copy entire JSON file content |
| `RECIPIENT_EMAIL` | Your email address | Your Gmail address for delivery |

**Optional secrets:**
| Secret Name | Default Value | Description |
|-------------|---------------|-------------|
| `NEWSLETTER_LABEL` | `newsletters-to-podcast` | Gmail label to filter |
| `TTS_VOICE_NAME` | `en-US-Neural2-J` | Voice name (J=male, F=female) |

### 9. Adjust Timezone

Edit `.github/workflows/daily-podcast.yml`:

```yaml
schedule:
  - cron: '0 16 * * *'  # Change this for your timezone
```

Timezone conversion (8 AM local time):
- PST (UTC-8): `0 16 * * *`
- EST (UTC-5): `0 13 * * *`
- CST (UTC-6): `0 14 * * *`
- MST (UTC-7): `0 15 * * *`

Use this formula: `8 AM + (0 - your_UTC_offset) = UTC_time`

### 10. Test the Workflow

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Daily Newsletter Podcast** workflow
4. Click **Run workflow > Run workflow**
5. Check the logs to verify it works

## Usage

### Daily Automation

Once set up, the system runs automatically every day at 8 AM:

1. Labels your desired newsletters with `newsletters-to-podcast`
2. The workflow fetches them, generates a podcast, and emails it to you
3. Processed newsletters are marked and moved to `podcast-processed` label

### Manual Trigger

To generate a podcast on-demand:

1. Go to **Actions** tab in your GitHub repository
2. Select **Daily Newsletter Podcast**
3. Click **Run workflow**

## File Structure

```
newsletter-podcast-generator/
├── .github/
│   └── workflows/
│       └── daily-podcast.yml      # GitHub Actions workflow
├── src/
│   ├── gmail_client.py            # Gmail API integration
│   ├── podcast_generator.py       # Main orchestrator
│   ├── ai_processor.py            # Gemini AI summarization
│   └── audio_generator.py         # Google TTS
├── credentials/                    # Secret files (git-ignored)
│   ├── gmail_credentials.json     # OAuth client credentials
│   ├── gmail_token.json           # Gmail refresh token
│   └── tts_credentials.json       # TTS service account
├── scripts/                        # Utility scripts
│   ├── generate_gmail_token.py    # Token generation helper
│   └── gemini_test.py             # API testing utility
├── experiments/                    # Experimental code
│   └── gemini.mjs                 # Node.js alternative
├── docs/
│   └── plans/
│       └── 2026-01-13-newsletter-podcast-generator-design.md
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md
```

## Troubleshooting

### No podcast received

1. Check GitHub Actions logs for errors
2. Verify you have newsletters labeled `newsletters-to-podcast`
3. Ensure all secrets are correctly set in GitHub

### Authentication errors

- Re-generate Gmail token using the script above
- Verify service account has correct permissions
- Check API keys are valid and not expired

### Podcast quality issues

- Change voice by setting `TTS_VOICE_NAME` secret:
  - Male voices: `en-US-Neural2-A`, `en-US-Neural2-D`, `en-US-Neural2-J`
  - Female voices: `en-US-Neural2-C`, `en-US-Neural2-E`, `en-US-Neural2-F`

### Workflow not running at scheduled time

- GitHub Actions can be delayed up to 15 minutes during high load
- Check the cron expression matches your desired timezone

## Cost Analysis

All services are within free tiers:

| Service | Free Tier | Expected Usage | Status |
|---------|-----------|----------------|--------|
| GitHub Actions | 2,000 min/month | ~150-300 min/month | ✅ Free |
| Gmail API | 1B quota/day | ~3,000 units/month | ✅ Free |
| Gemini API | 1,500 req/day | ~30 requests/month | ✅ Free |
| Google TTS | 1M chars/month | ~750K chars/month | ✅ Free |

**Total cost: $0/month**

## Security Notes

- All credentials are stored as encrypted GitHub secrets
- Never commit credentials to the repository
- OAuth tokens have limited scopes (read/modify Gmail only)
- Service accounts have minimal permissions

## Advanced Configuration

### Custom Podcast Length

Edit the prompt in `src/ai_processor.py` to change target word count:
- 5 minutes: ~750 words
- 15 minutes: ~2,000 words
- 30 minutes: ~4,000-5,000 words
- 60 minutes: ~8,000-9,000 words

### Multiple Newsletters

The system automatically processes all newsletters with the specified label. No limit on number of newsletters.

### Voice Customization

Available Neural2 voices:
- `en-US-Neural2-A`: Male
- `en-US-Neural2-C`: Female
- `en-US-Neural2-D`: Male
- `en-US-Neural2-E`: Female
- `en-US-Neural2-F`: Female
- `en-US-Neural2-J`: Male (default)

## Contributing

This is a personal project. Feel free to fork and customize for your needs.

## License

MIT License - Feel free to use and modify.

## Support

For issues, check the GitHub Actions logs or review the design document in `docs/plans/`.
