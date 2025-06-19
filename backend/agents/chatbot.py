import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from typing import TypedDict, Literal, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END


# --- Constants ---
PROCESSED_DATA_DIR = "data/processed"

# Define a custom prompt prefix to guide the agent's reasoning.
# This makes the agent more reliable for specific questions.
PANDAS_AGENT_PREFIX = """
You are an expert at working with pandas dataframes.
You are given a dataframe named `df` that contains cryptocurrency price prediction data. 
The most important columns are: 'coin_name', 'combined_gain_percent', 'current_price', and 'combined_prediction' (the estimated future price).

If the user ask about the predicted price, remember to answer the current price as well, and the 'combined_gain_percent' to let the user know the percentage gain of the coin in the next few days.
When a user asks a question about "growth", "gain", or "tăng trưởng", you MUST use the 'combined_gain_percent' column to find the answer.
When a user asks about "price" or "giá", you should use the 'current_price' and 'combined_prediction' columns.

The percentage gain should be in this format: "2.56%". If the percentage gain is none (eg. 0.0%), you should answer, for example: "dự kiến đồng Bitcoin ổn định trong vài ngày tới."
Based on the user's question, find the relevant information in the dataframe and provide a concise, natural language answer, REMEMBER to answer in USD, for example:
"Giá hiện tại của đồng Bitcoin là 144000$". ALWAY answer in Vietnamese, DO NOT answer in any other language.
"""

# --- 1. Define Agent State ---
class RAGState(TypedDict):
    question: str
    # These dataframes are updated at runtime but included for clarity
    predict_df: pd.DataFrame
    scoring_df: pd.DataFrame
    history: List[BaseMessage]
    route: Literal["price_query", "recommendation_query"]
    answer: str

