"""
MongoDB Database Setup for Crypto Chatbot
This script sets up the MongoDB database and collections.
"""

import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, TEXT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "")
DATABASE_NAME = "crypto_chatbot"

class DatabaseSetup:
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB successfully!")
            
            # Get server info
            server_info = await self.client.server_info()
            print(f"   MongoDB version: {server_info['version']}")
            print(f"   Database: {DATABASE_NAME}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def create_collections_and_indexes(self):
        """Create collections and indexes"""
        try:
            # Create users collection with indexes
            users_collection = self.db.users
            
            # Create indexes for users collection
            users_indexes = [
                IndexModel([("username", ASCENDING)], unique=True),
                IndexModel([("email", ASCENDING)], unique=True),
                IndexModel([("created_at", ASCENDING)])
            ]
            await users_collection.create_indexes(users_indexes)
            print("✅ Created 'users' collection with indexes")
            
            # Create conversation_history collection with indexes
            conversations_collection = self.db.conversation_history
            
            # Create indexes for conversation_history collection
            conversation_indexes = [
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("username", ASCENDING)]),
                IndexModel([("timestamp", ASCENDING)]),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("conversation_type", ASCENDING)]),
                IndexModel([("user_question", TEXT), ("bot_answer", TEXT)])  # Text search
            ]
            await conversations_collection.create_indexes(conversation_indexes)
            print("✅ Created 'conversation_history' collection with indexes")
            
            # Create news collection with indexes (for future use)
            news_collection = self.db.news
            news_indexes = [
                IndexModel([("title", TEXT), ("content", TEXT)]),  # Text search
                IndexModel([("timestamp", ASCENDING)]),
                IndexModel([("source", ASCENDING)])
            ]
            await news_collection.create_indexes(news_indexes)
            print("✅ Created 'news' collection with indexes")
            
            # Create predictions collection with indexes (for future use)
            predictions_collection = self.db.predictions
            predictions_indexes = [
                IndexModel([("symbol", ASCENDING)]),
                IndexModel([("timestamp", ASCENDING)]),
                IndexModel([("prediction_type", ASCENDING)])
            ]
            await predictions_collection.create_indexes(predictions_indexes)
            print("✅ Created 'predictions' collection with indexes")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create collections: {e}")
            return False
    
    async def verify_setup(self):
        """Verify the database setup"""
        try:
            # List all collections
            collections = await self.db.list_collection_names()
            print(f"\n📊 Database Setup Summary:")
            print(f"   Database: {DATABASE_NAME}")
            print(f"   Collections: {', '.join(collections)}")
            
            # Check indexes for each collection
            for collection_name in collections:
                collection = self.db[collection_name]
                indexes = await collection.list_indexes().to_list(None)
                index_names = [idx['name'] for idx in indexes]
                print(f"   {collection_name} indexes: {len(index_names)} ({', '.join(index_names)})")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to verify setup: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔒 Database connection closed")

async def main():
    """Main setup function"""
    print("🚀 MongoDB Database Setup for Crypto Chatbot")
    print("=" * 60)
    
    setup = DatabaseSetup()
    
    try:
        # Step 1: Connect to MongoDB
        if not await setup.connect():
            return
        
        # Step 2: Create collections and indexes
        if not await setup.create_collections_and_indexes():
            return
        
        # Step 3: Verify setup
        if not await setup.verify_setup():
            return
        
        print("\n✅ MongoDB database setup completed successfully!")
        print(f"🌐 Connection string: {MONGODB_URL[:50]}...")
        print("🎯 Next steps:")
        print("   1. Run: python sample_data.py")
        print("   2. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
    
    finally:
        await setup.close()

if __name__ == "__main__":
    asyncio.run(main()) 
