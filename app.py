# ==========================================================
# cam1.py
# AI Vision Voice Assistant + Clothes Recommendation
# Aesthetic: Luxury Fashion Editorial — deep charcoal, warm gold
# ==========================================================

import cv2
import re
import base64
import queue
import threading
import webbrowser

import tkinter as tk
from tkinter import messagebox, font as tkfont

from PIL import Image, ImageTk, ImageDraw, ImageFilter
from google import genai
import speech_recognition as sr
import pyttsx3

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
from recommender import get_clothes


# ==========================================================
# DESIGN TOKENS
# ==========================================================
BG_DEEP       = "#0F0F0F"   # main background
BG_PANEL      = "#161616"   # right panel
BG_CARD       = "#1C1C1C"   # product cards
BG_INPUT      = "#111111"   # answer box
GOLD          = "#C9A84C"   # primary accent
GOLD_LIGHT    = "#E2C97E"   # hover/highlight
GOLD_DIM      = "#7A6330"   # subtle accent
WHITE         = "#F5F0E8"   # warm white text
GREY_MID      = "#888580"   # secondary text
GREY_DIM      = "#3A3835"   # borders/dividers
RED_ACCENT    = "#C0392B"   # error states
GREEN_ACCENT  = "#27AE60"   # success states

FONT_TITLE    = ("Georgia", 22, "bold")
FONT_HEADING  = ("Georgia", 11, "bold")
FONT_LABEL    = ("Trebuchet MS", 9)
FONT_LABEL_B  = ("Trebuchet MS", 9, "bold")
FONT_STATUS   = ("Trebuchet MS", 8)
FONT_BODY     = ("Trebuchet MS", 9)
FONT_BTN      = ("Trebuchet MS", 11, "bold")
FONT_BTN_SM   = ("Trebuchet MS", 8, "bold")


# ==========================================================
# API KEY
# ==========================================================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================================
# TTS — queue-based, non-blocking
# ==========================================================
tts_queue = queue.Queue()

def tts_worker():
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    while True:
        text = tts_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)
        tts_queue.task_done()

tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def speak(text):
    tts_queue.put(text)


# ==========================================================
# SPEECH RECOGNITION
# ==========================================================
recognizer = sr.Recognizer()

# ==========================================================
# GLOBAL STATE
# ==========================================================
last_question = None


# ==========================================================
# GENDER EXTRACTION
# ==========================================================
def extract_gender(question):
    q = question.lower()
    female_keywords = ["female", "woman", "women", "womens", "girl", "girls",
                       "her", "she", "ladies", "lady"]
    male_keywords   = ["male", "man", "men", "mens", "boy", "boys",
                       "his", "him", "he", "guys", "gents", "gentleman"]
    for word in female_keywords:
        if re.search(rf"\b{re.escape(word)}\b", q):
            return "female"
    for word in male_keywords:
        if re.search(rf"\b{re.escape(word)}\b", q):
            return "male"
    return "unknown"


# ==========================================================
# CAMERA
# ==========================================================
def open_camera():
    for index in range(2):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"Camera opened at index {index}")
            return cap
    return None

cap = open_camera()


# ==========================================================
# ROOT WINDOW
# ==========================================================
root = tk.Tk()
root.title("STYLO — AI Fashion Assistant")
root.geometry("1160x720")
root.configure(bg=BG_DEEP)
root.resizable(False, False)


# ==========================================================
# HELPERS
# ==========================================================
def update_status(text, color=GREY_MID):
    root.after(0, lambda: status_label.config(text=text, fg=color))

def _update_answer_box(answer):
    answer_box.config(state="normal")
    answer_box.delete("1.0", tk.END)
    answer_box.insert(tk.END, answer)
    answer_box.config(state="disabled")

def make_rounded_image(pil_img, radius=10):
    """Add rounded corners to a PIL image."""
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), pil_img.size], radius=radius, fill=255)
    result = pil_img.copy()
    result.putalpha(mask)
    return result


# ==========================================================
# BUTTON HOVER EFFECTS
# ==========================================================
def on_enter_btn(e, btn, color):
    btn.config(bg=color)

def on_leave_btn(e, btn, color):
    btn.config(bg=color)


