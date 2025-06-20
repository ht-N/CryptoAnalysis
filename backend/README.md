# Crypto Analysis Chatbot Backend

This is the backend service for the Crypto Analysis Chatbot, built with FastAPI and PostgreSQL.

## Features

- 🤖 AI-powered cryptocurrency analysis chatbot
- 📊 Price prediction using ARIMA and XGBoost models
- 📰 News sentiment analysis using Google Gemini
- 🗄️ PostgreSQL database for conversation history
- 🔄 Automated data pipeline with scheduling
- 🌐 RESTful API with FastAPI

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Google Gemini API key

## Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### 2. Create Database User

```bash
# Access PostgreSQL as superuser
sudo -u postgres psql

# Create user and database
CREATE USER crypto_user WITH PASSWORD 'your_password';
CREATE DATABASE crypto_chatbot OWNER crypto_user;
GRANT ALL PRIVILEGES ON DATABASE crypto_chatbot TO crypto_user;
\q
```

### 3. Configure Environment Variables

Create a `.env` file in the backend directory:

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://crypto_user:your_password@localhost:5432/crypto_chatbot

# Server Configuration
HOST=127.0.0.1
PORT=8000
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup Database Tables

```bash
python database_setup.py
```

## API Endpoints

### Main Endpoints

- `POST /ask` - Ask a question to the chatbot
- `POST /save-conversation` - Manually save conversation history
- `GET /conversation-history` - Retrieve conversation history

### Example Usage

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the price prediction for Bitcoin?"}'
```

**Save conversation:**
```bash
curl -X POST "http://localhost:8000/save-conversation" \
     -H "Content-Type: application/json" \
     -d '{
       "user_question": "How is Ethereum performing?",
       "bot_answer": "Ethereum is showing positive trends...",
       "session_id": "session_123",
       "user_id": "user_456"
     }'
```

**Get conversation history:**
```bash
curl "http://localhost:8000/conversation-history?limit=10&session_id=session_123"
```

## Database Schema

### conversation_history table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_question | TEXT | User's question |
| bot_answer | TEXT | Bot's response |
| timestamp | DATETIME | When the conversation occurred |
| session_id | VARCHAR(255) | Optional session identifier |
| user_id | VARCHAR(255) | Optional user identifier |

## Running the Application

### Development Mode

```bash
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Data Pipeline

The application includes an automated data pipeline that:

1. **News Scraping**: Collects cryptocurrency news from Binance
2. **Sentiment Analysis**: Analyzes news sentiment using Google Gemini
3. **Price Prediction**: Generates price forecasts using ML models
4. **Scoring**: Combines prediction and sentiment data for investment recommendations

## Troubleshooting

### Database Connection Issues

1. Ensure PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Test database connection:
   ```bash
   psql -h localhost -U crypto_user -d crypto_chatbot
   ```

3. Check firewall settings for port 5432

### API Issues

1. Check if the server is running on the correct port
2. Verify environment variables are loaded correctly
3. Check server logs for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

"# MLOPS_food" 
