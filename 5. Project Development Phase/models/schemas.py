from pydantic import BaseModel, Field
from typing import List, Optional

# Chat Schemas
class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question")
    history: Optional[List[dict]] = Field(default=[], description="Chat history context")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Direct concise answer")
    explanation: str = Field(..., description="Detailed explanation")
    example: str = Field(..., description="Illustrative example")
    key_points: List[str] = Field(..., description="Bullet list of key take-away points")

# Concept Explanation Schemas
class ExplainRequest(BaseModel):
    concept: str = Field(..., description="The concept to explain")
    level: str = Field("medium", description="Target complexity: simple, medium, advanced")

class ExplainResponse(BaseModel):
    concept: str = Field(..., description="The concept explained")
    explanation: str = Field(..., description="The concept explanation")
    examples: List[str] = Field(..., description="Real-life examples illustrating the concept")
    analogies: List[str] = Field(..., description="Analogies to help understand the concept")

# Quiz Schemas
class QuizRequest(BaseModel):
    topic: str = Field(..., description="Topic of the quiz")
    count: int = Field(10, ge=1, le=15, description="Number of MCQs to generate")
    use_local: Optional[bool] = Field(False, description="Use local T5 model instead of Gemini")

class QuizQuestion(BaseModel):
    question: str = Field(..., description="The quiz question")
    options: List[str] = Field(..., description="List of exactly 4 options")
    correct_answer: str = Field(..., description="The correct option matching exactly one item in options")
    explanation: str = Field(..., description="Detailed explanation of why the answer is correct")

class QuizResponse(BaseModel):
    topic: str = Field(..., description="Quiz topic")
    questions: List[QuizQuestion] = Field(..., description="List of generated questions")

# Summarizer Schemas
class SummaryRequest(BaseModel):
    text: str = Field(..., description="The content to summarize")
    length: str = Field("medium", description="Length: short, medium")
    format: str = Field("bullet_points", description="Format: paragraph, bullet_points")
    use_local: Optional[bool] = Field(False, description="Use local T5 model instead of Gemini")

class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Text summary description")
    bullet_points: List[str] = Field(..., description="Main bullet points of the text")
    keywords: List[str] = Field(..., description="Important keywords extracted from the text")

# Recommendations Schemas
class RecommendRequest(BaseModel):
    topic: str = Field(..., description="Topic or subject the student wants to learn")
    level: str = Field("beginner", description="Difficulty level: beginner, intermediate, advanced")

class ResourceItem(BaseModel):
    title: str = Field(..., description="Title of the learning resource")
    type: str = Field(..., description="Type of resource (e.g., Book, Course, Practice)")
    url: str = Field(..., description="URL link/search recommendation for the resource")
    time_estimate: str = Field(..., description="Estimated time to complete")

class RoadmapStep(BaseModel):
    step_number: int = Field(..., description="Step position in sequence")
    title: str = Field(..., description="Title of the topic/subtopic")
    description: str = Field(..., description="What to learn at this step")
    estimated_hours: int = Field(..., description="Estimated study time in hours")

class RecommendResponse(BaseModel):
    topic: str = Field(..., description="Subject domain")
    level: str = Field(..., description="User level")
    resources: List[ResourceItem] = Field(..., description="Recommended reading/practice material")
    roadmap: List[RoadmapStep] = Field(..., description="Step-by-step roadmap timeline")
