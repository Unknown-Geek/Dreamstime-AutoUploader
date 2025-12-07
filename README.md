# Dreamstime Automation Bot - Enhanced Edition

🤖 **Automated image submission workflow for Dreamstime with advanced features**

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
- **Batch processing** - Process multiple images (up to 10,000 per run)
- ⏸️ **Pause intervals** - Pause every 20 images for 2 minutes by defaulty default
- **Duplicate detection** - Skip or stop on duplicate image IDs
- ⚡ **Configurable delays** - Fast (5-10s) or Slow (10-15s) modes
- **Stop functionality** - Gracefully stop automation anytime
- **Real-time progress tracking** - See exactly what's happening

## Requirements

- Python 3.8+
- Playwright
- Flask
- python-dotenv

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Dreamstime-Bot
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
   
   Copy `.env.example` to `.env` and add your Dreamstime credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```
   DREAMSTIME_USERNAME=your_username
   DREAMSTIME_PASSWORD=your_password
   FLASK_SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True
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
- **Number of Images**: How many to process (unlimited, default 10000)
- **Pause Settings**: Pause every N images for M seconds
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
Number of Images: 20
Speed: Slow
Pause After: 10 images
Pause Duration: 120 seconds
```

#### Exclusive Content with Model Releases
```
Template: Template 2 (Creative)
Manual Description: "High quality commercial content"
Model Release: Yes
Exclusive: Yes
Number of Images: 50
Pause After: 20
Duplicate Action: Stop
```

## Architecture

### Backend (Python + Playwright)

- **`automation.py`**: Core automation logic with Playwright
  - `AutomationState`: State management class
  - `DreamstimeBot`: Main automation orchestrator
  - Enhanced processing methods for all features

- **`app.py`**: Flask web server
  - REST API endpoints for control
  - Real-time status updates
  - Options handling and validation

- **`config.py`**: Configuration management
  - Credentials loading
  - Default option values
  - URL configurations

- **`utils.py`**: Utility functions
  - Template management (80 phrases total)
  - Delay calculation
  - Title sanitization
  - Stop-safe wait operations

### Frontend (HTML + CSS + JavaScript)

- **`templates/index.html`**: Web interface
  - Comprehensive options panel
  - Real-time progress display
  - Start/Stop controls

- **`static/style.css`**: Modern, professional styling
  - Dark mode design
  - Smooth animations
## Progress Tracking

Real-time updates show:
- Current step and action
- Success/error status
- Progress percentage
- Processed vs. successful count
- Timestamps for all actions

## UI Features

- **Modern Dark Theme**: Professional gradient design
- **Real-time Status**: Color-coded status badge with animations
- **Progress Log**: Scrollable list with icons and timestamps
- **Responsive Design**: Works on all screen sizes
- **Smooth Animations**: Fade-in effects and transitions
- **Form Validation**: Input validation and helpful tooltips

## Debugging

Check console logs for detailed execution information:

```bash
# Run with debug mode
FLASK_DEBUG=True python app.py
```

Browser console (F12) shows:
- API request/response details
- Status polling updates
- JavaScript errors (if any)

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
- Systemd timer checks remote debugging port every 2 minutes
- Auto-restarts browser if connection is lost
- Maintains persistent browser session to prevent captcha challenges

## Important Notes

1. **Persistent Browser Session**: The browser maintains a persistent session to avoid repeated captcha challenges
2. **Health Monitoring**: Automatic health checks restart the browser if needed
3. **Manual Intervention**: Initial login may require manual captcha solving via VNC
4. **Credentials Security**: Never commit your `.env` file to version control
5. **Rate Limiting**: Default delays (5-15 seconds) help avoid triggering anti-bot measures
6. **Duplicate Detection**: The bot tracks image IDs to prevent reprocessing
7. **Max Images Per Run**: Default 10,000 images per API call (customizable via payload)

## Changelog

### Version 2.1 (Current)
- Added Gemini AI image analysis for descriptive title/description generation
- Improved fallback title logic to use descriptions when AI analysis unavailable
- Increased default batch size to 10,000 images per run
- Added health check system with automatic browser recovery
- Fixed browser session persistence to prevent captcha loops
- Reduced delay ranges (5-10s fast, 10-15s slow) for faster processing

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
- UI overhaul

### Version 1.0
- Basic automation workflow
- Login and navigation
- Image processing
- Basic progress tracking

## Support

For issues or questions:
1. Check browser status via VNC (https://vnc.shravanpandala.me)
2. Review logs: `sudo journalctl -u dreamstime-bot -f`
3. Verify Chromium service: `sudo systemctl status chromium-dreamstime`
4. Ensure credentials are correctly configured in `.env`
5. Check health: `curl http://localhost:9222/json/version`

## Acknowledgments

- Built with Playwright for reliable browser automation
- Flask for the web interface
- Google Gemini AI for image analysis
- Systemd for service management and health monitoring
