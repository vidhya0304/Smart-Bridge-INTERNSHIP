import logging
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from config import STATIC_DIR, TEMPLATES_DIR, HOST, PORT, GEMINI_API_KEY
from utils.db_manager import init_db

# Import root modules and core functions
import qna
import explanation_module
import quiz_module
import summary_module
import learning_path

from qna import answer_question_with_gemini
from explanation_module import explain_topic
from quiz_module import generate_quiz
from summary_module import summarize_text
from learning_path import get_learning_recommendations

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EduGenie AI",
    description="Educational AI assistant platform powered by Gemini & LaMini-Flan-T5",
    version="1.0.0"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API sub-routers (kept for schema structure and testing backwards-compatibility)
app.include_router(qna.router, prefix="/api", tags=["chat"])
app.include_router(explanation_module.router, prefix="/api", tags=["explain"])
app.include_router(quiz_module.router, prefix="/api", tags=["quiz"])
app.include_router(summary_module.router, prefix="/api", tags=["summary"])
app.include_router(learning_path.router, prefix="/api", tags=["recommend"])

# --- DIRECT RESTFUL API ENDPOINTS FROM SCHEMATICS ---

# Q&A - GET API using Gemini
@app.get("/qa")
async def answer_question(question: str = Query(...)):
    answer = answer_question_with_gemini(question)
    
    # Log database query/response mapping
    try:
        import uuid
        import json
        from utils.db_manager import log_query, log_ai_response
        query_id = uuid.uuid4().hex
        log_query(query_id, "qa", question)
        response_id = uuid.uuid4().hex
        log_ai_response(response_id, query_id, json.dumps({"answer": answer}), "Gemini")
    except Exception as db_err:
        logger.error(f"Failed to log DB in qa endpoint: {str(db_err)}")
        
    return {"answer": answer}

# Explanation - POST API
@app.post("/explain/")
async def explain_api(request: Request):
    data = await request.json()
    topic = data.get("topic")
    if not topic:
        return JSONResponse(content={"error": "Please provide a topic."}, status_code=400)
    explanation = explain_topic(topic)
    
    # Log database query/response mapping
    try:
        import uuid
        import json
        from utils.db_manager import log_query, log_ai_response
        query_id = uuid.uuid4().hex
        log_query(query_id, "explain", topic)
        response_id = uuid.uuid4().hex
        log_ai_response(response_id, query_id, json.dumps({"topic": topic, "explanation": explanation}), "LaMini-Flan-T5-783M")
    except Exception as db_err:
        logger.error(f"Failed to log DB in explain endpoint: {str(db_err)}")
        
    return {"topic": topic, "explanation": explanation}

# Summarization - POST API
@app.post("/summarize/")
async def summarize_api(request: Request):
    data = await request.json()
    text = data.get("text")
    if not text:
        return JSONResponse(content={"error": "Please provide text to summarize."}, status_code=400)
    summary = summarize_text(text)
    
    # Log database query/response mapping
    try:
        import uuid
        import json
        from utils.db_manager import log_query, log_ai_response, log_summary as log_db_summary
        query_id = uuid.uuid4().hex
        log_query(query_id, "summarize", text[:150] + "...")
        response_id = uuid.uuid4().hex
        log_ai_response(response_id, query_id, json.dumps({"summary": summary}), "Gemini")
        summary_record_id = uuid.uuid4().hex
        log_db_summary(summary_record_id, query_id, text, summary, "Gemini")
    except Exception as db_err:
        logger.error(f"Failed to log DB in summarize endpoint: {str(db_err)}")
        
    return {"summary": summary}

# Quiz Generation - POST API
@app.post("/quiz")
async def quiz_api(request: Request):
    data = await request.json()
    text = data.get("text")
    if not text:
        return JSONResponse(content={"error": "Please provide text for quiz."}, status_code=400)
    quiz = generate_quiz(text)
    print("Generated quiz:", quiz) # DEBUG
    
    # Log database query/response mapping
    try:
        import uuid
        import json
        from utils.db_manager import log_query, log_ai_response, log_quiz_question
        query_id = uuid.uuid4().hex
        log_query(query_id, "quiz", text[:150] + "...")
        response_id = uuid.uuid4().hex
        log_ai_response(response_id, query_id, json.dumps({"quiz": quiz}), "Gemini")
        for q in quiz:
            quiz_question_id = uuid.uuid4().hex
            log_quiz_question(
                quiz_question_id, 
                query_id, 
                q.get("question", ""), 
                q.get("options", []), 
                q.get("answer", "")
            )
    except Exception as db_err:
        logger.error(f"Failed to log DB in quiz endpoint: {str(db_err)}")
        
    return JSONResponse(content={"quiz": quiz})

# Learning Recommendations - GET API
@app.get("/learn/recommendations")
async def learning_recommendation_api(topic: str = Query(...)):
    recommendation = get_learning_recommendations(topic)
    
    # Log database query/response mapping
    try:
        import uuid
        import json
        from utils.db_manager import log_query, log_ai_response, log_learning_path
        query_id = uuid.uuid4().hex
        log_query(query_id, "learn", topic)
        response_id = uuid.uuid4().hex
        log_ai_response(response_id, query_id, json.dumps({"topic": topic, "recommendation": recommendation}), "Gemini")
        path_id = uuid.uuid4().hex
        step_titles = [line.strip() for line in recommendation.split("\n") if line.strip() and line.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "Step"))]
        if not step_titles:
            step_titles = ["Personalized Learning Path"]
        log_learning_path(path_id, query_id, topic, "beginner", step_titles)
    except Exception as db_err:
        logger.error(f"Failed to log DB in recommendations endpoint: {str(db_err)}")
        
    return {"topic": topic, "recommendation": recommendation}

# Helper function to get default template context
def get_base_context(request: Request) -> dict:
    return {
        "request": request,
        "gemini_configured": bool(GEMINI_API_KEY)
    }

# --- HTML Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/chat", response_class=HTMLResponse)
async def read_chat(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/quiz", response_class=HTMLResponse)
async def read_quiz(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/summary", response_class=HTMLResponse)
async def read_summary(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/explain", response_class=HTMLResponse)
async def read_explain(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/recommend", response_class=HTMLResponse)
async def read_recommend(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

@app.get("/contact", response_class=HTMLResponse)
async def read_contact(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=get_base_context(request))

# Startup event to warm up local model lazily
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up EduGenie AI Backend...")
    # Initialize JSON database
    init_db()
    
    # Lazy load HF T5 in the background
    import threading
    from utils.local_t5_service import load_t5_pipeline
    threading.Thread(target=load_t5_pipeline, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Running EduGenie locally on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
