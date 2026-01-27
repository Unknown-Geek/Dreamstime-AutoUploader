import time
import logging
import json
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import Config
from utils import (
    TemplateManager, 
    DelayCalculator, 
    sanitize_title, 
    safe_wait, 
    StopRequestedException
)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cookie file path
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'dreamstime_cookies.json')


class AutomationState:
    """Tracks automation state across processing"""
    
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.retry_count = 0
        self.last_image_id = ""
        self.processed_count = 0
        self.successful_count = 0
        self.page_stuck_count = 0  # Track consecutive stuck detections
        self.max_stuck_retries = 3  # Max times to refresh before giving up
    
    def reset(self):
        """Reset state for new automation run"""
        self.is_running = False
        self.stop_requested = False
        self.retry_count = 0
        self.last_image_id = ""
        self.processed_count = 0
        self.successful_count = 0
        self.page_stuck_count = 0
    
    def is_stop_requested(self):
        """Check if stop was requested"""
        return self.stop_requested


class DreamstimeBot:
    """Automation bot for Dreamstime image submission using Playwright"""
    
    def __init__(self, progress_callback=None, options=None):
        """
        Initialize the bot
        
        Args:
            progress_callback: Function to call with progress updates (step, message, status)
            options: Dictionary of automation options
        """
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.progress_callback = progress_callback
        self.state = AutomationState()
        

        # Automation options with defaults
        self.options = options or {}
        self.template = self.options.get('template', Config.DEFAULT_TEMPLATE)
        self.manual_description = self.options.get('manualDescription', Config.DEFAULT_MANUAL_DESCRIPTION)
        self.model_release = self.options.get('modelRelease', Config.DEFAULT_MODEL_RELEASE)
        self.exclusive_image = self.options.get('exclusiveImage', Config.DEFAULT_EXCLUSIVE_IMAGE)
        self.ai_image = self.options.get('aiImage', Config.DEFAULT_AI_IMAGE)
        self.delay = self.options.get('delay', Config.DEFAULT_DELAY)
        self.repeat_count = self.options.get('repeatCount', Config.DEFAULT_REPEAT_COUNT)
        self.pause_after = self.options.get('pauseAfter', Config.DEFAULT_PAUSE_AFTER)
        self.pause_duration = self.options.get('pauseDuration', Config.DEFAULT_PAUSE_DURATION)
        self.same_id_action = self.options.get('sameIdAction', Config.DEFAULT_SAME_ID_ACTION)
        
    def log_progress(self, step, message, status='info'):
        """Log progress and call callback if provided"""
        logger.info(f"Step {step}: {message}")
        if self.progress_callback:
            self.progress_callback(step, message, status)
    
    def setup_browser(self):
        """Initialize Playwright browser - connect to existing Chrome with remote debugging"""
        try:
            self.log_progress(0, "Connecting to existing Chrome session...", "info")
            
            self.playwright = sync_playwright().start()
            
            # Connect to Chrome running with --remote-debugging-port=9222
            try:
                self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                self.context = self.browser.contexts[0]
                
                # Get the active page - prefer the first page to maintain state
                if len(self.context.pages) > 0:
                    self.page = self.context.pages[0]
                    current_url = self.page.url
                    self.log_progress(0, f"Connected to existing page: {current_url}", "info")
                else:
                    self.page = self.context.new_page()
                
                self.page.set_default_timeout(Config.TIMEOUT)
                
                self.log_progress(0, "✅ Connected to existing Chrome session (page state preserved!)", "success")
                return True
                
            except Exception as e:
                self.log_progress(0, f"Failed to connect to Chrome: {str(e)}", "error")
                self.log_progress(0, "Please ensure Chrome is running with --remote-debugging-port=9222", "error")
                return False
            
        except Exception as e:
            self.log_progress(0, f"Failed to setup browser: {str(e)}", "error")
            return False
    
    def check_for_captcha(self):
        """Check if captcha is present and attempt automatic bypass, fallback to manual"""
        try:
            # Check page title first (most reliable indicator)
            page_title = self.page.title()
            captcha_detected = "denied" in page_title.lower() or "blocked" in page_title.lower()
            
            # Also check for common captcha element patterns
            if not captcha_detected:
                captcha_selectors = [
                    'text="Press & Hold"',
                    '.gkfWUyaFMteSFAk',
                    '[aria-label*="Press"]',
                    'text="Human Challenge"'
                ]
                for selector in captcha_selectors:
                    if self.page.locator(selector).count() > 0:
                        captcha_detected = True
                        break
            
            if captcha_detected:
                self.log_progress(-1, f"⚠️ CAPTCHA DETECTED (title: {page_title}) - Attempting automatic bypass...", "warning")
                
                # Try automatic bypass using keyboard simulation (PerimeterX bypass technique)
                bypass_success = self._attempt_captcha_bypass()
                
                if bypass_success:
                    self.log_progress(-1, "✅ CAPTCHA bypassed automatically!", "success")
                    return True
                
                # Fall back to manual intervention
                self.log_progress(-1, "⚠️ Auto-bypass failed - Manual intervention required", "warning")
                self.log_progress(-1, "Please solve captcha via VNC: https://vnc.shravanpandala.me", "warning")
                self.log_progress(-1, "Waiting up to 5 minutes for captcha resolution...", "info")
                
                # Wait up to 5 minutes for captcha to be solved
                captcha_selectors = [
                    'text="Press & Hold"',
                    '.gkfWUyaFMteSFAk',
                    '[aria-label*="Press"]',
                    'text="Human Challenge"'
                ]
                
                for attempt in range(60):
                    if self.state.is_stop_requested():
                        raise StopRequestedException("Stop requested during captcha wait")
                    
                    safe_wait(self.page, 5000, self.state.is_stop_requested)
                    
                    # Check if captcha is gone (check title first)
                    page_title = self.page.title()
                    if "denied" not in page_title.lower() and "blocked" not in page_title.lower():
                        self.log_progress(-1, "✅ Captcha solved! Resuming automation...", "success")
                        return True
                    
                    if attempt % 6 == 0:  # Log every 30 seconds
                        remaining = (60 - attempt) * 5
                        self.log_progress(-1, f"Still waiting for captcha... ({remaining}s remaining)", "info")
                
                self.log_progress(-1, "❌ Captcha timeout - stopping automation", "error")
                return False
            
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(-1, f"Error checking captcha: {str(e)}", "warning")
            return True  # Continue on error
    
    def _attempt_captcha_bypass(self):
        """
        Attempt to automatically bypass PerimeterX 'Press & Hold' CAPTCHA
        using keyboard simulation technique.
        
        The technique: Press Tab once to focus on the button, then hold Enter key for 5 seconds.
        This mimics the 'Press & Hold' action without needing to locate/click the button.
        """
        try:
            self.log_progress(-1, "🔄 Trying keyboard bypass (Tab + Enter hold)...", "info")
            time.sleep(0.5)
            self.page.keyboard.press('Tab')
            self.log_progress(-1, "📍 Pressed Tab to focus on button", "info")
            time.sleep(0.3)

            max_hold = 15.0  # seconds
            check_interval = 0.5  # seconds
            elapsed = 0.0
            self.log_progress(-1, f"⏳ Holding Enter for up to {max_hold} seconds or until captcha is solved...", "info")
            self.page.keyboard.down('Enter')
            solved = False
            while elapsed < max_hold:
                time.sleep(check_interval)
                elapsed += check_interval
                # Check if captcha is solved (page title no longer contains denied/blocked)
                page_title = self.page.title()
                if "denied" not in page_title.lower() and "blocked" not in page_title.lower():
                    solved = True
                    break
            self.page.keyboard.up('Enter')
            if solved:
                self.log_progress(-1, f"🎉 CAPTCHA bypassed after holding for {elapsed:.1f} seconds! New title: {page_title}", "success")
                return True
            else:
                self.log_progress(-1, f"❌ Still blocked after {max_hold} seconds (title: {page_title})", "warning")
                return False
        except Exception as e:
            self.log_progress(-1, f"Error during captcha bypass: {str(e)}", "warning")
            return False
    
    def is_page_stuck(self):
        """
        Check if the page appears to be stuck/unresponsive.
        Returns True if page seems stuck, False otherwise.
        """
        try:
            # Quick check - see if we can get basic page info
            page_url = self.page.url
            page_title = self.page.title()
            
            # Check for blank/empty page
            if not page_url or page_url == "about:blank":
                self.log_progress(-1, "⚠️ Page appears blank/empty", "warning")
                return True
            
            # Check for common error indicators in title
            error_indicators = ["error", "timeout", "refused", "unavailable", "failed"]
            if any(indicator in page_title.lower() for indicator in error_indicators):
                self.log_progress(-1, f"⚠️ Page shows error state: {page_title}", "warning")
                return True
            
            # Try to evaluate simple JS to check if page is responsive
            try:
                result = self.page.evaluate("document.readyState", timeout=5000)
                if result not in ["complete", "interactive"]:
                    self.log_progress(-1, f"⚠️ Page not fully loaded: {result}", "warning")
                    return True
            except Exception:
                self.log_progress(-1, "⚠️ Page not responding to JavaScript", "warning")
                return True
            
            return False
            
        except Exception as e:
            self.log_progress(-1, f"⚠️ Error checking page state: {str(e)}", "warning")
            return True
    
    def refresh_page_if_stuck(self, context_msg=""):
        """
        Refresh the page if it appears stuck. Returns True if page was refreshed successfully.
        
        Args:
            context_msg: Context message describing what operation was happening
            
        Returns:
            True if page was refreshed and recovered, False if max retries exceeded
        """
        try:
            if self.state.page_stuck_count >= self.state.max_stuck_retries:
                self.log_progress(-1, f"❌ Max refresh retries ({self.state.max_stuck_retries}) exceeded - giving up", "error")
                return False
            
            self.state.page_stuck_count += 1
            self.log_progress(-1, f"🔄 Page stuck{' during ' + context_msg if context_msg else ''} - refreshing (attempt {self.state.page_stuck_count}/{self.state.max_stuck_retries})...", "warning")
            
            current_url = self.page.url
            
            # Try to reload the page
            try:
                self.page.reload(timeout=30000, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                # If reload times out, try navigating directly
                self.log_progress(-1, "⚠️ Reload timed out, trying direct navigation...", "warning")
                if current_url and current_url != "about:blank":
                    self.page.goto(current_url, timeout=30000, wait_until="domcontentloaded")
                else:
                    # Navigate to upload page as fallback
                    self.page.goto("https://www.dreamstime.com/upload", timeout=30000, wait_until="domcontentloaded")
            
            # Wait for page to stabilize
            safe_wait(self.page, 3000, self.state.is_stop_requested)
            
            # Verify page is responsive now
            if not self.is_page_stuck():
                self.log_progress(-1, "✅ Page refreshed successfully!", "success")
                self.state.page_stuck_count = 0  # Reset stuck counter on success
                return True
            else:
                self.log_progress(-1, "⚠️ Page still not responsive after refresh", "warning")
                return self.refresh_page_if_stuck(context_msg)  # Recursive retry
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(-1, f"❌ Error during page refresh: {str(e)}", "error")
            return False
    
    def wait_for_element_with_refresh(self, selector, timeout=10000, context_msg=""):
        """
        Wait for an element, refreshing the page if it gets stuck.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
            context_msg: Context message for logging
            
        Returns:
            True if element found, False otherwise
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            self.state.page_stuck_count = 0  # Reset on success
            return True
        except PlaywrightTimeoutError:
            self.log_progress(-1, f"⚠️ Timeout waiting for '{selector}'{' during ' + context_msg if context_msg else ''}", "warning")
            
            # Check if page is stuck and try to refresh
            if self.is_page_stuck():
                if self.refresh_page_if_stuck(context_msg):
                    # Try waiting for element again after refresh
                    try:
                        self.page.wait_for_selector(selector, timeout=timeout)
                        return True
                    except PlaywrightTimeoutError:
                        return False
            return False
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(-1, f"Error waiting for element: {str(e)}", "error")
            return False

    def save_cookies(self):
        """Save cookies to file after successful login"""
        try:
            cookies = self.context.cookies()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            self.log_progress(-1, f"✅ Saved {len(cookies)} cookies to {COOKIES_FILE}", "success")
            return True
        except Exception as e:
            self.log_progress(-1, f"Failed to save cookies: {str(e)}", "error")
            return False
    
    def load_cookies(self):
        """Load cookies from file"""
        try:
            if not os.path.exists(COOKIES_FILE):
                self.log_progress(-1, "No saved cookies found", "info")
                return False
            
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            
            if not cookies:
                self.log_progress(-1, "Cookie file is empty", "info")
                return False
            
            self.context.add_cookies(cookies)
            self.log_progress(-1, f"✅ Loaded {len(cookies)} cookies from file", "success")
            return True
        except Exception as e:
            self.log_progress(-1, f"Failed to load cookies: {str(e)}", "error")
            return False
    
    def is_logged_in(self):
        """Check if we're currently logged in by looking for logged-in indicators"""
        try:
            # Check URL first - if we're on upload/member page, we're likely logged in
            current_url = self.page.url
            if "/upload" in current_url or "/member/" in current_url:
                self.log_progress(-1, f"✅ Logged in (URL check): {current_url}", "info")
                return True
            
            # Check for login form - if present, NOT logged in
            login_form = self.page.locator("form[name='loginfrm'], input[name='username'], #loginForm")
            if login_form.count() > 0:
                self.log_progress(-1, "❌ Login form detected - not logged in", "info")
                return False
            
            # Look for any upload-related elements
            upload_elements = self.page.locator("a[href*='upload'], .upload-btn, button:has-text('Upload')")
            if upload_elements.count() > 0:
                self.log_progress(-1, "✅ Upload button found - logged in", "info")
                return True
            
            # Look for user menu or profile elements
            user_menu = self.page.locator(".h-user, .user-menu, a.h-user__link")
            if user_menu.count() > 0:
                self.log_progress(-1, "✅ User menu found - logged in", "info")
                return True
            
            self.log_progress(-1, "⚠️ Could not determine login status - assuming not logged in", "warning")
            return False
        except Exception as e:
            self.log_progress(-1, f"❌ Error checking login status: {e}", "error")
            return False
    
    def wait_for_manual_login(self, timeout_seconds=300):
        """Wait for user to manually complete login via VNC viewer"""
        try:
            self.log_progress(-1, "=" * 60, "warning")
            self.log_progress(-1, "🔐 MANUAL LOGIN REQUIRED", "warning")
            self.log_progress(-1, "=" * 60, "warning")
            self.log_progress(-1, "Please log in manually using the VNC viewer:", "warning")
            self.log_progress(-1, "1. Open: https://n8n.shravanpandala.me/vnc/vnc.html", "info")
            self.log_progress(-1, "2. Complete the login and any captcha challenges", "info")
            self.log_progress(-1, "3. Make sure you can see the upload button", "info")
            self.log_progress(-1, f"Waiting up to {timeout_seconds} seconds for login...", "info")
            self.log_progress(-1, "=" * 60, "warning")
            
            # Navigate to Dreamstime login page
            self.page.goto(Config.BASE_URL)
            self.page.wait_for_load_state('domcontentloaded')
            
            # Try clicking login button if visible
            try:
                login_btn = self.page.locator("a.h-login__btn--sign-in.js-loginform-trigger")
                if login_btn.count() > 0:
                    login_btn.click()
                    self.page.wait_for_timeout(2000)
            except:
                pass
            
            # Wait for user to complete login
            start_time = time.time()
            check_interval = 5  # Check every 5 seconds
            
            while time.time() - start_time < timeout_seconds:
                # Check if stop requested
                if self.state.is_stop_requested():
                    self.log_progress(-1, "Stop requested during manual login", "warning")
                    return False
                
                self.page.wait_for_timeout(check_interval * 1000)
                
                # Check if logged in now
                if self.is_logged_in():
                    self.log_progress(-1, "✅ Login detected! Saving cookies...", "success")
                    self.save_cookies()
                    return True
                
                elapsed = int(time.time() - start_time)
                remaining = timeout_seconds - elapsed
                self.log_progress(-1, f"⏳ Still waiting for login... ({remaining}s remaining)", "info")
            
            self.log_progress(-1, "❌ Manual login timeout - please try again", "error")
            return False
            
        except Exception as e:
            self.log_progress(-1, f"Error during manual login wait: {str(e)}", "error")
            return False

    def step1_navigate_to_dreamstime(self):
        """Step 1: Navigate to Dreamstime upload page (already logged in)"""
        try:
            self.log_progress(1, "Navigating to upload page...", "info")
            
            # First navigate to stock vector page (workaround for website glitch)
            self.log_progress(1, "Going to stock vector page first (website glitch workaround)...", "info")
            self.page.goto("https://www.dreamstime.com/stock-vector-illustrations-clipart")
            self.page.wait_for_load_state('domcontentloaded')
            self.page.wait_for_timeout(2000)
            
            # Check for CAPTCHA on vector page
            if not self.check_for_captcha():
                self.log_progress(1, "CAPTCHA could not be solved - stopping", "error")
                return False
            
            # Now navigate to the upload page
            self.log_progress(1, "Now navigating to upload page...", "info")
            try:
                self.page.goto("https://www.dreamstime.com/upload", timeout=30000)
                self.page.wait_for_load_state('domcontentloaded', timeout=15000)
            except PlaywrightTimeoutError:
                self.log_progress(1, "⚠️ Upload page load timeout - checking if stuck...", "warning")
                if self.is_page_stuck():
                    if not self.refresh_page_if_stuck("navigating to upload page"):
                        return False
            
            self.page.wait_for_timeout(3000)
            
            # Check for CAPTCHA after navigation to upload
            if not self.check_for_captcha():
                self.log_progress(1, "CAPTCHA could not be solved - stopping", "error")
                return False
            
            # Verify we're logged in
            if self.is_logged_in():
                self.log_progress(1, "✅ On upload page - ready to process images!", "success")
                return True
            else:
                self.log_progress(1, "⚠️ Not logged in - please log in via VNC first", "warning")
                return False
            
        except PlaywrightTimeoutError as e:
            self.log_progress(1, f"⚠️ Navigation timeout: {str(e)}", "warning")
            if self.is_page_stuck():
                if self.refresh_page_if_stuck("navigation timeout"):
                    return self.step1_navigate_to_dreamstime()  # Retry the step
            return False
        except Exception as e:
            self.log_progress(1, f"Navigation failed: {str(e)}", "error")
            return False
    
    def step2_click_signin(self):
        """Step 2: Skip - login is now handled via cookies in step1"""
        # With cookie-based auth, login is already done in step1
        self.log_progress(2, "Login handled via cookies - skipping sign-in step", "success")
        return True
    
    def step3_enter_username(self):
        """Step 3: Skip - login is now handled via cookies in step1"""
        # With cookie-based auth, username entry is not needed
        self.log_progress(3, "Login handled via cookies - skipping username step", "success")
        return True
    
    def step4_enter_password(self):
        """Step 4: Skip - login is now handled via cookies in step1"""
        # With cookie-based auth, password entry is not needed
        self.log_progress(4, "Login handled via cookies - skipping password step", "success")
        return True
    
    def step5_click_upload_button(self):
        """Step 5: Navigate to upload page and wait for images"""
        try:
            self.log_progress(5, "Checking upload page...", "info")
            
            # If not already on upload page, navigate there (with workaround)
            if "/upload-photos-for-sale" not in self.page.url and "/upload" not in self.page.url:
                # First go to stock vector page (website glitch workaround)
                self.log_progress(5, "Going to stock vector page first...", "info")
                self.page.goto("https://www.dreamstime.com/stock-vector-illustrations-clipart")
                self.page.wait_for_load_state('domcontentloaded')
                self.page.wait_for_timeout(2000)
                
                if not self.check_for_captcha():
                    self.log_progress(5, "CAPTCHA could not be solved - stopping", "error")
                    return False
                
                # Then navigate to upload page
                self.log_progress(5, "Navigating to upload page...", "info")
                self.page.goto("https://www.dreamstime.com/upload")
                self.page.wait_for_load_state('domcontentloaded')
                self.page.wait_for_timeout(3000)
            
            # Check for CAPTCHA after navigation
            if not self.check_for_captcha():
                self.log_progress(5, "CAPTCHA could not be solved - stopping", "error")
                return False
            
            self.log_progress(5, "On upload page, ready to process images", "success")
            return True
            
        except Exception as e:
            self.log_progress(5, f"Failed to access upload page: {str(e)}", "error")
            return False
    
    def step6_check_and_click_images(self):
        """Step 6: Process images - click first one to open edit page, then process in loop"""
        import re
        try:
            self.log_progress(6, "Looking for images to process...", "info")
            
            # Navigate to upload page first
            if "/upload" not in self.page.url or re.search(r'/upload/(edit)?\d+', self.page.url):
                self.page.goto("https://www.dreamstime.com/upload")
                self.page.wait_for_load_state('domcontentloaded')
                safe_wait(self.page, 2000, self.state.is_stop_requested)
            
            current_url = self.page.url
            self.log_progress(6, f"Current URL: {current_url}", "info")
            
            # Look for edit links with pattern /upload/editNNNN or /upload/NNNN
            edit_links = self.page.locator("a[href*='/upload/edit']").all()
            self.log_progress(6, f"Found {len(edit_links)} edit links", "info")
            
            if edit_links:
                # Click first edit link
                first_link = edit_links[0]
                href = first_link.get_attribute('href') or ''
                self.log_progress(6, f"Clicking edit link: {href}", "info")
                first_link.click()
                safe_wait(self.page, 2000, self.state.is_stop_requested)
            else:
                # Try alternative selectors - look for any links with /upload/ followed by digits
                all_links = self.page.locator("a").all()
                found_link = None
                for link in all_links:
                    try:
                        href = link.get_attribute('href') or ''
                        if re.search(r'/upload/(edit)?\d+', href):
                            found_link = link
                            self.log_progress(6, f"Found image link: {href}", "info")
                            break
                    except:
                        continue
                
                if found_link:
                    found_link.click()
                    safe_wait(self.page, 2000, self.state.is_stop_requested)
                else:
                    # Try clicking on image thumbnails that might be inside edit links
                    thumb_containers = self.page.locator(".js-readyToSubmit, .upload-item, [data-id]").all()
                    self.log_progress(6, f"Found {len(thumb_containers)} thumbnail containers", "info")
                    
                    if thumb_containers:
                        thumb_containers[0].click()
                        safe_wait(self.page, 2000, self.state.is_stop_requested)
                    else:
                        self.log_progress(6, "No images found to process - please upload images first", "warning")
                        return False
            
            # Verify we're now on an edit page
            new_url = self.page.url
            self.log_progress(6, f"Navigated to: {new_url}", "info")
            
            if not re.search(r'/upload/(edit)?\d+', new_url):
                self.log_progress(6, "Failed to navigate to image edit page", "error")
                return False
            
            # Run the processing loop
            return self.process_images_loop()
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(6, f"Failed to find images: {str(e)}", "error")
            return False
    
    def process_images_loop(self):
        """Process images in a loop on the edit page (like Chrome extension)"""
        import re
        processed = 0
        
        try:
            # Wait for the edit page to fully load - with stuck page detection
            try:
                self.page.wait_for_load_state('networkidle', timeout=15000)
            except PlaywrightTimeoutError:
                self.log_progress(6, "⚠️ Page load timeout - checking if stuck...", "warning")
                if self.is_page_stuck():
                    if not self.refresh_page_if_stuck("initial page load"):
                        self.log_progress(6, "❌ Could not recover from stuck page", "error")
                        return False
            
            safe_wait(self.page, 2000, self.state.is_stop_requested)
            
            # Check for CAPTCHA before starting loop
            if not self.check_for_captcha():
                self.log_progress(6, "CAPTCHA could not be solved - stopping", "error")
                return
            
            for i in range(self.repeat_count):
                # Track start time for this image (for 60 second timeout)
                image_start_time = time.time()
                
                if self.state.stop_requested:
                    self.log_progress(6, "Stop requested, halting processing", "warning")
                    break
                
                self.log_progress(6, f"Processing image {i + 1} of {self.repeat_count}", "info")
                
                # Check if we're on an edit page (URL contains /upload/edit followed by digits)
                current_url = self.page.url
                self.log_progress(6, f"Current URL: {current_url}", "info")
                
                # Match patterns like /upload/edit421059885 or /upload/421059885
                if not re.search(r'/upload/(edit)?\d+', current_url):
                    self.log_progress(6, "Not on edit page, navigating to find images...", "info")
                    
                    # First go to stock vector page (website glitch workaround)
                    self.page.goto("https://www.dreamstime.com/stock-vector-illustrations-clipart")
                    safe_wait(self.page, 2000, self.state.is_stop_requested)
                    
                    if not self.check_for_captcha():
                        self.log_progress(6, "CAPTCHA could not be solved - stopping", "error")
                        break
                    
                    # Then go to upload page
                    self.page.goto("https://www.dreamstime.com/upload")
                    safe_wait(self.page, 3000, self.state.is_stop_requested)
                    
                    # Check for CAPTCHA after navigation
                    if not self.check_for_captcha():
                        self.log_progress(6, "CAPTCHA could not be solved - stopping", "error")
                        break
                    
                    # Find edit page links - look for links with edit+digits
                    all_links = self.page.locator("a[href*='/upload/edit']").all()
                    self.log_progress(6, f"Found {len(all_links)} edit links", "info")
                    
                    edit_page_links = []
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            if href and re.search(r'/upload/edit\d+', href):
                                edit_page_links.append(link)
                        except:
                            continue
                    
                    if not edit_page_links:
                        self.log_progress(6, "No more images to process", "info")
                        break
                    
                    # Click first edit link
                    self.log_progress(6, f"Clicking: {edit_page_links[0].get_attribute('href')}", "info")
                    edit_page_links[0].click()
                    safe_wait(self.page, 3000, self.state.is_stop_requested)
                
                # Wait for title field to be visible (confirms page loaded) - with page refresh on stuck
                title_found = self.wait_for_element_with_refresh("#title", timeout=15000, context_msg="waiting for edit form")
                if not title_found:
                    self.log_progress(6, "Form fields not found after refresh attempts, skipping to next image", "warning")
                    # Try to navigate back and continue
                    try:
                        self.page.goto("https://www.dreamstime.com/upload", timeout=15000, wait_until="domcontentloaded")
                        safe_wait(self.page, 2000, self.state.is_stop_requested)
                    except:
                        pass
                    continue
                
                # Also check for description field
                desc_found = self.wait_for_element_with_refresh("#description", timeout=10000, context_msg="waiting for description field")
                if not desc_found:
                    self.log_progress(6, "Description field not found, skipping to next image", "warning")
                    continue
                
                # Get current image ID for duplicate detection
                try:
                    original_filename = self.page.locator("#js-originalfilename")
                    if original_filename.count() > 0:
                        current_image_id = original_filename.inner_text().strip()
                        self.log_progress(6, f"Processing image: {current_image_id}", "info")
                        
                        # Check for duplicate
                        if current_image_id and current_image_id == self.state.last_image_id:
                            self.log_progress(6, f"Duplicate image ID: {current_image_id}", "warning")
                            
                            if self.same_id_action == "stop":
                                break
                            elif self.same_id_action == "skip":
                                # Click next button
                                next_button = self.page.locator("#js-next-submit")
                                if next_button.count() > 0:
                                    next_button.click()
                                    safe_wait(self.page, 2000, self.state.is_stop_requested)
                                
                                self.state.retry_count += 1
                                if self.state.retry_count >= Config.MAX_RETRIES:
                                    self.state.retry_count = 0
                                    processed += 1
                                continue
                        
                        self.state.last_image_id = current_image_id
                        self.state.retry_count = 0
                except Exception as e:
                    self.log_progress(6, f"Could not get image ID: {str(e)}", "warning")
                
                # Check if title and description are already filled
                title_field = self.page.locator("#title")
                description_field = self.page.locator("#description")
                
                title_value = title_field.input_value() if title_field.count() > 0 else ""
                desc_value = description_field.input_value() if description_field.count() > 0 else ""
                
                # If title is empty, copy description to title (fast, no API calls)
                if not title_value.strip():
                    if desc_value.strip():
                        # Copy description to title
                        sanitized = desc_value.replace(":", ",")[:115]
                        title_value = sanitized
                        self.log_progress(6, f"Copying description to title: {title_value[:40]}...", "info")
                    else:
                        # Last-resort generic fallback when both are empty
                        title_value = f"AI Generated Image {current_image_id if 'current_image_id' in dir() else i+1}"
                        desc_value = "AI generated digital artwork, high quality image"
                        self.log_progress(6, f"Using fallback title: {title_value}", "info")
                    
                    self.page.evaluate(f"""
                        const titleField = document.querySelector('input#title');
                        const descField = document.querySelector('textarea#description');
                        
                        if (titleField) {{
                            titleField.focus();
                            titleField.value = {repr(title_value)};
                            titleField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            titleField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                        
                        if (descField && {repr(desc_value)}.length > 0) {{
                            descField.focus();
                            descField.value = {repr(desc_value)};
                            descField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            descField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    """)
                    safe_wait(self.page, 500, self.state.is_stop_requested)
                
                # Copy description to title if title is still empty but description exists
                title_value = title_field.input_value() if title_field.count() > 0 else ""
                desc_value = description_field.input_value() if description_field.count() > 0 else ""
                
                if not title_value.strip() and desc_value.strip():
                    sanitized_title = desc_value.replace(":", ",")[:115]
                    self.log_progress(6, f"Copying description to title: {sanitized_title[:40]}...", "info")
                    
                    self.page.evaluate(f"""
                        const titleField = document.querySelector('input#title');
                        if (titleField) {{
                            titleField.focus();
                            titleField.value = {repr(sanitized_title)};
                            
                            // Trigger all events
                            const inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
                            const changeEvent = new Event('change', {{ bubbles: true, cancelable: true }});
                            
                            titleField.dispatchEvent(inputEvent);
                            titleField.dispatchEvent(changeEvent);
                            
                            // Also manually trigger any attached event listeners
                            if (titleField.oninput) titleField.oninput(inputEvent);
                            if (titleField.onchange) titleField.onchange(changeEvent);
                        }}
                    """)
                    safe_wait(self.page, 500, self.state.is_stop_requested)
                
                # Add template text to description if configured
                if self.template != "none":
                    template_text = TemplateManager.get_random_text(self.template)
                    if template_text:
                        current_desc = description_field.input_value()
                        new_desc = f"{current_desc}{template_text}"
                        self.page.evaluate(f"""
                            const desc = document.querySelector('#description');
                            if (desc) {{
                                desc.value = {repr(new_desc)};
                                desc.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                desc.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            }}
                        """)
                        safe_wait(self.page, 300, self.state.is_stop_requested)
                
                # Skip category checks - they auto-populate correctly
                # Go directly to submit
                
                # Check for captcha before submitting
                if not self.check_for_captcha():
                    self.log_progress(6, "Captcha timeout - stopping automation", "error")
                    break
                
                # Click submit button
                self.log_progress(6, "Submitting image...", "info")
                submit_success = False
                try:
                    submit_btn = self.page.locator("#submitbutton")
                    if submit_btn.count() > 0:
                        submit_btn.click()
                        safe_wait(self.page, 1000, self.state.is_stop_requested)
                        submit_success = True
                    else:
                        self.log_progress(6, "Submit button not found", "error")
                except Exception as e:
                    self.log_progress(6, f"Submit failed: {str(e)}", "error")
                    submit_success = False
                
                # Check if taking too long (more than 60 seconds for this image)
                elapsed_time = time.time() - image_start_time
                if elapsed_time > 60:
                    self.log_progress(6, f"⏱️ Image took {elapsed_time:.0f}s - deleting to skip...", "warning")
                    try:
                        # Click delete button
                        delete_btn = self.page.locator("a#js-delete-submit, #js-delete-submit")
                        if delete_btn.count() > 0:
                            delete_btn.click()
                            safe_wait(self.page, 500, self.state.is_stop_requested)
                            
                            # Click confirm button in the popup
                            confirm_btn = self.page.locator("button.js-confirm, .js-confirm")
                            if confirm_btn.count() > 0:
                                confirm_btn.click()
                                safe_wait(self.page, 1000, self.state.is_stop_requested)
                            
                            self.log_progress(6, "🗑️ Image deleted, moving to next...", "info")
                    except Exception as del_err:
                        self.log_progress(6, f"Delete failed: {str(del_err)}", "warning")
                        if self.refresh_page_if_stuck("delete failed"):
                            continue
                    continue
                
                if not submit_success:
                    continue
                
                # Check for captcha after submission
                if not self.check_for_captcha():
                    self.log_progress(6, "Captcha timeout - stopping automation", "error")
                    break
                
                processed += 1
                self.state.processed_count = processed
                self.state.successful_count = processed
                
                progress_pct = int((processed / self.repeat_count) * 100)
                self.log_progress(6, f"✅ Submitted! Progress: {progress_pct}% ({processed}/{self.repeat_count})", "success")
                
                # Apply delay between images (minimal)
                if processed < self.repeat_count:
                    delay_seconds = DelayCalculator.calculate(self.delay)
                    self.log_progress(6, f"Waiting {delay_seconds}s before next image...", "info")
                    safe_wait(self.page, delay_seconds * 1000, self.state.is_stop_requested)
                
                # Check for pause
                if self.pause_after > 0 and processed % self.pause_after == 0 and processed < self.repeat_count:
                    self.log_progress(6, f"Pausing for {self.pause_duration}s...", "info")
                    safe_wait(self.page, self.pause_duration * 1000, self.state.is_stop_requested)
            
            self.log_progress(6, f"Completed processing {processed} image(s)", "success")
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(6, f"Processing loop error: {str(e)}", "error")
            return False
    
    def step7_copy_description_to_title(self):
        """Step 7: Copy description and paste into title, with enhancements"""
        try:
            self.log_progress(7, "Processing title and description...", "info")
            
            # Get current title and description
            title_field = self.page.locator("input#title")
            description_field = self.page.locator("textarea#description")
            
            title_text = title_field.input_value()
            description_text = description_field.input_value()
            
            # If title is empty, copy description to title (fast, no API calls)
            if not title_text.strip():
                if description_text.strip():
                    # Copy description to title
                    title_text = description_text
                    self.log_progress(7, "Copying description to title field", "info")
                else:
                    # Both empty - use generic fallback
                    self.log_progress(7, "Both title and description empty - using fallback", "warning")
                    title_text = "AI Generated Image"
                    description_text = "AI generated digital artwork, high quality image"
                    description_field.fill(description_text)
                    description_field.dispatch_event("input")
            # Copy description to title if title is empty (since description filling works)
            if not title_text or not title_text.strip():
                # Get the description value that was successfully filled
                current_desc = self.page.evaluate("document.querySelector('textarea#description')?.value || ''")
                if current_desc:
                    title_text = current_desc
                    self.log_progress(7, "Copied description to title field", "info")
            
            # Sanitize title (remove colons, limit to 115 chars)
            if title_text:
                sanitized_title = sanitize_title(title_text)
                
                # Use the same approach that works for description
                self.page.evaluate(f"""
                    const descField = document.querySelector('textarea#description');
                    const titleField = document.querySelector('input#title');
                    
                    if (titleField && descField) {{
                        // Set title to sanitized description
                        titleField.value = {repr(sanitized_title)};
                        
                        // Trigger the same events that work for description
                        const inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
                        const changeEvent = new Event('change', {{ bubbles: true, cancelable: true }});
                        
                        titleField.dispatchEvent(inputEvent);
                        titleField.dispatchEvent(changeEvent);
                        
                        // Also manually trigger any attached event listeners
                        if (titleField.oninput) titleField.oninput(inputEvent);
                        if (titleField.onchange) titleField.onchange(changeEvent);
                    }}
                """)
                safe_wait(self.page, 1500, self.state.is_stop_requested)
                self.log_progress(7, f"Title set: {sanitized_title[:50]}...", "info")
            
            # Enhance description with manual text if provided
            if self.manual_description and self.manual_description.strip():
                current_desc = description_field.input_value()
                enhanced_desc = f"{current_desc} {self.manual_description}" if current_desc else self.manual_description
                description_field.fill(enhanced_desc)
                description_field.dispatch_event("input")
                safe_wait(self.page, 1000, self.state.is_stop_requested)
                self.log_progress(7, "Added manual description", "info")
            
            # Add template text if selected
            if self.template != "none":
                template_text = TemplateManager.get_random_text(self.template)
                if template_text:
                    current_desc = description_field.input_value()
                    enhanced_desc = f"{current_desc}{template_text}" if current_desc else template_text
                    description_field.fill(enhanced_desc)
                    description_field.dispatch_event("input")
                    safe_wait(self.page, 1000, self.state.is_stop_requested)
                    self.log_progress(7, f"Added template: {template_text}", "info")
            
            self.log_progress(7, "Title and description processed", "success")
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(7, f"Failed to process title/description: {str(e)}", "error")
            return False
    
    def process_ai_image(self):
        """Process AI image categorization (sets category and subcategory)"""
        try:
            if self.ai_image != "yes":
                return True
            
            self.log_progress(7, "Processing AI image categorization...", "info")
            
            # Remove existing category if present
            try:
                remove_button = self.page.locator("#js-remove-cat3 > i")
                if remove_button.count() > 0 and remove_button.is_visible():
                    remove_button.click()
                    safe_wait(self.page, 1500, self.state.is_stop_requested)
                    self.log_progress(7, "Removed existing category", "info")
            except:
                pass
            
            # Set category to 172 (AI Generated)
            category_dropdown = self.page.locator("#M_Category_3")
            if category_dropdown.count() > 0:
                category_dropdown.select_option("172")
                category_dropdown.dispatch_event("change")
                safe_wait(self.page, 1500, self.state.is_stop_requested)
                self.log_progress(7, "Set AI category", "info")
            
            # Set subcategory to 212
            subcategory_dropdown = self.page.locator("#M_Subcategory_3")
            if subcategory_dropdown.count() > 0:
                subcategory_dropdown.select_option("212")
                subcategory_dropdown.dispatch_event("change")
                safe_wait(self.page, 1000, self.state.is_stop_requested)
                self.log_progress(7, "Set AI subcategory", "info")
            
            self.log_progress(7, "AI categorization complete", "success")
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(7, f"Failed to process AI categorization: {str(e)}", "error")
            return False
    
    def process_model_release(self):
        """Process model release selection"""
        try:
            if self.model_release != "yes":
                return True
            
            self.log_progress(7, "Adding model release...", "info")
            
            # Click model release button
            mr_button = self.page.locator("#js-mr-href")
            if mr_button.count() > 0:
                mr_button.click()
                safe_wait(self.page, 1000, self.state.is_stop_requested)
                
                # Select first model release option
                first_option = self.page.locator("#js-mr-list > div.popup-release__list > div > div > div > label")
                if first_option.count() > 0:
                    first_option.first.click()
                    safe_wait(self.page, 1000, self.state.is_stop_requested)
                    self.log_progress(7, "Model release added", "success")
                    return True
            
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(7, f"Failed to add model release: {str(e)}", "error")
            return False
    
    def process_exclusive_image(self):
        """Process exclusive image checkbox"""
        try:
            if self.exclusive_image != "yes":
                return True
            
            self.log_progress(7, "Marking as exclusive...", "info")
            
            # Click exclusive checkbox
            exclusive_checkbox = self.page.locator("#js-exclusively > div > label")
            if exclusive_checkbox.count() > 0:
                exclusive_checkbox.click()
                safe_wait(self.page, 1000, self.state.is_stop_requested)
                
                # Click confirm button if it appears
                confirm_button = self.page.locator("button.btn.button.green.js-confirm")
                if confirm_button.count() > 0 and confirm_button.is_visible():
                    confirm_button.click()
                    safe_wait(self.page, 1000, self.state.is_stop_requested)
                
                self.log_progress(7, "Marked as exclusive", "success")
            
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(7, f"Failed to mark as exclusive: {str(e)}", "error")
            return False
    
    def step8_submit_image(self):
        """Step 8: Click submit commercial button"""
        try:
            self.log_progress(8, "Submitting image...", "info")
            
            # Click submit
            submit_button = self.page.locator("a#submitbutton")
            if submit_button.count() > 0:
                submit_button.click()
                safe_wait(self.page, 1500, self.state.is_stop_requested)
                
                self.log_progress(8, "Image submitted successfully", "success")
                self.state.successful_count += 1
                return True
            else:
                self.log_progress(8, "Submit button not found", "error")
                return False
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(8, f"Failed to submit image: {str(e)}", "error")
            return False
    
    def run(self):
        """Run the complete automation workflow"""
        try:
            Config.validate_credentials()
            
            # Reset state for new run
            self.state.reset()
            self.state.is_running = True
            
            if not self.setup_browser():
                return False
            
            # Execute login and navigation steps
            steps = [
                self.step1_navigate_to_dreamstime,
                self.step2_click_signin,
                self.step3_enter_username,
                self.step4_enter_password,
                self.step5_click_upload_button,
                self.step6_check_and_click_images,
            ]
            
            for step_func in steps:
                # Check for stop request before each step
                if self.state.stop_requested:
                    self.log_progress(-1, "Automation stopped by user", "warning")
                    return False
                
                try:
                    if not step_func():
                        self.log_progress(-1, f"Automation stopped at {step_func.__name__}", "error")
                        return False
                except StopRequestedException:
                    self.log_progress(-1, "Automation stopped by user during execution", "warning")
                    return False
            
            # Log final summary
            self.log_progress(
                -1, 
                f"Automation completed! Processed: {self.state.processed_count}, Successful: {self.state.successful_count}", 
                "success"
            )
            return True
            
        except StopRequestedException:
            self.log_progress(-1, "Automation stopped by user", "warning")
            return False
        except Exception as e:
            self.log_progress(-1, f"Automation failed: {str(e)}", "error")
            return False
            
        finally:
            self.state.is_running = False
            # Don't wait or close - leave the browser exactly as-is
            # The page will stay on whatever URL it's currently on
            self.close()
    
    def stop(self):
        """Request automation to stop"""
        self.state.stop_requested = True
        self.log_progress(-1, "Stop requested, automation will halt soon...", "warning")
    
    def close(self):
        """Disconnect from browser - but keep Chrome session completely intact"""
        # IMPORTANT: Do NOT close browser or context when using remote debugging
        # The user's logged-in Chrome session and current page state must stay exactly as-is
        
        # Only disconnect playwright, don't close anything
        if self.playwright:
            try:
                # Disconnect gracefully without closing the browser
                self.playwright.stop()
            except:
                pass
        
        # Clear references but browser stays open with same page
        self.browser = None
        self.context = None
        self.page = None
        
        self.log_progress(-1, "✅ Disconnected from Chrome - browser and page remain open unchanged", "success")


if __name__ == "__main__":
    # For testing the automation independently
    bot = DreamstimeBot()
    bot.run()
