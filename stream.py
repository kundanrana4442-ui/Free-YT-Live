import os
import time
import subprocess
import requests
import base64
import threading

YOUTUBE_URL = os.environ.get("YOUTUBE_URL")
REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GITHUB_TOKEN")

def get_live_playlist():
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/playlist.txt"
        headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_b64 = r.json()['content']
            content = base64.b64decode(content_b64).decode('utf-8')
            return[line.strip() for line in content.split('\n') if line.strip()]
    except:
        pass
    return[]

def download_video(link, filename):
    print(f"📥 Downloading: {link}")
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass
    os.system(f"gdown --fuzzy \"{link}\" -O {filename}")
    return os.path.exists(filename) and os.path.getsize(filename) > 1000000

current_index = 0

while True:
    links = get_live_playlist()
    if not links:
        print("Playlist khali hai... wait kar rahe hain")
        time.sleep(10)
        continue
        
    if current_index >= len(links):
        current_index = 0

    current_link = links[current_index]
    
    # JADOO: Agar background me pehle se download ho chuki hai, to direct chalao!
    if os.path.exists("next_video.mp4") and os.path.getsize("next_video.mp4") > 1000000:
        os.rename("next_video.mp4", "current_video.mp4")
    else:
        download_video(current_link, "current_video.mp4")

    # High Quality YouTube Settings
    cmd =[
        "ffmpeg", "-re", "-i", "current_video.mp4",
        "-c:v", "libx264", "-preset", "veryfast", 
        "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", 
        "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k", 
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", YOUTUBE_URL
    ]
    
    print("✅ Streaming shuru (No Gap Mode)...")
    process = subprocess.Popen(cmd)
    
    # BACKGROUND THREAD: Jab tak current stream chal rahi hai, agli video download karke rakh lo
    next_index = (current_index + 1) % len(links)
    next_link = links[next_index]
    
    def bg_task():
        download_video(next_link, "next_video.mp4")
        
    bg_thread = threading.Thread(target=bg_task)
    bg_thread.start()
    
    changed = False
    while process.poll() is None:
        time.sleep(10)
        new_links = get_live_playlist()
        
        # Agar tumne beech me file change kar di!
        if new_links and new_links != links:
            print("🚨 PLAYLIST CHANGE DETECTED! Bina stream kate nayi video chalu kar rahe hain...")
            # Nayi video jaldi se background me download karo
            download_video(new_links[0], "urgent_video.mp4")
            
            # Puraani stream ko cut karo
            process.terminate()
            process.kill()
            
            if os.path.exists("next_video.mp4"):
                try: os.remove("next_video.mp4")
                except: pass
            os.rename("urgent_video.mp4", "next_video.mp4")
            
            changed = True
            current_index = 0
            break
            
    if not changed:
        current_index += 1
        
    if os.path.exists("current_video.mp4"):
        try: os.remove("current_video.mp4")
        except: pass
