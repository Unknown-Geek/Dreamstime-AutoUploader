# Dreamstime Automation Bot - Enhanced Edition

🤖 **Automated image submission workflow for Dreamstime with advanced features**

## 🎯 Features

### Core Automation
- ✅ Automatic login to Dreamstime
- ✅ Navigate to upload section
- ✅ Process uploaded images
- ✅ Title sanitization (remove colons, limit to 115 chars)
- ✅ Auto-submit images

### Advanced Features (NEW! 🎉)
- ✨ **Template-based description enhancement** - Two template sets with 40 descriptive phrases each
- 🤖 **AI image auto-categorization** - Automatically categorize AI-generated images
- 📝 **Model release management** - Add model releases automatically
- ⭐ **Exclusive content marking** - Mark images as exclusive
- 🔄 **Batch processing** - Process multiple images with configurable count
- ⏸️ **Pause intervals** - Pause after N images for M seconds
- 🎯 **Duplicate detection** - Skip or stop on duplicate image IDs
- ⚡ **Configurable delays** - Fast (5-11s) or Slow (10-16s) modes
- 🛑 **Stop functionality** - Gracefully stop automation anytime
- 📊 **Real-time progress tracking** - See exactly what's happening

## 📋 Requirements

- Python 3.8+
- Playwright
- Flask
- python-dotenv

## 🚀 Installation

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

## 💻 Usage

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
- **Speed**: Fast (5-11s delays) or Slow (10-16s delays)
- **Number of Images**: How many to process (1-100)
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
Pause After: 5 images
Pause Duration: 60 seconds
```

#### Exclusive Content with Model Releases
```
Template: Template 2 (Creative)
Manual Description: "High quality commercial content"
Model Release: Yes
Exclusive: Yes
Number of Images: 50
Pause After: 10
Duplicate Action: Stop
```

## 🏗️ Architecture

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
## 📊 Progress Tracking

Real-time updates show:
- Current step and action
- Success/error status
- Progress percentage
- Processed vs. successful count
- Timestamps for all actions

## 🎨 UI Features

- **Modern Dark Theme**: Professional gradient design
- **Real-time Status**: Color-coded status badge with animations
- **Progress Log**: Scrollable list with icons and timestamps
- **Responsive Design**: Works on all screen sizes
- **Smooth Animations**: Fade-in effects and transitions
- **Form Validation**: Input validation and helpful tooltips

## 🔍 Debugging

Check console logs for detailed execution information:

```bash
# Run with debug mode
FLASK_DEBUG=True python app.py
```

Browser console (F12) shows:
- API request/response details
- Status polling updates
- JavaScript errors (if any)

## ⚠️ Important Notes

1. **Non-Headless Mode**: The browser runs in visible mode so you can monitor progress
2. **Manual Intervention**: You may need to solve captchas manually
3. **Credentials Security**: Never commit your `.env` file to version control
4. **Rate Limiting**: Use appropriate delays to avoid triggering anti-bot measures
5. **Duplicate Detection**: The bot tracks image IDs to prevent reprocessing

## 📝 Changelog

### Version 2.0 (Current)
- ✨ Added template system with 80 descriptive phrases
- 🤖 AI image auto-categorization
- 📝 Model release management
- ⭐ Exclusive content marking
- 🔄 Configurable batch processing
- ⏸️ Pause interval support
- 🎯 Duplicate image detection
- ⚡ Configurable processing speeds
- 🛑 Stop functionality
- 📊 Enhanced progress tracking
- 🎨 Complete UI overhaul

### Version 1.0
- ✅ Basic automation workflow
- ✅ Login and navigation
- ✅ Image processing
- ✅ Basic progress tracking

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and personal use. Please comply with Dreamstime's Terms of Service.

## 🆘 Support

For issues or questions:
1. Check the walkthrough documentation
2. Review error logs in the console
3. Ensure credentials are correctly configured
4. Verify Playwright browsers are installed

## 🙏 Acknowledgments

- Built with Playwright for reliable browser automation
- Flask for the web interface
- Modern CSS for professional styling
- Inspired by browser extension automation patterns

---

**Made with ❤️ for automating tedious tasks**
