"""
Environment setup script for Crypto Chatbot
This script helps you set up the environment variables and check system requirements.
"""

import os
import sys

def create_env_file():
    """Create .env file with default configuration."""
    
    print("🔧 Setting up environment variables...")
    
    env_content = """# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://crypto_user:crypto_password@localhost:5432/crypto_chatbot

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
        'fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2-binary', 
        'pandas', 'python-dotenv'
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

def test_database_connection():
    """Test database connection."""
    
    print("\n🔍 Testing database connection...")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Try to connect
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="crypto_chatbot",
            user="crypto_user",
            password="crypto_password"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print("✅ Database connection successful!")
        print(f"   PostgreSQL version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🛠️  To fix this:")
        print("1. Make sure PostgreSQL is running")
        print("2. Create the database and user in pgAdmin:")
        print("   CREATE USER crypto_user WITH PASSWORD 'crypto_password';")
        print("   CREATE DATABASE crypto_chatbot OWNER crypto_user;")
        print("   GRANT ALL PRIVILEGES ON DATABASE crypto_chatbot TO crypto_user;")
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

def main():
    """Main setup function."""
    
    print("🚀 Crypto Chatbot Environment Setup")
    print("=" * 50)
    
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
    
    # Step 3: Test database
    db_connected = test_database_connection()
    
    # Step 4: Show next steps
    show_next_steps()
    
    if db_connected:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n⚠️  Setup completed but database connection failed")
        print("Please fix the database connection before proceeding")

if __name__ == "__main__":
    main() 