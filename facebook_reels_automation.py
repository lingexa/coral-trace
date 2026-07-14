"""
Facebook Reels Automation - Bilingual English/Telugu Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Telugu branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file. "
        "For GitHub Actions: Add AI_MODEL to repository secrets."
    )

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for learners of Telugu)
# Essential Telugu learning categories + Motivational categories
CATEGORIES_ENGLISH = [
    "Greetings", "Basic Phrases", "Common Expressions", "Travel Telugu", "Restaurant Telugu",
    "Shopping Telugu", "Emergency Telugu", "Family Terms", "Numbers Telugu", "Time Telugu",
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Telugu translations for display
CATEGORIES_TELUGU = {
    "Greetings": "పలుకులు",
    "Basic Phrases": "ప్రాథమిక పదబంధాలు",
    "Common Expressions": "సాధారణ వ్యక్తులు",
    "Travel Telugu": "ప్రయాణ తెలుగు",
    "Restaurant Telugu": "రెస్టారెంట్ తెలుగు",
    "Shopping Telugu": "షాపింగ్ తెలుగు",
    "Emergency Telugu": "అత్యవసర తెలుగు",
    "Family Terms": "కుటుంబ పదాలు",
    "Numbers Telugu": "సంఖ్యలు",
    "Time Telugu": "సమయం",
    "Motivation": "ప్రేరణ",
    "Love": "ప్రేమ",
    "Success": "విజయం",
    "Wisdom": "జ్ఞానం",
    "Happiness": "సంతోషం",
    "Self Improvement": "స్వీయ మెరుగుదల",
    "Gratitude": "కృతజ్ఞత",
    "Friendship": "స్నేహం",
    "Hope": "ఆశ",
    "Creativity": "సృజనాత్మకత",
    "Inner Peace": "అంతర్ శాంతి",
    "Confidence": "విశ్వాసం",
    "Perseverance": "దృఢత్వం",
    "Inspiration": "స్ఫూర్తి",
    "Positive Life": "సానుకూల జీవితం",
    "Courage": "ధైర్యం",
    "Kindness": "దయ",
    "Patience": "ఓపిక",
    "Forgiveness": "క్షమాపణ",
    "Strength": "బలం",
    "Joy": "ఆనందం",
    "Balance": "సమతుల్యత",
    "Growth": "వృద్ధి",
    "Purpose": "ప్రయోజనం",
    "Mindfulness": "సంపూర్ణ అవగాహన",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
TELUGU_VOICE = "te-IN-MohanNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Recent categories file (for rotation - prevents category repeats)
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"
MAX_RECENT_CATEGORIES = 15


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "telugu": phrase["telugu"],
            "transliteration": phrase.get("transliteration", ""),
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CATEGORY ROTATION MANAGEMENT (Prevent Repeats) ==============

def load_recent_categories():
    """Load recently used categories"""
    if RECENT_CATEGORIES_FILE.exists():
        with open(RECENT_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"recent_categories": [], "last_updated": None}


def save_recent_categories(data):
    """Save recent categories"""
    data["last_updated"] = datetime.now().isoformat()
    with open(RECENT_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_category():
    """Get a category that hasn't been used recently - ensures rotation across ALL 35 categories"""
    recent_data = load_recent_categories()
    recent = recent_data.get("recent_categories", [])

    available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent]

    if not available:
        recent_data["recent_categories"] = recent[-5:]
        save_recent_categories(recent_data)
        available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent_data["recent_categories"]]
        print(f"[rotation] All categories used recently - cleared old ones, {len(available)} available")

    selected = random.choice(available)

    recent.append(selected)

    if len(recent) > MAX_RECENT_CATEGORIES:
        recent = recent[-MAX_RECENT_CATEGORIES:]

    recent_data["recent_categories"] = recent
    save_recent_categories(recent_data)

    print(f"[rotation] Selected '{selected}' ({len(available)} available, {len(recent)} in recent history)")
    return selected


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""

    category_telugu = CATEGORIES_TELUGU[category_english]

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Telugu.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Telugu text should be CLEAN - use standard Telugu script
7. Do NOT include multiple versions or slashes - just ONE clean Telugu translation
8. Transliteration should be in Roman script (e.g., "namaskaram")

For each phrase:
1. English phrase (with commas for natural pauses)
2. Telugu translation (in Telugu script)
3. Transliteration (Roman script pronunciation, e.g., "namaskaram")

