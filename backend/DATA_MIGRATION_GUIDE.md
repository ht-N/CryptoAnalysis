# Data Migration Guide - Push Data to MongoDB

## Overview
This guide explains how to use the `push_data_to_mongodb.py` script to migrate all your CSV data files to MongoDB Cloud.

## What Data Gets Migrated

### Main Data Files (`/data/` folder):
1. **symbols.csv** → `symbols` collection
   - All cryptocurrency symbols
   - Added metadata: created_at, source, is_active

2. **predict.csv** → `predictions` collection  
   - Price predictions for each coin
   - Current price, estimated price, gain percentages
   - ARIMA and XGBoost model results

3. **analysis.csv** → `market_analysis` collection
   - Sentiment analysis results
   - Coin names and sentiment labels (positive/negative/neutral)

4. **news.csv** → `news_links` collection
   - Binance news links for each cryptocurrency
   - Auto-extracted coin names from URLs

5. **binance_news.csv** → `binance_news` collection
   - Complete news article content
   - Coin-specific news with full text search capability

### Processed Data Files (`/data/processed/` folder):
6. **analysis.csv** → `processed_analysis` collection
7. **predict.csv** → `processed_predictions` collection  
8. **scoring.csv** → `processed_scoring` collection

## Database Structure

Each collection includes:
- **Indexes** for fast querying
- **Timestamps** (created_at)
- **Source tracking** (which file the data came from)
- **Metadata** for better organization

## How to Run the Migration

### Prerequisites
```bash
# Make sure you're in the backend directory
cd backend

# Install required packages (should already be installed)
pip install motor pandas python-dotenv pymongo
```

### Run the Migration
```bash
python push_data_to_mongodb.py
```

### Expected Output
```
🚀 Starting Data Migration to MongoDB
============================================================

✅ Connected to MongoDB successfully!

🗑️  Cleaning existing data collections...
🗑️  Dropped existing collection: symbols
🗑️  Dropped existing collection: predictions
...

🔧 Creating database indexes...
✅ Created indexes for 'symbols' collection
✅ Created indexes for 'predictions' collection
...

📂 Migrating data files...
📊 Processing 11 symbols...
✅ Inserted 11 symbols

📊 Processing 11 predictions...
✅ Inserted 11 predictions

📊 Processing 244 analysis records...
✅ Inserted 244 analysis records

📊 Processing 11 news links...
✅ Inserted 11 news links

📊 Processing 244 Binance news articles...
✅ Inserted 244 Binance news articles

📊 Database Summary After Migration:
==================================================
📁 symbols              :     11 documents
📁 predictions          :     11 documents  
📁 market_analysis      :    244 documents
📁 news_links           :     11 documents
📁 binance_news         :    244 documents
📁 processed_analysis   :    246 documents
📁 processed_predictions:     11 documents
📁 processed_scoring    :     11 documents
==================================================
🎯 Total Documents: 789

✅ Data migration completed successfully!
```

## What Happens During Migration

1. **Connection Test**: Connects to MongoDB Cloud
2. **Clean Slate**: Drops existing data collections (optional)
3. **Index Creation**: Creates optimized indexes for fast queries
4. **Data Processing**: 
   - Reads each CSV file
   - Converts to MongoDB documents
   - Adds metadata and timestamps
   - Handles data type conversions
5. **Bulk Insert**: Efficiently uploads all data
6. **Summary Report**: Shows what was uploaded

## MongoDB Collections Created

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `symbols` | Crypto symbols | symbol, is_active |
| `predictions` | Price predictions | coin_name, current_price, estimated_price, gain% |
| `market_analysis` | Sentiment analysis | coin_name, label (positive/negative/neutral) |
| `news_links` | News URLs | link, coin_name, platform |
| `binance_news` | News content | coin_name, content, content_length |
| `processed_*` | Processed data | Various depending on source |

## Indexes Created

For optimal query performance:
- **Text search** on news content
- **Compound indexes** for coin_name + timestamp queries
- **Unique indexes** on symbols and news links
- **Ascending indexes** on commonly queried fields

## Verification Steps

After migration, verify your data:

1. **Check MongoDB Compass**:
   - Connect to your MongoDB Cloud cluster
   - Browse the `crypto_chatbot` database
   - Verify collections and document counts

2. **Test API Endpoints**:
   ```bash
   # Start your main application
   python main.py
   
   # Test the database tables endpoint
   curl http://localhost:8000/database/tables
   ```

3. **Test Chatbot Integration**:
   - Ask questions about crypto prices
   - Verify data is being retrieved correctly

## Troubleshooting

### Common Issues

**MongoDB Connection Failed**:
- Check your internet connection
- Verify MongoDB URL in environment variables
- Ensure MongoDB Cloud cluster is running

**File Not Found**:
- Make sure you're running from the `backend` directory
- Verify all CSV files exist in the `data` folder

**Memory Issues**:
- Large CSV files are processed in chunks
- If you get memory errors, consider splitting large files

**Permission Errors**:
- Ensure MongoDB user has read/write permissions
- Check if cluster IP whitelist includes your IP

### Re-running Migration

The script is designed to be re-runnable:
- It drops existing collections before migration
- Creates fresh indexes each time
- Safe to run multiple times

## Next Steps

After successful migration:

1. **Update Your Application**: Ensure all API endpoints can access the new data
2. **Test Functionality**: Verify chatbot responses use the migrated data  
3. **Monitor Performance**: Check query speeds with the new indexes
4. **Backup Strategy**: Consider setting up automated backups in MongoDB Atlas

## Support

If you encounter issues:
1. Check the console output for detailed error messages
2. Verify your MongoDB connection string
3. Ensure all required Python packages are installed
4. Check that data files are in the correct format

The migration script includes comprehensive error handling and will provide specific guidance for most common issues. 