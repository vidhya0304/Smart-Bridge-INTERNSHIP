import uuid
import json
import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from models.schemas import SummaryRequest, SummaryResponse
from utils.db_manager import log_query, log_ai_response, log_summary
from utils.gemini_service import is_gemini_active, get_mock_summary, best_model_name

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

def summarize_text(text: str) -> str:
    """Core educational text summarizer using Gemini."""
    try:
        if not is_gemini_active:
            # Fallback for Demo mode
            mock_data = get_mock_summary(text, "medium")
            return mock_data.summary
            
        prompt = f"Summarize the following text in simple language:\n\n{text}"
        model = genai.GenerativeModel(model_name=best_model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in summarize_text: {str(e)}")
        return f"⚠️ Error in Summary: {e}"

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """Endpoint to summarize text notes."""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")
            
        # 1. Log query
        query_id = uuid.uuid4().hex
        log_query(query_id, "summarize", request.text[:150] + "...")
        
        # 2. Get summary from core logic
        summary_text = summarize_text(request.text)
        
        # Format response to match SummaryResponse schema
        if not is_gemini_active:
            response = get_mock_summary(request.text, request.length)
        else:
            # Split summary_text into sentences for bullet points
            bullets = [s.strip() + "." for s in summary_text.split(".") if len(s.strip()) > 8]
            if not bullets:
                bullets = [summary_text]
            
            # Simple keyword extraction (words > 5 characters, excluding basic duplicates)
            words = [w.strip(".,;:!?\"'()").lower() for w in request.text.split()]
            common_stopwords = {"should", "would", "could", "about", "their", "there", "these", "those"}
            keywords = []
            for w in words:
                if len(w) > 5 and w not in common_stopwords and w not in keywords:
                    keywords.append(w)
                if len(keywords) >= 6:
                    break
                    
            response = SummaryResponse(
                summary=summary_text,
                bullet_points=bullets,
                keywords=keywords or ["education", "summary"]
            )
            
        # 3. Log response
        response_id = uuid.uuid4().hex
        response_text = json.dumps(response.model_dump())
        log_ai_response(response_id, query_id, response_text, "Gemini")
        
        # 4. Log summary mapping in summaries.json
        summary_record_id = uuid.uuid4().hex
        log_summary(summary_record_id, query_id, request.text, response.summary, "Gemini")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
