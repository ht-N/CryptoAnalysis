"""
Data Migration Script for Crypto Chatbot (MongoDB)
This script pushes all data from the /data folder to MongoDB Cloud
"""

import os
import asyncio
import pandas as pd
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, TEXT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "")
DATABASE_NAME = "crypto_chatbot"

class DataMigrator:
    def __init__(self):
        self.client = None
        self.db = None
        self.data_folder = "data"
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def drop_existing_collections(self):
        """Drop existing data collections to avoid duplicates"""
        collections_to_drop = ['symbols', 'predictions', 'market_analysis', 'news_links', 'binance_news', 'processed_analysis', 'processed_predictions', 'processed_scoring']
        
        for collection_name in collections_to_drop:
            try:
                await self.db[collection_name].drop()
                print(f"🗑️  Dropped existing collection: {collection_name}")
            except Exception as e:
                print(f"⚠️  Collection {collection_name} doesn't exist or couldn't be dropped: {e}")
    
    async def create_indexes(self):
        """Create indexes for all data collections"""
        try:
            # Symbols collection indexes
            symbols_indexes = [
                IndexModel([("symbol", ASCENDING)], unique=True),
                IndexModel([("created_at", ASCENDING)])
            ]
            await self.db.symbols.create_indexes(symbols_indexes)
            print("✅ Created indexes for 'symbols' collection")
            
            # Predictions collection indexes
            predictions_indexes = [
                IndexModel([("coin_name", ASCENDING)]),
                IndexModel([("current_price", ASCENDING)]),
                IndexModel([("estimated_price", ASCENDING)]),
                IndexModel([("combined_gain_percent", ASCENDING)]),
                IndexModel([("created_at", ASCENDING)])
            ]
            await self.db.predictions.create_indexes(predictions_indexes)
            print("✅ Created indexes for 'predictions' collection")
            
            # Market analysis collection indexes
            analysis_indexes = [
                IndexModel([("coin_name", ASCENDING)]),
                IndexModel([("label", ASCENDING)]),
                IndexModel([("created_at", ASCENDING)]),
                IndexModel([("coin_name", ASCENDING), ("label", ASCENDING)])  # Compound index
            ]
            await self.db.market_analysis.create_indexes(analysis_indexes)
            print("✅ Created indexes for 'market_analysis' collection")
            
            # News links collection indexes
            news_indexes = [
                IndexModel([("link", ASCENDING)], unique=True),
                IndexModel([("coin_name", ASCENDING)]),
                IndexModel([("created_at", ASCENDING)])
            ]
            await self.db.news_links.create_indexes(news_indexes)
            print("✅ Created indexes for 'news_links' collection")
            
            # Binance news collection indexes
            binance_news_indexes = [
                IndexModel([("coin_name", ASCENDING)]),
                IndexModel([("content", TEXT)]),  # Text search
                IndexModel([("created_at", ASCENDING)]),
                IndexModel([("coin_name", ASCENDING), ("created_at", ASCENDING)])  # Compound index
            ]
            await self.db.binance_news.create_indexes(binance_news_indexes)
            print("✅ Created indexes for 'binance_news' collection")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
            return False
    
    async def push_symbols_data(self):
        """Push symbols.csv data to MongoDB"""
        try:
            file_path = os.path.join(self.data_folder, "symbols.csv")
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                return False
                
            df = pd.read_csv(file_path)
            print(f"📊 Processing {len(df)} symbols...")
            
            documents = []
            for _, row in df.iterrows():
                doc = {
                    "symbol": row["symbol"],
                    "created_at": datetime.utcnow(),
                    "source": "symbols.csv",
                    "is_active": True
                }
                documents.append(doc)
            
            result = await self.db.symbols.insert_many(documents)
            print(f"✅ Inserted {len(result.inserted_ids)} symbols")
            return True
            
        except Exception as e:
            print(f"❌ Error pushing symbols data: {e}")
            return False
    
    async def push_predictions_data(self):
        """Push predict.csv data to MongoDB"""
        try:
            file_path = os.path.join(self.data_folder, "predict.csv")
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                return False
                
            df = pd.read_csv(file_path)
            print(f"📊 Processing {len(df)} predictions...")
            
            documents = []
            for _, row in df.iterrows():
                doc = {
                    "coin_name": row["Coin Name"],
                    "current_price": float(row["Current Price"]),
                    "estimated_price": float(row["Estimated Price"]),
                    "combined_gain_percent": float(row["Combined Gain %"]),
                    "arima_gain_percent": float(row["ARIMA Gain %"]),
                    "xgboost_gain_percent": float(row["XGBoost Gain %"]),
                    "created_at": datetime.utcnow(),
                    "source": "predict.csv",
                    "prediction_type": "combined_model"
                }
                documents.append(doc)
            
            result = await self.db.predictions.insert_many(documents)
            print(f"✅ Inserted {len(result.inserted_ids)} predictions")
            return True
            
        except Exception as e:
            print(f"❌ Error pushing predictions data: {e}")
            return False
    
    async def push_analysis_data(self):
        """Push analysis.csv data to MongoDB"""
        try:
            file_path = os.path.join(self.data_folder, "analysis.csv")
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                return False
                
            df = pd.read_csv(file_path)
            print(f"📊 Processing {len(df)} analysis records...")
            
            documents = []
            for _, row in df.iterrows():
                # Skip the header row if it exists
                if row["coin_name"] == "coin_name" or row["label"] == "error":
                    continue
                    
                doc = {
                    "coin_name": row["coin_name"],
                    "label": row["label"],
                    "created_at": datetime.utcnow(),
                    "source": "analysis.csv",
                    "analysis_type": "sentiment"
                }
                documents.append(doc)
            
            if documents:
                result = await self.db.market_analysis.insert_many(documents)
                print(f"✅ Inserted {len(result.inserted_ids)} analysis records")
            else:
                print("⚠️  No valid analysis records to insert")
            return True
            
        except Exception as e:
            print(f"❌ Error pushing analysis data: {e}")
            return False
    
    async def push_news_links_data(self):
        """Push news.csv data to MongoDB"""
        try:
            file_path = os.path.join(self.data_folder, "news.csv")
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                return False
                
            df = pd.read_csv(file_path)
            print(f"📊 Processing {len(df)} news links...")
            
            documents = []
            for _, row in df.iterrows():
                link = row["link"]
                
                # Extract coin name from the link
                coin_name = "UNKNOWN"
                if "BITCOIN" in link.upper():
                    coin_name = "BITCOIN"
                elif "ETHEREUM" in link.upper():
                    coin_name = "ETHEREUM"
                elif "XRP" in link.upper():
                    coin_name = "XRP"
                elif "BNB" in link.upper():
                    coin_name = "BNB"
                elif "SOL" in link.upper():
                    coin_name = "SOL"
                elif "DOGECOIN" in link.upper():
                    coin_name = "DOGECOIN"
                elif "ADA" in link.upper():
                    coin_name = "ADA"
                elif "TRX" in link.upper():
                    coin_name = "TRX"
                elif "AVAX" in link.upper():
                    coin_name = "AVAXUSDT"
                elif "SUI" in link.upper():
                    coin_name = "SUI"
                elif "TON" in link.upper():
                    coin_name = "TONCOIN"
                
                doc = {
                    "link": link,
                    "coin_name": coin_name,
                    "created_at": datetime.utcnow(),
                    "source": "news.csv",
                    "platform": "binance",
                    "is_active": True
                }
                documents.append(doc)
            
            result = await self.db.news_links.insert_many(documents)
            print(f"✅ Inserted {len(result.inserted_ids)} news links")
            return True
            
        except Exception as e:
            print(f"❌ Error pushing news links data: {e}")
            return False
    
    async def push_binance_news_data(self):
        """Push binance_news.csv data to MongoDB"""
        try:
            file_path = os.path.join(self.data_folder, "binance_news.csv")
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                return False
                
            df = pd.read_csv(file_path)
            print(f"📊 Processing {len(df)} Binance news articles...")
            
            documents = []
            for _, row in df.iterrows():
                doc = {
                    "coin_name": row["coin_name"],
                    "content": row["content"],
                    "created_at": datetime.utcnow(),
                    "source": "binance_news.csv",
                    "platform": "binance",
                    "content_length": len(row["content"]),
                    "language": "mixed"  # As the content appears to be in multiple languages
                }
                documents.append(doc)
            
            result = await self.db.binance_news.insert_many(documents)
            print(f"✅ Inserted {len(result.inserted_ids)} Binance news articles")
            return True
            
        except Exception as e:
            print(f"❌ Error pushing Binance news data: {e}")
            return False
    
    async def push_processed_data(self):
        """Push data from the processed folder"""
        try:
            processed_folder = os.path.join(self.data_folder, "processed")
            
            # Process analysis.csv from processed folder
            analysis_path = os.path.join(processed_folder, "analysis.csv")
            if os.path.exists(analysis_path):
                df = pd.read_csv(analysis_path)
                print(f"📊 Processing {len(df)} processed analysis records...")
                
                documents = []
                for _, row in df.iterrows():
                    if row["coin_name"] != "coin_name" and row["label"] != "error":
                        doc = {
                            "coin_name": row["coin_name"],
                            "label": row["label"],
                            "created_at": datetime.utcnow(),
                            "source": "processed/analysis.csv",
                            "analysis_type": "processed_sentiment",
                            "processing_stage": "final"
                        }
                        documents.append(doc)
                
                if documents:
                    result = await self.db.processed_analysis.insert_many(documents)
                    print(f"✅ Inserted {len(result.inserted_ids)} processed analysis records")
            
            # Process predict.csv from processed folder
            predict_path = os.path.join(processed_folder, "predict.csv")
            if os.path.exists(predict_path):
                df = pd.read_csv(predict_path)
                print(f"📊 Processing {len(df)} processed predictions...")
                
                documents = []
                for _, row in df.iterrows():
                    doc = {
                        "coin_name": row.get("Coin Name", row.get("coin_name", "UNKNOWN")),
                        "created_at": datetime.utcnow(),
                        "source": "processed/predict.csv",
                        "processing_stage": "final"
                    }
                    
                    # Add all columns dynamically
                    for col in df.columns:
                        if col not in ["Coin Name", "coin_name"]:
                            try:
                                # Try to convert to float if it's a numeric field
                                doc[col.lower().replace(" ", "_")] = float(row[col])
                            except (ValueError, TypeError):
                                doc[col.lower().replace(" ", "_")] = row[col]
                    
                    documents.append(doc)
                
                if documents:
                    result = await self.db.processed_predictions.insert_many(documents)
                    print(f"✅ Inserted {len(result.inserted_ids)} processed predictions")
            
            # Process scoring.csv from processed folder
            scoring_path = os.path.join(processed_folder, "scoring.csv")
            if os.path.exists(scoring_path):
                df = pd.read_csv(scoring_path)
                print(f"📊 Processing {len(df)} scoring records...")
                
                documents = []
                for _, row in df.iterrows():
                    doc = {
                        "created_at": datetime.utcnow(),
                        "source": "processed/scoring.csv",
                        "processing_stage": "final"
                    }
                    
                    # Add all columns dynamically
                    for col in df.columns:
                        try:
                            # Try to convert to float if it's a numeric field
                            doc[col.lower().replace(" ", "_")] = float(row[col])
                        except (ValueError, TypeError):
                            doc[col.lower().replace(" ", "_")] = row[col]
                    
                    documents.append(doc)
                
                if documents:
                    result = await self.db.processed_scoring.insert_many(documents)
                    print(f"✅ Inserted {len(result.inserted_ids)} scoring records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error pushing processed data: {e}")
            return False
    
    async def generate_summary_stats(self):
        """Generate summary statistics for all collections"""
        try:
            print("\n📊 Database Summary After Migration:")
            print("=" * 50)
            
            collections = [
                "symbols", "predictions", "market_analysis", 
                "news_links", "binance_news", "processed_analysis", 
                "processed_predictions", "processed_scoring"
            ]
            
            total_documents = 0
            
            for collection_name in collections:
                try:
                    count = await self.db[collection_name].count_documents({})
                    total_documents += count
                    print(f"📁 {collection_name:20}: {count:6} documents")
                except Exception as e:
                    print(f"⚠️  {collection_name:20}: Error counting documents")
            
            print("=" * 50)
            print(f"🎯 Total Documents: {total_documents}")
            
            # Sample some data from each collection
            print("\n🔍 Sample Data:")
            print("-" * 30)
            
            # Sample from predictions
            sample_prediction = await self.db.predictions.find_one({})
            if sample_prediction:
                print(f"💰 Sample Prediction: {sample_prediction['coin_name']} - Current: ${sample_prediction['current_price']:.2f}, Estimated: ${sample_prediction['estimated_price']:.2f}")
            
            # Sample from analysis
            sample_analysis = await self.db.market_analysis.find_one({})
            if sample_analysis:
                print(f"📈 Sample Analysis: {sample_analysis['coin_name']} - Sentiment: {sample_analysis['label']}")
            
            # Sample from news
            sample_news = await self.db.binance_news.find_one({})
            if sample_news:
                print(f"📰 Sample News: {sample_news['coin_name']} - Content length: {sample_news['content_length']} chars")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("\n🔒 Database connection closed")

