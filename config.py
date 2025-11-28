import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Dreamstime automation bot"""
    
    # Dreamstime credentials
    DREAMSTIME_USERNAME = os.getenv('DREAMSTIME_USERNAME', '')
    DREAMSTIME_PASSWORD = os.getenv('DREAMSTIME_PASSWORD', '')
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API settings for external integrations (n8n, webhooks, etc.)
    API_KEY = os.getenv('API_KEY', '')  # Optional API key for authentication
    REQUIRE_API_KEY = os.getenv('REQUIRE_API_KEY', 'False').lower() == 'true'
    
    # Gemini AI settings for image analysis
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Playwright settings
    # Auto-detect Docker environment and force headless mode
    IS_DOCKER = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true'
    HEADLESS = IS_DOCKER or os.getenv('HEADLESS', 'False').lower() == 'true'
    TIMEOUT = 30000  # 30 seconds in milliseconds
    VIEWPORT = {'width': 1280, 'height': 720}
    
    # Dreamstime URLs
    BASE_URL = 'https://www.dreamstime.com'
    LOGIN_URL = 'https://www.dreamstime.com/login'
    UPLOAD_URL = 'https://www.dreamstime.com/upload'
    
    # Automation configuration options (User's preferences)
    DEFAULT_TEMPLATE = 'template1'  # Always use professional template
    DEFAULT_MANUAL_DESCRIPTION = ''
    DEFAULT_MODEL_RELEASE = 'no'  # No model releases
    DEFAULT_EXCLUSIVE_IMAGE = 'no'  # Not exclusive
    DEFAULT_AI_IMAGE = 'yes'  # All images marked as AI generated
    DEFAULT_DELAY = 'fast'  # Fast processing with random small pauses (1-5 seconds)
    DEFAULT_REPEAT_COUNT = 999  # Process all unfinished images
    DEFAULT_PAUSE_AFTER = 0  # No pause intervals between batches
    DEFAULT_PAUSE_DURATION = 60
    DEFAULT_SAME_ID_ACTION = 'skip'  # Skip duplicates
    MAX_RETRIES = 3
    
    @classmethod
    def validate_credentials(cls):
        """Validate that credentials are configured"""
        if not cls.DREAMSTIME_USERNAME or not cls.DREAMSTIME_PASSWORD:
            raise ValueError("Dreamstime credentials not configured. Please set DREAMSTIME_USERNAME and DREAMSTIME_PASSWORD in .env file")
        return True
