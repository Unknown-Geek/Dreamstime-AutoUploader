# API Integration Guide - n8n and Webhooks

## Overview

The Dreamstime Bot now supports external API requests from tools like n8n, Zapier, Make.com, or custom webhooks. This allows you to trigger automation programmatically.

---

## API Endpoints

### 1. Start Automation

**Endpoint:** `POST /api/start`

**Description:** Starts the automation with optional configuration

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here  (if REQUIRE_API_KEY=True)
```

**Request Body (all optional):**
```json
{
  "template": "template1",
  "manualDescription": "Additional description text",
  "aiImage": "yes",
  "modelRelease": "yes",
  "exclusiveImage": "no",
  "delay": "fast",
  "repeatCount": 10,
  "pauseAfter": 5,
  "pauseDuration": 60,
  "sameIdAction": "skip"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Automation started successfully",
  "options": {
    "template": "template1",
    "repeatCount": 10,
    ...
  }
}
```

**Error Response (400/401/403):**
```json
{
  "success": false,
  "message": "Error description"
}
```

---

### 2. Stop Automation

**Endpoint:** `POST /api/stop`

**Description:** Stops the running automation

**Headers:**
```
X-API-Key: your-api-key-here  (if REQUIRE_API_KEY=True)
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Stop request sent to automation"
}
```

---

### 3. Get Status

**Endpoint:** `GET /api/status`

**Description:** Get current automation status and progress

**Headers:**
```
X-API-Key: your-api-key-here  (if REQUIRE_API_KEY=True)
```

**Query Parameters (alternative to header):**
```
?api_key=your-api-key-here
```

**Response (200):**
```json
{
  "running": true,
  "status": "running",
  "progress": [
    {
      "step": 6,
      "message": "Processing image 3 of 10",
      "status": "info"
    }
  ]
}
```

---

## Configuration

### 1. Enable API Key Authentication (Optional but Recommended)

Edit your `.env` file:

```env
REQUIRE_API_KEY=True
API_KEY=your-secure-api-key-here
```

**Generate a secure API key:**
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use any strong random string
```

### 2. Without API Key Authentication

If you're running the bot in a private network:

```env
REQUIRE_API_KEY=False
```

---

## n8n Integration Examples

### Example 1: Basic Workflow Trigger

**n8n Workflow:**
1. **Trigger Node:** Webhook or Schedule
2. **HTTP Request Node:**
   - Method: POST
   - URL: `http://localhost:5000/api/start`
   - Headers:
     - `Content-Type`: `application/json`
     - `X-API-Key`: `your-api-key`
   - Body (JSON):
     ```json
     {
       "repeatCount": 5,
       "delay": "fast"
     }
     ```

---

### Example 2: Upload Detection → Auto-Submit

**Scenario:** Detect new uploads in Dreamstime and automatically submit them

**n8n Workflow:**
1. **Webhook Node:** Receives upload notification
2. **Code Node:** Parse upload data
3. **HTTP Request Node:** Call `/api/start`
   ```json
   {
     "template": "template1",
     "aiImage": "yes",
     "repeatCount": {{ $json["uploadCount"] }}
   }
   ```
4. **HTTP Request Node (polling):** Check status every 10s
   - URL: `http://localhost:5000/api/status?api_key=your-key`
   - Method: GET
5. **IF Node:** Check if `running === false`
6. **Notification Node:** Send completion notification

---

### Example 3: Scheduled Batch Processing

**n8n Workflow:**
1. **Cron Node:** Trigger at 2 AM daily
2. **HTTP Request:** Start automation
   ```json
   {
     "template": "template2",
     "aiImage": "yes",
     "modelRelease": "yes",
     "repeatCount": 50,
     "pauseAfter": 10,
     "pauseDuration": 120,
     "delay": "slow"
   }
   ```
3. **Wait Node:** Wait for completion (poll status)
4. **Email Node:** Send summary report

---

## cURL Examples

### Start Automation (with API key)
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "template": "template1",
    "aiImage": "yes",
    "repeatCount": 10,
    "delay": "fast"
  }'
```

### Start Automation (without API key)
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "repeatCount": 5
  }'
```

