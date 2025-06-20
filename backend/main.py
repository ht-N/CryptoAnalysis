from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import multiprocessing
import time
from datetime import datetime
from typing import Optional, List
import asyncio

# MongoDB imports
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from bson import ObjectId

from pipeline import start_pipeline_scheduler
from agents.chatbot import ChatbotAgent

# --- MongoDB Configuration ---
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1")
DATABASE_NAME = "crypto_chatbot"

# Global MongoDB client and database
mongo_client = None
database = None

async def connect_to_mongodb():
    """Connect to MongoDB"""
    global mongo_client, database
    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        database = mongo_client[DATABASE_NAME]
        
        # Test connection
        await mongo_client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()

def convert_objectid_to_str(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

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

# --- FastAPI Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB when the app starts"""
    await connect_to_mongodb()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection when the app shuts down"""
    await close_mongodb_connection()

# --- 2. Define Pydantic Models for Request and Response ---
# These models define the "schema" of our API's inputs and outputs.
# FastAPI uses them for validation and automatic documentation.

class AskRequest(BaseModel):
    question: str
    username: Optional[str] = None  # Optional username for logged-in users

class AskResponse(BaseModel):
    answer: str
    conversation_id: str

class UserRegisterRequest(BaseModel):
    name: str
    age: int
    currency: int  # Amount in VND
    description: str
    address: str
    country: Optional[str] = "Vietnam"
    preferred_language: Optional[str] = "vi"

class UserRegisterResponse(BaseModel):
    success: bool
    user_id: str
    name: str
    message: str

class SaveConversationRequest(BaseModel):
    user_question: str
    bot_answer: str
    username: Optional[str] = None
    session_id: Optional[str] = None
    conversation_type: Optional[str] = "general"

class SaveConversationResponse(BaseModel):
    success: bool
    conversation_id: str
    message: str

class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    age: int
    currency: int
    description: str
    address: str
    country: str
    preferred_language: str
    created_at: str
    updated_at: str
    total_conversations: int
    is_active: bool

# --- Sample Users CRUD Models ---
class SampleUserCreate(BaseModel):
    name: str
    age: int
    currency: int  # Amount in VND
    description: str
    address: str

class SampleUserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    currency: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None

class SampleUserResponse(BaseModel):
    id: str
    name: str
    age: int
    currency: int
    description: str
    address: str
    created_at: str
    updated_at: str
    is_active: bool
    country: str
    preferred_language: str


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
            # Get user_id if username provided
            user_id = None
            if request.username:
                user = await database.users.find_one({"username": request.username})
                user_id = str(user["_id"]) if user else None
            
            conversation_doc = {
                "user_id": user_id,
                "username": request.username,
                "user_question": request.question,
                "bot_answer": answer_text,
                "timestamp": datetime.utcnow(),
                "session_id": f"session_{datetime.utcnow().timestamp()}",
                "conversation_type": "general"
            }
            
            result = await database.conversation_history.insert_one(conversation_doc)
            conversation_id = str(result.inserted_id)
            print(f"Conversation saved to database with ID: {conversation_id}")
            
            return {"answer": answer_text, "conversation_id": conversation_id}
        except Exception as db_error:
            print(f"Warning: Failed to save conversation to database: {db_error}")
            # Don't fail the request if database save fails
            return {"answer": answer_text, "conversation_id": "error"}
            
    except Exception as e:
        print(f"Error generating answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.post("/save-conversation", response_model=SaveConversationResponse)
async def save_conversation(request: SaveConversationRequest):
    """
    Save a conversation to the database.
    
    This endpoint allows manual saving of conversations that may have been processed
    outside of the main /ask endpoint.
    """
    try:
        # Get user_id if username provided
        user_id = None
        if request.username:
            user = await database.users.find_one({"username": request.username})
            user_id = str(user["_id"]) if user else None
        
        conversation_doc = {
            "user_id": user_id,
            "username": request.username,
            "user_question": request.user_question,
            "bot_answer": request.bot_answer,
            "timestamp": datetime.utcnow(),
            "session_id": request.session_id or f"session_{datetime.utcnow().timestamp()}",
            "conversation_type": request.conversation_type or "general"
        }
        
        result = await database.conversation_history.insert_one(conversation_doc)
        conversation_id = str(result.inserted_id)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation saved successfully"
        }
        
    except Exception as e:
        print(f"Error saving conversation: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save conversation: {str(e)}"
        )


@app.post("/register", response_model=UserRegisterResponse)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user.
    
    Creates a new user with same fields as sample_users collection.
    Names don't need to be unique since multiple people can have same names.
    """
    try:
        # Create new user document (using same structure as sample_users)
        user_doc = {
            "name": request.name,
            "age": request.age,
            "currency": request.currency,
            "description": request.description,
            "address": request.address,
            "country": request.country,
            "preferred_language": request.preferred_language,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "join_date": datetime.utcnow().strftime("%Y-%m-%d")
        }
        
        # Insert into users collection (not sample_users)
        result = await database.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "name": request.name,
            "message": f"User '{request.name}' registered successfully"
        }
        
    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register user: {str(e)}"
        )


