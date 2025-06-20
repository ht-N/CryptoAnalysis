from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import multiprocessing
import time
from datetime import datetime
from typing import Optional

# Database imports
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from pipeline import start_pipeline_scheduler
from agents.chatbot import ChatbotAgent

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/crypto_chatbot")

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String(10), default="active")  # active, inactive, banned

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # Can be null for anonymous users
    username = Column(String(50), nullable=True)  # Store username for quick access
    user_question = Column(Text, nullable=False)
    bot_answer = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(255), nullable=True)
    conversation_type = Column(String(50), default="general")  # general, price_query, recommendation

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 0. Define a function to run the pipeline in a separate process ---
def run_pipeline_process():
    """
    Wrapper function to start the pipeline scheduler.
    This will be the target for our multiprocessing.Process.
    """
    print("Kicking off background pipeline process...")
    # Add a small delay to ensure the main process starts up first
    time.sleep(5) 
    start_pipeline_scheduler()

# --- 1. Initialize FastAPI App and Chatbot Agent ---
app = FastAPI(
    title="Crypto Analysis Chatbot API",
    description="An API to interact with a RAG-based chatbot for cryptocurrency analysis.",
    version="1.0.0"
)

# ADD CORS MIDDLEWARE - CRITICAL FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Allow OPTIONS for preflight
    allow_headers=["*"],  # Allow all headers
)

# Load the agent only once when the application starts.
# This is crucial for performance as it avoids reloading models and data on every request.
try:
    agent = ChatbotAgent()
    print("Chatbot Agent loaded successfully.")
except FileNotFoundError as e:
    print(f"CRITICAL ERROR: {e}")
    print("Please run the data pipeline (`python run_pipeline.py`) before starting the API server.")
    # We allow the app to start, but the endpoint will raise an error.
    agent = None
except Exception as e:
    print(f"CRITICAL ERROR during agent initialization: {e}")
    agent = None


# --- 2. Define Pydantic Models for Request and Response ---
# These models define the "schema" of our API's inputs and outputs.
# FastAPI uses them for validation and automatic documentation.

class AskRequest(BaseModel):
    question: str
    username: Optional[str] = None  # Optional username for logged-in users

class AskResponse(BaseModel):
    answer: str
    conversation_id: int

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserRegisterResponse(BaseModel):
    success: bool
    user_id: int
    username: str
    message: str

class SaveConversationRequest(BaseModel):
    user_question: str
    bot_answer: str
    username: Optional[str] = None
    session_id: Optional[str] = None
    conversation_type: Optional[str] = "general"

class SaveConversationResponse(BaseModel):
    success: bool
    conversation_id: int
    message: str

class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: str
    total_conversations: int
    is_active: str



