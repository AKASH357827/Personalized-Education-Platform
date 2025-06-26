# activity.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import User, CourseProgress, UserActivity, db  # Correct absolute imports

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/activity')
def activity():
    # Check if user is logged in using both session variables
    if 'username' not in session or 'logged_in' not in session:
        flash('Please log in to view your activity', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        # Clear invalid session and redirect to login
        session.clear()
        flash('User session invalid. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Get courses with progress
        courses = CourseProgress.query.filter_by(user_id=user.id,)\
            .filter((CourseProgress.current_step > 1) | (CourseProgress.completed == True))\
            .order_by(CourseProgress.last_accessed.desc())\
            .all()
        # Get all activities
        activities = UserActivity.query.filter_by(user_id=user.id)\
            .order_by(UserActivity.timestamp.desc())\
            .limit(10)\
            .all()
        return render_template('activity.html', courses=courses, activities=activities)

    except Exception as e:
        flash(f'Error loading activity data: {str(e)}', 'error')
        return redirect(url_for('main.index'))