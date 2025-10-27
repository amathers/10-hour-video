import os
import sys
import logging
import argparse
import re
import subprocess
from pathlib import Path
from math import ceil
import yt_dlp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_looper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DOWNLOADS_DIR = 'downloads'
DEFAULT_OUTPUT_DIR = 'output'
DEFAULT_DURATION_HOURS = 10
YOUTUBE_URL_PATTERN = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
)

def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube URL.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    return bool(YOUTUBE_URL_PATTERN.match(url.strip()))

def cleanup_file(file_path):
    """
    Safely remove a file if it exists.

    Args:
        file_path (str): Path to the file to remove
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")

def progress_hook(d):
    """
    Callback function to display download progress for yt-dlp.

    Args:
        d (dict): Progress dictionary from yt-dlp
    """
    if d['status'] == 'downloading':
        if 'downloaded_bytes' in d and 'total_bytes' in d:
            percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            print(f"\rDownload progress: {percentage:.1f}%", end='', flush=True)
        elif '_percent_str' in d:
            print(f"\rDownload progress: {d['_percent_str']}", end='', flush=True)
    elif d['status'] == 'finished':
        print()  # New line after progress bar

def download_youtube_video(url, output_path=DEFAULT_DOWNLOADS_DIR, quality='highest'):
    """
    Download a YouTube video with error handling and progress tracking.

    Args:
        url (str): YouTube video URL
        output_path (str): Directory to save the downloaded video
        quality (str): Quality selection - 'highest', 'lowest', or specific resolution like '720p'

    Returns:
        str: Path to the downloaded video file

    Raises:
        ValueError: If URL is invalid
        Exception: If download fails
    """
    # Validate URL
    if not validate_youtube_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    # Create output directory
    try:
        os.makedirs(output_path, exist_ok=True)
        logger.info(f"Output directory ready: {output_path}")
    except Exception as e:
        raise IOError(f"Failed to create output directory: {e}")

    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer mp4, fallback to best
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

        # Adjust format based on quality preference
        if quality == 'highest':
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == 'lowest':
            ydl_opts['format'] = 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst'
        elif quality in ['360p', '480p', '720p', '1080p']:
            # Extract height from quality string
            height = quality.replace('p', '')
            ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'

        logger.info(f"Fetching video information from: {url}")

        # Get video info first
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video title: {info['title']}")
            logger.info(f"Video length: {info['duration']} seconds")

        # Download the video
        logger.info("Starting download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])
            if error_code != 0:
                raise Exception(f"Download failed with error code: {error_code}")

            # Get the downloaded file path
            info = ydl.extract_info(url, download=False)
            download_path = ydl.prepare_filename(info)

        logger.info(f"Download completed: {download_path}")

        if not os.path.exists(download_path):
            raise FileNotFoundError(f"Downloaded file not found at: {download_path}")

        file_size_mb = os.path.getsize(download_path) / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")

        return download_path

    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

def get_video_duration(video_path):
    """
    Get video duration using ffprobe.

    Args:
        video_path (str): Path to the video file

    Returns:
        float: Duration in seconds
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to get video duration: {result.stderr}")

    return float(result.stdout.strip())

