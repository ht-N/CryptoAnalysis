# 🚀 Complete Setup Guide - Crypto Chatbot with Network Access

## 📋 **Prerequisites**
- Windows 10/11
- Internet connection
- Admin rights (for PostgreSQL installation)

---

## **STEP 1: Install PostgreSQL** 

### 1.1 Download PostgreSQL
- Go to: https://www.postgresql.org/download/windows/
- Download **Windows x86-64** version (latest stable)
- **File size:** ~350MB

### 1.2 Install PostgreSQL
1. **Run installer as Administrator**
2. **Installation directory:** Keep default (`C:\Program Files\PostgreSQL\16\`)
3. **Components:** ✅ PostgreSQL Server, ✅ pgAdmin 4, ✅ Command Line Tools
4. **Data directory:** Keep default
5. **Password:** Set password for `postgres` user (remember this!)
6. **Port:** Keep `5432`
7. **Locale:** Keep default
8. **Finish installation**

### 1.3 Verify PostgreSQL is Running
1. **Open Services** (`Win + R` → `services.msc`)
2. **Look for:** `postgresql-x64-16` (or similar)
3. **Status should be:** `Running`

---

## **STEP 2: Setup Database in pgAdmin**

### 2.1 Open pgAdmin 4
- **Start Menu** → **PostgreSQL 16** → **pgAdmin 4**
- **Set master password** (first time only)

### 2.2 Connect to PostgreSQL
1. **Click "Add New Server"** or right-click "Servers"
2. **General Tab:**
   - **Name:** `Local PostgreSQL`
3. **Connection Tab:**
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `postgres`
   - **Username:** `postgres`
   - **Password:** `[your installation password]`
4. **Click Save**

### 2.3 Create Crypto Database
1. **Right-click server** → **Query Tool**
2. **Copy and paste these commands:**

```sql
-- Create user for the application
CREATE USER crypto_user WITH PASSWORD 'crypto_password';

-- Create database
CREATE DATABASE crypto_chatbot OWNER crypto_user;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE crypto_chatbot TO crypto_user;
ALTER USER crypto_user CREATEDB;
```

3. **Click Execute** (⚡ button)
4. **You should see:** `Query returned successfully`

---

## **STEP 3: Setup Python Environment**

### 3.1 Navigate to Project
```powershell
cd D:\3rd\2ndSem\MLOps\MLOPS_food\backend
```

### 3.2 Check Python Installation
```powershell
python --version
```
*If Python not found, install from: https://www.python.org/downloads/*

### 3.3 Install Required Packages
```powershell
pip install -r requirements.txt
```

---

## **STEP 4: Configure Application**

### 4.1 Run Environment Setup
```powershell
python setup_environment.py
```

This will:
- ✅ Create `.env` file
- ✅ Check packages
- ✅ Test database connection

### 4.2 Edit .env File (IMPORTANT!)
**Open `.env` file and add your real Gemini API key:**

```env
# API Keys
GEMINI_API_KEY=your_real_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://crypto_user:crypto_password@localhost:5432/crypto_chatbot

# Server Configuration - Make accessible from other computers
HOST=0.0.0.0
PORT=8000
```

**Get Gemini API Key:**
- Go to: https://makersuite.google.com/app/apikey
- Create new API key
- Copy and paste into `.env` file

---

## **STEP 5: Initialize Database**

### 5.1 Create Database Tables
```powershell
python database_setup.py
```

**Expected output:**
```
✅ Database 'crypto_chatbot' created successfully!
✅ Connected to PostgreSQL: PostgreSQL 16.x...
✅ Database tables created successfully!
✅ Created tables: users, conversation_history
```

### 5.2 Add Sample Data
```powershell
python sample_data.py
```

**Expected output:**
```
✅ Created user: john_trader (ID: 1)
✅ Created user: crypto_alice (ID: 2)
✅ Created user: btc_bob (ID: 3)
✅ Created user: demo_user (ID: 4)
✅ Created 7 sample conversations

📊 Database Summary:
   👥 Total Users: 4
   💬 Total Conversations: 7
```

---

## **STEP 6: Start the Application**

### 6.1 Run the Server
```powershell
python main.py
```

**Expected output:**
```
🚀 Starting FastAPI server on 0.0.0.0:8000
📡 Local access: http://localhost:8000
🌐 Network access: http://YOUR_IP_ADDRESS:8000
📚 API Documentation: http://localhost:8000/docs
🗄️  Database: PostgreSQL on localhost:5432
================================================================
```

### 6.2 Test Local Access
- **Open browser:** http://localhost:8000/docs
- **You should see:** FastAPI interactive documentation

---

## **STEP 7: Make Accessible from Other Computers**

### 7.1 Find Your IP Address
```powershell
ipconfig
```
**Look for:** `IPv4 Address` (e.g., `192.168.1.100`)

### 7.2 Configure Windows Firewall
1. **Windows Security** → **Firewall & network protection**
2. **Advanced settings**
3. **Inbound Rules** → **New Rule**
4. **Port** → **TCP** → **Specific Local Ports:** `8000`
5. **Allow the connection**
6. **Name:** `Crypto Chatbot API`

### 7.3 Test Network Access
**From another computer:**
- **Browser:** `http://YOUR_IP_ADDRESS:8000/docs`
- **Example:** `http://192.168.1.100:8000/docs`

---

## **STEP 8: Test the Database and API**

### 8.1 View Database in pgAdmin
1. **Connect to:** `crypto_chatbot` database with `crypto_user`
2. **Browse:** `Schemas` → `public` → `Tables`
3. **You should see:** `users` and `conversation_history` tables
4. **Right-click table** → **View/Edit Data** → **All Rows**

### 8.2 Test API Endpoints

**Register a new user:**
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "full_name": "Test User"}'
```

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Bitcoin giá bao nhiêu?", "username": "testuser"}'
```

