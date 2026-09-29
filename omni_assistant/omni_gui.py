import sys
import os
import time
import math
import datetime
import random
import pyautogui
import pyjokes
import wikipedia
import webbrowser as wb
import pyttsx3
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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QPolygonF

def load_assistant_name():
    try:
        with open("assistant_name.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Omni Assistant"


def speak_text(text):
    try:
        spoken_text = text.replace("O.M.N.I.", "Omni Assistant").replace("O.m.n.i.", "Omni Assistant")
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        local_engine = pyttsx3.init()
        voices = local_engine.getProperty('voices')
        if len(voices) > 1:
            local_engine.setProperty('voice', voices[1].id)
        local_engine.setProperty('rate', 150)
        local_engine.setProperty('volume', 1.0)
        local_engine.say(spoken_text)
        local_engine.runAndWait()
        local_engine.stop()
    except Exception as e:
        print(f"TTS Error: {e}")


# ==========================================
# ANIMATED ARC REACTOR CUSTOM WIDGET
# ==========================================
class ArcReactorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        # State colors: cyan (idle), gold (listening), purple (processing), green (speaking)
        self.state_color = QColor(0, 243, 255) # Default Cyan
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)

    def set_state(self, state_name):
        if state_name == "listening":
            self.state_color = QColor(255, 170, 0) # Gold Amber
        elif state_name == "processing":
            self.state_color = QColor(208, 0, 255) # Cyber Purple
        elif state_name == "speaking":
            self.state_color = QColor(0, 255, 128) # Arc Green
        else:
            self.state_color = QColor(0, 243, 255) # Electric Cyan
        self.update()

    def update_animation(self):
        self.angle = (self.angle + 2) % 360
        self.pulse += 0.05 * self.pulse_dir
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2)
        radius = min(width, height) / 2 - 15

        c = self.state_color

        # 1. Outer Tech Ring
        pen = QPen(QColor(c.red(), c.green(), c.blue(), 100), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(center, radius, radius)

        # 2. Rotating HUD Marks
        painter.save()
        painter.translate(center)
        painter.rotate(self.angle)

        pen = QPen(QColor(c.red(), c.green(), c.blue(), 200), 2)
        painter.setPen(pen)
        for i in range(12):
            painter.rotate(30)
            painter.drawLine(int(radius - 12), 0, int(radius - 2), 0)

        # Inner Triangles / Arc Nodes
        pen = QPen(QColor(c.red(), c.green(), c.blue(), 180), 1.5)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 40)))
        for i in range(3):
            painter.rotate(120)
            poly = QPolygonF([
                QPointF(radius * 0.4, -8),
                QPointF(radius * 0.75, 0),
                QPointF(radius * 0.4, 8)
            ])
            painter.drawPolygon(poly)

        painter.restore()

        # 3. Middle Glow Ring
        pulse_radius = radius * 0.5 + (self.pulse * 6)
        pen = QPen(QColor(c.red(), c.green(), c.blue(), 220), 4)
        painter.setPen(pen)
        painter.drawEllipse(center, pulse_radius, pulse_radius)

        # 4. Central Glowing Core
        grad = QRadialGradient(center, radius * 0.35)
        grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        grad.setColorAt(0.4, QColor(c.red(), c.green(), c.blue(), 220))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(center, radius * 0.35, radius * 0.35)


