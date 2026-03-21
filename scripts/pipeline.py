"""
Broken Court — Master Pipeline
Orchestrates the full video+audio generation pipeline:
  1. Generate narration audio (Piper TTS)
  2. Generate background music (MusicGen)
  3. Generate animated clips (ComfyUI + AnimateDiff) — manual step
  4. Assemble final video (FFmpeg)

Usage:
  python scripts/pipeline.py narration   — Generate all narration audio
  python scripts/pipeline.py music       — Generate background music
  python scripts/pipeline.py assemble    — Assemble final video from clips + audio
  python scripts/pipeline.py all         — Run steps 1, 2, 4 in sequence
"""
import subprocess, sys, json, os
from pathlib import Path

BASE = Path(r"F:\BROKEN-COURT")
SCRIPTS = BASE / "scripts"
AUDIO_OUTPUT = BASE / "audio" / "output"
MUSIC_DIR = BASE / "audio" / "music"
VIDEO_CLIPS = BASE / "video" / "clips"
VIDEO_FINAL = BASE / "video" / "final"


def run_script(name):
    script = SCRIPTS / name
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, str(script)], cwd=str(BASE))
    return result.returncode == 0


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
        return True
    except FileNotFoundError:
        print("ERROR: FFmpeg not found. Install from https://ffmpeg.org/download.html")
        print("  Or: winget install Gyan.FFmpeg")
        return False


def assemble_chapter(chapter_num):
    """Assemble a single chapter's clips + narration into a video."""
    manifest_path = AUDIO_OUTPUT / "lines_manifest.json"
    if not manifest_path.exists():
        print("ERROR: No lines manifest. Run narration first.")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        lines = json.load(f)

    # Filter lines for this chapter
    ch_lines = [l for l in lines if l["chapter"] == chapter_num]
    if not ch_lines:
        print(f"No lines found for chapter {chapter_num}")
        return False

    print(f"\nAssembling Chapter {chapter_num} — {len(ch_lines)} lines")

    # Build FFmpeg concat list from audio files
    concat_list = VIDEO_FINAL / f"ch{chapter_num:02d}_audio_list.txt"
    audio_files = []
    for line in ch_lines:
        audio_file = line.get("audio_file")
        if audio_file:
            full_path = AUDIO_OUTPUT / audio_file
            if full_path.exists():
                audio_files.append(full_path)

    if not audio_files:
        print(f"No audio files found for chapter {chapter_num}")
        return False

    # Concatenate all chapter audio into one file
    with open(concat_list, "w", encoding="utf-8") as f:
        for af in audio_files:
            f.write(f"file '{af}'\n")

    ch_audio = VIDEO_FINAL / f"ch{chapter_num:02d}_narration.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy", str(ch_audio)
    ], capture_output=True)

    print(f"  Narration audio: {ch_audio.name}")

    # Check for video clips
    clip_pattern = f"ch{chapter_num:02d}_*"
    clips = sorted(VIDEO_CLIPS.glob(f"{clip_pattern}.*"))
    if clips:
        print(f"  Found {len(clips)} video clips")

        # Concat video clips
        video_list = VIDEO_FINAL / f"ch{chapter_num:02d}_video_list.txt"
        with open(video_list, "w", encoding="utf-8") as f:
            for c in clips:
                f.write(f"file '{c}'\n")

        ch_video_raw = VIDEO_FINAL / f"ch{chapter_num:02d}_video_raw.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(video_list),
            "-c", "copy", str(ch_video_raw)
        ], capture_output=True)

        # Mix background music if available
        music_file = None
        music_candidates = sorted(MUSIC_DIR.glob(f"ch{chapter_num:02d}*"))
        if music_candidates:
            music_file = music_candidates[0]

        # Final assembly: video + narration + music
        final_output = VIDEO_FINAL / f"ch{chapter_num:02d}_final.mp4"
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(ch_video_raw),
            "-i", str(ch_audio),
        ]
        if music_file:
            ffmpeg_cmd.extend(["-i", str(music_file)])
            # Mix narration (loud) + music (soft)
            ffmpeg_cmd.extend([
                "-filter_complex",
                "[1:a]volume=1.0[narr];[2:a]volume=0.15[music];[narr][music]amix=inputs=2:duration=longest[aout]",
                "-map", "0:v", "-map", "[aout]",
            ])
        else:
            ffmpeg_cmd.extend(["-map", "0:v", "-map", "1:a"])

        ffmpeg_cmd.extend([
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final_output)
        ])
        subprocess.run(ffmpeg_cmd, capture_output=True)
        print(f"  FINAL: {final_output.name}")
    else:
        print(f"  No video clips found for chapter {chapter_num}.")
        print(f"  Place clips in: {VIDEO_CLIPS}")
        print(f"  Format: ch{chapter_num:02d}_001.mp4, ch{chapter_num:02d}_002.mp4, etc.")
        print(f"  Audio-only output saved as: {ch_audio.name}")

    return True


def cmd_narration():
    return run_script("generate_narration.py")

def cmd_music():
    return run_script("generate_music.py")

def cmd_assemble():
    if not check_ffmpeg():
        return False
    for ch in range(1, 11):
        assemble_chapter(ch)
    return True


def main():
    print(r"""
    ╔══════════════════════════════════════════╗
    ║   BROKEN COURT — Production Pipeline    ║
    ║   Volume 1: The Rise                    ║
    ╚══════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/pipeline.py narration  — Generate TTS audio")
        print("  python scripts/pipeline.py music      — Generate background music")
        print("  python scripts/pipeline.py assemble   — Assemble final videos")
        print("  python scripts/pipeline.py all        — Run full pipeline")
        print()
        print("For video clips, use ComfyUI at http://localhost:8188")
        print("  ComfyUI start: python F:\\ComfyUI\\main.py --listen --port 8188")
        return

    cmd = sys.argv[1].lower()

    if cmd == "narration":
        cmd_narration()
    elif cmd == "music":
        cmd_music()
    elif cmd == "assemble":
        cmd_assemble()
    elif cmd == "all":
        cmd_narration()
        cmd_music()
        cmd_assemble()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
