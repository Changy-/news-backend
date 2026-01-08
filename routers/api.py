from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
import concurrent.futures
from services import news_service, ai_service

router = APIRouter()

class ArticleRequest(BaseModel):
    content: str
    query: str

class ChatResponse(BaseModel):
    answer: str

class Article(BaseModel):
    title: str
    link: str
    published: str
    summary: str # This will be the AI summary
    original_content: str

def summarize_article_task(article):
    # Use the content if available, else summary (which might be shorter but safer)
    text_to_summarize = article.get('content') or article.get('summary') or ""
    # Strip heavy HTML? Gemini is decent at it. 
    # Let's just pass it.
    summary = ai_service.generate_summary(text_to_summarize)
    article['summary'] = summary
    article['original_content'] = text_to_summarize
    return article

@router.get("/news", response_model=List[Article])
def get_news():
    try:
        # raw_articles = news_service.fetch_techcrunch_news(limit=5) # Limit to 5 for speed in demo, or 10 as requested
        # # Use 5 to avoid long wait times and potential rate limits during dev
        # # User asked for 'fetch to 10', so I'll try 10 but use threads.
        
        # If I strictly follow fetch TO 10, it implies up to 10.
        # Let's do 10.
        raw_articles = news_service.fetch_techcrunch_news(limit=10)
        
        processed_articles = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_article = {executor.submit(summarize_article_task, art): art for art in raw_articles}
            for future in concurrent.futures.as_completed(future_to_article):
                try:
                    data = future.result()
                    processed_articles.append(data)
                except Exception as exc:
                    print(f'Article processing generated an exception: {exc}')
                    
        return processed_articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
def chat(request: ArticleRequest):
    try:
        answer = ai_service.chat_with_article(request.content, request.query)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-chat")
def voice_chat(request: ArticleRequest):
    try:
        audio_data = ai_service.generate_voice_response(request.content, request.query)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate voice response")
        
        from fastapi.responses import Response
        return Response(content=audio_data, media_type="audio/wav")
    except Exception as e:
        print(f"Voice Chat Error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

class SpeakRequest(BaseModel):
    text: str

@router.post("/speak")
def speak(request: SpeakRequest):
    try:
        audio_data = ai_service.generate_audio(request.text)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        # Return audio bytes. Gemini usually returns WAV-formatted data in the inline_data.
        from fastapi.responses import Response
        return Response(content=audio_data, media_type="audio/wav")
    except Exception as e:
        print(f"Speak Error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
