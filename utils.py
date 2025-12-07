import random
import time
import logging

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages description templates for enhancing image descriptions"""
    
    TEMPLATE1 = [
        ", high resolution",
        ", aesthetic background",
        ", stunning visual effect",
        ", detailed texture",
        ", artistic vibe",
        ", captivating background",
        ", high quality result",
        ", elegant style",
        ", mesmerizing view",
        ", beautiful background",
        ", professional touch",
        ", vibrant tone",
        ", luxurious feel",
        ", cinematic background",
        ", colorful theme",
        ", minimalist background",
        ", vintage charm",
        ", futuristic concept",
        ", abstract background",
        ", modern aesthetic",
        ", polished appearance",
        ", seamless texture",
        ", harmonious background",
        ", immersive atmosphere",
        ", nature-inspired background",
        ", bold composition",
        ", intricate background design",
        ", glossy reflection",
        ", refined elegance",
        ", subtle gradient",
        ", dreamy concept",
        ", expressive background details",
        ", creative perspective",
        ", layered depth",
        ", smooth transitions",
        ", timeless background beauty",
        ", fresh tone",
        ", urban background",
        ", artistic arrangement",
        ", dynamic background flow"
    ]
    
    TEMPLATE2 = [
        ", glowing background effect",
        ", intricate detail",
        ", serene vibe",
        ", cozy background atmosphere",
        ", exotic touch",
        ", pastel background tone",
        ", bold appearance",
        ", surreal background theme",
        ", enchanting mood",
        ", rustic texture",
        ", glossy background finish",
        ", monochrome style",
        ", geometric background pattern",
        ", dynamic flow",
        ", dreamy and soft background gradient",
        ", playful design",
        ", refined background touch",
        ", sophisticated detail",
        ", urban aesthetic",
        ", whimsical background charm",
        ", radiant glow",
        ", natural elegance",
        ", fluid motion",
        ", stylish background execution",
        ", polished lines",
        ", innovative background concept",
        ", vibrant highlights",
        ", balanced composition",
        ", gentle background curves",
        ", cool tones",
        ", modern simplicity",
        ", artistic harmony",
        ", textured dimension",
        ", vivid saturation",
        ", contrasting background elements",
        ", fresh composition",
        ", subtle details",
        ", timeless atmosphere",
        ", bright inspiration",
        ", dynamic background perspective"
    ]
    
    @staticmethod
    def get_random_text(template_name):
        """
        Get random template text based on template name
        
        Args:
            template_name: "template1", "template2", or "none"
            
        Returns:
            Random template text or empty string if "none"
        """
        if template_name == "template1":
            return random.choice(TemplateManager.TEMPLATE1)
        elif template_name == "template2":
            return random.choice(TemplateManager.TEMPLATE2)
        else:
            return ""


class DelayCalculator:
    """Calculate human-like random delays"""
    
    @staticmethod
    def calculate(delay_option="fast"):
        """
        Calculate random delay in seconds
        
        Args:
            delay_option: "fast" or "slow"
            
        Returns:
            Random delay in seconds
        """
        if delay_option == "slow":
            # 10-15 seconds for slow mode
            return random.randint(10, 15)
        else:
            # 5-10 seconds for fast mode
            return random.randint(5, 10)


def sanitize_title(title):
    """
    Sanitize title text: replace colons with commas and limit to 115 characters
    
    Args:
        title: Original title text
        
    Returns:
        Sanitized title
    """
    if not title:
        return ""
    
    # Replace colons with commas
    sanitized = title.replace(":", ",")
    
    # Truncate to 115 characters
    if len(sanitized) > 115:
        sanitized = sanitized[:115]
    
    return sanitized


def safe_wait(page, ms, stop_check_callback=None):
    """
    Wait with periodic stop check
    
    Args:
        page: Playwright page object
        ms: Milliseconds to wait
        stop_check_callback: Function that returns True if stop requested
        
    Raises:
        StopRequestedException: If stop is requested during wait
    """
    if stop_check_callback is None:
        page.wait_for_timeout(ms)
        return
    
    # Check stop flag every 100ms
    interval = 100
    elapsed = 0
    
    while elapsed < ms:
        if stop_check_callback():
            raise StopRequestedException("Stop requested during wait")
        
        wait_time = min(interval, ms - elapsed)
        page.wait_for_timeout(wait_time)
        elapsed += wait_time


class StopRequestedException(Exception):
    """Exception raised when automation stop is requested"""
    pass
