import uuid
import json
import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from models.schemas import RecommendRequest, RecommendResponse, RoadmapStep, ResourceItem
from utils.db_manager import log_query, log_ai_response, log_learning_path
from utils.gemini_service import is_gemini_active, get_mock_recommendations, best_model_name

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

def get_learning_recommendations(topic: str) -> str:
    """Core educational recommendations logic using Gemini."""
    prompt = f"""
You are an AI tutor. The student wants to learn about: {topic}.
Suggest a structured and adaptive learning path including key topics, order of learning, and resources.
Include beginner, intermediate, and advanced levels if needed.
"""
    try:
        if not is_gemini_active:
            # Fallback for Demo mode
            mock_data = get_mock_recommendations(topic, "beginner")
            roadmap_str = "\n".join([f"Step {s.step_number}: {s.title} - {s.description}" for s in mock_data.roadmap])
            return roadmap_str
            
        model = genai.GenerativeModel(model_name=best_model_name)
        response = model.generate_content(prompt)
            
        if hasattr(response, "text"):
            return response.text
        elif hasattr(response, "parts") and response.parts:
            return response.parts[0].text
        else:
            return "❌ Could not extract content from Gemini response."
    except Exception as e:
        import traceback
        logger.error(f"Error in learning recommendations: {str(e)}")
        return f"❌ Error occurred: {str(e)}"

@router.post("/recommend", response_model=RecommendResponse)
async def generate_recommendations(request: RecommendRequest):
    """Endpoint to generate study roadmaps and resources."""
    try:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty.")
            
        valid_levels = ["beginner", "intermediate", "advanced"]
        if request.level.lower() not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Level must be one of: {', '.join(valid_levels)}")
            
        # 1. Log query
        query_id = uuid.uuid4().hex
        log_query(query_id, "learn", request.topic)
        
        # 2. Get recommendations text from core logic
        roadmap_text = get_learning_recommendations(request.topic)
        
        # Format response to match RecommendResponse schema
        if not is_gemini_active:
            response = get_mock_recommendations(request.topic, request.level.lower())
        else:
            # Parse roadmap steps from Gemini response or construct a clean structured object
            # (We separate steps based on common lines like "Step", numbers, or bullet points)
            steps = []
            lines = roadmap_text.split("\n")
            step_counter = 1
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Match lines like "1. ...", "- ...", "* ...", "Step 1: ..."
                if line.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "Step")):
                    title_content = line.lstrip("-*123456789. ").strip()
                    if len(title_content) > 10:
                        steps.append(
                            RoadmapStep(
                                step_number=step_counter,
                                title=title_content[:40] + "...",
                                description=title_content,
                                estimated_hours=4
                            )
                        )
                        step_counter += 1
                        if step_counter > 5:
                            break
                            
            if not steps:
                steps = [
                    RoadmapStep(
                        step_number=1,
                        title="Personalized Roadmap",
                        description=roadmap_text[:200] + "...",
                        estimated_hours=10
                    )
                ]
                
            response = RecommendResponse(
                topic=request.topic,
                level=request.level.lower(),
                resources=[
                    ResourceItem(title="Official Documentation", type="documentation", url="https://docs.google.com", time_estimate="2 hours"),
                    ResourceItem(title="AI Tutor Video Tutorial", type="video", url="https://youtube.com", time_estimate="1 hour")
                ],
                roadmap=steps
            )
            
        # 3. Log response
        response_id = uuid.uuid4().hex
        response_text = json.dumps(response.model_dump())
        log_ai_response(response_id, query_id, response_text, "Gemini")
        
        # 4. Log learning path recommended topics
        path_id = uuid.uuid4().hex
        step_titles = [s.title for s in response.roadmap]
        log_learning_path(path_id, query_id, request.topic, request.level.lower(), step_titles)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
