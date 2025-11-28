# Bypassing Dreamstime Bot Detection

## Problem

When using Playwright automation, Dreamstime shows a "Press & Hold to confirm you are a human" page. This doesn't appear when logging in with a regular browser because automation tools are detected.

## Solution: Stealth Mode

The bot now includes comprehensive anti-detection measures:

### 1. Browser Arguments
```python
args=[
    '--disable-blink-features=AutomationControlled',  # Hide automation flag
    '--user-agent=Mozilla/5.0 ...',  # Real Chrome user agent
]
```

### 2. Context Settings
- Realistic viewport (1920x1080)
- Real user agent string
- Timezone and locale set to US
- Color scheme and JavaScript enabled

### 3. JavaScript Injection
Removes bot detection signals:
- `navigator.webdriver = undefined`
- Mock plugins array
- Mock languages
- Add Chrome runtime object
- Fix permissions API

### 4. Mouse Simulation
- Initial mouse movement to mimic real user

## Additional Tips

### Use Persistent Browser Context (Best Solution)

Instead of launching a fresh browser each time, use a persistent context with saved cookies:

```python
# In automation.py, modify browser launch:
self.context = p.chromium.launch_persistent_context(
    user_data_dir='./browser-data',  # Saves cookies/session
    headless=False,
    args=[
        '--disable-blink-features=AutomationControlled',
    ]
)
self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
```

**Benefits:**
- First run: Complete verification manually
- Subsequent runs: No verification needed (cookies saved)
- Appears as same browser session

### Manual First Login

1. Run bot once
2. Complete "Press & Hold" manually in the visible browser
3. Complete login manually
4. Next runs will use saved session

### Slow Down Actions

Add longer delays between actions to seem more human:

```python
# In config.py
DEFAULT_DELAY = "slow"  # Use slow mode
```

### Alternative: Use Firefox

Firefox is sometimes less detected:

```python
# Change in automation.py
self.browser = p.firefox.launch(headless=False)
```

## Current Implementation

The bot now includes all basic stealth techniques. If you still see the verification:

1. **Complete it manually once** - The browser stays open in non-headless mode
2. **Consider persistent context** - Add to code if needed frequently
3. **Use longer delays** - Set delay to "slow" in options

## Testing

After the stealth updates, the bot should:
- ✅ Appear as regular Chrome browser
- ✅ Pass most automated detection
- ⚠️ May still need manual verification first time
- ✅ Should work smoothly after first verification

## If Still Detected

Some sites have very strict detection. Solutions:

1. **Use real browser profile:**
   ```python
   user_data_dir='C:/Users/YourName/AppData/Local/Google/Chrome/User Data'
   ```

2. **Add delays before each action:**
   ```python
   await safe_wait(page, random.randint(500, 1500))
   ```

3. **Use undetected-playwright** (external library)
   ```bash
   pip install undetected-playwright
   ```

## Current Status

✅ Basic stealth implemented
✅ Should work for most cases
⚠️ May need manual verification first time
📝 Persistent context can be added if needed

---

Just restart the bot to use the new stealth features!
