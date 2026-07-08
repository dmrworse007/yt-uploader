"""Auto-generate a title, description, and tags for each video.

Fully automatic and offline: it derives a clean, human-looking title from
the Drive filename and rotates through engaging templates so uploads don't
look copy-pasted. No extra API keys required.

If you later want smarter AI-written metadata, replace generate() with a
call to your LLM of choice -- the interface (returns title/description/tags)
stays the same.
"""
import os
import random
import re

# Neutral, broadly-safe hashtags for shorts. Edit to fit your niche.
BASE_TAGS = [
    "shorts", "viral", "trending", "fyp", "reels", "explore",
    "video", "youtube", "youtubeshorts", "short",
]

HOOK_PREFIXES = [
    "", "", "",  # weight toward no prefix
    "Watch: ", "Don't miss: ", "You need to see this - ",
    "Wait for it... ", "This is wild - ",
]

DESC_TEMPLATES = [
    "{title}\n\nThanks for watching! Subscribe for daily shorts.\n\n{hashtags}",
    "{title} \U0001F525\n\nHit like and subscribe if you enjoyed this one.\n\n{hashtags}",
    "{title}\n\nNew shorts every day - turn on notifications so you never miss one!\n\n{hashtags}",
    "{title}\n\nDrop a comment and let me know what you think.\n\n{hashtags}",
]


def _clean_title_from_filename(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    # Replace separators with spaces.
    name = re.sub(r"[._\-]+", " ", name)
    # Strip common junk tokens (resolution, codecs, counters).
    name = re.sub(
        r"\b(1080p|720p|4k|hd|final|copy|edit|v\d+|mp4|mov|export|render|\d{6,})\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = "Short Video"
    # Title-case but keep short all-caps words (like "AI", "DIY").
    words = []
    for w in name.split():
        words.append(w if (w.isupper() and len(w) <= 4) else w.capitalize())
    title = " ".join(words)
    return title


def generate(filename: str, seed: int | None = None) -> dict:
    rng = random.Random(seed if seed is not None else filename)
    core = _clean_title_from_filename(filename)

    prefix = rng.choice(HOOK_PREFIXES)
    title = f"{prefix}{core} #shorts"
    # YouTube hard limit is 100 chars.
    if len(title) > 100:
        title = title[:97].rstrip() + "..."

    tags = rng.sample(BASE_TAGS, k=min(8, len(BASE_TAGS)))
    hashtags = " ".join("#" + t for t in ["shorts", "viral", "trending"])
    description = rng.choice(DESC_TEMPLATES).format(title=core, hashtags=hashtags)
    # Description hard limit is 5000 chars.
    description = description[:4900]

    return {"title": title, "description": description, "tags": tags}


if __name__ == "__main__":
    # Quick manual check.
    for fn in ["funny_cat_1080p_final.mp4", "DIY.hack_042.mov", "20240817_track.mp4"]:
        print(fn, "->", generate(fn))
