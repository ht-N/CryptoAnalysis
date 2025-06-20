"""
Database setup script for the Crypto Chatbot application.
This script helps you create the database and tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database_if_not_exists(database_url: str, database_name: str):
    """
    Creates the database if it doesn't exist.
    
    Args:
        database_url: PostgreSQL connection URL without database name
        database_name: Name of the database to create
    """
    try:
        # Connect to PostgreSQL server (not to specific database)
        base_url = database_url.rsplit('/', 1)[0]  # Remove database name from URL
        conn = psycopg2.connect(base_url + '/postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            print(f"✅ Database '{database_name}' created successfully!")
        else:
            print(f"✅ Database '{database_name}' already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def setup_database():
    """
    Main function to set up the database and tables.
    """
    print("🗄️  Setting up PostgreSQL database for Crypto Chatbot...")
    
    # Get database URL from environment or use default
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/crypto_chatbot")
    database_url = DATABASE_URL
    
    # Extract database name
    database_name = database_url.split('/')[-1]
    
    print(f"Database URL: {database_url}")
    print(f"Database Name: {database_name}")
    
    # Create database if it doesn't exist
    if not create_database_if_not_exists(database_url, database_name):
        print("❌ Failed to create database. Please check your PostgreSQL connection.")
        sys.exit(1)
    
    try:
        # Create engine and connect to the database
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Import and create tables
        from main import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Created tables: {', '.join(tables)}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your .env file with the correct DATABASE_URL")
        print("2. Start the application with: python main.py")
        
    except SQLAlchemyError as e:
        print(f"❌ SQLAlchemy error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database() 