@app.get("/user/{name}", response_model=UserProfileResponse)
async def get_user_profile(name: str):
    """
    Get a user's profile information including conversation count.
    
    Returns user details and statistics about their conversation history.
    """
    try:
        # Find user by name
        user = await database.users.find_one({"name": name})
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User '{name}' not found"
            )
        
        # Count user's conversations (search by user_id or name-based username)
        name_username = name.replace(" ", "_").lower()
        conversation_count = await database.conversation_history.count_documents({
            "$or": [
                {"user_id": str(user["_id"])},
                {"username": name_username}
            ]
        })
        
        return {
            "user_id": str(user["_id"]),
            "name": user["name"],
            "age": user["age"],
            "currency": user["currency"],
            "description": user["description"],
            "address": user["address"],
            "country": user.get("country", "Vietnam"),
            "preferred_language": user.get("preferred_language", "vi"),
            "created_at": user["created_at"].isoformat(),
            "updated_at": user.get("updated_at", user["created_at"]).isoformat(),
            "total_conversations": conversation_count,
            "is_active": user.get("is_active", True)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user profile: {str(e)}"
        )


@app.get("/users")
async def get_all_users(limit: int = 50, offset: int = 0):
    """
    Get a list of all users with pagination.
    
    Returns basic user information with optional limit and offset for pagination.
    """
    try:
        # Get users with pagination
        users_cursor = database.users.find({}).skip(offset).limit(limit)
        users = await users_cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        users_list = []
        for user in users:
            user_data = {
                "user_id": str(user["_id"]),
                "name": user["name"],
                "age": user["age"],
                "currency": user["currency"],
                "description": user["description"],
                "address": user["address"],
                "country": user.get("country", "Vietnam"),
                "preferred_language": user.get("preferred_language", "vi"),
                "created_at": user["created_at"].isoformat(),
                "updated_at": user.get("updated_at", user["created_at"]).isoformat(),
                "is_active": user.get("is_active", True)
            }
            users_list.append(user_data)
        
        # Get total count
        total_users = await database.users.count_documents({})
        
        return {
            "users": users_list,
            "total": total_users,
            "limit": limit,
            "offset": offset,
            "message": f"Retrieved {len(users_list)} users"
        }
        
    except Exception as e:
        print(f"Error getting users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get users: {str(e)}"
        )


