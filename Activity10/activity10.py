from faster_whisper import WhisperModel
import asyncio
import time
import threading
import queue
import os
import re
import torch
import tempfile
import pyaudio
import wave
import keyboard
import json
from collections import deque
import numpy as np
import sounddevice as sd
import chromadb
from sentence_transformers import SentenceTransformer
import PyPDF2
import hashlib
from typing import Dict, List, Tuple
import pickle

# -----------------------------
# Config
# -----------------------------
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
REFERENCE_VOICE = "reference.wav"
MODEL_PATH = r

# RAG Configuration
PDF_FOLDER = "school_documents"
VECTOR_DB_PATH = "chroma_db"
EMBEDDING_CACHE_FILE = "embedding_cache.pkl"

# Audio settings
SAMPLE_RATE = 24000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
WHISPER_RATE = 16000

# -----------------------------
# ULTRA-FAST RAG COMPONENTS
# -----------------------------
class UltraFastDocumentRAG:
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.is_ready = False
        
        # HIGH-PERFORMANCE CACHING SYSTEM
        self.embedding_cache: Dict[str, List[float]] = {}
        self.query_cache: Dict[str, str] = {}
        self.school_keywords = None
        
        # PRE-COMPUTED EMBEDDINGS
        self.precomputed_query_embeddings: Dict[str, List[float]] = {}
        
        # Load cache if exists
        self._load_embedding_cache()
        
        self.init_thread = threading.Thread(target=self._initialize_rag, daemon=True)
        self.init_thread.start()
    
    def _load_embedding_cache(self):
        """Load embedding cache from file"""
        try:
            cache_path = os.path.abspath(EMBEDDING_CACHE_FILE)
            print(f"[RAG] 🔍 Looking for cache file: {cache_path}")
            
            if os.path.exists(cache_path):
                print(f"[RAG] 📦 Cache file found, loading...")
                with open(cache_path, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                print(f"[RAG] ✅ Loaded {len(self.embedding_cache)} cached embeddings")
            else:
                print(f"[RAG] ⚠️ No cache file found at {cache_path}")
                self.embedding_cache = {}
        except Exception as e:
            print(f"[RAG] ❌ Cache load error: {e}")
            self.embedding_cache = {}
    
    def _save_embedding_cache(self):
        """Save embedding cache to file"""
        try:
            cache_path = os.path.abspath(EMBEDDING_CACHE_FILE)
            print(f"[RAG] 💾 Saving cache to: {cache_path}")
            print(f"[RAG] 💾 Cache size: {len(self.embedding_cache)} embeddings")
            
            with open(cache_path, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            print(f"[RAG] ✅ Cache saved successfully!")
        except Exception as e:
            print(f"[RAG] ❌ Cache save error: {e}")
    
    def _initialize_rag(self):
        """Initialize RAG system in background"""
        try:
            print("[RAG] 🚀 Initializing ULTRA-FAST document knowledge base...")
            
            # DEBUG: Print current working directory
            print(f"[RAG] 📍 Current directory: {os.getcwd()}")
            print(f"[RAG] 📁 Looking for PDF folder: {PDF_FOLDER}")
            
            # Check if PDF folder exists - FIXED PATH CHECK
            pdf_folder_path = os.path.abspath(PDF_FOLDER)
            print(f"[RAG] 📁 Absolute PDF path: {pdf_folder_path}")
            print(f"[RAG] 📁 Folder exists: {os.path.exists(pdf_folder_path)}")
            
            if not os.path.exists(pdf_folder_path):
                print(f"[RAG] ❌ PDF folder '{pdf_folder_path}' not found!")
                # List files in current directory to help debug
                print(f"[RAG] 📋 Files in current directory:")
                for file in os.listdir('.'):
                    print(f"      {file}")
                return
            
            # Check PDF files
            pdf_files = [f for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]
            print(f"[RAG] 📄 Found {len(pdf_files)} PDF files: {pdf_files}")
            
            if not pdf_files:
                print(f"[RAG] ⚠️ No PDF files found in '{pdf_folder_path}'")
                return
            
            # STRICT SCHOOL KEYWORDS ONLY - NO GENERAL WORDS
            self.school_keywords = [
                 # University specific
                 "university of batangas", "ub", "western philippine colleges", "wpc",
                
                 # Enrollment and admission
                 "enroll", "enrollment", "admission", "admit", "registrar", "application",
                 "requirements", "entrance", "qualification", "eligible", "deadline",
                 "freshmen", "transferee", "transfer", "new student", "old student",
                 "college freshmen", "shifter", "exchange student",
                
                 # Academic programs
                 "program", "course", "curriculum", "degree", "bachelor", "master", 
                 "doctorate", "undergraduate", "graduate", "major", "subject",
                
                 # Financial
                 "tuition", "fee", "payment", "scholarship", "financial aid", "grant",
                 "discount", "budget", "cashier", "accounting", "assessment",
                
                 # Academic structure
                 "faculty", "department", "college", "professor", "instructor", "teacher",
                 "dean", "chairperson", "administrator",
                
                 # Facilities
                 "library", "laboratory", "classroom", "campus", "facility", "building",
                 "clinic", "bookstore", "it center", "guidance office",
                
                 # University information
                 "vision", "mission", "philosophy", "history", "founder", "background",
                 "values", "core values", "objective", "goal", "purpose", "heritage",
                 "tradition", "legacy", "establishment", "foundation", "attributes",
                
                 # Student types
                 "student", "alumni", "graduate", "freshman", "sophomore", "junior", 
                 "senior", "high school", "elementary", "junior high", "senior high",
                 "nkp", "kinder", "grade", "pupil",
                
                 # Procedures and forms
                 "procedure", "process", "step", "form", "eaf", "enrollment assessment",
                 "registration", "encode", "advising", "subject", "schedule"
                
            ]
            
            print(f"[RAG] 🔑 Loaded {len(self.school_keywords)} STRICT school keywords")
            
            # Load embedding model ONCE
            print("[RAG] 🔄 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[RAG] ✅ Embedding model loaded")
            
            # Setup ChromaDB
            print(f"[RAG] 🗄️ Setting up ChromaDB at: {os.path.abspath(VECTOR_DB_PATH)}")
            self.chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            
            # Check if collection exists and is up to date
            if self._is_vector_db_current():
                try:
                    print("[RAG] 🔍 Getting existing collection...")
                    self.collection = self.chroma_client.get_collection(name="school_info")
                    print("[RAG] ✅ Using existing vector database")
                    self.is_ready = True
                    
                    # PRE-WARM with common queries
                    self._pre_warm_common_queries()
                    return
                except Exception as e:
                    print(f"[RAG] ⚠️ Cannot get existing collection: {e}")
                    pass
            
            # Process PDFs and create vector database
            print("[RAG] 🔄 Processing PDFs...")
            if self._process_pdfs_fast():
                self.is_ready = True
                print("[RAG] ✅ Document knowledge base ready!")
                
                # PRE-WARM with common queries
                self._pre_warm_common_queries()
            else:
                print("[RAG] ⚠️ Running without document knowledge base.")
                
        except Exception as e:
            print(f"[RAG] ❌ Initialization error: {e}")
            import traceback
            traceback.print_exc()
    
    def _pre_warm_common_queries(self):
        """Pre-compute embeddings for common queries"""
        common_queries = [
            "what is the school history",
            "admission requirements",
            "tuition fee payment",
            "academic programs offered",
            "scholarship opportunities",
            "school vision and mission",
            "faculty information",
            "campus facilities"
        ]
        
        print("[RAG] 🔥 Pre-warming common query embeddings...")
        for query in common_queries:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            if query_hash not in self.precomputed_query_embeddings:
                embedding = self.embedding_model.encode([query]).tolist()[0]
                self.precomputed_query_embeddings[query_hash] = embedding
        
        print(f"[RAG] ✅ Pre-warmed {len(common_queries)} common queries")
    
    def _is_vector_db_current(self):
        """ULTRA-FAST check if vector DB is current"""
        vector_db_path = os.path.abspath(VECTOR_DB_PATH)
        print(f"[RAG] 🔍 Checking vector DB at: {vector_db_path}")
        print(f"[RAG] 🔍 Vector DB exists: {os.path.exists(vector_db_path)}")
        
        if not os.path.exists(vector_db_path):
            return False
        
        try:
            db_time = os.path.getmtime(vector_db_path)
            pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
            if not pdf_files:
                return False
            
            # Fast file time comparison
            for pdf_file in pdf_files:
                pdf_time = os.path.getmtime(os.path.join(PDF_FOLDER, pdf_file))
                if pdf_time > db_time:
                    print(f"[RAG] ⚠️ PDF {pdf_file} is newer than DB, need to update")
                    return False
            return True
        except Exception as e:
            print(f"[RAG] ❌ Error checking DB currency: {e}")
            return False
    
    def _extract_text_from_pdf_fast(self, pdf_path):
        """FAST PDF text extraction with optimization"""
        text = ""
        try:
            print(f"[RAG] 📖 Reading PDF: {os.path.basename(pdf_path)}")
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                # Process first 20 pages only for speed (most relevant content)
                max_pages = min(20, len(reader.pages))
                print(f"[RAG]   Processing {max_pages} pages...")
                
                for i in range(max_pages):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        # Fast text cleaning
                        page_text = re.sub(r'\s+', ' ', page_text).strip()
                        if len(page_text) > 50:  # Only add substantial text
                            text += page_text + "\n"
            
            print(f"[RAG]   Extracted {len(text)} characters")
        except Exception as e:
            print(f"[RAG] ❌ Error reading PDF {pdf_path}: {e}")
        return text
    
    def _split_text_into_chunks_fast(self, text, chunk_size=400, overlap=30):
        """ULTRA-FAST text chunking"""
        text = re.sub(r'\s+', ' ', text).strip()
        words = text.split()
        chunks = []
        
        # Fast chunking with minimal operations
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk) > 50:  # Only substantial chunks
                chunks.append(chunk)
                
            # Early stop if we have enough chunks
            if len(chunks) >= 100:  # Max 100 chunks per document
                break
                
        return chunks
    
    def _process_pdfs_fast(self):
        """HIGH-SPEED PDF processing"""
        try:
            all_chunks = []
            pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
            
            if not pdf_files:
                print(f"[RAG] ❌ No PDF files found in '{PDF_FOLDER}'")
                return False
            
            print(f"[RAG] 🚀 Fast-processing {len(pdf_files)} PDF files...")
            
            for filename in pdf_files:
                file_path = os.path.join(PDF_FOLDER, filename)
                print(f"[RAG] 📄 Processing {filename}...")
                
                text = self._extract_text_from_pdf_fast(file_path)
                if text:
                    chunks = self._split_text_into_chunks_fast(text)
                    # Add filename context to chunks
                    for chunk in chunks:
                        all_chunks.append(f"[From {filename}] {chunk}")
                    print(f"[RAG]   Created {len(chunks)} chunks")
                else:
                    print(f"[RAG]   No text extracted from {filename}")
            
            if not all_chunks:
                print("[RAG] ❌ No text extracted from PDFs")
                return False
            
            print(f"[RAG] ✅ Created {len(all_chunks)} total chunks from all PDFs")
            
            # Delete existing collection if any
            try:
                print("[RAG] 🗑️ Deleting old collection...")
                self.chroma_client.delete_collection(name="school_info")
                print("[RAG] ✅ Old collection deleted")
            except Exception as e:
                print(f"[RAG] ℹ️ No existing collection to delete: {e}")
            
            # Create new collection
            print("[RAG] 🆕 Creating new collection...")
            self.collection = self.chroma_client.create_collection(name="school_info")
            print("[RAG] ✅ New collection created")
            
            # BATCH PROCESS embeddings with caching
            batch_size = 50  # Reduced for stability
            total_batches = (len(all_chunks) + batch_size - 1) // batch_size
            
            print(f"[RAG] 🔄 Processing {total_batches} batches...")
            
            for batch_idx in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[batch_idx:batch_idx + batch_size]
                batch_embeddings = []
                
                print(f"[RAG]   Processing batch {batch_idx//batch_size + 1}/{total_batches} ({len(batch_chunks)} chunks)")
                
                # Compute or get cached embeddings
                for chunk in batch_chunks:
                    chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                    if chunk_hash in self.embedding_cache:
                        batch_embeddings.append(self.embedding_cache[chunk_hash])
                    else:
                        embedding = self.embedding_model.encode([chunk]).tolist()[0]
                        self.embedding_cache[chunk_hash] = embedding
                        batch_embeddings.append(embedding)
                
                # Add to vector database
                for i, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                    self.collection.add(
                        ids=[f"chunk_{batch_idx + i}"],
                        embeddings=[embedding],
                        documents=[chunk]
                    )
                
                print(f"[RAG]   ✅ Batch {batch_idx//batch_size + 1} completed")
            
            # Save cache
            print("[RAG] 💾 Saving embeddings cache...")
            self._save_embedding_cache()
            print(f"[RAG] ✅ Saved {len(self.embedding_cache)} embeddings to cache")
            
            return True
            
        except Exception as e:
            print(f"[RAG] ❌ Error processing PDFs: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _is_school_related_ultra_fast(self, query_text):
        """STRICT school topic detection - NO FALSE POSITIVES"""
        if not self.school_keywords:
            return False
        
        query_lower = query_text.lower()
        
        # STRICT CHECKING - require school context
        # Check if query contains school-related words in meaningful context
        school_context_found = False
        matched_keywords = []
        
        for keyword in self.school_keywords:
            if keyword in query_lower:
                # Additional context checking for ambiguous words
                if keyword == "history":
                    # Only match "history" if it's clearly school-related
                    if any(ctx in query_lower for ctx in ["school", "university", "college", "institution", "academic"]):
                        school_context_found = True
                        matched_keywords.append(keyword)
                elif keyword == "program":
                    # Only match "program" if it's academic
                    if any(ctx in query_lower for ctx in ["academic", "course", "study", "school", "university"]):
                        school_context_found = True
                        matched_keywords.append(keyword)
                else:
                    # For most keywords, direct match is sufficient
                    school_context_found = True
                    matched_keywords.append(keyword)
        
        if school_context_found:
            print(f"[RAG] 🔑 STRICT School context confirmed. Matched keywords: {matched_keywords}")
            return True
        else:
            print(f"[RAG] 🚫 Query rejected - no clear school context: '{query_text}'")
            return False
    
    def _get_query_embedding_fast(self, query_text):
        """HIGH-SPEED embedding with caching"""
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        
        # Check precomputed first
        if query_hash in self.precomputed_query_embeddings:
            print(f"[RAG] ⚡ Using precomputed embedding for query")
            return self.precomputed_query_embeddings[query_hash]
        
        # Check cache
        if query_hash in self.embedding_cache:
            print(f"[RAG] ⚡ Using cached embedding for query")
            return self.embedding_cache[query_hash]
        
        # Compute new embedding
        print(f"[RAG] 🔄 Computing new embedding for query")
        embedding = self.embedding_model.encode([query_text]).tolist()[0]
        self.embedding_cache[query_hash] = embedding
        return embedding
    
    def query_documents_ultra_fast(self, query_text, max_results=2):
        """ULTRA-FAST document querying"""
        if not self.is_ready or not self.collection:
            print(f"[RAG] ❌ RAG not ready or no collection")
            return ""
        
        start_time = time.time()
        
        try:
            # STRICT topic detection
            print(f"[RAG] 🔍 STRICT Checking if query is school-related: '{query_text}'")
            if not self._is_school_related_ultra_fast(query_text):
                print(f"[RAG] 🚫 Query REJECTED - not school-related")
                return "NOT_SCHOOL_RELATED"  # Special marker for non-school queries
            
            # Check query cache first
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            if query_hash in self.query_cache:
                print(f"[RAG] ⚡ CACHE HIT for query")
                return self.query_cache[query_hash]
            else:
                print(f"[RAG] 🔄 CACHE MISS for query")
            
            # FAST embedding
            query_embedding = self._get_query_embedding_fast(query_text)
            
            # FAST vector search
            print(f"[RAG] 🔍 Performing vector search...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            if results['documents'] and results['documents'][0]:
                context = " ".join(results['documents'][0])
                
                # Cache the result
                self.query_cache[query_hash] = context
                
                query_time = time.time() - start_time
                print(f"[RAG] ✅ Found context in {query_time:.3f}s ({len(context)} chars)")
                return context
            else:
                print(f"[RAG] ❌ No documents found in vector search")
                return "NO_DOCUMENTS_FOUND"
            
        except Exception as e:
            print(f"[RAG] ❌ Query error: {e}")
            return ""

# Initialize ULTRA-FAST RAG system
document_rag = UltraFastDocumentRAG()



# ULTRA-FAST STT STREAMING
# -----------------------------
class UltraFastRealTimeSTT:
    def __init__(self):
        self.whisper_model = WhisperModel("base", device="cuda", compute_type="float16")
        self.is_recording = False
        self.audio_buffer = []
        self.stream = None
        self.p = None
        self.recording_start_time = 0
        
        # PRE-WARM WHISPER with a dummy transcription
        print("[STT] 🔥 Pre-warming Whisper...")
        self._pre_warm_whisper()
        print("[STT] 🎯 Ultra-fast STT ready!")
    
    def _pre_warm_whisper(self):
        """Pre-warm Whisper without file permission issues"""
        try:
            # Create a proper temporary file that gets auto-deleted
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                # Generate 1 second of silence
                dummy_audio = np.zeros(16000, dtype=np.int16)
                
                # Write WAV file properly
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(dummy_audio.tobytes())
                
                # Pre-warm with fast settings
                segments = list(self.whisper_model.transcribe(
                    temp_file.name, 
                    beam_size=1, 
                    best_of=1, 
                    without_timestamps=True
                ))
                
        except Exception as e:
            print(f"[STT] ⚠️ Pre-warming skipped: {e}")
    
    def start_recording(self):
        """Start recording and transcription immediately"""
        self.is_recording = True
        self.audio_buffer = []
        self.recording_start_time = time.time()
        
        # Start audio stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=WHISPER_RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        print(f"[STT_TIMING] 🔴 Recording STARTED - Speak now...")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for real-time streaming"""
        if self.is_recording:
            self.audio_buffer.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self):
        """Stop recording and return transcribed text INSTANTLY"""
        if not self.is_recording:
            return ""
        
        stop_start_time = time.time()
        self.is_recording = False
        
        # Stop stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        
        # ULTRA-FAST transcription with optimized settings
        if self.audio_buffer:
            # Use proper temp file handling
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                # Write audio data to file
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(WHISPER_RATE)
                    wf.writeframes(b''.join(self.audio_buffer))
                
                # ULTRA-FAST transcription (30-40% faster)
                segments, info = self.whisper_model.transcribe(
                    temp_filename, 
                    language="en",
                    beam_size=1,
                    best_of=1,
                    without_timestamps=True,
                    patience=1
                )
                
                text = " ".join([segment.text for segment in segments]).strip()
                
            finally:
                # Always clean up the temp file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
            
            # CLEAR CUDA CACHE for XTTS
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            total_stop_time = time.time() - stop_start_time
            print(f"[STT_TIMING] ✅ STT processed in {total_stop_time:.3f}s")
            
            return text
        
        return ""

# Initialize Ultra-Fast STT
realtime_stt = UltraFastRealTimeSTT()

# -----------------------------
# SIMPLE Word Fixer
# -----------------------------
class SimpleWordFixer:
    def __init__(self):
        self.common_fixes = [
            (r'\bdont\b', 'don\'t'),
            (r'\bcant\b', 'can\'t'),
            (r'\bwont\b', 'won\'t'),
            (r'\bim\b', 'I\'m'),
            (r'\byoure\b', 'you\'re'),
            (r'\btheyre\b', 'they\'re'),
            (r'\bwere\b', 'we\'re'),
            (r'\bthats\b', 'that\'s'),
            (r'\bwhats\b', 'what\'s'),
            (r'\bwheres\b', 'where\'s'),
        ]
    
    def fix_text(self, text):
        """Apply simple fixes"""
        if not text:
            return text
        
        for pattern, replacement in self.common_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Clean up spaces
        text = re.sub(r'\s+([.,!?;])', r'\1', text)
        text = re.sub(r'([.,!?;])(\w)', r'\1 \2', text)
        
        return text

# -----------------------------
# Audio Player
# -----------------------------
class InstantAudioPlayer:
    def __init__(self):
        self.audio_buffer = np.array([], dtype=np.float32)
        self.is_playing = False
        self.current_stream = None
        self.buffer_lock = threading.Lock()
        print("[Audio] Instant player ready")
    
    def start_streaming(self):
        if self.is_playing:
            return
        
        def audio_callback(outdata, frames, time, status):
            with self.buffer_lock:
                if len(self.audio_buffer) >= frames:
                    outdata[:, 0] = self.audio_buffer[:frames]
                    self.audio_buffer = self.audio_buffer[frames:]
                else:
                    outdata.fill(0)
        
        try:
            self.current_stream = sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=audio_callback,
                blocksize=256,
                latency='low',
                dtype=np.float32
            )
            self.current_stream.start()
            self.is_playing = True
        except Exception as e:
            print(f"[Audio] Stream error: {e}")
    
    def add_audio_chunk(self, audio_chunk):
        if audio_chunk is None or len(audio_chunk) == 0:
            return
        
        try:
            if not isinstance(audio_chunk, np.ndarray):
                audio_chunk = np.array(audio_chunk, dtype=np.float32)
            
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            audio_chunk = audio_chunk.flatten()
            
            max_val = np.max(np.abs(audio_chunk))
            if max_val > 1.0:
                audio_chunk = audio_chunk / max_val
            
            with self.buffer_lock:
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_chunk])
            
            if not self.is_playing and len(self.audio_buffer) >= 512:
                self.start_streaming()
                
        except Exception as e:
            print(f"[Audio] Chunk error: {e}")
    
    def stop_streaming(self):
        self.is_playing = False
        if self.current_stream:
            try:
                self.current_stream.stop()
                self.current_stream.close()
            except:
                pass
            self.current_stream = None
        
        with self.buffer_lock:
            self.audio_buffer = np.array([], dtype=np.float32)

