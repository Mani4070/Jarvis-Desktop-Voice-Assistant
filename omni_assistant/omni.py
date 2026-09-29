import pyttsx3
import datetime
import sys
import wikipedia
import webbrowser as wb
import os
import random
import pyautogui
import pyjokes
import urllib.parse

try:
    import speech_recognition as sr
except ModuleNotFoundError as e:
    if "aifc" in str(e):
        try:
            import standard_aifc as aifc
            sys.modules["aifc"] = aifc
            import speech_recognition as sr
        except ModuleNotFoundError:
            print("Python 3.13 detected: SpeechRecognition needs 'standard-aifc'. Run: pip install standard-aifc audioop-lts")
            sr = None
    else:
        raise e

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1)
except Exception as e:
    engine = None
    print(f"Warning: TTS initialization issue: {e}")


def speak(audio) -> None:
    if engine:
        try:
            spoken_audio = str(audio).replace("O.M.N.I.", "Omni Assistant").replace("O.m.n.i.", "Omni Assistant")
            engine.say(spoken_audio)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")


def time() -> None:
    """Tells the current time."""
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    speak("The current time is")
    speak(current_time)
    print("The current time is", current_time)


def date() -> None:
    """Tells the current date."""
    now = datetime.datetime.now()
    speak("The current date is")
    speak(f"{now.day} {now.strftime('%B')} {now.year}")
    print(f"The current date is {now.day}/{now.month}/{now.year}")


def wishme() -> None:
    """Greets the user based on the time of day."""
    speak("Welcome back, sir!")
    print("Welcome back, sir!")

    hour = datetime.datetime.now().hour
    if 4 <= hour < 12:
        speak("Good morning!")
        print("Good morning!")
    elif 12 <= hour < 16:
        speak("Good afternoon!")
        print("Good afternoon!")
    elif 16 <= hour < 24:
        speak("Good evening!")
        print("Good evening!")
    else:
        speak("Good night, see you tomorrow.")

    assistant_name = load_name()
    speak(f"{assistant_name} at your service. Please tell me how may I assist you.")
    print(f"{assistant_name} at your service. Please tell me how may I assist you.")


def screenshot() -> None:
    """Takes a screenshot and saves it."""
    img = pyautogui.screenshot()
    img_path = os.path.expanduser("~\\Pictures\\screenshot.png")
    img.save(img_path)
    speak(f"Screenshot saved as {img_path}.")
    print(f"Screenshot saved as {img_path}.")

def takecommand() -> str:
    """Takes microphone input from the user and returns it as text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1

        try:
            audio = r.listen(source, timeout=5)  # Listen with a timeout
        except sr.WaitTimeoutError:
            speak("Timeout occurred. Please try again.")
            return None

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(query)
        return query.lower()
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        speak("Speech recognition service is unavailable.")
        return None
    except Exception as e:
        speak(f"An error occurred: {e}")
        print(f"Error: {e}")
        return None

def play_music(song_name=None) -> None:
    """Plays music from the user's Music directory."""
    song_dir = os.path.expanduser("~\\Music")
    songs = os.listdir(song_dir)

    if song_name:
        songs = [song for song in songs if song_name.lower() in song.lower()]

    if songs:
        song = random.choice(songs)
        os.startfile(os.path.join(song_dir, song))
        speak(f"Playing {song}.")
        print(f"Playing {song}.")
    else:
        speak("No song found.")
        print("No song found.")

def set_name() -> None:
    """Sets a new name for the assistant."""
    speak("What would you like to name me?")
    name = takecommand()
    if name:
        with open("assistant_name.txt", "w") as file:
            file.write(name)
        speak(f"Alright, I will be called {name} from now on.")
    else:
        speak("Sorry, I couldn't catch that.")

