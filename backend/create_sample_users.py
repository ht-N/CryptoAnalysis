"""
Sample Users Generator and MongoDB Insertion Script
Creates 10 sample users with Vietnamese data and pushes to MongoDB
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

# Vietnamese sample data
VIETNAMESE_NAMES = [
    "Nguyễn Văn Anh", "Trần Thị Bình", "Lê Hoàng Cường", "Phạm Thị Dung",
    "Hoàng Minh Đức", "Vũ Thị Em", "Đặng Văn Phong", "Bùi Thị Giang",
    "Dương Văn Hải", "Ngô Thị Hương", "Lý Văn Inh", "Tạ Thị Kim",
    "Phan Văn Long", "Đỗ Thị Mai", "Chu Văn Nam"
]

VIETNAMESE_ADDRESSES = [
    "123 Nguyễn Huệ, Quận 1, TP.HCM",
    "456 Lê Lợi, Quận 3, TP.HCM", 
    "789 Trần Hưng Đạo, Quận 5, TP.HCM",
    "321 Điện Biên Phủ, Quận Bình Thạnh, TP.HCM",
    "654 Võ Văn Tần, Quận 3, TP.HCM",
    "987 Cách Mạng Tháng 8, Quận 10, TP.HCM",
    "147 Pasteur, Quận 1, TP.HCM",
    "258 Hai Bà Trưng, Quận 1, TP.HCM",
    "369 Nguyễn Thị Minh Khai, Quận 3, TP.HCM",
    "741 Lý Tự Trọng, Quận 1, TP.HCM",
    "852 Đồng Khởi, Quận 1, TP.HCM",
    "963 Nam Kỳ Khởi Nghĩa, Quận 3, TP.HCM",
    "159 Lê Duẩn, Quận 1, TP.HCM",
    "357 Nguyễn Du, Quận 1, TP.HCM",
    "486 Võ Thị Sáu, Quận 3, TP.HCM"
]

VIETNAMESE_DESCRIPTIONS = [
    "Nhà đầu tư crypto nhiều kinh nghiệm, chuyên về Bitcoin và Ethereum",
    "Trader chuyên nghiệp, tập trung vào altcoins và DeFi",
    "Sinh viên công nghệ thông tin, đam mê blockchain",
    "Doanh nhân trẻ, đầu tư dài hạn vào cryptocurrency",
    "Kỹ sư phần mềm, quan tâm đến công nghệ Web3",
    "Giáo viên đại học, nghiên cứu về fintech và blockchain",
    "Freelancer IT, kiếm thu nhập từ crypto trading",
    "Chuyên viên tài chính ngân hàng, học hỏi về DeFi",
    "Startup founder, sử dụng crypto cho thanh toán quốc tế",
    "Designer UI/UX, đầu tư tiết kiệm vào các đồng coin ổn định",
    "Marketing manager, quan tâm đến NFT và metaverse",
    "Kế toán viên, tìm hiểu về stablecoin và yield farming",
    "Bác sĩ, đầu tư crypto như một kênh tài chính bổ sung",
    "Luật sư, nghiên cứu về quy định pháp lý của cryptocurrency",
    "Nhà báo công nghệ, theo dõi xu hướng crypto và blockchain"
]

class UserGenerator:
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
    
    def generate_sample_users(self, count=10):
        """Generate sample users with Vietnamese data"""
        users = []
        used_names = set()
        
        for i in range(count):
            # Ensure unique names
            while True:
                name = random.choice(VIETNAMESE_NAMES)
                if name not in used_names:
                    used_names.add(name)
                    break
            
            # Generate user data
            user = {
                "name": name,
                "age": random.randint(18, 65),
                "currency": random.randint(100000, 50000000),  # VND from 100k to 50M
                "description": random.choice(VIETNAMESE_DESCRIPTIONS),
                "address": random.choice(VIETNAMESE_ADDRESSES),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "join_date": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                "preferred_language": "vi",
                "country": "Vietnam"
            }
            users.append(user)
        
        return users
    
    async def create_indexes(self):
        """Create indexes for users collection"""
        try:
            indexes = [
                IndexModel([("name", ASCENDING)], unique=True),
                IndexModel([("age", ASCENDING)]),
                IndexModel([("currency", ASCENDING)]),
                IndexModel([("created_at", ASCENDING)]),
                IndexModel([("is_active", ASCENDING)]),
                IndexModel([("country", ASCENDING)])
            ]
            
            await self.db.sample_users.create_indexes(indexes)
            print("✅ Created indexes for 'sample_users' collection")
            return True
            
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
            return False
    
    async def insert_users(self, users):
        """Insert users into MongoDB"""
        try:
            # Drop existing collection first
            await self.db.sample_users.drop()
            print("🗑️  Dropped existing 'sample_users' collection")
            
            # Create indexes
            await self.create_indexes()
            
            # Insert users
            result = await self.db.sample_users.insert_many(users)
            print(f"✅ Inserted {len(result.inserted_ids)} users successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inserting users: {e}")
            return False
    
    async def display_users(self):
        """Display all inserted users"""
        try:
            print("\n📋 Sample Users Created:")
            print("=" * 80)
            
            users = await self.db.sample_users.find({}).to_list(length=None)
            
            for i, user in enumerate(users, 1):
                print(f"\n👤 User {i}:")
                print(f"   📛 Tên: {user['name']}")
                print(f"   🎂 Tuổi: {user['age']}")
                print(f"   💰 Tiền: {user['currency']:,} VND")
                print(f"   📝 Mô tả: {user['description']}")
                print(f"   🏠 Địa chỉ: {user['address']}")
                print(f"   📅 Ngày tham gia: {user['join_date'].strftime('%d/%m/%Y')}")
            
            # Statistics
            total_currency = sum(user['currency'] for user in users)
            avg_age = sum(user['age'] for user in users) / len(users)
            
            print("\n📊 Thống kê:")
            print(f"   👥 Tổng số users: {len(users)}")
            print(f"   💵 Tổng tiền: {total_currency:,} VND")
            print(f"   📈 Tiền trung bình: {total_currency//len(users):,} VND")
            print(f"   🎯 Tuổi trung bình: {avg_age:.1f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error displaying users: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("\n🔒 Database connection closed")

async def main():
    """Main function to generate and insert sample users"""
    print("🚀 Generating Sample Users for MongoDB")
    print("=" * 50)
    
    generator = UserGenerator()
    
    try:
        # Connect to MongoDB
        if not await generator.connect():
            return
        
        # Generate sample users
        print("\n👥 Generating 10 sample Vietnamese users...")
        users = generator.generate_sample_users(10)
        
        # Insert users into MongoDB
        print("\n📤 Inserting users into MongoDB...")
        if await generator.insert_users(users):
            # Display created users
            await generator.display_users()
            
            print("\n✅ Sample users created successfully!")
            print("🎯 Next step: Run the main API to use CRUD operations")
            print("   python main.py")
            print("   Then visit: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
    
    finally:
        await generator.close()

if __name__ == "__main__":
    asyncio.run(main()) 