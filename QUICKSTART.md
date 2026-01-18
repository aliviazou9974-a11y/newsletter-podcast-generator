# Quick Start Guide

Get your newsletter podcast system running in 30 minutes!

## Step 1: Google Cloud Setup (10 minutes)

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Click "New Project" → Name it "newsletter-podcast" → Create
   - Note your project ID

2. **Enable APIs**
   - In search bar, type "Gmail API" → Enable
   - In search bar, type "Cloud Text-to-Speech API" → Enable

3. **Create OAuth Credentials**
   - Go to "APIs & Services > Credentials"
   - Click "Create Credentials > OAuth client ID"
   - If prompted, configure consent screen:
     - User Type: External → Create
     - App name: "Newsletter Podcast"
     - Add your email as test user → Save
   - Back to Credentials, click "Create Credentials > OAuth client ID"
   - Application type: Desktop app
   - Name: "Newsletter Podcast Desktop"
   - Click Create → Download JSON
   - Save as `credentials/gmail_credentials.json` (keep it secret!)

4. **Create Service Account**
   - Go to "IAM & Admin > Service Accounts"
   - Click "Create Service Account"
   - Name: "newsletter-podcast-tts"
   - Click "Create and Continue"
   - Role: "Cloud Text-to-Speech User"
   - Click "Done"
   - Click on the service account email
   - Go to "Keys" tab → "Add Key" → "Create new key"
   - Key type: JSON → Create
   - Save as `credentials/tts_credentials.json` (keep it secret!)

5. **Get Gemini API Key**
   - Go to https://aistudio.google.com/app/apikey
   - Click "Get API key" or "Create API key"
   - Select your project
   - Copy the API key (starts with `AIza...`)

## Step 2: Generate Gmail Token (5 minutes)

1. **Install dependencies locally**
   ```bash
   pip install google-auth-oauthlib
   ```

2. **Run token generator**
   ```bash
   python scripts/generate_gmail_token.py
   ```

3. **Complete authentication**
   - Browser will open automatically
   - Sign in with your Gmail account
   - Click "Allow" to grant permissions
   - You'll see "The authentication flow has completed"
   - Close the browser

4. **Verify token created**
   - Check that `credentials/gmail_token.json` was created
   - Keep it secret!

## Step 3: Set Up Gmail Label (2 minutes)

1. **Open Gmail**
2. **Create label**
   - Click gear icon → See all settings
   - Go to "Labels" tab
   - Scroll down → "Create new label"
   - Name: `newsletters-to-podcast`
   - Click Create

3. **(Optional) Create filter**
   - Settings → Filters and Blocked Addresses
   - Create a new filter
   - From: (your newsletter sender emails)
   - Click "Create filter"
   - Check "Apply the label" → Choose `newsletters-to-podcast`
   - Click "Create filter"

## Step 4: Configure GitHub Secrets (5 minutes)

1. **Go to your repository**
   https://github.com/aliviazou9974-a11y/newsletter-podcast-generator

2. **Open Settings → Secrets and variables → Actions**

3. **Add these secrets** (click "New repository secret" for each):

   | Name | Value |
   |------|-------|
   | `GMAIL_CREDENTIALS` | Paste entire contents of `credentials/gmail_credentials.json` |
   | `GMAIL_TOKEN` | Paste entire contents of `credentials/gmail_token.json` |
   | `GEMINI_API_KEY` | Your Gemini API key (AIza...) |
   | `GOOGLE_TTS_CREDENTIALS` | Paste entire contents of `credentials/tts_credentials.json` |
   | `RECIPIENT_EMAIL` | Your Gmail address |

4. **Optional secrets** (use defaults if you skip these):
   - `NEWSLETTER_LABEL`: Custom label name (default: newsletters-to-podcast)
   - `TTS_VOICE_NAME`: Voice preference (default: en-US-Neural2-J)

## Step 5: Set Your Timezone (2 minutes)

1. **Edit `.github/workflows/daily-podcast.yml`**
2. **Find the cron line:**
   ```yaml
   - cron: '0 16 * * *'  # 8 AM PST
   ```

3. **Change to your timezone** (8 AM local time):
   - PST (UTC-8): `'0 16 * * *'`
   - EST (UTC-5): `'0 13 * * *'`
   - CST (UTC-6): `'0 14 * * *'`
   - MST (UTC-7): `'0 15 * * *'`

4. **Commit and push the change**

## Step 6: Test It! (5 minutes)

1. **Label a test newsletter**
   - Go to Gmail
   - Find any newsletter email
   - Click the label icon → Add `newsletters-to-podcast`

2. **Manually trigger workflow**
   - Go to GitHub repository
   - Click "Actions" tab
   - Select "Daily Newsletter Podcast"
   - Click "Run workflow" → "Run workflow"

3. **Watch the logs**
   - Click on the running workflow
   - Watch the steps execute
   - Should complete in 5-10 minutes

4. **Check your email!**
   - You should receive an email with the podcast MP3 attached

## Done! 🎉

Your system is now running! Every morning at 8 AM:
1. It will fetch newsletters labeled `newsletters-to-podcast`
2. Generate an AI-powered 30-minute podcast
3. Email it to you
4. Mark the newsletters as processed

## Troubleshooting

**No email received?**
- Check GitHub Actions logs for errors
- Verify all secrets are set correctly
- Make sure you have newsletters labeled

**Authentication errors?**
- Re-run `python scripts/generate_gmail_token.py`
- Double-check credentials JSON files are complete
- Verify service account has TTS role

**Need help?**
- Check README.md for detailed documentation
- Review GitHub Actions logs
- Ensure all APIs are enabled in Google Cloud

## Daily Usage

Just label your newsletters with `newsletters-to-podcast` and forget about it! The system handles everything automatically.

**To pause:**
- Disable the workflow in GitHub Actions

**To change voices:**
- Add `TTS_VOICE_NAME` secret with: en-US-Neural2-F (female) or en-US-Neural2-J (male)

Enjoy your automated morning podcast! ☕🎧
