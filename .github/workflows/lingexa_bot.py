"""
Lingexa - English Vocabulary Builder
Properly centered text in containers with accurate padding.
"""

import os, sys, json, random, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError("AI_MODEL not set!")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
TTS_VOICE = "en-US-GuyNeural"
CHANNEL_NAME = "Lingexa"
WORDS_PER_VIDEO = 5
WORD_HISTORY_FILE = HISTORY_DIR / "all_generated_words.json"

WORD_LEVELS = ["Beginner", "Intermediate", "Advanced", "GRE", "SAT", "TOEFL"]

FALLBACK_WORDS = [
    {"word": "Eloquent", "part_of_speech": "adjective", "definition": "Fluent and persuasive in speaking", "example": "She gave an eloquent speech.", "synonyms": ["articulate", "expressive"], "fun_fact": "From Latin meaning 'to speak out'", "level": "Advanced"},
    {"word": "Resilient", "part_of_speech": "adjective", "definition": "Able to recover quickly", "example": "The resilient community rebuilt.", "synonyms": ["tough", "strong"], "fun_fact": "From Latin 'to jump back'", "level": "Intermediate"},
    {"word": "Serendipity", "part_of_speech": "noun", "definition": "Finding good things by chance", "example": "Finding the book was serendipity.", "synonyms": ["luck", "fortune"], "fun_fact": "From a Persian fairy tale", "level": "Advanced"},
    {"word": "Ubiquitous", "part_of_speech": "adjective", "definition": "Present or found everywhere", "example": "Smartphones are ubiquitous now.", "synonyms": ["everywhere", "common"], "fun_fact": "Latin for 'everywhere'", "level": "GRE"},
    {"word": "Ephemeral", "part_of_speech": "adjective", "definition": "Lasting a very short time", "example": "Cherry blossoms are ephemeral.", "synonyms": ["fleeting", "brief"], "fun_fact": "Greek for 'one day only'", "level": "Literary"},
]


def load_word_history():
    if WORD_HISTORY_FILE.exists():
        with open(WORD_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"words": [], "last_updated": None}


def save_word_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(WORD_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_word_used(word):
    history = load_word_history()
    return word.lower().strip() in [w.lower().strip() for w in history.get("words", [])]


def add_words_to_history(words):
    history = load_word_history()
    for w in words:
        history["words"].append(w.lower().strip())
    save_word_history(history)


def generate_word_data(num_words: int = WORDS_PER_VIDEO) -> list:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
            prompt = f"""Generate {num_words * 2} unique English vocabulary words.
Return as JSON: [{{"word": "word", "part_of_speech": "noun/verb/adjective/adverb", "definition": "simple max 10 words", "example": "example sentence", "synonyms": ["syn1", "syn2"], "fun_fact": "short fact"}}]
Return ONLY valid JSON array"""
            payload = {"model": AI_MODEL, "messages": [{"role": "system", "content": "Return ONLY valid JSON array."}, {"role": "user", "content": prompt}], "temperature": 0.9}
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            words = json.loads(content)
            fresh_words = []
            for w in words:
                word = w.get("word", "").strip()
                if word and not is_word_used(word) and len(word.split()) == 1:
                    w["level"] = random.choice(WORD_LEVELS)
                    fresh_words.append(w)
                if len(fresh_words) >= num_words:
                    break
            if len(fresh_words) >= num_words:
                add_words_to_history([w["word"] for w in fresh_words[:num_words]])
                return fresh_words[:num_words]
        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")
    print("[content] Using fallback words...")
    return get_fallback_words(num_words)


def get_fallback_words(num_words: int) -> list:
    fresh = [w.copy() for w in FALLBACK_WORDS if not is_word_used(w["word"])]
    if not fresh:
        fresh = [w.copy() for w in FALLBACK_WORDS]
    result = []
    for w in fresh:
        if len(result) >= num_words:
            break
        result.append(w)
        add_words_to_history([w["word"]])
    return result


def create_background():
    from PIL import Image, ImageDraw
    import random
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    circles = [(VIDEO_WIDTH - 120, 280, 150), (100, 600, 100), (VIDEO_WIDTH - 180, 1000, 180), (150, 1400, 130), (VIDEO_WIDTH - 100, 1700, 120)]
    for cx, cy, r in circles:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(220, 210, 200), width=2)
    for _ in range(80):
        x = random.randint(50, VIDEO_WIDTH - 50)
        y = random.randint(50, VIDEO_HEIGHT - 50)
        size = random.randint(2, 4)
        draw.ellipse([(x, y), (x + size, y + size)], fill=(230, 220, 210))
    return img


