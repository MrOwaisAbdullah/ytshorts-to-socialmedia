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
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "transcripts" not in data or not data["transcripts"]:
            raise Exception("Transcript not available for this video")
        
        transcript_text = " ".join(
            [line["text"].strip() + "." if not line["text"].strip().endswith('.') else line["text"].strip()
             for line in data["transcripts"]]
        )
        return transcript_text
    
    except requests.RequestException as e:
        raise Exception(f"Error fetching transcript: {e}")
    except KeyError as e:
        raise Exception(f"Unexpected API response format: {e}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")