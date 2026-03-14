#!/usr/bin/env python3
"""
Automated blog article generator using Claude API.
Generates articles on geopolitics, technology, and finance.
"""

import anthropic
import os
import random
from datetime import datetime
from pathlib import Path

# Topics to rotate through
TOPICS = [
    {
        "category": "geopolitics",
        "prompts": [
            "Write about a current geopolitical shift or alliance forming between nations",
            "Analyze a recent trade war, sanction, or economic conflict between countries",
            "Discuss how a country is positioning itself strategically on the global stage",
            "Explain the chess moves happening in a current international conflict or negotiation",
            "Analyze the geopolitical implications of a recent energy or resource deal",
        ]
    },
    {
        "category": "technology",
        "prompts": [
            "Write about a breakthrough in AI and its implications for society",
            "Analyze the tech cold war between major powers and its impact",
            "Discuss how a new technology is disrupting an established industry",
            "Explain the strategic importance of semiconductor supply chains",
            "Analyze the race for quantum computing or space technology dominance",
        ]
    },
    {
        "category": "finance",
        "prompts": [
            "Analyze a major market shift and what smart money is doing",
            "Write about central bank policies and their hidden implications",
            "Discuss how institutional investors are positioning for the future",
            "Explain a complex financial instrument or strategy in simple terms",
            "Analyze the intersection of geopolitics and financial markets",
        ]
    }
]

SYSTEM_PROMPT = """
Role: You are a contrarian, razor-sharp strategic analyst who writes high-impact blog posts. You do not just report the news; you decode the hidden mechanics behind it.

Strict Formatting and Stylistic Rules:

    1.Pacing (Direct & Punchy): Cut the fluff. Use short, punchy paragraphs (maximum 2-3 sentences each). Start with impactful, definitive statements. No passive voice.

    2.Depth (Analytical): Look entirely past the PR headlines. Tell me the real story playing out beneath the surface. What is the mainstream media missing?

    3.The Dichotomy ("Rich Dad vs. Poor Dad" Framing): Explicitly contrast the amateur, surface-level reaction with the deep, strategic reality. (e.g., "The novice sees [X], but the strategist knows this is actually about [Y].")

    4.The Board (Chess Metaphor): Map this situation to a chessboard. Who is playing white and forcing the action? Who is stuck playing black and reacting? What is the hidden endgame or the next three moves?

    5.The Motive ("What's in it for them?"): Follow the money and power. Aggressively analyze the hidden motivations and incentives of the key players. Answer the question: Why does this actually benefit them behind closed doors?

    Output: Give me a compelling title, followed by the blog post. Ensure the tone is authoritative, cynical yet objective, and highly engaging.

Your articles should:
- Be 500-700 words
- Have a compelling hook in the first paragraph
- Include section breaks (---) between major points
- End with a thought-provoking conclusion
- Use **bold** for emphasis on key points
- Use *italics* for quotes or contrasting perspectives

Do NOT include a title - that will be added separately.
Do NOT use generic phrases like "In conclusion" or "To summarize".
Write as if you're explaining complex moves on a chess board to someone who wants to understand power dynamics."""

def generate_article():
    """Generate a new article using Claude API."""
    client = anthropic.Anthropic()

    # Pick a random topic and prompt
    topic = random.choice(TOPICS)
    prompt = random.choice(topic["prompts"])
    category = topic["category"]

    # Generate the article content
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nWrite this as a blog article. Focus on recent events or developments that readers would find relevant and insightful."
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

    # Create frontmatter - escape single quotes in title
    escaped_title = title.replace("'", "''")
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

def main():
    print("Generating article with Claude...")
    title, content, category = generate_article()
    print(f"Title: {title}")
    print(f"Category: {category}")

    filepath = create_post_file(title, content, category)
    print(f"Article saved to: {filepath}")

    # Build Hugo site
    os.system("hugo")
    print("Hugo build complete!")

if __name__ == "__main__":
    main()
