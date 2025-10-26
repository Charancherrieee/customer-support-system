from flask import Flask, render_template, session, redirect, url_for
from flask_mysqldb import MySQL
from flask_login import LoginManager
from config import config
import os

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Load configuration
app.config.from_object(config['development'])

# Initialize MySQL
mysql = MySQL(app)

# Make mysql available globally
app.mysql = mysql

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Import models
from models import User

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.get_by_id(mysql, int(user_id))

# Import and register blueprints
from routes.auth import auth_bp
from routes.tickets import tickets_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(tickets_bp, url_prefix='/tickets')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Home route
@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        user = User.get_by_id(mysql, session['user_id'])
        if user and user.is_agent():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('tickets.user_dashboard'))
    return render_template('index.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# Template filters
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format datetime for templates"""
    if value is None:
        return ""
    return value.strftime(format)

@app.template_filter('date')
def format_date(value):
    """Format date for templates"""
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d')

# Context processors
@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def get_priority_class(priority):
        """Get CSS class for priority badge"""
        classes = {
            'low': 'bg-info',
            'medium': 'bg-warning',
            'high': 'bg-danger',
            'urgent': 'bg-dark'
        }
        return classes.get(priority, 'bg-secondary')
    
    def get_status_class(status):
        """Get CSS class for status badge"""
        classes = {
            'open': 'bg-primary',
            'in_progress': 'bg-warning',
            'resolved': 'bg-success',
            'closed': 'bg-secondary'
        }
        return classes.get(status, 'bg-secondary')
    
    return dict(
        get_priority_class=get_priority_class,
        get_status_class=get_status_class
    )

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)