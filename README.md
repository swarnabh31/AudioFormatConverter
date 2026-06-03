# Audio Format Converter

Desktop GUI app that batch-converts audio files (WAV, FLAC, M4A, OGG) to compressed MP3 using FFmpeg under the hood — fully offline, zero cloud dependency.

## Features

- **Drag & drop** or browse to import audio files
- **Batch processing** — convert all queued files with one click
- **MP3 quality presets**: 64 / 128 / 192 / 256 / 320 kbps
- **Sample rate**: 44.1 kHz or 48 kHz
- **Mono downmix** option for smaller file sizes
- **Real-time progress bars** — per-file and overall
- **FFmpeg validation** at startup with helpful installation guidance
- **Fully offline** — no API calls, no cloud dependency

## Requirements

| Requirement | Detail |
|-------------|--------|
| Python | 3.10+ |
| FFmpeg | Installed on PATH (detects automatically) |
| OS | Windows / macOS / Linux |

Install dependencies:

```bash
pip install flet pydub
```

## Usage

```bash
cd C:\Users\swarnabh\Desktop\Github_Projects\format_converter
python main.py
```

Then:
1. **Drag & drop** audio files or click the browse button
2. **Select conversion settings** (bitrate, sample rate, channels)
3. Click **"Convert All"**
4. Wait for progress bars to complete
5. Click **"Open Output Folder"** to find your MP3s

## Project Structure

```
format_converter/
├── main.py                    # App entry point — Flet window, FFmpeg validation
├── requirements.txt           # flet, pydub
├── config/
│   └── settings.json          # Default bitrate, sample rate, channel mode
├── core/
│   ├── __init__.py
│   ├── conversion_engine.py   # Core FFmpeg encoder (convert_file method)
│   ├── conversion_models.py   # Pydantic: ConversionSettings, ConversionJob, JobStatus
│   └── conversion_queue.py    # Async job queue with semaphore-based concurrency
├── gui/
│   ├── __init__.py
│   ├── theme.py               # Dark theme constants (Flet)
│   ├── drag_drop_zone.py      # Drag-and-drop file zone component
│   ├── file_table.py          # Progress table per-file status display
│   ├── batch_controls.py      # Convert All / Clear Queue / Open Output buttons
│   ├── progress_bar.py        # Overall + per-file progress bars
│   └── settings_panel.py      # Bitrate, sample rate, channel mode selectors
├── utils/
│   ├── __init__.py
│   ├── ffmpeg_detector.py     # PATH detection + version check (>= 4.0)
│   ├── file_helpers.py        # File validation (magic bytes), human-readable sizes
│   ├── format_mapper.py       # Supported formats, output extension mapping
│   ├── path_sanitizer.py      # Input/output path safety helpers
│   └── config_loader.py       # JSON settings loader with fallback defaults
├── tests/
│   ├── __init__.py
│   ├── test_conversion_models.py
│   ├── test_file_helpers.py
│   ├── test_format_mapper.py
│   └── test_path_sanitizer.py
└── README.md
```

## Architecture Decisions

### Why FFmpeg via pydub?
- pydub is a thin, well-maintained wrapper around FFmpeg's libavcodec
- Avoids writing raw subprocess calls manually
- Cross-platform: uses native FFmpeg on all systems

### Why Flet?
- Single codebase for Windows / macOS / Linux desktop apps
- Native-looking widgets without platform-specific UI toolkits
- Async support (`page.run_task`) keeps GUI responsive during batch conversion

### Bitrate stored in kbps (not bps)
Configuration uses kbps values (64, 128, 192, 256, 320) for human readability. Internally converted to bits per second when building the FFmpeg command (`-b:a {bitrate}k`).

## Known Limitations

- **FFmpeg required** on PATH — app validates at startup and shows clear install instructions if missing
- **Mono downmix** always downsamples stereo to 1 channel (can't restore it)
- **Batch queue** processes sequentially via semaphore(1) — no parallel conversion. Can be increased for speed but may impact performance

## License

MIT