@app.get("/conversation-history")
async def get_conversation_history(
    limit: int = 50, 
    offset: int = 0,
    username: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_type: Optional[str] = None
):
    """
    Get conversation history with optional filtering.
    
    Can filter by username, session_id, or conversation_type.
    Results are paginated with limit and offset.
    """
    try:
        # Build filter query
        filter_query = {}
        
        if username:
            filter_query["username"] = username
        if session_id:
            filter_query["session_id"] = session_id
        if conversation_type:
            filter_query["conversation_type"] = conversation_type
        
        # Get conversations with pagination, sorted by timestamp (newest first)
        conversations_cursor = database.conversation_history.find(filter_query).sort("timestamp", DESCENDING).skip(offset).limit(limit)
        conversations = await conversations_cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings and format response
        conversations_list = []
        for conv in conversations:
            conv_data = {
                "conversation_id": str(conv["_id"]),
                "user_id": conv.get("user_id"),
                "username": conv.get("username"),
                "user_question": conv["user_question"],
                "bot_answer": conv["bot_answer"],
                "timestamp": conv["timestamp"].isoformat(),
                "session_id": conv.get("session_id"),
                "conversation_type": conv.get("conversation_type", "general")
            }
            conversations_list.append(conv_data)
        
        # Get total count
        total_conversations = await database.conversation_history.count_documents(filter_query)
        
        return {
            "conversations": conversations_list,
            "total": total_conversations,
            "limit": limit,
            "offset": offset,
            "filters": {
                "username": username,
                "session_id": session_id,
                "conversation_type": conversation_type
            },
            "message": f"Retrieved {len(conversations_list)} conversations"
        }
        
    except Exception as e:
        print(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@app.get("/database/tables")
async def view_database_tables():
    """
    View database collections and their document counts.
    
    This endpoint provides information about the database structure,
    similar to viewing tables in a SQL database.
    """
    try:
        # Get all collection names
        collections = await database.list_collection_names()
        
        # Get statistics for each collection
        collection_stats = []
        
        for collection_name in collections:
            collection = database[collection_name]
            
            # Get document count
            doc_count = await collection.count_documents({})
            
            # Get a sample document to show structure
            sample_doc = await collection.find_one({})
            sample_structure = {}
            
            if sample_doc:
                # Show field names and types
                for key, value in sample_doc.items():
                    if key == "_id":
                        sample_structure[key] = "ObjectId"
                    else:
                        sample_structure[key] = type(value).__name__
            
            collection_stats.append({
                "collection_name": collection_name,
                "document_count": doc_count,
                "sample_structure": sample_structure
            })
        
        return {
            "database_name": DATABASE_NAME,
            "collections": collection_stats,
            "total_collections": len(collections),
            "connection_status": "connected",
            "message": f"Database has {len(collections)} collections"
        }
        
    except Exception as e:
        print(f"Error viewing database tables: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to view database structure: {str(e)}"
        )


# --- SAMPLE USERS CRUD ENDPOINTS ---

@app.post("/sample-users", response_model=SampleUserResponse)
async def create_sample_user(user: SampleUserCreate):
    """Create a new sample user"""
    try:
        # Check if user with same name already exists
        existing_user = await database.sample_users.find_one({"name": user.name})
        if existing_user:
            raise HTTPException(status_code=400, detail=f"User với tên '{user.name}' đã tồn tại")
        
        # Create user document
        user_doc = {
            "name": user.name,
            "age": user.age,
            "currency": user.currency,
            "description": user.description,
            "address": user.address,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "country": "Vietnam",
            "preferred_language": "vi"
        }
        
        # Insert into database
        result = await database.sample_users.insert_one(user_doc)
        
        # Get the created user
        created_user = await database.sample_users.find_one({"_id": result.inserted_id})
        
        # Convert to response format
        return SampleUserResponse(
            id=str(created_user["_id"]),
            name=created_user["name"],
            age=created_user["age"],
            currency=created_user["currency"],
            description=created_user["description"],
            address=created_user["address"],
            created_at=created_user["created_at"].isoformat(),
            updated_at=created_user["updated_at"].isoformat(),
            is_active=created_user["is_active"],
            country=created_user["country"],
            preferred_language=created_user["preferred_language"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo user: {str(e)}")

@app.get("/sample-users", response_model=List[SampleUserResponse])
async def get_sample_users(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_currency: Optional[int] = None,
    max_currency: Optional[int] = None
):
    """Get all sample users with filtering and pagination"""
    try:
        # Build filter query
        filter_query = {"is_active": True}
        
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"address": {"$regex": search, "$options": "i"}}
            ]
        
        if min_age is not None:
            filter_query["age"] = {"$gte": min_age}
        if max_age is not None:
            if "age" in filter_query:
                filter_query["age"]["$lte"] = max_age
            else:
                filter_query["age"] = {"$lte": max_age}
        
        if min_currency is not None:
            filter_query["currency"] = {"$gte": min_currency}
        if max_currency is not None:
            if "currency" in filter_query:
                filter_query["currency"]["$lte"] = max_currency
            else:
                filter_query["currency"] = {"$lte": max_currency}
        
        # Get users with pagination
        users = await database.sample_users.find(filter_query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=None)
        
        # Convert to response format
        result = []
        for user in users:
            result.append(SampleUserResponse(
                id=str(user["_id"]),
                name=user["name"],
                age=user["age"],
                currency=user["currency"],
                description=user["description"],
                address=user["address"],
                created_at=user["created_at"].isoformat(),
                updated_at=user["updated_at"].isoformat(),
                is_active=user["is_active"],
                country=user["country"],
                preferred_language=user["preferred_language"]
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách users: {str(e)}")

@app.get("/sample-users/{user_id}", response_model=SampleUserResponse)
async def get_sample_user(user_id: str):
    """Get a specific sample user by ID"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="ID không hợp lệ")
        
        # Find user
        user = await database.sample_users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user")
        
        # Convert to response format
        return SampleUserResponse(
            id=str(user["_id"]),
            name=user["name"],
            age=user["age"],
            currency=user["currency"],
            description=user["description"],
            address=user["address"],
            created_at=user["created_at"].isoformat(),
            updated_at=user["updated_at"].isoformat(),
            is_active=user["is_active"],
            country=user["country"],
            preferred_language=user["preferred_language"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy thông tin user: {str(e)}")

@app.put("/sample-users/{user_id}", response_model=SampleUserResponse)
async def update_sample_user(user_id: str, user_update: SampleUserUpdate):
    """Update a sample user"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="ID không hợp lệ")
        
        # Check if user exists
        existing_user = await database.sample_users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user")
        
        # Build update document (only include fields that are not None)
        update_doc = {"updated_at": datetime.utcnow()}
        
        if user_update.name is not None:
            # Check if another user with same name exists
            name_check = await database.sample_users.find_one({
                "name": user_update.name,
                "_id": {"$ne": ObjectId(user_id)}
            })
            if name_check:
                raise HTTPException(status_code=400, detail=f"User với tên '{user_update.name}' đã tồn tại")
            update_doc["name"] = user_update.name
        
        if user_update.age is not None:
            update_doc["age"] = user_update.age
        if user_update.currency is not None:
            update_doc["currency"] = user_update.currency
        if user_update.description is not None:
            update_doc["description"] = user_update.description
        if user_update.address is not None:
            update_doc["address"] = user_update.address
        
        # Update user
        result = await database.sample_users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Không có thay đổi nào được thực hiện")
        
        # Get updated user
        updated_user = await database.sample_users.find_one({"_id": ObjectId(user_id)})
        
        # Convert to response format
        return SampleUserResponse(
            id=str(updated_user["_id"]),
            name=updated_user["name"],
            age=updated_user["age"],
            currency=updated_user["currency"],
            description=updated_user["description"],
            address=updated_user["address"],
            created_at=updated_user["created_at"].isoformat(),
            updated_at=updated_user["updated_at"].isoformat(),
            is_active=updated_user["is_active"],
            country=updated_user["country"],
            preferred_language=updated_user["preferred_language"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật user: {str(e)}")

@app.delete("/sample-users/{user_id}")
async def delete_sample_user(user_id: str):
    """Delete a sample user (soft delete - mark as inactive)"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="ID không hợp lệ")
        
        # Check if user exists
        existing_user = await database.sample_users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user")
        
        # Soft delete (mark as inactive)
        result = await database.sample_users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Không thể xóa user")
        
        return {
            "success": True,
            "message": f"User '{existing_user['name']}' đã được xóa thành công",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa user: {str(e)}")

@app.get("/sample-users/stats/summary")
async def get_sample_users_stats():
    """Get statistics about sample users"""
    try:
        # Get basic counts
        total_users = await database.sample_users.count_documents({"is_active": True})
        total_inactive = await database.sample_users.count_documents({"is_active": False})
        
        # Get age statistics
        age_pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "avg_age": {"$avg": "$age"},
                "min_age": {"$min": "$age"},
                "max_age": {"$max": "$age"}
            }}
        ]
        age_stats = await database.sample_users.aggregate(age_pipeline).to_list(length=1)
        
        # Get currency statistics
        currency_pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "total_currency": {"$sum": "$currency"},
                "avg_currency": {"$avg": "$currency"},
                "min_currency": {"$min": "$currency"},
                "max_currency": {"$max": "$currency"}
            }}
        ]
        currency_stats = await database.sample_users.aggregate(currency_pipeline).to_list(length=1)
        
        # Get top cities
        city_pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$address",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_cities = await database.sample_users.aggregate(city_pipeline).to_list(length=5)
        
        return {
            "total_active_users": total_users,
            "total_inactive_users": total_inactive,
            "age_statistics": age_stats[0] if age_stats else None,
            "currency_statistics": currency_stats[0] if currency_stats else None,
            "top_cities": top_cities,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy thống kê: {str(e)}")

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    """
    try:
        # Test MongoDB connection
        await mongo_client.admin.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "agent_loaded": agent is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


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
    print(f"🗄️  Database: MongoDB Cloud")
    print("=" * 60)
    
    # Run the FastAPI app
    uvicorn.run(app, host=host, port=port) 