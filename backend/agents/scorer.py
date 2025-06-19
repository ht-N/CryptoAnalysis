import pandas as pd

def _calculate_prediction_score(gain_percent: float) -> int:
    """
    Calculates a score based on the predicted gain percentage.

    Args:
        gain_percent (float): The combined gain percentage.

    Returns:
        int: The calculated score based on predefined tiers.
    """
    if gain_percent < 0:
        return 0
    elif 0 <= gain_percent < 2:
        return 1
    elif 2 <= gain_percent < 4:
        return 2
    elif 4 <= gain_percent < 6:
        return 3
    elif 6 <= gain_percent < 8:
        return 4
    else:  # gain_percent >= 8
        return 8

def run_scoring_flow(predictions_df: pd.DataFrame, sentiments_df: pd.DataFrame) -> pd.DataFrame:
    """
    The main tool function for scoring cryptocurrencies.
    It calculates scores based on prediction gains and news sentiment.

    Args:
        predictions_df (pd.DataFrame): DataFrame from the prediction tool.
                                       Expected columns: 'coin_name', 'combined_gain_percent'.
        sentiments_df (pd.DataFrame): DataFrame from the analysis tool.
                                      Expected columns: 'coin_name', 'label'.

    Returns:
        pd.DataFrame: A DataFrame with coins, their scores, and final ranking.
    """
    print("--- Running Coin Scoring Tool ---")

    # 1. Standardize coin names using the explicit user-defined mapping.
    if not sentiments_df.empty:
        
        # User-defined mapping from news names (uppercase) to canonical symbols.
        name_to_symbol_map = {
            'BITCOIN': 'BTC',
            'ETHEREUM': 'ETH',
            'DOGECOIN': 'DOGE',
            'AVAXUSDT': 'AVAX',
            'XRP': 'XRP',
            'SUI': 'SUI20947',
            'ADA': 'ADA',
            'TONCOIN': 'TON11419',
            'SOL': 'SOL',
            'BNB': 'BNB',
            'TRX': 'TRX',
        }
        
        def standardize_name(long_name):
            # Cleans and maps a name from the news data to a canonical symbol.
            # Converts to uppercase for case-insensitive matching.
            upper_name = str(long_name).upper()
            # Return the mapped symbol or the original name if not in the map.
            return name_to_symbol_map.get(upper_name, upper_name)
            
        print("Standardizing coin names using explicit user-defined mapping...")
        sentiments_df['coin_name'] = sentiments_df['coin_name'].apply(standardize_name)

    # 2. Calculate sentiment score from the now-standardized sentiments_df
    if sentiments_df.empty:
        sentiment_scores_df = pd.DataFrame(columns=['coin_name', 'sentiment_score'])
    else:
        sentiment_counts = sentiments_df.groupby('coin_name')['label'].value_counts().unstack(fill_value=0)
        
        if 'positive' not in sentiment_counts.columns:
            sentiment_counts['positive'] = 0
            
        sentiment_counts['total'] = sentiment_counts.sum(axis=1)
        sentiment_counts['sentiment_score'] = sentiment_counts.apply(
            lambda row: row['positive'] / row['total'] if row['total'] > 0 else 0,
            axis=1
        )
        sentiment_scores_df = sentiment_counts[['sentiment_score']].reset_index()

    # 3. Calculate prediction score from predictions_df
    predictions_df['prediction_score'] = predictions_df['combined_gain_percent'].apply(_calculate_prediction_score)

    # 4. Merge prediction data with sentiment scores on the standardized 'coin_name'
    final_df = pd.merge(predictions_df, sentiment_scores_df, on='coin_name', how='left')
    final_df['sentiment_score'].fillna(0, inplace=True)

    # 5. Calculate total score
    final_df['total_score'] = final_df['prediction_score'] + final_df['sentiment_score']
    
    # 6. Format the final DataFrame for user-friendly display
    output_df = final_df[[
        'coin_name',
        'current_price',
        'combined_prediction',
        'combined_gain_percent',
        'prediction_score',
        'sentiment_score',
        'total_score'
    ]].copy()
    
    output_df.rename(columns={
        'coin_name': 'Coin Name',
        'current_price': 'Current Price',
        'combined_prediction': 'Estimated Price',
        'combined_gain_percent': 'Combined Gain %',
        'prediction_score': 'Prediction Score',
        'sentiment_score': 'Sentiment Score',
        'total_score': 'Total Score'
    }, inplace=True)

    # 7. Sort by the final score in descending order
    output_df = output_df.sort_values(by='Total Score', ascending=False).reset_index(drop=True)
    
    print("--- Coin Scoring Tool Finished ---")
    
    return output_df

if __name__ == '__main__':
    # This block allows you to test the tool independently
    print("--- Testing scorer.py ---")
    
    # Create dummy dataframes to simulate the outputs of other tools
    predict_data = {
        'coin_name': ['BTC', 'ETH', 'XRP', 'DOGE', 'SUI20947', 'TON11419'],
        'current_price': [60000, 3000, 0.5, 0.15, 1.0, 6.0],
        'combined_prediction': [63000, 3300, 0.49, 0.15, 1.2, 7.0],
        'combined_gain_percent': [5.0, 10.0, -2.0, 0.0, 20.0, 16.6],
        'arima_gain_percent': [4.0, 9.0, -2.0, 0.0, 18.0, 15.0],
        'xgboost_gain_percent': [6.0, 11.0, -2.0, 0.0, 22.0, 18.0]
    }
    predictions = pd.DataFrame(predict_data)

    analysis_data = {
        'coin_name': ['BITCOIN', 'ETHEREUM', 'SUI', 'TONCOIN'],
        'content': ['...']*4,
        'label': ['positive', 'negative', 'positive', 'positive']
    }
    sentiments = pd.DataFrame(analysis_data)
    
    # Run the scoring flow
    scoring_result = run_scoring_flow(predictions, sentiments)
    
    print("\n--- Final Scoring Result ---")
    print(scoring_result)

    # Expected output explanation for BTC:
    # Prediction Gain is 5.0% -> prediction_score = 3
    # Sentiment is 2 positive out of 3 total -> sentiment_score = 0.666
    # Total score = 3 + 0.666 = 3.666
    
    # Expected output explanation for ETH:
    # Prediction Gain is 10.0% -> prediction_score = 8
    # Sentiment is 1 positive out of 2 total -> sentiment_score = 0.5
    # Total score = 8 + 0.5 = 8.5
    
    # Expected output explanation for XRP:
    # Prediction Gain is -2.0% -> prediction_score = 0
    # No news -> sentiment_score = 0
    # Total score = 0 + 0 = 0
    
    # Expected output explanation for DOGE:
    # Prediction Gain is 0.0% -> prediction_score = 1
    # No news -> sentiment_score = 0
    # Total score = 1 + 0 = 1
    
    # Expected output explanation for SUI:
    # 'SUI' from news is mapped to 'SUI20947' to match prediction data.
    # Prediction Gain is 20.0% -> prediction_score = 8
    # Sentiment is 1 positive out of 1 total -> sentiment_score = 1.0
    # Total score = 8 + 1.0 = 9.0
    
    # Expected output explanation for TONCOIN:
    # 'TONCOIN' from news is mapped to 'TON11419'.
    # Prediction Gain is 16.6% -> prediction_score = 8
    # Sentiment is 1 positive out of 1 total -> sentiment_score = 1.0
    # Total score = 8 + 1.0 = 9.0 