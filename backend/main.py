from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import multiprocessing
import time

from pipeline import start_pipeline_scheduler
from agents.chatbot import ChatbotAgent

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

class AskResponse(BaseModel):
    answer: str


# --- 3. Define the API Endpoint ---
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    The main endpoint to ask a question to the chatbot.
    
    Receives a question, passes it to the chatbot agent, and returns the answer.
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
        return {"answer": answer_text}
    except Exception as e:
        print(f"ERROR during question processing: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


# --- 4. Main Execution Block for Local Testing ---
# This block allows you to run the API locally for testing using Uvicorn.
# For production, you would typically use a process manager like Gunicorn or systemd.
if __name__ == "__main__":
    # --- Start the background pipeline process ---
    print("Starting main application and background pipeline...")
    
    # Create a separate process for the pipeline scheduler
    pipeline_process = multiprocessing.Process(target=run_pipeline_process, daemon=True)
    pipeline_process.start()
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))

    print(f"Starting FastAPI server on {host}:{port}")
    # Run the FastAPI app
    uvicorn.run(app, host=host, port=port) 