# ==========================================
# WORKER THREAD FOR VOICE & COMMAND EXECUTION
# ==========================================
class Omni AssistantWorkerThread(QThread):
    sig_log = pyqtSignal(str, str)     # (message, category)
    sig_status = pyqtSignal(str, str)  # (status_text, state_color_key)

    def __init__(self, mode="listen", command_text=None):
        super().__init__()
        self.mode = mode
        self.command_text = command_text
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        if self.mode == "welcome":
            self.do_welcome()
        elif self.mode == "listen":
            query = self.take_command(silent_timeout=False)
            if query:
                self.process_query(query)
            else:
                self.sig_status.emit("SYSTEM STANDBY", "idle")
        elif self.mode == "continuous":
            self.sig_log.emit("Continuous voice listening mode active. Speak any command anytime...", "SYSTEM")
            while self.is_running:
                self.sig_status.emit("LISTENING VOICE...", "listening")
                query = self.take_command(silent_timeout=True)
                if not self.is_running:
                    break
                if query:
                    self.process_query(query)
                    q_lower = query.lower()
                    if "offline" in q_lower or "exit" in q_lower or "shutdown" in q_lower:
                        break
                time.sleep(0.3)
            self.sig_status.emit("SYSTEM STANDBY", "idle")
        elif self.mode == "text":
            if self.command_text:
                self.process_query(self.command_text.lower())
            else:
                self.sig_status.emit("SYSTEM STANDBY", "idle")

    def speak(self, text):
        self.sig_status.emit("JARVIS SPEAKING...", "speaking")
        self.sig_log.emit(text, "JARVIS")
        speak_text(text)

    def do_welcome(self):
        self.sig_log.emit("Initializing O.M.N.I. Core Systems...", "SYSTEM")
        hour = datetime.datetime.now().hour
        if 4 <= hour < 12:
            greeting = "Good morning, sir!"
        elif 12 <= hour < 16:
            greeting = "Good afternoon, sir!"
        elif 16 <= hour < 24:
            greeting = "Good evening, sir!"
        else:
            greeting = "Good night, sir."

        assistant_name = load_assistant_name()
        welcome_msg = f"{greeting} {assistant_name} online and ready."
        self.speak(welcome_msg)
        self.sig_status.emit("SYSTEM STANDBY", "idle")

    def take_command(self, silent_timeout=False):
        if sr is None:
            self.speak("Voice recognition requires standard-aifc on Python 3.13. Please run pip install standard-aifc audioop-lts")
            return None
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                if not silent_timeout:
                    self.sig_status.emit("LISTENING VOICE...", "listening")
                    self.sig_log.emit("Listening for voice input...", "SYSTEM")
                r.pause_threshold = 1
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    if not silent_timeout:
                        self.speak("Voice input timeout. Standing by.")
                    return None
        except (AttributeError, OSError, Exception) as mic_err:
            if not silent_timeout:
                self.sig_log.emit(f"Microphone error: {mic_err}. Ensure PyAudio is installed and mic is connected.", "ERROR")
                self.speak("Microphone initialization error. Please check PyAudio or type your command.")
            return None

        try:
            self.sig_status.emit("ANALYZING VOICE...", "processing")
            if not silent_timeout:
                self.sig_log.emit("Recognizing speech...", "SYSTEM")
            query = r.recognize_google(audio, language="en-in").lower()
            self.sig_log.emit(query, "USER")
            return query
        except sr.UnknownValueError:
            if not silent_timeout:
                self.speak("Audio not understood. Please repeat.")
            return None
        except sr.RequestError:
            if not silent_timeout:
                self.speak("Speech recognition network service unavailable.")
            return None
        except Exception as e:
            if not silent_timeout:
                self.sig_log.emit(f"Mic error: {e}", "ERROR")
            return None

    def clean_query_text(self, raw_query):
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

    def open_app_or_website(self, target):
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
                self.speak(f"Opening {key} in browser.")
                wb.open(url)
                return

        # 2. Check desktop apps (e.g. "chrome app", "open notepad")
        for key, cmd in sys_apps.items():
            if key in target_clean:
                self.speak(f"Opening {key} application.")
                os.system(cmd)
                return

        # 3. Check direct website URLs (e.g. "open wikipedia.org")
        for word in target_clean.split():
            if any(word.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".in", ".co"]):
                url = word if word.startswith("http") else f"https://{word}"
                self.speak(f"Opening website {word}.")
                wb.open(url)
                return

        # 4. Fallback search on Google
        if target_clean:
            cleaned_query = target_clean.replace("in chrome", "").replace("on chrome", "").replace("in browser", "").strip()
            self.speak(f"Searching for {cleaned_query}.")
            wb.open(f"https://www.google.com/search?q={urllib.parse.quote(cleaned_query)}")
        else:
            self.speak("What would you like me to open, sir?")

    def process_query(self, raw_query):
        self.sig_status.emit("PROCESSING QUERY...", "processing")
        query = self.clean_query_text(raw_query)

        if not query:
            self.speak("Hello sir! Omni Assistant online and listening. How may I assist you?")

        elif "how are you" in query:
            self.speak("I am functioning at maximum capacity, sir. All systems optimal.")

        elif "time" in query:
            curr_time = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.speak(f"The current time is {curr_time}")

        elif "date" in query:
            now = datetime.datetime.now()
            self.speak(f"Today is {now.day} {now.strftime('%B')} {now.year}")

        elif "open" in query:
            target = query.replace("open", "").strip()
            self.open_app_or_website(target)

        elif "wikipedia" in query:
            clean_query = query.replace("wikipedia", "").strip()
            if clean_query:
                self.sig_log.emit(f"Searching Wikipedia for: {clean_query}", "SYSTEM")
                try:
                    res = wikipedia.summary(clean_query, sentences=2)
                    self.speak(res)
                except wikipedia.exceptions.DisambiguationError:
                    self.speak("Multiple results found. Please be more specific.")
                except Exception:
                    self.speak("No matching results found on Wikipedia.")
            else:
                self.speak("What topic would you like me to search on Wikipedia?")

        elif "youtube" in query:
            search_term = query.replace("in youtube", "").replace("on youtube", "").replace("youtube", "").replace("play", "").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                self.speak(f"Searching for {search_term} on YouTube.")
                wb.open(f"https://www.youtube.com/results?search_query={encoded}")
            else:
                self.speak("Opening YouTube.")
                wb.open("https://www.youtube.com")

        elif "play music" in query or ("music" in query and "youtube" not in query):
            song_name = query.replace("play music", "").replace("music", "").strip()
            song_dir = os.path.expanduser("~\\Music")
            played_local = False
            if os.path.exists(song_dir):
                songs = os.listdir(song_dir)
                if song_name:
                    songs = [s for s in songs if song_name.lower() in s.lower()]
                if songs:
                    choice = random.choice(songs)
                    os.startfile(os.path.join(song_dir, choice))
                    self.speak(f"Playing {choice}")
                    played_local = True

            if not played_local:
                target = song_name if song_name else query.replace("play", "").replace("music", "").strip()
                if target:
                    encoded = urllib.parse.quote(target)
                    self.speak(f"Searching for {target} on YouTube.")
                    wb.open(f"https://www.youtube.com/results?search_query={encoded}")
                else:
                    self.speak("No local audio track found and no search term provided.")

        elif "google" in query or "search" in query:
            search_term = query.replace("search on google", "").replace("on google", "").replace("google", "").replace("search", "").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                self.speak(f"Searching Google for {search_term}")
                wb.open(f"https://www.google.com/search?q={encoded}")
            else:
                self.speak("Opening Google.")
                wb.open("https://www.google.com")

        elif "screenshot" in query:
            img = pyautogui.screenshot()
            img_path = os.path.expanduser("~\\Pictures\\screenshot.png")
            img.save(img_path)
            self.speak(f"Screenshot successfully saved to Pictures.")

        elif "joke" in query or "tell me a joke" in query:
            joke = pyjokes.get_joke()
            self.speak(joke)

        elif "offline" in query or "exit" in query or "shutdown" in query:
            self.speak("Systems going offline. Goodbye, sir.")

        else:
            encoded = urllib.parse.quote(query)
            self.speak(f"Searching for {query} on Google.")
            wb.open(f"https://www.google.com/search?q={encoded}")

        self.sig_status.emit("SYSTEM STANDBY", "idle")