async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except:
        return False


async def generate_audio_with_retries(text: str, voice: str, output_path: str, max_retries: int = 3):
    for attempt in range(1, max_retries + 1):
        success = await generate_single_audio(text, voice, output_path)
        if success and Path(output_path).exists() and Path(output_path).stat().st_size > 100:
            return True
        if attempt < max_retries:
            await asyncio.sleep(2 * attempt)
    return False


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def generate_all_audio(words: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []
    total_duration = 0.0
    for i, word_data in enumerate(words):
        word = word_data["word"]
        pos = word_data["part_of_speech"]
        definition = word_data["definition"]
        example = word_data["example"]
        synonyms = word_data.get("synonyms", [])
        fun_fact = word_data.get("fun_fact", "")
        syn_text = ", ".join(synonyms[:3]) if synonyms else ""
        text = f"{word}. {pos}. {definition}. Example: {example}."
        if syn_text:
            text += f" Synonyms: {syn_text}."
        if fun_fact:
            text += f" {fun_fact}"
        audio_file = output_dir / f"word_{i}.mp3"
        success = asyncio.run(generate_audio_with_retries(text, TTS_VOICE, str(audio_file)))
        if not success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "5", str(audio_file)]
            subprocess.run(cmd, capture_output=True)
        duration = get_audio_duration(str(audio_file))
        audio_files.append({"file": str(audio_file), "duration": duration})
        total_duration += duration + 0.3
    print(f"[audio] Generated {len(audio_files)} narrations, total: {total_duration:.1f}s")
    return audio_files, total_duration


