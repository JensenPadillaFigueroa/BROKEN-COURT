"""
Broken Court — Piper TTS Narration Generator
Generates high-quality local audio for all dialogue lines using Piper TTS.
Each character gets different pitch/speed settings for differentiation.
"""
import subprocess, json, os, re, wave, struct, sys
from pathlib import Path
from html.parser import HTMLParser

# ── Paths ──
BASE = Path(r"F:\BROKEN-COURT")
HTML_FILE = BASE / "manga-viewer.html"
VOICE_MODEL = BASE / "audio" / "voices" / "en_US-lessac-medium.onnx"
OUTPUT_DIR = BASE / "audio" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Character voice profiles (length_scale = slower > 1.0, faster < 1.0) ──
PROFILES = {
    "narrator":     {"length_scale": 1.05, "noise_scale": 0.5,  "noise_w": 0.7},
    "yadi":         {"length_scale": 0.92, "noise_scale": 0.6,  "noise_w": 0.8},
    "yen":          {"length_scale": 1.15, "noise_scale": 0.4,  "noise_w": 0.5},
    "papa":         {"length_scale": 1.18, "noise_scale": 0.45, "noise_w": 0.6},
    "mama":         {"length_scale": 1.05, "noise_scale": 0.55, "noise_w": 0.75},
    "don emilio":   {"length_scale": 1.22, "noise_scale": 0.4,  "noise_w": 0.5},
    "daimon":       {"length_scale": 0.95, "noise_scale": 0.55, "noise_w": 0.7},
    "kai":          {"length_scale": 1.20, "noise_scale": 0.3,  "noise_w": 0.4},
    "luca":         {"length_scale": 0.98, "noise_scale": 0.6,  "noise_w": 0.8},
    "crowd":        {"length_scale": 0.88, "noise_scale": 0.7,  "noise_w": 0.9},
    "_default":     {"length_scale": 1.0,  "noise_scale": 0.5,  "noise_w": 0.7},
}

def get_profile(speaker):
    if not speaker:
        return PROFILES["_default"]
    s = speaker.lower()
    for key in PROFILES:
        if key in s:
            return PROFILES[key]
    return PROFILES["_default"]


# ── HTML Parser to extract dialogue lines ──
class DialogueExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.current_chapter = 0
        self.current_page = 0
        self.in_element = None
        self.current_text = ""
        self.current_class = ""
        self.in_speaker = False
        self.speaker_text = ""
        self.in_line = False
        self.line_text = ""
        self.in_chapter_num = False
        self.in_chapter_title = False
        self.in_chapter_summary = False
        self.in_page_label = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        
        if tag == "section" and "chapter" in cls and "char-gallery" not in cls:
            self.current_chapter += 1
            self.current_page = 0
        
        if tag == "div":
            if "manga-page" in cls:
                self.current_page += 1
            elif cls == "chapter-num":
                self.in_chapter_num = True
                self.current_text = ""
            elif cls == "chapter-title":
                self.in_chapter_title = True
                self.current_text = ""
            elif cls == "chapter-summary":
                self.in_chapter_summary = True
                self.current_text = ""
            elif cls == "page-label":
                self.in_page_label = True
                self.current_text = ""
            elif "narration" in cls:
                self.in_element = "narration"
                self.current_text = ""
            elif "speech" in cls and "speaker" not in cls:
                self.in_element = "speech"
                self.speaker_text = ""
                self.line_text = ""
            elif "thought" in cls:
                self.in_element = "thought"
                self.current_text = ""
            elif "sfx" in cls:
                self.in_element = "sfx"
                self.current_text = ""
            elif "scene-note" in cls:
                self.in_element = "scene-note"
                self.current_text = ""

        if tag == "span":
            if "speaker" in cls:
                self.in_speaker = True
                self.speaker_text = ""
            elif "line" in cls:
                self.in_line = True
                self.line_text = ""

    def handle_data(self, data):
        if self.in_chapter_num:
            self.current_text += data
        elif self.in_chapter_title:
            self.current_text += data
        elif self.in_chapter_summary:
            self.current_text += data
        elif self.in_page_label:
            self.current_text += data
        elif self.in_speaker:
            self.speaker_text += data
        elif self.in_line:
            self.line_text += data
        elif self.in_element in ("narration", "thought", "sfx", "scene-note"):
            self.current_text += data

    def handle_endtag(self, tag):
        if tag == "div":
            if self.in_chapter_num:
                self.in_chapter_num = False
                self.lines.append({
                    "chapter": self.current_chapter,
                    "page": 0,
                    "speaker": "Narrator",
                    "text": self.current_text.strip(),
                    "type": "narration"
                })
            elif self.in_chapter_title:
                self.in_chapter_title = False
                self.lines.append({
                    "chapter": self.current_chapter,
                    "page": 0,
                    "speaker": "Narrator",
                    "text": self.current_text.strip(),
                    "type": "narration"
                })
            elif self.in_chapter_summary:
                self.in_chapter_summary = False
                self.lines.append({
                    "chapter": self.current_chapter,
                    "page": 0,
                    "speaker": "Narrator",
                    "text": self.current_text.strip(),
                    "type": "narration"
                })
            elif self.in_page_label:
                self.in_page_label = False
            elif self.in_element == "narration":
                self.in_element = None
                text = self.current_text.strip()
                if text:
                    self.lines.append({
                        "chapter": self.current_chapter,
                        "page": self.current_page,
                        "speaker": "Narrator",
                        "text": text,
                        "type": "narration"
                    })
            elif self.in_element == "speech":
                self.in_element = None
                speaker = self.speaker_text.strip() or "Narrator"
                text = self.line_text.strip().strip('\u201c\u201d""')
                if text:
                    self.lines.append({
                        "chapter": self.current_chapter,
                        "page": self.current_page,
                        "speaker": speaker,
                        "text": text,
                        "type": "speech"
                    })
            elif self.in_element == "thought":
                self.in_element = None
                raw = self.current_text.strip()
                m = re.match(r'^(.+?):\s*["\u201c]?(.+?)["\u201d]?$', raw, re.S)
                if m:
                    speaker, text = m.group(1).strip(), m.group(2).strip()
                else:
                    speaker, text = "Yadi", raw
                if text:
                    self.lines.append({
                        "chapter": self.current_chapter,
                        "page": self.current_page,
                        "speaker": speaker,
                        "text": text,
                        "type": "thought"
                    })
            elif self.in_element == "sfx":
                self.in_element = None
                text = self.current_text.strip()
                if text:
                    self.lines.append({
                        "chapter": self.current_chapter,
                        "page": self.current_page,
                        "speaker": "SFX",
                        "text": text,
                        "type": "sfx"
                    })
            elif self.in_element == "scene-note":
                self.in_element = None
                text = self.current_text.strip()
                if text:
                    self.lines.append({
                        "chapter": self.current_chapter,
                        "page": self.current_page,
                        "speaker": "Narrator",
                        "text": text,
                        "type": "narration"
                    })

        if tag == "span":
            if self.in_speaker:
                self.in_speaker = False
            elif self.in_line:
                self.in_line = False