**View all users:**
```bash
curl "http://localhost:8000/users"
```

**View database tables:**
```bash
curl "http://localhost:8000/database/tables"
```

---

## **STEP 9: Access from Other Computers**

### 9.1 Share Your IP Address
**Tell others to access:**
- **API Docs:** `http://YOUR_IP:8000/docs`
- **Example:** `http://192.168.1.100:8000/docs`

### 9.2 From Mobile/Tablet
- **Same WiFi network:** Use same IP address
- **Browser:** Navigate to `http://YOUR_IP:8000/docs`

### 9.3 Data Persistence
**All data is stored in PostgreSQL:**
- ✅ **User registrations** persist across restarts
- ✅ **Conversations** are saved automatically
- ✅ **Other computers** see the same data
- ✅ **Database survives** application restarts

---

## **🔧 Troubleshooting**

### Database Connection Issues
```powershell
# Test database connection
python -c "import psycopg2; conn = psycopg2.connect('postgresql://crypto_user:crypto_password@localhost:5432/crypto_chatbot'); print('✅ Connected!')"
```

### Can't Access from Other Computers
1. **Check firewall** (Windows Defender)
2. **Verify IP address** with `ipconfig`
3. **Ensure same network** (WiFi/LAN)
4. **Try:** `http://IP:8000/docs` not `https://`

### Application Won't Start
1. **Check Python installation:** `python --version`
2. **Install packages:** `pip install -r requirements.txt`
3. **Check PostgreSQL service** in `services.msc`
4. **Verify .env file** has correct Gemini API key

---

## **🎉 Success Checklist**

- ✅ PostgreSQL installed and running
- ✅ Database `crypto_chatbot` created with tables
- ✅ Sample data loaded (4 users, 7 conversations)
- ✅ Application starts on `http://localhost:8000`
- ✅ API docs accessible at `/docs`
- ✅ Other computers can access via your IP
- ✅ Database viewable in pgAdmin
- ✅ New data persists across restarts

**🌐 Your API is now accessible from any computer on your network!** 