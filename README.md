# 10-Hour Video Looper

Download YouTube videos and create extended looped versions of any duration.

## Features

- Download YouTube videos with quality selection
- Create extended versions by looping (default: 10 hours)
- Progress tracking for downloads and video processing
- Comprehensive error handling and logging
- Automatic cleanup of temporary files
- Command-line interface with multiple options
- Support for multiple video codecs

## Installation

1. Ensure you have Python 3.12 or higher installed
2. Install dependencies:

```bash
uv pip install -e .
```

## Usage

### Basic Usage

Interactive mode (prompts for URL):
```bash
python script.py
```

With command-line URL:
```bash
python script.py -u "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

### Advanced Options

Create a 5-hour video with 720p quality:
```bash
python script.py -u "https://youtube.com/watch?v=..." -d 5 -q 720p
```

Use H.265 codec for better compression:
```bash
python script.py -u "https://youtube.com/watch?v=..." --codec libx265
```

Keep the original downloaded video:
```bash
python script.py -u "https://youtube.com/watch?v=..." --keep-original
```

Enable verbose logging:
```bash
python script.py -u "https://youtube.com/watch?v=..." -v
```

### All Available Options

```
-u, --url              YouTube video URL
-d, --duration         Duration in hours (default: 10)
-q, --quality          Video quality: highest, lowest, 360p, 480p, 720p, 1080p
                       (default: highest)
--codec                Video codec: libx264, libx265, mpeg4 (default: libx264)
--downloads-dir        Directory for downloads (default: downloads)
--output-dir           Directory for output (default: output)
--keep-original        Keep the downloaded original video after processing
-v, --verbose          Enable verbose logging
```

## How It Works

1. **Download**: The script downloads the YouTube video using yt-dlp (a robust youtube-dl fork), selecting the best format based on your quality preference

2. **Loop**: The video is looped using moviepy's efficient loop function to reach the target duration

3. **Export**: The final video is encoded and saved to the output directory

4. **Cleanup**: Unless `--keep-original` is specified, the original downloaded video is removed to save space

## Output

- Downloaded videos are saved to `downloads/` directory
- Extended videos are saved to `output/` directory with format: `{duration}h_{original_name}.mp4`
- Log file is created at `video_looper.log`

## Error Handling

The script includes comprehensive error handling for:
- Invalid YouTube URLs
- Network failures during download
- Missing or corrupted video files
- Insufficient disk space
- User interruption (Ctrl+C)

All errors are logged to both console and log file.

## Requirements

- Python >= 3.12
- yt-dlp >= 2024.0.0 (more reliable than pytube)
- moviepy >= 2.0.0

## Notes

- Processing time depends on:
  - Original video length
  - Target duration
  - Selected codec (libx265 is slower but produces smaller files)
  - Your computer's processing power

- Disk space required:
  - Original video size (temporarily, unless --keep-original is used)
  - Final video size (typically very large for 10-hour videos)

## Troubleshooting

**Download fails**:
- Check your internet connection
- Verify the YouTube URL is valid and the video is publicly accessible
- Try a different quality setting
- Update yt-dlp to the latest version: `uv pip install --upgrade yt-dlp`
- yt-dlp is much more reliable than pytube and handles YouTube API changes better

**Out of memory**:
- The script uses moviepy's efficient looping, but very long videos may still require significant RAM
- Try using a lower quality video
- Close other applications to free up memory

**Slow processing**:
- This is normal for long videos
- Consider using libx264 instead of libx265 for faster (but larger) output
- Processing a 10-hour video can take 30+ minutes depending on your hardware
