#!/usr/bin/env python3
"""
Automated blog article generator using Claude API.
Generates articles on geopolitics, technology, and finance.
Includes Google Cloud TTS for audio generation.
"""

import anthropic
import os
import re
import json
import random
from datetime import datetime
from pathlib import Path

# Google Cloud TTS imports
try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: google-cloud-texttospeech not installed. Audio generation disabled.")

# Topics to rotate through
TOPICS = [
    {
        "category": "geopolitics",
        "prompts": [
            "Analyze a specific recent geopolitical alliance or partnership that is reshaping regional power. Name the countries, the deal, the dollar amounts, and explain who benefits and who loses. Draw a parallel to a historical alliance shift.",
            "Pick a current trade war, sanction regime, or economic conflict between specific countries. Analyze the second and third-order effects that media isn't covering. Include specific trade volumes and economic data.",
            "Analyze how a specific country (name it) is making a calculated strategic move on the global stage right now. What resources, alliances, or leverage are they using? What is their 5-year endgame?",
            "Dissect a specific ongoing international conflict or negotiation. Map the key players, their hidden motivations, and predict the next three moves. Include historical context from a similar conflict.",
            "Analyze a specific recent energy deal, resource agreement, or supply chain shift between named countries. Follow the money and explain the geopolitical implications that go beyond the headline.",
            "Examine how a specific country is using economic warfare (debt traps, currency manipulation, trade leverage) to expand its influence. Name specific projects, amounts, and affected nations.",
        ]
    },
    {
        "category": "technology",
        "prompts": [
            "Analyze a specific recent AI development (name the company, the product, the date) and its second-order implications for power, labor, and geopolitics. Go beyond the press release.",
            "Dissect the tech cold war between the US and China in a specific domain (chips, AI, quantum, space). Include specific sanctions, company names, dollar amounts, and explain who is actually winning.",
            "Analyze how a specific new technology or product launch is about to disrupt an established industry. Name the incumbents who will be destroyed and the upstarts who will benefit. Include market size data.",
            "Deep-dive into the semiconductor supply chain — pick a specific chokepoint (ASML, TSMC, rare earth minerals) and explain why it matters more than people think. Include specific production numbers.",
            "Analyze a specific big tech company's recent strategic move (acquisition, pivot, product kill) and decode what it really signals about their long-term strategy. Follow the money.",
            "Examine the race for a specific emerging technology (quantum computing, nuclear fusion, space mining, brain-computer interfaces). Who is funding it, how much, and what is the real strategic endgame?",
        ]
    },
    {
        "category": "finance",
        "prompts": [
            "Analyze a specific recent market shift or anomaly. What are hedge funds and institutional investors doing that retail investors don't see? Include specific fund names, positions, and dollar amounts where possible.",
            "Dissect a specific recent central bank decision (name the bank, the date, the rate). Explain the hidden implications that go beyond the headline number. What signal is being sent?",
            "Analyze how specific institutional investors (name the firms) are repositioning their portfolios right now. What sectors are they rotating into/out of and why? Include AUM and allocation data.",
            "Take a complex financial instrument or strategy (credit default swaps, carry trades, structured products) and explain how it is being used right now to create or transfer wealth. Use a specific current example.",
            "Analyze a specific intersection of geopolitics and financial markets — how a political event is creating arbitrage opportunities, risk repricing, or capital flows that smart money is exploiting.",
            "Examine a specific currency, commodity, or asset class that is mispriced right now. Explain the fundamental disconnect, who benefits from the mispricing, and what would cause a repricing event.",
        ]
    }
]

