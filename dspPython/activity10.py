import os
import fitz
import tkinter as tk
from tkinter import filedialog
import google.generativeai as genai

genai.configure(api_key="AIzaSyCQ_sJhXqEe7-SAadMPN981hbE_upB_MXw")

class PDFAssistant:
    def __init__(self):
        self.model_name = "gemini-2.5-flash"
        self.chat = None

    @staticmethod
    def choose_pdf():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )
        return file_path

    @staticmethod
    def extract_text(file_path):
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return ""

        try:
            with fitz.open(file_path) as pdf:
                text = "".join(page.get_text("text") for page in pdf)

            if not text.strip():
                print("PDF has no readable text (possibly scanned or image-only).")
            else:
                print(f"Successfully read content from '{os.path.basename(file_path)}'.\n")
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def initialize_chat(self):
        model = genai.GenerativeModel(self.model_name)
        self.chat = model.start_chat(history=[])

    def ask_questions(self, text):
        if not self.chat:
            self.initialize_chat()

        print("\nYou can now ask questions about the PDF content.")
        print("Type 'exit' or 'quit' to leave.\n")

        while True:
            question = input("Ask: ").strip()
            if question.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            prompt = (
                f"You are an intelligent assistant. Based on the following story, "
                f"answer the user's question accurately.\n\n"
                f"--- STORY START ---\n{text[:20000]}\n--- STORY END ---\n\n"
                f"Question: {question}"
            )

            try:
                response = self.chat.send_message(prompt)
                print("\nAnswer:", response.text, "\n")
            except Exception as e:
                print(f"Error communicating with Gemini API: {e}")

def main():
    print("Please select a PDF file to analyze...\n")
    pdf_path = PDFAssistant.choose_pdf()

    if not pdf_path:
        print("No file selected. Exiting.")
        return

    print(f"Reading PDF file: {pdf_path}\n")
    text = PDFAssistant.extract_text(pdf_path)

    if text:
        print("Extracted text preview (first 500 chars):\n")
        print(text[:500])
        assistant = PDFAssistant()
        assistant.ask_questions(text)
    else:
        print("No readable text found in the PDF.")

if __name__ == "__main__":
    main()