def create_final_audio(audio_files: list, output_file: str):
    output_dir = Path(output_file).parent
    concat_parts = []
    for i, af in enumerate(audio_files):
        padded = output_dir / f"padded_{i}.mp3"
        cmd = ["ffmpeg", "-y", "-i", str(af["file"]), "-af", "apad=pad_dur=0.3", "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", str(padded)]
        subprocess.run(cmd, capture_output=True)
        concat_parts.append(padded)
    concat_file = output_dir / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for part in concat_parts:
            f.write(f"file '{str(part.resolve()).replace(chr(92), chr(47))}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "libmp3lame", str(output_file)]
    subprocess.run(cmd, capture_output=True)
    for part in concat_parts:
        if part.exists():
            part.unlink()
    if concat_file.exists():
        concat_file.unlink()
    if Path(output_file).exists() and Path(output_file).stat().st_size > 100:
        print(f"[audio] Final: {Path(output_file).name}")
        return True
    return False


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = ' '.join(current + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current.append(w)
        else:
            lines.append(' '.join(current))
            current = [w]
    if current:
        lines.append(' '.join(current))
    return lines


def get_multiline_text_bbox(draw, lines, font):
    """Get accurate bounding box for multiple lines of text"""
    if not lines:
        return (0, 0, 0, 0)
    
    # Get single character bbox for line height
    char_bbox = draw.textbbox((0, 0), "A", font=font)
    line_height = char_bbox[3] - char_bbox[1]
    
    # Find max width
    max_width = 0
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        if line_w > max_width:
            max_width = line_w
    
    total_height = len(lines) * line_height
    return (0, 0, max_width, total_height)


def draw_centered_text_in_box(img_draw, text, font, box_x, box_y, box_width, box_height, fill_color, padding=30):
    """Draw text perfectly centered in a box with equal padding on all sides"""
    lines = wrap_text(img_draw, text, font, box_width - (padding * 2))
    
    # Get accurate text dimensions
    char_bbox = img_draw.textbbox((0, 0), "A", font=font)
    line_height = char_bbox[3] - char_bbox[1]
    text_total_height = len(lines) * line_height
    
    # Calculate centered starting position
    # Equal padding top and bottom
    actual_padding_top = (box_height - text_total_height) // 2
    actual_padding_bottom = box_height - text_total_height - actual_padding_top
    
    # Draw each line
    for i, line in enumerate(lines):
        line_y = box_y + actual_padding_top + (i * line_height) + (line_height // 2)
        img_draw.text((box_x + box_width // 2, line_y), line, fill=fill_color, font=font, anchor="mm")
    
    return len(lines) * (line_height + 5)


def generate_word_image(word_data: dict, bg_image, output_path: str):
    from PIL import Image, ImageDraw, ImageFont

    img = bg_image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img)

    MARGIN_X = 70
    CENTER_X = VIDEO_WIDTH // 2
    CONTENT_WIDTH = VIDEO_WIDTH - (MARGIN_X * 2)

    fonts_bold = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/verdanab.ttf"]
    fonts_regular = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/verdana.ttf"]

    def load_font(paths, size):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
        return ImageFont.load_default()

    font_header = load_font(fonts_bold, 52)
    font_word = load_font(fonts_bold, 130)
    font_level = load_font(fonts_bold, 42)
    font_pos = load_font(fonts_bold, 52)
    font_def_label = load_font(fonts_bold, 38)
    font_def = load_font(fonts_regular, 58)
    font_ex_label = load_font(fonts_bold, 38)
    font_ex = load_font(fonts_regular, 48)
    font_syn_label = load_font(fonts_bold, 38)
    font_syn = load_font(fonts_regular, 42)
    font_ff_label = load_font(fonts_bold, 38)
    font_ff = load_font(fonts_regular, 40)
    font_footer = load_font(fonts_bold, 40)

    word = word_data["word"].upper()
    pos = word_data.get("part_of_speech", "")
    definition = word_data["definition"]
    example = word_data["example"]
    synonyms = word_data.get("synonyms", [])
    fun_fact = word_data.get("fun_fact", "")
    level = word_data.get("level", "")

    # === START WITH BIG GAP FROM TOP ===
    y_cursor = 200

    # Header bar
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 90)], fill=(45, 35, 65))
    draw.text((CENTER_X, 45), CHANNEL_NAME.upper(), fill=(255, 255, 255), font=font_header, anchor="mm")
    
    # === GAP AFTER HEADER ===
    y_cursor = 220

    # Word
    word_bbox = draw.textbbox((0, 0), word, font=font_word)
    word_h = word_bbox[3] - word_bbox[1]
    draw.text((CENTER_X, y_cursor), word, fill=(25, 20, 45), font=font_word, anchor="mm", stroke_width=4, stroke_fill=(200, 190, 180))
    y_cursor += word_h + 35

    # Level badge
    if level:
        level_text = level.upper()
        level_bbox = draw.textbbox((0, 0), level_text, font=font_level)
        level_w = level_bbox[2] - level_bbox[0]
        level_h = level_bbox[3] - level_bbox[1]
        draw.rounded_rectangle(
            [(CENTER_X - level_w // 2 - 10, y_cursor), (CENTER_X + level_w // 2 + 10, y_cursor + level_h + 16)],
            radius=10, fill=(90, 70, 130)
        )
        draw.text((CENTER_X, y_cursor + level_h // 2 + 8), level_text, fill=(255, 255, 255), font=font_level, anchor="mm")
        y_cursor += level_h + 40

    # Part of speech
    if pos:
        pos_text = pos.upper()
        pos_bbox = draw.textbbox((0, 0), pos_text, font=font_pos)
        pos_w = pos_bbox[2] - pos_bbox[0]
        pos_h = pos_bbox[3] - pos_bbox[1]
        draw.rounded_rectangle(
            [(CENTER_X - pos_w // 2 - 20, y_cursor), (CENTER_X + pos_w // 2 + 20, y_cursor + pos_h + 20)],
            radius=12, fill=(75, 55, 115)
        )
        draw.text((CENTER_X, y_cursor + pos_h // 2 + 10), pos_text, fill=(255, 245, 140), font=font_pos, anchor="mm")
        y_cursor += pos_h + 55

    # === DEFINITION - PERFECTLY CENTERED ===
    def_label = "MEANING"
    draw.text((MARGIN_X, y_cursor), def_label, fill=(80, 65, 105), font=font_def_label, anchor="lm")
    y_cursor += 50

    def_lines = wrap_text(draw, definition, font_def, CONTENT_WIDTH - 60)
    def_lines_count = len(def_lines)
    
    char_bbox = draw.textbbox((0, 0), "A", font=font_def)
    line_height = char_bbox[3] - char_bbox[1]
    text_height = def_lines_count * line_height
    
    # BIG equal padding
    padding = 35
    def_box_h = text_height + (padding * 2)

    def_box = Image.new('RGBA', (CONTENT_WIDTH, def_box_h), (65, 50, 95, 255))
    def_draw = ImageDraw.Draw(def_box)
    def_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, def_box_h)], radius=18, fill=(65, 50, 95, 255))

    # Draw each line centered
    for i, line in enumerate(def_lines):
        line_y = padding + (i * line_height) + (line_height // 2)
        def_draw.text((CONTENT_WIDTH // 2, line_y), line, fill=(255, 255, 255), font=font_def, anchor="mm")

    img.paste(def_box, (MARGIN_X, y_cursor), def_box)
    y_cursor += def_box_h + 50

    # === EXAMPLE - PERFECTLY CENTERED ===
    ex_label = "EXAMPLE"
    draw.text((MARGIN_X, y_cursor), ex_label, fill=(80, 65, 105), font=font_ex_label, anchor="lm")
    y_cursor += 50

    ex_lines = wrap_text(draw, example, font_ex, CONTENT_WIDTH - 60)
    ex_lines_count = len(ex_lines)
    
    ex_char_bbox = draw.textbbox((0, 0), "A", font=font_ex)
    ex_line_height = ex_char_bbox[3] - ex_char_bbox[1]
    ex_text_height = ex_lines_count * ex_line_height
    
    # BIG equal padding
    ex_padding = 30
    ex_box_h = ex_text_height + (ex_padding * 2)

    ex_box = Image.new('RGBA', (CONTENT_WIDTH, ex_box_h), (95, 80, 125, 220))
    ex_draw = ImageDraw.Draw(ex_box)
    ex_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, ex_box_h)], radius=15, fill=(95, 80, 125, 220))

    # Draw each line centered
    for i, line in enumerate(ex_lines):
        line_y = ex_padding + (i * ex_line_height) + (ex_line_height // 2)
        ex_draw.text((CONTENT_WIDTH // 2, line_y), line, fill=(255, 255, 255), font=font_ex, anchor="mm")

    img.paste(ex_box, (MARGIN_X, y_cursor), ex_box)
    y_cursor += ex_box_h + 50

    # Synonyms
    if synonyms:
        syn_label = "SYNONYMS"
        draw.text((MARGIN_X, y_cursor), syn_label, fill=(80, 65, 105), font=font_syn_label, anchor="lm")
        y_cursor += 50

        syn_text = ", ".join(synonyms[:4])
        syn_lines = wrap_text(draw, syn_text, font_syn, CONTENT_WIDTH - 60)

        for i, line in enumerate(syn_lines):
            syn_char_bbox = draw.textbbox((0, 0), "A", font=font_syn)
            syn_line_height = syn_char_bbox[3] - syn_char_bbox[1]
            line_y = y_cursor + (i * syn_line_height) + (syn_line_height // 2)
            draw.text((CENTER_X, line_y), line, fill=(55, 45, 85), font=font_syn, anchor="mm")

        y_cursor += len(syn_lines) * syn_line_height + 45

    # Fun fact
    if fun_fact:
        ff_label = "DID YOU KNOW?"
        draw.text((MARGIN_X, y_cursor), ff_label, fill=(110, 75, 55), font=font_ff_label, anchor="lm")
        y_cursor += 50

        ff_lines = wrap_text(draw, fun_fact, font_ff, CONTENT_WIDTH - 60)
        
        ff_char_bbox = draw.textbbox((0, 0), "A", font=font_ff)
        ff_line_height = ff_char_bbox[3] - ff_char_bbox[1]
        ff_text_height = len(ff_lines) * ff_line_height
        
        ff_padding = 22
        ff_box_h = ff_text_height + (ff_padding * 2)

        ff_box = Image.new('RGBA', (CONTENT_WIDTH, ff_box_h), (255, 210, 160, 200))
        ff_draw = ImageDraw.Draw(ff_box)
        ff_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, ff_box_h)], radius=14, fill=(255, 210, 160, 200))

        for i, line in enumerate(ff_lines):
            line_y = ff_padding + (i * ff_line_height) + (ff_line_height // 2)
            ff_draw.text((CONTENT_WIDTH // 2, line_y), line, fill=(70, 45, 25), font=font_ff, anchor="mm")

        img.paste(ff_box, (MARGIN_X, y_cursor), ff_box)

    # Footer
    draw.rectangle([(0, VIDEO_HEIGHT - 65), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65))
    draw.text((CENTER_X, VIDEO_HEIGHT - 32), f"Learn a new word every day  |  {CHANNEL_NAME}", fill=(210, 200, 220), font=font_footer, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=96, optimize=True)
    print(f"[image] Generated: {Path(output_path).name}")
    return output_path


def create_video(image_files: list, audio_files: list, output_file: str):
    print(f"[video] Creating video from {len(image_files)} images...")
    temp_clips = []
    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        temp_clip = Path(output_file).parent / f"clip_{i}.mp4"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img_path), "-i", str(audio_info["file"]),
               "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
               "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", str(temp_clip)]
        subprocess.run(cmd, capture_output=True)
        temp_clips.append(temp_clip)
        print(f"  Clip {i+1}: {audio_info['duration']:.1f}s")
    if not temp_clips:
        return False
    concat_file = Path(output_file).parent / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{str(clip.resolve()).replace(chr(92), chr(47))}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, capture_output=True)
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if concat_file.exists():
        concat_file.unlink()
    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Created: {Path(output_file).name} ({video_duration:.1f}s)")
    return True


def generate_reel():
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()} - ENGLISH VOCABULARY BUILDER\n{'='*80}\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"words_{timestamp}"
    reel_dir.mkdir(exist_ok=True)
    print("[1/5] Generating 5 vocabulary words...")
    words = generate_word_data(WORDS_PER_VIDEO)
    print(f"\n  Words:")
    for i, w in enumerate(words, 1):
        print(f"    {i}. {w['word']} ({w['part_of_speech']}) - {w['level']}")
    print("\n[2/5] Generating background...")
    bg = create_background()
    print("\n[3/5] Generating 5 word images...")
    image_files = []
    for i, word_data in enumerate(words):
        img_path = reel_dir / f"word_{i}.jpg"
        generate_word_image(word_data, bg, str(img_path))
        image_files.append(str(img_path))
    print("\n[4/5] Generating audio...")
    audio_files, total_duration = generate_all_audio(words, str(reel_dir))
    final_audio = reel_dir / "narration.mp3"
    create_final_audio(audio_files, str(final_audio))
    print("\n[5/5] Creating video...")
    output_video = reel_dir / "final_reel.mp4"
    create_video(image_files, audio_files, str(output_video))
    metadata = {"channel": CHANNEL_NAME, "words": words, "timestamp": timestamp, "video": str(output_video), "duration": total_duration, "all_words_list": [w["word"] for w in words]}
    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n{'='*80}\n  COMPLETE! Duration: {total_duration:.1f}s\n  Output: {reel_dir}\n{'='*80}\n")
    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print(f"  {CHANNEL_NAME.upper()}")
    print("="*80)
    print("\n  ONE word per screen | BIG fonts | Proper spacing | PERFECTLY centered text")
    print("="*80)
    generate_reel()