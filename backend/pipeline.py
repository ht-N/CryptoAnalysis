import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from typing import TypedDict, List
import operator
import schedule
import time
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END

# --- Import Tools ---
from agents.predict import run_prediction_flow
from agents.get_news import run_news_scraping_flow
from agents.analysis import run_sentiment_analysis_flow
from agents.scorer import run_scoring_flow

# --- 1. Define Agent State ---
# This dictionary defines the data that will be passed between nodes in the graph.
class PipelineState(TypedDict):
    symbols: List[str]
    news_urls: List[str]
    prediction_results: pd.DataFrame
    scraped_news: pd.DataFrame
    sentiment_results: pd.DataFrame
    final_scoring: pd.DataFrame

# --- 2. Define the Agent as a Class ---
class PipelineAgent:
    def __init__(self):
        """
        Initializes the agent, the Gemini model, and builds the graph.
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemma-3n-e4b-it')
        
        # Build the graph when the agent is instantiated
        self.graph = self._build_graph()

    # --- Node Definitions ---
    # Each node is a step in our pipeline. It takes the state, performs an action,
    # and returns a dictionary with the updated state.
    
    def run_prediction_node(self, state: PipelineState) -> dict:
        print("\n--- NODE: RUNNING PREDICTIONS ---")
        symbols = state['symbols']
        predictions_df = run_prediction_flow(symbols=symbols)
        return {"prediction_results": predictions_df}

    def get_news_urls_node(self, state: PipelineState) -> dict:
        print("\n--- NODE: GETTING NEWS URLS ---")
        # In a real-world scenario, you might have a tool to dynamically find news.
        # For now, we read from a predefined CSV as per the original script.
        try:
            news_df = pd.read_csv('data/news.csv')
            urls = news_df['link'].tolist()
            print(f"Found {len(urls)} URLs in data/news.csv")
            return {"news_urls": urls}
        except FileNotFoundError:
            print("Warning: data/news.csv not found. Skipping news scraping.")
            return {"news_urls": []}

    def run_scraping_node(self, state: PipelineState) -> dict:
        print("\n--- NODE: SCRAPING NEWS CONTENT (SELENIUM) ---")
        if not state.get('news_urls'):
            print("No URLs to scrape. Skipping.")
            return {"scraped_news": pd.DataFrame()}
            
        scraped_df = run_news_scraping_flow(urls_to_process=state['news_urls'])
        return {"scraped_news": scraped_df}

    def run_sentiment_analysis_node(self, state: PipelineState) -> dict:
        print("\n--- NODE: ANALYZING SENTIMENT ---")
        scraped_news = state.get('scraped_news')
        if scraped_news is None or scraped_news.empty:
            print("No news to analyze. Skipping.")
            return {"sentiment_results": pd.DataFrame()}
            
        sentiment_df = run_sentiment_analysis_flow(news_df=scraped_news, model=self.model)
        return {"sentiment_results": sentiment_df}

    def run_scoring_node(self, state: PipelineState) -> dict:
        print("\n--- NODE: SCORING COINS ---")
        predictions = state.get('prediction_results')
        sentiments = state.get('sentiment_results')

        if predictions is None or predictions.empty:
            print("Missing prediction data. Skipping scoring.")
            return {"final_scoring": pd.DataFrame()}
        
        if sentiments is None:
            sentiments = pd.DataFrame()
            
        scoring_df = run_scoring_flow(predictions_df=predictions, sentiments_df=sentiments)
        return {"final_scoring": scoring_df}

    # --- Graph Builder ---
    def _build_graph(self):
        """
        Builds the LangGraph workflow.
        """
        workflow = StateGraph(PipelineState)

        # Add nodes
        workflow.add_node("predict", self.run_prediction_node)
        workflow.add_node("get_news", self.get_news_urls_node)
        workflow.add_node("scrape", self.run_scraping_node)
        workflow.add_node("analyze", self.run_sentiment_analysis_node)
        workflow.add_node("score", self.run_scoring_node)

        # Define edges
        workflow.set_entry_point("predict")
        workflow.add_edge("predict", "get_news")
        workflow.add_edge("get_news", "scrape")
        workflow.add_edge("scrape", "analyze")
        workflow.add_edge("analyze", "score")
        workflow.add_edge("score", END)

        # Compile the graph
        return workflow.compile()

    def run(self, symbols: List[str]):
        """
        Invokes the graph with an initial state.

        Args:
            symbols (List[str]): The list of crypto symbols to process.
        
        Returns:
            The final state of the graph after execution.
        """
        initial_state = {"symbols": symbols}
        # Use .invoke() to get the final, accumulated state of the graph.
        # This is more reliable than iterating through the stream for the final result.
        final_state = self.graph.invoke(initial_state)
        return final_state


# --- 3. Main Execution Block ---

def run_job():
    """
    Encapsulates the entire pipeline run, from instantiation to saving results.
    """
    print("="*50)
    print(f"STARTING AUTOMATED CRYPTO ANALYSIS PIPELINE AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Define initial symbols
    initial_symbols = ['BTC-USD', 'ETH-USD', 'XRP-USD', 'SOL-USD', 'DOGE-USD', 'ADA-USD', 'TRX-USD', 'AVAX-USD', 'SUI20947-USD', 'TON11419-USD']
    # initial_symbols = ['BTC-USD']
    
    final_result = None # Initialize to None
    try:
        # Instantiate and run the agent
        agent = PipelineAgent()
        final_result = agent.run(symbols=initial_symbols)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED DURING PIPELINE EXECUTION: {e}")
        import traceback
        traceback.print_exc()

    print("\nPIPELINE EXECUTION FINISHED.")

    # --- Save results to processed data folder ---
    output_dir = "./data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    if final_result:
        print("\n--- Final State Contents ---")
        for key, value in final_result.items():
            if isinstance(value, pd.DataFrame):
                print(f"Key '{key}': DataFrame with {len(value)} rows.")
            else:
                print(f"Key '{key}': {type(value)}")
        print("--------------------------\n")
        
        # Save prediction results
        if 'prediction_results' in final_result and not final_result['prediction_results'].empty:
            final_result['prediction_results'].to_csv(f"{output_dir}/predict.csv", index=False)
            print(f"Saved prediction results to {output_dir}/predict.csv")

        # Save sentiment analysis results
        if 'sentiment_results' in final_result and not final_result['sentiment_results'].empty:
            final_result['sentiment_results'].to_csv(f"{output_dir}/analysis.csv", index=False)
            print(f"Saved sentiment analysis results to {output_dir}/analysis.csv")

        # Save final scoring results
        if 'final_scoring' in final_result and not final_result['final_scoring'].empty:
            final_result['final_scoring'].to_csv(f"{output_dir}/scoring.csv", index=False)
            print(f"Saved final scoring to {output_dir}/scoring.csv")
            
            print("\n--- TOP 5 RANKED COINS ---")
            print(final_result['final_scoring'].head(5))
    else:
        print("Pipeline did not produce a final result.")
    
    next_run_time = datetime.now() + timedelta(minutes=30)
    print("\n" + "="*50)
    print(f"JOB COMPLETE. Next run scheduled for {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")


def start_pipeline_scheduler():
    """
    Starts the scheduler to run the pipeline job periodically.
    """
    # Run the job immediately on startup
    run_job()

    # Schedule the job to run every 1 minutes
    schedule.every(30).minutes.do(run_job)

    print("Pipeline scheduler started. The process will now run every 1 hours.")
    print("Press Ctrl+C on the main server process to stop everything.")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_pipeline_scheduler() 