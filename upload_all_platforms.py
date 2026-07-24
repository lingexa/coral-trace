"""
Lingexa - Unified Social Media Upload Script
Uploads vocabulary reels to all connected social media platforms
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None

try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError as e:
    print(f"[!] Facebook upload module not available: {e}")

try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError as e:
    print(f"[!] Instagram upload module not available: {e}")

try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError as e:
    print(f"[!] YouTube upload module not available: {e}")


def get_latest_reel():
    video_dir = Path("output/video")

    if not video_dir.exists():
        print("No output/video directory found")
        return None

    reels = list(video_dir.glob("*/final_reel.mp4"))

    if not reels:
        print("No reels found in output/video directory")
        return None

    latest = max(reels, key=lambda p: p.stat().st_mtime)

    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    words_data = metadata.get("words", [])
    all_words = [w.get("word", "") for w in words_data]

    return {
        "video_path": str(latest),
        "metadata": metadata,
        "words": words_data,
        "all_words": all_words,
        "word": all_words[0] if all_words else "Vocabulary",
    }


def generate_caption(reel_data, platform="facebook"):
    words = reel_data.get("words", [])
    all_words = reel_data.get("all_words", [])
    
    if not words:
        return f"Learn English vocabulary with Lingexa! #lingexa #vocabulary #learnenglish"
    
    if platform == "facebook":
        lines = [
            f"📚 Learn 5 New English Words with Lingexa!",
            f"",
            f"Today's Vocabulary Lesson:",
            f"",
        ]
        
        for i, w in enumerate(words, 1):
            word = w.get("word", "")
            pos = w.get("part_of_speech", "")
            definition = w.get("definition", "")
            example = w.get("example", "")
            
            lines.append(f"{i}. {word.upper()} ({pos})")
            lines.append(f"   → {definition}")
            lines.append(f"   Example: {example}")
            lines.append(f"")
        
        lines.extend([
            f"💡 Save this post and practice these words today!",
            f"👍 Like if you learned something new!",
            f"🔔 Follow Lingexa for daily vocabulary lessons!",
            f"",
            f"#lingexa #vocabulary #learnenglish #wordoftheday #englishlearning #vocabularybuilder #englishwords #studyenglish #dailyvocabulary #englishgrammar #esl #englishpractice #languagelearning",
        ])
        
    elif platform == "instagram":
        lines = [
            f"📚 5 New Words to Learn Today!",
            f"",
        ]
        
        for i, w in enumerate(words, 1):
            word = w.get("word", "")
            pos = w.get("part_of_speech", "")
            definition = w.get("definition", "")
            
            lines.append(f"{i}. {word.upper()} ({pos})")
            lines.append(f"   {definition}")
            lines.append(f"")
        
        lines.extend([
            f"💡 Save & practice!",
            f"🔔 Follow @lingexa for daily lessons!",
            f"",
            f"#lingexa #vocabulary #learnenglish #wordoftheday #englishlearning #vocabularybuilder #englishwords #esl #englishpractice #languagelearning",
        ])
        
    else:
        lines = [
            f"Learn 5 English words with Lingexa!",
            f"",
        ]
        for i, w in enumerate(words[:3], 1):
            word = w.get("word", "")
            definition = w.get("definition", "")
            lines.append(f"{i}. {word.upper()} - {definition}")
        
        lines.extend([
            f"",
            f"#lingexa #vocabulary #learnenglish #wordoftheday",
        ])
    
    return "\n".join(lines)


def upload_to_all_platforms(video_path, caption, word, reel_data=None):
    results = {
        "timestamp": datetime.now().isoformat(),
        "word": word,
        "video": video_path,
        "uploads": {},
        "platforms_attempted": [],
        "platforms_successful": [],
        "platforms_skipped": [],
        "platforms_failed": []
    }

    print("\n" + "="*80)
    print(f"LINGEXA - MULTI-PLATFORM UPLOAD")
    print("="*80)
    print(f"Video: {video_path}")
    print(f"Word: {word}")
    print(f"Caption length: {len(caption)} characters")
    print("="*80)

    if not Path(video_path).exists():
        print(f"Video file not found: {video_path}")
                # === UPLOAD STATUS REPORT ===
    print("\n" + "=" * 60)
    print("UPLOAD STATUS REPORT")
    print("=" * 60)
    uploads = results.get("uploads", {})
    for pname, pkey in [("INSTAGRAM", "instagram"), ("FACEBOOK", "facebook"), ("YOUTUBE", "youtube"),
                          ("THREADS", "threads"), ("TIKTOK", "tiktok"), ("TWITTER", "twitter"),
                          ("VK", "vk"), ("TELEGRAM", "telegram")]:
        pinfo = uploads.get(pkey, {})
        if pinfo and pinfo.get("status") == "success":
            pid = pinfo.get("id", "N/A")
            print(f"{pname}: SUCCESS (ID: {pid})")
        elif pinfo:
            err = str(pinfo.get("error", pinfo.get("reason", "unknown")))[:80]
            print(f"{pname}: FAILED - {err}")
        else:
            pl = pkey.lower()
            failed = pl in [p.lower() for p in results.get("platforms_failed", [])]
            skipped = pl in [p.lower() for p in results.get("platforms_skipped", [])]
            print(f"{pname}: {'FAILED' if failed else ('SKIPPED' if skipped else '-')}")
    print("=" * 60)

    return results

    platforms = [
        ("facebook", upload_to_facebook, "Facebook"),
        ("instagram", upload_to_instagram, "Instagram"),
        ("youtube", upload_to_youtube, "YouTube"),
    ]

    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)

        if upload_func:
            try:
                upload_result = None

                if platform_name == "facebook":
                    upload_result = upload_func(
                        video_path=video_path,
                        description=caption,
                        title=f"Vocabulary: {word}"
                    )
                elif platform_name == "instagram":
                    upload_result = upload_func(
                        video_path=video_path,
                        caption=caption,
                        is_story=False
                    )
                elif platform_name == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    words_data = reel_data.get("words", [])
                    yt_title, yt_description, yt_tags = generate_video_metadata(words_data, reel_data)

                    upload_result = upload_func(
                        video_path=video_path,
                        title=yt_title,
                        description=yt_description,
                        tags=yt_tags,
                        category_id='27'
                    )

                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                    print(f"  {display_name} upload successful")
                else:
                    results["uploads"][platform_name] = {"status": "failed", "error": "Upload function returned None"}
                    results["platforms_failed"].append(platform_name)
                    print(f"  {display_name} upload failed: No result returned")

            except Exception as e:
                error_msg = str(e)
                results["uploads"][platform_name] = {"status": "failed", "error": error_msg}
                results["platforms_failed"].append(platform_name)
                print(f"  {display_name} upload failed: {error_msg}")
        else:
            print(f"  {display_name} upload skipped (module not available)")
            results["uploads"][platform_name] = {"status": "skipped", "reason": "Module not available"}
            results["platforms_skipped"].append(platform_name)

    print("\n" + "="*80)
    print("UPLOAD SUMMARY")
    print("="*80)

    total_attempted = len(results["platforms_attempted"])
    successful_count = len(results["platforms_successful"])
    failed_count = len(results["platforms_failed"])
    skipped_count = len(results["platforms_skipped"])

    print(f"\nOverall Status:")
    print(f"   Total Platforms: {total_attempted}")
    print(f"   Successful: {successful_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Skipped: {skipped_count}")

    if total_attempted > 0:
        success_rate = (successful_count / total_attempted) * 100
        print(f"\nSuccess Rate: {success_rate:.0f}%")

    if results["platforms_successful"]:
        print(f"\nSUCCESSFUL UPLOADS ({len(results['platforms_successful'])}):")
        for platform in results["platforms_successful"]:
            platform_data = results["uploads"].get(platform, {})
            video_id = platform_data.get("video_id", "N/A")
            print(f"   {platform.upper()}: Success (Video ID: {video_id})")

    if results["platforms_failed"]:
        print(f"\nFAILED UPLOADS ({len(results['platforms_failed'])}):")
        for platform in results["platforms_failed"]:
            platform_data = results["uploads"].get(platform, {})
            error = platform_data.get("error", "Unknown error")
            print(f"   {platform.upper()}: Failed - {error[:80]}...")

    if results["platforms_skipped"]:
        print(f"\nSKIPPED PLATFORMS ({len(results['platforms_skipped'])}):")
        skipped_list = ", ".join([p.upper() for p in results["platforms_skipped"]])
        print(f"   {skipped_list}")
        print(f"   Add credentials to enable these platforms")

    print("\n" + "="*80)

    results_file = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved: {results_file}")
    print("="*80)

        # === UPLOAD STATUS REPORT ===
    print("\n" + "=" * 60)
    print("UPLOAD STATUS REPORT")
    print("=" * 60)
    success_list = [p.lower() for p in results.get("platforms_successful", [])]
    failed_list = [p.lower() for p in results.get("platforms_failed", [])]
    skipped_list = [p.lower() for p in results.get("platforms_skipped", [])]
    for pname in ["INSTAGRAM", "FACEBOOK", "YOUTUBE", "THREADS", "TIKTOK", "TWITTER", "VK", "TELEGRAM"]:
        pl = pname.lower()
        if pl in success_list: status = "SUCCESS"
        elif pl in failed_list: status = "FAILED"
        elif pl in skipped_list: status = "SKIPPED"
        else: status = "-"
        print(f"{pname}: {status}")
    print("=" * 60)
    return results


def main():
    print("\n" + "="*80)
    print("LINGEXA - AUTOMATED UPLOAD")
    print("="*80)

    reel = get_latest_reel()

    if not reel:
        print("\nNo reel found! Run lingexa_bot.py first.")
        sys.exit(1)

    print(f"\nFound latest reel:")
    print(f"   Word: {reel['word']}")
    print(f"   Words count: {len(reel.get('words', []))}")
    print(f"   Video: {reel['video_path']}")

    caption = generate_caption(reel, platform="facebook")
    print(f"\nGenerated caption ({len(caption)} chars):")
    print("-"*80)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("-"*80)

    results = upload_to_all_platforms(
        reel['video_path'],
        caption,
        reel['word'],
        reel
    )

    successful = len(results.get("platforms_successful", []))
    failed = len(results.get("platforms_failed", []))
    skipped = len(results.get("platforms_skipped", []))

    if successful > 0:
        print(f"\nUpload complete! {successful} platform(s) successful.")
        if skipped > 0:
            print(f"{skipped} platform(s) skipped - add credentials to enable them")
        sys.exit(0)
    elif failed > 0:
        print(f"\nAll attempted uploads failed ({failed} failed, {skipped} skipped).")
        sys.exit(1)
    else:
        print(f"\nAll uploads skipped ({skipped} skipped).")
        sys.exit(1)


if __name__ == "__main__":
    main()