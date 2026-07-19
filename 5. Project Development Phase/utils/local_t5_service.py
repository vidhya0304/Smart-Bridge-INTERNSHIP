import logging
import threading
from config import DISABLE_LOCAL_T5, LOCAL_T5_MODEL

# Set up logging
logger = logging.getLogger(__name__)

# Threading lock and global pipeline placeholder
_model_lock = threading.Lock()
_t5_pipeline = None
_model_loaded_successfully = False

def load_t5_pipeline():
    """Initializes and caches the Hugging Face text2text-generation pipeline.
    
    This is executed lazily to prevent blocking server startup.
    """
    global _t5_pipeline, _model_loaded_successfully
    
    if DISABLE_LOCAL_T5:
        logger.info("Local T5 model is disabled via configuration.")
        return None

    if _t5_pipeline is not None:
        return _t5_pipeline

    with _model_lock:
        # Check again in case another thread initialized it while waiting
        if _t5_pipeline is not None:
            return _t5_pipeline
            
        try:
            logger.info(f"Loading local T5 model: {LOCAL_T5_MODEL}... (This may take some time on first run)")
            
            # Import transformers and torch inside the function to save start-up overhead
            from transformers import pipeline
            import torch
            
            # Use CPU by default to ensure maximum compatibility; if CUDA is available, use it.
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Using device: {'GPU (cuda)' if device == 0 else 'CPU'}")
            
            # Load the text2text-generation pipeline
            _t5_pipeline = pipeline(
                "text2text-generation",
                model=LOCAL_T5_MODEL,
                device=device,
                max_length=512
            )
            _model_loaded_successfully = True
            logger.info("Local T5 model loaded successfully.")
            return _t5_pipeline
            
        except Exception as e:
            logger.error(f"Failed to load local T5 model: {str(e)}")
            _t5_pipeline = None
            _model_loaded_successfully = False
            return None

def is_t5_available() -> bool:
    """Checks if T5 model has loaded successfully."""
    return _model_loaded_successfully

def run_local_t5_summary(text: str, length: str = "medium") -> str:
    """Generates a text summary using the local T5 model.
    
    Falls back to Gemini if the local T5 model fails or is disabled.
    """
    pipe = load_t5_pipeline()
    if pipe is None:
        logger.warning("Local T5 is unavailable. Cannot run local summary.")
        raise RuntimeError("Local T5 model not loaded.")
        
    try:
        max_len = 80 if length == "short" else 200
        min_len = 20 if length == "short" else 50
        
        prompt = f"summarize: {text}"
        
        logger.info("Running local T5 summarization...")
        result = pipe(prompt, max_length=max_len, min_length=min_len, do_sample=False)
        
        if result and len(result) > 0:
            summary_text = result[0].get("generated_text", "")
            return summary_text
        else:
            raise Exception("T5 generated empty output.")
            
    except Exception as e:
        logger.error(f"Error during T5 execution: {str(e)}")
        raise e

def run_local_t5_quiz(topic: str) -> list:
    """Generates basic educational questions using local T5.
    
    Since LaMini is a text-to-text model, we prompt it to write questions.
    Returns a list of dicts or raises an exception for fallback.
    """
    pipe = load_t5_pipeline()
    if pipe is None:
        raise RuntimeError("Local T5 model not loaded.")
        
    try:
        prompt = f"Write three multiple choice questions on {topic} with answers."
        logger.info("Running local T5 quiz generation...")
        result = pipe(prompt, max_length=256)
        
        if result and len(result) > 0:
            output_text = result[0].get("generated_text", "")
            # Return list containing this parsed text or raise error to fallback to Gemini (which generates strict JSON)
            # Since local small models are bad at JSON, we parse output_text or fall back.
            # To ensure the user gets a premium experience, we will return the text content 
            # wrapped as a fallback question, or let the router fall back to Gemini.
            return [{
                "question": f"Self-study question about {topic}",
                "options": ["Read local T5 output details below", "Review Gemini responses", "Study topic basics", "All of the above"],
                "correct_answer": "All of the above",
                "explanation": f"Generated text by T5: {output_text}"
            }]
        else:
            raise Exception("T5 generated empty quiz output.")
            
    except Exception as e:
        logger.error(f"Error during T5 quiz generation: {str(e)}")
        raise e