def load_name() -> str:
    """Loads the assistant's name from a file, or uses a default name."""
    try:
        with open("assistant_name.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Omni Assistant"  # Default name


def search_wikipedia(query):
    """Searches Wikipedia and returns a summary."""
    try:
        speak("Searching Wikipedia...")
        result = wikipedia.summary(query, sentences=2)
        speak(result)
        print(result)
    except wikipedia.exceptions.DisambiguationError:
        speak("Multiple results found. Please be more specific.")
    except Exception:
        speak("I couldn't find anything on Wikipedia.")


def clean_query_text(raw_query):
    q = raw_query.strip().lower()
    prefixes = [
        "hello omni", "hey omni", "hi omni", "ok omni", "okay omni",
        "hello jervis", "hey jervis", "hi jervis", "jervis",
        "hello", "hey", "hi", "omni"
    ]
    for p in prefixes:
        if q.startswith(p):
            remainder = q[len(p):].strip()
            if remainder:
                return remainder
            else:
                return ""
    return q


def open_app_or_website(target):
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

    # 1. Check web apps (e.g. "youtube in chrome" -> opens youtube)
    for key, url in web_apps.items():
        if key in target_clean:
            speak(f"Opening {key} in browser.")
            wb.open(url)
            return

    # 2. Check desktop apps (e.g. "chrome app", "open notepad")
    for key, cmd in sys_apps.items():
        if key in target_clean:
            speak(f"Opening {key} application.")
            os.system(cmd)
            return

    # 3. Check direct website URLs (e.g. "open wikipedia.org")
    for word in target_clean.split():
        if any(word.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".in", ".co"]):
            url = word if word.startswith("http") else f"https://{word}"
            speak(f"Opening website {word}.")
            wb.open(url)
            return

    # 4. Fallback search on Google
    if target_clean:
        cleaned_query = target_clean.replace("in chrome", "").replace("on chrome", "").replace("in browser", "").strip()
        speak(f"Searching for {cleaned_query}.")
        wb.open(f"https://www.google.com/search?q={urllib.parse.quote(cleaned_query)}")
    else:
        speak("What would you like me to open, sir?")


if __name__ == "__main__":
    wishme()

    while True:
        raw_query = takecommand()
        if not raw_query:
            continue

        query = clean_query_text(raw_query)

        if not query:
            speak("Hello sir! Omni Assistant online and listening. How may I assist you?")

        elif "how are you" in query:
            speak("I am functioning at maximum capacity, sir. All systems optimal.")

        elif "time" in query:
            time()

        elif "date" in query:
            date()

        elif "open" in query:
            target = query.replace("open", "").strip()
            open_app_or_website(target)

        elif "wikipedia" in query:
            query = query.replace("wikipedia", "").strip()
            search_wikipedia(query)

        elif "play music" in query:
            song_name = query.replace("play music", "").strip()
            play_music(song_name)

        elif "youtube" in query:
            search_term = query.replace("in youtube", "").replace("on youtube", "").replace("youtube", "").replace("play", "").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                speak(f"Searching for {search_term} on YouTube.")
                wb.open(f"https://www.youtube.com/results?search_query={encoded}")
            else:
                speak("Opening YouTube.")
                wb.open("https://www.youtube.com")

        elif "google" in query or "search" in query:
            search_term = query.replace("search on google", "").replace("on google", "").replace("google", "").replace("search", "").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                speak(f"Searching Google for {search_term}")
                wb.open(f"https://www.google.com/search?q={encoded}")
            else:
                speak("Opening Google.")
                wb.open("https://www.google.com")

        elif "change your name" in query:
            set_name()

        elif "screenshot" in query:
            screenshot()
            speak("I've taken screenshot, please check it")

        elif "tell me a joke" in query:
            joke = pyjokes.get_joke()
            speak(joke)
            print(joke)

        elif "shutdown" in query:
            speak("Shutting down the system, goodbye!")
            os.system("shutdown /s /f /t 1")
            break
            
        elif "restart" in query:
            speak("Restarting the system, please wait!")
            os.system("shutdown /r /f /t 1")
            break
            
        elif "offline" in query or "exit" in query:
            speak("Going offline. Have a good day!")
            break