# ==========================================================
# CLOTHES DISPLAY
# ==========================================================
def show_clothes(images):
    for widget in clothes_frame.winfo_children():
        widget.destroy()

    if not images:
        tk.Label(
            clothes_frame,
            text="No matching items found",
            bg=BG_PANEL,
            fg=GREY_MID,
            font=FONT_LABEL
        ).pack(pady=30)
        clothes_frame.update_idletasks()
        clothes_canvas.configure(scrollregion=clothes_canvas.bbox("all"))
        return

    for image_path, category, buy_url in images:
        try:
            # Card frame with subtle border
            card = tk.Frame(
                clothes_frame,
                bg=BG_CARD,
                highlightbackground=GREY_DIM,
                highlightthickness=1
            )
            card.pack(fill="x", padx=12, pady=5)

            # Inner padding frame
            inner = tk.Frame(card, bg=BG_CARD, padx=10, pady=10)
            inner.pack(fill="x")

            # Horizontal layout: image left, info right
            img_frame = tk.Frame(inner, bg=BG_CARD)
            img_frame.pack(side="left")

            info_frame = tk.Frame(inner, bg=BG_CARD, padx=12)
            info_frame.pack(side="left", fill="both", expand=True)

            # Product image
            img = Image.open(image_path).convert("RGBA")
            img = img.resize((90, 112), Image.LANCZOS)
            img = make_rounded_image(img, radius=6)
            imgtk = ImageTk.PhotoImage(img)
            img_label = tk.Label(img_frame, image=imgtk, bg=BG_CARD, bd=0)
            img_label.image = imgtk
            img_label.pack()

            # Category text — show last meaningful part
            parts = [p.strip() for p in category.split(",") if p.strip()]
            cat_main = parts[-1] if parts else category
            cat_sub  = parts[-2] if len(parts) >= 2 else ""

            if cat_sub:
                tk.Label(
                    info_frame,
                    text=cat_sub.upper(),
                    bg=BG_CARD,
                    fg=GOLD_DIM,
                    font=("Trebuchet MS", 7, "bold"),
                    anchor="w"
                ).pack(anchor="w")

            tk.Label(
                info_frame,
                text=cat_main,
                bg=BG_CARD,
                fg=WHITE,
                font=FONT_HEADING,
                anchor="w",
                wraplength=200
            ).pack(anchor="w", pady=(2, 6))

            # Gold divider line
            tk.Frame(info_frame, bg=GOLD_DIM, height=1).pack(fill="x", pady=4)

            # Buy Now button
            buy_btn = tk.Button(
                info_frame,
                text="SHOP NOW  →",
                font=FONT_BTN_SM,
                bg=GOLD,
                fg=BG_DEEP,
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                command=lambda url=buy_url: webbrowser.open(url)
            )
            buy_btn.pack(anchor="w", pady=(4, 0))
            buy_btn.bind("<Enter>", lambda e, b=buy_btn: b.config(bg=GOLD_LIGHT))
            buy_btn.bind("<Leave>", lambda e, b=buy_btn: b.config(bg=GOLD))

        except Exception as e:
            print("Image load error:", e)

    clothes_frame.update_idletasks()
    clothes_canvas.configure(scrollregion=clothes_canvas.bbox("all"))


# ==========================================================
# CAMERA UPDATE
# ==========================================================
def update_camera():
    if cap and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb).resize((580, 435), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(pil_img)
            camera_label.imgtk = imgtk
            camera_label.configure(image=imgtk)
            camera_label.current_frame = frame
    camera_label.after(10, update_camera)


# ==========================================================
# VOICE INPUT
# ==========================================================
def listen_question():
    global last_question
    try:
        with sr.Microphone() as source:
            update_status("● LISTENING", GOLD)
            speak("Please ask your question")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6)

        question = recognizer.recognize_google(audio)
        update_status(f'"{question}"', WHITE)
        last_question = question
        return question

    except sr.WaitTimeoutError:
        update_status("No voice detected. Try again.", RED_ACCENT)
        speak("I did not hear anything.")
    except sr.UnknownValueError:
        update_status("Could not understand. Speak clearly.", RED_ACCENT)
        speak("Sorry, I did not understand.")
    except Exception as e:
        update_status(f"Mic error: {e}", RED_ACCENT)
        print("Mic error:", e)
    return None


# ==========================================================
# AI ANALYSIS
# ==========================================================
def analyze_with_ai():
    frame = getattr(camera_label, "current_frame", None)
    if frame is None:
        messagebox.showerror("Error", "Camera not ready")
        return

    question = listen_question()
    if not question:
        return

    _, buffer = cv2.imencode(".jpg", frame)
    image_base64 = base64.b64encode(buffer).decode("utf-8")

    try:
        update_status("● ANALYZING WITH AI", GOLD)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{
                "role": "user",
                "parts": [
                    {"text": question},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
                ]
            }]
        )

        answer = response.text
        root.after(0, lambda: _update_answer_box(answer))
        update_status("● SPEAKING", GOLD_LIGHT)
        speak(answer)
        update_status("Ready", GREY_MID)

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("AI Error", str(e)))
        update_status("AI error. Try again.", RED_ACCENT)


