import customtkinter as ctk
import speech_recognition as sr
import pyttsx3
import threading
import wikipedia
import datetime
import webbrowser
import os
import pywhatkit
import requests

# -------------------- Audio Engine --------------------
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)
engine.setProperty("rate", 175)

listening = False
memory_city = None
waiting_for_city_input = False

def speak(text):
    engine.say(text)
    engine.runAndWait()


# -------------------- Custom Mapped Commands --------------------
CUSTOM_COMMANDS = {
    "open notepad": "notepad.exe",
    "open explorer": "explorer.exe",
    "open calculator": "calc.exe",
    "open chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "open vs code": r"C:\Users\LENOVO\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "open downloads": r"C:\Users\LENOVO\Downloads",
}

VOICE_COMMANDS = [
    "Time",
    "Weather in <city>",
    "Search <topic>",
    "Play <song>",
    "Open YouTube / Google",
    "Shutdown / Restart PC",
    "Stop listening / Exit"
] + list(CUSTOM_COMMANDS.keys())


# ---------------- Weather API ----------------
def get_weather(city):
    try:
        url = f"http://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        return f"🌤 Weather in {city.title()} → {desc}, {temp}°C, Humidity: {humidity}%"
    except:
        return None


# ---------------- Command Handler ----------------
def handle_command(query):
    global waiting_for_city_input, memory_city
    query = query.lower().strip()

    # If waiting for city
    if waiting_for_city_input:
        waiting_for_city_input = False
        memory_city = query
        weather_info = get_weather(query)
        if weather_info:
            update_output(weather_info)
            speak(weather_info)
        else:
            speak("Sorry, I couldn't find weather details.")
        return

    # TIME
    if "time" in query:
        now = datetime.datetime.now().strftime("%I:%M %p")
        msg = f"⏱ The time is {now}"
        update_output(msg)
        speak(msg)
        return

    # WEATHER
    if "weather" in query:
        words = query.split()
        if "in" in words:
            city = words[words.index("in") + 1]
        else:
            if memory_city:
                city = memory_city
            else:
                speak("Which city?")
                update_output("📍 Awaiting city input...")
                waiting_for_city_input = True
                return

        weather_info = get_weather(city)
        if weather_info:
            memory_city = city
            update_output(weather_info)
            speak(weather_info)
        else:
            speak("Couldn't check weather right now.")
        return

    # WIKIPEDIA
    if "wikipedia" in query:
        term = query.replace("wikipedia", "").strip()
        update_output(f"📘 Searching Wikipedia for {term}...")
        try:
            result = wikipedia.summary(term, sentences=2)
            update_output(result)
            speak(result)
        except:
            speak("Unable to find details.")
        return

    # SEARCH
    if "search" in query:
        term = query.replace("search", "").strip()
        update_output(f"🔍 Searching {term}...")
        pywhatkit.search(term)
        speak(f"Searching {term}")
        return

    # SONGS
    if "play" in query:
        song = query.replace("play", "").strip()
        update_output(f"🎶 Playing {song}")
        pywhatkit.playonyt(song)
        speak(f"Playing {song}")
        return

    # WEBSITES
    if "open youtube" in query:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
        update_output("▶ Opening YouTube...")
        return

    if "open google" in query:
        webbrowser.open("https://google.com")
        speak("Opening Google")
        update_output("🌍 Opening Google...")
        return

    # CUSTOM COMMANDS
    if query in CUSTOM_COMMANDS:
        os.startfile(CUSTOM_COMMANDS[query])
        speak(f"Opening {query.replace('open ', '')}")
        update_output(f"🚀 Opening {query.replace('open ', '')}")
        return

    # PC Commands
    if "shutdown" in query:
        speak("Shutting down...")
        os.system("shutdown /s /t 5")
        return

    if "restart" in query:
        speak("Restarting now...")
        os.system("shutdown /r /t 5")
        return

    # Exit
    if "stop listening" in query or "exit" in query:
        speak("Goodbye!")
        app.destroy()
        return

    update_output("❓ Command not recognized")
    speak("Sorry, I didn’t understand.")


# ---------------- Voice Recognition Thread ----------------
def listen():
    global listening
    recognizer = sr.Recognizer()

    while listening:
        try:
            with sr.Microphone() as source:
                update_status("🎤 Listening...")
                recognizer.pause_threshold = 1
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)

            update_status("🔍 Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
            update_output(f"🧑 You: {query}")
            handle_command(query)

        except:
            update_status("⚠ Try speaking again...")
            continue


# ---------------- GUI Handlers ----------------
def start_listening():
    global listening
    if not listening:
        listening = True
        speak("Voice mode activated")
        update_status("🟢 Active")
        threading.Thread(target=listen, daemon=True).start()

def stop_listening():
    global listening
    listening = False
    update_status("🔴 Paused")

def update_status(text):
    status_label.configure(text=text)

def update_output(text):
    output_box.insert("end", f"{text}\n")
    output_box.see("end")

# ---------------- GUI Styling ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("✨ AI Desktop Assistant ✨")
app.geometry("1050x620")
app.resizable(False, False)

# Panels
left_panel = ctk.CTkFrame(app, width=320, corner_radius=25)
left_panel.pack(side="left", fill="y", padx=10, pady=10)

right_panel = ctk.CTkFrame(app, corner_radius=25)
right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Left Panel
ctk.CTkLabel(left_panel, text="🧠 Available Commands", font=("Segoe UI", 24, "bold")).pack(pady=20)

command_box = ctk.CTkTextbox(left_panel, width=290, height=500,
                             font=("Consolas", 15), fg_color="#0d0d0d")
command_box.pack(padx=10)

for cmd in VOICE_COMMANDS:
    command_box.insert("end", f"⭐ {cmd}\n")

command_box.configure(state="disabled")

# Right Panel
ctk.CTkLabel(right_panel, text="🤖 AI Voice Assistant", font=("Segoe UI", 34, "bold")).pack(pady=10)
status_label = ctk.CTkLabel(right_panel, text="🔴 Idle", font=("Segoe UI", 18, "bold"))
status_label.pack(pady=5)

output_box = ctk.CTkTextbox(right_panel, width=650, height=330, font=("Consolas", 14),
                            fg_color="#101820", text_color="white")
output_box.pack(pady=15)

button_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
button_frame.pack(pady=10)

ctk.CTkButton(button_frame, text="🎤 Start Listening", width=250, height=50,
              fg_color="#00c853", hover_color="#00e676",
              command=start_listening).grid(row=0, column=0, padx=15)

ctk.CTkButton(button_frame, text="🛑 Stop", width=250, height=50,
              fg_color="#ff1744", hover_color="#ff5252",
              command=stop_listening).grid(row=0, column=1, padx=15)

ctk.CTkButton(right_panel, text="❌ Exit", width=200, height=40,
              fg_color="#d32f2f", hover_color="#e53935",
              command=app.destroy).pack(pady=10)

app.mainloop()
