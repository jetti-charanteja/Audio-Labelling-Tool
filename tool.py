# tool.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Scrollbar
from utils.waveform_display import display_waveform
from utils.transcription_ai import transcribe_audio
from utils.db_upload import upload_to_mysql
from utils.pdf_generator import generate_pdf
from utils.shortcuts_handler import bind_shortcuts
import pandas as pd
import os
import threading
import librosa
import pygame
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'audio_labeling_tool/utils'))


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
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        load_button = tk.Button(self.main_frame, text="Load Audio File", command=self.load_audio_file)
        self.load_button.pack(pady=10)

        self.canvas = tk.Canvas(self.main_frame)
        self.scroll_y = Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")

        self.transcription_entry = tk.Entry(self.scroll_frame, width=100)
        self.transcription_entry.pack(pady=5)

        self.label_vars = {}
        self.labels = ["Speech", "Noise", "Music", "Happy", "Sad", "Angry", "English", "Telugu"]
        for label in self.labels:
            var = tk.IntVar()
            chk = tk.Checkbutton(self.scroll_frame, text=label, variable=var)
            chk.pack(anchor='w')
            self.label_vars[label] = var

        tk.Label(self.scroll_frame, text="Start Time (sec)").pack()
        self.start_time_entry = tk.Entry(self.scroll_frame)
        self.start_time_entry.pack()

        tk.Label(self.scroll_frame, text="End Time (sec)").pack()
        self.end_time_entry = tk.Entry(self.scroll_frame)
        self.end_time_entry.pack()

        self.waveform_button = tk.Button(self.scroll_frame, text="Show Waveform", command=self.plot_waveform)
        self.waveform_button.pack(pady=5)

        self.transcribe_button = tk.Button(self.scroll_frame, text="Auto Transcribe", command=self.auto_transcribe)
        self.transcribe_button.pack(pady=5)

        self.play_button = tk.Button(self.scroll_frame, text="Play", command=self.play_audio)
        self.play_button.pack(pady=5)

        self.save_button = tk.Button(self.scroll_frame, text="Save & Next", command=self.save_label)
        self.save_button.pack(pady=5)

        self.export_csv_button = tk.Button(self.scroll_frame, text="Export CSV", command=self.export_csv)
        self.export_csv_button.pack(pady=5)

        self.export_pdf_button = tk.Button(self.scroll_frame, text="Export PDF", command=self.export_pdf)
        self.export_pdf_button.pack(pady=5)

        self.upload_db_button = tk.Button(self.scroll_frame, text="Upload to MySQL", command=self.upload_db)
        self.upload_db_button.pack(pady=5)

    def load_audio_files(self):
        folder = filedialog.askdirectory()
        if folder:
            self.audio_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(('.wav', '.mp3'))]
            self.audio_files.sort()
            self.current_index = 0
            messagebox.showinfo("Loaded", f"{len(self.audio_files)} audio files loaded.")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioLabelingTool(root)
    root.mainloop()
