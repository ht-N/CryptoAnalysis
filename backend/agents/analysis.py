import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time

# --- PROMPT ENGINEERING SECTION ---
# Bạn có thể chỉnh sửa prompt dưới đây để cải thiện hiệu suất của mô hình.
# Chỗ `{{content}}` sẽ được thay thế bằng nội dung tin tức thực tế.
PROMPT_TEMPLATE = """
You're an expert in sentiment analysis, you will be provided a news that is about a cryto coin.
Analyze the sentiment of the following news content and classify it as either these three words: 'positive', 'negative', or 'neutral'.
Return only one classification word, between these three, DO NOT RETURN ANY OTHER WORD THAN THESE THREE.

News:
"{{content}}"

Sentiment:
"""
PROMPT_TEMPLATE_VIETNAMESE = """
Bạn là một chuyên gia phân tích cảm xúc, bạn sẽ được cung cấp một tin tức về một đồng tiền mã hóa.
Phân tích cảm xúc của nội dung tin tức sau và phân loại nó thành một trong ba từ này: 'positive', 'negative', hoặc 'neutral'.
Chỉ trả về một từ phân loại, trong số ba từ này, KHÔNG TRẢ VỀ BẤT KỲ TỪ NÀO KHÁC NGOÀI BA TỪ NÀY.

Tin tức:
"{{content}}"

Cảm xúc:
"""

def get_sentiment(content: str, model, prompt_template: str) -> str:
    """
    Calls the Gemini API to get the sentiment of a text.

    Args:
        content: The text content to analyze.
        model: The generative model object.
        prompt_template: The prompt template to use.

    Returns:
        The sentiment label ('positive', 'negative', 'neutral') or 'error'.
    """
    if not content or pd.isna(content):
        return "neutral"
        
    prompt = prompt_template.replace("{{content}}", str(content))
    
    # Simple retry mechanism
    for attempt in range(3):
        try:
            # Increase timeout for the request
            response = model.generate_content(prompt, request_options={'timeout': 120})
            label = response.text.strip().lower()
            if label in ['positive', 'negative', 'neutral']:
                return label
            else:
                print(f"Warning: Unexpected label '{label}' for content: '{content[:50]}...'. Returning 'error'.")
                return 'error'
        except Exception as e:
            print(f"An error occurred on attempt {attempt + 1}: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    print(f"Failed to get sentiment for content after 3 attempts: '{content[:50]}...'")
    return "error"


def run_sentiment_analysis_flow(
    news_df: pd.DataFrame, 
    model, 
    prompt_template: str = PROMPT_TEMPLATE_VIETNAMESE
) -> pd.DataFrame:
    """
    The main tool function for sentiment analysis.
    This function can be imported and used in a larger workflow (e.g., LangGraph).

    Args:
        news_df (pd.DataFrame): A DataFrame with 'coin_name' and 'content' columns.
        model: The initialized generative model object (e.g., genai.GenerativeModel).
        prompt_template (str): The prompt template for sentiment classification.

    Returns:
        pd.DataFrame: The input DataFrame with an added 'label' column for sentiment.
    """
    print(f"--- Running Sentiment Analysis Tool for {len(news_df)} articles ---")
    
    if 'content' not in news_df.columns:
        raise ValueError("Input DataFrame must contain a 'content' column.")

    sentiments = []
    # Use tqdm for a progress bar
    for content in tqdm(news_df['content'], total=news_df.shape[0], desc="Analyzing sentiment"):
        sentiment = get_sentiment(content, model, prompt_template)
        sentiments.append(sentiment)
        time.sleep(2) # Pause between API calls to avoid rate limiting

    results_df = news_df.copy()
    results_df['label'] = sentiments
    
    print("--- Sentiment Analysis Tool Finished ---")
    return results_df


def main():
    """Main function to run the script from the command line."""
    
    # 1. Load environment variables and configure API
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please create a .env file and add your API key.")
        return

    genai.configure(api_key=api_key)
    
    # 2. Initialize the model
    # Use a robust and fast model. 'gemini-1.5-flash' is a great choice.
    model = genai.GenerativeModel('gemma-3n-e4b-it')

    # 3. Load data
    input_csv_path = '../data/binance_news.csv'
    output_csv_path = '../data/analysis.csv'
    
    try:
        # Assuming the CSV from get_news.py has 'coin_name' and 'content' columns
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        return

    # 4. Run sentiment analysis workflow
    analysis_results_df = run_sentiment_analysis_flow(df, model, PROMPT_TEMPLATE_VIETNAMESE)

    # 5. Save results
    analysis_results_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\nAnalysis complete. Results saved to {output_csv_path}")

    # Optional: Display a summary of the sentiment distribution
    # if 'label' in analysis_results_df.columns:
    #     print("\nSentiment Distribution:")
    #     print(analysis_results_df['label'].value_counts())


if __name__ == "__main__":
    main()