Return as JSON array:
[{{"english": "...", "telugu": "...", "transliteration": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.
IMPORTANT: Telugu text must be clean - no slashes, no multiple versions."""

            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a Telugu teacher. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            phrases = json.loads(content)

            # Normalize: accept both 'romaji' and 'transliteration' keys
            for p in phrases:
                if "transliteration" not in p and "romaji" in p:
                    p["transliteration"] = p.pop("romaji")

            unique_phrases = []
            for phrase in phrases:
                if len(phrase["english"].split()) > 15:
                    continue
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break

            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""

    all_fallbacks = {
        "Greetings": [
            {"english": "Hello, nice to meet you.", "telugu": "నమస్కారం, మీతో పరిచయం సంతోషం.", "transliteration": "Namaskaram, meeto parichayam santosham."},
            {"english": "Good morning!", "telugu": "శుభోదయం!", "transliteration": "Shubhodayam!"},
            {"english": "Good evening, how are you?", "telugu": "శుభ సాయంత్రం, ఎలా ఉన్నారు?", "transliteration": "Shubha sayantram, elaa unnaru?"},
            {"english": "See you tomorrow!", "telugu": "రేపు కలవాల!", "transliteration": "Repu kalavaala!"},
            {"english": "Goodbye, take care.", "telugu": "వీడ్కోలు, జాగ్రత్తగా ఉండండి.", "transliteration": "Veedkolu, jaagrattaga undandi."},
        ],
        "Basic Phrases": [
            {"english": "Thank you very much.", "telugu": "చాలా ధన్యవాదాలు.", "transliteration": "Chala dhanyavaadaalu."},
            {"english": "You're welcome.", "telugu": "పర్వాలేదు.", "transliteration": "Parvaaledu."},
            {"english": "I'm sorry, excuse me.", "telugu": "క్షమించండి.", "transliteration": "Kshaminchandi."},
            {"english": "Yes, that's correct.", "telugu": "అవును, అది సరే.", "transliteration": "Avunu, adi sare."},
            {"english": "No, I don't think so.", "telugu": "లేదు, నా అభిప్రాయం లేదు.", "transliteration": "Ledu, na abhipraayam ledu."},
        ],
        "Common Expressions": [
            {"english": "How are you doing today?", "telugu": "ఈరోజు ఎలా ఉన్నారు?", "transliteration": "Eeroju elaa unnaru?"},
            {"english": "I'm fine, thank you.", "telugu": "నేను బాగున్నాను, ధన్యవాదాలు.", "transliteration": "Nenu baagunnanu, dhanyavaadaalu."},
            {"english": "What's your name?", "telugu": "మీ పేరు ఏమిటి?", "transliteration": "Mee peru emit?"},
            {"english": "My name is...", "telugu": "నా పేరు...", "transliteration": "Naa peru..."},
            {"english": "Nice to meet you too.", "telugu": "మీతో పరిచయం ఆనందం.", "transliteration": "Meeto parichayam aanandam."},
        ],
        "Travel Telugu": [
            {"english": "Where is the bathroom?", "telugu": "బాత్రూమ్ ఎక్కడ ఉంది?", "transliteration": "Bathroom ekkada undi?"},
            {"english": "How do I get there?", "telugu": "అక్కడికి ఎలా వెళ్ళాలి?", "transliteration": "Akkadiki elaa vellaali?"},
            {"english": "I need a taxi, please.", "telugu": "నాకు టాక్సీ కావాలి, దయచేసి.", "transliteration": "Naaku taxi kaavaali, dayachesi."},
            {"english": "Take me to the hotel.", "telugu": "హోటల్‌కి తీసుకెళ్ళండి.", "transliteration": "Hotel ki teesukellandi."},
            {"english": "How much does it cost?", "telugu": "ఎంత ఖర్చవుతుంది?", "transliteration": "Entha karchavuthund?"},
        ],
        "Restaurant Telugu": [
            {"english": "Can I see the menu?", "telugu": "మెనూ చూపించగలరా?", "transliteration": "Menu choopinchagalara?"},
            {"english": "This looks delicious!", "telugu": "ఇది రుచిగా కనిపిస్తోంది!", "transliteration": "Idi ruchigaa kanipistondi!"},
            {"english": "Water, please.", "telugu": "నీళ్లు, దయచేసి.", "transliteration": "Neellu, dayachesi."},
            {"english": "Check, please.", "telugu": "బిల్లు, దయచేసి.", "transliteration": "Billu, dayachesi."},
            {"english": "It was delicious!", "telugu": "చాలా రుచిగా ఉంది!", "transliteration": "Chala ruchigaa undi!"},
        ],
        "Shopping Telugu": [
            {"english": "How much is this?", "telugu": "ఇది ఎంత?", "transliteration": "Idi entha?"},
            {"english": "Can I try this on?", "telugu": "దీన్ని ట్రై చేయవచ్చా?", "transliteration": "Deenni try cheyyavachaa?"},
            {"english": "Do you have a smaller size?", "telugu": "చిన్న సైజు ఉందా?", "transliteration": "Chinna size undaa?"},
            {"english": "I'll take this one.", "telugu": "ఇది తీసుకుంటాను.", "transliteration": "Idi teesukuntaanu."},
            {"english": "Can I pay by card?", "telugu": "కార్డుతో చెల్లించవచ్చా?", "transliteration": "Cardutho chellinchavachaa?"},
        ],
        "Emergency Telugu": [
            {"english": "Help me, please!", "telugu": "సహాయం చేయండి!", "transliteration": "Sahayam cheyandi!"},
            {"english": "Call the police!", "telugu": "పోలీసుకి ఫోన్ చేయండి!", "transliteration": "Police ki phone cheyandi!"},
            {"english": "I need a doctor.", "telugu": "నాకు డాక్టర్ కావాలి.", "transliteration": "Naaku doctor kaavaali."},
            {"english": "Where is the hospital?", "telugu": "ఆసుపత్రి ఎక్కడ ఉంది?", "transliteration": "Aasupatri ekkada undi?"},
            {"english": "I'm lost, can you help?", "telugu": "నేను దారి తప్పాను, సహాయం చేయగలరా?", "transliteration": "Nenu daari tappanu, sahayam cheyagalaraa?"},
        ],
        "Family Terms": [
            {"english": "This is my mother.", "telugu": "ఇది నా అమ్మ.", "transliteration": "Idi naa amma."},
            {"english": "This is my father.", "telugu": "ఇది నా నాన్న.", "transliteration": "Idi naa nanna."},
            {"english": "I have an older brother.", "telugu": "నాకు అన్నయ్య ఉన్నారు.", "transliteration": "Naaku annayya unnaaru."},
            {"english": "I have a younger sister.", "telugu": "నాకు చెల్లి ఉంది.", "transliteration": "Naaku chelli undi."},
            {"english": "These are my parents.", "telugu": "వీరు నా తల్లిదండ్రులు.", "transliteration": "Veera naa tallidandhrulu."},
        ],
        "Numbers Telugu": [
            {"english": "One, two, three.", "telugu": "ఒకటి, రెండు, మూడు.", "transliteration": "Okati, rendu, moodu."},
            {"english": "Four, five, six.", "telugu": "నాలుగు, ఐదు, ఆరు.", "transliteration": "Naalugu, aidu, aaru."},
            {"english": "Seven, eight, nine, ten.", "telugu": "ఏడు, ఎనిమిది, తొమ్మిది, పది.", "transliteration": "Eedu, enimidi, thomidi, padi."},
            {"english": "What number is this?", "telugu": "ఇది ఏ సంఖ్య?", "transliteration": "Idi ee sankhya?"},
            {"english": "Give me two, please.", "telugu": "రెండు ఇవ్వండి, దయచేసి.", "transliteration": "Rendu ivvandi, dayachesi."},
        ],
        "Time Telugu": [
            {"english": "What time is it?", "telugu": "ఇప్పుడు ఎంత సేపు?", "transliteration": "Ippudu entha sepu?"},
            {"english": "It's three o'clock.", "telugu": "మూడు గంటలు అయింది.", "transliteration": "Moodu gantalu aindi."},
            {"english": "See you at noon.", "telugu": "మధ్యాహ్నం కలవాల.", "transliteration": "Madhyaahnham kalavaala."},
            {"english": "I'll be there in five minutes.", "telugu": "ఐదు నిమిషాల్లో వస్తాను.", "transliteration": "Aidu nimishaallo vastaana."},
            {"english": "What day is today?", "telugu": "ఈరోజు ఏమి రోజు?", "transliteration": "Eeroju emi roju?"},
        ],
        "Motivation": [
            {"english": "Believe in yourself.", "telugu": "మీపై నమ్మకం ఉంచుకోండి.", "transliteration": "Meepai nammakam unchukondi."},
            {"english": "You are capable of amazing things.", "telugu": "మీరు అద్భుతమైన పనులు చేయగలరు.", "transliteration": "Meeru-adbhuthamaina panulu cheyagalaru."},
            {"english": "Dream big, start small.", "telugu": "పెద్ద కల కనండి, చిన్నదానితో మొదలుపెట్టండి.", "transliteration": "Pedda kala kanandi, chinnadaani tho modalupettandi."},
            {"english": "Your future is created by your actions.", "telugu": "మీ భవిష్యత్తు మీ చర్యలతో నిర్మించబడుతుంది.", "transliteration": "Mee bhavishthattu mee charyalatho nirminchabaduthundi."},
            {"english": "Never give up on your dreams.", "telugu": "మీ కలలను ఎప్పుడూ వదులుకోకండి.", "transliteration": "Mee kalalanu eppuduu vadulukokandi."},
        ],
        "Love": [
            {"english": "Love yourself first.", "telugu": "ముందు మిమ్మల్ని ప్రేమించుకోండి.", "transliteration": "Mundu mimmlanni premichukondi."},
            {"english": "Love makes everything possible.", "telugu": "ప్రేమ అన్నీ సాధ్యం చేస్తుంది.", "transliteration": "Prema annii saadhyam chesthundi."},
            {"english": "You are loved more than you know.", "telugu": "మీరు ఊహించిన దానికన్నా ఎక్కువ ప్రేమించబడుతున్నారు.", "transliteration": "Meeru ohinchina daanikanna ekkuva preminchabaduthunnaaru."},
            {"english": "Love is the greatest power.", "telugu": "ప్రేమే అతిపెద్ద శక్తి.", "transliteration": "Preme athipedda shakthi."},
            {"english": "Spread love everywhere you go.", "telugu": "ఎక్కడికి వెళ్ళినా ప్రేమ పంచండి.", "transliteration": "Ekkadiki vellina prema panchandi."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "telugu": "విజయం కష్టం నుండి వస్తుంది.", "transliteration": "Vijayam kashtam nundi vasthundi."},
            {"english": "Keep going, you're getting there.", "telugu": "కొనసాగించండి, మీరు చేరుకుంటున్నారు.", "transliteration": "Konasaaginchandi, meeru cherukuthunnaaru."},
            {"english": "Every step counts toward success.", "telugu": "ప్రతి అడుగూ విజయానికి దోహదపడుతుంది.", "transliteration": "Prathi-adugoo vijayaaniki dohadapaduthundi."},
            {"english": "Your effort will pay off.", "telugu": "మీ కృషి ఫలిస్తుంది.", "transliteration": "Mee krushi phalisthundi."},
            {"english": "Success is a journey, not a destination.", "telugu": "విజయం ఒక ప్రయాణం, గమ్యం కాదు.", "transliteration": "Vijayam oka prayaanam, gamyam kaadu."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "telugu": "జ్ఞానమే శక్తి.", "transliteration": "Jnāaname shakthi."},
            {"english": "Learn from yesterday, live for today.", "telugu": "నిన్నటి నుండి నేర్చుకోండి, ఈరోజు బ్రతకండి.", "transliteration": "Ninnati nundi nearchukondi, eeroju brathakandi."},
            {"english": "The wise learn from others' mistakes.", "telugu": "వివేకులు ఇతరుల తప్పుల నుండి నేర్చుకుంటారు.", "transliteration": "Vivekulu itharula thappula nundi nearchukuntaaru."},
            {"english": "Experience is the best teacher.", "telugu": "అనుభవమే ఉత్తమ గురువు.", "transliteration": "Anubhavame-uthama guruvu."},
            {"english": "Wisdom comes with age.", "telugu": "వయస్సుతో జ్ఞానం వస్తుంది.", "transliteration": "Vayassutho jnaanam vasthundi."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "telugu": "సంతోషం ఒక ఎంపిక.", "transliteration": "Santhosham oka empika."},
            {"english": "Find joy in the little things.", "telugu": "చిన్న చిన్న విషయాల్లో ఆనందం కనుగొనండి.", "transliteration": "Chinna chinna vishayaallo aanandam kanugonandi."},
            {"english": "Your happiness matters most.", "telugu": "మీ సంతోషమే అత్యంత ముఖ్యం.", "transliteration": "Mee santhoshame-athyantam mukhyam."},
            {"english": "Smile, it makes others happy.", "telugu": "చిన్నగా నవ్వండి, ఇది ఇతరులను సంతోషపరుస్తుంది.", "transliteration": "Chinnagaa navvandi, idi itharulana santhosha-parusthundi."},
            {"english": "Happiness is contagious, spread it.", "telugu": "సంతోషం అంటువ్వుతుంది, పంచండి.", "transliteration": "Santhosham antuvuventhundi, panchandi."},
        ],
        "Self Improvement": [
            {"english": "Better today than yesterday.", "telugu": "నిన్నటి కన్నా ఈరోజు మెరుగ్గా ఉంది.", "transliteration": "Ninnat kanna eerou meruggaa undi."},
            {"english": "Small steps lead to big changes.", "telugu": "చిన్న అడుగులు పెద్ద మార్పులకు దారితీస్తాయి.", "transliteration": "Chinna adugulu pedda maarpulaku daaritheesthaayi."},
            {"english": "Invest in yourself daily.", "telugu": "ప్రతిరోజు మీలో పెట్టుబడి చేయండి.", "transliteration": "Prathi-roju meelo pettu-badi cheyandi."},
            {"english": "Growth requires discomfort.", "telugu": "వృద్ధికి అసౌకర్యం అవసరం.", "transliteration": "Vrudhdhiki asoukaryam avasaram."},
            {"english": "Be your own competition.", "telugu": "మీ స్వంత పోటీదారుడిగా ఉండండి.", "transliteration": "Mee swantha pootidaarudigaa undandi."},
        ],
        "Gratitude": [
            {"english": "I am grateful for today.", "telugu": "ఈరోజుకి నేను కృతజ్ఞుడిని.", "transliteration": "Eerojuki nenu kruthagnudini."},
            {"english": "Thank you for everything.", "telugu": "అంతా ధన్యవాదాలు.", "transliteration": "Anthaa dhanyavaadaalu."},
            {"english": "Gratitude turns what we have into enough.", "telugu": "కృతజ్ఞత మనకు ఉన్నదానిని సరిపోనట్లు చేస్తుంది.", "transliteration": "Kruthagnatha manaku unnadaanini sariponaTlu chesthundi."},
            {"english": "Count your blessings daily.", "telugu": "ప్రతిరోజు మీ వరాలను లెక్కించండి.", "transliteration": "Prathiroju mee varaalana lekkinchandi."},
            {"english": "A grateful heart is a happy heart.", "telugu": "కృతజ్ఞతాపూరిత హృదయం సంతోషపూరిత హృదయం.", "transliteration": "Kruthagnatha-pooritha hridayam santhosha-pooritha hridayam."},
        ],
        "Friendship": [
            {"english": "Friends make life better.", "telugu": "స్నేహితులు జీవితాన్ని మెరుగుపరుస్తారు.", "transliteration": "Snehithulu jeevithaanni merugu-parustaaru."},
            {"english": "A true friend is always there.", "telugu": "నిజమైన స్నేహితుడు ఎప్పుడూ ఉంటాడు.", "transliteration": "Nijamaina snehithudu eppudoo untaadu."},
            {"english": "Friendship is a precious gift.", "telugu": "స్నేహం విలువైన బహుమతి.", "transliteration": "Snehatham viluvaina bahumathi."},
            {"english": "Good friends are like stars.", "telugu": "మంచి స్నేహితులు నక్షత్రాల లాంటివి.", "transliteration": "Manchi snehithulu nakshathrala laantivi."},
            {"english": "Cherish your true friends.", "telugu": "మీ నిజమైన స్నేహితులను విలువచేయండి.", "transliteration": "Mee nijamaina snehithulana viluva-cheyandi."},
        ],
        "Hope": [
            {"english": "Hope never dies.", "telugu": "ఆశ ఎప్పుడూ చనిపోదు.", "transliteration": "Aasha eppudoo chanipoodu."},
            {"english": "Tomorrow is a new beginning.", "telugu": "రేపు ఒక కొత్త ప్రారంభం.", "transliteration": "Repu oka koththa praarambham."},
            {"english": "Keep hope alive in your heart.", "telugu": "మీ హృదయంలో ఆశను సజీవంగా ఉంచుకోండి.", "transliteration": "Mee hridayamlo aashana sajaeeavagaa unchukondi."},
            {"english": "Hope is the light in darkness.", "telugu": "ఆశ చీకటిలో వెలుగు.", "transliteration": "Aasha cheekatilo velugu."},
            {"english": "Where there's hope, there's life.", "telugu": "ఆశ ఉన్నచోట జీవితం ఉంది.", "transliteration": "Aasha unnachota jeevitham undi."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "telugu": "ఈరోజు ఏదైనా అందమైనది సృష్టించండి.", "transliteration": "Eeroju edaina-andamainadi srushtimchandi."},
            {"english": "Your creativity is unique.", "telugu": "మీ సృజనాత్మకత అద్వితీయం.", "transliteration": "Mee srujanaathmakatha-advitheeyam."},
            {"english": "Let your imagination run wild.", "telugu": "మీ ఊహలను స్వేచ్ఛగా వదులుకోండి.", "transliteration": "Mee oohalana swechchagaa vadulukondi."},
            {"english": "Art comes from the heart.", "telugu": "కళ హృదయం నుండి వస్తుంది.", "transliteration": "Kala hridayam nundi vasthundi."},
            {"english": "Every day is a canvas.", "telugu": "ప్రతిరోజు ఒక కాన్వాస్.", "transliteration": "Prathiroju oka canvas."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "telugu": "మీలో శాంతిని కనుగొనండి.", "transliteration": "Meelo shanthini kanugonandi."},
            {"english": "Calm mind, happy heart.", "telugu": "ప్రశాంత మనస్సు, సంతోషపూరిత హృదయం.", "transliteration": "Prashaantha manassu, santhosha-pooritha hridayam."},
            {"english": "Peace begins with a smile.", "telugu": "శాంతి ఒక చిన్నగుడుపుతో మొదలవుతుంది.", "transliteration": "Shanth oka chinnagudiputho modalavuthundi."},
            {"english": "Breathe deeply, let go.", "telugu": "లోతుగా ఊపిరి తీసుకోండి, వదులుకోండి.", "transliteration": "Lothugaa oopiri theesukondi, vadulukondi."},
            {"english": "Your inner peace is precious.", "telugu": "మీ అంతర్ శాంతి విలువైనది.", "transliteration": "Mee anthar shanthi viluvainadhi."},
        ],
        "Confidence": [
            {"english": "Believe you can, you're right.", "telugu": "మీరు చేయగలరని నమ్మండి, మీరు సరే.", "transliteration": "Meeru cheyagalarani nammnadi, meeru sare."},
            {"english": "You are stronger than you think.", "telugu": "మీరు అనుకున్న దానికన్నా బలంగా ఉన్నారు.", "transliteration": "Meeru anukunna daanikanna balangaa unnaru."},
            {"english": "Confidence comes from within.", "telugu": "విశ్వాసం లోపలి నుండి వస్తుంది.", "transliteration": "Vishwaasam lopali nundi vasthundi."},
            {"english": "Stand tall, be proud.", "telugu": "నిటారుగా నిలబడండి, గర్వంగా ఉండండి.", "transliteration": "Nitaarugaa nilabidandi, garvamgaa undandi."},
            {"english": "You have what it takes.", "telugu": "మీకు అవసరమైనది మీలో ఉంది.", "transliteration": "Meeku avasaramainadhi meelo undi."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep going.", "telugu": "ఎప్పుడూ వదులుకోకండి, కొనసాగండి.", "transliteration": "Eppudoo vadulukokandi, konasaagandi."},
            {"english": "Persistence beats talent.", "telugu": "పట్టుదల ప్రతిభని ఓడిస్తుంది.", "transliteration": "Pattudala prathibhani oadisthundi."},
            {"english": "Fall seven times, rise eight.", "telugu": "ఏడుసార్లు కూలితే ఎనిమిది సార్లు లెగెదులుకోండి.", "transliteration": "Edusaarlu koolithe enimidi saarlu legedulukondi."},
            {"english": "Hard work pays off eventually.", "telugu": "కష్టం చివరకు ఫలిస్తుంది.", "transliteration": "Kashtam chivaraku phalisthundi."},
            {"english": "Stay the course, don't quit.", "telugu": "మార్గంలో ఉండండి, వదులుకోకండి.", "transliteration": "Maargamlo undandi, vadulukokandi."},
        ],
        "Inspiration": [
            {"english": "Let inspiration guide you.", "telugu": "స్ఫూర్తి మిమ్మల్ని మార్గనిర్దేశం చేయనివ్వండి.", "transliteration": "Sphoorthi mimmlanni maarga-nirdesham cheyanivvandi."},
            {"english": "Be the inspiration others need.", "telugu": "ఇతరులకు అవసరమైన స్ఫూర్తిగా ఉండండి.", "transliteration": "Itharulaku avasaramaina sphoorthigaa undandi."},
            {"english": "Inspire by example, not words.", "telugu": "మాటలతో కాదు, ఆదర్శంతో స్ఫూర్తినివ్వండి.", "transliteration": "Maatalatho kaadu, aadarshamtho sphoorthi-nivvandi."},
            {"english": "Your story inspires others.", "telugu": "మీ కథ ఇతరులను స్ఫూర్తివంతం చేస్తుంది.", "transliteration": "Mee katha itharulana sphoorthi-vantham chesthundi."},
            {"english": "Find inspiration in nature.", "telugu": "ప్రకృతిలో స్ఫూర్తిని కనుగొనండి.", "transliteration": "Prakruthilo sphoorthini kanugonandi."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "telugu": "ప్రతిరోజు సానుకూలతను ఎంచుకోండి.", "transliteration": "Prathiroju saanukoolathana enchukondi."},
            {"english": "Positive thoughts create positive life.", "telugu": "సానుకూల ఆలోచనలు సానుకూల జీవితాన్ని సృష్టిస్తాయి.", "transliteration": "Saanukoola aalochanalu saanukoola jeevithaanni srushtistaayi."},
            {"english": "Surround yourself with positivity.", "telugu": "మిమ్మల్ని సానుకూలతతో చుట్టుముట్టండి.", "transliteration": "Mimmlanni saanukoolathatho chuttumuttandi."},
            {"english": "Every day is a fresh start.", "telugu": "ప్రతిరోజు ఒక కొత్త ప్రారంభం.", "transliteration": "Prathiroju oka koththa praarambham."},
            {"english": "Live life with a positive heart.", "telugu": "సానుకూల హృదయంతో జీవించండి.", "transliteration": "Saanukoola hridayamtho jeevinchandi."},
        ],
        "Courage": [
            {"english": "Be brave, take the leap.", "telugu": "ధైర్యంగా ఉండండి, ముందుకు వెళ్ళండి.", "transliteration": "Dhairyangaa undandi, mundhuku vellandi."},
            {"english": "Courage is not absence of fear.", "telugu": "ధైర్యం అనేది భయం లేకపోవడం కాదు.", "transliteration": "Dhairyam anedhi bhayam lekapovadam kaadhu."},
            {"english": "Face your fears with courage.", "telugu": "ధైర్యంతో మీ భయాలను ఎదుర్కోండి.", "transliteration": "Dhiryantho mee bhayaalana edhurukondi."},
            {"english": "Brave hearts change the world.", "telugu": "ధైర్యవంతుల హృదయాలు ప్రపంచాన్ని మారుస్తాయి.", "transliteration": "Dhairya-vanthula hridayaalu prapanchaanni maaruthaayi."},
            {"english": "Courage grows with use.", "telugu": "ధైర్యం వాడుకోగా పెరుగుతుంది.", "transliteration": "Dhairyam vaadukogaa peruguthundi."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "telugu": "మీరు కలుసుకునే ప్రతి ఒక్కరితో దయగా ఉండండి.", "transliteration": "Meeru kalusukuney prathi okkaritho dhayagaa undandi."},
            {"english": "Kindness costs nothing, means everything.", "telugu": "దయకు ఖర్చు లేదు, అది అంతా అర్థం చేస్తుంది.", "transliteration": "Dayaku kharchu ledu, adi anthaa artham chesthundi."},
            {"english": "A kind word warms the heart.", "telugu": "దయగల మాట హృదయాన్ని వెచ్చగా చేస్తుంది.", "transliteration": "Dayagala maata hridayaanni vechchagaa chesthundi."},
            {"english": "Spread kindness wherever you go.", "telugu": "ఎక్కడికి వెళ్ళినా దయను పంచండి.", "transliteration": "Ekkadiki vellina dayana panchandi."},
            {"english": "Kindness makes the world better.", "telugu": "దయ ప్రపంచాన్ని మెరుగుపరుస్తుంది.", "transliteration": "Daya prapanchaanni merugu-parusthundi."},
        ],
        "Patience": [
            {"english": "Good things come to those who wait.", "telugu": "ఎదురుచూసేవారికి మంచి విషయాలు వస్తాయి.", "transliteration": "Edhuruchosevaariki manchi vishayaalu vasthaayi."},
            {"english": "Patience is a virtue.", "telugu": "ఓపిక ఒక సుగుణం.", "transliteration": "Opika oka sugunam."},
            {"english": "Take your time, don't rush.", "telugu": "మీ సమయం తీసుకోండి, త్వరపడకండి.", "transliteration": "Mee samayam theesukondi, thvarapada-kandi."},
            {"english": "Patience brings peace of mind.", "telugu": "ఓపిక మనసుకు శాంతినిస్తుంది.", "transliteration": "Opika manasuku shanthim-isthundi."},
            {"english": "Wait patiently, trust the process.", "telugu": "ఓపికగా ఎదురుచూడండి, ప్రక్రియను నమ్మండి.", "transliteration": "Opikagaa edhuruchoodandi, prakriyana nammnadi."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "telugu": "క్షమించండి, మిమ్మల్ని విముక్తం చేసుకోండి.", "transliteration": "Kshaminchandi, mimmlanni vimuktham chesukondi."},
            {"english": "Forgiveness is a gift to yourself.", "telugu": "క్షమాపణ మీకు మీరే ఇచ్చుకున్న బహుమతి.", "transliteration": "Kshamaapanam meeku meeray ichhukunna bahumathi."},
            {"english": "Let go of grudges, find peace.", "telugu": "పగలను వదులుకోండి, శాంతిని కనుగొనండి.", "transliteration": "Pagalana vadulukondi, shaanthini kanugonandi."},
            {"english": "To err is human, to forgive divine.", "telugu": "తప్పు చేయడం మానవ సహజం, క్షమించడం దైవికం.", "transliteration": "Thappu cheyadam maanava sahajam, kshaminchadam daivikam."},
            {"english": "Forgiveness heals all wounds.", "telugu": "క్షమాపణ అన్ని గాయాలను నయం చేస్తుంది.", "transliteration": "Kshamaapanam anni gaayaalana nayam chesthundi."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "telugu": "మీరు తెలుసుకున్న దానికన్నా బలంగా ఉన్నారు.", "transliteration": "Meeru thelusukunna daanikanna balangaa-unnaru."},
            {"english": "Strength comes from within.", "telugu": "బలం లోపలి నుండి వస్తుంది.", "transliteration": "Balam lopali nundi vasthundi."},
            {"english": "Your struggles develop your strength.", "telugu": "మీ పోరాటాలు మీ బలాన్ని పెంచుతాయి.", "transliteration": "Mee pooraatallu mee balanni penchuthaayi."},
            {"english": "Be strong, stay steady.", "telugu": "బలంగా ఉండండి, స్థిరంగా ఉండండి.", "transliteration": "Balamgaa undandi, sthiramgaa undandi."},
            {"english": "Inner strength conquers all.", "telugu": "అంతర్బలం అన్నింటినీ జయిస్తుంది.", "transliteration": "Anthar-balam annintini jayisthundi."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "telugu": "ప్రతి క్షణంలో ఆనందాన్ని కనుగొనండి.", "transliteration": "Prathi kshanamlo aanandhaanni kanugonandi."},
            {"english": "Joy is contagious, spread it.", "telugu": "ఆనందం అంటువ్వుతుంది, పంచండి.", "transliteration": "Aanandham antuvuventhundi, panchandi."},
            {"english": "Let joy fill your heart today.", "telugu": "ఈరోజు ఆనందం మీ హృదయాన్ని నింపనివ్వండి.", "transliteration": "Eeroju aanandam mee hridayaanni ninpaa-nivvandi."},
            {"english": "Choose joy over worry.", "telugu": "బెంగ కంటే ఆనందాన్ని ఎంచుకోండి.", "transliteration": "Benga kantey aanandhaanni enchukondi."},
            {"english": "Joy is the simplest form of gratitude.", "telugu": "ఆనందం అనేది కృతజ్ఞత యొక్క సరళమైన రూపం.", "transliteration": "Aanandham anedhi kruthagnatha yokka sarala-maina roopam."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "telugu": "మీ జీవితంలో సమతుల్యతను కనుగొనండి.", "transliteration": "Mee jeevithamlo samathul yathana kanugonandi."},
            {"english": "Balance is the key to happiness.", "telugu": "సమతుల్యతే సంతోషానికి మార్గం.", "transliteration": "Samathulyathe santhoshaaniki maargam."},
            {"english": "Work hard, rest well.", "telugu": "గట్టిగా పని చేయండి, బాగా విశ్రాంతి తీసుకోండి.", "transliteration": "Gattigaa pani cheyandi, baagaa vishraanthi theesukondi."},
            {"english": "A balanced life is a peaceful life.", "telugu": "సమతుల్య జీవితమే శాంతిమయ జీవితం.", "transliteration": "Samathuly jeevithame shaanthimaya jeevitham."},
            {"english": "Prioritize what matters most.", "telugu": "అత్యంత ముఖ్యమైనదానికి ప్రాధాన్యత ఇవ్వండి.", "transliteration": "Athyantam mukhyamainadaaniki praadhaanyatha ivvandi."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "telugu": "వృద్ధి మీ సౌకర్య మండలం వెలుపల జరుగుతుంది.", "transliteration": "Vrudhdhi mee soukarthya mandalam velupala Jaruguthundi."},
            {"english": "Embrace change, grow stronger.", "telugu": "మార్పును ఆహ్వానించండి, బలపడండి.", "transliteration": "Maarupuna aahvaaninchandi, balapadandi."},
            {"english": "Every challenge is a growth opportunity.", "telugu": "ప్రతి సవాలూ వృద్ధికి ఒక అవకాశం.", "transliteration": "Prathi-savaaloo vrudhdhiki oka avakaasham."},
            {"english": "Grow through what you go through.", "telugu": "మీ అనుభవాల ద్వారా పెరగండి.", "transliteration": "Mee anubhavaala dhwaaraa peragandi."},
            {"english": "Personal growth is a lifelong journey.", "telugu": "వ్యక్తిగత వృద్ధి జీవితాంతపు ప్రయాణం.", "transliteration": "Vyakthigatha vrudhdhi jeevithaanthapu prayaanam."},
        ],
        "Purpose": [
            {"english": "Find your purpose, live it.", "telugu": "మీ ప్రయోజనాన్ని కనుగొనండి, దానిని జీవించండి.", "transliteration": "Mee prayojanaanni kanugonandi, daanini jeevinchandi."},
            {"english": "Purpose gives life meaning.", "telugu": "ప్రయోజనం జీవితానికి అర్థాన్ని ఇస్తుంది.", "transliteration": "Prayojanam jeevithaaniki arthaanni isthundi."},
            {"english": "Live with purpose and passion.", "telugu": "ప్రయోజనంతో మరియు ఉత్సాహంతో జీవించండి.", "transliteration": "Prayojanamtho mariyu uthsaahamtho jeevinchandi."},
            {"english": "Your purpose is your calling.", "telugu": "మీ ప్రయోజనమే మీ పిలుపు.", "transliteration": "Mee prayojaname-mee pilupu."},
            {"english": "Discover purpose in everyday moments.", "telugu": "రోజువారీ క్షణాల్లో ప్రయోజనాన్ని కనుగొనండి.", "transliteration": "Rojuvaaree kshanaallo prayojanaanni kanugonandi."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "telugu": "ఈ క్షణంలో ఉండండి.", "transliteration": "Ee kshanamlo undandi."},
            {"english": "Mindfulness brings inner peace.", "telugu": "సంపూర్ణ అవగాహన అంతర్ శాంతినిస్తుంది.", "transliteration": "Sampoorna avagaahana anthar shaanthini-sthundi."},
            {"english": "Breathe deeply, stay mindful.", "telugu": "లోతుగా ఊపిరి తీసుకోండి, జాగ్రత్తగా ఉండండి.", "transliteration": "Lothugaa oopiri theesukondi, jaagrattagaa undandi."},
            {"english": "The present moment is all we have.", "telugu": "ప్రస్తుత క్షణమే మనకు ఉన్నదంతా.", "transliteration": "Prasthutha kshaname manaku unna-danthaa."},
            {"english": "Practice mindfulness daily.", "telugu": "ప్రతిరోజు సంపూర్ణ అవగాహనను అభ్యాసం చేయండి.", "transliteration": "Prathiroju sampoorna avagaahanana abhyaasam cheyandi."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]
    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


async def generate_audio_with_retries(text: str, voice: str, output_path: str, max_retries: int = 3):
    """Generate audio with retry logic for TTS failures"""
    import asyncio
    for attempt in range(1, max_retries + 1):
        success = await generate_single_audio(text, voice, output_path)
        if success:
            if Path(output_path).exists() and Path(output_path).stat().st_size > 100:
                return True
            else:
                print(f"    TTS file too small or missing, retrying ({attempt}/{max_retries})...")
                await asyncio.sleep(2 * attempt)
                continue
        else:
            if attempt < max_retries:
                wait = 2 * attempt
                print(f"    TTS retry {attempt}/{max_retries} in {wait}s...")
                await asyncio.sleep(wait)
            else:
                print(f"    TTS failed after {max_retries} attempts, using silence fallback")
                return False
    return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        telugu_file = output_dir / f"telugu_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    TE: {phrase['telugu']}")

        # Generate English audio
        en_success = asyncio.run(generate_audio_with_retries(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    - English: {english_file.name}")
        else:
            print(f"    - English: SILENCE FALLBACK (TTS failed)")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Telugu audio
        te_success = asyncio.run(generate_audio_with_retries(phrase["telugu"], TELUGU_VOICE, str(telugu_file)))
        if te_success:
            print(f"    - Telugu: {telugu_file.name}")
        else:
            print(f"    - Telugu: SILENCE FALLBACK (TTS failed)")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(telugu_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        te_duration = get_audio_duration(str(telugu_file))

        # Add pause between English and Telugu
        pause_between = 0.5
        total_duration = en_duration + pause_between + te_duration

        print(f"    Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + TE: {te_duration:.2f}s)")

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(telugu_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{telugu_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "telugu": str(telugu_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "te_duration": te_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

NOTO_TELUGU_FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosanstelugu/NotoSansTelugu%5BBDU%5D.ttf"
FONTS_DIR = BASE_DIR / "fonts"


def ensure_telugu_font():
    """Download NotoSansTelugu font if not available locally"""
    font_file = FONTS_DIR / "NotoSansTelugu-Bold.ttf"
    if font_file.exists():
        return str(font_file)

    FONTS_DIR.mkdir(exist_ok=True)

    try:
        import urllib.request
        print("[font] Downloading NotoSansTelugu font (Telugu script support)...")
        urllib.request.urlretrieve(NOTO_TELUGU_FONT_URL, str(font_file))
        print(f"[font] Downloaded: {font_file}")
        return str(font_file)
    except Exception as e:
        print(f"[font] Download failed: {e}")
        alt_url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Bold.ttf"
        try:
            import urllib.request
            urllib.request.urlretrieve(alt_url, str(font_file))
            print(f"[font] Downloaded from alternate: {font_file}")
            return str(font_file)
        except Exception as e2:
            print(f"[font] Alternate download also failed: {e2}")
    return None


def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    category_colors = {
        "Greetings": [(70, 130, 180), (255, 140, 0), (255, 255, 0), (255, 99, 71)],
        "Basic Phrases": [(60, 179, 113), (255, 215, 0), (144, 238, 144), (255, 140, 0)],
        "Common Expressions": [(138, 43, 226), (255, 20, 147), (75, 0, 130), (255, 105, 180)],
        "Travel Telugu": [(0, 191, 255), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Restaurant Telugu": [(255, 69, 0), (255, 215, 0), (220, 20, 60), (255, 140, 0)],
        "Shopping Telugu": [(255, 105, 180), (0, 100, 80), (255, 192, 203), (0, 200, 160)],
        "Emergency Telugu": [(255, 0, 0), (139, 0, 0), (255, 69, 0), (220, 20, 60)],
        "Family Terms": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],
        "Numbers Telugu": [(255, 215, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],
        "Time Telugu": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],
        "Love": [(255, 0, 100), (139, 0, 0), (255, 105, 180), (255, 192, 203)],
        "Success": [(255, 215, 0), (0, 100, 0), (255, 140, 0), (34, 139, 34)],
        "Wisdom": [(0, 0, 139), (255, 215, 0), (70, 130, 180), (255, 255, 0)],
        "Happiness": [(255, 255, 0), (255, 0, 255), (255, 165, 0), (147, 112, 219)],
        "Self Improvement": [(0, 128, 0), (255, 215, 0), (0, 255, 0), (255, 140, 0)],
        "Gratitude": [(255, 127, 80), (75, 0, 130), (255, 160, 122), (138, 43, 226)],
        "Friendship": [(255, 192, 203), (0, 100, 80), (255, 105, 180), (0, 200, 160)],
        "Hope": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Creativity": [(255, 0, 127), (0, 0, 139), (255, 20, 147), (75, 0, 130)],
        "Inner Peace": [(135, 206, 235), (0, 0, 100), (176, 224, 230), (75, 0, 130)],
        "Confidence": [(255, 69, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],
        "Perseverance": [(139, 69, 19), (255, 215, 0), (160, 82, 45), (255, 140, 0)],
        "Inspiration": [(255, 0, 255), (75, 0, 130), (255, 20, 147), (0, 0, 139)],
        "Positive Life": [(50, 205, 50), (255, 0, 127), (144, 238, 144), (255, 20, 147)],
        "Courage": [(178, 34, 34), (255, 215, 0), (220, 20, 60), (255, 140, 0)],
        "Kindness": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],
        "Patience": [(34, 139, 34), (255, 255, 0), (60, 179, 113), (255, 215, 0)],
        "Forgiveness": [(230, 230, 250), (75, 0, 130), (216, 191, 216), (138, 43, 226)],
        "Strength": [(100, 100, 100), (255, 69, 0), (150, 150, 150), (255, 140, 0)],
        "Joy": [(255, 255, 0), (255, 0, 127), (255, 215, 0), (147, 112, 219)],
        "Balance": [(60, 179, 113), (138, 43, 226), (152, 251, 152), (75, 0, 130)],
        "Growth": [(0, 100, 0), (255, 215, 0), (34, 139, 34), (255, 140, 0)],
        "Purpose": [(75, 0, 130), (255, 215, 0), (138, 43, 226), (255, 140, 0)],
        "Mindfulness": [(210, 180, 140), (75, 0, 130), (245, 245, 220), (138, 43, 226)],
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def _find_telugu_font_file():
    """Find the best Telugu font file path for HarfBuzz rendering"""
    candidates = [
        str(FONTS_DIR / "NotoSansTelugu-Bold.ttf"),
        str(FONTS_DIR / "NotoSansTelugu-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansTelugu-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTelugu-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/gautami.ttf",
        "C:/Windows/Fonts/mangal.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path

    for search_dir in ["/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts"]:
        if not Path(search_dir).exists():
            continue
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                fname_lower = fname.lower()
                if any(t.lower() in fname_lower for t in ["notosanstelugu", "nirmala", "gautami", "mangal", "latha"]):
                    return str(Path(root) / fname)

    return None


def _render_text_harfbuzz(text, font_path, font_size, fill_color, stroke_color=None, stroke_width=0):
    """Render Telugu text with proper HarfBuzz shaping and FreeType rasterization.
    Returns a PIL Image with the rendered text on transparent background."""
    import uharfbuzz as hb
    import freetype as ft
    from PIL import Image, ImageDraw, ImageChops

    blob = hb.Blob.from_file_path(font_path)
    hb_face = hb.Face(blob)
    hb_font = hb.Font(hb_face)
    hb_font.scale = (font_size * 64, font_size * 64)

    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(hb_font, buffer)

    infos = buffer.glyph_infos
    positions = buffer.glyph_positions

    ft_face = ft.Face(font_path)
    ft_face.set_char_size(font_size * 64)

    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    x_cursor = 0.0
    y_cursor = 0.0
    glyph_metrics = []

    for info, pos in zip(infos, positions):
        ft_face.load_glyph(info.codepoint)
        bitmap = ft_face.glyph.bitmap
        bitmap_left = ft_face.glyph.bitmap_left
        bitmap_top = ft_face.glyph.bitmap_top
        x_off = pos.x_offset / 64.0
        y_off = pos.y_offset / 64.0
        x_adv = pos.x_advance / 64.0

        px = x_cursor + x_off + bitmap_left
        py = y_cursor + y_off - bitmap_top

        if bitmap.width > 0 and bitmap.rows > 0:
            min_x = min(min_x, px - stroke_width)
            min_y = min(min_y, py - stroke_width)
            max_x = max(max_x, px + bitmap.width + stroke_width)
            max_y = max(max_y, py + bitmap.rows + stroke_width)

        glyph_metrics.append({
            'codepoint': info.codepoint,
            'x': px, 'y': py,
            'width': bitmap.width, 'height': bitmap.rows,
            'x_advance': x_adv,
        })
        x_cursor += x_adv

    if min_x == float('inf'):
        total_width = max(x_cursor, 50)
        total_height = int(font_size * 1.5)
        min_x = 0
        min_y = 0
    else:
        total_width = max(max_x - min_x + stroke_width * 2, x_cursor + stroke_width * 2)
        total_height = max_y - min_y + stroke_width * 2

    total_width = int(total_width) + stroke_width * 2 + 4
    total_height = int(total_height) + stroke_width * 2 + 4

    img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

    def _draw_glyphs(target_img, color):
        draw = ImageDraw.Draw(target_img)
        for gm in glyph_metrics:
            ft_face.load_glyph(gm['codepoint'])
            bitmap = ft_face.glyph.bitmap
            if bitmap.width > 0 and bitmap.rows > 0:
                glyph_img = Image.frombytes('L', (bitmap.width, bitmap.rows), bytes(bitmap.buffer))
                paste_x = int(gm['x'] - min_x + stroke_width)
                paste_y = int(gm['y'] - min_y + stroke_width)
                if color[-1] == 255:
                    colored_glyph = Image.new('RGBA', glyph_img.size, color)
                    colored_glyph.putalpha(glyph_img)
                    target_img.paste(colored_glyph, (paste_x, paste_y), glyph_img)
                else:
                    blended = Image.new('RGBA', glyph_img.size, color)
                    mask = glyph_img.point(lambda p: min(255, int(p * color[-1] / 255)))
                    blended.putalpha(mask)
                    target_img.paste(blended, (paste_x, paste_y), blended)

    if stroke_width > 0 and stroke_color:
        stroke_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx * dx + dy * dy <= stroke_width * stroke_width + 1:
                    shifted = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
                    _draw_glyphs(shifted, stroke_color)
                    stroke_img = Image.alpha_composite(stroke_img, ImageChops.offset(shifted, dx, dy))
        img = Image.alpha_composite(img, stroke_img)

    fill_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    _draw_glyphs(fill_img, fill_color)
    img = Image.alpha_composite(img, fill_img)

    return img, int(x_cursor)


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageChops
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    downloaded_font = ensure_telugu_font()

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # English text fonts (bold, professional)
    english_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    telugu_font_paths = [
        str(FONTS_DIR / "NotoSansTelugu-Bold.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansTelugu-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTelugu-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTelugu-Regular.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/nirmala.ttf",
        "C:/Windows/Fonts/gautami.ttf",
        "C:/Windows/Fonts/mangal.ttf",
    ]

    def load_font(font_paths, size):
        """Load font with fallback - searches directories if direct paths fail"""
        for font_path in font_paths:
            try:
                f = ImageFont.truetype(font_path, size)
                test_bbox = f.getbbox("తెలుగు")
                if test_bbox[2] - test_bbox[0] > size * 0.5:
                    return f
            except (IOError, OSError):
                continue

        font_search_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "C:/Windows/Fonts",
        ]
        telugu_font_names = [
            "NotoSansTelugu-Bold.ttf", "NotoSansTelugu-Regular.ttf",
            "NotoSansTelugu-Bold.ttc", "NotoSansTelugu-Regular.ttc",
            "Nirmala.ttc", "gautami.ttf", "mangal.ttf", "latha.ttf",
        ]

        for search_dir in font_search_dirs:
            if not Path(search_dir).exists():
                continue
            for root, dirs, files in os.walk(search_dir):
                for fname in files:
                    fname_lower = fname.lower()
                    if any(t.lower() in fname_lower for t in telugu_font_names):
                        try:
                            f = ImageFont.truetype(str(Path(root) / fname), size)
                            test_bbox = f.getbbox("తెలుగు")
                            if test_bbox[2] - test_bbox[0] > size * 0.5:
                                print(f"  [font] Found Telugu font: {fname}")
                                return f
                        except (IOError, OSError):
                            continue

        print("  [WARNING] No Telugu-capable font found! Telugu text may not render.")
        return ImageFont.load_default()

    # English text fonts (bold, professional)
    font_category = load_font(english_font_paths, 60)
    font_large = load_font(english_font_paths, 85)
    font_branding = load_font(english_font_paths, 52)

    # Telugu text fonts (supports Telugu characters, bold)
    font_telugu = load_font(telugu_font_paths, 65)

    # Transliteration fonts - BOLD and LARGER for better visibility
    font_transliteration = load_font(english_font_paths, 55)

    english = phrase_data.get("english", "")
    telugu = phrase_data.get("telugu", "")
    transliteration = phrase_data.get("transliteration", phrase_data.get("romaji", ""))

    def wrap_text(text, font, max_width):
        """Wrap text to fit within max_width - handles both English and Telugu"""
        lines = []

        is_telugu = any('\u0c00' <= c <= '\u0c7f' for c in text)

        if is_telugu:
            words = text.split(' ')
            current_line = ''
            for word in words:
                test_line = (current_line + ' ' + word).strip() if current_line else word
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    width = bbox[2] - bbox[0]
                except Exception:
                    width = len(test_line) * 40
                if width <= max_width or not current_line:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            if not lines:
                lines = [text]
        else:
            words = text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

        return lines

    # Category at top
    category_text = category_english.upper()
    category_bbox = draw.textbbox((VIDEO_WIDTH // 2, 140), category_text, font=font_category, anchor="mm")
    padding = 25
    draw.rectangle(
        [(category_bbox[0] - padding, category_bbox[1] - padding),
         (category_bbox[2] + padding, category_bbox[3] + padding)],
        fill=(0, 0, 0, 200)
    )
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    # English text
    english_y = 470
    english_lines = wrap_text(english, font_large, VIDEO_WIDTH - 140)
    total_height = len(english_lines) * 95

    draw.rectangle(
        [(60, english_y - 55), (VIDEO_WIDTH - 60, english_y + total_height + 15)],
        fill=(20, 30, 80, 220)
    )

    for i, line in enumerate(english_lines):
        y_pos = english_y + (i * 95)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 255),
            font=font_large,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    # Telugu text - rendered with HarfBuzz for proper conjunct shaping
    telugu_y = english_y + total_height + 110
    telugu_font_path = _find_telugu_font_file()
    use_harfbuzz = telugu_font_path is not None

    if use_harfbuzz:
        try:
            import uharfbuzz as hb
            import freetype as ft
        except ImportError:
            use_harfbuzz = False
            print("  [WARNING] uharfbuzz/freetype not available, falling back to Pillow")

    if use_harfbuzz:
        max_telugu_width = VIDEO_WIDTH - 200
        telugu_words = telugu.split(' ')
        telugu_lines = []
        current_line_words = []

        for word in telugu_words:
            test_line = ' '.join(current_line_words + [word]) if current_line_words else word
            _, test_w = _render_text_harfbuzz(
                test_line, telugu_font_path, 65,
                fill_color=(255, 255, 0, 255)
            )
            single_word_w = 0
            if current_line_words:
                _, single_word_w = _render_text_harfbuzz(
                    word, telugu_font_path, 65,
                    fill_color=(255, 255, 0, 255)
                )

            if test_w <= max_telugu_width or not current_line_words:
                current_line_words.append(word)
            else:
                telugu_lines.append(' '.join(current_line_words))
                current_line_words = [word]

        if current_line_words:
            telugu_lines.append(' '.join(current_line_words))

        if not telugu_lines:
            telugu_lines = [telugu]

        line_spacing = 85
        total_height = len(telugu_lines) * line_spacing

        telugu_padding = 60
        draw.rectangle(
            [(50, telugu_y - telugu_padding), (VIDEO_WIDTH - 50, telugu_y + total_height + telugu_padding - 10)],
            fill=(80, 30, 30, 220)
        )

        for i, line in enumerate(telugu_lines):
            rendered, text_w = _render_text_harfbuzz(
                line, telugu_font_path, 65,
                fill_color=(255, 255, 0, 255),
                stroke_color=(0, 0, 0, 255),
                stroke_width=2
            )
            x_pos = (VIDEO_WIDTH - rendered.width) // 2
            y_pos = telugu_y + (i * line_spacing) - rendered.height // 2
            img.paste(rendered, (x_pos, y_pos), rendered)
    else:
        telugu_lines = wrap_text(telugu, font_telugu, VIDEO_WIDTH - 200)
        total_height = len(telugu_lines) * 75

        telugu_padding = 60
        draw.rectangle(
            [(50, telugu_y - telugu_padding), (VIDEO_WIDTH - 50, telugu_y + total_height + telugu_padding - 10)],
            fill=(80, 30, 30, 220)
        )

        for i, line in enumerate(telugu_lines):
            y_pos = telugu_y + (i * 75)
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                line,
                fill=(255, 255, 0),
                font=font_telugu,
                anchor="mm",
                stroke_width=3,
                stroke_fill=(0, 0, 0)
            )

    # Transliteration with FILLED BOX - BOLDER text for better visibility
    transliteration_y = telugu_y + total_height + 90
    transliteration_text = f"[{transliteration}]"
    transliteration_lines = wrap_text(transliteration_text, font_transliteration, VIDEO_WIDTH - 160)

    if transliteration_lines:
        transliteration_total_height = len(transliteration_lines) * 60
        draw.rectangle(
            [(70, transliteration_y - 25), (VIDEO_WIDTH - 70, transliteration_y + transliteration_total_height + 15)],
            fill=(40, 40, 40, 230)
        )

        for i, transliteration_line in enumerate(transliteration_lines):
            y_pos = transliteration_y + (i * 60)
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                transliteration_line,
                fill=(255, 255, 255),
                font=font_transliteration,
                anchor="mm",
                stroke_width=3,
                stroke_fill=(0, 0, 0, 220)
            )

    # Branding
    branding_y = VIDEO_HEIGHT - 100
    draw.rectangle(
        [(0, branding_y - 30), (VIDEO_WIDTH, branding_y + 50)],
        fill=(0, 0, 0, 180)
    )
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY TELUGU",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + TE: {audio_info.get('te_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        category_english = get_available_category()

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_TELUGU[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['telugu']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        print(f"  Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Telugu with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_telugu": CATEGORIES_TELUGU[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"REEL COMPLETE!")
    print(f"  {reel_dir}")
    print(f"  {output_video.name}")
    print(f"  Branding: Velocity Telugu")
    print(f"{'='*80}\n")

    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print("VELOCITY TELUGU - FACEBOOK REELS AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  - Natural pauses with commas (non-robotic TTS)")
    print("  - Perfect audio-video synchronization")
    print("  - Complete audio playback guaranteed")
    print("  - English category names (for learners)")
    print("  - Velocity Telugu branding at bottom")
    print("  - NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_TELUGU[cat]})")
    print(f"\nDAILY CAPACITY:")
    print(f"  4 reels per day = 20 unique phrases daily")
    print(f"  {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  Phrase history is PERMANENT (never deletes)")
    print(f"  AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)