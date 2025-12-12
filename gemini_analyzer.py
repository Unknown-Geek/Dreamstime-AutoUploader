"""
Gemini AI Image Analyzer
Analyzes images using Google's Gemini Vision API to generate titles and descriptions
"""

import google.generativeai as genai
from PIL import Image
import logging
from config import Config

logger = logging.getLogger(__name__)


class GeminiImageAnalyzer:
    """Analyzes images using Gemini Vision API"""
    
    def __init__(self):
        """Initialize Gemini API"""
        if not Config.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            self.enabled = False
            return
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            logger.info("Gemini AI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            self.enabled = False
    
    def generate_title_only(self, image_path):
        """
        Generate only a title for the image (optimized for speed)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str with title, or None if failed
        """
        if not self.enabled:
            logger.warning("Gemini API not enabled, skipping analysis")
            return None
        
        try:
            # Load image
            img = Image.open(image_path)
            
            # Prepare prompt for stock photography title only
            prompt = """Analyze this image for stock photography submission. Generate ONLY a TITLE:

Requirements:
- Maximum 115 characters
- Descriptive and SEO-friendly
- Highlight main subject and key elements
- Professional tone
- No colons or special characters

Format your response EXACTLY as:
TITLE: [your title here]"""
            
            # Generate content
            response = self.model.generate_content([prompt, img])
            
            # Parse response
            title = self._parse_title_response(response.text)
            
            if title:
                logger.info(f"Generated title: {title[:50]}...")
            
            return title
            
        except Exception as e:
            logger.error(f"Failed to generate title: {str(e)}")
            return None
    
    def analyze_image(self, image_path):
        """
        Analyze an image and generate title and description
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict with 'title' and 'description' keys, or None if failed
        """
        if not self.enabled:
            logger.warning("Gemini API not enabled, skipping analysis")
            return None
        
        try:
            # Load image
            img = Image.open(image_path)
            
            # Prepare prompt for stock photography
            prompt = """Analyze this image for stock photography submission. Generate:

1. TITLE (max 115 characters):
   - Descriptive and SEO-friendly
   - Highlight main subject and key elements
   - Professional tone
   - No colons or special characters

2. DESCRIPTION (2-3 sentences, max 200 characters):
   - Detailed description of what's in the image
   - Include colors, mood, composition, and setting
   - Mention potential use cases
   - Professional and engaging

Format your response EXACTLY as:
TITLE: [your title here]
DESCRIPTION: [your description here]"""
            
            # Generate content
            response = self.model.generate_content([prompt, img])
            
            # Parse response
            result = self._parse_response(response.text)
            
            if result:
                logger.info(f"Generated title: {result['title'][:50]}...")
                logger.info(f"Generated description: {result['description'][:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze image: {str(e)}")
            return None
    
    def _parse_title_response(self, response_text):
        """Parse Gemini response to extract title only"""
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('TITLE:'):
                    title = line.split(':', 1)[1].strip()
                    # Remove any quotes or extra formatting
                    title = title.strip('"\'')
                    # Limit to 115 characters
                    if len(title) > 115:
                        title = title[:112] + '...'
                    return title
            
            logger.warning("Could not parse title from Gemini response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini title response: {str(e)}")
            return None
    
    def _parse_response(self, response_text):
        """Parse Gemini response to extract title and description"""
        try:
            lines = response_text.strip().split('\n')
            
            title = None
            description = None
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('TITLE:'):
                    title = line.split(':', 1)[1].strip()
                    # Remove any quotes or extra formatting
                    title = title.strip('"\'')
                    # Limit to 115 characters
                    if len(title) > 115:
                        title = title[:112] + '...'
                elif line.upper().startswith('DESCRIPTION:'):
                    description = line.split(':', 1)[1].strip()
                    description = description.strip('"\'')
            
            if title and description:
                return {
                    'title': title,
                    'description': description
                }
            
            logger.warning("Could not parse title/description from Gemini response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {str(e)}")
            return None
    
    def enhance_description(self, description, template_text=""):
        """
        Enhance existing description with template text
        
        Args:
            description: Original description
            template_text: Template text to append
            
        Returns:
            Enhanced description
        """
        if not description:
            return template_text
        
        if template_text:
            return f"{description}{template_text}"
        
        return description
