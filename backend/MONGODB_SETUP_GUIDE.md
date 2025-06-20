# 🚀 Complete Setup Guide - Crypto Chatbot with MongoDB Cloud

## 📋 **Prerequisites**
- Windows 10/11
- Internet connection
- No database installation needed (using MongoDB Cloud!)

---

## **STEP 1: Setup Python Environment**

### 1.1 Navigate to Project
```powershell
cd D:\3rd\2ndSem\MLOps\MLOPS_food\backend
```

### 1.2 Check Python Installation
```powershell
python --version
```
*If Python not found, install from: https://www.python.org/downloads/*

### 1.3 Install Required Packages
```powershell
pip install -r requirements.txt
```

---

## **STEP 2: Configure Application**

### 2.1 Run Environment Setup
```powershell
python setup_environment.py
```

This will:
- ✅ Create `.env` file with MongoDB connection
- ✅ Check required packages
- ✅ Test MongoDB Cloud connection

### 2.2 Edit .env File (IMPORTANT!)
**Open `.env` file and add your real Gemini API key:**

```env
# API Keys
GEMINI_API_KEY=your_real_gemini_api_key_here

# MongoDB Configuration
MONGODB_URL=mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/?retryWrites=true&w=majority&appName=mlops1

# Server Configuration - Make accessible from other computers
HOST=0.0.0.0
PORT=8000
```

**Get Gemini API Key:**
- Go to: https://makersuite.google.com/app/apikey
- Create new API key
- Copy and paste into `.env` file

---

## **STEP 3: Initialize Database**

### 3.1 Setup MongoDB Collections
```powershell
python database_setup.py
```

**Expected output:**
```
✅ Connected to MongoDB successfully!
   MongoDB version: 7.x.x
   Database: crypto_chatbot
✅ Created 'users' collection with indexes
✅ Created 'conversation_history' collection with indexes
✅ Created 'news' collection with indexes
✅ Created 'predictions' collection with indexes
```

### 3.2 Add Sample Data
```powershell
python sample_data.py
```

**Expected output:**
```
✅ Connected to MongoDB successfully!
✅ Created user: john_trader (ID: 67a...)
✅ Created user: crypto_alice (ID: 67b...)
✅ Created user: btc_bob (ID: 67c...)
✅ Created user: demo_user (ID: 67d...)
✅ Created 7 sample conversations

📊 Database Summary:
   👥 Total Users: 4
   💬 Total Conversations: 7
```

---

## **STEP 4: Start the Application**

### 4.1 Run the Server
```powershell
python main.py
```

**Expected output:**
```
🚀 Starting FastAPI server on 0.0.0.0:8000
📡 Local access: http://localhost:8000
🌐 Network access: http://YOUR_IP_ADDRESS:8000
📚 API Documentation: http://localhost:8000/docs
🗄️  Database: MongoDB Cloud
================================================================
```

### 4.2 Test Local Access
- **Open browser:** http://localhost:8000/docs
- **You should see:** FastAPI interactive documentation

---

## **STEP 5: Make Accessible from Other Computers**

### 5.1 Find Your IP Address
```powershell
ipconfig
```
**Look for:** `IPv4 Address` (e.g., `192.168.1.100`)

### 5.2 Configure Windows Firewall
1. **Windows Security** → **Firewall & network protection**
2. **Advanced settings**
3. **Inbound Rules** → **New Rule**
4. **Port** → **TCP** → **Specific Local Ports:** `8000`
5. **Allow the connection**
6. **Name:** `Crypto Chatbot API`

### 5.3 Test Network Access
**From another computer:**
- **Browser:** `http://YOUR_IP_ADDRESS:8000/docs`
- **Example:** `http://192.168.1.100:8000/docs`

---

## **STEP 6: Test the Database and API**

### 6.1 View Database Collections
**Use the API to view database structure:**
```bash
curl "http://localhost:8000/database/tables"
```

**Or open in browser:**
- http://localhost:8000/database/tables

### 6.2 Test API Endpoints

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

**Health check:**
```bash
curl "http://localhost:8000/health"
```