async def main():
    """Main migration function"""
    print("🚀 Starting Data Migration to MongoDB")
    print("=" * 60)
    
    migrator = DataMigrator()
    
    try:
        # Step 1: Connect to MongoDB
        if not await migrator.connect():
            return
        
        # Step 2: Drop existing collections (optional - uncomment if you want clean migration)
        print("\n🗑️  Cleaning existing data collections...")
        await migrator.drop_existing_collections()
        
        # Step 3: Create indexes
        print("\n🔧 Creating database indexes...")
        if not await migrator.create_indexes():
            print("⚠️  Index creation failed, but continuing...")
        
        # Step 4: Migrate all data files
        print("\n📂 Migrating data files...")
        
        await migrator.push_symbols_data()
        await migrator.push_predictions_data()
        await migrator.push_analysis_data()
        await migrator.push_news_links_data()
        await migrator.push_binance_news_data()
        await migrator.push_processed_data()
        
        # Step 5: Generate summary
        await migrator.generate_summary_stats()
        
        print("\n✅ Data migration completed successfully!")
        print(f"🌐 MongoDB database: {DATABASE_NAME}")
        print(f"🔗 Connection: MongoDB Cloud (Atlas)")
        print("\n🎯 Next steps:")
        print("   1. Verify data in MongoDB Compass or your preferred tool")
        print("   2. Test the API endpoints to ensure data is accessible")
        print("   3. Run the chatbot to verify integration")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    
    finally:
        await migrator.close()

if __name__ == "__main__":
    # Check if data folder exists
    if not os.path.exists("data"):
        print("❌ Error: 'data' folder not found!")
        print("Make sure you're running this script from the backend directory")
        exit(1)
    
    asyncio.run(main()) 
