import json
from pathlib import Path
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "upload"))

# Load metadata
metadata_file = Path("output/video/words_20260509_201639/metadata.json")
with open(metadata_file, "r", encoding="utf-8") as f:
    metadata = json.load(f)

reel_data = {
    "words": metadata["words"],
    "all_words": metadata["all_words_list"],
}

print("="*80)
print("FACEBOOK/INSTAGRAM CAPTION")
print("="*80)
from upload_all_platforms import generate_caption
caption = generate_caption(reel_data, "facebook")
print(caption.encode('utf-8', errors='replace').decode('utf-8'))

print("\n" + "="*80)
print("YOUTUBE METADATA")
print("="*80)
from upload_to_youtube import generate_video_metadata
title, description, tags = generate_video_metadata(metadata["words"])
print(f"\nTITLE: {title}\n")
print(f"DESCRIPTION (first 2000 chars):\n{description[:2000].encode('utf-8', errors='replace').decode('utf-8')}")
print(f"\nTAGS: {tags}")