"""
Sample Conversations Generator for Crypto Chatbot
Creates realistic conversations between users and assistant with 3 turns each
"""

import os
import asyncio
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1")
DATABASE_NAME = "crypto_chatbot"

# Sample conversation templates with 3 turns each
CONVERSATION_TEMPLATES = [
    {
        "topic": "Bitcoin Price Analysis",
        "turns": [
            {
                "user": "Giá Bitcoin hiện tại như thế nào?",
                "assistant": "Hiện tại Bitcoin đang giao dịch quanh mức $105,000. Theo dữ liệu phân tích của chúng tôi, BTC đã tăng khoảng 2.5% trong 24h qua. Xu hướng tổng thể vẫn đang trong giai đoạn tích lũy với khối lượng giao dịch ổn định."
            },
            {
                "user": "Bạn có thể dự đoán giá Bitcoin trong tuần tới không?",
                "assistant": "Dựa trên mô hình ARIMA và XGBoost của chúng tôi, Bitcoin có thể dao động trong khoảng $103,000 - $108,000 trong tuần tới. Tuy nhiên, thị trường crypto rất biến động, nên bạn cần cẩn trọng và có chiến lược quản lý rủi ro phù hợp."
            },
            {
                "user": "Cảm ơn bạn. Tôi có nên mua Bitcoin bây giờ không?",
                "assistant": "Tôi không thể đưa ra lời khuyên đầu tư cụ thể. Tuy nhiên, bạn nên: 1) Nghiên cứu kỹ trước khi đầu tư, 2) Chỉ đầu tư số tiền có thể chấp nhận mất, 3) Phân bổ danh mục hợp lý, và 4) Có kế hoạch dài hạn. Hãy tham khảo thêm ý kiến từ các chuyên gia tài chính."
            }
        ]
    },
    {
        "topic": "Ethereum vs Bitcoin",
        "turns": [
            {
                "user": "Ethereum và Bitcoin khác nhau như thế nào?",
                "assistant": "Bitcoin được thiết kế như 'vàng số' - chủ yếu để lưu trữ giá trị. Ethereum là nền tảng smart contract cho DeFi, NFT và các ứng dụng phi tập trung. ETH hiện giao dịch khoảng $2,540, trong khi BTC ở mức $105,000."
            },
            {
                "user": "Đầu tư vào ETH có rủi ro hơn BTC không?",
                "assistant": "ETH thường có độ biến động cao hơn BTC. Bitcoin được coi là 'safer bet' do độ trưởng thành và acceptance. Ethereum có tiềm năng tăng trưởng cao hơn nhưng cũng rủi ro hơn do phụ thuộc vào ecosystem DeFi và regulatory của smart contracts."
            },
            {
                "user": "Portfolio của tôi nên có tỷ lệ BTC/ETH như thế nào?",
                "assistant": "Tỷ lệ phổ biến là 60-70% BTC và 30-40% ETH cho portfolio conservative. Aggressive traders có thể 50/50 hoặc tăng ETH. Quan trọng là diversification và phù hợp với risk tolerance của bạn. Luôn DYOR (Do Your Own Research)!"
            }
        ]
    },
    {
        "topic": "Altcoin Investment",
        "turns": [
            {
                "user": "Tôi muốn tìm hiểu về các altcoin. Bạn có thể giới thiệu không?",
                "assistant": "Altcoin là các cryptocurrency khác ngoài Bitcoin. Một số altcoin phổ biến: Solana (SOL) - $147, XRP - $2.17, BNB - $645. Mỗi coin có usecase riêng: SOL cho DeFi tốc độ cao, XRP cho thanh toán xuyên biên giới, BNB cho Binance ecosystem."
            },
            {
                "user": "Altcoin nào đang có triển vọng tốt nhất?",
                "assistant": "Theo phân tích sentiment của chúng tôi: SOL đang có momentum tích cực với ecosystem DeFi phát triển mạnh. XRP có potential từ các partnership ngân hàng. Tuy nhiên, altcoin rủi ro cao hơn BTC/ETH. Hãy research kỹ về technology, team, và roadmap."
            },
            {
                "user": "Làm sao để research một altcoin hiệu quả?",
                "assistant": "Research checklist: 1) Whitepaper và technology, 2) Team background và partnerships, 3) Tokenomics và supply, 4) Community và social sentiment, 5) Use cases thực tế, 6) Competitors analysis, 7) Price history và trading volume. Sử dụng CoinGecko, CoinMarketCap để research."
            }
        ]
    },
    {
        "topic": "DeFi and Yield Farming",
        "turns": [
            {
                "user": "DeFi là gì và có an toàn không?",
                "assistant": "DeFi (Decentralized Finance) là hệ thống tài chính phi tập trung chạy trên blockchain, cho phép lending, borrowing, trading không qua trung gian. Tuy nhiên, DeFi có risks: smart contract bugs, impermanent loss, rug pulls. Năng suất cao đi kèm rủi ro cao."
            },
            {
                "user": "Yield farming hoạt động như thế nào?",
                "assistant": "Yield farming là cung cấp thanh khoản cho các protocol DeFi để nhận rewards. Ví dụ: deposit ETH/USDC vào Uniswap pool, nhận LP tokens, stake để earn fees + token rewards. APY có thể 5-100%+ nhưng có impermanent loss risk khi giá tokens thay đổi."
            },
            {
                "user": "Tôi nên bắt đầu DeFi với số tiền nhỏ được không?",
                "assistant": "Hoàn toàn được! Bắt đầu với số tiền nhỏ để học. Thử các protocol uy tín như Uniswap, Compound, Aave trước. Chú ý gas fees trên Ethereum có thể cao. Consider layer 2 như Polygon hoặc Arbitrum để giảm phí. Practice trên testnet trước khi dùng mainnet."
            }
        ]
    },
    {
        "topic": "Cryptocurrency Security",
        "turns": [
            {
                "user": "Làm sao để bảo mật ví crypto an toàn?",
                "assistant": "Security best practices: 1) Sử dụng hardware wallet (Ledger, Trezor), 2) Backup seed phrase an toàn (viết tay, không chụp ảnh), 3) Enable 2FA, 4) Kiểm tra địa chỉ kỹ trước khi transfer, 5) Không click link lạ, 6) Sử dụng official websites only."
            },
            {
                "user": "Tôi có nên để crypto trên exchange không?",
                "assistant": "Nguyên tắc 'Not your keys, not your coins'. Exchanges tiện lợi cho trading nhưng có risks: hack, bankruptcy, frozen accounts. Chỉ để số tiền cần thiết cho trading trên exchange. Số lớn nên chuyển về personal wallet. Chia nhỏ trên nhiều wallets để giảm rủi ro."
            },
            {
                "user": "Nếu tôi mất seed phrase thì sao?",
                "assistant": "Mất seed phrase = mất vĩnh viễn crypto trong wallet đó. Không có cách nào recover. Vì vậy: 1) Backup multiple copies ở nơi an toàn, 2) Không lưu digital (cloud, email, photo), 3) Viết tay trên kim loại hoặc giấy chất lượng cao, 4) Test recovery process trước khi deposit lớn."
            }
        ]
    },
    {
        "topic": "Market Analysis and News",
        "turns": [
            {
                "user": "Tin tức nào đang ảnh hưởng đến thị trường crypto?",
                "assistant": "Hiện tại thị trường đang chú ý: 1) Quyết định lãi suất của Fed, 2) ETF Bitcoin approval updates, 3) Regulatory news từ các quốc gia, 4) Institutional adoption, 5) Technical upgrades của major blockchains. BlackRock và các tổ chức lớn đang tích cực mua Bitcoin."
            },
            {
                "user": "Làm sao để theo dõi tin tức crypto hiệu quả?",
                "assistant": "Nguồn tin đáng tin: 1) CoinDesk, CoinTelegraph cho news, 2) Twitter/X của các KOLs, 3) Official announcements từ projects, 4) On-chain data từ Glassnode, 5) Reddit communities, 6) Binance Academy cho education. Set up alerts cho các keywords quan trọng."
            },
            {
                "user": "Sentiment analysis có đáng tin không?",
                "assistant": "Sentiment analysis là tool hữu ích nhưng không nên dùng standalone. Combine với: 1) Technical analysis, 2) Fundamental analysis, 3) On-chain metrics, 4) Macro economic factors. Sentiment có thể manipulated, especially trong short term. Long-term fundamentals quan trọng hơn."
            }
        ]
    }
]

