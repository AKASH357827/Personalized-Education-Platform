# models.py
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime
import pytz

db = SQLAlchemy()  # Initialize SQLAlchemy (but don't bind to app yet)

def ist_now():
    return datetime.now(pytz.timezone('Asia/Kolkata'))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    password = db.Column(db.String(60), nullable=False)
    score = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hashes the password using bcrypt."""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(20))
    score = db.Column(db.Integer)

    def __repr__(self):
        return f'<QuizResult user_id={self.user_id}, question_id={self.question_id}, score={self.score}>'


class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(20), nullable=False)  # 'quiz' or 'course'
    topic = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer)  # For quizzes
    timestamp = db.Column(db.DateTime(timezone=True), default=ist_now)

    # Add unique constraint for user_id, activity_type, and topic
    __table_args__ = (
        db.UniqueConstraint('user_id', 'activity_type', 'topic', name='unique_user_activity'),
    )


class CourseProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime(timezone=True), default=ist_now)