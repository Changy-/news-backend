import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger("uvicorn")

load_dotenv()

from google import genai as new_genai
from google.genai import types
import struct
import traceback
import time

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger("uvicorn")

def generate_audio(text):
    """
    Generates audio from text using Gemini 2.0 Flash.
    Returns: bytes (audio data) with WAV header.
    """
    if not GEMINI_API_KEY:
        print("DEBUG: Missing Gemini API Key for audio", flush=True)
        return None

    if not text or not text.strip():
        print("DEBUG: Text for audio generation is empty", flush=True)
        return None

    try:
        start_time = time.time()
        client = new_genai.Client(api_key=GEMINI_API_KEY)
        
        # Explicit config to avoid "Model tried to generate text" error
        config = types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck' # Or 'Aoede', 'Charon', 'Fenrir', 'Kore'
                    )
                )
            )
        )

        # Prefix with explicit TTS instruction to prevent text generation
        tts_prompt = f"Read the following text aloud exactly as written: {text}"

        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-tts',
            contents=tts_prompt,
            config=config
        )
        tts_latency = time.time() - start_time
        print(f"LATENCY: TTS API call took {tts_latency:.2f}s for {len(text)} chars", flush=True)
        # Verify structure: output should be in parts -> inline_data
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                pcm_data = part.inline_data.data
                
                # Gemini TTS default is 24kHz, 1 channel, 16-bit PCM
                sample_rate = 24000
                channels = 1
                bit_depth = 16
                
                # Create WAV header
                header = struct.pack('<4sI4s4sIHHIIHH4sI',
                    b'RIFF',
                    36 + len(pcm_data),
                    b'WAVE',
                    b'fmt ',
                    16,
                    1,  # PCM format
                    channels,
                    sample_rate,
                    sample_rate * channels * bit_depth // 8, # ByteRate
                    channels * bit_depth // 8, # BlockAlign
                    bit_depth,
                    b'data',
                    len(pcm_data)
                )
                
                return header + pcm_data
        
        print("DEBUG: No audio data found in Gemini response", flush=True)
        return None
    except Exception as e:
        print(f"DEBUG: Gemini Audio Generation Error: {traceback.format_exc()}", flush=True)
        return None

def generate_voice_response(article_content, user_query):
    """
    Optimized backend chain: Chat -> TTS.
    Faster than frontend-driven chain (fewer round trips).
    """
    if not GEMINI_API_KEY:
        return None

    try:
        # 1. Get Text Answer (Fast)
        print("DEBUG: Getting text answer from Gemini...", flush=True)
        answer_text = chat_with_article(article_content, user_query)
        if not answer_text or "Error" in answer_text:
            print(f"DEBUG: Chat failed: {answer_text}", flush=True)
            return None
            
        # 2. Convert to Audio (Fast)
        print("DEBUG: Converting answer to audio...", flush=True)
        audio_data = generate_audio(answer_text)
        
        return audio_data
    except Exception as e:
        print(f"DEBUG: Backend Voice Chat Chain Error: {traceback.format_exc()}", flush=True)
        return None
if AI_PROVIDER == "gemini":
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
    else:
        model = None
elif AI_PROVIDER == "openai":
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        client = None
else:
    model = None
    client = None

def generate_summary(text):
    """
    Generates a concise summary (< 100 words) for the given text.
    """
    if AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY or not model:
            return "AI Service Unavailable: Missing Gemini API Key"

        prompt = f"Summarize the following news article in less than 100 words. Capture the key points clearly:\n\n{text}"
        try:
            start_time = time.time()
            response = model.generate_content(prompt)
            latency = time.time() - start_time
            print(f"LATENCY: Gemini Summary took {latency:.2f}s", flush=True)
            return response.text
        except Exception as e:
            return f"Error generating summary with Gemini: {str(e)}"

    elif AI_PROVIDER == "openai":
        if not OPENAI_API_KEY or not client:
            return "AI Service Unavailable: Missing OpenAI API Key"

        prompt = f"Summarize the following news article in less than 100 words. Capture the key points clearly:\n\n{text}"
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful news assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            latency = time.time() - start_time
            print(f"LATENCY: OpenAI Summary took {latency:.2f}s", flush=True)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary with OpenAI: {str(e)}"
    
    return "AI Service Unavailable: Invalid AI Provider"

def chat_with_article(article_content, user_query, history=[]):
    """
     answers a user query based on the article content.
    """
    if AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY or not model:
            return "AI Service Unavailable: Missing API Key"

        prompt = f"""
        You are a helpful and conversational news assistant. 
        
        Context Article:
        {article_content}
        
        User Input: {user_query}
        
        Instructions:
        1. If the user asks a question about the article, answer it naturally using the article context.
        2. If the user wants to move on, skip, or go to the next story (and they haven't been caught by the local 'next' command), acknowledge them briefly and suggest they say "next news".
        3. Be concise and friendly.
        """
        
        try:
            start_time = time.time()
            response = model.generate_content(prompt)
            latency = time.time() - start_time
            print(f"LATENCY: Gemini Chat took {latency:.2f}s", flush=True)
            return response.text
        except Exception as e:
            return f"Error processing query with Gemini: {str(e)}"

    elif AI_PROVIDER == "openai":
        if not OPENAI_API_KEY or not client:
            return "AI Service Unavailable: Missing API Key"

        system_prompt = f"""
        You are a helpful and conversational news assistant. 
        
        Context Article:
        {article_content}
        
        Instructions:
        1. If the user asks a question about the article, answer it naturally using the article context.
        2. If the user wants to move on, skip, or go to the next story, acknowledge them briefly and suggest they say "next news".
        3. Be concise and friendly.
        """

        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ]
            )
            latency = time.time() - start_time
            print(f"LATENCY: OpenAI Chat took {latency:.2f}s", flush=True)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error processing query with OpenAI: {str(e)}"

    return "AI Service Unavailable: Invalid AI Provider"
