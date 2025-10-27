# 10-Hour Video Looper

Download YouTube videos and create extended looped versions of any duration - **FAST!**

## Features

- Download YouTube videos with quality selection
- Create extended versions by looping (default: 10 hours)
- **Ultra-fast processing** using ffmpeg stream copying (10-100x faster than re-encoding!)
- Progress tracking for downloads
- Comprehensive error handling and logging
- Automatic cleanup of temporary files
- Command-line interface with multiple options

## Installation

1. Ensure you have Python 3.12 or higher installed
2. **Install ffmpeg** (required for video processing):
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (RHEL/CentOS)
3. Install Python dependencies:

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

Trim to exactly 10 hours (instead of complete loops):
```bash
python script.py -u "https://youtube.com/watch?v=..." -d 10 --exact-duration
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
-d, --duration         Minimum duration in hours (default: 10)
-q, --quality          Video quality: highest, lowest, 360p, 480p, 720p, 1080p
                       (default: highest)
--downloads-dir        Directory for downloads (default: downloads)
--output-dir           Directory for output (default: output)
--keep-original        Keep the downloaded original video after processing
--exact-duration       Trim output to exact duration (default: use complete loops)
-v, --verbose          Enable verbose logging
```

**Note about duration:**
- **By default**, the output uses complete loops and may exceed the target duration
  - Example: A 61-minute video looped for 10 hours → 10 hours 10 minutes (10 complete loops)
- **With --exact-duration**, the output is trimmed to exactly the target duration
  - Example: A 61-minute video looped for 10 hours → exactly 10 hours (last loop trimmed)

## How It Works

1. **Download**: The script downloads the YouTube video using yt-dlp (a robust youtube-dl fork), selecting the best format based on your quality preference

2. **Loop**: The video is looped using ffmpeg's concat demuxer with **stream copying** - this means it doesn't re-encode the video, making it 10-100x faster than traditional methods!
   - By default, uses complete loops (output may slightly exceed target duration)
   - Use `--exact-duration` to trim the last loop to exactly match the target

3. **Export**: The final video uses the same codec/quality as the original (no quality loss, no re-encoding overhead)

4. **Cleanup**: Unless `--keep-original` is specified, the original downloaded video is removed to save space

## Why So Fast?

Traditional video looping tools (like moviepy) re-encode every single frame:
- 10 hours at 30fps = **1,080,000 frames** to encode
- Can take 2-6+ hours depending on CPU

This script uses ffmpeg's stream copy feature:
- Just copies the video/audio data without re-encoding
- Same quality, 10-100x faster
- Takes 1-5 minutes instead of hours!

## Output

- Downloaded videos are saved to `downloads/` directory
- Extended videos are saved to `output/` directory with format: `{actual_duration}h_{original_name}.mp4`
  - Example: `10.17h_Amazing_Video.mp4` (10 hours 10 minutes)
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
- yt-dlp >= 2024.0.0 (for downloading YouTube videos)
- ffmpeg (for fast video processing with stream copying)

## Notes

- **Processing is very fast!** Using stream copying instead of re-encoding:
  - A 10-hour video typically processes in 1-5 minutes
  - Speed depends mainly on disk I/O, not CPU
  - No quality loss since there's no re-encoding

- Disk space required:
  - Original video size (temporarily, unless --keep-original is used)
  - Final video size = Original size × number of loops
  - Example: 50MB source × 200 loops = ~10GB output for 10 hours

## Troubleshooting

**Download fails**:
- Check your internet connection
- Verify the YouTube URL is valid and the video is publicly accessible
- Try a different quality setting
- Update yt-dlp to the latest version: `uv pip install --upgrade yt-dlp`
- yt-dlp is actively maintained and handles YouTube API changes quickly

**ffmpeg not found**:
- Make sure ffmpeg is installed and in your PATH
- Test by running `ffmpeg -version` in your terminal
- On Windows, you may need to add ffmpeg to your system PATH environment variable
- Reinstall ffmpeg following the installation instructions above

**Processing fails or creates corrupted video**:
- Ensure you have enough disk space (output file can be very large)
- Try downloading a different quality if the source video has issues
- Check that ffmpeg is working: `ffmpeg -version`

**Slow processing** (unexpected):
- The script should be very fast (1-5 minutes for 10 hours)
- If it's slow, ffmpeg might be re-encoding instead of stream copying
- Check the ffmpeg output for warnings about incompatible formats
