# app.py
import os
from flask import Flask, render_template, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DATABASE_URI = os.environ.get("DATABASE_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")

from models import db  # Import the db object
from auth import auth_bp
from main import main_bp
from course import course_bp
from activity import activity_bp
from quiz import quiz_bp
from custom_topic import custom_topic_bp
from utils import markdown_filter

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(course_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(custom_topic_bp)

# Template filter (if you keep it here)
app.jinja_env.filters['markdown'] = markdown_filter  # Register in app context

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Create database tables within the Flask application context
with app.app_context():
    db.create_all()  # Recreates tables with new constraints

# main Starts
if __name__ == '__main__':
    app.run(debug=True)