import os
import fitz
import google.generativeai as genai

# ----------------------- CONFIG -----------------------
genai.configure(api_key="AIzaSyAaNou_zMFAF_5KCK7rtTHLDzkqOF44hAg")

# ----------------------- PDF READER -----------------------
def read_pdf_file(file_path: str) -> str:
    """Reads and extracts text from a PDF file."""
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""

        with fitz.open(file_path) as pdf:
            text_content = "".join(page.get_text("text") for page in pdf)

        if text_content.strip():
            print(f"Successfully read content from '{file_path}'\n")
        else:
            print("The PDF file has no readable text (possibly image-only).")

        return text_content.strip()

    except Exception as error:
        print(f"Error reading PDF file: {error}")
        return ""

# ----------------------- Q&A FUNCTION -----------------------
def ask_question_about_pdf(text: str):
    """Allows the user to ask questions about the PDF content interactively."""
    print("\nYou can now ask questions about the PDF content.")
    print("Type 'exit' to quit.\n")

    model = genai.GenerativeModel("gemini-2.5-flash")
    chat = model.start_chat(history=[])

    while True:
        question = input("Ask: ")
        if question.lower() in ("exit", "quit"):
            print("Goodbye.")
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
        except Exception as error:
            print(f"Error communicating with Gemini API: {error}")

# ----------------------- MAIN EXECUTION -----------------------
if __name__ == "__main__":
    pdf_path = r"C:\Users\Janssen_Jude\Downloads\LastWish.pdf"

    print("Reading PDF file...\n")
    pdf_text = read_pdf_file(pdf_path)

    if pdf_text:
        print("Extracted text preview:\n")
        print(pdf_text[:500])
        ask_question_about_pdf(pdf_text)
    else:
        print("No readable text found in the PDF.")
