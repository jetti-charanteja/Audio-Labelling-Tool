# pdf_generator.py

from fpdf import FPDF
import os

def generate_pdf(data, filename="output/report.pdf"):
    try:
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
    except Exception as e:
        print(f"Error generating PDF: {e}")
