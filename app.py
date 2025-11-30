import os
import logging
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

logging.basicConfig(level=logging.WARNING)  # Changed from DEBUG to WARNING to reduce noise

# Vercel deployment detection
is_vercel = os.environ.get('VERCEL', False)

if is_vercel:
    # In Vercel, we're running from the root directory
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
else:
    # Local development
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

MONGODB_URI = "mongodb+srv://root:root@cluster0.lw4vrik.mongodb.net/?appName=Cluster0"

mongo_client = None
db = None

def get_db():
    global mongo_client, db
    if mongo_client is None:
        try:
            # Add connection options for better reliability
            mongo_client = MongoClient(
                MONGODB_URI,
                server_api=ServerApi('1'),
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connection timeout
                socketTimeoutMS=45000,  # 45 second socket timeout
                maxPoolSize=10,
                minPoolSize=2,
                maxIdleTimeMS=30000,
                retryWrites=True,
                retryReads=True
            )
            # Test the connection
            mongo_client.admin.command('ping')
            db = mongo_client.research_intelligence
            logging.info("Successfully connected to MongoDB!")
        except (ServerSelectionTimeoutError, OperationFailure) as e:
            logging.error(f"MongoDB connection failed: {e}")
            mongo_client = None
            db = None
        except Exception as e:
            logging.error(f"Unexpected MongoDB error: {e}")
            mongo_client = None
            db = None
    return db

def init_default_api_keys():
    database = get_db()
    if database is not None:
        api_keys_collection = database.api_keys
        existing = api_keys_collection.find_one({"_id": "default"})
        if not existing:
            default_keys = {
                "_id": "default",
                "serper": os.environ.get("SERPER_API_KEY", ""),
                "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
                "cartesia": os.environ.get("CARTESIA_API_KEY", ""),
                "deepgram": os.environ.get("DEEPGRAM_API_KEY", ""),
                "firecrawl": os.environ.get("FIRECRAWL_API_KEY", ""),
                "sonar": os.environ.get("SONAR_API_KEY", "")
            }
            api_keys_collection.insert_one(default_keys)
            logging.info("Default API keys initialized from environment")

with app.app_context():
    init_default_api_keys()

import routes
