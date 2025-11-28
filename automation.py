import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import Config
from utils import (
    TemplateManager, 
    DelayCalculator, 
    sanitize_title, 
    safe_wait, 
    StopRequestedException
)
from gemini_analyzer import GeminiImageAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutomationState:
    """Tracks automation state across processing"""
    
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.retry_count = 0
        self.last_image_id = ""
        self.processed_count = 0
        self.successful_count = 0
    
    def reset(self):
        """Reset state for new automation run"""
        self.is_running = False
        self.stop_requested = False
        self.retry_count = 0
        self.last_image_id = ""
        self.processed_count = 0
        self.successful_count = 0
    
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
        
        # Initialize Gemini AI analyzer
        try:
            self.gemini_analyzer = GeminiImageAnalyzer()
            if self.gemini_analyzer.enabled:
                logger.info("Gemini AI analyzer initialized successfully")
            else:
                logger.warning("Gemini AI analyzer not available - API key not configured")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini analyzer: {str(e)}")
            self.gemini_analyzer = None
        
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
        """Initialize Playwright browser with stealth settings"""
        try:
            self.log_progress(0, "Setting up Chromium browser with stealth mode...", "info")
            
            self.playwright = sync_playwright().start()
            
            # Launch browser with anti-detection arguments
            self.browser = self.playwright.chromium.launch(
                headless=Config.HEADLESS,
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            # Create context with stealth settings
            self.context = self.browser.new_context(
                viewport=None,  # Disable viewport to allow maximization
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Inject JavaScript to remove webdriver property and other bot signals
            self.context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Add Chrome runtime
                window.chrome = { runtime: {} };
            """)
            
            self.page = self.context.new_page()
            self.page.set_default_timeout(Config.TIMEOUT)
            
            self.log_progress(0, "Browser setup complete", "success")
            return True
            
        except Exception as e:
            self.log_progress(0, f"Failed to setup browser: {str(e)}", "error")
            return False
    
    def handle_bot_protection(self):
        """Check for and handle bot protection/security challenges"""
        try:
            # Check for common challenge frames or elements
            # This is a generic check, might need specific selectors based on the screenshot
            # The screenshot shows "Press & Hold to confirm you are a human"
            
            # Look for iframes that might contain the challenge
            frames = self.page.frames
            for frame in frames:
                try:
                    # Look for the button text
                    button = frame.get_by_text("Press & Hold", exact=False)
                    if button.count() > 0 and button.is_visible():
                        self.log_progress(1, "Bot protection detected. Attempting to solve...", "warning")
                        
                        # Move mouse to button and press down
                        box = button.bounding_box()
                        if box:
                            self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            self.page.mouse.down()
                            # Hold for a few seconds
                            self.page.wait_for_timeout(5000)
                            self.page.mouse.up()
                            
                        self.page.wait_for_timeout(3000)
                        return True
                except:
                    continue
            
            # Also check main page just in case
            button = self.page.get_by_text("Press & Hold", exact=False)
            if button.count() > 0 and button.is_visible():
                self.log_progress(1, "Bot protection detected. Attempting to solve...", "warning")
                box = button.bounding_box()
                if box:
                    self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    self.page.mouse.down()
                    self.page.wait_for_timeout(5000)
                    self.page.mouse.up()
                self.page.wait_for_timeout(3000)
                return True
                
            return False
        except Exception as e:
            # Don't fail if detection fails, just proceed
            return False

    def step1_navigate_to_dreamstime(self):
        """Step 1: Navigate to https://www.dreamstime.com"""
        try:
            self.log_progress(1, "Navigating to Dreamstime...", "info")
            self.page.goto(Config.BASE_URL)
            self.page.wait_for_load_state('networkidle')
            
            # Check for bot protection
            self.handle_bot_protection()
            
            self.log_progress(1, "Successfully navigated to Dreamstime", "success")
            return True
        except Exception as e:
            self.log_progress(1, f"Navigation failed: {str(e)}", "error")
            return False
    
    def step2_click_signin(self):
        """Step 2: Click the sign-in button"""
        try:
            self.log_progress(2, "Looking for sign-in button...", "info")
            
            # Check if we are already on the login page (redirected by bot protection)
            if "login" in self.page.url or "securelogin" in self.page.url:
                self.log_progress(2, "Already on login page", "info")
                return True

            # Click the sign-in button
            try:
                self.page.click("a.h-login__btn--sign-in.js-loginform-trigger", timeout=5000)
            except:
                # If button not found, maybe we need to handle bot protection again
                self.handle_bot_protection()
                # Try finding it again or check if we are on login page
                if "login" in self.page.url:
                    return True
                self.page.click("a.h-login__btn--sign-in.js-loginform-trigger")
                
            self.page.wait_for_timeout(2000)
            
            self.log_progress(2, "Clicked sign-in button", "success")
            return True
            
        except Exception as e:
            self.log_progress(2, f"Failed to click sign-in: {str(e)}", "error")
            return False
    
    def step3_enter_username(self):
        """Step 3: Enter username"""
        try:
            self.log_progress(3, "Entering username...", "info")
            
            # Handle potential bot protection on login page
            self.handle_bot_protection()
            
            # Wait for username field with a longer timeout to allow manual intervention
            try:
                self.page.wait_for_selector("input.js-login-uname[name='uname']", timeout=10000)
            except PlaywrightTimeoutError:
                self.log_progress(3, "Waiting for user to solve captcha...", "warning")
                # Wait longer if element not found immediately (giving user time to solve captcha)
                self.page.wait_for_selector("input.js-login-uname[name='uname']", timeout=60000)
            
            # Fill username with delay to mimic human typing
            # Clear field first
            self.page.fill("input.js-login-uname[name='uname']", "")
            # Type slowly (100ms delay between keystrokes)
            self.page.type("input.js-login-uname[name='uname']", Config.DREAMSTIME_USERNAME, delay=100)
            
            self.log_progress(3, "Username entered", "success")
            return True
            
        except Exception as e:
            self.log_progress(3, f"Failed to enter username: {str(e)}", "error")
            return False
    
    def step4_enter_password(self):
        """Step 4: Enter password"""
        try:
            self.log_progress(4, "Entering password...", "info")
            
            # Fill password with delay
            # Clear field first
            self.page.fill("input.js-login-pass[name='pass']", "")
            # Type slowly (100ms delay between keystrokes)
            self.page.type("input.js-login-pass[name='pass']", Config.DREAMSTIME_PASSWORD, delay=100)
            self.page.wait_for_timeout(1000)
            
            # Click submit
            self.page.click("button[type='submit'], input[type='submit']")
            
            # Wait for navigation or login completion
            self.page.wait_for_timeout(5000)
            
            # Check for bot protection (Press & Hold button) after login
            self.log_progress(4, "Checking for bot protection challenge...", "info")
            self.handle_bot_protection()
            self.page.wait_for_timeout(2000)
            
            # Check if we landed on securelogin page
            if "securelogin" in self.page.url:
                self.log_progress(4, "Security verification page detected - please complete manually", "warning")
                self.log_progress(4, "Waiting for you to complete verification (up to 60 seconds)...", "info")
                
                # Wait for user to complete verification or timeout
                try:
                    # Wait until URL changes from securelogin (user completes verification)
                    self.page.wait_for_url(lambda url: "securelogin" not in url, timeout=60000)
                    self.log_progress(4, "Verification completed, continuing...", "success")
                except:
                    self.log_progress(4, "Still on verification page - you may need more time", "warning")
            
            self.log_progress(4, "Password entered and login submitted", "success")
            return True
            
        except Exception as e:
            self.log_progress(4, f"Failed to enter password: {str(e)}", "error")
            return False
    
    def step5_click_upload_button(self):
        """Step 5: Click on upload a file button"""
        try:
            self.log_progress(5, "Looking for upload button...", "info")
            
            # Click upload button
            self.page.click("a.upload-btn.upload-btn--big.upload-btn--green")
            self.page.wait_for_timeout(3000)
            
            self.log_progress(5, "Clicked upload button", "success")
            return True
            
        except Exception as e:
            self.log_progress(5, f"Failed to click upload button: {str(e)}", "error")
            return False
    
    def step6_check_and_click_images(self):
        """Step 6: Check for images and process them with advanced features"""
        try:
            self.log_progress(6, "Checking for uploaded images...", "info")
            
            # Wait for uploads section
            safe_wait(self.page, 3000, self.state.is_stop_requested)
            
            # Check upload count
            count_element = self.page.locator("a#js-upload span")
            if count_element.count() > 0:
                image_count = count_element.inner_text().strip()
                self.log_progress(6, f"Found {image_count} image(s) uploaded", "info")
            
            # Find all image items
            image_items = self.page.locator("div.js-readyToSubmit").all()
            
            if not image_items:
                self.log_progress(6, "No images found to process", "warning")
                return False
            
            total_to_process = min(len(image_items), self.repeat_count)
            self.log_progress(6, f"Will process {total_to_process} image(s)...", "info")
            
            # Process each image up to repeat_count
            processed = 0
            while processed < total_to_process and not self.state.stop_requested:
                try:
                    # Check for stop request
                    if self.state.stop_requested:
                        self.log_progress(6, "Stop requested, halting processing", "warning")
                        break
                    
                    # Re-query to avoid stale elements
                    current_items = self.page.locator("div.js-readyToSubmit").all()
                    if len(current_items) == 0:
                        self.log_progress(6, "No more images to process", "info")
                        break
                    
                    # Always process the first item (as items shift after submission)
                    image_item = current_items[0]
                    
                    self.log_progress(6, f"Processing image {processed + 1} of {total_to_process}", "info")
                    
                    # Click edit link
                    image_item.locator("a.js-upload-edit").click()
                    safe_wait(self.page, 3000, self.state.is_stop_requested)
                    
                    self.log_progress(6, f"Opened editor for image {processed + 1}", "success")
                    
                    # Get current image ID for duplicate detection
                    try:
                        original_filename = self.page.locator("#js-originalfilename")
                        if original_filename.count() > 0:
                            current_image_id = original_filename.inner_text().strip()
                            
                            # Check for duplicate
                            if current_image_id and current_image_id == self.state.last_image_id:
                                self.log_progress(6, f"Duplicate image ID detected: {current_image_id}", "warning")
                                
                                if self.same_id_action == "stop":
                                    self.log_progress(6, "Stopping due to duplicate image ID", "info")
                                    break
                                elif self.same_id_action == "skip":
                                    self.log_progress(6, "Skipping duplicate image", "info")
                                    # Click next button to move to next image
                                    next_button = self.page.locator("#js-next-submit")
                                    if next_button.count() > 0:
                                        next_button.click()
                                        safe_wait(self.page, 2000, self.state.is_stop_requested)
                                    
                                    self.state.retry_count += 1
                                    if self.state.retry_count >= Config.MAX_RETRIES:
                                        self.log_progress(6, "Max retries reached", "warning")
                                        self.state.retry_count = 0
                                        processed += 1
                                    continue
                            
                            # Update last image ID
                            self.state.last_image_id = current_image_id
                            self.state.retry_count = 0  # Reset retry count on new image
                    except:
                        pass
                    
                    # Process title and description (step 7)
                    result = self.step7_copy_description_to_title()
                    if result in ("stop", "skip"):
                        if result == "stop":
                            self.log_progress(6, "Stopping due to empty fields", "info")
                            break
                        else:  # skip
                            # Move to next image
                            next_button = self.page.locator("#js-next-submit")
                            if next_button.count() > 0:
                                next_button.click()
                                safe_wait(self.page, 2000, self.state.is_stop_requested)
                            continue
                    elif not result:
                        # Failed to process, try next image
                        continue
                    
                    # Process AI image categorization if enabled
                    if not self.process_ai_image():
                        self.log_progress(6, "AI categorization failed, continuing...", "warning")
                    
                    # Process model release if enabled
                    if not self.process_model_release():
                        self.log_progress(6, "Model release processing failed, continuing...", "warning")
                    
                    # Process exclusive image if enabled
                    if not self.process_exclusive_image():
                        self.log_progress(6, "Exclusive image processing failed, continuing...", "warning")
                    
                    # Submit the image (step 8)
                    if not self.step8_submit_image():
                        self.log_progress(6, "Failed to submit image", "error")
                        continue
                    
                    # Increment processed count
                    processed += 1
                    self.state.processed_count = processed
                    
                    # Calculate progress percentage
                    progress_pct = int((processed / total_to_process) * 100)
                    self.log_progress(6, f"Progress: {progress_pct}% ({processed}/{total_to_process})", "info")
                    
                    # Apply delay between images
                    if processed < total_to_process:
                        delay_seconds = DelayCalculator.calculate(self.delay)
                        self.log_progress(6, f"Waiting {delay_seconds} seconds before next image...", "info")
                        safe_wait(self.page, delay_seconds * 1000, self.state.is_stop_requested)
                    
                    # Check if we need to pause
                    if self.pause_after > 0 and processed % self.pause_after == 0 and processed < total_to_process:
                        self.log_progress(6, f"Pausing for {self.pause_duration} seconds...", "info")
                        safe_wait(self.page, self.pause_duration * 1000, self.state.is_stop_requested)
                    
                    # Navigate back to upload page if there are more images
                    if processed < total_to_process:
                        safe_wait(self.page, 2000, self.state.is_stop_requested)
                        self.page.goto(Config.UPLOAD_URL)
                        safe_wait(self.page, 3000, self.state.is_stop_requested)
                    
                except StopRequestedException:
                    raise
                except Exception as e:
                    self.log_progress(6, f"Error processing image {processed + 1}: {str(e)}", "error")
                    # Try to recover by going back to upload page
                    try:
                        self.page.goto(Config.UPLOAD_URL)
                        safe_wait(self.page, 3000, self.state.is_stop_requested)
                    except:
                        pass
                    continue
            
            self.log_progress(6, f"Completed processing {processed} image(s)", "success")
            return True
            
        except StopRequestedException:
            raise
        except Exception as e:
            self.log_progress(6, f"Failed to process images: {str(e)}", "error")
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
            
            # Skip if both are empty - use Gemini AI analysis
            if not title_text.strip() and not description_text.strip():
                self.log_progress(7, "Both title and description are empty - using Gemini AI...", "info")
                
                # Try to use Gemini AI to analyze the image and generate content
                if self.gemini_analyzer and self.gemini_analyzer.enabled:
                    try:
                        # Screenshot the visible image thumbnail to analyze
                        image_container = self.page.locator(".upload-item.submit").first
                        if image_container.count() > 0:
                            # Take screenshot of the image area
                            screenshot_bytes = image_container.screenshot()
                            
                            # Save temporarily
                            import tempfile
                            import os
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                                tmp_file.write(screenshot_bytes)
                                tmp_path = tmp_file.name
                            
                            try:
                                # Use Gemini to analyze
                                self.log_progress(7, "Analyzing image with Gemini AI...", "info")
                                ai_result = self.gemini_analyzer.analyze_image(tmp_path)
                                
                                if ai_result:
                                    # Fill in generated title and description using JavaScript
                                    self.page.evaluate(f"""
                                        const titleField = document.querySelector('input#title');
                                        const descField = document.querySelector('textarea#description');
                                        
                                        if (titleField) {{
                                            titleField.focus();
                                            titleField.value = {repr(ai_result['title'])};
                                            titleField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                            titleField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                        }}
                                        
                                        if (descField) {{
                                            descField.focus();
                                            descField.value = {repr(ai_result['description'])};
                                            descField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                            descField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                        }}
                                    """)
                                    safe_wait(self.page, 1000, self.state.is_stop_requested)
                                    
                                    self.log_progress(7, f"AI generated: {ai_result['title'][:40]}...", "success")
                                    title_text = ai_result['title']
                                    description_text = ai_result['description']
                                else:
                                    self.log_progress(7, "Gemini analysis failed - skipping image", "warning")
                                    if self.same_id_action == "stop":
                                        return "stop"
                                    return "skip"
                            finally:
                                # Clean up temp file
                                try:
                                    os.unlink(tmp_path)
                                except:
                                    pass
                    except Exception as e:
                        self.log_progress(7, f"Gemini AI error: {str(e)} - skipping image", "warning")
                        if self.same_id_action == "stop":
                            return "stop"
                        return "skip"
                else:
                    self.log_progress(7, "Gemini AI not available - skipping empty image", "warning")
                    if self.same_id_action == "stop":
                        return "stop"
                    return "skip"
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
                safe_wait(self.page, 4500, self.state.is_stop_requested)
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
                safe_wait(self.page, 3000, self.state.is_stop_requested)
                
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
            # Keep browser open for 10 seconds to view results
            if self.page:
                try:
                    self.page.wait_for_timeout(10000)
                except:
                    pass
            self.close()
    
    def stop(self):
        """Request automation to stop"""
        self.state.stop_requested = True
        self.log_progress(-1, "Stop requested, automation will halt soon...", "warning")
    
    def close(self):
        """Close the browser"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


if __name__ == "__main__":
    # For testing the automation independently
    bot = DreamstimeBot()
    bot.run()