---

## **STEP 7: Access from Other Computers**

### 7.1 Share Your IP Address
**Tell others to access:**
- **API Docs:** `http://YOUR_IP:8000/docs`
- **Example:** `http://192.168.1.100:8000/docs`

### 7.2 From Mobile/Tablet
- **Same WiFi network:** Use same IP address
- **Browser:** Navigate to `http://YOUR_IP:8000/docs`

### 7.3 Data Persistence & Global Access
**MongoDB Cloud Benefits:**
- ✅ **Data accessible from anywhere** with internet
- ✅ **No local database installation** required
- ✅ **Automatic backups** and scaling
- ✅ **Multiple users can access** the same data globally
- ✅ **Data survives** computer restarts/shutdowns
- ✅ **High availability** and redundancy

---

## **🌐 Global Access Features**

### Anyone Can Access Your API:
1. **Same WiFi Network:** Use your local IP (192.168.x.x)
2. **Internet Access:** Deploy to cloud platforms like:
   - **Heroku:** Free hosting
   - **Railway:** Easy deployment
   - **DigitalOcean:** VPS hosting
   - **AWS/GCP:** Enterprise solutions

### MongoDB Cloud Database:
- **Connection:** Works from any computer with internet
- **Security:** Username/password protected
- **Speed:** Optimized for global access
- **Backup:** Automatic data backup and recovery

---

## **🔧 Troubleshooting**

### MongoDB Connection Issues
```powershell
# Test MongoDB connection
python -c "import pymongo; client = pymongo.MongoClient('mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/'); client.admin.command('ping'); print('✅ Connected!')"
```

### Can't Access from Other Computers
1. **Check firewall** (Windows Defender)
2. **Verify IP address** with `ipconfig`
3. **Ensure same network** (WiFi/LAN)
4. **Try:** `http://IP:8000/docs` not `https://`

### Application Won't Start
1. **Check Python installation:** `python --version`
2. **Install packages:** `pip install -r requirements.txt`
3. **Check internet connection** for MongoDB
4. **Verify .env file** has correct Gemini API key

### Missing Packages Error
```powershell
pip install fastapi uvicorn pymongo motor dnspython python-dotenv google-generativeai
```

---

## **📊 Database Management**

### Using MongoDB Compass (Optional)
1. **Download:** https://www.mongodb.com/products/compass
2. **Connection String:** `mongodb+srv://user1:Toilaan123*@mlops1.o9mdodh.mongodb.net/`
3. **View Collections:** Users, conversations, news, predictions
4. **Query Data:** Visual interface for database queries

### API Database Endpoints:
- **View Collections:** `GET /database/tables`
- **User List:** `GET /users`
- **Conversations:** `GET /conversation-history`
- **Health Check:** `GET /health`

---

## **🎉 Success Checklist**

- ✅ Python and packages installed
- ✅ MongoDB Cloud connection working
- ✅ Collections created with indexes
- ✅ Sample data loaded (4 users, 7 conversations)
- ✅ Application starts on `http://localhost:8000`
- ✅ API docs accessible at `/docs`
- ✅ Other computers can access via your IP
- ✅ Database accessible globally via MongoDB Cloud
- ✅ Data persists across restarts

**🌐 Your API is now accessible globally with cloud database storage!**

---

## **🚀 Deployment Options**

### For Global Internet Access:

#### Option 1: Railway (Recommended)
1. **Create account:** https://railway.app/
2. **Connect GitHub repo**
3. **Deploy automatically**
4. **Get public URL:** `https://your-app.railway.app`

#### Option 2: Heroku
1. **Create account:** https://heroku.com/
2. **Install Heroku CLI**
3. **Deploy with Git**
4. **Get public URL:** `https://your-app.herokuapp.com`

#### Option 3: DigitalOcean App Platform
1. **Create account:** https://www.digitalocean.com/
2. **Deploy from GitHub**
3. **Get public URL:** `https://your-app.ondigitalocean.app`

**With cloud deployment + MongoDB Cloud = Fully global crypto chatbot! 🌍** 