audio_player = InstantAudioPlayer()

# -----------------------------
# ULTRA-OPTIMIZED XTTS Streamer
# -----------------------------
class UltraOptimizedXTTSStreamer:
    def __init__(self):
        self.model = None
        self.gpt_cond_latent = None
        self.speaker_embedding = None
        self.is_ready = False
        self.currently_streaming = False
        self.word_fixer = SimpleWordFixer()
        self.init_thread = threading.Thread(target=self._initialize_model)
        self.init_thread.daemon = True
        self.init_thread.start()
    
    def _initialize_model(self):
        try:
      
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            config = XttsConfig()
            config.load_json(os.path.join(MODEL_PATH, "config.json"))
            
            self.model = Xtts.init_from_config(config)
        
               
               
        
            
            if torch.cuda.is_available():
                print("[XTTS] Using GPU")
                self.model = self.model.to("cuda")
            
            print("[XTTS] Computing voice embeddings...")
            
            if torch.cuda.is_available():
                original_device = next(self.model.parameters()).device
                self.model = self.model.cpu()
            
            self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                audio_path=[REFERENCE_VOICE]
            )
            
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
                if isinstance(self.gpt_cond_latent, list):
                    self.gpt_cond_latent = [latent.to("cuda") for latent in self.gpt_cond_latent]
                else:
                    self.gpt_cond_latent = self.gpt_cond_latent.to("cuda")
                self.speaker_embedding = self.speaker_embedding.to("cuda")
            
            # PRE-WARM XTTS with dummy inference
            print("[XTTS] 🔥 Pre-warming TTS engine...")
            self._pre_warm_tts()
            
            self.is_ready = True
            print("[XTTS] ✅ XTTS-v2 Ready & Pre-warmed!")
            
        except Exception as e:
            
            try:
               
                
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
                
                self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                    audio_path=[REFERENCE_VOICE]
                )
                
                if torch.cuda.is_available():
                    if isinstance(self.gpt_cond_latent, list):
                        self.gpt_cond_latent = [latent.to("cuda") for latent in self.gpt_cond_latent]
                    else:
                        self.gpt_cond_latent = self.gpt_cond_latent.to("cuda")
                    self.speaker_embedding = self.speaker_embedding.to("cuda")
                
                # Pre-warm fallback
                self._pre_warm_tts()
                
                self.is_ready = True
                print("[XTTS] ✅ XTTS-v2 Ready (Standard Loading)")
                
            except Exception as fallback_error:
                print(f"[XTTS] ❌ Fallback failed: {fallback_error}")
    
    def _pre_warm_tts(self):
        """Pre-warm TTS to hide 1.5s warm-up cost"""
        try:
        
            # Consume the dummy chunks without playing
            for chunk in dummy_chunks:
                if chunk is not None:
                    pass
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            print("[XTTS] ✅ Pre-warming complete!")
        except Exception as e:
            print(f"[XTTS] ⚠️ Pre-warming skipped: {e}")
    
    def wait_until_ready(self):
        self.init_thread.join(timeout=60)
        return self.is_ready
    
    def stream_text(self, text, audio_callback=None):
        if not self.is_ready or self.currently_streaming:
            return False
        
        clean_text = self._clean_text(text)
        if not clean_text:
            return False
        
        self.currently_streaming = True
        try:
            print(f"[XTTS] 🔊 Streaming: '{clean_text}'")
            
            tts_start_time = time.time()
            chunks = self.model.inference_stream(
                text=clean_text,
                language="en",
                gpt_cond_latent=self.gpt_cond_latent,
                speaker_embedding=self.speaker_embedding,
                temperature=XTTS_TEMPERATURE,
                length_penalty=XTTS_LENGTH_PENALTY,
                repetition_penalty=XTTS_REPETITION_PENALTY,
                top_k=XTTS_TOP_K,
                top_p=XTTS_TOP_P,
                speed=XTTS_SPEED,
                enable_text_splitting=ENABLE_TEXT_SPLITTING,
                stream_chunk_size=STREAM_CHUNK_SIZE,
            )
            
            chunk_count = 0
            first_chunk_time = time.time()
            first_chunk_received = False
            
            for chunk in chunks:
                if chunk is not None:
                    if not first_chunk_received:
                        first_chunk_latency = time.time() - first_chunk_time
                        print(f"[XTTS_TIMING] ⚡ First audio chunk in {first_chunk_latency:.3f}s")
                        first_chunk_received = True
                    
                    audio_chunk = self._process_audio_chunk(chunk)
                    if audio_chunk is not None and audio_callback:
                        audio_callback(audio_chunk)
                    chunk_count += 1
            
            total_tts_time = time.time() - tts_start_time
            print(f"[XTTS_TIMING] ✅ Streamed {chunk_count} chunks in {total_tts_time:.3f}s")
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return True
            
        except Exception as e:
            print(f"[XTTS] ❌ Streaming error: {e}")
            return False
        finally:
            self.currently_streaming = False
    
    def _clean_text(self, text):
        if not text:
            return None
        
        text = self.word_fixer.fix_text(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _process_audio_chunk(self, chunk):
        try:
            if isinstance(chunk, torch.Tensor):
                audio_chunk = chunk.cpu().numpy()
            else:
                audio_chunk = np.array(chunk)
            
            audio_chunk = audio_chunk.squeeze().astype(np.float32)
            
            max_val = np.max(np.abs(audio_chunk))
            if max_val > 1.0:
                audio_chunk = audio_chunk / max_val
            
            return audio_chunk
            
        except Exception as e:
            print(f"[XTTS] ❌ Chunk processing error: {e}")
            return None




class AdvancedPipeline:
    def __init__(self):
        self.text_queue = queue.Queue()
        self.is_processing = False
        self.processing_thread = None
        self.sentence_buffer = ""
        self._start_processor()
    
    def _start_processor(self):
        def process_text():
            while True:
                text = self.text_queue.get()
                if text is None:
                    break
                
                self.is_processing = True
                pipeline_start = time.time()
                try:
                    print(f"[Pipeline] 🎯 Text to XTTS: '{text}'")
                    
                    success = tts_model.stream_text(text, audio_player.add_audio_chunk)
                    
                    if not success:
                        print(f"[Pipeline] TTS failed for text")
                    
                    pipeline_time = time.time() - pipeline_start
                    print(f"[PIPELINE_TIMING] ✅ Pipeline processed in {pipeline_time:.3f}s")
                    
                    time.sleep(SENTENCE_DELAY)
                            
                except Exception as e:
                    print(f"[Pipeline] Error: {e}")
                finally:
                    self.is_processing = False
                    self.text_queue.task_done()
        
        self.processing_thread = threading.Thread(target=process_text, daemon=True)
        self.processing_thread.start()
    
    def stream_text(self, text):
        """Stream text chunks as they arrive from LM Studio"""
        if not text or text.strip() == "":
            return
        
        # FILTER OUT CONTEXT MARKERS - FIX FOR SYSTEM PROMPT LEAKAGE
        if any(marker in text for marker in ['###', 'User:', 'AI:', 'System:', 'Jarvis:']):
            return
        
        # Add to sentence buffer
        self.sentence_buffer += text
        
        # Check for sentence boundaries
        sentence_endings = ['.', '!', '?', ',', '\n']
        
        # Process complete sentences
        while any(marker in self.sentence_buffer for marker in sentence_endings):
            # Find the earliest sentence ending
            positions = []
            for marker in sentence_endings:
                pos = self.sentence_buffer.find(marker)
                if pos != -1:
                    positions.append(pos)
            
            if not positions:
                break
                
            end_pos = min(positions) + 1  # Include the punctuation
            
            sentence = self.sentence_buffer[:end_pos].strip()
            self.sentence_buffer = self.sentence_buffer[end_pos:].strip()
            
            if sentence and len(sentence) > 2:  # Minimum length check
                self.text_queue.put(sentence)
                print(f"[STREAMING] 🎯 Queued sentence: '{sentence}'")
    
    def flush_buffer(self):
        """Flush any remaining text in the buffer"""
        if self.sentence_buffer.strip():
            # Filter context markers from buffer too
            if not any(marker in self.sentence_buffer for marker in ['###', 'User:', 'AI:', 'System:', 'Jarvis:']):
                self.text_queue.put(self.sentence_buffer.strip())
                print(f"[STREAMING] 🎯 Flushed buffer: '{self.sentence_buffer.strip()}'")
            self.sentence_buffer = ""
    
    def stop(self):
        self.flush_buffer()
        self.text_queue.put(None)

pipeline = AdvancedPipeline()

# -----------------------------
# OPTIMIZED Conversation Memory
# -----------------------------
class OptimizedConversationMemory:
    def __init__(self, max_items=3):  # Reduced for speed
        self.max_items = max_items
        self.memory = deque(maxlen=max_items)
    
    def add_exchange(self, user_input, ai_response):
        # Clean AI response before storing
        clean_ai_response = self._clean_response(ai_response)
        self.memory.append({
            "user": user_input,
            "ai": clean_ai_response,
            "timestamp": time.time()
        })
    
    def _clean_response(self, response):
        """Remove any system prompts or context markers from responses"""
        if not response:
            return response
        
        # Remove common context markers
        clean_response = re.sub(r'###\s*(User|AI|System|Jarvis):?', '', response)
        clean_response = re.sub(r'^(User|AI|System|Jarvis):?\s*', '', clean_response)
        return clean_response.strip()
    
    def get_smart_context(self):
        """ULTRA-LIGHT context - only last 1-2 exchanges"""
        if len(self.memory) == 0:
            return ""
        
        recent_items = list(self.memory)[-2:]  # Last 2 exchanges for context
        
        context_str = ""
        for item in recent_items:
            user_text = item['user'][:80] + "..." if len(item['user']) > 80 else item['user']
            ai_text = item['ai'][:120] + "..." if len(item['ai']) > 120 else item['ai']
            context_str += f"User: {user_text}\nAI: {ai_text}\n"
        
        return context_str.strip()

conversation_memory = OptimizedConversationMemory()


async def stream_from_lm_studio_async(prompt, text_callback=None):
    global lm_client
    
    lm_start_time = time.time()
    
    if lm_client is None:
        await initialize_lm_client()
    
    context = conversation_memory.get_smart_context()
    
    # ULTRA-STRICT RAG: Get document context if available
    document_context = document_rag.query_documents_ultra_fast(prompt)
    
    # SMART SYSTEM PROMPT BASED ON STRICT RAG RESULT
    if document_context == "NOT_SCHOOL_RELATED":
        # If query is not school-related, use very restrictive prompt
        system_content = "You are an AI assistant that ONLY answers questions about the specific school in the documents. For any non-school questions, respond: 'I specialize only in school-related information such as admission, programs, tuition, and academic matters. Please ask me about our school.' Keep the response very short and direct. Do not answer the actual question."
        use_rag_context = False
        print("[PROMPT] 🚫 NON-SCHOOL QUERY - STRICTLY REJECTED")
    elif document_context == "NO_DOCUMENTS_FOUND":
        # School-related but no documents found
        system_content = "You are a school AI assistant. Respond: 'I don't have specific information about that topic in my school documents. I can help you with admission, programs, tuition, or other school-related matters.'"
        use_rag_context = False
        print("[PROMPT] ❓ SCHOOL QUERY but no documents found")
    elif document_context:
        # If we have document context, use it strictly
        system_content = "You are a helpful school AI assistant. Use ONLY the provided document information to answer. If the information is not in the documents, say 'I don't have that specific information in my school documents.' Do not make up or invent information. Be precise and factual."
        use_rag_context = True
        print("[PROMPT] 📚 SCHOOL QUERY with document context")
    else:
        # Default case
        system_content = "You are a school AI assistant. Respond that you can help with school-related questions about admission, programs, tuition, and academic matters."
        use_rag_context = False
        print("[PROMPT] ℹ️ Default school assistant mode")
    
    messages = [
        {"role": "system", "content": system_content},
    ]
    
    # Add RAG document context if available and relevant
    if use_rag_context and document_context and document_context not in ["NOT_SCHOOL_RELATED", "NO_DOCUMENTS_FOUND"]:
        messages.append({
            "role": "system", 
            "content": f"Use this school document information to answer: {document_context}"
        })
    
    # Add conversation context as separate messages if it exists
    if context:
        context_lines = context.split('\n')
        for line in context_lines:
            if line.startswith('User:'):
                user_content = line.replace('User:', '').strip()
                if user_content and len(user_content) > 3:  # Valid user message
                    messages.append({"role": "user", "content": user_content})
            elif line.startswith('AI:'):
                ai_content = line.replace('AI:', '').strip()
                if ai_content and len(ai_content) > 3:  # Valid AI response
                    messages.append({"role": "assistant", "content": ai_content})
    
    # Add current user message
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "meta-llama-3.1-8b-instruct",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 600,  # Reduced for faster responses
        "stream": True,
        "stop": ["###", "User:", "AI:", "System:"]  # PREVENT CONTEXT LEAKAGE
    }

    print(f"[LM_DEBUG] 🚀 Sending streaming request: {len(prompt)} chars")
    
    full_response = ""
    
    try:
        request_start = time.time()
        
        async with lm_client.stream(
            "POST",
            LM_STUDIO_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        ) as response:
            
            request_time = time.time() - request_start
            print(f"[LM_TIMING] 📤 Request sent in {request_time:.3f}s")
            
            if response.status_code != 200:
                print(f"[LM_DEBUG] ❌ HTTP Error: {response.status_code}")
                return f"Error: {response.status_code}"
            
            first_token_received = False
            token_count = 0
            stream_start = time.time()
            
            async for line in response.aiter_lines():
                if line and line.startswith('data: '):
                    if line == 'data: [DONE]':
                        break
                    try:
                        data = json.loads(line[6:])
                        if 'choices' in data and data['choices']:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                token = delta['content']
                                
                                # FILTER OUT SYSTEM PROMPT AND CONTEXT MARKERS
                                filtered_token = token
                                for marker in ['###', 'User:', 'AI:', 'System:', 'Jarvis:']:
                                    filtered_token = filtered_token.replace(marker, '')
                                
                                if filtered_token.strip():
                                    token_count += 1
                                    
                                    if not first_token_received:
                                        first_token_time = time.time() - stream_start
                                        print(f"[LM_TIMING] ⚡ First token in {first_token_time:.3f}s: '{filtered_token}'")
                                        first_token_received = True
                                    
                                    full_response += filtered_token
                                    
                                    # TRUE STREAMING: Send tokens immediately to TTS pipeline
                                    if text_callback and filtered_token.strip():
                                        text_callback(filtered_token)
                                
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"[LM_DEBUG] Token error: {e}")
                        continue
        
        # Flush any remaining text in the buffer
        if text_callback:
            pipeline.flush_buffer()
        
        total_lm_time = time.time() - lm_start_time
        print(f"[LM_TIMING] ✅ {token_count} tokens in {total_lm_time:.3f}s")
        
        # Clean final response before storing
        clean_response = re.sub(r'###\s*(User|AI|System|Jarvis):?', '', full_response)
        clean_response = re.sub(r'^(User|AI|System|Jarvis):?\s*', '', clean_response)
        
        return clean_response.strip()
        
    except Exception as e:
        print(f"[LM_DEBUG] ❌ Error: {e}")
        return f"Error: {str(e)}"

