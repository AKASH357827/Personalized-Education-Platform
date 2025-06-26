from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from models import User, QuizResult, UserActivity, db,ist_now
from utils import get_data, get_topic,get_questions
import json
import os

quiz_bp = Blueprint('quiz', __name__)


def get_topics_from_json():
    """Loads topics from question.json."""
    try:
        with open("static/question.json", 'r') as f:
            data = json.load(f)
            return list(data.keys())  # Return a list of topic names
    except FileNotFoundError:
        print("question.json not found!")
        return []
    except json.JSONDecodeError:
        print("Error decoding question.json!")
        return []

@quiz_bp.route('/quiz', methods=['GET'])
def quiz():
    if 'username' not in session:
        flash('You must be logged in to take the quiz!', 'danger')
        return redirect(url_for('auth.login'))

    topic = request.args.get('topic')  # Get topic from URL, if any
    topics = get_topics_from_json()

    if topic: # Check the topic has value
        print("The topic is: " + topic)
        return render_template('quiz.html', topics=topics,topic=topic) #The last value will tell renderQuestion to render if is there is a value
    else:
        print("The topic is None")
        return render_template('quiz.html', topics=topics,topic=None)
    


@quiz_bp.route('/result', methods=['GET', 'POST'])
def result():
    if 'username' not in session:
        flash('You must be logged in to take the quiz!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        topic = request.form.get('subject')
        data = None  # Initialize data

        try:
            if topic.startswith('custom_'):
                with open("static/custom_quiz.json", 'r') as f:
                    custom_quiz_data = json.load(f)
                    if topic in custom_quiz_data:
                        data = custom_quiz_data  # Use custom_quiz_data if topic exists
        except FileNotFoundError:
            flash("Custom quiz data file not found!", "error")
            return redirect(url_for('main.index'))
        except json.JSONDecodeError:  # Handle malformed json file
            flash("Error decoding custom quiz JSON file.", "error")
            return redirect(url_for('main.index'))

        if data is None:  # If not in custom_quiz.json, use the default
            data = get_questions()
            if topic not in data:
                flash(f"Topic '{topic}' not found in standard quiz data.", "error")
                return redirect(url_for('main.index'))


        questions = data[topic]
        score = 0
        wrong_answer = []

        for q in questions:
            correct_answer = q["options"][int(q["answer"])]
            selected_answer = request.form.get(str(q["id"]))

            if selected_answer is not None:
                if correct_answer == selected_answer:
                    score += 1
                else:
                    if wrong_answer:
                        t = True
                        for i in wrong_answer:
                            if q["subtopic"] == i[0]:
                                t = False
                        if t:
                            da = [q["subtopic"], q["link"]]
                            wrong_answer.append(da)
                    else:
                        da = [q["subtopic"], q["link"]]
                        wrong_answer.append(da)

        user = User.query.filter_by(username=session['username']).first()
        quizres = QuizResult.query.filter_by(user_id=user.id).all()
        t = True
        for q in quizres:
            if q.topic == topic:
                q.score = score
                db.session.commit()
                t = False
        if t:
            new_user = QuizResult(user_id=user.id, topic=topic, score=score)
            db.session.add(new_user)
        user_results = QuizResult.query.filter_by(user_id=user.id).all()
        ts = 0
        for usr in user_results:
            ts += usr.score
        user.score = ts
        db.session.commit()
        ifuser = UserActivity.query.filter_by(user_id=user.id, activity_type="quiz", topic=topic).first()

        # Add activity tracking

        if ifuser is None: # Check if ifuser is none instead of not user
            new_activity = UserActivity(
                user_id=user.id,
                activity_type='quiz',
                topic=topic,
                score=score * 10  # Convert score to percentage
            )
            db.session.add(new_activity)

        else:
            ifuser.activity_type = 'quiz'
            ifuser.topic = topic
            ifuser.score = score * 10  # Convert score to percentage
            ifuser.timestamp = ist_now()
        db.session.commit()
        if score == 10:
            advance = get_topic()
            advance = advance[topic]
            data = {"score": score, "improvement": advance}
        else:
            data = {"score": score, "improvement": wrong_answer}
        return render_template('progress.html', result=data)

    return redirect(url_for('main.index'))