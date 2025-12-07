# Dreamstime Automation Bot - Enhanced Edition

Automated image submission workflow for Dreamstime with advanced AI-powered features.

## Features

### Core Automation
- Automatic login to Dreamstime
- Navigate to upload section
- Process uploaded images
- Title sanitization (remove colons, limit to 115 chars)
- Auto-submit images

### Advanced Features
- **Template-based description enhancement** - Two template sets with 40 descriptive phrases each
- **AI image auto-categorization** - Automatically categorize AI-generated images
- **Model release management** - Add model releases automatically
- **Exclusive content marking** - Mark images as exclusive
- **Batch processing** - Process up to 10,000 images per run
- **Pause intervals** - Pause every 20 images for 2 minutes by default
- **Duplicate detection** - Skip or stop on duplicate image IDs
- **Configurable delays** - Fast (5-10s) or Slow (10-15s) modes
- **Stop functionality** - Gracefully stop automation anytime
- **Real-time progress tracking** - See exactly what's happening
- **Gemini AI Analysis** - Auto-generate descriptive titles and descriptions
- **Health monitoring** - Automatic browser recovery on failure

## Requirements

- Python 3.8+
- Playwright
- Flask
- python-dotenv
- Google Gemini API key (optional, for AI features)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Dreamstime-AutoUploader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Configure credentials**
   
   Create `.env` file with your settings:
   ```
   DREAMSTIME_USERNAME=your_username
   DREAMSTIME_PASSWORD=your_password
   FLASK_SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True
   GEMINI_API_KEY=your-gemini-api-key
   ```

## Usage

### Start the Web Interface

```bash
python app.py
```

Then open your browser to: `http://localhost:5000`

### Configure Options

The web interface provides comprehensive options:

**1. Description Enhancement**
- **Template**: Choose from professional or creative phrase sets
- **Manual Description**: Add custom text to all descriptions

**2. Image Properties**
- **AI Generated**: Auto-categorize as AI (category 172, subcategory 212)
- **Model Release**: Add first available model release
- **Exclusive**: Mark as exclusive content

**3. Processing Configuration**
- **Speed**: Fast (5-10s delays) or Slow (10-15s delays)
- **Number of Images**: How many to process (default 10,000)
- **Pause Settings**: Pause every 20 images for 2 minutes by default
- **Duplicate Action**: Skip or stop on duplicate image IDs

### Example Configurations

#### Simple Batch Processing
```
Template: None
Number of Images: 10
Speed: Fast
Duplicate Action: Skip
```

#### AI Images with Professional Descriptions
```
Template: Template 1 (Professional)
AI Generated: Yes
Number of Images: 100
Speed: Fast
Pause After: 20 images
Pause Duration: 120 seconds
```

#### Exclusive Content with Model Releases
```
Template: Template 2 (Creative)
Manual Description: "High quality commercial content"
Model Release: Yes
Exclusive: Yes
Number of Images: 500
Pause After: 20
Duplicate Action: Stop
```

## API Integration

The bot exposes RESTful API endpoints for integration with n8n, webhooks, or other automation tools:

### Endpoints

```
POST /api/start      - Start automation with optional parameters
POST /api/stop       - Stop running automation
GET  /api/status     - Get current automation status
GET  /health         - Health check for the bot service
```

### Example API Call

```bash
curl -X POST https://n8n.shravanpandala.me/dreamstime/api/start \
  -H "Content-Type: application/json" \
  -d '{"repeatCount": 100}'
```

### Health Check

The bot includes automatic health monitoring:
- Systemd timer checks browser connection every 2 minutes
- Auto-restarts browser if remote debugging port is unavailable
- Maintains persistent browser session to prevent captcha challenges
- VNC interface available at: https://vnc.shravanpandala.me

## Architecture

### Backend (Python + Playwright)

- **`automation.py`**: Core automation logic with Playwright
  - `AutomationState`: State management class
  - `DreamstimeBot`: Main automation orchestrator
  - Gemini AI integration for image analysis

