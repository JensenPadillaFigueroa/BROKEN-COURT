# Broken Court — Production Pipeline

## Overview
Full local pipeline to produce animated motion-comic episodes from the manga, using your RTX 4070.

## Components Installed

| Tool | Location | Purpose |
|---|---|---|
| **ComfyUI** | `F:\ComfyUI` | Video generation (AnimateDiff + ControlNet) |
| **AnimateDiff v3** | `F:\ComfyUI\models\animatediff_models\` | Motion model for SD 1.5 |
| **SD 1.5 Checkpoint** | `F:\ComfyUI\models\checkpoints\` | Base image/video model |
| **Piper TTS** | pip package | High-quality local narration |
| **Piper Voice** | `F:\BROKEN-COURT\audio\voices\` | en_US-lessac-medium |
| **MusicGen** | via transformers | Background music generation |

## Quick Start

### 1. Generate Narration Audio
```powershell
python F:\BROKEN-COURT\scripts\pipeline.py narration
```
Generates `.wav` files for every dialogue line using Piper TTS with per-character voice settings.

### 2. Generate Background Music
```powershell
python F:\BROKEN-COURT\scripts\pipeline.py music
```
Generates scene-specific background music tracks using MusicGen-small. First run downloads the model (~2GB).

### 3. Generate Video Clips (ComfyUI)
```powershell
# Start ComfyUI
python F:\ComfyUI\main.py --listen --port 8188
```
Open **http://localhost:8188** in your browser. Load your manga images and use the AnimateDiff workflow to generate 3-5 second animated clips per panel.

Save clips to: `F:\BROKEN-COURT\video\clips\` with naming format:
```
ch01_001.mp4
ch01_002.mp4
ch02_001.mp4
...
```

### 4. Assemble Final Videos
```powershell
python F:\BROKEN-COURT\scripts\pipeline.py assemble
```
Combines video clips + narration + music into final chapter videos. Requires FFmpeg:
```powershell
winget install Gyan.FFmpeg
```

### Run Everything
```powershell
python F:\BROKEN-COURT\scripts\pipeline.py all
```

## Folder Structure
```
F:\BROKEN-COURT\
├── audio\
│   ├── voices\          ← Piper TTS voice models
│   ├── output\          ← Generated narration .wav files
│   ├── music\           ← Generated background music
│   └── sfx\             ← Sound effects (future)
├── video\
│   ├── clips\           ← AnimateDiff output clips (from ComfyUI)
│   └── final\           ← Assembled chapter videos
├── scripts\
│   ├── pipeline.py      ← Master pipeline orchestrator
│   ├── generate_narration.py  ← Piper TTS narration
│   └── generate_music.py      ← MusicGen background music
└── images\              ← Source manga images
```

## ComfyUI AnimateDiff Workflow
1. Open ComfyUI at http://localhost:8188
2. Load an image from `F:\BROKEN-COURT\images\`
3. Use **Load Image → AnimateDiff → Video Combine** workflow
4. Settings: 16 frames, 8 fps = 2 second clip
5. Motion model: `v3_sd15_mm.ckpt`
6. Checkpoint: `v1-5-pruned-emaonly.safetensors`

## Estimated Times (RTX 4070, 12GB VRAM)
- Narration: ~5-10 minutes for all chapters
- Music: ~30-45 minutes for all tracks
- Video clips: ~8-10 min per clip × ~50 clips = ~6-8 hours (run overnight)
- Assembly: ~2 minutes
