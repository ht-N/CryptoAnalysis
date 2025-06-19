import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from itertools import product
import warnings

warnings.filterwarnings("ignore")


class CryptoPricePredictor:
    """
    A class to predict cryptocurrency prices using ARIMA and XGBoost models
    and calculate gain percentages for investment recommendations.
    """
    
    def __init__(self, symbols_csv_path='../../data/symbols.csv', predict_days=5):
        """
        Initialize the predictor with symbols and prediction parameters.
        
        Args:
            symbols_csv_path (str): Path to CSV file containing cryptocurrency symbols
            predict_days (int): Number of days ahead to predict
        """
        self.predict_days = predict_days
        self.symbols = self._load_symbols(symbols_csv_path)
        self.results = []
        
    def _load_symbols(self, csv_path):
        """Load cryptocurrency symbols from CSV file."""
        try:
            df = pd.read_csv(csv_path)
            return df['symbol'].tolist()
        except Exception as e:
            print(f"Error loading symbols: {e}")
            return ['BTC-USD', 'ETH-USD', 'XRP-USD']  # Fallback symbols
    
    def create_features(self, df, target_column, window_sizes=[5, 10, 20]):
        """
        Create time series features for XGBoost model.
        
        Args:
            df (pd.DataFrame): Input dataframe with price data
            target_column (str): Column name for target variable
            window_sizes (list): List of window sizes for rolling features
            
        Returns:
            pd.DataFrame: DataFrame with engineered features
        """
        df_features = df.copy()
        
        # Add rolling statistics
        for window in window_sizes:
            df_features[f'rolling_mean_{window}'] = df[target_column].rolling(window=window).mean()
            df_features[f'rolling_std_{window}'] = df[target_column].rolling(window=window).std()
            
        # Add lag features
        for lag in range(1, max(window_sizes) + 1):
            df_features[f'lag_{lag}'] = df[target_column].shift(lag)
        
        # Add price momentum
        for window in window_sizes:
            df_features[f'momentum_{window}'] = df[target_column].pct_change(periods=window)
        
        # Add target column for future prediction
        df_features[f'target_{self.predict_days}d'] = df[target_column].shift(-self.predict_days)
        
        # Drop NaN values
        df_features = df_features.dropna()
        
        return df_features
    
    def find_best_arima_order(self, train_data, test_data):
        """
        Find the best ARIMA order using grid search.
        
        Args:
            train_data (pd.Series): Training data
            test_data (pd.Series): Testing data
            
        Returns:
            tuple: Best ARIMA order, MSE, and fitted model
        """
        p_values = range(0, 4)
        d_values = range(0, 2)
        q_values = range(0, 4)
        
        def evaluate_arima_model(train, test, arima_order):
            try:
                model = ARIMA(train, order=arima_order)
                model_fit = model.fit()
                predictions = model_fit.forecast(steps=len(test))
                mse = mean_squared_error(test, predictions)
                return mse, model_fit
            except:
                return float('inf'), None
        
        results = []
        for p, d, q in product(p_values, d_values, q_values):
            arima_order = (p, d, q)
            mse, model_fit = evaluate_arima_model(train_data, test_data, arima_order)
            results.append((arima_order, mse, model_fit))
        
        return min(results, key=lambda x: x[1])
    
    def train_xgboost_model(self, X_train, y_train):
        """
        Train XGBoost model with predefined parameters.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training targets
            
        Returns:
            XGBRegressor: Trained XGBoost model
        """
        xgb_model = XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method='hist',
            random_state=42
        )
        
        xgb_model.fit(X_train, y_train)
        return xgb_model
    
    def predict_single_crypto(self, symbol):
        """
        Predict price for a single cryptocurrency.
        
        Args:
            symbol (str): Cryptocurrency symbol (e.g., 'BTC-USD')
            
        Returns:
            dict: Dictionary containing prediction results
        """
        print(f"Analyzing {symbol}...")
        
        try:
            # Download crypto data for the last 3 months
            crypto_data = yf.download(symbol, period='3mo', interval='1d')
            crypto_data = crypto_data[['Close']].dropna()
            
            if len(crypto_data) < 30:  # Need sufficient data
                print(f"Insufficient data for {symbol}")
                return None
            
            # Prepare train-test split (80% train, 20% test)
            train_size = int(len(crypto_data) * 0.8)
            train, test = crypto_data[:train_size], crypto_data[train_size:]
            
            # ARIMA Model Training and Evaluation
            best_order, best_mse, best_arima_model = self.find_best_arima_order(
                train['Close'], test['Close']
            )
            
            # XGBoost Model Training and Evaluation
            features_df = self.create_features(crypto_data, 'Close')
            X = features_df.drop(['Close', f'target_{self.predict_days}d'], axis=1)
            y = features_df[f'target_{self.predict_days}d']
            
            # Split features based on original train/test split
            feature_train_size = len(features_df[features_df.index < crypto_data.index[train_size]])
            X_train = X[:feature_train_size]
            X_test = X[feature_train_size:len(X)-self.predict_days]
            y_train = y[:feature_train_size]
            y_test = y[feature_train_size:len(y)-self.predict_days]
            
            xgb_model = self.train_xgboost_model(X_train, y_train)
            
            # Make future predictions using all available data
            # Retrain ARIMA on all data
            full_arima_model = ARIMA(crypto_data['Close'], order=best_order).fit()
            arima_future_forecast = full_arima_model.forecast(steps=15)
            arima_price_prediction = float(arima_future_forecast.values[self.predict_days])
            
            # Retrain XGBoost on all data
            xgb_full_model = self.train_xgboost_model(X, y)
            latest_features = X.iloc[-1].values.reshape(1, -1)
            xgb_price_prediction = xgb_full_model.predict(latest_features)[0]
            
            # Calculate current price and gains
            current_price = float(crypto_data['Close'].iloc[-1])
            combined_price_prediction = (arima_price_prediction + xgb_price_prediction) / 2
            
            # Calculate percentage gains
            arima_gain = ((arima_price_prediction - current_price) / current_price) * 100
            xgb_gain = ((xgb_price_prediction - current_price) / current_price) * 100
            combined_gain = ((combined_price_prediction - current_price) / current_price) * 100
            
            # Extract coin name from symbol (remove -USD suffix)
            coin_name = symbol.replace('-USD', '').upper()
            
            result = {
                'coin_name': coin_name,
                'arima_gain_percent': round(arima_gain, 2),
                'xgboost_gain_percent': round(xgb_gain, 2),
                'combined_gain_percent': round(combined_gain, 2),
                'current_price': round(current_price, 2),
                'arima_prediction': round(arima_price_prediction, 2),
                'xgboost_prediction': round(xgb_price_prediction, 2),
                'combined_prediction': round(combined_price_prediction, 2)
            }
            
            print(f"✓ {symbol} analysis completed")
            return result
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def predict_all_cryptos(self):
        """
        Predict prices for all cryptocurrencies in the symbols list.
        """
        print(f"Starting prediction for {len(self.symbols)} cryptocurrencies...")
        print(f"Prediction horizon: {self.predict_days} days")
        print("-" * 50)
        
        for symbol in self.symbols:
            result = self.predict_single_crypto(symbol)
            if result:
                self.results.append(result)
        
        print("-" * 50)
        print(f"Completed analysis for {len(self.results)} cryptocurrencies")
    
    def save_results_to_csv(self, filename='predict.csv'):
        """
        Save prediction results to CSV file.
        
        Args:
            filename (str): Output CSV filename
        """
        if not self.results:
            print("No results to save. Run predict_all_cryptos() first.")
            return
        
        # Create DataFrame with required columns
        df_results = pd.DataFrame(self.results)
        
        # Select and rename columns as requested
        output_df = df_results[[
            'coin_name', 
            'current_price', 
            'combined_prediction', 
            'combined_gain_percent', 
            'arima_gain_percent', 
            'xgboost_gain_percent'
        ]].copy()
        output_df.columns = [
            'Coin Name', 
            'Current Price', 
            'Estimated Price', 
            'Combined Gain %', 
            'ARIMA Gain %', 
            'XGBoost Gain %'
        ]
        
        # Sort by Combined Gain % in descending order
        output_df = output_df.sort_values('Combined Gain %', ascending=False)
        
        # Save to CSV
        output_df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Display summary
        print("\nPrediction Summary:")
        print(output_df.to_string(index=False))
        
        # Find best investment opportunity
        best_crypto = output_df.iloc[0]
        print(f"\n🚀 Best Investment Opportunity:")
        print(f"   Cryptocurrency: {best_crypto['Coin Name']}")
        print(f"   Current Price: {best_crypto['Current Price']:.2f}")
        print(f"   Estimated Price in {self.predict_days} days: {best_crypto['Estimated Price']:.2f}")
        print(f"   Expected {self.predict_days}-day gain: {best_crypto['Combined Gain %']:.2f}%")

    
    def get_results_dataframe(self):
        """
        Get results as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing all prediction results
        """
        return pd.DataFrame(self.results) if self.results else pd.DataFrame()


def main():
    """Main function to run the crypto price prediction."""
    
    # Initialize predictor
    predictor = CryptoPricePredictor(
        symbols_csv_path='../../data/symbols.csv',
        predict_days=5
    )
    
    # Run predictions
    predictor.predict_all_cryptos()
    
    # Save results
    predictor.save_results_to_csv('predict.csv')
    
    print("\n✅ Prediction process completed!")


if __name__ == "__main__":
    main() 