import google.generativeai as genai
import fitz
import os
import tkinter as tk
from tkinter import filedialog

genai.configure(api_key="AIzaSyBLcKpMXm-86zVCzzwsTwMzlsJTt-TP_HQ")

def choose_pdf_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")],
    )
    return file_path

def read_pdf_file(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""

        with fitz.open(file_path) as pdf:
            text = ""
            for page in pdf:
                text += page.get_text("text")

        if not text.strip():
            print("The PDF file has no readable text (it might be scanned or image-only).")
        else:
            print(f"Successfully read content from '{os.path.basename(file_path)}'\n")

        return text.strip()

    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def ask_question_about_pdf(text):
    print("\nYou can now ask questions about the PDF content.")
    print("Type 'exit' to quit.\n")

    model = genai.GenerativeModel("gemini-2.5-flash")
    chat = model.start_chat(history=[])

    while True:
        question = input("Ask: ")
        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        prompt = f"""
You are an intelligent assistant. Based on the following story, answer the user's question accurately.

--- STORY START ---
{text[:20000]}
--- STORY END ---

Question: {question}
"""

        try:
            response = chat.send_message(prompt)
            print("\nAnswer:", response.text, "\n")
        except Exception as e:
            print(f"Error communicating with Gemini API: {e}")

if __name__ == "__main__":
    print("Please select a PDF file to analyze...\n")
    pdf_path = choose_pdf_file()

    if not pdf_path:
        print("No file selected. Exiting.")
    else:
        print(f"Reading PDF file: {pdf_path}\n")
        text = read_pdf_file(pdf_path)

        if text:
            print("Extracted text preview:\n")
            print(text[:500])
            ask_question_about_pdf(text)
        else:
            print("No readable text found in the PDF.")