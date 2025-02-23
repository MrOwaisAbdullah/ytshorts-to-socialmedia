import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_youtube_transcript_with_searchapi(video_id):
    api_key = os.environ.get("SEARCHAPI_KEY")
    if not api_key:
        raise ValueError("SEARCHAPI_KEY environment variable not set")
    
    api_url = "https://searchapi.io/api/v1/search"
    params = {
        "api_key": api_key,
        "engine": "youtube_transcripts",
        "video_id": video_id
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "transcripts" not in data or not data["transcripts"]:
            raise ValueError("Transcript not available for this video")
        
        transcript_text = " ".join(
            [line["text"].strip() + "." if not line["text"].strip().endswith('.') else line["text"].strip()
             for line in data["transcripts"]]
        )
        return transcript_text
    
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching transcript: {e}") from e
    except KeyError as e:
        raise ValueError(f"Unexpected API response format: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e

# Function to extract short ID from URL or return ID if provided
def extract_youtube_short_id(input_string):
    # Regular expression to match YouTube Shorts URL and extract ID
    pattern = r'(?:https?://(?:www\.)?youtube\.com/shorts/|https?://youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, input_string)
    if match:
        return match.group(1)  # Return the 11-character video ID
    # If no URL match, assume input is already a video ID
    if len(input_string) == 11 and input_string.isalnum():
        return input_string
    raise ValueError("Invalid YouTube Shorts URL or ID. Please provide a valid URL (e.g., https://youtube.com/shorts/CYTwGx43SzY) or 11-character ID.")
