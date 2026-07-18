import json
import logging
import time
import google.generativeai as genai
from config import GEMINI_API_KEY
from models.schemas import ChatResponse, ExplainResponse, QuizResponse, SummaryResponse, RecommendResponse, QuizQuestion, ResourceItem, RoadmapStep

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if Gemini key is set and valid
is_gemini_active = bool(GEMINI_API_KEY) and "your_gemini_api" not in GEMINI_API_KEY.lower()

if is_gemini_active:
    masked_key = f"{GEMINI_API_KEY[:6]}...{GEMINI_API_KEY[-4:]}" if len(GEMINI_API_KEY) > 10 else "too short"
    logger.info(f"GEMINI_API_KEY is loaded successfully! Length: {len(GEMINI_API_KEY)}, Masked: {masked_key}")
    genai.configure(api_key=GEMINI_API_KEY)
else:
    key_length = len(GEMINI_API_KEY) if GEMINI_API_KEY else 0
    masked_key = f"{GEMINI_API_KEY[:6]}...{GEMINI_API_KEY[-4:]}" if key_length > 10 else ("empty" if key_length == 0 else "placeholder")
    logger.warning(f"GEMINI_API_KEY is not active. Length: {key_length}, Masked: {masked_key}. Running in DEMO (Mock Data) Mode.")


# Dynamically resolve best model at startup
best_model_name = "gemini-1.5-flash"
if is_gemini_active:
    try:
        available = [m.name.split("/")[-1] for m in genai.list_models()]
        priority = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-1.5-flash",
            "gemini-pro-latest",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        for candidate in priority:
            if candidate in available:
                best_model_name = candidate
                break
        logger.info(f"Resolved best available Gemini model: {best_model_name}")
    except Exception as e:
        logger.warning(f"Error listing models, default to gemini-1.5-flash: {str(e)}")

def call_gemini_with_retry(prompt: str, system_instruction: str = None, retries: int = 3, backoff: float = 2.0) -> str:
    """Calls Gemini API with retries and exponential backoff."""
    if not is_gemini_active:
        raise ValueError("Gemini API key is not configured.")
    
    model_name = best_model_name
    
    for attempt in range(retries):
        try:
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            
            logger.info(f"Calling Gemini API (Attempt {attempt + 1}/{retries})...")
            response = model.generate_content(prompt)
            
            if response and response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini API.")
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            if attempt == retries - 1:
                raise e
            time.sleep(backoff ** attempt)
            
    raise Exception("Failed to get response from Gemini API after retries.")

# --- MOCK GENERATION HELPERS FOR DEMO MODE ---

def get_mock_chat_response(question: str) -> ChatResponse:
    logger.info(f"Generating mock chat response for question: {question}")
    return ChatResponse(
        answer=f"This is a pre-configured EduGenie demo reply for your question: '{question}'",
        explanation=(
            "To unlock live AI responses powered by Google Gemini, you simply need to configure your API key. "
            "Please open the project's '.env' file in your text editor, set GEMINI_API_KEY to your valid key, "
            "and restart the backend server.\n\n"
            "This structured interface is designed to break down information into modular, readable blocks "
            "including direct answers, step-by-step explanations, illustrative examples, and key takeaway points."
        ),
        example=f"For example, if you asked about recursion, the live AI would explain the call stack and base cases.",
        key_points=[
            "Find the '.env' file in your project root.",
            "Obtain a free Gemini API key from Google AI Studio.",
            "Insert your key: GEMINI_API_KEY=AIzaSy...",
            "Restart your development server."
        ]
    )

def get_mock_concept_explanation(concept: str, level: str) -> ExplainResponse:
    logger.info(f"Generating mock concept explanation: {concept} ({level})")
    
    if level == "simple":
        explanation = (
            f"Think of {concept} like a box of crayons! Each crayon has its own special color, and when you draw, "
            "they work together to make a beautiful picture. We use this idea to group things together so they are "
            "easy to find and play with."
        )
        analogies = [
            f"It is like organizing your toys into different plastic boxes based on their types.",
            "Like sorting candies by color before eating them."
        ]
    elif level == "advanced":
        explanation = (
            f"The concept of {concept} is formalised as a structured paradigm within computation or theory. "
            "It incorporates encapsulation principles, abstraction interfaces, and state-machine transitions. "
            "By implementing strict typing and algorithmic hierarchies, we establish scalable mathematical models "
            "that control runtime complexity."
        )
        analogies = [
            f"Equivalent to a dual-layered compiler optimizing assembly trees.",
            "Analogous to quantum superposition states in discrete architectures."
        ]
    else:
        explanation = (
            f"{concept} is an educational concept widely used in science, technology, or academic domains. "
            "It provides a clear framework to deconstruct complicated structures into smaller, digestible components. "
            "Understanding this concept is fundamental for intermediate students wishing to advance in this subject."
        )
        analogies = [
            f"It works like a thermostat maintaining a constant temperature in a house.",
            "Like a library catalog index routing users to the correct book row."
        ]
        
    return ExplainResponse(
        concept=concept,
        explanation=explanation,
        examples=[
            f"Standard practical application of {concept} in modern software engineering.",
            f"Common educational textbook example used in university research paper labs."
        ],
        analogies=analogies
    )

