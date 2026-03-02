
import os
import time
import subprocess
import requests
import base64
YOUTUBE_URL = os.environ.get("YOUTUBE_URL")
REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GITHUB_TOKEN")
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
                return links[0]
    except Exception as e:
        print("API Error:", e)
    return None
def download_video(link, filename):
    print(f"\n📥 Naya Link Mila! Downloading: {link}")
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass
        
    # Dropbox aur Direct links ke liye 'wget' sabse best hai
    os.system(f"wget -q -O {filename} \"{link}\"")
    
    return os.path.exists(filename) and os.path.getsize(filename) > 1000000
current_link = None
ffmpeg_process = None
while True:
    new_link = get_current_link()
    if not new_link:
        print("Playlist khali hai... wait kar rahe hain")
        time.sleep(10)
        continue
    if new_link != current_link:
        print("🚨 PLAYLIST UPDATE DETECTED! Nayi video download ho rahi hai...")
        
        success = download_video(new_link, "new_video.mp4")
        
        if success:
            if ffmpeg_process:
                print("🛑 Purani stream rok kar nayi chala rahe hain...")
                ffmpeg_process.terminate()
                ffmpeg_process.kill()
                ffmpeg_process.wait()
            if os.path.exists("current_video.mp4"):
                os.remove("current_video.mp4")
            os.rename("new_video.mp4", "current_video.mp4")
            
            current_link = new_link 
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
            print("❌ Download fail! Link check karo (Dropbox me dl=1 hona chahiye).")
            time.sleep(10)
    else:
        if ffmpeg_process and ffmpeg_process.poll() is not None:
            print("⚠️ Stream band hui, restart kar rahe hain...")
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
        
        time.sleep(10)
