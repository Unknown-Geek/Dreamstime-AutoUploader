# Handling Dreamstime Security Pages

## Issue: securelogin.php Page

After logging in, Dreamstime may show a security verification page at:
`https://www.dreamstime.com/securelogin.php`

### What It Is
- Security checkpoint by Dreamstime
- Requires user interaction to verify account
- May include captcha or other verification

### How the Bot Handles It

**Automatic Detection:**
The bot now detects when it lands on the securelogin page after login.

**User Notification:**
You'll see progress messages:
```
⚠️  Security verification page detected - please complete manually
ℹ️  Waiting for you to complete verification (up to 60 seconds)...
```

**What to Do:**
1. **Look at the browser window** (non-headless mode)
2. **Complete the verification** (solve captcha, confirm identity, etc.)
3. **The bot will automatically continue** once you're past the verification page

**Automatic Continuation:**
- Bot waits up to 60 seconds for verification
- Automatically proceeds when URL changes from securelogin
- Continues with normal workflow (navigate to upload page)

### Tips

**For Frequent Verifications:**
1. Use the same computer/browser each time
2. Log in manually first to establish browser fingerprint
3. Clear cookies less frequently

**If Stuck:**
- Check browser window for verification prompts
- Complete any captchas or security checks
- Bot will resume automatically

**Timeout Handling:**
- If 60 seconds isn't enough, the bot will log a warning
- Manual intervention may be needed
- You can increase timeout in code if necessary

### Code Location

File: `automation.py`
Method: `step4_enter_password()`
Lines: ~194-211

```python
# Check if we landed on securelogin page
if "securelogin" in self.page.url:
    self.log_progress(4, "Security verification detected", "warning")
    # Wait for user to complete (60 seconds)
    self.page.wait_for_url(lambda url: "securelogin" not in url, timeout=60000)
```

### Customization

**Increase Wait Time:**
Change `timeout=60000` (60 seconds) to longer:
```python
timeout=120000  # 2 minutes
timeout=300000  # 5 minutes
```

**Add Auto-Skip Logic:**
If you find patterns in the verification page, you could add specific handling:
```python
# Example: Click a specific button
if self.page.locator("button.verify-btn").count() > 0:
    self.page.click("button.verify-btn")
```

---

## Other Common Security Pages

### Bot Protection ("Press & Hold")
**Handled by:** `handle_bot_protection()` method
**Auto-handled:** Yes, bot attempts to solve automatically

### Captcha Pages
**Handled by:** Manual intervention required
**Process:** Bot waits, you solve, bot continues

### Email Verification
**Handled by:** Must be done outside automation
**Solution:** Verify email before running bot

---

## Preventing Security Checks

1. **Use consistent login credentials**
2. **Run from the same IP address**
3. **Don't clear browser data between runs**
4. **Add delays between login attempts**
5. **Consider using persistent browser context** (advanced)

---

This page handling ensures the bot can work through Dreamstime's security measures without failing the automation.
