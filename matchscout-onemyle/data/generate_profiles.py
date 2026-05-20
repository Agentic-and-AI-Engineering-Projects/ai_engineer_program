"""
generate_profiles.py — Generate Instagram-bio-style profile_description
for creators and businesses via Claude. One-time data prep.

Idempotent: skips rows that already have a non-empty profile_description.
Run with --dry-run first to preview output quality.

Usage:
  python data/generate_profiles.py --dry-run    # generate 3 samples per CSV, no save
  python data/generate_profiles.py              # generate all + save
"""

import os
import sys
from pathlib import Path

import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv
from tqdm import tqdm

# Load ANTHROPIC_API_KEY from the project .env
load_dotenv(Path(__file__).parent.parent / ".env")

# Anthropic SDK client — picks up the env var automatically
client = Anthropic()

# Tuning constants
MODEL = "claude-haiku-4-5-20251001"   # cheap + fast; quality is fine for short bios
MAX_TOKENS = 150                       # bios are 2-3 lines, plenty of headroom

DATA_DIR = Path(__file__).parent


# ============================================================
# SYSTEM PROMPTS — the style guide for each entity type
# ============================================================

CREATOR_SYSTEM = """You write authentic-sounding Instagram bios for content creators.

Style guide:
  - 2-3 short lines, casual tone
  - Occasional emojis are fine, but don't overdo it
  - Signal what they do + how to reach them
  - Sound like a real person, not corporate marketing

Examples of the style:
  - "Reel creator. Food & Beverages. DM For Collaboration. Food Review/PR"
  - "📍 Boston | Food photography ✨ | DMs open for collabs"
  - "Recipe developer + food stylist. Making food YOU should cook."
  - "Travel + lifestyle | Toronto-based | Couples / Food / Beauty ❤️"

Output ONLY the bio text. No preamble. No quotes around it. No labels."""


BUSINESS_SYSTEM = """You write authentic-sounding Instagram bios for small and medium businesses.

Style guide:
  - 2-3 short lines, descriptive
  - Occasional emojis are fine, but don't overdo it
  - Signal what they offer, their vibe, location if relevant
  - Sound like a real local business, not enterprise

Examples of the style:
  - "Cafe & deli. Authentic South Indian breakfast and meals. Ghee Podi Dosa, idli, filter coffee. 100% veg."
  - "🍩 Donut Shop | Open daily 5am-3pm | Donuts, cinnamon rolls, croissants, coffee"
  - "Craft brewery | 18 taps | Located on a San Ramon golf course. Bites, views, brews 🍻"
  - "Hair color | Balayage | Smoothening. Premium salon, 16+ years. Mississauga."

Output ONLY the bio text. No preamble. No quotes around it. No labels."""

# ============================================================
# PROMPT BUILDERS — format a CSV row into a user prompt
# ============================================================

def build_creator_prompt(row: dict) -> str:
    """Turn a creator's structured fields into a prompt for Claude."""
    return (
        f"Generate a profile description for this creator:\n"
        f"  Name: {row['name']}\n"
        f"  Primary category: {row['primary_category']}\n"
        f"  Subcategories: {row['primary_subcategories']}\n"
        f"  Content types: {row['content_types']}\n"
        f"  Location: {row['location']}\n"
        f"  Niche tags: {row['niche_tags']}\n"
        f"  Remote-friendly: {row['remote_friendly']}"
    )


def build_business_prompt(row: dict) -> str:
    """Turn a business's structured fields into a prompt for Claude."""
    return (
        f"Generate a profile description for this business:\n"
        f"  Name: {row['name']}\n"
        f"  Primary category: {row['primary_category']}\n"
        f"  Subcategories: {row['primary_subcategories']}\n"
        f"  Content needs: {row['content_needs']}\n"
        f"  Location: {row['location']}\n"
        f"  Niche tags: {row['niche_tags']}\n"
        f"  Business size: {row['business_size']}"
    )


# ============================================================
# LLM CALL — single API call to Claude, returns the bio text
# ============================================================

def generate_bio(system_prompt: str, user_prompt: str) -> str:
    """Call Claude once, return the cleaned bio text."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


# ============================================================
# CSV PROCESSOR — load CSV, fill bios, save back
# ============================================================

def process_csv(csv_path: Path, system_prompt: str, prompt_builder, dry_run: bool = False):
    """
    Load CSV, generate profile_description for any row missing it, save back.
    Idempotent: rows that already have a non-empty profile_description are skipped.
    """
    df = pd.read_csv(csv_path)

    # Make sure the column exists; if not, create it empty
    if "profile_description" not in df.columns:
        df["profile_description"] = ""
    df["profile_description"] = df["profile_description"].fillna("")

    # Which rows still need a bio?
    needs_bio = df["profile_description"].str.strip() == ""
    target_indices = list(df[needs_bio].index)

    if dry_run:
        target_indices = target_indices[:3]
        print(f"\n[DRY RUN] {csv_path.name}: generating {len(target_indices)} samples (no save)")
    else:
        print(f"\n{csv_path.name}: {len(target_indices)} bios to generate")

    if not target_indices:
        print("  Nothing to do — all rows already have a profile_description.")
        return

    for idx in tqdm(target_indices, desc=csv_path.stem):
        row = df.loc[idx].to_dict()
        bio = generate_bio(system_prompt, prompt_builder(row))
        df.at[idx, "profile_description"] = bio

    if dry_run:
        print(f"\n[DRY RUN sample output for {csv_path.name}]")
        for idx in target_indices:
            row = df.loc[idx]
            print(f"\n--- {row['id']} ({row['primary_category']}) ---")
            print(row["profile_description"])
    else:
        df.to_csv(csv_path, index=False)
        print(f"  Saved → {csv_path}")

# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    # Generate bios for creators
    process_csv(
        csv_path=DATA_DIR / "creators.csv",
        system_prompt=CREATOR_SYSTEM,
        prompt_builder=build_creator_prompt,
        dry_run=dry_run,
    )

    # Generate bios for businesses
    process_csv(
        csv_path=DATA_DIR / "businesses.csv",
        system_prompt=BUSINESS_SYSTEM,
        prompt_builder=build_business_prompt,
        dry_run=dry_run,
    )
