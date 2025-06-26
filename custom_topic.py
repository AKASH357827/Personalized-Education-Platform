from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from models import User, CourseProgress, UserActivity, db, ist_now
from utils import get_topic
import json
import os
from config import GROQ_API_KEY
from sqlalchemy.exc import IntegrityError
from groq import Groq
import re # Import the regular expression module

custom_topic_bp = Blueprint('custom_topic', __name__)

groq_client = Groq(api_key=GROQ_API_KEY)


def generate_and_save_quiz(topic, table_of_contents):
    # print("Generating quiz questions for topic:", topic)
    """Generates quiz questions using the LLM and saves them to a JSON file."""

    quiz_file_path = 'static/custom_quiz.json'
    # print("Got quiz questions")
    # Load existing quiz data or create a new structure
    if os.path.exists(quiz_file_path):
        with open(quiz_file_path, 'r') as file:
            try:
                quiz_data = json.load(file)
            except json.JSONDecodeError:
                print("Error: custom_quiz.json is corrupted. Initializing an empty structure.")
                quiz_data = {}
    else:
        quiz_data = {}
    # print("Loaded quiz data")

    # Check if topic already exists
    if topic in quiz_data:
        print(f"Quiz questions for topic '{topic}' already exist. Skipping generation.")
        return

    # Quiz generation prompt
    prompt = f"""You are an expert quiz generator. Your task is to create multiple-choice questions related to specific subtopics within a given topic. The output should be a JSON array containing question objects. You must generate exactly 10 questions.

    Here's the structure for each question object in the JSON array:

    ```json
    {{
      "id": <integer, unique identifier for the question>,
      "question": "<string, the quiz question>",
      "options": ["<string, option 1>", "<string, option 2>", "<string, option 3>", "<string, option 4>"],
      "answer": <integer, the index of the correct answer in the 'options' array (0-based)>,
      "subtopic": "<string, the subtopic the question belongs to>",
      "link": "<string, a relevant URL for more information on the topic. Provide a URL from a trusted source like w3schools.com, developer.mozilla.org, or official documentation. If no suitable link exists, leave this field blank.>"
    }}
    ```

    Your objective is to create engaging and informative quiz questions that assess understanding of the following topic and its associated subtopics. Ensure questions are clear, concise, and cover a range of difficulty levels. The `answer` field should accurately reflect the index of the correct option within the `options` array. The `subtopic` should directly correspond to a subtopic listed in the Table of Contents below. Aim for at least 1 question per subtopic. The [id](http://_vscodecontentref_/1) field should be incremented sequentially, starting from 1.

    Topic: {topic}
    Table of Contents:
    ```
    {table_of_contents}
    ```

    Generate ONLY the JSON array of quiz questions. Do not include any surrounding text, markdown, or formatting. Ensure there are exactly 10 questions. Follow to json format strictly. Do not include any additional information or explanations. The output should be a valid JSON array containing the question objects.
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            temperature=0.8,
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON using regex
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            content = match.group(0)
        else:
            print(f"Could not extract JSON from LLM response: {content}")
            flash(f"Error: Could not extract JSON from LLM for topic {topic}. Check server logs.", "error")
            return

        try:
            print("try")
            questions = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Content causing the error: {content}")
            flash(f"Error: Invalid JSON format for topic {topic}. Check server logs.", "error")
            return

        # Validate question format and data types
        if not isinstance(questions, list) or len(questions) != 10:
            print(f"Error: Expected 10 questions, but got {len(questions) if isinstance(questions, list) else 'invalid format'}")
            flash(f"Error: Expected 10 questions for topic {topic}, but got {len(questions)}. Check server logs.", "error")
            return

        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                print(f"Error: Each question must be a dictionary. Found: {type(question)}")
                return
            required_keys = ["id", "question", "options", "answer", "subtopic", "link"]
            if not all(key in question for key in required_keys):
                print(f"Error: Missing keys in question {i + 1}. Found keys: {list(question.keys())}")
                return
            if not isinstance(question["id"], int) or not isinstance(question["question"], str) or not isinstance(question["options"], list) or not isinstance(question["answer"], int) or not isinstance(question["subtopic"], str) or not isinstance(question["link"], str):
                print(f"Error: Incorrect data types in question {i + 1}: {question}")
                return
            if question["answer"] < 0 or question["answer"] >= len(question["options"]):
                print(f"Error: 'answer' index out of bounds in question {i + 1}: {question}")
                return

            # Ensure IDs are sequential
            question["id"] = i + 1
        print(questions)
        # Save questions to quiz_data
        quiz_data[f"custom_{topic}"] = questions

    except Exception as e:
        print(f"Error generating quiz for topic {topic}: {e}")
        flash(f"Error generating quiz for topic {topic}: {str(e)}", "error")
        return

    # Save the updated quiz data to the JSON file
    try:
        os.makedirs(os.path.dirname(quiz_file_path), exist_ok=True)
        with open(quiz_file_path, 'w', encoding="utf-8") as file:
            json.dump(quiz_data, file, indent=4)
        print(f"Quiz for topic '{topic}' saved successfully.")
    except Exception as e:
        print(f"Error saving quiz questions to file: {e}")
        flash(f"Error saving quiz questions to file for topic {topic}: {str(e)}", "error")


@custom_topic_bp.route('/add-custom-topic', methods=['POST'])
def add_custom_topic():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    topic_names = request.form.getlist('topic_names[]')

    if not topic_names:
        flash('At least one topic name is required', 'error')
        return redirect(url_for('main.index'))

    # Load or create user_topics.json
    file_path = 'static/user_topics.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            user_topics = json.load(file)
    else:
        user_topics = {}

    # Initialize user's topics if not exist
    if user.username not in user_topics:
        user_topics[user.username] = {"topics": {}}

    for topic_name in topic_names:
        topic_name = topic_name.lower()
        with open('static/all_topics.json', 'r') as file:
            all_topics = json.load(file)
        if topic_name not in all_topics["topics"]:
            flash(f'Topic {topic_name} not found in the database or already exists', 'error')
            continue
        if any(topic.lower() == topic_name for topic in user_topics[user.username]["topics"]):
            flash(f'Topic {topic_name} already exists', 'error')
            continue
        # Generate table of contents using LLama model
        prompt = f"""Create a detailed table of contents maximum of 3 contents for learning {topic_name}.
        Return the response as a JSON array in the following format:
        ["Subtopic 1", "Subtopic 2", "Subtopic 3"]
        Return ONLY the JSON array. Do not include surrounding text.
        """

        try:
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=600
            )

            # Process the response to ensure valid JSON
            content = response.choices[0].message.content.strip()

            # Extract JSON using regex
            match = re.search(r'\[.*\]', content, re.DOTALL) # added re.DOTALL to match across newlines
            if match:
                content = match.group(0)
            else:
                print(f"Could not extract JSON from LLM response: {content}")
                flash(f"Error: Could not extract JSON from LLM for topic {topic_name}. Check server logs.", "error")
                continue
            try:
                # Try to parse as JSON directly
                toc = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, extract array portion
                array_match = re.search(r'\[(.*)\]', content)
                if array_match:
                    # Convert to proper JSON array format
                    items = [item.strip().strip('"\'') for item in array_match.group(1).split(',')]
                    toc = items
                else:
                    # Fallback to simple split by newlines
                    toc = [line.strip().strip('"-,') for line in content.split('\n') if line.strip()]
            # Add topic to user's topics
            user_topics[user.username]["topics"][topic_name] = {
                "table_of_contents": toc,
                "created_at": ist_now().isoformat()
            }
            # Create course progress entry
            course_progress = CourseProgress(
                user_id=user.id,
                topic=f"custom_{topic_name}",
                current_step=0,
                total_steps=len(toc),
                completed=False
            )
            db.session.add(course_progress)

            # Add activity for new topic creation
            new_activity = UserActivity(
                user_id=user.id,
                activity_type='course',
                topic=f"custom_{topic_name}",
                score=0  # Initial score
            )
            db.session.add(new_activity)
            print("generating quiz")
            generate_and_save_quiz(topic_name, toc)

        except Exception as e:
            flash(f'Error creating topic {topic_name}: {str(e)}', 'error')
            continue

    # Save all topics back to file
    try:

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(user_topics, file, indent=4)

        db.session.commit()
        flash(f'{len(topic_names)} custom topics added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving topics: {str(e)}', 'error')

    return redirect(url_for('main.index'))

@custom_topic_bp.route('/dashboard')
def dashboard():
    with open('static/user_topics.json', 'r') as f:
        user_topics = json.load(f)

    username = session.get('username')
    if username in user_topics:
        custom_topics = user_topics[username].get('topics', {})
    else:
        custom_topics = {}

    return render_template('index.html', custom_topics=custom_topics)