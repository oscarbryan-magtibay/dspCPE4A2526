import os
import fitz  # For reading PDF text
from dotenv import load_dotenv
import google.generativeai as genai  # Google AI SDK

# -----------------------------------------------------------------------------
# 1. Load your Google API key from .env file
# -----------------------------------------------------------------------------
load_dotenv()  # Looks for a .env file in the same folder

# ✅ Correct: use the variable name, not the actual key
GOOGLE_API_KEY = os.getenv("AIzaSyCWR0ekYXTNSnB3XBmyJzD2xssJ45krwIU")

if not GOOGLE_API_KEY:
    print("❌ Google API key is missing. Please add it to your .env file:")
    print("   GOOGLE_API_KEY=your-valid-key-here")
    exit()

# Configure Gemini with your API key
genai.configure(api_key=GOOGLE_API_KEY)
print("✅ Google API key loaded successfully!")

# -----------------------------------------------------------------------------
# 2. PDF Reading Function
# -----------------------------------------------------------------------------
def read_pdf(file_path):
    """Reads the PDF file and extracts text."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return ""

    try:
        with fitz.open(file_path) as pdf:
            text = ""
            for page in pdf:
                text += page.get_text("text")
        if not text.strip():
            print("⚠️ No readable text in the PDF.")
            return ""
        return text.strip()
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""

# -----------------------------------------------------------------------------
# 3. Ask Questions Using Google Gemini
# -----------------------------------------------------------------------------
def ask_question_gemini(text):
    """Allows user to ask questions about the PDF using Google Gemini."""
    
    # List available models to check which one to use
    available_models = genai.list_models()
    print("Available Models:", available_models)

    # Assuming you select a model based on the list, like "gemini-1.0"
    model = genai.GenerativeModel("gemini-1.0")  # Update with the correct model after checking
    
    while True:
        question = input("❓ Ask a question about the PDF (or type 'exit' to quit): ")
        if question.lower() == "exit":
            print("👋 Goodbye!")
            break

        prompt = f"""
        Based on the following PDF content, answer the user's question clearly.

        --- PDF CONTENT ---
        {text[:4000]}
        --- END OF CONTENT ---

        Question: {question}
        """

        try:
            response = model.generate_text(prompt)  # Changed to generate_text
            print("💡 Answer:", response.text)
        except Exception as e:
            print(f"❌ Error with Gemini API: {e}")

# -----------------------------------------------------------------------------
# 4. Main Logic
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    pdf_path = "The_Quiet_Corners_of_Room_304 (1).pdf"

    print("📂 Reading PDF...\n")
    text = read_pdf(pdf_path)

    if text:
        print("\n✅ Extracted Text Preview:\n", text[:1000])
        ask_question_gemini(text)
    else:
        print("⚠️ No readable text found.")