class ConversationGenerator:
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
    
    async def get_sample_users(self):
        """Get sample users from database"""
        try:
            users = await self.db.sample_users.find({"is_active": True}).to_list(length=None)
            if not users:
                print("⚠️  No sample users found. Please run create_sample_users.py first")
                return []
            return users
        except Exception as e:
            print(f"❌ Error getting users: {e}")
            return []
    
    def generate_conversations(self, users):
        """Generate conversations using templates"""
        conversations = []
        
        if not users:
            print("⚠️  No users available to generate conversations")
            return conversations
        
        # Create multiple conversations from templates
        for i, template in enumerate(CONVERSATION_TEMPLATES):
            # Each template creates 2-3 conversations with different users
            num_conversations = random.randint(2, 3)
            
            for conv_idx in range(num_conversations):
                # Select random user
                user = random.choice(users)
                
                # Create base timestamp (spread over last 30 days)
                base_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                # Create conversation with 3 turns
                for turn_idx, turn in enumerate(template["turns"]):
                    # Each turn is a few minutes apart
                    turn_time = base_time + timedelta(minutes=turn_idx * random.randint(2, 8))
                    
                    conversation = {
                        "user_id": str(user["_id"]),
                        "username": user["name"].replace(" ", "_").lower(),
                        "user_question": turn["user"],
                        "bot_answer": turn["assistant"],
                        "timestamp": turn_time,
                        "session_id": f"conv_{i}_{conv_idx}_{user['name'].replace(' ', '_').lower()}",
                        "conversation_type": template["topic"].lower().replace(" ", "_"),
                        "turn_number": turn_idx + 1,
                        "total_turns": len(template["turns"]),
                        "topic": template["topic"],
                        "language": "vi",
                        "response_time_ms": random.randint(800, 3000),  # Simulated response time
                        "user_satisfaction": random.choice(["positive", "neutral", "positive", "positive"]),  # Mostly positive
                        "source": "sample_conversation_generator"
                    }
                    conversations.append(conversation)
        
        return conversations
    
    async def insert_conversations(self, conversations):
        """Insert conversations into MongoDB"""
        try:
            if not conversations:
                print("⚠️  No conversations to insert")
                return False
            
            # Create indexes for conversation_history collection
            indexes = [
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("timestamp", ASCENDING)]),
                IndexModel([("conversation_type", ASCENDING)]),
                IndexModel([("topic", ASCENDING)]),
                IndexModel([("turn_number", ASCENDING)])
            ]
            
            await self.db.conversation_history.create_indexes(indexes)
            print("✅ Created indexes for conversation_history collection")
            
            # Insert conversations
            result = await self.db.conversation_history.insert_many(conversations)
            print(f"✅ Inserted {len(result.inserted_ids)} conversation turns successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inserting conversations: {e}")
            return False
    
    async def display_conversation_stats(self):
        """Display statistics about created conversations"""
        try:
            print("\n📊 Conversation Statistics:")
            print("=" * 60)
            
            # Basic stats
            total_conversations = await self.db.conversation_history.count_documents({"source": "sample_conversation_generator"})
            
            # Stats by topic
            topic_pipeline = [
                {"$match": {"source": "sample_conversation_generator"}},
                {"$group": {
                    "_id": "$topic",
                    "count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"}
                }},
                {"$project": {
                    "topic": "$_id",
                    "conversations": "$count",
                    "unique_users": {"$size": "$unique_users"}
                }},
                {"$sort": {"conversations": -1}}
            ]
            
            topic_stats = await self.db.conversation_history.aggregate(topic_pipeline).to_list(length=None)
            
            print(f"🗨️  Total conversation turns: {total_conversations}")
            print(f"🎯 Topics covered: {len(topic_stats)}")
            
            print("\n📈 Breakdown by Topic:")
            for stat in topic_stats:
                print(f"   💬 {stat['topic']}: {stat['conversations']} turns, {stat['unique_users']} users")
            
            # Recent conversations sample
            print(f"\n🕒 Recent Conversations Sample:")
            recent_convs = await self.db.conversation_history.find(
                {"source": "sample_conversation_generator"}
            ).sort("timestamp", -1).limit(3).to_list(length=3)
            
            for conv in recent_convs:
                print(f"   👤 {conv['username']}: {conv['user_question'][:50]}...")
                print(f"   🤖 Assistant: {conv['bot_answer'][:80]}...")
                print(f"   🕐 {conv['timestamp'].strftime('%d/%m/%Y %H:%M')}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error displaying stats: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("\n🔒 Database connection closed")

async def main():
    """Main function to generate and insert sample conversations"""
    print("🚀 Generating Sample Conversations for Crypto Chatbot")
    print("=" * 70)
    
    generator = ConversationGenerator()
    
    try:
        # Connect to MongoDB
        if not await generator.connect():
            return
        
        # Get sample users
        print("\n👥 Getting sample users from database...")
        users = await generator.get_sample_users()
        
        if not users:
            print("❌ No users found! Please run 'python create_sample_users.py' first")
            return
        
        print(f"✅ Found {len(users)} sample users")
        
        # Generate conversations
        print(f"\n💬 Generating conversations from {len(CONVERSATION_TEMPLATES)} templates...")
        conversations = generator.generate_conversations(users)
        
        print(f"✅ Generated {len(conversations)} conversation turns")
        
        # Insert conversations into MongoDB
        print(f"\n📤 Inserting conversations into MongoDB...")
        if await generator.insert_conversations(conversations):
            # Display statistics
            await generator.display_conversation_stats()
            
            print("\n✅ Sample conversations created successfully!")
            print("🎯 Next steps:")
            print("   1. Start the API: python main.py")
            print("   2. Visit: http://localhost:8000/docs")
            print("   3. Test /conversation-history endpoint")
            print("   4. Try filtering by username, topic, or session_id")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
    
    finally:
        await generator.close()

if __name__ == "__main__":
    asyncio.run(main()) 