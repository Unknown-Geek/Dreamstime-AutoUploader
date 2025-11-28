# Quick Test - API Integration

## Test the API without n8n first

### 1. Start the Flask App

```bash
python app.py
```

### 2. Test with cURL (No API Key)

**Start automation:**
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -d "{\"repeatCount\": 3, \"delay\": \"fast\"}"
```

**Check status:**
```bash
curl http://localhost:5000/api/status
```

**Expected response:**
```json
{
  "running": true,
  "status": "running",
  "progress": [...]
}
```

### 3. Test with API Key (Optional)

**a) Update .env:**
```env
REQUIRE_API_KEY=True
API_KEY=test-key-12345
```

**b) Restart Flask app**

**c) Test with API key:**
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d "{\"repeatCount\": 2}"
```

**Test without API key (should fail):**
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -d "{\"repeatCount\": 2}"
```

**Expected error:**
```json
{
  "success": false,
  "error": "API key required",
  "message": "Please provide API key in X-API-Key header or api_key parameter"
}
```

---

## n8n Setup (After Basic Testing)

### Step 1: Create HTTP Request Node in n8n

1. **Add Node** → **HTTP Request**
2. **Method:** POST
3. **URL:** `http://localhost:5000/api/start`
4. **Authentication:** (if API key enabled)
   - Type: Header Auth
   - Name: `X-API-Key`
   - Value: `your-api-key`
5. **Body:**
   - Content Type: JSON
   - Add Parameters:
     ```json
     {
       "template": "template1",
       "aiImage": "yes",
       "repeatCount": 5,
       "delay": "fast"
     }
     ```

### Step 2: Test the Node

Click **Execute Node** in n8n

**Success response:**
```json
{
  "success": true,
  "message": "Automation started successfully",
  "options": {
    "template": "template1",
    "aiImage": "yes",
    "repeatCount": 5,
    "delay": "fast"
  }
}
```

---

## Common Scenarios

### Scenario 1: Trigger on File Upload

**n8n Workflow:**
1. **Webhook** → Receives upload notification
2. **HTTP Request** → `/api/start` with upload count
3. **Wait** → Poll status every 10s
4. **Send Email** → Notify on completion

### Scenario 2: Daily Scheduled Processing

**n8n Workflow:**
1. **Cron Trigger** → 2 AM daily
2. **HTTP Request** → `/api/start` with batch settings
3. **Loop** → Check status until complete
4. **Slack Notification** → Send summary

### Scenario 3: Manual Trigger with Form

**n8n Workflow:**
1. **Webhook** → Receives form data
2. **Code** → Parse options from form
3. **HTTP Request** → `/api/start` with parsed options
4. **Return Response** → Confirmation to user

---

## PowerShell Test Script

Save as `test-api.ps1`:

```powershell
# Test API without authentication
$body = @{
    template = "template1"
    aiImage = "yes"
    repeatCount = 3
    delay = "fast"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/start" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Response: $($response | ConvertTo-Json)"

# Check status
Start-Sleep -Seconds 2
$status = Invoke-RestMethod -Uri "http://localhost:5000/api/status"
Write-Host "Status: $($status | ConvertTo-Json)"
```

Run:
```powershell
.\test-api.ps1
```

---

## Test Checklist

- [ ] Flask app running on localhost:5000
- [ ] cURL test without API key works
- [ ] Status endpoint returns data
- [ ] API key authentication works (if enabled)
- [ ] n8n HTTP Request node succeeds
- [ ] Web UI still works independently
- [ ] Stop endpoint works via API

---

## Troubleshooting

**Issue:** Connection refused
```
Solution: Ensure Flask is running: python app.py
```

**Issue:** CORS error
```
Solution: API endpoints under /api/* have CORS enabled
Web UI endpoints don't need CORS (same origin)
```

**Issue:** 401 Unauthorized
```
Solution: Check REQUIRE_API_KEY setting in .env
If True, provide X-API-Key header
```

**Issue:** Automation already running
```
Solution: Call /api/stop first or wait for completion
```
