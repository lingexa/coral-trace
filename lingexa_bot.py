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
FONTS_DIR = Path(__file__).parent / "fonts"

WORD_LEVELS = ["Beginner", "Intermediate", "Advanced", "GRE", "GMAT", "SAT", "TOEFL", "IELTS"]

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
    existing = [w.lower().strip() for w in history.get("words", [])]
    for w in words:
        word_lower = w.lower().strip()
        if word_lower not in existing:
            history["words"].append(word_lower)
            existing.append(word_lower)
    save_word_history(history)


def generate_word_data(num_words: int = WORDS_PER_VIDEO) -> list:
    max_attempts = 30
    categories = [
        "business and professional",
        "academic and scientific",
        "literary and artistic",
        "emotional and psychological",
        "social and cultural",
        "philosophical and abstract",
        "descriptive and sensory",
        "technical and modern",
        "nature and environment",
        "character and personality",
        "medical and health",
        "legal and political",
        "culinary and food",
        "sports and fitness",
        "music and performing arts",
        "architecture and design",
        "ancient history and mythology",
        "astronomy and space",
        "fashion and textiles",
        "maritime and nautical",
        "IELTS preparation",
        "GMAT preparation",
        "psychology and behavior",
        "economics and finance",
        "geography and geology",
        "mathematics and logic",
        "religion and spirituality",
        "education and pedagogy",
        "linguistics and language",
        "anthropology and sociology",
        "photography and film",
        "theater and drama",
        "biotechnology and genetics",
        "robotics and artificial intelligence",
        "engineering and mechanics",
        "nutrition and wellness",
        "neuroscience and brain",
    ]
    collected = []
    collected_lower = set()
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
            category = categories[attempt % len(categories)]
            remaining = num_words - len(collected)
            print(f"[api] Attempt {attempt + 1}/{max_attempts}: Model={AI_MODEL}, Category={category} (need {remaining} more)")
            history = load_word_history()
            all_used = history.get("words", [])
            used_set = set()
            for w in all_used:
                used_set.add(w.lower().strip())
            used_set.update(collected_lower)
            if len(all_used) > 200:
                random_seed = random.sample(all_used, 100)
                recent_100 = all_used[-100:]
                context_words = list(set(random_seed + recent_100))
                random.shuffle(context_words)
            elif len(all_used) > 100:
                context_words = all_used[-100:]
            else:
                context_words = all_used
            context_words.extend(collected)
            print(f"[api] History: {len(all_used)} used + {len(collected)} collected this run, sending {len(context_words)} context words")
            used_list = ", ".join(context_words) if context_words else "(none yet)"
            prompt = f"""Generate exactly 20 unique English vocabulary words from the {category} domain.

STRICT RULES:
- NEVER repeat any of these words: {used_list}
- Each word must be a single word (no phrases, no hyphens, no spaces)
- Return ONLY a valid JSON array
- Every word must be different from all others in your response
- Choose OBSCURE and UNCOMMON words - avoid the most obvious ones

Format for each word:
{{"word": "word", "part_of_speech": "noun/verb/adjective/adverb", "definition": "simple definition under 12 words", "example": "example sentence under 10 words", "synonyms": ["syn1", "syn2"], "fun_fact": "short interesting fact"}}

Return ONLY the JSON array. Nothing else."""
            payload = {"model": AI_MODEL, "messages": [{"role": "system", "content": "You are an English vocabulary generator. Return ONLY valid JSON arrays."}, {"role": "user", "content": prompt}], "temperature": 1.5}
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            try:
                words = json.loads(content)
            except json.JSONDecodeError:
                print(f"[api] JSON parse failed, raw content preview: {content[:200]}")
                raise
            if not isinstance(words, list):
                print(f"[api] Response is not a list, got: {type(words).__name__}")
                raise ValueError("API did not return a JSON array")
            print(f"[api] AI returned {len(words)} words: {[w.get('word', '') for w in words]}")
            fresh_this_round = []
            skipped = []
            for w in words:
                word = w.get("word", "").strip()
                if not word:
                    skipped.append("(empty)")
                    continue
                if len(word.split()) > 1:
                    skipped.append(f"{word}(multi-word)")
                    continue
                word_lower = word.lower().strip()
                if word_lower in used_set:
                    skipped.append(f"{word}(already used)")
                    continue
                w["level"] = random.choice(WORD_LEVELS)
                fresh_this_round.append(w)
                used_set.add(word_lower)
                if len(collected) + len(fresh_this_round) >= num_words:
                    break
            if skipped:
                print(f"[api] Skipped: {', '.join(skipped)}")
            collected.extend(fresh_this_round)
            for w in fresh_this_round:
                collected_lower.add(w["word"].lower().strip())
            if len(collected) >= num_words:
                add_words_to_history([w["word"] for w in collected[:num_words]])
                print(f"[api] SUCCESS: Got {len(collected)} fresh words on attempt {attempt + 1}")
                return collected[:num_words]
            else:
                print(f"[api] Collected {len(collected)}/{num_words} so far, retrying with different category...")
        except json.JSONDecodeError:
            print(f"[api] Attempt {attempt + 1}/{max_attempts} SKIPPED (bad JSON), retrying...")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            print(f"[api] Attempt {attempt + 1}/{max_attempts} HTTP {status}, retrying...")
            if status in (401, 402, 403):
                print(f"[api] HTTP {status} indicates auth/payment issue, but continuing retries in case it's transient...")
        except Exception as e:
            print(f"[api] Attempt {attempt + 1}/{max_attempts} FAILED: {type(e).__name__}: {e}")
    if collected:
        print(f"[api] WARNING: Only got {len(collected)}/{num_words} words after {max_attempts} attempts, using partial set")
        add_words_to_history([w["word"] for w in collected])
        return collected
    raise RuntimeError("API failed all attempts - cannot generate words. Check POLLINATIONS_API_KEY and AI_MODEL in .env")


