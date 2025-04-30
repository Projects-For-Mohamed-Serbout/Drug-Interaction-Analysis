import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from app.extractor.parser_engine import extract_all

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

def get_mongo_connection():
    """Establish and verify MongoDB connection"""
    try:
        client = MongoClient(MONGO_URI)
        # Verify connection by pinging the server
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

def save_to_mongodb(dictionary_data, prescription_data):
    """Save extracted data to MongoDB collections"""
    try:
        client = get_mongo_connection()
        db = client[MONGO_DB]

        # Process dictionaries
        for name, entries in dictionary_data.items():
            if not entries:
                print(f"⚠️ No data found for dictionary: {name}")
                continue
            
            collection = db[name]
            result = collection.delete_many({})  # Clear existing
            print(f"♻️ Cleared {result.deleted_count} documents from '{name}'")
            
            result = collection.insert_many(entries)
            print(f"✅ Saved {len(result.inserted_ids)} entries to '{name}'")

        # Process prescriptions
        if prescription_data and 'prescriptions' in prescription_data:
            collection = db["prescriptions"]
            result = collection.delete_many({})
            print(f"♻️ Cleared {result.deleted_count} prescriptions")
            
            result = collection.insert_many(prescription_data['prescriptions'])
            print(f"✅ Saved {len(result.inserted_ids)} prescriptions")
        
        print("🗂️ All data successfully loaded to MongoDB")
    except Exception as e:
        print(f"❌ Error saving to MongoDB: {e}")
        raise
    finally:
        client.close()

def main():
    """Main execution function"""
    print("🚀 Starting data loading process...")
    
    try:
        # Get data directory path
        data_dir = Path(__file__).parent.parent.parent / "data"
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found at: {data_dir}")
        
        print(f"📂 Loading data from: {data_dir}")
        
        # Extract data
        dictionaries, prescriptions = extract_all(data_dir)
        print("🔍 Data extraction completed successfully")
        
        # Save to MongoDB
        save_to_mongodb(dictionaries, prescriptions)
        
    except Exception as e:
        print(f"💥 Critical error: {e}")
        raise

if __name__ == "__main__":
    main()