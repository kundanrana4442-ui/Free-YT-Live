import os
import time
import subprocess
import requests
import base64

YOUTUBE_URL = os.environ.get("YOUTUBE_URL")
REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GITHUB_TOKEN")

# Playlist se link nikalne ka function
def get_current_link():
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/playlist.txt"
        headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_b64 = r.json()['content']
            content = base64.b64decode(content_b64).decode('utf-8')
            links =[line.strip() for line in content.split('\n') if line.strip()]
            if links:
                return links[0] # Sirf pehla link lenge
    except Exception as e:
        print("API Error:", e)
    return None

def download_video(link, filename):
    print(f"\n📥 Naya Link Mila! Downloading: {link}")
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass
    os.system(f"gdown --fuzzy \"{link}\" -O {filename}")
    return os.path.exists(filename) and os.path.getsize(filename) > 1000000

current_link = None
ffmpeg_process = None

while True:
    # 1. GitHub se naya link check karo
    new_link = get_current_link()

    if not new_link:
        print("Playlist khali hai... 10 second wait kar rahe hain")
        time.sleep(10)
        continue

    # 2. Agar link CHANGE hua hai (ya script pehli baar chal rahi hai)
    if new_link != current_link:
        print("🚨 PLAYLIST UPDATE DETECTED! (Ya pehli video hai)")
        
        # Nayi video ko alag file me download karo taaki current stream na ruke
        success = download_video(new_link, "new_video.mp4")
        
        if success:
            # Agar purani stream chal rahi hai, toh usko band karo
            if ffmpeg_process:
                print("🛑 Purani stream rok kar nayi chala rahe hain...")
                ffmpeg_process.terminate()
                ffmpeg_process.kill()
                ffmpeg_process.wait()

            # Nayi video ko main video bana do
            if os.path.exists("current_video.mp4"):
                os.remove("current_video.mp4")
            os.rename("new_video.mp4", "current_video.mp4")
            
            current_link = new_link # Link update kar lo

            # 3. YAHAN HAI JADOO: "-stream_loop -1" matlab bina ruke Infinite loop
            cmd =[
                "ffmpeg", "-stream_loop", "-1", "-re", "-i", "current_video.mp4",
                "-c:v", "libx264", "-preset", "veryfast", 
                "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", 
                "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k", 
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-f", "flv", YOUTUBE_URL
            ]
            print("✅ Stream Shuru (Infinite Loop Mode) - Zero Gap!")
            ffmpeg_process = subprocess.Popen(cmd)
        else:
            print("❌ Download fail! Purani video hi chalne dete hain.")
            time.sleep(10)
            continue

    # 4. Agar link SAME hai, toh bas wait karo aur check karo ki FFmpeg chal raha hai
    else:
        if ffmpeg_process and ffmpeg_process.poll() is not None:
            print("⚠️ Stream band ho gayi thi, automatic wapas chalu kar rahe hain...")
            cmd =[
                "ffmpeg", "-stream_loop", "-1", "-re", "-i", "current_video.mp4",
                "-c:v", "libx264", "-preset", "veryfast", 
                "-r", "30", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", 
                "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k", 
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-f", "flv", YOUTUBE_URL
            ]
            ffmpeg_process = subprocess.Popen(cmd)
        
        # Shanti se 10 second wait karo bina download kiye
        time.sleep(10)
