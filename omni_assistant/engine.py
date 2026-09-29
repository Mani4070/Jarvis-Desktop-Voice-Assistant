import datetime
import wikipedia
import webbrowser as wb
import os
import random
import pyautogui
import pyjokes
import urllib.parse

def load_name() -> str:
    try:
        with open("assistant_name.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Omni Assistant"

def set_name(new_name: str) -> str:
    if new_name:
        with open("assistant_name.txt", "w") as file:
            file.write(new_name)
        return f"Alright, I will be called {new_name} from now on."
    return "Sorry, I couldn't catch that."

def get_time() -> str:
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    return f"The current time is {current_time}"

def get_date() -> str:
    now = datetime.datetime.now()
    return f"The current date is {now.day} {now.strftime('%B')} {now.year}"

def search_wikipedia_summary(query: str) -> str:
    try:
        result = wikipedia.summary(query, sentences=2)
        return result
    except wikipedia.exceptions.DisambiguationError:
        return "Multiple results found. Please be more specific."
    except Exception:
        return "I couldn't find anything on Wikipedia."

def take_screenshot() -> str:
    try:
        img = pyautogui.screenshot()
        img_path = os.path.expanduser("~\\Pictures\\screenshot.png")
        img.save(img_path)
        return f"Screenshot saved as {img_path}."
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def play_local_music(song_name: str = None) -> str:
    song_dir = os.path.expanduser("~\\Music")
    if not os.path.exists(song_dir):
        return "Music directory not found."
        
    songs = os.listdir(song_dir)
    if song_name:
        songs = [song for song in songs if song_name.lower() in song.lower()]

    if songs:
        song = random.choice(songs)
        os.startfile(os.path.join(song_dir, song))
        return f"Playing {song}."
    else:
        return "No song found locally."

def open_app_or_website(target: str) -> str:
    target_clean = target.strip().lower()

    sys_apps = {
        "notepad": "start notepad",
        "calculator": "start calc",
        "calc": "start calc",
        "cmd": "start cmd",
        "terminal": "start cmd",
        "command prompt": "start cmd",
        "explorer": "start explorer",
        "file explorer": "start explorer",
        "my computer": "start explorer",
        "paint": "start mspaint",
        "chrome": "start chrome",
        "task manager": "start taskmgr"
    }

    web_apps = {
        "whatsapp": "https://web.whatsapp.com",
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "chatgpt": "https://chatgpt.com",
        "spotify": "https://open.spotify.com",
        "github": "https://github.com",
        "linkedin": "https://linkedin.com",
        "gmail": "https://mail.google.com",
        "email": "https://mail.google.com",
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "reddit": "https://reddit.com",
        "netflix": "https://netflix.com",
        "amazon": "https://amazon.com",
        "stackoverflow": "https://stackoverflow.com"
    }

    for key, url in web_apps.items():
        if key in target_clean:
            wb.open(url)
            return f"Opening {key} in browser."

    for key, cmd in sys_apps.items():
        if key in target_clean:
            os.system(cmd)
            return f"Opening {key} application."

    for word in target_clean.split():
        if any(word.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".in", ".co"]):
            url = word if word.startswith("http") else f"https://{word}"
            wb.open(url)
            return f"Opening website {word}."

    if target_clean:
        cleaned_query = target_clean.replace("in chrome", "").replace("on chrome", "").replace("in browser", "").strip()
        wb.open(f"https://www.google.com/search?q={urllib.parse.quote(cleaned_query)}")
        return f"Searching for {cleaned_query}."
    
    return "What would you like me to open, sir?"

def process_query(raw_query: str) -> str:
    """Processes a text query and returns a response string."""
    q = raw_query.strip().lower()
    prefixes = [
        "hello omni", "hey omni", "hi omni", "ok omni", "okay omni",
        "hello jervis", "hey jervis", "hi jervis", "jervis",
        "hello", "hey", "hi", "omni"
    ]
    for p in prefixes:
        if q.startswith(p):
            q = q[len(p):].strip()
            break
            
    query = q
    if not query:
        return "Hello sir! Omni Assistant online and listening. How may I assist you?"

    if "how are you" in query:
        return "I am functioning at maximum capacity, sir. All systems optimal."

    if "time" in query:
        return get_time()

    if "date" in query:
        return get_date()

    if "open" in query:
        target = query.replace("open", "").strip()
        return open_app_or_website(target)

    if "wikipedia" in query:
        q_wiki = query.replace("wikipedia", "").strip()
        return search_wikipedia_summary(q_wiki)

    if "play music" in query:
        song_name = query.replace("play music", "").strip()
        return play_local_music(song_name)

    if "youtube" in query:
        search_term = query.replace("in youtube", "").replace("on youtube", "").replace("youtube", "").replace("play", "").strip()
        if search_term:
            encoded = urllib.parse.quote(search_term)
            wb.open(f"https://www.youtube.com/results?search_query={encoded}")
            return f"Searching for {search_term} on YouTube."
        else:
            wb.open("https://www.youtube.com")
            return "Opening YouTube."

    if "google" in query or "search" in query:
        search_term = query.replace("search on google", "").replace("on google", "").replace("google", "").replace("search", "").strip()
        if search_term:
            encoded = urllib.parse.quote(search_term)
            wb.open(f"https://www.google.com/search?q={encoded}")
            return f"Searching Google for {search_term}"
        else:
            wb.open("https://www.google.com")
            return "Opening Google."
            
    if "screenshot" in query:
        return take_screenshot()

    if "tell me a joke" in query or "joke" in query:
        return pyjokes.get_joke()

    if "shutdown" in query:
        os.system("shutdown /s /f /t 1")
        return "Shutting down the system, goodbye!"
        
    if "restart" in query:
        os.system("shutdown /r /f /t 1")
        return "Restarting the system, please wait!"
        
    if "offline" in query or "exit" in query:
        return "Going offline. Have a good day!"
        
    # Fallback Google search
    encoded = urllib.parse.quote(query)
    wb.open(f"https://www.google.com/search?q={encoded}")
    return f"Searching for {query} on Google."
