from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from models import User, db
from utils import markdown_filter
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/index')
def index():
    if 'logged_in' in session:
        user = User.query.filter_by(username=session['username']).first()
        with open('static/question.json', 'r') as file:
            topics_data = json.load(file)

        # Get custom topics with their full content
        custom_topics = {}
        try:
            if os.path.exists('static/user_topics.json'):
                with open('static/user_topics.json', 'r') as file:
                    user_topics = json.load(file)
                    if user.username in user_topics:
                        custom_topics = user_topics[user.username]["topics"]
        except FileNotFoundError:
            pass

        name = {'first_name': user.first_name, 'last_name': user.last_name}
        return render_template('index.html',
                             user=name,
                             topics=topics_data.keys(),
                             custom_topics=custom_topics)
    else:
        return redirect(url_for('auth.login'))


@main_bp.route('/')
@main_bp.route('/home')
def home():
    session.clear()
    return render_template('Home.html')

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()  # Fetch the user object

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone_number = request.form['phone_number']
        db.session.commit()  # Commit the changes to the database
        flash('Profile updated successfully!', 'success')
    return render_template('profile.html', user=user)

@main_bp.route('/leaderboard')
def leaderboard():
    if 'logged_in' not in session:
        return redirect(url_for('auth.login'))
     
    users = User.query.order_by(User.score.desc(),User.username.asc()).all()
    leaderboard_data = []
    rank = 1
    for user in users:
        username = user.username
        total_score = user.score
        if rank == 1:
            badge = "Gold"
        elif rank == 2:
            badge = "Silver"
        elif rank==3:
            badge = "Bronze"
        else:
            badge = "Participation"
        leaderboard_data.append({
            'rank': rank,
            'username': username,
            'score': total_score,
        })
        rank += 1
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)