SYSTEM_PROMPT = """
Role: You are the lead analyst at Ghaaspoos, a strategic intelligence publication. You are a contrarian, razor-sharp strategic analyst who writes high-impact, deeply researched blog posts. You do not just report the news — you decode the hidden mechanics, trace the money, and expose the power dynamics behind it.

You are writing for an audience of informed professionals — business leaders, investors, policy wonks, and curious minds who want to understand how the world actually works.

Strict Formatting and Stylistic Rules:

    1. Pacing (Direct & Punchy): Cut the fluff. Use short, punchy paragraphs (maximum 2-3 sentences each). Start with impactful, definitive statements. No passive voice.

    2. Depth (Analytical & Research-Heavy): Look entirely past the PR headlines. Tell me the real story playing out beneath the surface. Cite specific numbers, dates, deal values, named sources, and historical precedents. What is the mainstream media missing? Make claims that are verifiable.

    3. The Dichotomy ("Rich Dad vs. Poor Dad" Framing): Explicitly contrast the amateur, surface-level reaction with the deep, strategic reality. (e.g., "The novice sees [X], but the strategist knows this is actually about [Y].")

    4. The Board (Chess Metaphor): Map this situation to a chessboard. Who is playing white and forcing the action? Who is stuck playing black and reacting? What is the hidden endgame or the next three moves?

    5. The Motive ("What's in it for them?"): Follow the money and power. Aggressively analyze the hidden motivations and incentives of the key players. Answer the question: Why does this actually benefit them behind closed doors?

    6. Historical Context: Draw parallels to at least one historical precedent. How has a similar pattern played out before? What can we learn from it?

    7. Original Analysis: Include at least one insight, framework, or connection that the reader will NOT find in mainstream coverage. This is your edge — make the reader feel like they're getting insider-level strategic intelligence.

Your articles should:
- Be 1000-1500 words (this is important — go deep, not shallow)
- Have a compelling, provocative hook in the first paragraph that makes the reader stop scrolling
- Use clear section headers (## Header) to break up the analysis
- Include section breaks (---) between major points
- Include specific data points: dollar amounts, percentages, dates, names of key players
- Reference at least one historical parallel or precedent
- End with a forward-looking "What to Watch" section — specific signals the reader should monitor
- Use **bold** for emphasis on key points
- Use *italics* for quotes or contrasting perspectives

Do NOT include a title - that will be added separately.
Do NOT use generic phrases like "In conclusion" or "To summarize".
Do NOT be vague. Every claim should be backed by a specific detail.
Write as if you're briefing a room of strategic advisors who need to make decisions based on your analysis."""

def generate_article():
    """Generate a new article using Claude API."""
    client = anthropic.Anthropic()

    # Check for custom topic from environment (WhatsApp/OpenClaw trigger)
    custom_topic = os.environ.get("CUSTOM_TOPIC", "").strip()
    custom_category = os.environ.get("CUSTOM_CATEGORY", "").strip()

    if custom_topic:
        # Use custom topic from WhatsApp
        prompt = f"Write about: {custom_topic}"
        category = custom_category if custom_category in ["geopolitics", "technology", "finance"] else "geopolitics"
        print(f"Using custom topic: {custom_topic}")
    else:
        # Pick a random topic and prompt
        topic = random.choice(TOPICS)
        prompt = random.choice(topic["prompts"])
        category = topic["category"]

    # Generate the article content
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nWrite this as a deep-dive blog article for Ghaaspoos. Focus on recent, specific events with named players, real numbers, and verifiable details. The reader should walk away feeling like they understand something the mainstream media hasn't explained. Remember: 1000-1500 words minimum, with a 'What to Watch' section at the end."
            }
        ],
        system=SYSTEM_PROMPT
    )

    content = response.content[0].text

    # Generate a title
    title_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"Generate a short, punchy blog post title (5-10 words) for this article. Return ONLY the title, no quotes or explanation:\n\n{content[:500]}..."
            }
        ]
    )

    title = title_response.content[0].text.strip().strip('"\'')

    return title, content, category

def create_post_file(title: str, content: str, category: str):
    """Create a markdown file for the blog post."""
    # Create slug from title
    slug = title.lower()
    slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
    slug = '-'.join(slug.split())
    slug = slug[:50]  # Limit length

    # Get current timestamp in UTC, then format as UTC
    # Using a past time ensures Hugo always builds the post
    from datetime import timezone
    now = datetime.now(timezone.utc)
    # Subtract 1 hour to ensure it's always in the past
    past_time = now.replace(hour=max(0, now.hour - 1))
    date_str = past_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Create frontmatter - sanitize title for TOML
    # Remove double quotes and normalize apostrophes to prevent TOML parsing errors
    escaped_title = title.replace('"', '').replace("'", "'")
    frontmatter = f"""+++
date = '{date_str}'
draft = false
title = "{escaped_title}"
tags = ['{category}']
+++

"""

    # Full content
    full_content = frontmatter + content

    # Write file
    posts_dir = Path(__file__).parent.parent / "content" / "posts"
    filename = f"{slug}.md"
    filepath = posts_dir / filename

    # Ensure unique filename
    counter = 1
    while filepath.exists():
        filename = f"{slug}-{counter}.md"
        filepath = posts_dir / filename
        counter += 1

    filepath.write_text(full_content)
    print(f"Created: {filepath}")
    return filepath

