# main.py

import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar
import pandas as pd
import os
import threading
import librosa
import librosa.display
import matplotlib.pyplot as plt
from fpdf import FPDF
import speech_recognition as sr
import pygame
import pymysql
from db_config import DB_CONFIG
import PIL.Image

# ------------------ Helper Functions ------------------

def display_waveform(audio_path):
    y, sr = librosa.load(audio_path, sr=None)
    plt.figure(figsize=(10, 3))
    librosa.display.waveshow(y, sr=sr)
    plt.title(f"Waveform: {os.path.basename(audio_path)}")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    os.makedirs("assets", exist_ok=True)
    output_path = "assets/waveform_temp.png"
    plt.savefig(output_path)
    plt.close()
    PIL.Image.open(output_path).show()

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "[Unintelligible]"
    except sr.RequestError as e:
        return f"[Error: {e}]"
    except Exception as e:
        return f"[Unexpected error: {e}]"

def generate_pdf(data, filename="output/report.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Audio Labeling Report", ln=True, align='C')
    pdf.ln(10)
    for i, entry in enumerate(data, 1):
        pdf.multi_cell(0, 10, txt=f"{i}. File: {entry['filename']}\n"
                                     f"   Transcription: {entry['transcription']}\n"
                                     f"   Labels: {entry['labels']}\n"
                                     f"   Start Time: {entry['start_time']} sec\n"
                                     f"   End Time: {entry['end_time']} sec\n",
                       border=0)
        pdf.ln(2)
    pdf.output(filename)

def upload_to_mysql(data):
    try:
        conn = pymysql.connect(**DB_CONFIG)(
            host="localhost",
            user="your_username",
            password="root",
            database="audio_labeling_db"
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labeled_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255),
                transcription TEXT,
                labels VARCHAR(255),
                start_time VARCHAR(50),
                end_time VARCHAR(50)
            )
        """)
        for entry in data:
            cursor.execute("""
                INSERT INTO labeled_data (filename, transcription, labels, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                entry["filename"], entry["transcription"], entry["labels"], entry["start_time"], entry["end_time"]
            ))
        conn.commit()
        cursor.close()
        conn.close()
    except pymysql.connect.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def bind_shortcuts(root, app):
    root.bind('<space>', lambda event: app.play_audio())
    root.bind('<Return>', lambda event: app.save_label())
    root.bind('<Control-Right>', lambda event: app.next_audio())
    root.bind('<Control-Left>', lambda event: app.previous_audio())
    label_keys = {'1': "Speech", '2': "Noise", '3': "Music", '4': "Happy", '5': "Sad", '6': "Angry", '7': "English", '8': "Telugu"}
    for key, label in label_keys.items():
        root.bind(key, lambda e, lbl=label: toggle_label(app, lbl))

def toggle_label(app, label):
    var = app.label_vars.get(label)
    if var is not None:
        var.set(0 if var.get() == 1 else 1)

# ------------------ Main GUI Class ------------------

class AudioLabelingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Labeling & Transcription Tool")
        self.root.geometry("1200x700")
        self.audio_files = []
        self.current_index = 0
        self.data = []
        self.build_ui()
        pygame.mixer.init()
        bind_shortcuts(self.root, self)

    def build_ui(self):
        self.root.configure(bg="#ecf0f1")

        self.main_frame = tk.Frame(self.root, bg="#ecf0f1")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Label(self.main_frame, text="🎧 Audio Labeling & Transcription Tool",
                          font=("Segoe UI", 16, "bold"), fg="#2c3e50", bg="#ecf0f1", pady=15)
        header.pack(fill=tk.X)

        self.load_button = tk.Button(self.main_frame, text="Load Audio File", font=("Segoe UI", 10),
                                     width=20, pady=5, command=self.load_audio_file)
        self.load_button.pack(pady=(5, 15))

        self.canvas = tk.Canvas(self.main_frame, bg="#f8f9fa")
        self.scroll_y = Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#f8f9fa")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scroll_y.pack(side="right", fill="y")

        # Transcription
        tk.Label(self.scroll_frame, text="Transcription", font=("Segoe UI", 10, "bold"), bg="#f8f9fa").pack(
            pady=(10, 0))
        self.transcription_entry = tk.Entry(self.scroll_frame, width=100, font=("Segoe UI", 10))
        self.transcription_entry.pack(pady=5)

        # Labels
        tk.Label(self.scroll_frame, text="Select Labels", font=("Segoe UI", 10, "bold"), bg="#f8f9fa").pack(
            pady=(10, 5))
        self.label_vars = {}
        self.labels = ["Speech", "Noise", "Music", "Happy", "Sad", "Angry", "English", "Telugu"]
        for label in self.labels:
            var = tk.IntVar()
            chk = tk.Checkbutton(self.scroll_frame, text=label, variable=var,
                                 font=("Segoe UI", 10), bg="#f8f9fa", anchor='w')
            chk.pack(anchor='w', padx=10)
            self.label_vars[label] = var

        # Start and End Time
        tk.Label(self.scroll_frame, text="Start Time (sec)", font=("Segoe UI", 10, "bold"), bg="#f8f9fa").pack(
            pady=(10, 0))
        self.start_time_entry = tk.Entry(self.scroll_frame, font=("Segoe UI", 10))
        self.start_time_entry.pack(pady=3)

        tk.Label(self.scroll_frame, text="End Time (sec)", font=("Segoe UI", 10, "bold"), bg="#f8f9fa").pack(
            pady=(10, 0))
        self.end_time_entry = tk.Entry(self.scroll_frame, font=("Segoe UI", 10))
        self.end_time_entry.pack(pady=3)

        # Functional Buttons
        button_style = {"font": ("Segoe UI", 10), "width": 25, "pady": 5}

        self.waveform_button = tk.Button(self.scroll_frame, text="📊 Show Waveform", command=self.plot_waveform,
                                         **button_style)
        self.waveform_button.pack(pady=6)

        self.transcribe_button = tk.Button(self.scroll_frame, text="📝 Auto Transcribe", command=self.auto_transcribe,
                                           **button_style)
        self.transcribe_button.pack(pady=6)

        self.play_button = tk.Button(self.scroll_frame, text="▶️ Play Audio", command=self.play_audio, **button_style)
        self.play_button.pack(pady=6)

        self.save_button = tk.Button(self.scroll_frame, text="💾 Save & Next", command=self.save_label, **button_style)
        self.save_button.pack(pady=6)

        self.export_csv_button = tk.Button(self.scroll_frame, text="📤 Export CSV", command=self.export_csv,
                                           **button_style)
        self.export_csv_button.pack(pady=6)

        self.export_pdf_button = tk.Button(self.scroll_frame, text="📄 Export PDF", command=self.export_pdf,
                                           **button_style)
        self.export_pdf_button.pack(pady=6)

        self.upload_db_button = tk.Button(self.scroll_frame, text="☁️ Upload to MySQL", command=self.upload_db,
                                          **button_style)
        self.upload_db_button.pack(pady=6)

        # Optional Footer
        footer = tk.Label(self.root, text="🔊 Tip: Use SPACE to play audio, ENTER to save, CTRL+→ to skip",
                          font=("Segoe UI", 9), bg="#dfe6e9", fg="#2d3436", bd=1, relief=tk.SUNKEN, anchor='w')
        footer.pack(side=tk.BOTTOM, fill=tk.X)

    def load_audio_file(self):
        file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if file:
            self.audio_files = [file]
            self.current_index = 0
            messagebox.showinfo("Loaded", f"Loaded file: {os.path.basename(file)}")

    def play_audio(self):
        if self.current_index < len(self.audio_files):
            path = self.audio_files[self.current_index]
            threading.Thread(target=lambda: pygame.mixer.music.load(path) or pygame.mixer.music.play()).start()

    def plot_waveform(self):
        if self.current_index < len(self.audio_files):
            display_waveform(self.audio_files[self.current_index])

    def auto_transcribe(self):
        if self.current_index < len(self.audio_files):
            result = transcribe_audio(self.audio_files[self.current_index])
            self.transcription_entry.delete(0, tk.END)
            self.transcription_entry.insert(0, result)

    def save_label(self):
        if self.current_index < len(self.audio_files):
            labels = [label for label, var in self.label_vars.items() if var.get() == 1]
            entry = {
                "filename": os.path.basename(self.audio_files[self.current_index]),
                "transcription": self.transcription_entry.get(),
                "labels": ", ".join(labels),
                "start_time": self.start_time_entry.get(),
                "end_time": self.end_time_entry.get()
            }
            self.data.append(entry)
            self.transcription_entry.delete(0, tk.END)
            self.start_time_entry.delete(0, tk.END)
            self.end_time_entry.delete(0, tk.END)
            for var in self.label_vars.values():
                var.set(0)
            self.current_index += 1
            if self.current_index >= len(self.audio_files):
                messagebox.showinfo("Done", "All files labeled.")

    def export_csv(self):
        df = pd.DataFrame(self.data)
        os.makedirs("output", exist_ok=True)
        df.to_csv("output/labeled_data.csv", index=False)
        messagebox.showinfo("Exported", "CSV exported successfully.")

    def export_pdf(self):
        generate_pdf(self.data, "output/report.pdf")
        messagebox.showinfo("Exported", "PDF exported successfully.")

    def upload_db(self):
        upload_to_mysql(self.data)
        messagebox.showinfo("Uploaded", "Data uploaded to MySQL successfully.")

    def next_audio(self):
        if self.current_index < len(self.audio_files) - 1:
            self.current_index += 1

    def previous_audio(self):
        if self.current_index > 0:
            self.current_index -= 1

# ------------------ App Start ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioLabelingTool(root)
    root.mainloop()