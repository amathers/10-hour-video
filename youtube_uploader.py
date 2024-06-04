from google.auth.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# Define the scopes for the OAuth 2.0 credentials
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Path to the video file to upload
VIDEO_FILE_PATH = "sample.mkv"

def authenticate():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    # Created automatically when the authorization flow completes for the first time
    # if os.path.exists('token.json'):
    #     creds = Credentials.from_authorized_user_file('token.json')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_video(video_path, title, description, category_id):
    youtube = build('youtube', 'v3', credentials=authenticate())

    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public'
        }
    }

    media_file = MediaFileUpload(video_path)

    response = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media_file
    ).execute()

    print(f"Video uploaded successfully! Video ID: {response['id']}")

if __name__ == "__main__":
    upload_video(VIDEO_FILE_PATH, 
                 "Test Video", 
                 "This is a test video uploaded using the YouTube Data API", 
                 "22")  # Use the correct category ID for your video
