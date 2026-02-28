import os
import time
import subprocess
import requests
import base64

YOUTUBE_URL = os.environ.get("YOUTUBE_URL")
REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GITHUB_TOKEN")

# Yeh function direct GitHub se live playlist check karega (Bina delay ke)
def get_live_playlist():
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/playlist.txt"
        headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_b64 = r.json()['content']
            content = base64.b64decode(content_b64).decode('utf-8')
            links =[line.strip() for line in content.split('\n') if line.strip()]
            return links
    except Exception as e:
        print("API Error:", e)
    return[]

while True:
    links = get_live_playlist()
    
    if not links:
        print("Playlist khali hai! 10 second baad dobara check karenge...")
        time.sleep(10)
        continue

    current_playlist = links.copy()

    for link in links:
        print(f"\n🚀 Downloading: {link}")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
            
        # Video Download karna
        os.system(f"gdown --fuzzy \"{link}\" -O temp_video.mp4")
        
        if not os.path.exists("temp_video.mp4") or os.path.getsize("temp_video.mp4") < 1000000:
            print("❌ Download fail! Next video par ja rahe hain...")
            continue
        
        print("✅ Streaming shuru ho rahi hai...")
        cmd =[
            "ffmpeg", "-re", "-i", "temp_video.mp4",
            "-c:v", "libx264", "-preset", "veryfast", 
            "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", 
            "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k", 
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-f", "flv", YOUTUBE_URL
        ]
        
        # Popen ka use kiya hai taaki script background me ffmpeg ko chalakar aage ka kaam kar sake
        process = subprocess.Popen(cmd)
        
        changed = False
        # Jab tak video chal rahi hai, har 10 second me list check karo
        while process.poll() is None:
            time.sleep(10)
            new_links = get_live_playlist()
            
            # Agar list badal gayi, toh current video turant band kar do!
            if new_links and new_links != current_playlist:
                print("🚨 PLAYLIST CHANGE DETECTED! Purani video rok kar nayi chala rahe hain...")
                process.terminate()
                process.kill()
                changed = True
                break
                
        if changed:
            break # Pura loop break karo aur shuru se nayi list load karo
            
        print("⏹️ Video poori ho gayi. Next par ja rahe hain...")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