def get_mock_quiz(topic: str, count: int = 10) -> QuizResponse:
    logger.info(f"Generating mock quiz on topic: {topic}")
    questions = []
    
    # Generate mock questions dynamically based on count
    for i in range(1, count + 1):
        questions.append(QuizQuestion(
            question=f"Demo Question {i}: In the context of '{topic}', which statement is correct?",
            options=[
                f"Option A: This option is incorrect for {topic}.",
                f"Option B: This option represents the correct answer choice.",
                f"Option C: This option is a distractor and is incorrect.",
                f"Option D: None of the choices are correct."
            ],
            correct_answer=f"Option B: This option represents the correct answer choice.",
            explanation=f"Option B is correct because in '{topic}', this standard principle represents the core functional mechanism."
        ))
        
    return QuizResponse(topic=topic, questions=questions)

def get_mock_summary(text: str, length: str) -> SummaryResponse:
    logger.info("Generating mock text summary")
    summary_text = (
        f"This is a demo summary of your pasted note. (Pasted length: {len(text)} characters). "
        "To enable real summaries, insert your Gemini API Key in the '.env' file."
    )
    return SummaryResponse(
        summary=summary_text,
        bullet_points=[
            f"Input text contains approximately {len(text.split())} words.",
            "Demo Mode is currently active because no active GEMINI_API_KEY was found.",
            "Ensure the local HuggingFace T5 model is loaded if you selected local offline mode."
        ],
        keywords=["summary", "demo", "education", "notes"]
    )

def get_mock_recommendations(topic: str, level: str) -> RecommendResponse:
    logger.info(f"Generating mock recommendations for subject: {topic} ({level})")
    
    resources = [
        ResourceItem(
            title=f"Mastering {topic}: From {level.capitalize()} to Professional",
            type="Book",
            url=f"https://www.google.com/search?q=books+on+{topic}",
            time_estimate="2 weeks reading time"
        ),
        ResourceItem(
            title=f"Introduction to {topic} (Advanced Learning Program)",
            type="Course",
            url=f"https://www.google.com/search?q=courses+on+{topic}",
            time_estimate="15 hours video lectures"
        ),
        ResourceItem(
            title=f"{topic} Interactive Practice Lab",
            type="Practice",
            url=f"https://www.google.com/search?q=practice+exercises+for+{topic}",
            time_estimate="1 hour daily practice"
        )
    ]
    
    roadmap = [
        RoadmapStep(
            step_number=1,
            title=f"Core Foundations of {topic}",
            description="Study the basic principles, historical context, and terminology.",
            estimated_hours=8
        ),
        RoadmapStep(
            step_number=2,
            title="Intermediate Practical Projects",
            description="Complete simple hands-on exercises and implement basic structures.",
            estimated_hours=12
        ),
        RoadmapStep(
            step_number=3,
            title="System Optimizations & Scale",
            description="Learn how to refactor your knowledge for production or exam environments.",
            estimated_hours=15
        ),
        RoadmapStep(
            step_number=4,
            title="Advanced Topics & Project Portfolio",
            description="Build a final comprehensive project or complete standard certifications.",
            estimated_hours=20
        )
    ]
    
    return RecommendResponse(topic=topic, level=level, resources=resources, roadmap=roadmap)


# --- EXPOSED API SERVICES (WITH DEMO MODE FALLBACKS) ---

def get_chat_response(question: str, history: list = None) -> ChatResponse:
    """Generates structured educational question-answer response."""
    if not is_gemini_active:
        return get_mock_chat_response(question)
        
    history_context = ""
    if history:
        history_context = "Previous chat history for context:\n"
        for msg in history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"- {role.capitalize()}: {content}\n"
            
    system_instruction = (
        "You are EduGenie, a premium AI educational assistant. "
        "Answer the user's educational question thoroughly and clearly. "
        "You must return your response in JSON format matching this schema exactly:\n"
        "{\n"
        '  "answer": "A direct, clear, and concise answer to the question.",\n'
        '  "explanation": "A detailed, step-by-step educational explanation of the core concept.",\n'
        '  "example": "A concrete, relatable real-world example illustrating the answer.",\n'
        '  "key_points": ["Key takeaway point 1", "Key takeaway point 2", "Key takeaway point 3"]\n'
        "}"
    )
    
    prompt = f"{history_context}\nQuestion: {question}"
    
    try:
        response_text = call_gemini_with_retry(prompt, system_instruction=system_instruction)
        data = json.loads(response_text)
        return ChatResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini chat response, falling back to mock: {str(e)}")
        return get_mock_chat_response(question)

