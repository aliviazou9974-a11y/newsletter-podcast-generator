# Newsletter Podcast Generator - Design Document

**Date:** 2026-01-13
**Status:** Design Complete - Ready for Implementation

## Overview

An automated system that processes Gmail newsletters daily at 8 AM, uses AI to create intelligent summaries, generates a 30-minute podcast, and delivers it via email attachment.

## Requirements

### Functional Requirements
- Fetch newsletters from Gmail using label-based filtering
- Intelligently summarize and synthesize newsletter content using AI
- Generate 30-minute audio podcast from summarized content
- Deliver podcast as MP3 attachment via email
- Run automatically every morning at 8 AM
- Track processed newsletters to prevent re-processing

### Non-Functional Requirements
- Use only free-tier services
- Run reliably even when Mac is off/asleep
- Minimize manual maintenance
- Handle errors gracefully with notifications

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (8 AM Daily)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Gmail API: Fetch newsletters with label "newsletters-to-   │
│  podcast"                                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Gemini API: Summarize & create 30-min podcast script       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Google Cloud TTS: Convert script to MP3 audio              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Gmail API: Send MP3 as email attachment                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Mark emails: Remove "newsletters-to-podcast", add           │
│  "podcast-processed"                                         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Platform:** GitHub Actions (free tier, cloud-based)
- **Language:** Python 3.11+
- **Gmail Access:** Gmail API with OAuth 2.0
- **AI Summarization:** Google Gemini 2.0 Flash (free tier)
- **Text-to-Speech:** Google Cloud TTS Neural2 voices (free tier)
- **Scheduling:** GitHub Actions cron

## Component Designs

### 1. Gmail Integration

**Authentication:**
- Google OAuth 2.0 with Gmail API
- Create Google Cloud project (free)
- Enable Gmail API
- Generate OAuth credentials
- Store refresh token as GitHub secret (encrypted)

**Label-Based Filtering:**
- User creates Gmail label: `newsletters-to-podcast`
- Script searches: `label:newsletters-to-podcast is:unread`
- Fetches matching emails from last 24 hours
- Extracts: subject, sender, body text (HTML stripped)

**Post-Processing:**
After successful podcast generation:
- Mark emails as read
- Remove `newsletters-to-podcast` label
- Add `podcast-processed` label with timestamp

**Error Handling:**
- No newsletters found → send notification email
- Gmail API failure → retry 3 times with exponential backoff
- Log all errors to GitHub Actions

**Implementation Module:** `src/gmail_client.py`

### 2. AI Summarization Workflow

**Input Preparation:**
- Combine all newsletter content into structured prompt
- Include metadata: sender name, subject, publication date
- Format for context: "Newsletter 1 from [Sender]: [Subject]\n[Content]"

**Gemini Prompt Design:**
```
You are a podcast host creating a morning news briefing.
I've received these newsletters today:

[newsletters content with sender/subject metadata]

Create an engaging 30-minute podcast script that:
- Opens with a warm greeting and today's date
- Provides in-depth coverage of topics from the newsletters
- Groups related topics and provides context/analysis
- Uses natural, conversational tone with smooth transitions
- Includes interesting details and insights
- Ends with a comprehensive summary and sign-off

Target length: 4,000-5,000 words for 30 minutes of audio.
Format as a script ready for text-to-speech.
```

**Processing Strategy:**
- API: Gemini 2.0 Flash (free tier, fast, good quality)
- Single API call with all newsletters combined
- Token limit: ~1M input tokens (sufficient for daily newsletters)
- Temperature: 0.7 (natural but consistent tone)
- Expected output: 4,000-5,000 words

**Free Tier Limits:**
- 15 requests per minute
- 1,500 requests per day
- Well within limits for single daily run

**Implementation Module:** `src/ai_processor.py`

### 3. Podcast Generation and Delivery

**Text-to-Speech Conversion:**
- API: Google Cloud Text-to-Speech
- Voice options:
  - `en-US-Neural2-J` (male, natural)
  - `en-US-Neural2-F` (female, natural)
- Audio format: MP3, 128kbps
- Expected file size: 15-20 MB for 30 minutes
- Character count: 4,000-5,000 words (within free tier)

**Free Tier Limits:**
- Neural2 voices: 1 million characters/month free
- Daily usage: ~25,000-30,000 characters
- Monthly: ~750,000-900,000 characters (within limit)

**Podcast File Naming:**
- Format: `newsletter-podcast-YYYY-MM-DD.mp3`
- Example: `newsletter-podcast-2026-01-13.mp3`

**Email Delivery:**
- Method: Gmail API (programmatic sending)
- Subject: `Your Daily Newsletter Podcast - [Date]`
- Body: Brief summary of topics covered
- Attachment: MP3 file (15-20 MB, within 25 MB Gmail limit)
- Sent to user's Gmail address

**Fallback Strategy:**
- TTS fails → send email with text script instead
- Email sending fails → save MP3 to GitHub Actions artifacts
- All errors logged with details

**Implementation Modules:**
- `src/audio_generator.py` (TTS)
- `src/podcast_generator.py` (orchestration & email)

### 4. GitHub Actions Automation

**Repository Structure:**
```
newsletter-podcast-generator/
├── .github/
│   └── workflows/
│       └── daily-podcast.yml        # Scheduled workflow
├── src/
│   ├── gmail_client.py              # Gmail API integration
│   ├── podcast_generator.py         # Main orchestrator
│   ├── ai_processor.py              # Gemini summarization
│   └── audio_generator.py           # Google TTS
├── requirements.txt                  # Python dependencies
├── README.md                         # Setup instructions
└── docs/
    └── plans/
        └── 2026-01-13-newsletter-podcast-generator-design.md
```