def extract_lines():
    """Parse HTML and extract all dialogue lines."""
    html = HTML_FILE.read_text(encoding="utf-8")
    parser = DialogueExtractor()
    parser.feed(html)
    return parser.lines


def generate_audio(text, output_path, profile):
    """Generate audio for a single line using Piper TTS."""
    cmd = [
        sys.executable, "-m", "piper",
        "--model", str(VOICE_MODEL),
        "--output_file", str(output_path),
        "--length-scale", str(profile["length_scale"]),
        "--noise-scale", str(profile["noise_scale"]),
        "--noise-w", str(profile["noise_w"]),
    ]
    proc = subprocess.run(
        cmd, input=text, capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        print(f"  ERROR: {proc.stderr[:200]}")
        return False
    return True


def main():
    print("=" * 60)
    print("BROKEN COURT — Piper TTS Narration Generator")
    print("=" * 60)

    # Check voice model exists
    if not VOICE_MODEL.exists():
        print(f"ERROR: Voice model not found at {VOICE_MODEL}")
        return

    # Extract all dialogue lines from HTML
    lines = extract_lines()
    print(f"\nExtracted {len(lines)} dialogue lines from manga-viewer.html")

    # Save extracted lines as JSON for reference
    manifest_path = OUTPUT_DIR / "lines_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)
    print(f"Saved manifest to {manifest_path}")

    # Generate audio for each line
    total = len(lines)
    for i, line in enumerate(lines):
        filename = f"ch{line['chapter']:02d}_p{line['page']:03d}_{i:04d}.wav"
        output_path = OUTPUT_DIR / filename
        line["audio_file"] = filename

        if output_path.exists():
            print(f"[{i+1}/{total}] SKIP (exists): {filename}")
            continue

        profile = get_profile(line["speaker"])
        text = line["text"]

        # Skip SFX (these should be sound effects, not narrated)
        if line["type"] == "sfx":
            print(f"[{i+1}/{total}] SKIP (SFX): {text[:50]}")
            continue

        print(f"[{i+1}/{total}] {line['speaker']}: {text[:60]}...")
        success = generate_audio(text, output_path, profile)
        if not success:
            print(f"  FAILED: {filename}")

    # Update manifest with audio file references
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"DONE — Audio files saved to {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
