import os
import time
import subprocess

YOUTUBE_URL = os.environ.get("YOUTUBE_URL")

def get_playlist():
    # Playlist file se links padhna
    try:
        with open('playlist.txt', 'r') as f:
            links =[line.strip() for line in f.readlines() if line.strip()]
        return links
    except:
        return[]

while True:
    links = get_playlist()
    
    if not links:
        print("Playlist khali hai! 30 seconds wait kar rahe hain...")
        time.sleep(30)
        continue

    for link in links:
        print(f"Downloading: {link}")
        # Nayi video download karna
        os.system(f"wget -q -O temp_video.mp4 \"{link}\"")
        
        print("Streaming started...")
        # YouTube ki Strict Guidelines wala FFmpeg (Poor Quality Fix)
        cmd =[
            "ffmpeg", "-re", "-i", "temp_video.mp4",
            "-c:v", "libx264", "-preset", "veryfast", 
            "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", 
            "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k", 
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-f", "flv", YOUTUBE_URL
        ]
        
        subprocess.run(cmd)
        
        print("Video poori ho gayi. Next par ja rahe hain...")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
            
        # Check karna ki live chalte time tumne list update toh nahi ki?
        new_links = get_playlist()
        if new_links != links:
            print("Tumne playlist update ki hai! Nayi list start kar rahe hain...")
            break # Pura loop todkar nayi list shuru karega