def create_extended_video_fast(video_path, output_path=DEFAULT_OUTPUT_DIR,
                               duration_hours=DEFAULT_DURATION_HOURS):
    """
    Create an extended version of a video by looping it using ffmpeg (MUCH faster).

    This method uses ffmpeg's concat demuxer which is 10-100x faster than moviepy
    because it doesn't re-encode every frame.

    Args:
        video_path (str): Path to the input video file
        output_path (str): Directory to save the output video
        duration_hours (float): Desired duration in hours

    Returns:
        str: Path to the output video file

    Raises:
        FileNotFoundError: If input video doesn't exist
        ValueError: If duration is invalid
    """
    # Validate inputs
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if duration_hours <= 0:
        raise ValueError(f"Duration must be positive, got: {duration_hours}")

    # Create output directory
    try:
        os.makedirs(output_path, exist_ok=True)
        logger.info(f"Output directory ready: {output_path}")
    except Exception as e:
        raise IOError(f"Failed to create output directory: {e}")

    try:
        # Get original video duration
        logger.info(f"Getting video duration...")
        original_duration = get_video_duration(video_path)
        target_duration = duration_hours * 3600

        logger.info(f"Original video duration: {original_duration:.2f} seconds")
        logger.info(f"Target duration: {target_duration:.2f} seconds ({duration_hours} hours)")

        # Calculate number of loops needed
        num_loops = ceil(target_duration / original_duration)
        logger.info(f"Number of loops required: {num_loops}")

        # Generate output filename
        base_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(
            output_path,
            f"{duration_hours}h_{name_without_ext}.mp4"
        )

        # Use ffmpeg to loop the video efficiently
        # This is MUCH faster because it uses stream copying instead of re-encoding
        logger.info(f"Creating looped video using ffmpeg (this is much faster!)...")
        logger.info(f"Output file: {output_file}")

        # Method 1: Use concat filter with stream copy (fastest for exact loops)
        # Create a concat file listing the input video multiple times
        concat_file = os.path.join(output_path, 'concat_list.txt')
        try:
            with open(concat_file, 'w') as f:
                for i in range(num_loops):
                    # Use absolute path to avoid issues
                    abs_path = os.path.abspath(video_path)
                    f.write(f"file '{abs_path}'\n")

            logger.info(f"Created concat list with {num_loops} entries")

            # Build ffmpeg command
            # -f concat: use concat demuxer
            # -safe 0: allow absolute paths
            # -i: input concat file
            # -c copy: stream copy (no re-encoding) - this is what makes it fast!
            # -t: trim to exact duration
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-t', str(target_duration),
                '-c', 'copy',  # Stream copy - no re-encoding!
                '-y',  # Overwrite output file
                output_file
            ]

            logger.info("Running ffmpeg (this should be much faster than moviepy)...")

            # Run ffmpeg with progress output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # Show progress
            for line in process.stdout:
                if 'time=' in line:
                    # Extract time from ffmpeg output
                    print(f"\r{line.strip()}", end='', flush=True)

            process.wait()
            print()  # New line

            if process.returncode != 0:
                raise Exception(f"ffmpeg failed with return code {process.returncode}")

            logger.info(f"Video processing completed successfully!")

            if os.path.exists(output_file):
                file_size_gb = os.path.getsize(output_file) / (1024*1024*1024)
                logger.info(f"Output file size: {file_size_gb:.2f} GB")

            return output_file

        finally:
            # Clean up concat file
            if os.path.exists(concat_file):
                os.remove(concat_file)
                logger.debug("Cleaned up concat list file")

    except Exception as e:
        logger.error(f"Error during video processing: {e}")
        raise

def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Download YouTube videos and create extended looped versions (FAST version using ffmpeg)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script_fast.py -u "https://youtube.com/watch?v=..."
  python script_fast.py -u "https://youtube.com/watch?v=..." -d 5 -q 720p

Note: This version uses ffmpeg stream copying which is 10-100x faster than re-encoding!
        """
    )

    parser.add_argument(
        '-u', '--url',
        type=str,
        help='YouTube video URL'
    )

    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=DEFAULT_DURATION_HOURS,
        help=f'Duration in hours (default: {DEFAULT_DURATION_HOURS})'
    )

    parser.add_argument(
        '-q', '--quality',
        type=str,
        default='highest',
        choices=['highest', 'lowest', '360p', '480p', '720p', '1080p'],
        help='Video quality (default: highest)'
    )

    parser.add_argument(
        '--downloads-dir',
        type=str,
        default=DEFAULT_DOWNLOADS_DIR,
        help=f'Directory for downloads (default: {DEFAULT_DOWNLOADS_DIR})'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f'Directory for output (default: {DEFAULT_OUTPUT_DIR})'
    )

    parser.add_argument(
        '--keep-original',
        action='store_true',
        help='Keep the downloaded original video after processing'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()

def main():
    """
    Main function to orchestrate the video download and loop process.
    """
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    downloaded_video_path = None

    try:
        # Get URL from arguments or prompt user
        url = args.url
        if not url:
            url = input("Please enter the YouTube URL: ").strip()

        if not url:
            logger.error("No URL provided")
            sys.exit(1)

        # Download video
        logger.info("=" * 60)
        logger.info("STEP 1: DOWNLOADING VIDEO")
        logger.info("=" * 60)

        downloaded_video_path = download_youtube_video(
            url,
            output_path=args.downloads_dir,
            quality=args.quality
        )

        # Create extended version
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: CREATING EXTENDED VERSION (FAST METHOD)")
        logger.info("=" * 60)

        output_video_path = create_extended_video_fast(
            downloaded_video_path,
            output_path=args.output_dir,
            duration_hours=args.duration
        )

        # Cleanup if requested
        if not args.keep_original:
            logger.info("\nCleaning up original downloaded video...")
            cleanup_file(downloaded_video_path)

        # Final success message
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS!")
        logger.info("=" * 60)
        logger.info(f"Extended video saved to: {output_video_path}")
        logger.info(f"Duration: {args.duration} hours")

    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user")
        if downloaded_video_path and not args.keep_original:
            logger.info("Cleaning up downloaded file...")
            cleanup_file(downloaded_video_path)
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        if downloaded_video_path:
            cleanup_file(downloaded_video_path)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        if downloaded_video_path and not args.keep_original:
            cleanup_file(downloaded_video_path)
        sys.exit(1)

if __name__ == "__main__":
    main()
