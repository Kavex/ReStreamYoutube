import os
import json
import subprocess
import shutil  # Used to check for FFmpeg
import tkinter as tk
from tkinter import filedialog, messagebox

# Path to store config file in AppData
CONFIG_DIR = os.path.join(os.getenv("APPDATA"), "ReStreamYoutube")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Default config values
default_config = {
    "YOUTUBE_URL": "rtmp://a.rtmp.youtube.com/live2",
    "STREAM_KEY": ""
}

# Load or create config file
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f)

def load_config():
    """Loads the YouTube RTMP URL and Stream Key from the config file."""
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(yt_url, stream_key):
    """Saves the YouTube RTMP URL and Stream Key to the config file."""
    config = {"YOUTUBE_URL": yt_url, "STREAM_KEY": stream_key}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def check_ffmpeg():
    """Checks if FFmpeg is installed."""
    if shutil.which("ffmpeg") is None:  # Looks for ffmpeg in PATH
        messagebox.showerror("FFmpeg Not Found", "FFmpeg is required but not installed.\n\nPlease install FFmpeg from:\nhttps://ffmpeg.org/download.html")
        root.destroy()  # Closes the program
        exit()

# Load settings
config = load_config()
YOUTUBE_URL = config["YOUTUBE_URL"]
STREAM_KEY = config["STREAM_KEY"]

# Global Variables
VIDEO_FOLDER = ""
ffmpeg_process = None

def select_folder():
    """Opens a dialog to select a folder containing MP4 files."""
    global VIDEO_FOLDER
    folder = filedialog.askdirectory()
    if folder:
        VIDEO_FOLDER = folder
        folder_label.config(text=f"Selected Folder: {VIDEO_FOLDER}", fg="green")

def get_newest_mp4(folder):
    """Returns the most recently modified MP4 file in the folder."""
    if not folder:
        return None
    mp4_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".mp4")]
    return max(mp4_files, key=os.path.getmtime) if mp4_files else None

def start_stream():
    """Finds the newest MP4 file and starts streaming it to YouTube."""
    global ffmpeg_process

    if not VIDEO_FOLDER:
        messagebox.showerror("Error", "Please select a folder first!")
        return
    
    newest_mp4 = get_newest_mp4(VIDEO_FOLDER)

    if not newest_mp4:
        messagebox.showwarning("No MP4 Found", "No MP4 files found in the selected folder.")
        return

    config = load_config()  # Reload config in case it was updated
    youtube_url = config["YOUTUBE_URL"]
    stream_key = config["STREAM_KEY"]

    if not stream_key:
        messagebox.showerror("Error", "Stream Key is missing! Set it in Settings.")
        return

    ffmpeg_command = [
        "ffmpeg",
        "-re",
        "-i", newest_mp4,
        "-s", "1920x1080",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "4500k",
        "-maxrate", "5000k",
        "-bufsize", "10000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "44100",
        "-f", "flv",
        f"{youtube_url}/{stream_key}"
    ]

    print(f"Streaming: {newest_mp4}")
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stream_status_label.config(text=f"Streaming: {os.path.basename(newest_mp4)}", fg="blue")

def stop_stream():
    """Stops the FFmpeg stream."""
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None
        stream_status_label.config(text="Stream Stopped", fg="red")
        messagebox.showinfo("Stream Stopped", "The stream has been stopped.")

def open_settings():
    """Opens the settings window for YouTube RTMP URL and Stream Key."""
    def save_and_close():
        yt_url = yt_url_entry.get().strip()
        stream_key = stream_key_entry.get().strip()

        if not yt_url or not stream_key:
            messagebox.showerror("Error", "Both fields must be filled!")
            return

        save_config(yt_url, stream_key)
        settings_window.destroy()

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x250")
    settings_window.config(bg="#2c2f33")

    tk.Label(settings_window, text="YouTube RTMP URL:", fg="white", bg="#2c2f33", font=("Arial", 12)).pack(pady=5)
    yt_url_entry = tk.Entry(settings_window, width=50)
    yt_url_entry.insert(0, YOUTUBE_URL)
    yt_url_entry.pack(pady=5)

    tk.Label(settings_window, text="YouTube Stream Key:", fg="white", bg="#2c2f33", font=("Arial", 12)).pack(pady=5)
    stream_key_entry = tk.Entry(settings_window, width=50, show="*")  # Masked for security
    stream_key_entry.insert(0, STREAM_KEY)
    stream_key_entry.pack(pady=5)

    save_button = tk.Button(settings_window, text="Save", command=save_and_close, font=("Arial", 12, "bold"), bg="#28a745", fg="white")
    save_button.pack(pady=10)

# Create GUI
root = tk.Tk()
root.title("ReStreamYoutube")
root.geometry("500x350")
root.config(bg="#1e1e1e")
root.wm_attributes('-toolwindow', 'True')  # Makes it a small tool window

# Check if FFmpeg is installed before continuing
check_ffmpeg()

# Menu Bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Settings", command=open_settings)
menu_bar.add_cascade(label="Options", menu=settings_menu)

# UI Elements
title_label = tk.Label(root, text="ReStreamYoutube", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white")
title_label.pack(pady=15)

instruction_label = tk.Label(root, text="Select a folder containing MP4 files to stream", font=("Arial", 10), bg="#1e1e1e", fg="yellow")
instruction_label.pack(pady=5)

folder_button = tk.Button(root, text="Select Folder", command=select_folder, font=("Arial", 12, "bold"), bg="#0078D7", fg="white", width=20)
folder_button.pack(pady=10)

folder_label = tk.Label(root, text="No folder selected", font=("Arial", 10), bg="#1e1e1e", fg="white")
folder_label.pack(pady=5)

start_button = tk.Button(root, text="Start Streaming", command=start_stream, font=("Arial", 12, "bold"), bg="#28a745", fg="white", width=20)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Streaming", command=stop_stream, font=("Arial", 12, "bold"), bg="#dc3545", fg="white", width=20)
stop_button.pack(pady=10)

stream_status_label = tk.Label(root, text="Stream Status: Not Started", font=("Arial", 10), bg="#1e1e1e", fg="gray")
stream_status_label.pack(pady=10)

# Run the GUI
root.mainloop()