# ==========================================
# MAIN WINDOW - IRON MAN HUD THEME
# ==========================================
class Omni AssistantHUDWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("O.M.N.I. - STARK INDUSTRIES HUD OPERATING SYSTEM")
        self.resize(1000, 680)
        self.setMinimumSize(850, 580)
        self.worker = None

        self.init_ui()
        self.apply_hud_stylesheet()

        # Clock Timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        # Trigger initial welcome
        QTimer.singleShot(500, self.run_welcome)

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ----------------------------------------------------
        # TOP HEADER: STARK LOGO & TELEMETRY
        # ----------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("STARK INDUSTRIES  //  MARK VII A.I.")
        title_label.setObjectName("HeaderTitle")

        self.status_badge = QLabel("[ SYS STATUS: ONLINE ]")
        self.status_badge.setObjectName("StatusBadge")

        self.clock_label = QLabel("00:00:00 AM")
        self.clock_label.setObjectName("ClockLabel")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.clock_label)

        main_layout.addWidget(header_frame)

        # ----------------------------------------------------
        # MIDDLE SECTION: ARC REACTOR + TERMINAL LOG
        # ----------------------------------------------------
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(15)

        # Left Column: Arc Reactor HUD Box
        left_box = QFrame()
        left_box.setObjectName("HudBox")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setAlignment(Qt.AlignCenter)

        hud_title = QLabel("CORE ARC REACTOR")
        hud_title.setObjectName("SectionTitle")
        hud_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(hud_title)

        # Arc Reactor Widget
        self.arc_reactor = ArcReactorWidget()
        left_layout.addWidget(self.arc_reactor, alignment=Qt.AlignCenter)

        # Voice Trigger Buttons
        self.btn_auto_listen = QPushButton("⚡ CONTINUOUS VOICE MODE: OFF")
        self.btn_auto_listen.setObjectName("AutoListenButton")
        self.btn_auto_listen.clicked.connect(self.toggle_auto_wake_word)
        left_layout.addWidget(self.btn_auto_listen)

        self.btn_listen = QPushButton("🎙 SINGLE VOICE COMMAND")
        self.btn_listen.setObjectName("ListenButton")
        self.btn_listen.clicked.connect(self.start_listening)
        left_layout.addWidget(self.btn_listen)

        mid_layout.addWidget(left_box, 1)

        # Right Column: Console / Holographic Terminal Log
        right_box = QFrame()
        right_box.setObjectName("HudBox")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(15, 15, 15, 15)

        console_title = QLabel("HOLOGRAPHIC DIAGNOSTIC CONSOLE")
        console_title.setObjectName("SectionTitle")
        right_layout.addWidget(console_title)

        self.console_output = QTextEdit()
        self.console_output.setObjectName("ConsoleOutput")
        self.console_output.setReadOnly(True)
        right_layout.addWidget(self.console_output)

        mid_layout.addWidget(right_box, 2)

        main_layout.addLayout(mid_layout, 1)

        # ----------------------------------------------------
        # QUICK ACTION SHORTCUT BUTTONS
        # ----------------------------------------------------
        quick_frame = QFrame()
        quick_frame.setObjectName("QuickFrame")
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(10, 8, 10, 8)
        quick_layout.setSpacing(10)

        actions = [
            ("Time", "time"),
            ("Date", "date"),
            ("Wikipedia", "wikipedia"),
            ("Joke", "tell me a joke"),
            ("Music", "play music"),
            ("Screenshot", "screenshot"),
            ("YouTube", "open youtube"),
            ("Google", "open google")
        ]

        for label_str, cmd_str in actions:
            btn = QPushButton(f"[ {label_str} ]")
            btn.setObjectName("QuickButton")
            btn.clicked.connect(lambda checked, c=cmd_str: self.execute_quick_command(c))
            quick_layout.addWidget(btn)

        main_layout.addWidget(quick_frame)

        # ----------------------------------------------------
        # BOTTOM COMMAND LINE INPUT
        # ----------------------------------------------------
        input_frame = QFrame()
        input_frame.setObjectName("InputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 8, 10, 8)

        input_prefix = QLabel("COMMAND >")
        input_prefix.setObjectName("InputPrefix")

        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("CmdInput")
        self.cmd_input.setPlaceholderText("Enter manual command or speak via microphone...")
        self.cmd_input.returnPressed.connect(self.send_text_command)

        self.btn_send = QPushButton("TRANSMIT")
        self.btn_send.setObjectName("SendButton")
        self.btn_send.clicked.connect(self.send_text_command)

        input_layout.addWidget(input_prefix)
        input_layout.addWidget(self.cmd_input)
        input_layout.addWidget(self.btn_send)

        main_layout.addWidget(input_frame)

    def apply_hud_stylesheet(self):
        style = """
        QMainWindow {
            background-color: #040814;
        }

        #HeaderFrame {
            background-color: rgba(6, 16, 36, 0.85);
            border: 1px solid #00f3ff;
            border-radius: 6px;
        }

        #HeaderTitle {
            color: #00f3ff;
            font-family: 'Consolas', 'Segoe UI', sans-serif;
            font-size: 15px;
            font-weight: bold;
            letter-spacing: 2px;
        }

        #StatusBadge {
            color: #ffaa00;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
        }

        #ClockLabel {
            color: #00f3ff;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            font-weight: bold;
        }

        #HudBox {
            background-color: rgba(6, 16, 36, 0.65);
            border: 1px solid rgba(0, 243, 255, 0.4);
            border-radius: 8px;
        }

        #SectionTitle {
            color: #00f3ff;
            font-family: 'Consolas', 'Segoe UI', sans-serif;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1.5px;
        }

        #ConsoleOutput {
            background-color: #02050e;
            border: 1px solid rgba(0, 243, 255, 0.3);
            border-radius: 4px;
            color: #00f3ff;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            padding: 10px;
        }

        #AutoListenButton {
            background-color: rgba(0, 243, 255, 0.12);
            border: 1.5px solid #00f3ff;
            border-radius: 6px;
            color: #00f3ff;
            font-family: 'Consolas', sans-serif;
            font-size: 12px;
            font-weight: bold;
            padding: 8px;
            margin-bottom: 4px;
        }
        #AutoListenButton:hover {
            background-color: rgba(0, 243, 255, 0.3);
            color: #ffffff;
        }

        #ListenButton {
            background-color: rgba(0, 243, 255, 0.12);
            border: 1.5px solid #00f3ff;
            border-radius: 6px;
            color: #00f3ff;
            font-family: 'Consolas', sans-serif;
            font-size: 13px;
            font-weight: bold;
            padding: 10px;
        }
        #ListenButton:hover {
            background-color: rgba(0, 243, 255, 0.3);
            color: #ffffff;
        }
        #ListenButton:pressed {
            background-color: rgba(255, 170, 0, 0.4);
            border-color: #ffaa00;
        }

        #QuickFrame {
            background-color: rgba(6, 16, 36, 0.6);
            border: 1px solid rgba(0, 243, 255, 0.3);
            border-radius: 6px;
        }

        #QuickButton {
            background-color: transparent;
            border: 1px solid rgba(0, 243, 255, 0.4);
            border-radius: 4px;
            color: #00f3ff;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            padding: 6px 12px;
        }
        #QuickButton:hover {
            background-color: rgba(0, 243, 255, 0.25);
            color: #ffffff;
            border-color: #00f3ff;
        }

        #InputFrame {
            background-color: rgba(6, 16, 36, 0.85);
            border: 1px solid #00f3ff;
            border-radius: 6px;
        }

        #InputPrefix {
            color: #ffaa00;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
        }

        #CmdInput {
            background-color: transparent;
            border: none;
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            padding: 6px;
        }

        #SendButton {
            background-color: #00f3ff;
            border: none;
            border-radius: 4px;
            color: #040814;
            font-family: 'Consolas', sans-serif;
            font-size: 12px;
            font-weight: bold;
            padding: 6px 16px;
        }
        #SendButton:hover {
            background-color: #ffffff;
        }
        """
        self.setStyleSheet(style)

    def update_clock(self):
        now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.setText(now_str)

    def append_log(self, text, category="SYSTEM"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if category == "USER":
            color = "#ffaa00" # Gold
            prefix = "[USER]"
        elif category == "JARVIS":
            color = "#00ff88" # Green
            prefix = "[JARVIS]"
        elif category == "ERROR":
            color = "#ff3355" # Red
            prefix = "[ERROR]"
        else:
            color = "#00f3ff" # Cyan
            prefix = "[SYS]"

        formatted_msg = f'<span style="color: #666666;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{prefix}</span> {text}'
        self.console_output.append(formatted_msg)

    def update_status(self, status_text, state_key):
        self.status_badge.setText(f"[ {status_text} ]")
        self.arc_reactor.set_state(state_key)

    def start_worker(self, mode="listen", command_text=None):
        if self.worker and self.worker.isRunning():
            self.append_log("Previous task still running. Please wait...", "SYSTEM")
            return

        self.worker = Omni AssistantWorkerThread(mode=mode, command_text=command_text)
        self.worker.sig_log.connect(self.append_log)
        self.worker.sig_status.connect(self.update_status)
        self.worker.start()

    def run_welcome(self):
        self.start_worker(mode="welcome")

    def start_listening(self):
        self.start_worker(mode="listen")

    def send_text_command(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            self.append_log(text, "USER")
            self.start_worker(mode="text", command_text=text)

    def toggle_auto_wake_word(self):
        if self.worker and self.worker.isRunning() and getattr(self.worker, 'mode', '') == 'continuous':
            self.worker.stop()
            self.btn_auto_listen.setText("⚡ CONTINUOUS VOICE MODE: OFF")
            self.btn_auto_listen.setStyleSheet("""
                background-color: rgba(0, 243, 255, 0.12);
                border: 1.5px solid #00f3ff;
                border-radius: 6px;
                color: #00f3ff;
                font-family: 'Consolas', sans-serif;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
            """)
            self.append_log("Continuous voice mode deactivated.", "SYSTEM")
        else:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(1000)
            self.btn_auto_listen.setText("🔴 CONTINUOUS VOICE MODE: ACTIVE")
            self.btn_auto_listen.setStyleSheet("""
                background-color: rgba(255, 170, 0, 0.25);
                border: 1.5px solid #ffaa00;
                border-radius: 6px;
                color: #ffaa00;
                font-family: 'Consolas', sans-serif;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
            """)
            self.start_worker(mode="continuous")

    def execute_quick_command(self, cmd):
        self.append_log(cmd, "USER")
        self.start_worker(mode="text", command_text=cmd)


# ==========================================
# APPLICATION ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Omni AssistantHUDWindow()
    window.show()
    sys.exit(app.exec_())
