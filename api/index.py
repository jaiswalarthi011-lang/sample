import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import our Flask app
from app import app

# Export the app for Vercel
app = app
