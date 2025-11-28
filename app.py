from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from functools import wraps
from threading import Thread
import logging
from automation import DreamstimeBot
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for external integrations (n8n, webhooks, etc.)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for tracking automation progress
automation_state = {
    'running': False,
    'progress': [],
    'status': 'idle',
    'bot_instance': None  # Store bot instance for stop functionality
}


def progress_callback(step, message, status):
    """Callback function to track automation progress"""
    automation_state['progress'].append({
        'step': step,
        'message': message,
        'status': status
    })
    automation_state['status'] = status


def require_api_key(f):
    """Decorator to require API key for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip API key check if not required
        if not Config.REQUIRE_API_KEY:
            return f(*args, **kwargs)
        
        # Check for API key in header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key parameter'
            }), 401
        
        if api_key != Config.API_KEY:
            return jsonify({
                'success': False,
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def run_automation(options):
    """Run the automation in a separate thread"""
    global automation_state
    
    try:
        automation_state['running'] = True
        automation_state['progress'] = []
        automation_state['status'] = 'running'
        
        bot = DreamstimeBot(progress_callback=progress_callback, options=options)
        automation_state['bot_instance'] = bot
        
        success = bot.run()
        
        if success:
            automation_state['status'] = 'completed'
        else:
            automation_state['status'] = 'failed'
            
    except Exception as e:
        logger.error(f"Automation error: {str(e)}")
        automation_state['status'] = 'error'
        automation_state['progress'].append({
            'step': -1,
            'message': f"Error: {str(e)}",
            'status': 'error'
        })
    finally:
        automation_state['running'] = False
        automation_state['bot_instance'] = None


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start_automation():
    """Start the automation process (Web UI and API)"""
    global automation_state
    
    if automation_state['running']:
        return jsonify({
            'success': False,
            'message': 'Automation is already running'
        }), 400
    
    try:
        # Validate credentials before starting
        Config.validate_credentials()
        
        # Get automation options from request
        options = request.json if request.json else {}
        
        # Validate numeric options
        if 'repeatCount' in options:
            try:
                options['repeatCount'] = int(options['repeatCount'])
            except ValueError:
                options['repeatCount'] = Config.DEFAULT_REPEAT_COUNT
        
        if 'pauseAfter' in options:
            try:
                options['pauseAfter'] = int(options['pauseAfter'])
            except ValueError:
                options['pauseAfter'] = Config.DEFAULT_PAUSE_AFTER
        
        if 'pauseDuration' in options:
            try:
                options['pauseDuration'] = int(options['pauseDuration'])
            except ValueError:
                options['pauseDuration'] = Config.DEFAULT_PAUSE_DURATION
        
        logger.info(f"Starting automation with options: {options}")
        
        # Start automation in a separate thread
        thread = Thread(target=run_automation, args=(options,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Automation started successfully',
            'options': options
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Failed to start automation: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to start automation: {str(e)}'
        }), 500


@app.route('/api/start', methods=['POST'])
@require_api_key
def api_start_automation():
    """API endpoint to start automation (protected with API key)"""
    return start_automation()


@app.route('/stop', methods=['POST'])
def stop_automation():
    """Stop the running automation"""
    global automation_state
    
    if not automation_state['running']:
        return jsonify({
            'success': False,
            'message': 'No automation is currently running'
        }), 400
    
    try:
        bot = automation_state.get('bot_instance')
        if bot:
            bot.stop()
            return jsonify({
                'success': True,
                'message': 'Stop request sent to automation'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Bot instance not found'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to stop automation: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to stop automation: {str(e)}'
        }), 500


@app.route('/api/stop', methods=['POST'])
@require_api_key
def api_stop_automation():
    """API endpoint to stop automation (protected with API key)"""
    return stop_automation()


@app.route('/api/status')
@require_api_key
def api_get_status():
    """API endpoint to get status (protected with API key)"""
    return get_status()


@app.route('/status')
def get_status():
    """Get the current automation status"""
    return jsonify({
        'running': automation_state['running'],
        'status': automation_state['status'],
        'progress': automation_state['progress']
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 Dreamstime Automation Bot")
    print("="*60)
    print(f"📍 Server running at: http://localhost:5000")
    print(f"🔧 Debug mode: {Config.DEBUG}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
