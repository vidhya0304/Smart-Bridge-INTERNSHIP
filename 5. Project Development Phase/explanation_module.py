import uuid
import json
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import ExplainRequest, ExplainResponse
from utils.db_manager import log_query, log_ai_response
from utils.gemini_service import get_concept_explanation, is_gemini_active

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

from config import DISABLE_LOCAL_T5

# Try loading transformers lazily to avoid heavy start blocks
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    transformers_available = True
except ImportError:
    transformers_available = False

# Improved model placeholders
explain_tokenizer = None
explain_model = None

def init_local_t5():
    """Lazily load the LaMini-Flan-T5-783M model to prevent app startup blocking."""
    global explain_tokenizer, explain_model
    if DISABLE_LOCAL_T5:
        logger.info("Local T5 model is disabled via configuration. Falling back to Gemini.")
        return False
        
    if not transformers_available:
        return False

        
    if explain_tokenizer is None or explain_model is None:
        try:
            logger.info("Loading local LaMini-Flan-T5-783M model (this may take a few moments)...")
            explain_tokenizer = AutoTokenizer.from_pretrained("MBZUAI/LaMini-Flan-T5-783M")
            explain_model = AutoModelForSeq2SeqLM.from_pretrained("MBZUAI/LaMini-Flan-T5-783M")
            logger.info("Successfully loaded LaMini-Flan-T5-783M model.")
            return True
        except Exception as e:
            logger.error(f"Failed to load LaMini-Flan-T5-783M: {str(e)}. Falling back to Gemini.")
            return False
    return True

def explain_topic(topic: str) -> str:
    """Core educational concept explainer using local LaMini-Flan-T5-783M."""
    try:
        # Initialize the local T5 model
        success = init_local_t5()
        if not success or explain_model is None or explain_tokenizer is None:
            # Fallback to Gemini if model loading failed
            logger.warning("Local T5 model is unavailable. Falling back to Gemini for explanation.")
            gemini_res = get_concept_explanation(topic, "simple")
            return gemini_res.explanation
            
        input_text = f"Explain the concept of '{topic}' in a simple and clear way for a school student."
        inputs = explain_tokenizer(input_text, return_tensors="pt")
        
        outputs = explain_model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            do_sample=True
        )
        
        explanation = explain_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return explanation
    except Exception as e:
        logger.error(f"Error in explain_topic: {str(e)}")
        # Fallback to Gemini
        gemini_res = get_concept_explanation(topic, "simple")
        return gemini_res.explanation

@router.post("/explain", response_model=ExplainResponse)
async def explain_concept(request: ExplainRequest):
    """Endpoint to explain educational concepts at different learning levels."""
    try:
        if not request.concept.strip():
            raise HTTPException(status_code=400, detail="Concept cannot be empty.")
            
        valid_levels = ["simple", "medium", "advanced"]
        if request.level.lower() not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Level must be one of: {', '.join(valid_levels)}")
            
        # 1. Log query
        query_id = uuid.uuid4().hex
        log_query(query_id, "explain", request.concept)
        
        # 2. Get response from core local model
        explanation_text = explain_topic(request.concept)
        
        # Format response to match ExplainResponse schema
        response = ExplainResponse(
            concept=request.concept,
            explanation=explanation_text,
            examples=[f"Example of {request.concept} in real life."],
            analogies=[f"Analogy: Think of {request.concept} like a flow system."]
        )
        
        # 3. Log response
        response_id = uuid.uuid4().hex
        response_text = json.dumps(response.model_dump())
        log_ai_response(response_id, query_id, response_text, "LaMini-Flan-T5-783M")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