# --- 3. Define the API Endpoints ---
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    The main endpoint to ask a question to the chatbot.
    
    Receives a question, passes it to the chatbot agent, and returns the answer.
    Also automatically saves the conversation to the database.
    """
    if agent is None:
        raise HTTPException(
            status_code=503, 
            detail="Chatbot agent is not available. Please check server logs. The data pipeline may need to be run."
        )

    print(f"\nReceived question: {request.question}")
    
    try:
        # Pass the question to the agent's ask method
        answer_text = agent.ask(request.question)
        print(f"Generated answer: {answer_text}")
        
        # Automatically save conversation to database
        try:
            db = next(get_db())
            
            # Get user_id if username provided
            user_id = None
            if request.username:
                user = db.query(User).filter(User.username == request.username).first()
                user_id = user.id if user else None
            
            conversation = ConversationHistory(
                user_id=user_id,
                username=request.username,
                user_question=request.question,
                bot_answer=answer_text,
                timestamp=datetime.utcnow()
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            print(f"Conversation saved to database with ID: {conversation.id}")
            
            return {"answer": answer_text, "conversation_id": conversation.id}
        except Exception as db_error:
            print(f"Warning: Failed to save conversation to database: {db_error}")
            # Don't fail the request if database save fails
            return {"answer": answer_text, "conversation_id": -1}
        finally:
            db.close()
        
    except Exception as e:
        print(f"ERROR during question processing: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.post("/save-conversation", response_model=SaveConversationResponse)
async def save_conversation(request: SaveConversationRequest):
    """
    Endpoint to manually save conversation history to the database.
    
    Receives user question, bot answer, and optional username/session info.
    """
    try:
        db = next(get_db())
        
        # Get user_id if username provided
        user_id = None
        if request.username:
            user = db.query(User).filter(User.username == request.username).first()
            user_id = user.id if user else None
        
        # Create new conversation record
        conversation = ConversationHistory(
            user_id=user_id,
            username=request.username,
            user_question=request.user_question,
            bot_answer=request.bot_answer,
            session_id=request.session_id,
            conversation_type=request.conversation_type,
            timestamp=datetime.utcnow()
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        print(f"Conversation manually saved with ID: {conversation.id}")
        
        return SaveConversationResponse(
            success=True,
            conversation_id=conversation.id,
            message="Conversation saved successfully"
        )
        
    except SQLAlchemyError as e:
        print(f"Database error while saving conversation: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error while saving conversation: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        db.close()


@app.post("/register", response_model=UserRegisterResponse)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user in the system.
    """
    try:
        db = next(get_db())
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new user
        new_user = User(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            created_at=datetime.utcnow(),
            is_active="active"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"New user registered: {new_user.username} (ID: {new_user.id})")
        
        return UserRegisterResponse(
            success=True,
            user_id=new_user.id,
            username=new_user.username,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        print(f"Database error during user registration: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during user registration: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        db.close()


@app.get("/user/{username}", response_model=UserProfileResponse)
async def get_user_profile(username: str):
    """
    Get user profile information including conversation count.
    """
    try:
        db = next(get_db())
        
        # Get user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Count user's conversations
        conversation_count = db.query(ConversationHistory).filter(
            ConversationHistory.user_id == user.id
        ).count()
        
        return UserProfileResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
            total_conversations=conversation_count,
            is_active=user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()


@app.get("/users")
async def get_all_users(limit: int = 50, offset: int = 0):
    """
    Get all users in the system with pagination.
    """
    try:
        db = next(get_db())
        
        users = db.query(User).offset(offset).limit(limit).all()
        total_count = db.query(User).count()
        
        user_list = []
        for user in users:
            # Count conversations for each user
            conv_count = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user.id
            ).count()
            
            user_list.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "total_conversations": conv_count,
                "is_active": user.is_active
            })
        
        return {
            "users": user_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"Error retrieving users: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()


@app.get("/conversation-history")
async def get_conversation_history(
    limit: int = 50, 
    offset: int = 0,
    username: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_type: Optional[str] = None
):
    """
    Endpoint to retrieve conversation history from the database.
    
    Args:
        limit: Number of conversations to return (default: 50)
        offset: Number of conversations to skip (default: 0)
        username: Filter by username (optional)
        session_id: Filter by session ID (optional)
        conversation_type: Filter by conversation type (optional)
    """
    try:
        db = next(get_db())
        
        query = db.query(ConversationHistory)
        
        # Apply filters if provided
        if username:
            query = query.filter(ConversationHistory.username == username)
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        if conversation_type:
            query = query.filter(ConversationHistory.conversation_type == conversation_type)
        
        # Order by timestamp descending and apply pagination
        conversations = query.order_by(ConversationHistory.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Convert to dictionary format
        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "user_id": conv.user_id,
                "username": conv.username,
                "user_question": conv.user_question,
                "bot_answer": conv.bot_answer,
                "timestamp": conv.timestamp.isoformat(),
                "session_id": conv.session_id,
                "conversation_type": conv.conversation_type
            })
        
        return {
            "conversations": result,
            "total_count": len(result),
            "limit": limit,
            "offset": offset,
            "filters": {
                "username": username,
                "session_id": session_id,
                "conversation_type": conversation_type
            }
        }
        
    except SQLAlchemyError as e:
        print(f"Database error while retrieving conversations: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error while retrieving conversations: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        db.close()


@app.get("/database/tables")
async def view_database_tables():
    """
    View all tables in the database with their row counts.
    """
    try:
        db = next(get_db())
        
        # Get table information
        tables_info = []
        
        # Users table
        user_count = db.query(User).count()
        tables_info.append({
            "table_name": "users",
            "description": "Registered users in the system",
            "row_count": user_count,
            "columns": ["id", "username", "email", "full_name", "created_at", "is_active"]
        })
        
        # Conversation history table
        conversation_count = db.query(ConversationHistory).count()
        tables_info.append({
            "table_name": "conversation_history", 
            "description": "All conversations between users and the chatbot",
            "row_count": conversation_count,
            "columns": ["id", "user_id", "username", "user_question", "bot_answer", "timestamp", "session_id", "conversation_type"]
        })
        
        return {
            "database_name": "crypto_chatbot",
            "total_tables": len(tables_info),
            "tables": tables_info
        }
        
    except Exception as e:
        print(f"Error viewing database tables: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()


# --- 4. Main Execution Block for Local Testing ---
# This block allows you to run the API locally for testing using Uvicorn.
# For production, you would typically use a process manager like Gunicorn or systemd.
if __name__ == "__main__":
    # --- Start the background pipeline process ---
    print("🤖 Starting main application and background pipeline...")
    
    # Create a separate process for the pipeline scheduler
    pipeline_process = multiprocessing.Process(target=run_pipeline_process, daemon=True)
    pipeline_process.start()
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")  # 0.0.0.0 makes it accessible from other computers
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Starting FastAPI server on {host}:{port}")
    print(f"📡 Local access: http://localhost:{port}")
    print(f"🌐 Network access: http://YOUR_IP_ADDRESS:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"🗄️  Database: PostgreSQL on localhost:5432")
    print("=" * 60)
    
    # Run the FastAPI app
    uvicorn.run(app, host=host, port=port) 