def get_concept_explanation(concept: str, level: str) -> ExplainResponse:
    """Explains a difficult concept with varying levels of complexity."""
    if not is_gemini_active:
        return get_mock_concept_explanation(concept, level)
        
    system_instruction = (
        f"You are a master educator explaining concepts at a '{level}' level of understanding. "
        "Simple level should be understandable by a child (using simple language, fun analogies). "
        "Medium level is suited for high school / undergraduate students. "
        "Advanced level is deep, comprehensive, and technically rigorous. "
        "You must return your response in JSON format matching this schema exactly:\n"
        "{\n"
        '  "concept": "The concept name",\n'
        '  "explanation": "The explanation customized for the chosen level.",\n'
        '  "examples": ["Real-life example 1", "Real-life example 2"],\n'
        '  "analogies": ["Analogy 1", "Analogy 2"]\n'
        "}"
    )
    
    prompt = f"Explain the concept of: {concept}"
    
    try:
        response_text = call_gemini_with_retry(prompt, system_instruction=system_instruction)
        data = json.loads(response_text)
        return ExplainResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini concept explanation, falling back to mock: {str(e)}")
        return get_mock_concept_explanation(concept, level)

def get_quiz(topic: str, count: int = 10) -> QuizResponse:
    """Generates an educational quiz with multiple choice questions."""
    if not is_gemini_active:
        return get_mock_quiz(topic, count)
        
    system_instruction = (
        f"You are a professional educational assessment designer. "
        f"Generate a quiz with exactly {count} multiple choice questions (MCQs) on the topic. "
        "Each question must have exactly 4 choices, specify the correct answer (matching one option exactly), "
        "and provide a short, helpful explanation of why it is correct. "
        "You must return your response in JSON format matching this schema exactly:\n"
        "{\n"
        '  "topic": "The quiz topic",\n'
        '  "questions": [\n'
        "    {\n"
        '      "question": "Question text",\n'
        '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '      "correct_answer": "Option B",\n'
        '      "explanation": "Explanation of why Option B is correct."\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    
    prompt = f"Create a quiz on: {topic}"
    
    try:
        response_text = call_gemini_with_retry(prompt, system_instruction=system_instruction)
        data = json.loads(response_text)
        return QuizResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini quiz, falling back to mock: {str(e)}")
        return get_mock_quiz(topic, count)

def get_summary(text: str, length: str, format_type: str) -> SummaryResponse:
    """Summarizes educational texts, notes, or articles."""
    if not is_gemini_active:
        return get_mock_summary(text, length)
        
    length_instruction = "short (1-2 sentences)" if length == "short" else "medium (1-2 cohesive paragraphs)"
    format_instruction = "paragraphs" if format_type == "paragraph" else "bullet points"
    
    system_instruction = (
        f"You are a study assistant that summarizes text. Summarize the text to be {length_instruction} and format it as {format_instruction}. "
        "Identify key takeaways, bullet points, and core keywords. "
        "You must return your response in JSON format matching this schema exactly:\n"
        "{\n"
        '  "summary": "The main summary text.",\n'
        '  "bullet_points": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],\n'
        '  "keywords": ["keyword1", "keyword2", "keyword3"]\n'
        "}"
    )
    
    prompt = f"Summarize the following text:\n\n{text}"
    
    try:
        response_text = call_gemini_with_retry(prompt, system_instruction=system_instruction)
        data = json.loads(response_text)
        return SummaryResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini summary, falling back to mock: {str(e)}")
        return get_mock_summary(text, length)

def get_recommendations(topic: str, level: str) -> RecommendResponse:
    """Generates books, courses, practice, and step-by-step roadmap timeline."""
    if not is_gemini_active:
        return get_mock_recommendations(topic, level)
        
    system_instruction = (
        f"You are a curriculum designer. Create a personalized learning recommendations roadmap and resource guide "
        f"for a '{level}' student studying '{topic}'. "
        "Provide 3 resource items (a Book, a Course, and a Practice platform) and a 4-step learning roadmap. "
        "You must return your response in JSON format matching this schema exactly:\n"
        "{\n"
        '  "topic": "The study topic",\n'
        '  "level": "The student level",\n'
        '  "resources": [\n'
        "    {\n"
        '      "title": "Resource name",\n'
        '      "type": "Book / Course / Practice",\n'
        '      "url": "Search query or recommendation link",\n'
        '      "time_estimate": "Estimated time (e.g. 5 weeks, 2 hours/day)"\n'
        "    }\n"
        "  ],\n"
        '  "roadmap": [\n'
        "    {\n"
        '      "step_number": 1,\n'
        '      "title": "Subtopic title",\n'
        '      "description": "Short explanation of what to learn here",\n'
        '      "estimated_hours": 10\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    
    prompt = f"Design a learning recommendations curriculum for: {topic}"
    
    try:
        response_text = call_gemini_with_retry(prompt, system_instruction=system_instruction)
        data = json.loads(response_text)
        return RecommendResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini recommendations, falling back to mock: {str(e)}")
        return get_mock_recommendations(topic, level)