### Check Status
```bash
curl http://localhost:5000/api/status \
  -H "X-API-Key: your-api-key-here"
```

### Stop Automation
```bash
curl -X POST http://localhost:5000/api/stop \
  -H "X-API-Key: your-api-key-here"
```

---

## Python Example

```python
import requests
import time

API_URL = "http://localhost:5000/api"
API_KEY = "your-api-key-here"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Start automation
response = requests.post(
    f"{API_URL}/start",
    headers=headers,
    json={
        "template": "template1",
        "aiImage": "yes",
        "repeatCount": 10,
        "delay": "fast"
    }
)

if response.json()["success"]:
    print("Automation started!")
    
    # Poll status
    while True:
        status = requests.get(f"{API_URL}/status", headers=headers).json()
        
        if not status["running"]:
            print("Automation completed!")
            break
        
        if status["progress"]:
            latest = status["progress"][-1]
            print(f"Progress: {latest['message']}")
        
        time.sleep(5)  # Check every 5 seconds
```

---

## JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:5000/api';
const API_KEY = 'your-api-key-here';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY
};

async function startAutomation() {
  try {
    const response = await axios.post(`${API_URL}/start`, {
      template: 'template1',
      aiImage: 'yes',
      repeatCount: 10,
      delay: 'fast'
    }, { headers });
    
    console.log('Automation started:', response.data);
    
    // Poll for completion
    const checkStatus = setInterval(async () => {
      const status = await axios.get(`${API_URL}/status`, { headers });
      
      if (!status.data.running) {
        console.log('Automation completed!');
        clearInterval(checkStatus);
      } else {
        const progress = status.data.progress;
        if (progress.length > 0) {
          console.log('Progress:', progress[progress.length - 1].message);
        }
      }
    }, 5000);
    
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

startAutomation();
```

---

## Security Recommendations

1. **Always use API keys in production:**
   ```env
   REQUIRE_API_KEY=True
   API_KEY=<strong-random-key>
   ```

2. **Use HTTPS in production:**
   - Deploy behind nginx/Apache with SSL
   - Or use a reverse proxy with Let's Encrypt

3. **Restrict CORS origins:**
   Edit `app.py` to limit allowed origins:
   ```python
   CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
   ```

4. **Use environment-specific configurations:**
   - Development: API key optional
   - Production: API key required

5. **Monitor API usage:**
   - Add logging for all API requests
   - Set up rate limiting if needed

---

## Troubleshooting

### Issue: "API key required" error
**Solution:** Add API key to request headers or disable requirement:
```env
REQUIRE_API_KEY=False
```

### Issue: CORS error in browser
**Solution:** Ensure CORS is enabled for your origin in `app.py`

### Issue: Connection refused
**Solution:** Ensure Flask app is running:
```bash
python app.py
```

### Issue: Automation already running
**Solution:** Wait for current automation to finish or call `/api/stop` first

---

## Rate Limiting (Future Enhancement)

For production use, consider adding rate limiting:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/start', methods=['POST'])
@limiter.limit("10 per hour")
@require_api_key
def api_start_automation():
    return start_automation()
```

---

## Complete n8n Workflow Template

```json
{
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "hour": 2,
          "minute": 0
        }
      }
    },
    {
      "name": "Start Dreamstime Bot",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:5000/api/start",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "headerAuth": {
          "name": "X-API-Key",
          "value": "your-api-key"
        },
        "jsonParameters": true,
        "bodyParametersJson": {
          "template": "template1",
          "aiImage": "yes",
          "repeatCount": 20,
          "delay": "slow"
        }
      }
    },
    {
      "name": "Wait for Completion",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "amount": 5,
        "unit": "seconds"
      }
    },
    {
      "name": "Check Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://localhost:5000/api/status?api_key=your-api-key"
      }
    },
    {
      "name": "Is Running?",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.running }}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Send Notification",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "subject": "Dreamstime Automation Complete",
        "text": "The automation has finished processing images."
      }
    }
  ]
}
```

---

## Support

For issues or questions about API integration:
1. Check Flask logs: `python app.py`
2. Test with cURL first
3. Verify API key configuration
4. Check CORS settings for browser-based integrations