def create_background():
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Light cream gradient - NO circles, clean background
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    
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
    
    char_bbox = draw.textbbox((0, 0), "A", font=font)
    line_height = char_bbox[3] - char_bbox[1]
    line_spacing = int(line_height * 1.5)
    
    max_width = 0
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        if line_w > max_width:
            max_width = line_w
    
    total_height = (len(lines) - 1) * line_spacing + line_height
    return (0, 0, max_width, total_height)


def draw_centered_text_in_box(img_draw, text, font, box_x, box_y, box_width, box_height, fill_color, padding=30):
    """Draw text perfectly centered in a box with equal padding on all sides"""
    lines = wrap_text(img_draw, text, font, box_width - (padding * 2))
    
    char_bbox = img_draw.textbbox((0, 0), "A", font=font)
    line_height = char_bbox[3] - char_bbox[1]
    line_spacing = int(line_height * 1.5)
    text_total_height = (len(lines) - 1) * line_spacing + line_height
    
    actual_padding_top = (box_height - text_total_height) // 2
    actual_padding_bottom = box_height - text_total_height - actual_padding_top
    
    for i, line in enumerate(lines):
        line_y = box_y + actual_padding_top + (i * line_spacing) + (line_height // 2)
        img_draw.text((box_x + box_width // 2, line_y), line, fill=fill_color, font=font, anchor="mm")
    
    return len(lines) * (line_spacing + 5)


def generate_word_image(word_data: dict, bg_image, output_path: str):
    from PIL import Image, ImageDraw, ImageFont

    img = bg_image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img)

    MARGIN_X = 90
    CENTER_X = VIDEO_WIDTH // 2
    CONTENT_WIDTH = VIDEO_WIDTH - (MARGIN_X * 2)

    # Cross-platform font paths - system fonts only (no downloads needed)
    # Linux: Noto Sans (installed via apt-get install fonts-noto fonts-noto-core)
    # Windows: Arial/Verdana/Segoe UI
    fonts_bold = [
        # Linux paths (Ubuntu/Debian with fonts-noto-core)
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf",
        "/usr/share/fonts/noto/NotoSansDisplay-Bold.ttf",
        # Linux fallback to Liberation Sans Bold
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/Liberation/LiberationSans-Bold.ttf",
        # Last resort Linux fallback to regular
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        # Windows paths
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ]
    
    fonts_regular = [
        # Linux paths (Ubuntu/Debian with fonts-noto-core)
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-Regular.ttf",
        "/usr/share/fonts/noto/NotoSansDisplay-Regular.ttf",
        # Linux fallback to Liberation Sans
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/Liberation/LiberationSans-Regular.ttf",
        # Windows paths
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/verdana.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    def load_font(paths, size):
        for p in paths:
            try:
                font = ImageFont.truetype(p, size)
                # Test if font actually renders text
                test_bbox = draw.textbbox((0, 0), "AW", font=font)
                if test_bbox[2] - test_bbox[0] > size * 0.5:
                    print(f"[font] Loaded: {Path(p).name} ({size}pt)")
                    return font
            except:
                continue
        print(f"[font] WARNING: No font found at size {size}, using default")
        return ImageFont.load_default()

    # Verify fonts are loaded correctly
    print("[font] Loading fonts for Linux/Windows...")

    font_header = load_font(fonts_bold, 65)        # Increased from 52
    font_word = load_font(fonts_bold, 150)         # Increased from 130 - HUGE for visibility
    font_level = load_font(fonts_bold, 50)         # Increased from 42
    font_pos = load_font(fonts_bold, 60)           # Increased from 52
    font_def_label = load_font(fonts_bold, 42)     # Increased from 38
    font_def = load_font(fonts_regular, 65)        # Increased from 58 - BIG for readability
    font_ex_label = load_font(fonts_bold, 42)      # Increased from 38
    font_ex = load_font(fonts_regular, 54)         # Increased from 48
    font_syn_label = load_font(fonts_bold, 42)     # Increased from 38
    font_syn = load_font(fonts_regular, 48)        # Increased from 42
    font_ff_label = load_font(fonts_bold, 42)      # Increased from 38
    font_ff = load_font(fonts_regular, 46)         # Increased from 40
    font_footer = load_font(fonts_bold, 46)        # Increased from 40

    # Debug: Log font sizes being used
    print(f"[font] Font sizes - Header: 65, Word: 150, Level: 50, POS: 60, Def: 65, Example: 54")

    word = word_data["word"].upper()
    pos = word_data.get("part_of_speech", "")
    definition = word_data["definition"]
    example = word_data["example"]
    synonyms = word_data.get("synonyms", [])
    fun_fact = word_data.get("fun_fact", "")
    level = word_data.get("level", "")

    # === START WITH BIG GAP FROM TOP ===
    y_cursor = 220

    # Header bar
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 90)], fill=(45, 35, 65))
    draw.text((CENTER_X, 45), CHANNEL_NAME.upper(), fill=(255, 255, 255), font=font_header, anchor="mm")
    
    # === GAP AFTER HEADER ===
    y_cursor = 260

    # Word - dynamically size to prevent cropping
    MAX_WORD_WIDTH = VIDEO_WIDTH - MARGIN_X * 2
    word_font_size = 150
    word_font = font_word
    word_width = draw.textbbox((0, 0), word, font=word_font)[2]
    while word_width > MAX_WORD_WIDTH and word_font_size > 40:
        word_font_size -= 5
        word_font = load_font(fonts_bold, word_font_size)
        word_width = draw.textbbox((0, 0), word, font=word_font)[2]
    if word_font_size != 150:
        print(f"[word] Reduced '{word}' font to {word_font_size}pt (width: {word_width}/{MAX_WORD_WIDTH})")
    word_bbox = draw.textbbox((0, 0), word, font=word_font)
    word_h = word_bbox[3] - word_bbox[1]
    draw.text((CENTER_X, y_cursor), word, fill=(25, 20, 45), font=word_font, anchor="mm", stroke_width=max(1, word_font_size // 40), stroke_fill=(200, 190, 180))
    y_cursor += word_h + 50

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
        y_cursor += level_h + 55

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
        y_cursor += pos_h + 70

    # === DEFINITION - PERFECTLY CENTERED ===
    def_label = "MEANING"
    draw.text((MARGIN_X, y_cursor), def_label, fill=(80, 65, 105), font=font_def_label, anchor="lm")
    y_cursor += 60

    def_lines = wrap_text(draw, definition, font_def, CONTENT_WIDTH - 70)
    def_lines_count = len(def_lines)
    
    char_bbox = draw.textbbox((0, 0), "A", font=font_def)
    line_height = char_bbox[3] - char_bbox[1]
    line_spacing = int(line_height * 1.5)
    text_height = (def_lines_count - 1) * line_spacing + line_height
    
    # BIG equal padding
    padding = 45
    def_box_h = text_height + (padding * 2)

    def_box = Image.new('RGBA', (CONTENT_WIDTH, def_box_h), (65, 50, 95, 255))
    def_draw = ImageDraw.Draw(def_box)
    def_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, def_box_h)], radius=18, fill=(65, 50, 95, 255))

    # Draw each line centered with proper spacing
    for i, line in enumerate(def_lines):
        line_y = padding + (i * line_spacing) + (line_height // 2)
        def_draw.text((CONTENT_WIDTH // 2, line_y), line, fill=(255, 255, 255), font=font_def, anchor="mm")

    img.paste(def_box, (MARGIN_X, y_cursor), def_box)
    y_cursor += def_box_h + 65

    # === EXAMPLE - PERFECTLY CENTERED ===
    ex_label = "EXAMPLE"
    draw.text((MARGIN_X, y_cursor), ex_label, fill=(80, 65, 105), font=font_ex_label, anchor="lm")
    y_cursor += 60

    ex_lines = wrap_text(draw, example, font_ex, CONTENT_WIDTH - 70)
    ex_lines_count = len(ex_lines)
    
    ex_char_bbox = draw.textbbox((0, 0), "A", font=font_ex)
    ex_line_height = ex_char_bbox[3] - ex_char_bbox[1]
    ex_line_spacing = int(ex_line_height * 1.5)
    ex_text_height = (ex_lines_count - 1) * ex_line_spacing + ex_line_height
    
    # BIG equal padding
    ex_padding = 40
    ex_box_h = ex_text_height + (ex_padding * 2)

    ex_box = Image.new('RGBA', (CONTENT_WIDTH, ex_box_h), (95, 80, 125, 220))
    ex_draw = ImageDraw.Draw(ex_box)
    ex_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, ex_box_h)], radius=15, fill=(95, 80, 125, 220))

    # Draw each line centered with proper spacing
    for i, line in enumerate(ex_lines):
        line_y = ex_padding + (i * ex_line_spacing) + (ex_line_height // 2)
        ex_draw.text((CONTENT_WIDTH // 2, line_y), line, fill=(255, 255, 255), font=font_ex, anchor="mm")

    img.paste(ex_box, (MARGIN_X, y_cursor), ex_box)
    y_cursor += ex_box_h + 65

    # Synonyms
    if synonyms:
        syn_label = "SYNONYMS"
        draw.text((MARGIN_X, y_cursor), syn_label, fill=(80, 65, 105), font=font_syn_label, anchor="lm")
        y_cursor += 60

        syn_text = ", ".join(synonyms[:4])
        syn_lines = wrap_text(draw, syn_text, font_syn, CONTENT_WIDTH - 70)

        for i, line in enumerate(syn_lines):
            syn_char_bbox = draw.textbbox((0, 0), "A", font=font_syn)
            syn_line_height = syn_char_bbox[3] - syn_char_bbox[1]
            line_y = y_cursor + (i * syn_line_height) + (syn_line_height // 2)
            draw.text((CENTER_X, line_y), line, fill=(55, 45, 85), font=font_syn, anchor="mm")

        y_cursor += len(syn_lines) * syn_line_height + 60

    # Fun fact
    if fun_fact:
        ff_label = "DID YOU KNOW?"
        draw.text((MARGIN_X, y_cursor), ff_label, fill=(110, 75, 55), font=font_ff_label, anchor="lm")
        y_cursor += 60

        ff_lines = wrap_text(draw, fun_fact, font_ff, CONTENT_WIDTH - 70)
        
        ff_char_bbox = draw.textbbox((0, 0), "A", font=font_ff)
        ff_line_height = ff_char_bbox[3] - ff_char_bbox[1]
        ff_line_spacing = int(ff_line_height * 1.5)
        ff_text_height = (len(ff_lines) - 1) * ff_line_spacing + ff_line_height
        
        ff_padding = 35
        ff_box_h = ff_text_height + (ff_padding * 2)

        ff_box = Image.new('RGBA', (CONTENT_WIDTH, ff_box_h), (255, 210, 160, 200))
        ff_draw = ImageDraw.Draw(ff_box)
        ff_draw.rounded_rectangle([(0, 0), (CONTENT_WIDTH, ff_box_h)], radius=14, fill=(255, 210, 160, 200))

        for i, line in enumerate(ff_lines):
            line_y = ff_padding + (i * ff_line_spacing) + (ff_line_height // 2)
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