# ==========================================================
# CLOTHING RECOMMENDATION
# ==========================================================
def handle_clothing_display():
    if not last_question:
        return
    gender = extract_gender(last_question)
    print(f"[cam1] Query: {last_question!r} | Gender: {gender}")
    update_status("● FINDING OUTFITS", GOLD)
    clothes = get_clothes(last_question, gender)
    root.after(0, lambda: show_clothes(clothes))


# ==========================================================
# THREAD WRAPPER
# ==========================================================
def start_ai_thread():
    ask_btn.config(state="disabled", text="PROCESSING...", bg=GREY_DIM)

    def run():
        try:
            analyze_with_ai()
            handle_clothing_display()
        finally:
            root.after(0, lambda: ask_btn.config(
                state="normal", text="  ◉  ASK WITH VOICE", bg=GOLD
            ))

    threading.Thread(target=run, daemon=True).start()


# ==========================================================
# CLEAN EXIT
# ==========================================================
def on_close():
    tts_queue.put(None)
    if cap:
        cap.release()
    root.destroy()


# ==========================================================
# ░░░░░░░░░░  BUILD UI  ░░░░░░░░░░
# ==========================================================

# ── TOP BAR ──────────────────────────────────────────────
topbar = tk.Frame(root, bg=BG_DEEP, height=56)
topbar.pack(fill="x")
topbar.pack_propagate(False)

tk.Label(
    topbar,
    text="S T Y L O",
    font=("Georgia", 20, "bold"),
    bg=BG_DEEP,
    fg=GOLD
).pack(side="left", padx=24, pady=12)

tk.Label(
    topbar,
    text="A I  F A S H I O N  A S S I S T A N T",
    font=("Trebuchet MS", 8),
    bg=BG_DEEP,
    fg=GOLD_DIM
).pack(side="left", pady=20)

# Gold top-bar accent line
tk.Frame(root, bg=GOLD, height=1).pack(fill="x")

# ── MAIN BODY ─────────────────────────────────────────────
body = tk.Frame(root, bg=BG_DEEP)
body.pack(fill="both", expand=True)

# ── LEFT COLUMN: Camera ──────────────────────────────────
left_col = tk.Frame(body, bg=BG_DEEP)
left_col.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=16)

# Camera container with gold border
cam_border = tk.Frame(
    left_col,
    bg=GOLD_DIM,
    padx=1, pady=1
)
cam_border.pack(fill="both", expand=True)

cam_inner = tk.Frame(cam_border, bg=BG_DEEP)
cam_inner.pack(fill="both", expand=True)

camera_label = tk.Label(cam_inner, bg="#050505", cursor="none")
camera_label.pack(fill="both", expand=True)

# Camera label strip
cam_strip = tk.Frame(left_col, bg=BG_DEEP, height=28)
cam_strip.pack(fill="x", pady=(6, 0))

tk.Label(
    cam_strip,
    text="◉  LIVE FEED",
    font=("Trebuchet MS", 8),
    bg=BG_DEEP,
    fg=GREY_MID
).pack(side="left")

status_label = tk.Label(
    cam_strip,
    text="Ready",
    font=FONT_STATUS,
    bg=BG_DEEP,
    fg=GREY_MID
)
status_label.pack(side="right")

# ── RIGHT COLUMN: Controls + Results ─────────────────────
right_col = tk.Frame(body, bg=BG_PANEL, width=380)
right_col.pack(side="right", fill="y", padx=(0, 0), pady=0)
right_col.pack_propagate(False)

# Gold left-edge accent
tk.Frame(right_col, bg=GOLD_DIM, width=1).pack(side="left", fill="y")

right_inner = tk.Frame(right_col, bg=BG_PANEL)
right_inner.pack(side="left", fill="both", expand=True)

# ── ASK BUTTON ───────────────────────────────────────────
btn_frame = tk.Frame(right_inner, bg=BG_PANEL)
btn_frame.pack(fill="x", padx=16, pady=(20, 8))

