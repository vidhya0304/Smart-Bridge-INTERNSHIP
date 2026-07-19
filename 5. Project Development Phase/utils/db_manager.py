import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Base directory for data storage
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Create data directory if it does not exist
DATA_DIR.mkdir(exist_ok=True)

# Define collection files
FILES = {
    "users": DATA_DIR / "users.json",
    "queries": DATA_DIR / "queries.json",
    "responses": DATA_DIR / "responses.json",
    "learning_paths": DATA_DIR / "learning_paths.json",
    "quizzes": DATA_DIR / "quizzes.json",
    "summaries": DATA_DIR / "summaries.json"
}

def init_db():
    """Initializes JSON data files and a default user if they do not exist."""
    for name, filepath in FILES.items():
        if not filepath.exists() or os.path.getsize(filepath) == 0:
            with open(filepath, "w") as f:
                json.dump([], f, indent=2)
            logger.info(f"Initialized empty JSON table: {filepath.name}")
            
    # Seed default user if empty
    users = read_table("users")
    if not users:
        default_user = {
            "UserID": "user_default",
            "UserName": "Demo Student",
            "Email": "student@edugenie.ai",
            "PasswordHash": "pbkdf2:sha256:default_hash_value_here",
            "CreatedAt": datetime.utcnow().isoformat()
        }
        write_record("users", default_user)
        logger.info("Seeded default user 'user_default' in users.json")

def read_table(name: str) -> list:
    """Reads all records from a specific JSON file table."""
    filepath = FILES.get(name)
    if not filepath or not filepath.exists():
        return []
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON table {name}: {str(e)}")
        return []

def write_table(name: str, data: list):
    """Writes the entire list of records to a JSON file table."""
    filepath = FILES.get(name)
    if not filepath:
        return
        
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing to JSON table {name}: {str(e)}")

def write_record(name: str, record: dict):
    """Appends a new record to a JSON table."""
    data = read_table(name)
    data.append(record)
    write_table(name, data)

# --- CRUD HELPER METHODS LINKED TO ER SCHEMAS ---

def log_query(query_id: str, query_type: str, query_text: str, user_id: str = "user_default") -> dict:
    """Inserts a record into queries.json."""
    record = {
        "QueryID": query_id,
        "UserID": user_id,
        "QueryType": query_type,
        "QueryText": query_text,
        "CreatedAt": datetime.utcnow().isoformat()
    }
    write_record("queries", record)
    return record

def log_ai_response(response_id: str, query_id: str, response_text: str, model_used: str) -> dict:
    """Inserts a record into responses.json."""
    record = {
        "ResponseID": response_id,
        "QueryID": query_id,
        "ResponseText": response_text,
        "ModelUsed": model_used,
        "CreatedAt": datetime.utcnow().isoformat()
    }
    write_record("responses", record)
    return record

def log_learning_path(path_id: str, query_id: str, topic: str, level: str, recommended_topics: list) -> dict:
    """Inserts a record into learning_paths.json."""
    record = {
        "PathID": path_id,
        "QueryID": query_id,
        "Topic": topic,
        "Level": level,
        "RecommendedTopics": recommended_topics,
        "CreatedAt": datetime.utcnow().isoformat()
    }
    write_record("learning_paths", record)
    return record

def log_quiz_question(quiz_id: str, query_id: str, question_text: str, options: list, correct_option: str) -> dict:
    """Inserts an MCQ question record into quizzes.json."""
    record = {
        "QuizID": quiz_id,
        "QueryID": query_id,
        "QuestionText": question_text,
        "OptionA": options[0] if len(options) > 0 else "",
        "OptionB": options[1] if len(options) > 1 else "",
        "OptionC": options[2] if len(options) > 2 else "",
        "OptionD": options[3] if len(options) > 3 else "",
        "CorrectOption": correct_option,
        "CreatedAt": datetime.utcnow().isoformat()
    }
    write_record("quizzes", record)
    return record

def log_summary(summary_id: str, query_id: str, original_text: str, summary_text: str, model_used: str) -> dict:
    """Inserts a record into summaries.json."""
    record = {
        "SummaryID": summary_id,
        "QueryID": query_id,
        "OriginalText": original_text,
        "SummaryText": summary_text,
        "ModelUsed": model_used,
        "CreatedAt": datetime.utcnow().isoformat()
    }
    write_record("summaries", record)
    return record
