from flask import Flask, render_template, request, jsonify
import json
from textwrap import dedent
from openai import OpenAI
import os
from dotenv import load_dotenv
import sqlite3
import difflib

app = Flask(__name__)

load_dotenv('api_key.env')
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Please set it in the .env file.")

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

task = '''
    You are a helpful educational assistant. You will be provided with a section of a textbook and an essay prompt,
    and your task is to write an essay that answers the essay prompt using the textbook section to support your answer.
'''

simplify_task = '''
    You are a precise and discerning editor. You will be provided with an essay, and your task is to identify only words that are exceptionally academic or overly complicated.
    These words must represent a significant barrier to comprehension for a general audience, requiring advanced knowledge or niche expertise to understand easily.
    Ignore words that are simply formal or uncommon but can still be understood in context.
'''

exemplify_task = '''
    You are a meticulous and insightful editor. You will be provided with an essay, and your task is to identify only the most critical spots where an example is essential to enhance clarity, engagement, or persuasiveness.
    Focus on sections that genuinely lack evidence, are difficult to grasp, or feel overly abstract. Ignore areas that are already clear or adequately detailed, even if they could theoretically be improved by an example.
'''

factcheck_task = '''
    You are a meticulous and skeptical editor. You will be provided with an essay and a source text. Your task is to identify only the most critical spots in the essay that require fact-checking for accuracy.
    Focus on statements that directly contradict the source text, make bold or improbable claims without evidence, or are likely to mislead readers if incorrect.
    Avoid flagging general statements or minor details unless they are integral to the argument or significantly impact credibility.
'''

clarify_task = '''
    You are an incisive and thoughtful editor. You will be provided with an essay, and your task is to identify only the most compelling opportunities for deeper exploration of the text’s ideas.
    Focus on areas where key ethical, moral, social, or practical implications are glaringly unexplored or where a deeper investigation would significantly enhance the argument’s depth and nuance.
    Avoid suggesting reflection for sections that are already clear or sufficiently detailed unless the lack of depth weakens the essay.
'''

assert_task = '''
    You are a discerning and assertive editor. You will be provided with an essay, and your task is to identify only the areas where the essay most critically lacks originality or conviction.
    Focus on sections that feel notably weak, neutral, or overly cautious, and suggest ways for the user to add a bold, distinctive perspective or stronger reasoning.
    Avoid flagging statements that are already clear or sufficiently assertive unless taking a more definitive stance would meaningfully enhance the essay's persuasiveness and engagement.
'''

@app.route('/')
def index():
    clear_tables()
    return render_template('rewrite.html')  # Render the HTML file

