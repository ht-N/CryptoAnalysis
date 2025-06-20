"""
Sample Data Script for Crypto Chatbot (MongoDB Version)
This script creates sample users and conversation history for testing.
"""

import os
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1")
DATABASE_NAME = "crypto_chatbot"

class SampleDataCreator:
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
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def create_sample_users(self):
        """Create sample users"""
        users_collection = self.db.users
        
        sample_users = [
            {
                "username": "john_trader",
                "email": "john@cryptotrader.com",
                "full_name": "John Trader",
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "username": "crypto_alice",
                "email": "alice@blockchain.io",
                "full_name": "Alice Crypto",
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "username": "btc_bob",
                "email": "bob@bitcoin.org",
                "full_name": "Bob Bitcoin",
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "username": "demo_user",
                "email": "demo@example.com",
                "full_name": "Demo User",
                "created_at": datetime.utcnow(),
                "is_active": True
            }
        ]
        
        created_users = []
        
        for user_data in sample_users:
            try:
                # Check if user already exists
                existing_user = await users_collection.find_one({"username": user_data["username"]})
                
                if existing_user:
                    print(f"⚠️  User '{user_data['username']}' already exists (ID: {existing_user['_id']})")
                    created_users.append(existing_user)
                else:
                    # Insert new user
                    result = await users_collection.insert_one(user_data)
                    user_data["_id"] = result.inserted_id
                    created_users.append(user_data)
                    print(f"✅ Created user: {user_data['username']} (ID: {result.inserted_id})")
                    
            except Exception as e:
                print(f"❌ Error creating user {user_data['username']}: {e}")
        
        return created_users
    
    async def create_sample_conversations(self, users):
        """Create sample conversation history"""
        conversations_collection = self.db.conversation_history
        
        # Sample conversations in Vietnamese
        sample_conversations = [
            {
                "user": "john_trader",
                "question": "Bitcoin giá bao nhiêu hôm nay?",
                "answer": "Theo dữ liệu mới nhất, giá Bitcoin hiện tại là khoảng $65,400 USD. Giá đã tăng 2.3% trong 24 giờ qua. Đây là một tín hiệu tích cực cho thị trường crypto.",
                "type": "price_query"
            },
            {
                "user": "crypto_alice",
                "question": "Tôi nên đầu tư vào coin nào để lợi nhuận cao?",
                "answer": "Dựa trên phân tích thị trường, một số đồng tiền tiềm năng bao gồm: Ethereum (ETH) với công nghệ smart contracts mạnh mẽ, Solana (SOL) với tốc độ giao dịch nhanh, và Polygon (MATIC) với chi phí thấp. Tuy nhiên, bạn nên nghiên cứu kỹ và chỉ đầu tư số tiền có thể chấp nhận mất.",
                "type": "investment_advice"
            },
            {
                "user": "btc_bob",
                "question": "Tôi có thể mua Bitcoin ở đâu an toàn?",
                "answer": "Bạn có thể mua Bitcoin từ các sàn giao dịch uy tín như: Binance, Coinbase, Kraken, hoặc FTX. Đối với người Việt Nam, có thể sử dụng Binance P2P để mua bằng VND. Nhớ bật xác thực 2 lớp (2FA) và không chia sẻ thông tin tài khoản cho ai.",
                "type": "exchange_recommendation"
            },
            {
                "user": "demo_user",
                "question": "Ethereum sẽ lên hay xuống trong tuần tới?",
                "answer": "Dựa trên phân tích kỹ thuật, Ethereum đang trong xu hướng tăng trung hạn. Tuy nhiên, thị trường crypto rất biến động và khó dự đoán chính xác. Tôi khuyên bạn nên theo dõi các chỉ báo kỹ thuật như RSI, MACD và volume để đưa ra quyết định đầu tư phù hợp.",
                "type": "prediction"
            },
            {
                "user": "john_trader",
                "question": "DCA là gì? Có nên áp dụng cho crypto không?",
                "answer": "DCA (Dollar Cost Averaging) là chiến lược đầu tư định kỳ với số tiền cố định bất kể giá thị trường. Với crypto, DCA rất hiệu quả vì giúp giảm rủi ro biến động giá. Ví dụ: thay vì đầu tư 12 triệu một lần, bạn có thể đầu tư 1 triệu mỗi tháng trong 12 tháng.",
                "type": "strategy_advice"
            },
            {
                "user": "crypto_alice",
                "question": "Làm sao để bảo mật ví crypto?",
                "answer": "Để bảo mật ví crypto: 1) Sử dụng hardware wallet cho số tiền lớn, 2) Bật 2FA trên tất cả tài khoản, 3) Không bao giờ chia sẻ private key, 4) Sử dụng ví cold storage, 5) Backup seed phrase ở nơi an toàn, 6) Cập nhật phần mềm thường xuyên. Nhớ rằng 'Not your keys, not your coins'!",
                "type": "security_advice"
            },
            {
                "user": "btc_bob",
                "question": "Thị trường bull run hay bear market hiện tại?",
                "answer": "Hiện tại thị trường đang trong giai đoạn phục hồi sau chu kỳ bear market. Các chỉ số như Bitcoin Fear & Greed Index, tổng vốn hóa thị trường, và hoạt động của các nhà đầu tư tổ chức đều cho thấy tín hiệu tích cực. Tuy nhiên, cần thận trọng vì thị trường vẫn còn nhiều biến động.",
                "type": "market_analysis"
            }
        ]
        
        # Create user lookup dictionary
        user_lookup = {user["username"]: user for user in users}
        
        created_conversations = []
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i, conv_data in enumerate(sample_conversations):
            try:
                username = conv_data["user"]
                user = user_lookup.get(username)
                
                if not user:
                    print(f"⚠️  User '{username}' not found, skipping conversation")
                    continue
                
                conversation = {
                    "user_id": str(user["_id"]),
                    "username": username,
                    "user_question": conv_data["question"],
                    "bot_answer": conv_data["answer"],
                    "timestamp": base_time + timedelta(hours=i*4),  # Spread conversations over time
                    "session_id": f"session_{username}_{i+1}",
                    "conversation_type": conv_data["type"]
                }
                
                result = await conversations_collection.insert_one(conversation)
                conversation["_id"] = result.inserted_id
                created_conversations.append(conversation)
                print(f"✅ Created conversation for {username}: {conv_data['question'][:50]}...")
                
            except Exception as e:
                print(f"❌ Error creating conversation: {e}")
        
        return created_conversations
    
    async def verify_data(self):
        """Verify the created data"""
        try:
            # Count users
            users_count = await self.db.users.count_documents({})
            
            # Count conversations
            conversations_count = await self.db.conversation_history.count_documents({})
            
            print(f"\n📊 Database Summary:")
            print(f"   👥 Total Users: {users_count}")
            print(f"   💬 Total Conversations: {conversations_count}")
            
            # Show recent conversations
            print(f"\n💬 Recent Conversations:")
            recent_conversations = await self.db.conversation_history.find({}).sort("timestamp", -1).limit(3).to_list(3)
            
            for conv in recent_conversations:
                print(f"   - {conv['username']}: {conv['user_question'][:60]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔒 Database connection closed")

async def main():
    """Main function to create sample data"""
    print("🚀 Creating Sample Data for Crypto Chatbot (MongoDB)")
    print("=" * 60)
    
    creator = SampleDataCreator()
    
    try:
        # Step 1: Connect to MongoDB
        if not await creator.connect():
            return
        
        # Step 2: Create sample users
        print("\n👥 Creating sample users...")
        users = await creator.create_sample_users()
        
        if not users:
            print("❌ No users created. Cannot proceed with conversations.")
            return
        
        # Step 3: Create sample conversations
        print("\n💬 Creating sample conversations...")
        conversations = await creator.create_sample_conversations(users)
        
        # Step 4: Verify data
        await creator.verify_data()
        
        print(f"\n✅ Sample data creation completed!")
        print(f"🌐 MongoDB database: {DATABASE_NAME}")
        print("🎯 You can now start the application: python main.py")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
    
    finally:
        await creator.close()

if __name__ == "__main__":
    asyncio.run(main()) 