def generate_audio(text: str, slug: str) -> str | None:
    """Generate audio file from text using Google Cloud TTS."""
    if not TTS_AVAILABLE:
        print("TTS not available, skipping audio generation")
        return None

    # Check for credentials
    creds_json = os.environ.get("GOOGLE_TTS_CREDENTIALS")
    if not creds_json:
        print("GOOGLE_TTS_CREDENTIALS not set, skipping audio generation")
        return None

    try:
        # Write credentials to temp file
        creds_path = Path("/tmp/gcp_credentials.json")
        creds_path.write_text(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)

        # Initialize client
        client = texttospeech.TextToSpeechClient()

        # Clean text for speech (remove markdown formatting)
        clean_text = text
        clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)  # Remove bold
        clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)      # Remove italics
        clean_text = re.sub(r'#{1,6}\s*', '', clean_text)          # Remove headers
        clean_text = re.sub(r'---+', '', clean_text)               # Remove hr
        clean_text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean_text)  # Remove links
        clean_text = clean_text.strip()

        # Limit text length (Google TTS has limits)
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000] + "..."

        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)

        # Voice configuration - using a natural-sounding voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-D",  # Male, natural voice
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        # Audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        # Generate speech
        print("Generating audio with Google Cloud TTS...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save audio file
        audio_dir = Path(__file__).parent.parent / "static" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_filename = f"{slug}.mp3"
        audio_path = audio_dir / audio_filename

        audio_path.write_bytes(response.audio_content)
        print(f"Audio saved to: {audio_path}")

        # Clean up credentials
        creds_path.unlink(missing_ok=True)

        return f"/audio/{audio_filename}"

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


def create_post_file(title: str, content: str, category: str, audio_path: str | None = None):
    """Create a markdown file for the blog post."""
    # Create slug from title
    slug = title.lower()
    slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
    slug = '-'.join(slug.split())
    slug = slug[:50]  # Limit length

    # Get current timestamp in UTC, then format as UTC
    # Using a past time ensures Hugo always builds the post
    from datetime import timezone
    now = datetime.now(timezone.utc)
    # Subtract 1 hour to ensure it's always in the past
    past_time = now.replace(hour=max(0, now.hour - 1))
    date_str = past_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Create frontmatter - sanitize title for TOML
    # Remove double quotes and normalize apostrophes to prevent TOML parsing errors
    escaped_title = title.replace('"', '').replace("'", "'")

    # Add audio path to frontmatter if available
    audio_line = f'\naudioFile = "{audio_path}"' if audio_path else ""

    frontmatter = f"""+++
date = '{date_str}'
draft = false
title = "{escaped_title}"
tags = ['{category}']{audio_line}
+++

"""

    # Full content
    full_content = frontmatter + content

    # Write file
    posts_dir = Path(__file__).parent.parent / "content" / "posts"
    filename = f"{slug}.md"
    filepath = posts_dir / filename

    # Ensure unique filename
    counter = 1
    while filepath.exists():
        filename = f"{slug}-{counter}.md"
        filepath = posts_dir / filename
        counter += 1

    filepath.write_text(full_content)
    print(f"Created: {filepath}")
    return filepath, slug


def main():
    print("Generating article with Claude...")
    title, content, category = generate_article()
    print(f"Title: {title}")
    print(f"Category: {category}")

    # Create slug for audio file
    slug = title.lower()
    slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
    slug = '-'.join(slug.split())
    slug = slug[:50]

    # Generate audio
    audio_path = generate_audio(content, slug)
    if audio_path:
        print(f"Audio generated: {audio_path}")

    # Create post with audio path
    filepath, _ = create_post_file(title, content, category, audio_path)
    print(f"Article saved to: {filepath}")

    # Build Hugo site
    os.system("hugo")
    print("Hugo build complete!")

if __name__ == "__main__":
    main()
