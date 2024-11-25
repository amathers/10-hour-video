import os
import yt_dlp
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Function to download YouTube video
def download_youtube_video(url, output_path='downloads'):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Define output path
    output_path_template = os.path.join(output_path, '%(title)s.%(ext)s')

    # Set for yt-dlp
    ydl_opts = {
        'format': 'best',  # Download the best quality video+audio
        'outtmpl': output_path_template,  # Save the video with the title as the filename
        'postprocessors': [{  # This section is optional
            'key': 'FFmpegVideoConvertor'
        }],
    }
    
    # Download the video, getting the title and extension information
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    
    # Construct the resulting file path using info_dict to get the title and format
    title = info_dict.get('title', 'video')
    ext = info_dict.get('ext', 'mp4')
    result_path = os.path.join(output_path, f'{title}.{ext}')
    
    # Return the path of the downloaded video file
    return result_path

# Function to create a 10-hour version of the video
def create_10_hour_version(video_path, output_path='output', duration_hours=10):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Load the downloaded video into a VideoFileClip object
    clip = VideoFileClip(video_path)

    # Initialize an empty list to hold the repeated clips
    clips = []

    # Initialize the duration in seconds of the concatenated clips
    total_duration = 0

    # Repeat the video clip until the total duration reaches 10 hours (36000 seconds)
    while total_duration < (duration_hours * 3600):
        clips.append(clip)
        total_duration += clip.duration

    # Concatenate all the video clips into a single video
    final_clip = concatenate_videoclips(clips)

    # Create the output file path for the 10-hour video
    output_file = os.path.join(output_path, f"10_hour_{os.path.basename(video_path)}")

    # Write the final concatenated video to the output file
    final_clip.write_videofile(output_file, codec="libx264")

    # Return the path of the final 10-hour video file
    return output_file

if __name__ == "__main__":
    # Prompt the user to enter the YouTube URL
    youtube_url = input("Please enter the YouTube URL: ")
    
    # Download the YouTube video and get the path of the downloaded file
    print(f"Downloading video from: {youtube_url}")
    downloaded_video_path = download_youtube_video(youtube_url)
    print(downloaded_video_path)
    # Create a 10-hour version of the downloaded video
    print(f"Creating 10-hour video...")
    ten_hour_video_path = create_10_hour_version(downloaded_video_path)

    # Print the path of the final 10-hour video file
    print(f"10-hour video saved to: {ten_hour_video_path}")