@app.route('/rewrite', methods=['POST'])
def rewrite():
    data = request.json
    source_text = data.get('source_text')
    essay_prompt = data.get('essay_prompt')

    # Prepare messages for ChatGPT API
    messages = [
        {"role": "system", "content": dedent(task)},
        {"role": "user", "content": dedent(f"Textbook: {source_text}")},
        {"role": "user", "content": dedent(f"Assignment: {essay_prompt}")}
    ]

    # Call the OpenAI chat completion API
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",  # Change this to the appropriate model as needed
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "essay_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "final_answer": {"type": "string"}
                        },
                        "required": ["final_answer"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        rewritten_text = result.get('final_answer', "No answer provided.")

    except Exception as e:
        rewritten_text = "An unexpected error occurred: " + str(e)

    return jsonify({"response": rewritten_text})


####### SIMPLIFY #######

@app.route('/simplify', methods=['POST'])
def simplify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(simplify_task)},
        {"role": "user", "content": dedent('''Provide:
                                            - A list where each entry is an identified word that meets the criteria for being overly academic or complex (as simplify_context).
                                            - A list where each entry provides an explanation of why the identified word is overly academic or complex and presents a significant barrier to comprehension (as simplify_reasoning).
                                            - A list where each entry suggests a simpler, equally precise alternative or improvement, ensuring the meaning and tone remain appropriate for the audience (as simplify_suggestion).
                                           ''')},
        {"role": "user", "content": dedent(f"Essay: {essay}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "simplify_context": {"type": "array", "items": {"type": "string"}},
                            "simplify_reasoning": {"type": "array", "items": {"type": "string"}},
                            "simplify_suggestion": {"type": "array", "items": {"type": "string"}},

                        },
                        "required": ["simplify_context", "simplify_reasoning", "simplify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        simplify_context = result.get('simplify_context', [])
        simplify_reasoning = result.get('simplify_context', [])
        simplify_suggestion = result.get('simplify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        simplify_context = []
        simplify_reasoning = []
        simplify_suggestion = []

    return jsonify({
        "simplify_context": simplify_context,
        "simplify_reasoning": simplify_reasoning,
        "simplify_suggestion": simplify_suggestion,

        })


####### EXEMPLIFY #######

@app.route('/exemplify', methods=['POST'])
def exemplify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(exemplify_task)},
        {"role": "user", "content": dedent('''Provide:
                                            - A list where each entry includes the four words closest to the identified spot that clearly indicate where an example would enhance the content (as exemplify_context).
                                            - A list where each entry provides a clear reasoning for why the identified spot critically lacks an example, emphasizing how it impacts clarity, engagement, or persuasiveness (as exemplify_reasoning).
                                            - A list where each entry suggests a specific type of example or approach the user could take to improve the spot, ensuring the suggestion aligns with the context and enhances relatability or evidence (as exemplify_suggestion).
                                           ''')},
        {"role": "user", "content": dedent(f"Essay: {essay}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "exemplify_context": {"type": "array", "items": {"type": "string"}},
                            "exemplify_reasoning": {"type": "array", "items": {"type": "string"}},
                            "exemplify_suggestion": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["exemplify_context", "exemplify_reasoning", "exemplify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        exemplify_context = result.get('exemplify_context', [])
        exemplify_reasoning = result.get('exemplify_reasoning', [])
        exemplify_suggestion = result.get('exemplify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        exemplify_context = []
        exemplify_reasoning = []
        exemplify_suggestion = []



    return jsonify({
        "exemplify_context": exemplify_context,
        "exemplify_reasoning": exemplify_reasoning,
        "exemplify_suggestion": exemplify_suggestion
        })


####### FACTCHECK #######

@app.route('/factcheck', methods=['POST'])
def factcheck():
    data = request.json
    essay = data.get('essay')
    source_text = data.get('source_text')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(factcheck_task)},
        {"role": "user", "content": dedent('''Provide:
                                            - A list where each entry includes the four words closest to the identified spot that clearly indicate the statement or claim requiring fact-checking (as factcheck_context).
                                            - A list where each entry provides an explanation of why the identified spot was chosen, focusing on significant claims that appear unsupported, contradictory, or potentially misleading (as factcheck_reasoning).
                                            - A list where each entry suggests a specific improvement, such as verifying the claim with credible sources, rephrasing for accuracy, or removing unsupported statements (as factcheck_suggestion).
                                           ''')},
        {"role": "user", "content": dedent(f"Essay: {essay}")},
        {"role": "user", "content": dedent(f"Source Text: {source_text}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "factcheck_context": {"type": "array", "items": {"type": "string"}},
                            "factcheck_reasoning": {"type": "array", "items": {"type": "string"}},
                            "factcheck_suggestion": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["factcheck_context", "factcheck_reasoning", "factcheck_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        factcheck_context = result.get('factcheck_context', [])
        factcheck_reasoning = result.get('factcheck_reasoning', [])
        factcheck_suggestion = result.get('factcheck_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        factcheck_context = []
        factcheck_reasoning = []
        factcheck_suggestion = []


    return jsonify({
        "factcheck_context": factcheck_context,
        "factcheck_reasoning": factcheck_reasoning,
        "factcheck_suggestion": factcheck_suggestion,
        })


####### CLARIFY #######

@app.route('/clarify', methods=['POST'])
def clarify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(factcheck_task)},
        {"role": "user", "content": dedent('''Provide:
                                            - A list where each entry includes the four words closest to the identified spot that highlight where deeper exploration or clarification is needed (as clarify_context).
                                            - A list where each entry provides an explanation of why the identified spot was chosen, focusing on areas where key implications, assumptions, or consequences are notably unexplored or vague (as clarify_reasoning).
                                            - A list where each entry suggests a specific way the user could enhance the spot, such as expanding on implications, questioning assumptions, or exploring ethical, moral, social, or practical consequences (as clarify_suggestion).
                                           ''')},
        {"role": "user", "content": dedent(f"Essay: {essay}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "clarify_context": {"type": "array", "items": {"type": "string"}},
                            "clarify_reasoning": {"type": "array", "items": {"type": "string"}},
                            "clarify_suggestion": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["clarify_context", "clarify_reasoning", "clarify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        clarify_context = result.get('clarify_context', [])
        clarify_reasoning = result.get('clarify_reasoning', [])
        clarify_suggestion = result.get('clarify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        clarify_context = []
        clarify_reasoning = []
        clarify_suggestion = []


    return jsonify({
        "clarify_context": clarify_context,
        "clarify_reasoning": clarify_reasoning,
        "clarify_suggestion": clarify_suggestion,

        })


####### ASSERT #######

@app.route('/assert', methods=['POST'])
def assertify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(assert_task)},
        {"role": "user", "content": dedent('''Provide:
                                            - A list where each entry includes the four words closest to the identified spot that clearly indicate where a stronger or more original stance is needed (as assert_context).
                                            - A list where each entry provides an explanation of why the identified spot was chosen, focusing on areas that appear overly neutral, lack conviction, or fail to present a distinct perspective (as assert_reasoning).
                                            - A list where each entry suggests a specific way the user could improve the spot, such as by taking a definitive stance, adding stronger reasoning, or presenting a unique perspective to enhance engagement and persuasiveness (as assert_suggestion).
                                           ''')},
        {"role": "user", "content": dedent(f"Essay: {essay}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "assert_context": {"type": "array", "items": {"type": "string"}},
                            "assert_reasoning": {"type": "array", "items": {"type": "string"}},
                            "assert_suggestion": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["assert_context", "assert_reasoning", "assert_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        assert_context = result.get('assert_context', [])
        assert_reasoning = result.get('assert_reasoning', [])
        assert_suggestion = result.get('assert_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        assert_context = []
        assert_reasoning = []
        assert_suggestion = []


    return jsonify({
        "assert_context": assert_context,
        "assert_reasoning": assert_reasoning,
        "assert_suggestion": assert_suggestion,

        })


####### CREATE DATABASE #######
DATABASE = 'edits.db'

def init_db():
    """Create the edits table if it doesn't already exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                phrase TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                startIndex INTEGER NOT NULL,
                endIndex INTEGER NOT NULL,
                completed BOOLEAN NOT NULL,
                UNIQUE(type, startIndex, endIndex)
            )
                       
                       
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                startIndex INTEGER NOT NULL,
                endIndex INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                edit_content TEXT NOT NULL
            )
        ''')

        conn.commit()

# Call this function to initialize the database
init_db()


####### CLEAR DATABASE #######
def clear_tables():
    """Clear all data in the edits table."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM edits')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="edits"')
        cursor.execute('DELETE FROM user_edits')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="user_edits"')
        conn.commit()

@app.route('/store-edits', methods=['POST'])
def store_llm_edits():
    """Store edits in the database."""
    try:
        # Get data from request
        data = request.get_json()
        if not data or 'edits' not in data:
            return jsonify({"error": "Invalid request, 'edits' key missing"}), 400

        # Handle single edit or multiple edits
        if 'edits' in data:
            edits = data['edits']
        else:
            edits = [data]

        # Store edits in the SQLite database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for edit in edits:
                cursor.execute('''
                    INSERT INTO edits (type, phrase, suggestion, reasoning, startIndex, endIndex, completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    edit['type'],
                    edit['phrase'],
                    edit['suggestion'],
                    edit['reasoning'],
                    edit.get('startIndex'),
                    edit.get('endIndex'),
                    int(edit.get('completed', False))  # Store completed as 0 or 1
                ))
            conn.commit()

        return jsonify({"message": "Edits stored successfully", "edits_count": len(edits)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

####### TOGGLE UPDATE COMPLETITION #######
@app.route('/update-completion', methods=['POST'])
def update_completion():
    try:
        data = request.get_json()

        highlight_id = data.get('highlightId')
        completed = data.get('completed')

        if highlight_id is None or completed is None:
            return jsonify({"error": "Missing highlightId or completed status"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE edits
                SET completed = ?
                WHERE highlight_id = ?
            ''', (completed, highlight_id))
            conn.commit()

        return jsonify({"message": "Completion status updated successfully"}), 200

    except Exception as e:
        print("Error updating completion status:", e)
        return jsonify({"error": str(e)}), 500
    

####### USER EDITS #######
# Store the last known state of the response-box
last_response_text = ""

@app.route('/track-edits', methods=['POST'])
def store_user_edits():
    global last_response_text
    try:
        # Get the current text from the request
        current_text = request.json.get('responseBoxText', '')
        if current_text is None:
            return jsonify({"error": "responseBoxText is missing"}), 400

        # Compare the current text with the last known text
        if last_response_text != current_text:
            # Find the difference
            start_index, end_index, change_type, edit_content = calculate_edit(last_response_text, current_text)

            # Save the change to the database
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_edits (start_index, end_index, change_type, edit_content)
                    VALUES (?, ?, ?, ?)
                ''', (start_index, end_index, change_type, edit_content))
                conn.commit()

            # Update the last known text
            last_response_text = current_text

        return jsonify({"message": "Edit tracked successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_edit(old_text, new_text):
    """Calculate the edit details: start, end indices, type, and content of the change."""
    diff = difflib.SequenceMatcher(None, old_text, new_text)
    start_index = None
    end_index = None
    added_words = []
    deleted_words = []

    # Find changes in the text
    for tag, i1, i2, j1, j2 in diff.get_opcodes():
        if tag == 'replace':
            deleted_words.append(old_text[i1:i2])
            added_words.append(new_text[j1:j2])
            if start_index is None:
                start_index = j1
            end_index = j2
        elif tag == 'delete':
            deleted_words.append(old_text[i1:i2])
            if start_index is None:
                start_index = j1
            end_index = j2
        elif tag == 'insert':
            added_words.append(new_text[j1:j2])
            if start_index is None:
                start_index = j1
            end_index = j2

    # Combine added and deleted words for logging
    edit_content = f"Added: {' '.join(added_words)}; Deleted: {' '.join(deleted_words)}"

    # Determine the type of change
    change_length = len(new_text) - len(old_text)
    change_type = "new essay" if abs(change_length) > 1000 else "user edit"

    # Handle cases where no explicit diff is found
    if start_index is None or end_index is None:
        start_index = 0
        end_index = len(new_text)

    return start_index, end_index, change_type, edit_content

def get_db_connection():
    """Establish and return a database connection."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/get-edits', methods=['GET'])
def get_edits():
    """Retrieve all edits from the database."""
    try:
        with get_db_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL for better concurrency
            conn.commit()  # Ensure all pending writes are committed
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edits ORDER BY id ASC")  # Ensure consistent order
            edits = [dict(row) for row in cursor.fetchall()]

        return jsonify({'edits': edits}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)