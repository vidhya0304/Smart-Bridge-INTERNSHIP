import re
import uuid
import json
import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from models.schemas import QuizRequest, QuizResponse, QuizQuestion
from utils.db_manager import log_query, log_ai_response, log_quiz_question
from utils.gemini_service import is_gemini_active, get_mock_quiz, best_model_name

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

def clean_json_block(text: str) -> str:
    """Removes Markdown ```json code fences from text blocks."""
    # Remove markdown code blocks if any
    text = re.sub(r"```(?:json)?\n(.*?)```", r"\1", text, flags=re.DOTALL).strip()
    # Also handle single-line triple backticks if any
    text = text.strip("`").strip()
    return text

def generate_quiz(text: str) -> list:
    """Core educational quiz generation logic using Gemini."""
    try:
        if not is_gemini_active:
            # Fallback for Demo mode
            mock_res = get_mock_quiz(text, 3)
            return [
                {
                    "question": q.question,
                    "options": q.options,
                    "answer": q.correct_answer
                }
                for q in mock_res.questions
            ]
            
        prompt = f"""
You are a quiz generator.

From the following passage, create 3 multiple-choice questions. Each question should include:
- A "question"
- A list of 4 "options"
- A correct "answer" that must exactly match one of the options.

Format your output as **valid JSON**, like this:
[
  {{
    "question": "What is ...?",
    "options": ["A", "B", "C", "D"],
    "answer": "A"
  }}
]

Passage:
{text}
"""
        model = genai.GenerativeModel(model_name=best_model_name)
        response = model.generate_content(prompt)
        quiz_text = response.text.strip()
            
        # Clean markdown code blocks if any
        cleaned_text = clean_json_block(quiz_text)
        return json.loads(cleaned_text)
    except Exception as e:
        logger.error(f"Error in generate_quiz: {str(e)}")
        # Fallback to local mock generator
        mock_res = get_mock_quiz(text, 3)
        return [
            {
                "question": q.question,
                "options": q.options,
                "answer": q.correct_answer
            }
            for q in mock_res.questions
        ]

@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz_endpoint(request: QuizRequest):
    """Endpoint to generate educational quiz questions."""
    try:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty.")
            
        # 1. Log query
        query_id = uuid.uuid4().hex
        log_query(query_id, "quiz", request.topic)
        
        # 2. Get questions from core logic
        questions_list = generate_quiz(request.topic)
        
        # Map questions list to QuizQuestion Pydantic schemas
        pydantic_questions = []
        for q in questions_list:
            pydantic_questions.append(
                QuizQuestion(
                    question=q.get("question", "Question Text"),
                    options=q.get("options", ["Option A", "Option B", "Option C", "Option D"]),
                    correct_answer=q.get("answer", "Option A"),
                    explanation="Verify this answer using your notes."
                )
            )
            
        response = QuizResponse(
            topic=request.topic,
            questions=pydantic_questions
        )
        
        # 3. Log response
        response_id = uuid.uuid4().hex
        response_text = json.dumps(response.model_dump())
        log_ai_response(response_id, query_id, response_text, "Gemini")
        
        # 4. Log individual quiz questions to quizzes.json
        for q in response.questions:
            quiz_question_id = uuid.uuid4().hex
            log_quiz_question(quiz_question_id, query_id, q.question, q.options, q.correct_answer)
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
