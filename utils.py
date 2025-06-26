import json
from groq import Groq
from config import GROQ_API_KEY
import markdown2
from flask import flash

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)


def get_data():
    with open('static\\topics.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data

def get_questions():
    with open('static\\question.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data

def get_topic():
    with open('static\\advanced.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data

# Add this near other helper functions in Main.py
def get_step_content(topic, subtopic):
    """Helper function to get content for a specific step"""
    try:
        # Handle custom topics
        if isinstance(topic, str) and topic.startswith('custom_'):
            real_topic = topic[7:]  # Remove 'custom_' prefix
            prompt = f"""Explain {subtopic} in detail with the following structure:
            1. Brief Introduction (2-3 sentences)
            2. Main Concept (detailed explanation)
            3. Examples and Implementation
            4. Key Points to Remember

            Format the response with proper Markdown headings and code blocks."""

            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=1000
            )
            content = response.choices[0].message.content

            # Parse content into sections using existing logic
            sections = []
            current_section = {"heading": "", "description": "", "examples": []}
            in_code_block = False
            current_code = ""

            for line in content.split('\n'):
                if line.startswith('#'):  # Section header
                    if current_section["heading"]:
                        if current_code:
                            current_section["examples"].append(current_code)
                            current_code = ""
                        sections.append(current_section.copy())
                    current_section = {
                        "heading": line.replace('#', '').strip(),
                        "description": "",
                        "examples": []
                    }
                elif line.strip().startswith('```'):
                    if in_code_block:
                        current_section["examples"].append(current_code.strip())
                        current_code = ""
                        in_code_block = False
                    else:
                        in_code_block = True
                else:
                    if in_code_block:
                        current_code += line + "\n"
                    elif line.strip():
                        current_section["description"] += line + "\n"

            # Add the last section
            if current_section["heading"]:
                if current_code:
                    current_section["examples"].append(current_code)
                sections.append(current_section)

            return {
                "content": {
                    "title": f"{subtopic} in {real_topic}",
                    "introduction": sections[0]["description"] if sections else "",
                    "sections": sections[1:] if len(sections) > 1 else sections,
                    "summary": "Generated content for custom topic",
                    "notes": "Practice these concepts to better understand them."
                }
            }

        # Handle regular topics (existing logic)
        else:
            with open('static/topics.json', 'r') as file:
                topics_data = json.load(file)
            
            question = next((q for q in topics_data.get(topic, []) if q['subtopic'] == subtopic), None)
            if question:
                prompt = f"""Explain {subtopic} in {topic} programming language with the following structure:
                1. Brief Introduction (2-3 sentences)
                2. Main Concept (detailed explanation)
                3. Code Examples (with comments if necessary else text or formule examples)
                4. Key Points to Remember

                Format the response with proper Markdown headings and code blocks."""

                response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=1500
                )
                content = response.choices[0].message.content
                # Parse content into sections
                sections = []
                current_section = {"heading": "", "description": "", "examples": []}
                in_code_block = False
                current_code = ""

                for line in content.split('\n'):
                    if line.startswith('#'):  # Section header
                        if current_section["heading"]:
                            if current_code:
                                current_section["examples"].append(current_code)
                                current_code = ""
                            sections.append(current_section.copy())
                        current_section = {
                            "heading": line.replace('#', '').strip(),
                            "description": "",
                            "examples": []
                        }
                    elif line.strip().startswith('```'):
                        if in_code_block:
                            current_section["examples"].append(current_code.strip())
                            current_code = ""
                            in_code_block = False
                        else:
                            in_code_block = True
                    else:
                        if in_code_block:
                            current_code += line + "\n"
                        elif line.strip():
                            current_section["description"] += line + "\n"

                # Add the last section
                if current_section["heading"]:
                    if current_code:
                        current_section["examples"].append(current_code)
                    sections.append(current_section)
                if question and 'link' in question:
                    summary = question['link']
                else:
                    summary = "Visit the provided link to learn more."
                return {
                    "content": {
                        "title": f"{subtopic} in {topic}",
                        "introduction": sections[0]["description"] if sections else "",
                        "sections": sections[1:] if len(sections) > 1 else sections,
                        "summary": summary,
                        "notes": "Practice these concepts to better understand them."
                    }
                }
            return None
    except Exception as e:
        print(f"Error in get_step_content: {str(e)}")
        return None


# Add this helper function
def markdown_filter(text):
    return markdown2.markdown(text, extras=['fenced-code-blocks', 'tables'])