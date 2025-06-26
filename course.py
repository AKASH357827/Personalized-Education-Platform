# course.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import User, CourseProgress, UserActivity, db, ist_now
from utils import get_step_content
import json
import os
from sqlalchemy.exc import IntegrityError

course_bp = Blueprint('course', __name__)

@course_bp.route('/topics/<topic>')
def topic_content(topic):
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    # Initialize progress tracking if not exists
    if 'progress' not in session:
        session['progress'] = {}
    if topic not in session['progress']:
        session['progress'][topic] = {
            'current_step': 1,
            'total_steps': len(get_topic_content(topic)),
            'completed': False
        }

    # Redirect to the current step
    current_step = session['progress'][topic]['current_step']
    return redirect(url_for('course.topic_step', topic=topic, step=current_step))

def get_topic_content(topic):
    # Check if it's a custom topic
    if topic.startswith('custom_'):
        topic_name = topic[7:]  # Remove 'custom_' prefix
        try:
            with open('static/user_topics.json', 'r') as file:
                user_topics = json.load(file)
                username = session.get('username')
                if username in user_topics and topic_name in user_topics[username]['topics']:
                    return user_topics[username]['topics'][topic_name]['table_of_contents']
        except (FileNotFoundError, KeyError):
            return []
    else:
        # Handle regular topics as before
        with open('static/question.json', 'r') as file:
            topics_data = json.load(file)

        if topic not in topics_data:
            return []

        subtopics = list(set(q['subtopic'] for q in topics_data[topic]))
        return subtopics
@course_bp.route('/topics/<topic>/step/<int:step>')
def topic_step(topic, step):
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    try:
        # Get the user
        user = User.query.filter_by(username=session['username']).first()
        # Handle custom topics
        if topic.startswith('custom_'):
            real_topic = topic[7:]  # Remove 'custom_' prefix
            with open('static/user_topics.json', 'r') as file:
                user_topics = json.load(file)
                if user.username in user_topics and real_topic in user_topics[user.username]['topics']:
                    toc = user_topics[user.username]['topics'][real_topic]['table_of_contents']
                    total_steps = len(toc)

                    # Step Validation (Crucially Adjusted)
                    if step < 1 or step > total_steps: # step > not >= total_steps
                        return redirect(url_for('main.index'))

                    # Corrected Indexing
                    current_subtopic = toc[step-1] #subtract 1 to correctly access elements, due to 1-based indexing
                    content = get_step_content(topic, current_subtopic)
        else:
            # Handle regular topics
            with open('static/topics.json', 'r') as file:
                topics_data = json.load(file)

            if topic not in topics_data:
                flash('Topic not found', 'error')
                return redirect(url_for('main.index'))

            subtopics = list((q['subtopic'] for q in topics_data[topic]))
            total_steps = len(subtopics)

            if step < 1 or step > total_steps:  # step > not >= total_steps
                return redirect(url_for('course.topic_content', topic=topic))

            # Corrected Indexing: Also needs adjustment
            current_subtopic = subtopics[step-1] #subtract 1 to correctly access elements, due to 1-based indexing
            content = get_step_content(topic, current_subtopic)

        if content:
            # Update progress
            progress = CourseProgress.query.filter_by(
                user_id=user.id,
                topic=topic
            ).first()

            if not progress:
                progress = CourseProgress(
                    user_id=user.id,
                    topic=topic,
                    current_step=step,
                    total_steps=total_steps,
                    completed=False
                )
                db.session.add(progress)
                progress_changed = True  # Mark that progress changed
            else:
                old_step = progress.current_step
                progress.current_step = step
                progress.last_accessed = ist_now()
                if step == total_steps:
                    progress.completed = True
                else:
                    progress.completed = False
                progress_changed = (progress.current_step != old_step) or progress.completed

            # Calculate progress percentage
            progress_percentage = int((progress.current_step ) / total_steps * 100)

            try:
                if progress_changed: # Only update the UserActivity if course progress changed
                    # Update or create activity
                    activity = UserActivity.query.filter_by(
                        user_id=user.id,
                        activity_type='course',
                        topic=topic
                    ).first()

                    if activity:
                        activity.score = progress_percentage
                        activity.timestamp = ist_now()
                    else:
                        activity = UserActivity(
                            user_id=user.id,
                            activity_type='course',
                            topic=topic,
                            score=progress_percentage
                        )
                        db.session.add(activity)

                db.session.commit()
                return render_template('steps.html',
                                    topic=topic,
                                    current_step=step,
                                    total_steps=total_steps,
                                    progress=progress_percentage,
                                    section_name=f"Learning {topic.replace('custom_', '')}",
                                    content=[content])
            except IntegrityError:
                db.session.rollback()
                flash('Error updating progress', 'error')
                return redirect(url_for('main.index'))

        flash('Content not found', 'error')
        return redirect(url_for('main.index'))

    except Exception as e:
        flash(f"Error loading content: {str(e)}", "error")
        return redirect(url_for('main.index'))