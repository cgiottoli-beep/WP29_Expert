"""
Configuration module for UNECE WP.29 Archive
Loads and validates environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

class Config:
    """Application configuration"""
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Google Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Storage
    STORAGE_BUCKET = "unece-archive"
    CHUNKS_CACHE_BUCKET = "chunks_cache"  # For storing chunk JSON files
    
    # AI Models (Gemini 2.x)
    GEMINI_FLASH_MODEL = "models/gemini-2.0-flash"
    GEMINI_PRO_MODEL = "models/gemini-2.5-pro"
    GEMINI_EMBEDDING_MODEL = "models/embedding-001"
    
    # App Version
    APP_VERSION = "1.1.0"
    APP_DATE = "2026-01-13"
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "GOOGLE_API_KEY": cls.GOOGLE_API_KEY,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file"
            )
        
        return True

# Validate on import
Config.validate()
