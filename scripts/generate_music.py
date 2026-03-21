"""
Broken Court — MusicGen Background Music Generator
Uses Meta's MusicGen-small via Hugging Face transformers (runs on RTX 4070).
Generates scene-specific background music tracks for each chapter.
"""
import torch
import scipy.io.wavfile
from pathlib import Path

BASE = Path(r"F:\BROKEN-COURT")
MUSIC_DIR = BASE / "audio" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# ── Scene music prompts for each chapter ──
SCENES = [
    {
        "name": "ch01_island_roots",
        "prompt": "gentle acoustic guitar, Caribbean tropical atmosphere, warm breeze, isolated island feeling, nostalgic, soft percussion, ambient ocean sounds, contemplative mood, cinematic underscore",
        "duration": 30,
    },
    {
        "name": "ch01_supernatural_moment",
        "prompt": "sudden dramatic orchestral hit, deep bass, mysterious tension, supernatural energy rising, short powerful moment, cinematic impact, thunder-like reverb",
        "duration": 15,
    },
    {
        "name": "ch02_training_begins",
        "prompt": "building percussion rhythm, motivational sports music, acoustic guitar transitioning to electric, Caribbean fusion, growing intensity, determination theme, cinematic sports montage",
        "duration": 30,
    },
    {
        "name": "ch03_leaving_island",
        "prompt": "emotional piano melody, bittersweet farewell, Caribbean acoustic guitar fading, strings entering slowly, the weight of leaving home, cinematic emotional scene, gentle and sad",
        "duration": 25,
    },
    {
        "name": "ch03_new_world",
        "prompt": "grand orchestral reveal, awe-inspiring, massive scale, professional tournament atmosphere, crowd ambience, bright and overwhelming, cinematic wonder",
        "duration": 20,
    },
    {
        "name": "ch04_first_tournament",
        "prompt": "intense sports battle music, fast percussion, driving rhythm, competitive tennis match energy, electric guitar riffs, orchestral strings, high stakes, cinematic action",
        "duration": 30,
    },
    {
        "name": "ch05_the_wall",
        "prompt": "relentless mechanical rhythm, oppressive heavy percussion, hitting a wall repeatedly, frustration building, stoic and immovable force, dark cinematic tension",
        "duration": 25,
    },
    {
        "name": "ch06_psychological_warfare",
        "prompt": "unsettling dissonant strings, psychological thriller atmosphere, creeping dread, charming surface hiding darkness, manipulation theme, off-beat rhythm, cinematic suspense",
        "duration": 25,
    },
    {
        "name": "ch06_mental_armor",
        "prompt": "silence breaking into powerful orchestral surge, cold determination, transformation moment, ice-like clarity, cinematic rebirth theme, controlled power",
        "duration": 20,
    },
    {
        "name": "ch07_golden_boy_battle",
        "prompt": "epic orchestral battle music, two titans clashing, full orchestra with choir, dramatic tennis match finale, cinematic peak intensity, heroic theme emerging",
        "duration": 30,
    },
    {
        "name": "ch08_reflection",
        "prompt": "quiet contemplative piano, hotel room at night, looking at ceiling, processing everything that happened, gentle strings, introspective mood, cinematic emotional reflection",
        "duration": 25,
    },
    {
        "name": "ch09_world_stage",
        "prompt": "massive stadium atmosphere, global scale orchestral, the whole world watching, pressure and spotlight, cinematic grandeur, building to something enormous",
        "duration": 25,
    },
    {
        "name": "ch10_the_call",
        "prompt": "triumphant yet bittersweet orchestral theme, the end of volume one, looking forward to the future, warm Caribbean guitar returning underneath grand orchestra, cinematic finale, hope and determination",
        "duration": 30,
    },
    {
        "name": "ch10_don_emilio_moonlight",
        "prompt": "mysterious night atmosphere, moonlight on a tennis court, old wise man watching from shadows, gentle Caribbean breeze, secrets and legacy, cinematic ambient, subtle and powerful",
        "duration": 20,
    },
]


def main():
    print("=" * 60)
    print("BROKEN COURT — MusicGen Background Music Generator")
    print("=" * 60)
    print("Loading MusicGen model (first run downloads ~2GB)...")

    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    model = model.to("cuda" if torch.cuda.is_available() else "cpu")
    sample_rate = model.config.audio_encoder.sampling_rate

    print(f"Model loaded. Sample rate: {sample_rate}Hz")
    print(f"Device: {next(model.parameters()).device}")
    print()

    for i, scene in enumerate(SCENES):
        output_path = MUSIC_DIR / f"{scene['name']}.wav"
        if output_path.exists():
            print(f"[{i+1}/{len(SCENES)}] SKIP (exists): {scene['name']}")
            continue

        print(f"[{i+1}/{len(SCENES)}] Generating: {scene['name']} ({scene['duration']}s)")
        print(f"  Prompt: {scene['prompt'][:80]}...")

        # MusicGen-small generates ~256 tokens/sec at 32kHz
        # max_new_tokens controls duration: ~50 tokens per second
        tokens = scene["duration"] * 50

        inputs = processor(
            text=[scene["prompt"]],
            padding=True,
            return_tensors="pt",
        ).to(model.device)

        with torch.no_grad():
            audio_values = model.generate(**inputs, max_new_tokens=tokens)

        audio_data = audio_values[0, 0].cpu().numpy()
        scipy.io.wavfile.write(str(output_path), rate=sample_rate, data=audio_data)
        print(f"  Saved: {output_path.name} ({len(audio_data)/sample_rate:.1f}s)")
        print()

    print(f"\n{'=' * 60}")
    print(f"DONE — Music files saved to {MUSIC_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
