from faster_whisper import WhisperModel
import requests
import time
import threading
import queue
import os
import re
import torch
import pygame
from TTS.api import TTS
import tempfile
import gc
import pyaudio
import wave
import keyboard
import json
from collections import deque
import PyPDF2

# LangChain imports (updated)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# -----------------------------
# Config
# -----------------------------
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
TIMEOUT = 30
MAX_RETRIES = 3
REFERENCE_VOICE = "reference.wav"
PDF_FOLDER = "school_documents"
VECTOR_DB_PATH = "chroma_langchain"

# -----------------------------
# Global RAG Components (Initialized once)
# -----------------------------
rag_vector_db = None
retriever = None

# -----------------------------
# RAG Setup with Optimization
# -----------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def load_documents():
    docs = []
    if not os.path.exists(PDF_FOLDER):
        print(f"PDF folder '{PDF_FOLDER}' not found. Skipping document load.")
        return docs

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in '{PDF_FOLDER}'.")
        return docs

    for filename in pdf_files:
        file_path = os.path.join(PDF_FOLDER, filename)
        print(f"Processing {filename}...")
        text = extract_text_from_pdf(file_path)
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": filename}))
    return docs

def setup_vector_db():
    docs = load_documents()
    if not docs:
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_docs = text_splitter.split_documents(docs)

    # Updated embeddings import (no deprecation warning)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Chroma automatically persists if persist_directory is set
    vectordb = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )

    print(f"Vector database updated with {len(split_docs)} chunks.")
    return vectordb

def initialize_rag_system():
    global rag_vector_db, retriever
    
    # Build vector DB only if not yet built
    if not os.path.exists(VECTOR_DB_PATH):
        print("Building vector DB (first time)...")
        rag_vector_db = setup_vector_db()
    else:
        print("Loading existing vector DB...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        rag_vector_db = Chroma(
            embedding_function=embeddings,
            persist_directory=VECTOR_DB_PATH
        )
    
    # Cache the retriever object for faster queries
    retriever = rag_vector_db.as_retriever(search_kwargs={"k": 5})  # Increased k to get more context
    print("RAG system initialized with cached retriever")

def query_school_info(query_text):
    global retriever
    
    if not retriever:
        print("RAG system not initialized. Please call initialize_rag_system() first.")
        return ""
    
    try:
        # Use the cached retriever for fast queries
        results = retriever.invoke(query_text)

        if results:
            # Extract and format context with source information
            context_parts = []
            for doc in results:
                source = doc.metadata.get('source', 'Unknown document')
                content = doc.page_content
                context_parts.append(f"[From {source}]: {content}")
            
            context = "\n\n".join(context_parts)
            return context
        return ""
    except Exception as e:
        print(f"Error querying vector DB: {e}")
        return ""

# -----------------------------
# Audio Recording Setup
# -----------------------------
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# -----------------------------
# Init Whisper Model
# -----------------------------
whisper_model = WhisperModel("base", device="cuda" if torch.cuda.is_available() else "cpu", compute_type="float16")