- **`app.py`**: Flask web server
  - REST API endpoints for control
  - Real-time status updates
  - Options handling and validation

- **`config.py`**: Configuration management
  - Credentials and API key loading
  - Default option values
  - URL configurations

- **`utils.py`**: Utility functions
  - Template management (80+ phrases)
  - Delay calculation with randomization
  - Title sanitization
  - Stop-safe wait operations

- **`gemini_analyzer.py`**: AI analysis module
  - Google Gemini API integration
  - Image-to-text analysis
  - Title and description generation

### Frontend (HTML + CSS + JavaScript)

- **`templates/index.html`**: Web interface
  - Comprehensive options panel
  - Real-time progress display
  - Start/Stop controls

- **`static/style.css`**: Modern, professional styling
  - Dark mode design
  - Smooth animations

### Services

- **`chromium-dreamstime.service`**: Systemd service for persistent browser
- **`dreamstime-bot.service`**: Systemd service for Flask app
- **`chromium-healthcheck.service`**: Health monitoring and recovery
- **`chromium-healthcheck.timer`**: Runs health checks every 2 minutes

## Progress Tracking

Real-time updates show:
- Current step and action
- Success/error status
- Progress percentage
- Processed vs. successful count
- Timestamps for all actions

## UI Features

- Modern dark theme with gradient design
- Real-time status with color-coded indicators
- Scrollable progress log with icons
- Responsive design for all screen sizes
- Smooth animations and transitions

## Debugging

Check console logs for detailed execution information:

```bash
# View bot service logs
sudo journalctl -u dreamstime-bot -f

# View browser service logs
sudo journalctl -u chromium-dreamstime -f

# Check health check status
sudo systemctl status chromium-healthcheck.timer

# Verify browser connection
curl http://localhost:9222/json/version
```

## Important Notes

1. **Persistent Browser Session**: The browser maintains a persistent session to avoid repeated captcha challenges
2. **Health Monitoring**: Automatic health checks (every 2 minutes) restart the browser if needed
3. **Initial Login**: First login may require manual captcha solving via VNC viewer
4. **Credentials Security**: Never commit your `.env` file to version control
5. **Rate Limiting**: Default delays (5-15 seconds) help avoid triggering anti-bot measures
6. **Duplicate Detection**: The bot tracks image IDs to prevent reprocessing
7. **Max Images Per Run**: Default 10,000 images per API call (customizable via payload)
8. **AI Analysis**: Gemini API is optional; titles fall back to descriptions if unavailable

## Changelog

### Version 2.1 (Current)
- Added Gemini AI image analysis for descriptive titles/descriptions
- Improved fallback title logic to use descriptions when AI unavailable
- Increased default batch size to 10,000 images per run
- Added health check system with automatic browser recovery
- Fixed browser session persistence to prevent captcha loops
- Reduced delay ranges (5-10s fast, 10-15s slow) for faster processing
- Professional README with reduced emoji usage

### Version 2.0
- Added template system with 80 descriptive phrases
- AI image auto-categorization
- Model release management
- Exclusive content marking
- Configurable batch processing
- Pause interval support
- Duplicate image detection
- Configurable processing speeds
- Stop functionality
- Enhanced progress tracking

### Version 1.0
- Basic automation workflow
- Login and navigation
- Image processing
- Basic progress tracking

## Support

For issues or questions:
1. Check browser status via VNC: https://vnc.shravanpandala.me
2. Review bot logs: `sudo journalctl -u dreamstime-bot -f`
3. Check browser service: `sudo systemctl status chromium-dreamstime`
4. Verify health check: `systemctl status chromium-healthcheck.timer`
5. Test connection: `curl http://localhost:9222/json/version`
6. Ensure `.env` file is properly configured

## Acknowledgments

- Built with Playwright for reliable browser automation
- Flask for the web interface
- Google Gemini AI for image analysis
- Systemd for service management and health monitoring
