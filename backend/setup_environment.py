"""
Environment setup script for Crypto Chatbot (MongoDB Version)
This script helps you set up the environment variables and check system requirements.
"""

import os
import sys

def create_env_file():
    """Create .env file with default configuration."""
    
    print("🔧 Setting up environment variables...")
    
    env_content = """# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB Configuration
MONGODB_URL=mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1

# Server Configuration - Make accessible from other computers
HOST=0.0.0.0
PORT=8000
"""
    
    env_file_path = ".env"
    
    if os.path.exists(env_file_path):
        print("ℹ️  .env file already exists")
        with open(env_file_path, 'r') as f:
            current_content = f.read()
        print("Current .env content:")
        print("-" * 40)
        print(current_content)
        print("-" * 40)
        
        response = input("Do you want to overwrite it? (y/n): ").lower()
        if response != 'y':
            print("Keeping existing .env file")
            return
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file successfully!")
        print("\n⚠️  IMPORTANT: Edit the .env file and add your real GEMINI_API_KEY")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False
    
    return True

def check_python_packages():
    """Check if required packages are installed."""
    
    print("\n🔍 Checking Python packages...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pymongo', 'motor', 'dnspython',
        'pandas', 'python-dotenv', 'google-generativeai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed!")
    return True

def test_mongodb_connection():
    """Test MongoDB connection."""
    
    print("\n🔍 Testing MongoDB connection...")
    
    try:
        import pymongo
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # MongoDB connection string
        mongodb_url = "mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1"
        
        # Try to connect
        client = pymongo.MongoClient(mongodb_url)
        
        # Test connection
        client.admin.command('ping')
        
        # Get server info
        server_info = client.server_info()
        
        print("✅ MongoDB connection successful!")
        print(f"   MongoDB version: {server_info['version']}")
        print(f"   Database: crypto_chatbot")
        print(f"   Connection: MongoDB Cloud (Atlas)")
        
        client.close()
        return True
        
    except ImportError:
        print("❌ pymongo not installed. Run: pip install pymongo")
        return False
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n🛠️  To fix this:")
        print("1. Check your internet connection")
        print("2. Verify the MongoDB connection string is correct")
        print("3. Make sure the MongoDB cluster is running")
        print("4. Check if your IP is whitelisted in MongoDB Atlas")
        return False

def show_next_steps():
    """Show the next steps to run the application."""
    
    print("\n🎯 Next Steps:")
    print("1. Edit .env file and add your real GEMINI_API_KEY")
    print("2. Run: python database_setup.py")
    print("3. Run: python sample_data.py")
    print("4. Run: python main.py")
    print("5. Open browser: http://localhost:8000/docs")
    print("\n🌐 To access from other computers:")
    print("- Find your IP address: ipconfig")
    print("- Other computers can access: http://YOUR_IP:8000")
    print("\n💾 Database Info:")
    print("- Using MongoDB Cloud (Atlas)")
    print("- No local database installation needed")
    print("- Data is stored in the cloud and accessible from anywhere")

def main():
    """Main setup function."""
    
    print("🚀 Crypto Chatbot Environment Setup (MongoDB Version)")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Please run this script from the backend directory")
        print("   cd backend")
        print("   python setup_environment.py")
        return
    
    # Step 1: Create .env file
    if not create_env_file():
        return
    
    # Step 2: Check packages
    if not check_python_packages():
        print("\n❌ Please install missing packages first:")
        print("pip install -r requirements.txt")
        return
    
    # Step 3: Test MongoDB connection
    db_connected = test_mongodb_connection()
    
    # Step 4: Show next steps
    show_next_steps()
    
    if db_connected:
        print("\n✅ Setup completed successfully!")
        print("🌐 MongoDB Cloud connection verified!")
    else:
        print("\n⚠️  Setup completed but MongoDB connection failed")
        print("Please check the connection and try again")

if __name__ == "__main__":
    main() 