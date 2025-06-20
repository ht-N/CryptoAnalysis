"""
Sample data script to populate the crypto chatbot database with initial data.
Run this after setting up the database to have some test data to work with.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the current directory to the Python path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import User, ConversationHistory, Base

def create_sample_data():
    """Create sample users and conversations."""
    
    load_dotenv()
    
    # Database connection
    database_url = os.getenv("DATABASE_URL", "postgresql://crypto_user:crypto_password@localhost:5432/crypto_chatbot")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("🗄️  Creating sample data for crypto chatbot...")
        
        # Sample users
        sample_users = [
            {
                "username": "john_trader",
                "email": "john@example.com",
                "full_name": "John Smith",
                "created_at": datetime.utcnow() - timedelta(days=30)
            },
            {
                "username": "crypto_alice",
                "email": "alice@example.com", 
                "full_name": "Alice Johnson",
                "created_at": datetime.utcnow() - timedelta(days=15)
            },
            {
                "username": "btc_bob",
                "email": "bob@example.com",
                "full_name": "Bob Wilson",
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "username": "demo_user",
                "email": "demo@example.com",
                "full_name": "Demo User",
                "created_at": datetime.utcnow() - timedelta(days=1)
            }
        ]
        
        created_users = []
        for user_data in sample_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing_user:
                user = User(**user_data)
                db.add(user)
                db.commit()
                db.refresh(user)
                created_users.append(user)
                print(f"✅ Created user: {user.username} (ID: {user.id})")
            else:
                created_users.append(existing_user)
                print(f"ℹ️  User already exists: {existing_user.username}")
        
        # Sample conversations
        sample_conversations = [
            {
                "user": created_users[0],  # john_trader
                "conversations": [
                    {
                        "user_question": "Giá Bitcoin hiện tại là bao nhiêu?",
                        "bot_answer": "Giá hiện tại của đồng Bitcoin là khoảng $45,000. Dự đoán trong 5 ngày tới có thể tăng lên $47,500 với mức tăng trưởng dự kiến 5.5%.",
                        "conversation_type": "price_query",
                        "timestamp": datetime.utcnow() - timedelta(hours=2)
                    },
                    {
                        "user_question": "Ethereum có nên đầu tư không?",
                        "bot_answer": "Dựa trên phân tích của chúng tôi, Ethereum có điểm số 8.2/10. Giá hiện tại $2,800 với dự đoán tăng lên $3,100 trong 5 ngày tới. Đây là một lựa chọn tốt để đầu tư.",
                        "conversation_type": "recommendation_query",
                        "timestamp": datetime.utcnow() - timedelta(hours=1)
                    }
                ]
            },
            {
                "user": created_users[1],  # crypto_alice
                "conversations": [
                    {
                        "user_question": "Những đồng coin nào đang có xu hướng tích cực?",
                        "bot_answer": "Hiện tại, BTC (Bitcoin), ETH (Ethereum), và SOL (Solana) đang có xu hướng tích cực với điểm sentiment analysis cao. BTC có điểm 8.5/10, ETH có 8.2/10.",
                        "conversation_type": "recommendation_query",
                        "timestamp": datetime.utcnow() - timedelta(days=1)
                    },
                    {
                        "user_question": "Solana giá bao nhiêu?",
                        "bot_answer": "Giá hiện tại của Solana (SOL) là $85. Dự đoán trong 5 ngày tới có thể đạt $92 với mức tăng trưởng 8.2%.",
                        "conversation_type": "price_query",
                        "timestamp": datetime.utcnow() - timedelta(hours=12)
                    }
                ]
            },
            {
                "user": created_users[2],  # btc_bob
                "conversations": [
                    {
                        "user_question": "Tôi nên mua Bitcoin hay Ethereum?",
                        "bot_answer": "Dựa trên phân tích hiện tại: Bitcoin có độ ổn định cao hơn với điểm 8.5/10, trong khi Ethereum có tiềm năng tăng trưởng mạnh hơn với điểm 8.2/10. Nếu bạn ưa thích an toàn, chọn Bitcoin. Nếu muốn tiềm năng cao hơn, chọn Ethereum.",
                        "conversation_type": "recommendation_query",
                        "timestamp": datetime.utcnow() - timedelta(days=2)
                    }
                ]
            },
            {
                "user": None,  # Anonymous user
                "username": None,
                "conversations": [
                    {
                        "user_question": "Crypto market hôm nay thế nào?",
                        "bot_answer": "Thị trường crypto hôm nay tương đối tích cực. Bitcoin tăng 2.3%, Ethereum tăng 3.1%. Nhìn chung, sentiment trong cộng đồng đang khá lạc quan.",
                        "conversation_type": "general",
                        "timestamp": datetime.utcnow() - timedelta(hours=6)
                    },
                    {
                        "user_question": "Làm sao để bắt đầu đầu tư crypto?",
                        "bot_answer": "Để bắt đầu đầu tư crypto: 1) Học hiểu cơ bản về blockchain, 2) Chọn sàn giao dịch uy tín, 3) Bắt đầu với số tiền nhỏ, 4) Đa dạng hóa danh mục, 5) Không đầu tư quá số tiền bạn có thể mất.",
                        "conversation_type": "general",
                        "timestamp": datetime.utcnow() - timedelta(hours=8)
                    }
                ]
            }
        ]
        
        # Create conversations
        conversation_count = 0
        for conv_data in sample_conversations:
            user = conv_data.get("user")
            username = user.username if user else conv_data.get("username")
            user_id = user.id if user else None
            
            for conv in conv_data["conversations"]:
                conversation = ConversationHistory(
                    user_id=user_id,
                    username=username,
                    user_question=conv["user_question"],
                    bot_answer=conv["bot_answer"],
                    conversation_type=conv["conversation_type"],
                    timestamp=conv["timestamp"],
                    session_id=f"session_{user_id or 'anon'}_{conv['timestamp'].strftime('%Y%m%d')}"
                )
                db.add(conversation)
                conversation_count += 1
        
        db.commit()
        print(f"✅ Created {conversation_count} sample conversations")
        
        # Display summary
        total_users = db.query(User).count()
        total_conversations = db.query(ConversationHistory).count()
        
        print(f"\n📊 Database Summary:")
        print(f"   👥 Total Users: {total_users}")
        print(f"   💬 Total Conversations: {total_conversations}")
        
        print(f"\n🎉 Sample data created successfully!")
        print(f"\n🔗 You can now test the API endpoints:")
        print(f"   GET  /users - View all users")
        print(f"   GET  /user/john_trader - View specific user profile")
        print(f"   GET  /conversation-history - View all conversations")
        print(f"   GET  /database/tables - View database tables info")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Crypto Chatbot Sample Data Generator\n")
    
    if create_sample_data():
        print("\n✅ Sample data creation completed!")
    else:
        print("\n❌ Sample data creation failed!")
        print("Make sure PostgreSQL is running and the database is set up correctly.")
        print("Run: python database_setup.py first if needed.") 