ask_btn = tk.Button(
    btn_frame,
    text="  ◉  ASK WITH VOICE",
    font=FONT_BTN,
    bg=GOLD,
    fg=BG_DEEP,
    relief="flat",
    cursor="hand2",
    padx=0,
    pady=12,
    activebackground=GOLD_LIGHT,
    activeforeground=BG_DEEP,
    command=start_ai_thread
)
ask_btn.pack(fill="x")
ask_btn.bind("<Enter>", lambda e: ask_btn.config(bg=GOLD_LIGHT))
ask_btn.bind("<Leave>", lambda e: ask_btn.config(bg=GOLD) if ask_btn["state"] == "normal" else None)

# ── ANSWER SECTION ───────────────────────────────────────
tk.Frame(right_inner, bg=GREY_DIM, height=1).pack(fill="x", padx=16, pady=(12, 0))

tk.Label(
    right_inner,
    text="AI RESPONSE",
    font=("Trebuchet MS", 7, "bold"),
    bg=BG_PANEL,
    fg=GOLD_DIM
).pack(anchor="w", padx=18, pady=(8, 3))

answer_box = tk.Text(
    right_inner,
    height=7,
    font=FONT_BODY,
    wrap="word",
    state="disabled",
    bg=BG_INPUT,
    fg=WHITE,
    relief="flat",
    padx=10,
    pady=8,
    insertbackground=GOLD,
    selectbackground=GOLD_DIM,
    cursor="arrow",
    highlightthickness=1,
    highlightbackground=GREY_DIM,
    highlightcolor=GOLD_DIM
)
answer_box.pack(fill="x", padx=16, pady=(0, 8))

# ── OUTFITS SECTION ──────────────────────────────────────
tk.Frame(right_inner, bg=GREY_DIM, height=1).pack(fill="x", padx=16, pady=(4, 0))

outfit_header = tk.Frame(right_inner, bg=BG_PANEL)
outfit_header.pack(fill="x", padx=16, pady=(8, 4))

tk.Label(
    outfit_header,
    text="RECOMMENDED OUTFITS",
    font=("Trebuchet MS", 7, "bold"),
    bg=BG_PANEL,
    fg=GOLD_DIM
).pack(side="left")

# ── SCROLLABLE CARDS ─────────────────────────────────────
scroll_container = tk.Frame(right_inner, bg=BG_PANEL)
scroll_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

clothes_canvas = tk.Canvas(
    scroll_container,
    bg=BG_PANEL,
    highlightthickness=0,
    bd=0
)
scrollbar = tk.Scrollbar(
    scroll_container,
    orient="vertical",
    command=clothes_canvas.yview,
    bg=BG_PANEL,
    troughcolor=BG_PANEL,
    activebackground=GOLD_DIM
)
clothes_canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
clothes_canvas.pack(side="left", fill="both", expand=True)

clothes_frame = tk.Frame(clothes_canvas, bg=BG_PANEL)
clothes_canvas_window = clothes_canvas.create_window(
    (0, 0), window=clothes_frame, anchor="nw"
)

def on_clothes_frame_resize(event):
    clothes_canvas.configure(scrollregion=clothes_canvas.bbox("all"))

def on_clothes_canvas_resize(event):
    clothes_canvas.itemconfig(clothes_canvas_window, width=event.width)

clothes_frame.bind("<Configure>", on_clothes_frame_resize)
clothes_canvas.bind("<Configure>", on_clothes_canvas_resize)

def on_mousewheel(event):
    clothes_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def on_mousewheel_linux(event):
    clothes_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

clothes_canvas.bind_all("<MouseWheel>", on_mousewheel)
clothes_canvas.bind_all("<Button-4>", on_mousewheel_linux)
clothes_canvas.bind_all("<Button-5>", on_mousewheel_linux)

# ── BOTTOM STATUS BAR ─────────────────────────────────────
tk.Frame(root, bg=GREY_DIM, height=1).pack(fill="x")
bottom_bar = tk.Frame(root, bg=BG_DEEP, height=24)
bottom_bar.pack(fill="x")
bottom_bar.pack_propagate(False)
tk.Label(
    bottom_bar,
    text="Powered by Gemini 2.5 Flash  ·  Google Speech Recognition  ·  pyttsx3",
    font=("Trebuchet MS", 7),
    bg=BG_DEEP,
    fg=GREY_DIM
).pack(side="right", padx=12)


# ==========================================================
# START
# ==========================================================
if cap is None:
    messagebox.showerror(
        "Camera Error",
        "No camera found. Please connect a camera and restart."
    )

update_camera()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