# --- 2. Define the Agent as a Class ---
class ChatbotAgent:
    def __init__(self):
        """
        Initializes the chatbot, loads data, sets up models and tools.
        The data is loaded dynamically and checked for updates before each query.
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        
        # --- Init LLM and chat history ---
        self.llm = ChatGoogleGenerativeAI(model="gemma-3n-e4b-it", google_api_key=api_key)
        self.chat_history: List[BaseMessage] = []

        # --- Init data holders and timestamps ---
        self.predict_df = None
        self.scoring_df = None
        self.predict_df_timestamp = 0
        self.scoring_df_timestamp = 0
        self.pandas_agent = None
        
        # --- Initial data load and agent setup ---
        # This will raise an error on startup if files don't exist, which is intended.
        self._check_and_reload_data(force_reload=True)
        
        # --- Build Graph ---
        self.graph = self._build_graph()

    def _get_file_timestamp(self, path: str) -> float:
        """Safely gets the last modification time of a file."""
        try:
            return os.path.getmtime(path)
        except FileNotFoundError:
            return 0

    def _check_and_reload_data(self, force_reload: bool = False):
        """
        Checks if the processed data files have been updated and reloads them if necessary.
        Also re-initializes the pandas agent if the prediction data changes.
        """
        predict_path = f"{PROCESSED_DATA_DIR}/predict.csv"
        scoring_path = f"{PROCESSED_DATA_DIR}/scoring.csv"

        current_predict_ts = self._get_file_timestamp(predict_path)
        current_scoring_ts = self._get_file_timestamp(scoring_path)
        
        reloaded_predict = False
        reloaded_scoring = False

        # Reload prediction data if it's new or on a forced reload
        if force_reload or (current_predict_ts > self.predict_df_timestamp and current_predict_ts != 0):
            try:
                print(f"Loading/Reloading prediction data from '{predict_path}'...")
                self.predict_df = pd.read_csv(predict_path)
                self.predict_df_timestamp = current_predict_ts
                # Re-create the pandas agent with the new data
                self.pandas_agent = create_pandas_dataframe_agent(
                    self.llm,
                    self.predict_df,
                    prefix=PANDAS_AGENT_PREFIX,
                    agent_executor_kwargs={"handle_parsing_errors": True},
                    verbose=True,
                    allow_dangerous_code=True
                )
                print("Prediction data and agent reloaded successfully.")
                reloaded_predict = True
            except Exception as e:
                print(f"Error reloading prediction data: {e}")
                if force_reload: raise e # Fail on startup if initial load fails

        # Reload scoring data if it's new or on a forced reload
        if force_reload or (current_scoring_ts > self.scoring_df_timestamp and current_scoring_ts != 0):
            try:
                print(f"Loading/Reloading scoring data from '{scoring_path}'...")
                self.scoring_df = pd.read_csv(scoring_path)
                self.scoring_df_timestamp = current_scoring_ts
                print("Scoring data reloaded successfully.")
                reloaded_scoring = True
            except Exception as e:
                print(f"Error reloading scoring data: {e}")
                if force_reload: raise e

        # On initial startup (force_reload=True), ensure all data was loaded.
        if force_reload and not (reloaded_predict and reloaded_scoring):
            raise FileNotFoundError("One or more processed data files not found on initial load. Please run `run_pipeline.py` first.")

    # --- Node Definitions ---
    
    def route_question_node(self, state: RAGState) -> dict:
        """
        Classifies the user's question to decide the workflow path.
        """
        print("\n--- NODE: ROUTING QUESTION ---")
        history = state['history']
        question = state['question']

        # Format history for the prompt to give context
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

        prompt = f"""
        Based on the conversation history, classify the user's latest question into one of two categories:
        1. `price_query`: The user is asking about the current price, estimated price, or predicted gain of one or more specific cryptocurrencies. This includes follow-up questions about other coins.
        2. `recommendation_query`: The user is asking for a recommendation, analysis, ranking, reliability, or score of which coin to invest in.

        Conversation History:
        {history_str}

        User Question: "{state['question']}"
        Classification:
        """
        response = self.llm.invoke(prompt)
        route = response.content.strip().lower()
        
        if "price_query" in route:
            print("Route: price_query")
            return {"route": "price_query"}
        else:
            print("Route: recommendation_query")
            return {"route": "recommendation_query"}

    def run_price_rag_node(self, state: RAGState) -> dict:
        """
        Uses the Pandas DataFrame Agent to answer price-related questions.
        """
        print("\n--- NODE: RUNNING PRICE RAG ---")
        question = state['question']
        history = state['history']
        # The pandas agent can accept chat_history directly.
        response = self.pandas_agent.invoke({
            "input": question,
            "chat_history": history
        })
        return {"answer": response['output']}

    def run_recommendation_rag_node(self, state: RAGState) -> dict:
        """
        Uses the scoring data and an LLM to answer recommendation questions.
        """
        print("\n--- NODE: RUNNING RECOMMENDATION RAG ---")
        question = state['question']
        history = state['history']
        # Convert the top 10 scoring rows to a string to use as context
        context = self.scoring_df.head(10).to_string()
        
        # Format history for the prompt to give context
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

        prompt = f"""
        You are a crypto analyst assistant. Answer the user's question based on the conversation history and the following data, which includes prediction scores and sentiment analysis scores.
        The score is described as follow:
        0 - 1: Không nên đánh
        1 - 2: Trung bình
        2 - 10: Tốt, nên đánh

        Conversation History:
        {history_str}
        
        Data:
        {context}

        User Question: {question}

        Answer:
        """
        response = self.llm.invoke(prompt)
        return {"answer": response.content}

    # --- Graph Builder ---
    def _build_graph(self):
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("router", self.route_question_node)
        workflow.add_node("price_rag", self.run_price_rag_node)
        workflow.add_node("recommendation_rag", self.run_recommendation_rag_node)

        # Define entry and conditional edges
        workflow.set_entry_point("router")
        workflow.add_conditional_edges(
            "router",
            lambda x: x["route"],
            {
                "price_query": "price_rag",
                "recommendation_query": "recommendation_rag",
            },
        )
        
        # Define end points
        workflow.add_edge("price_rag", END)
        workflow.add_edge("recommendation_rag", END)

        return workflow.compile()

    def ask(self, question: str):
        """
        Invokes the RAG graph to answer a user's question.
        Checks for data updates before running.
        """
        # Check for any new data from the pipeline before answering
        self._check_and_reload_data()
        
        if self.pandas_agent is None or self.scoring_df is None:
            return "Chatbot data is not loaded correctly. Please ensure the pipeline has run successfully at least once."

        initial_state = {
            "question": question,
            "predict_df": self.predict_df,
            "scoring_df": self.scoring_df,
            "history": self.chat_history,
        }
        final_state = self.graph.invoke(initial_state)
        answer = final_state['answer']

        # Update history with the new interaction
        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=answer))

        # Keep only the last 3 interactions (3 pairs of human/ai messages)
        if len(self.chat_history) > 6:
            self.chat_history = self.chat_history[-6:]

        return answer


# --- 3. Main Execution Block ---
if __name__ == "__main__":
    print("🤖 Crypto Chatbot is ready. Type 'quit' to exit.")
    
    try:
        agent = ChatbotAgent()
        while True:
            user_question = input("\n> ")
            if user_question.lower() == 'quit':
                break
            
            answer = agent.ask(user_question)
            print(f"\nChatbot: {answer}")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please make sure you have run the pipeline first by executing `python run_pipeline.py`")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}") 