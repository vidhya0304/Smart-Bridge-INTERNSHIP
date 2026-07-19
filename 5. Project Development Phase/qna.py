import uuid
import json
import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from utils.db_manager import log_query, log_ai_response
from utils.gemini_service import is_gemini_active, get_mock_chat_response, best_model_name, get_chat_response

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

def answer_question_with_gemini(question: str) -> str:
    """Core educational QnA logic using Gemini with fallback."""
    try:
        response = get_chat_response(question)
        return response.explanation
    except Exception as e:
        logger.error(f"Error in answer_question_with_gemini: {str(e)}")
        return get_mock_chat_response(question).explanation

@router.post("/ask", response_model=ChatResponse)

async def ask_question(request: ChatRequest):
    """Endpoint to answer educational questions with detailed responses."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
        # 1. Log query
        query_id = uuid.uuid4().hex
        log_query(query_id, "qa", request.question)
        
        # 2. Get response from core gemini_service wrapper
        response = get_chat_response(request.question)
        
        # 3. Log response
        response_id = uuid.uuid4().hex
        response_text = json.dumps(response.model_dump())
        log_ai_response(response_id, query_id, response_text, "Gemini")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

