import google.generativeai as genai
import fitz
import os
import tkinter as tk
from tkinter import filedialog

# Configure API key for the generative AI model
genai.configure(api_key="AIzaSyAzqyNbRDJ8THxqpGK_SXbqZaJgnf0w8bc")

def choose_pdf_file():
    """
    Prompts the user to select a PDF file using a file dialog window.
    
    Returns:
        str: The file path of the selected PDF file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")],
    )
    return file_path

def read_pdf_file(file_path):
    """
    Reads the content of a PDF file and extracts its text.
    
    Args:
        file_path (str): The file path of the PDF to read.
    
    Returns:
        str: Extracted text from the PDF file.
    """
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""

        with fitz.open(file_path) as pdf:
            text = ""
            for page in pdf:
                text += page.get_text("text")

        if not text.strip():
            print("The PDF file contains no readable text (it might be a scanned or image-only document).")
        else:
            print(f"Successfully read content from '{os.path.basename(file_path)}'.\n")

        return text.strip()

    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def ask_question_about_pdf(text):
    """
    Allows the user to interactively ask questions based on the extracted text from the PDF.
    
    Args:
        text (str): Extracted text from the PDF.
    """
    print("\nYou can now ask questions regarding the content of the PDF.")
    print("Type 'exit' to terminate the session.\n")

    model = genai.GenerativeModel("gemini-2.5-flash")
    chat = model.start_chat(history=[])

    while True:
        question = input("Ask: ")
        if question.lower() in ["exit", "quit"]:
            print("Ending session. Goodbye.")
            break

        prompt = f"""
You are an intelligent assistant. Based on the following content, provide an accurate response to the user's question.

--- CONTENT START ---
{text[:20000]}
--- CONTENT END ---

Question: {question}
"""

        try:
            response = chat.send_message(prompt)
            print("\nAnswer:", response.text, "\n")
        except Exception as e:
            print(f"Error communicating with Gemini API: {e}")

if __name__ == "__main__":
    print("Please select a PDF file for analysis...\n")
    pdf_path = choose_pdf_file()

    if not pdf_path:
        print("No file selected. Exiting program.")
    else:
        print(f"Reading PDF file: {pdf_path}\n")
        text = read_pdf_file(pdf_path)

        if text:
            print("Extracted text preview:\n")
            print(text[:500])  # Display first 500 characters as a preview
            ask_question_about_pdf(text)
        else:
            print("No readable text found in the selected PDF.")
