# waveform_display.py

import librosa
import librosa.display
import matplotlib.pyplot as plt
import os


def display_waveform(audio_path):
    try:
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

        # Optionally, show in a new window (depends on GUI design)
        import PIL.Image
        PIL.Image.open(output_path).show()

    except Exception as e:
        print(f"Error displaying waveform: {e}")
