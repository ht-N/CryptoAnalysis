# 🚀 Quick Setup Guide - Crypto Chatbot with User System

## 📋 Prerequisites
- PostgreSQL installed and running
- Python 3.8+
- Google Gemini API key

## ⚡ Quick Setup Steps

### 1. Setup Database
```bash
# Install PostgreSQL and create user/database in pgAdmin:
CREATE USER crypto_user WITH PASSWORD 'crypto_password';
CREATE DATABASE crypto_chatbot OWNER crypto_user;
GRANT ALL PRIVILEGES ON DATABASE crypto_chatbot TO crypto_user;
```

### 2. Configure Environment
Create `.env` file in backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://crypto_user:crypto_password@localhost:5432/crypto_chatbot
HOST=127.0.0.1
PORT=8000
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Setup Database Tables
```bash
python database_setup.py
```

### 5. Create Sample Data
```bash
python sample_data.py
```

### 6. Start the Server
```bash
python main.py
```

## 🎯 API Endpoints Overview

### User Management
- `POST /register` - Register new user
- `GET /user/{username}` - Get user profile
- `GET /users` - List all users

### Conversations
- `POST /ask` - Ask chatbot (with optional username)
- `POST /save-conversation` - Save conversation manually
- `GET /conversation-history` - View conversation history

### Database
- `GET /database/tables` - View database structure

## 🧪 Test the System

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username", 
    "email": "your@email.com",
    "full_name": "Your Name"
  }'
```

### 2. Ask a Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Bitcoin giá bao nhiêu?",
    "username": "your_username"
  }'
```

### 3. View Your Profile
```bash
curl "http://localhost:8000/user/your_username"
```

### 4. View All Tables
```bash
curl "http://localhost:8000/database/tables"
```

## 📊 Database Schema

### users Table
- `id` - Primary key
- `username` - Unique username
- `email` - User email
- `full_name` - Full name
- `created_at` - Registration date
- `is_active` - Account status

### conversation_history Table  
- `id` - Primary key
- `user_id` - Link to user (optional)
- `username` - Username for quick access
- `user_question` - User's question
- `bot_answer` - Bot's response
- `timestamp` - When conversation happened
- `session_id` - Session identifier
- `conversation_type` - Type of conversation

## 🔧 pgAdmin 4 Connection
- **Host:** localhost
- **Port:** 5432
- **Database:** crypto_chatbot
- **Username:** crypto_user
- **Password:** crypto_password

## ✅ Sample Data Included
After running `sample_data.py`, you'll have:
- 4 sample users (john_trader, crypto_alice, btc_bob, demo_user)
- 7 sample conversations with Vietnamese responses
- Different conversation types (price_query, recommendation_query, general)

Browse to `http://localhost:8000/docs` for interactive API documentation! 