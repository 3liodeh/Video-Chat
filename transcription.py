import whisper
import yt_dlp
import re
import json

def convert_cookies_to_netscape(input_file, output_file="youtube_cookies.txt"):
    try:
        # Read the JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            cookies_data = json.load(f)

        # Convert to Netscape format
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies_data:
                domain = cookie["domain"]
                flag = "TRUE" if not cookie.get("hostOnly", True) else "FALSE"
                path = cookie["path"]
                secure = "TRUE" if cookie["secure"] else "FALSE"
                expires = str(int(cookie["expirationDate"])) if "expirationDate" in cookie else "0"
                name = cookie["name"]
                value = cookie["value"]
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        return output_file 
    except Exception as e:
        print(f"❌ An error occurred while converting cookies: {e}")

def sanitize_filename(title):
    """Removes or replaces invalid filename characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid characters with '_'

def download_audio(video_url, output_filename=None):
    try:
        ydl_options = {
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "ffmpeg_location": "/usr/bin/ffmpeg",
            "outtmpl": "%(title)s.%(ext)s",
            "cookies": convert_cookies_to_netscape("/etc/secrets/cookies.json"),
            "http_headers": {
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/91.0.4472.124 Safari/537.36")
            }
        }

        
        # Sanitize the video URL (though typically not necessary for URLs)
        video_url_safe = sanitize_filename(video_url)
        
        # Extract video info
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get("title", "unknown_title")
            safe_title = sanitize_filename(video_title)
            
            if output_filename is None:
                output_filename = safe_title  # Use sanitized title
        
        # Update output template using sanitized video URL and title
        ydl_options["outtmpl"] = f"{video_url_safe}#&$$&#{output_filename}.%(ext)s"
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            ydl.download([video_url])

        return f"{video_url_safe}#&$$&#{output_filename}.mp3"

    except Exception as e:
        return f"Invalid URL {e}"
    
def transcribe_audio(audio_path):
    try:
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_path)
        return result
    except Exception as error:
        return f"An error occurred: {error}"


def split_transcription_into_chunks(extracted_text):
    text_chunks = {}
    segment_texts = []
    chunk_count = 1
    transcription_result = extracted_text

    def extract_segment_info(segment):
        return segment["start"], segment["end"], segment["text"]

    _, _, last_segment_end = extract_segment_info(transcription_result['segments'][-1])
    start_time, _, _ = extract_segment_info(transcription_result['segments'][0])

    for segment in transcription_result['segments']:
        segment_start, segment_end, text = extract_segment_info(segment)
        segment_texts.append(text)

        time_limit = 120 - ((segment_start + segment_end) / chunk_count)

        if time_limit <= 2.5 or last_segment_end == segment_end:
            text_chunks[f"{round(start_time, 3)} - {round(segment_end, 3)}"] = " ".join(segment_texts)
            segment_texts = []
            chunk_count += 1
            start_time = segment_end

    return text_chunks