# -----------------------------
# Improved TTS Model Initialization
# -----------------------------
def init_tts_model(model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
    use_gpu = torch.cuda.is_available()
    tts_model = None

    try:
        if use_gpu:
            print("[TTS] Loading model on GPU with optimized settings...")
            torch.cuda.empty_cache()
            gc.collect()
            tts_model = TTS(model_name, gpu=True)
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tts_model.tts_to_file(text="Hello", file_path=tmp.name, speaker_wav=REFERENCE_VOICE, language="en")
                    os.unlink(tmp.name)
            except Exception:
                pass
            print("[TTS] Model loaded successfully on GPU")
        else:
            print("[TTS] Loading model on CPU...")
            tts_model = TTS(model_name, gpu=False)
            print("[TTS] Model loaded on CPU successfully")
    except Exception as e:
        print(f"[TTS] Error loading model: {e}")
        if use_gpu:
            print("[TTS] Falling back to CPU...")
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
            tts_model = TTS(model_name, gpu=False)

    return tts_model

tts_model = init_tts_model()

# -----------------------------
# Init pygame for audio playback
# -----------------------------
pygame.mixer.init()
pygame.init()
pygame.mixer.set_num_channels(8)

# -----------------------------
# Word-based Text Chunking for Smooth Playback
# -----------------------------
def split_text_into_tts_chunks(text, max_words_per_chunk=35, min_words_per_chunk=5):
    text = re.sub(r'(\d)\.\s', r'\1<dot> ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []

    sentence_endings = r'(?<=[.,!?:;])\s+'
    sentences = re.split(sentence_endings, text)

    chunks = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue

        if len(words) <= max_words_per_chunk:
            chunks.append(sentence.strip())
            continue

        current = []
        for w in words:
            current.append(w)
            if (len(current) >= min_words_per_chunk and
                (len(current) >= max_words_per_chunk or w.endswith(('.', '!', '?')))):
                chunks.append(" ".join(current).strip())
                current = []

        if current:
            if len(current) < min_words_per_chunk and chunks:
                chunks[-1] = chunks[-1] + " " + " ".join(current)
            else:
                chunks.append(" ".join(current).strip())

    chunks = [c for c in chunks if c]
    print(f"[TTS] Split text into {len(chunks)} word-based chunks")
    return chunks

# -----------------------------
# TTS Queues & State
# -----------------------------
tts_generation_queue = queue.Queue()
playback_queue = queue.Queue()
is_playing = False
is_generating = False
interrupt_playback = False
interrupt_generation = False
current_tts_text = ""

# -----------------------------
# TTS Generation Worker
# -----------------------------
def tts_generation_worker():
    global is_generating, interrupt_generation
    while True:
        text = tts_generation_queue.get()
        if text is None:
            tts_generation_queue.task_done()
            break

        is_generating = True
        interrupt_generation = False

        try:
            chunks = split_text_into_tts_chunks(text)
            for i, chunk in enumerate(chunks):
                if interrupt_generation:
                    print("[TTS] Generation interrupted")
                    break

                print(f"[TTS] Generating chunk {i+1}/{len(chunks)}: '{chunk}'")
                if torch.cuda.is_available():
                    try:
                        torch.cuda.empty_cache()
                        gc.collect()
                    except Exception:
                        pass

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    temp_filename = tmp.name

                try:
                    tts_model.tts_to_file(
                        text=chunk,
                        file_path=temp_filename,
                        speaker_wav=REFERENCE_VOICE,
                        language="en"
                    )

                    if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                        playback_queue.put((temp_filename, chunk))
                        print(f"[TTS] Chunk {i+1} queued for playback")
                    else:
                        print(f"[TTS] Chunk {i+1} generation failed (empty file)")
                        try:
                            os.unlink(temp_filename)
                        except Exception:
                            pass

                except Exception as e:
                    print(f"[TTS] Error generating chunk {i+1}: {e}")
                    try:
                        if os.path.exists(temp_filename):
                            os.unlink(temp_filename)
                    except Exception:
                        pass
                    continue

                time.sleep(0.02)

        except Exception as e:
            print("[TTS] Generation worker error:", e)
        finally:
            is_generating = False
            tts_generation_queue.task_done()

# -----------------------------
# TTS Playback Worker
# -----------------------------
def tts_playback_worker():
    global is_playing, interrupt_playback, current_tts_text
    while True:
        item = playback_queue.get()
        if item is None:
            playback_queue.task_done()
            break

        filename, chunk_text = item
        try:
            sound = pygame.mixer.Sound(filename)
            channel = pygame.mixer.find_channel()
            if channel is None:
                channel = pygame.mixer.Channel(0)

            is_playing = True
            current_tts_text = chunk_text

            channel.play(sound)
            while channel.get_busy() and not interrupt_playback:
                time.sleep(0.01)

            if interrupt_playback:
                try:
                    channel.stop()
                except Exception:
                    pass
                print("[TTS] Playback interrupted by user")

        except Exception as e:
            print(f"[TTS] Playback error: {e}")

        finally:
            try:
                if os.path.exists(filename):
                    os.unlink(filename)
            except Exception:
                pass

            is_playing = False
            current_tts_text = ""
            playback_queue.task_done()

# Start TTS threads
tts_gen_thread = threading.Thread(target=tts_generation_worker, daemon=True)
tts_play_thread = threading.Thread(target=tts_playback_worker, daemon=True)
tts_gen_thread.start()
tts_play_thread.start()

# -----------------------------
# speak() helper
# -----------------------------
def speak(text):
    global interrupt_playback, interrupt_generation, is_playing, is_generating

    if not text or not text.strip():
        return

    if is_playing or is_generating:
        interrupt_playback = True
        interrupt_generation = True
        time.sleep(0.05)

        while not tts_generation_queue.empty():
            try:
                _ = tts_generation_queue.get_nowait()
                tts_generation_queue.task_done()
            except queue.Empty:
                break

        while not playback_queue.empty():
            try:
                item = playback_queue.get_nowait()
                if item and isinstance(item, tuple) and len(item) >= 1:
                    fn = item[0]
                    try:
                        if os.path.exists(fn):
                            os.unlink(fn)
                    except Exception:
                        pass
                playback_queue.task_done()
            except queue.Empty:
                break

        interrupt_playback = False
        interrupt_generation = False

    tts_generation_queue.put(text)

# -----------------------------
# Speech recording and recognition
# -----------------------------
def record_audio_while_key_pressed():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Hold ENTER to record... Release to stop")
    frames = []

    while not keyboard.is_pressed('enter'):
        time.sleep(0.01)

    print("Recording... Speak now!")
    while keyboard.is_pressed('enter'):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        time.sleep(0.01)

    print("Finished recording")
    stream.stop_stream()
    stream.close()
    p.terminate()

    if not frames:
        return None

    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wf = wave.open(temp_file.name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return temp_file.name

def listen(max_retries=MAX_RETRIES):
    for _ in range(max_retries):
        try:
            print("Press and hold ENTER to start recording...")
            audio_file = record_audio_while_key_pressed()
            if audio_file is None:
                print("No audio recorded. Try again.")
                continue

            segments, info = whisper_model.transcribe(audio_file, beam_size=5, language="en")
            try:
                os.unlink(audio_file)
            except Exception:
                pass

            text = " ".join([segment.text for segment in segments]).strip()
            if text:
                print("You said:", text)
                return text
            else:
                print("No speech detected. Try again.")
        except Exception as e:
            print(f"Error in speech recognition: {e}")

    print("No valid input detected. Moving on...")
    return None

# -----------------------------
# Send to LM Studio with RAG Context
# -----------------------------
def send_to_lm_studio(prompt):
    # Query RAG system for relevant information
    rag_context = query_school_info(prompt)
    
    system_prompt = """You are an AI assistant for University of Batangas. Provide accurate information based on the provided context.
- Speak in a clear, professional, and helpful tone.
- Use the provided context information when relevant to answer questions accurately.
- If the context doesn't contain the answer, say you don't have that information.
- Be specific and provide step-by-step instructions when appropriate.
- Format your response in a way that's easy to understand and follow."""

    # Build the message history with RAG context
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add RAG context if available
    if rag_context:
        messages.append({"role": "system", "content": f"Relevant information from University of Batangas documents:\n{rag_context}"})
    
    # Add the current user prompt
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "dolphin-2.2.1-mistral-7b",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 400,  # Increased to allow for more detailed responses
        "stream": False
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        print("LM Studio API error:", e)
        return "Sorry, I cannot connect to my AI model right now."

# -----------------------------
# Main loop
# -----------------------------
if __name__ == "__main__":
    # Initialize RAG system once at startup
    print("Initializing RAG system...")
    initialize_rag_system()
    
    print("AI assistant is ready!")
    print("Press and hold ENTER to speak, release to stop recording")

    try:
        while True:
            if is_playing:
                if keyboard.is_pressed('enter'):
                    print("Interrupting playback...")
                    interrupt_playback = True
                    interrupt_generation = True

                    while not tts_generation_queue.empty():
                        try:
                            _ = tts_generation_queue.get_nowait()
                            tts_generation_queue.task_done()
                        except queue.Empty:
                            break

                    while not playback_queue.empty():
                        try:
                            item = playback_queue.get_nowait()
                            if item and isinstance(item, tuple) and len(item) > 0:
                                try:
                                    if os.path.exists(item[0]):
                                        os.unlink(item[0])
                                except Exception:
                                    pass
                            playback_queue.task_done()
                        except queue.Empty:
                            break

                    time.sleep(0.05)
                    print("Recording... Speak now!")
                    audio_file = record_audio_while_key_pressed()

                    if audio_file:
                        segments, info = whisper_model.transcribe(audio_file, beam_size=5, language="en")
                        try:
                            os.unlink(audio_file)
                        except Exception:
                            pass
                        text = " ".join([segment.text for segment in segments]).strip()
                        if text:
                            print("You said:", text)
                            reply_text = send_to_lm_studio(text)
                            print("Brahmy replied:", reply_text)
                            speak(reply_text)
                        else:
                            print("No speech detected.")

                    while keyboard.is_pressed('enter'):
                        time.sleep(0.01)

                    interrupt_playback = False
                    interrupt_generation = False
                else:
                    time.sleep(0.05)
            else:
                if keyboard.is_pressed('enter'):
                    user_input = listen()
                    if user_input:
                        reply_text = send_to_lm_studio(user_input)
                        print("Brahmy replied:", reply_text)
                        speak(reply_text)
                else:
                    time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting AI assistant...")

    finally:
        try:
            tts_generation_queue.put(None)
        except Exception:
            pass
        try:
            playback_queue.put(None)
        except Exception:
            pass

        try:
            tts_gen_thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            tts_play_thread.join(timeout=1.0)
        except Exception:
            pass

        while not playback_queue.empty():
            try:
                item = playback_queue.get_nowait()
                if item and isinstance(item, tuple) and item[0]:
                    try:
                        if os.path.exists(item[0]):
                            os.unlink(item[0])
                    except Exception:
                        pass
                playback_queue.task_done()
            except queue.Empty:
                break

        print("Shutdown complete.")