# -----------------------------
# MAIN LOOP
# -----------------------------
async def main_async():

    
    # Wait for RAG to initialize
    print("[SYSTEM] ⏳ Waiting for RAG system to initialize...")
    time.sleep(2)  # Give RAG time to start
    
    await initialize_lm_client()
    
    print("Initializing pipeline...")
    if tts_model.wait_until_ready():
        print("✅ Pipeline Ready!")
    
    print("\n🎯 Press and hold ENTER to speak - RELEASE for instant send!")
    print("✅ ASK ABOUT: admission, tuition, programs, school history, campus")
    print("🚫 WILL REJECT: stories, jokes, weather, general knowledge")
    
    try:
        while True:
            if not pipeline.is_processing:
                if keyboard.is_pressed('enter'):
                    if not realtime_stt.is_recording:
                        realtime_stt.start_recording()
                    await asyncio.sleep(0.001)
                else:
                    if realtime_stt.is_recording:
                        total_start_time = time.time()
                        user_input = realtime_stt.stop_recording()
                        
                        if user_input and user_input.strip():
                            print(f"👤 You: {user_input}")
                            
                            lm_start = time.time()
                            ai_response = await stream_from_lm_studio_async(
                                user_input, 
                                pipeline.stream_text  # TRUE STREAMING CALLBACK
                            )
                            lm_total_time = time.time() - lm_start
                            
                            conversation_memory.add_exchange(user_input, ai_response)
                            
                            total_end_to_end = time.time() - total_start_time
                            print(f"[TOTAL_TIMING] 🚀 END-TO-END: {total_end_to_end:.3f}s")
                            print("=" * 50)
                    
                    await asyncio.sleep(0.001)
            else:
                await asyncio.sleep(0.001)
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if realtime_stt.is_recording:
            realtime_stt.stop_recording()
        pipeline.stop()
        audio_player.stop_streaming()
        await close_lm_client()
        print("✅ Shutdown complete")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()