**Workflow Configuration (`daily-podcast.yml`):**
```yaml
name: Daily Newsletter Podcast

on:
  schedule:
    - cron: '0 15 * * *'  # 8 AM PST (adjust for timezone)
  workflow_dispatch:       # Manual trigger for testing

jobs:
  generate-podcast:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run podcast generator
        env:
          GMAIL_CREDENTIALS: ${{ secrets.GMAIL_CREDENTIALS }}
          GMAIL_TOKEN: ${{ secrets.GMAIL_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GOOGLE_TTS_CREDENTIALS: ${{ secrets.GOOGLE_TTS_CREDENTIALS }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python src/podcast_generator.py

      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: error-logs
          path: logs/
```

**GitHub Secrets Required:**
- `GMAIL_CREDENTIALS`: OAuth credentials JSON
- `GMAIL_TOKEN`: Refresh token for authentication
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_TTS_CREDENTIALS`: Google Cloud TTS service account JSON
- `RECIPIENT_EMAIL`: User's email address for delivery

**Scheduling:**
- Cron: `0 15 * * *` (8 AM PST - adjust based on timezone)
- Runs daily, automatically
- Can be manually triggered via workflow_dispatch

**Resource Usage:**
- Runner: ubuntu-latest (free)
- Runtime: ~5-10 minutes per execution
- Monthly usage: ~150-300 minutes (within 2,000 free minutes)

## Error Handling & Edge Cases

### No Newsletters Found
- Send notification email: "No newsletters to process today"
- Log event for tracking

### API Failures
- Gmail API: Retry 3 times with exponential backoff (1s, 2s, 4s)
- Gemini API: Retry 2 times, fallback to error notification
- Google TTS: Retry 2 times, fallback to text-only email

### Rate Limits
- Gmail API: 250 quota units per user per second (sufficient)
- Gemini API: 15 RPM (only 1 request needed)
- Google TTS: No explicit rate limit on free tier

### File Size Limits
- Gmail attachment: 25 MB max (30-min MP3 is ~15-20 MB, safe)
- If exceeded: Upload to Google Drive, send link instead

### Timezone Handling
- GitHub Actions runs in UTC
- Convert cron schedule to match user's local 8 AM
- Example: PST is UTC-8, so 8 AM PST = 4 PM UTC (cron: `0 16 * * *`)

## Cost Analysis

All services used are free tier:

| Service | Free Tier Limit | Expected Daily Usage | Monthly Usage | Status |
|---------|----------------|---------------------|---------------|--------|
| GitHub Actions | 2,000 min/month | 5-10 min | 150-300 min | ✅ Safe |
| Gmail API | 1B quota/day | ~100 units | ~3,000 units | ✅ Safe |
| Gemini API | 1,500 req/day | 1 request | ~30 requests | ✅ Safe |
| Google TTS Neural2 | 1M chars/month | 25-30K chars | 750-900K chars | ✅ Safe |

**Total monthly cost: $0**

## Security Considerations

- All API credentials stored as GitHub encrypted secrets
- OAuth tokens have limited scope (Gmail read/modify)
- Service account for TTS has minimal permissions
- No credentials stored in code or logs
- GitHub Actions logs sanitize sensitive data automatically

## Setup & Deployment Steps

1. **Create GitHub Repository**
   - Initialize with Python .gitignore
   - Create directory structure

2. **Set Up Google Cloud Project**
   - Create new project
   - Enable Gmail API, Cloud TTS API
   - Create OAuth 2.0 credentials for Gmail
   - Create service account for TTS
   - Generate Gemini API key

3. **Configure GitHub Secrets**
   - Add all required secrets
   - Test secret availability

4. **Implement Python Modules**
   - `gmail_client.py`: Authentication, fetch, label management
   - `ai_processor.py`: Gemini integration, prompt engineering
   - `audio_generator.py`: Google TTS integration
   - `podcast_generator.py`: Main orchestrator

5. **Create Workflow File**
   - Configure cron schedule
   - Set up environment variables
   - Add error handling steps

6. **Test Manually**
   - Use workflow_dispatch to trigger manually
   - Verify email delivery
   - Check label management

7. **Monitor First Week**
   - Check GitHub Actions logs daily
   - Verify podcast quality
   - Adjust prompt if needed

## Testing Strategy

### Manual Testing
- Trigger workflow manually with test newsletters
- Verify each component independently
- Test error scenarios (no newsletters, API failures)

### Integration Testing
- End-to-end flow with real newsletters
- Verify email delivery and label management
- Check audio quality and length

### Monitoring
- GitHub Actions logs for execution status
- Email notifications for failures
- Weekly review of podcast quality

## Future Enhancements (Out of Scope)

- Voice customization options
- Multiple podcast lengths (5/15/30 min)
- Web dashboard for podcast history
- RSS feed for podcast subscription
- Multi-language support
- Custom summarization styles

## Success Criteria

- ✅ Podcast generated and delivered daily at 8 AM
- ✅ 30-minute audio length (±2 minutes)
- ✅ High-quality, natural-sounding voice
- ✅ Intelligent summarization that synthesizes topics
- ✅ Automated label management prevents re-processing
- ✅ Zero manual intervention required
- ✅ All services remain within free tier
- ✅ Graceful error handling with notifications

## Implementation Timeline

This is a planning document. Implementation will be handled separately using the superpowers:writing-plans and superpowers:executing-plans skills.

---

**Ready to proceed with implementation?** Use the superpowers:writing-plans skill to create a detailed implementation plan.
