"""Entry script for ReWrite app."""

import asyncio
import difflib
import json
import os
import sqlite3
from textwrap import dedent

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI, AsyncOpenAI

import prompts

__author__ = "Ben Klassen"
__license__ = "MIT"
__version__ = "0.1.0"
__email__ = "bklassen3434@gmail.com"

# global vars
DATABASE = "edits.db"
last_response_text = ""  # Store the last known state of the response-box


# Get env vars for OpenAI API
load_dotenv("api_key.env")
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Please set it in the .env file.")

# instantiate clients
client = OpenAI(api_key=api_key)
async_client = AsyncOpenAI(api_key=api_key)


### PROMPT OPERATIONS ###


def run_evaluation_prompts(essay, source_text):
    """Run prompts asynchronously to evalaute user essay."""

    async def call_api(type, messages, response_format):
        # Call the OpenAI chat completion API for evaluation
        try:
            print(f"running {type}...")
            chat_completion = await async_client.chat.completions.create(
                messages=messages,
                model="gpt-4o-mini",
                response_format=response_format,
            )

            # Parse the result
            result = json.loads(chat_completion.choices[0].message.content)
            context = result.get(f"{type}_context", [])
            reasoning = result.get(f"{type}_context", [])
            suggestion = result.get(f"{type}_suggestion", [])
            print(f"{type} success!")

        except Exception as e:
            print(f"Error: {e}")
            context = []
            reasoning = []
            suggestion = []
            print(f"{type} failed")

        return {
            "type": f"{type}",
            "edits": {
                "context": context,
                "reasoning": reasoning,
                "suggestion": suggestion,
            },
        }

    async def run_simplify(essay):
        """Run simplify OpenAI request."""
        messages = [
            {"role": "system", "content": dedent(prompts.simplify["sys_prompt"])},
            {"role": "user", "content": dedent(prompts.simplify["task_prompt"])},
            {"role": "user", "content": dedent(f"Essay: {essay}")},
        ]
        return await call_api("simplify", messages, prompts.simplify["response_format"])

    async def run_exemplify(essay):
        """Run exemplify OpenAI request."""
        messages = [
            {"role": "system", "content": dedent(prompts.exemplify["sys_prompt"])},
            {"role": "user", "content": dedent(prompts.exemplify["task_prompt"])},
            {"role": "user", "content": dedent(f"Essay: {essay}")},
        ]
        return await call_api("exemplify", messages, prompts.exemplify["response_format"])

    async def run_factcheck(essay, source_text):
        """Run fact check OpenAI request."""
        messages = [
            {"role": "system", "content": dedent(prompts.factcheck["sys_prompt"])},
            {"role": "user", "content": dedent(prompts.factcheck["task_prompt"])},
            {"role": "user", "content": dedent(f"Essay: {essay}")},
            {"role": "user", "content": dedent(f"Source Text: {source_text}")},
        ]
        return await call_api("factcheck", messages, prompts.factcheck["response_format"])

    async def run_clarify(essay):
        """Run clarify OpenAI request."""
        messages = [
            {"role": "system", "content": dedent(prompts.clarify["sys_prompt"])},
            {"role": "user", "content": dedent(prompts.clarify["task_prompt"])},
            {"role": "user", "content": dedent(f"Essay: {essay}")},
        ]
        return await call_api("clarify", messages, prompts.clarify["response_format"])

    async def run_assertify(essay):
        """Run assert OpenAI request."""
        messages = [
            {"role": "system", "content": dedent(prompts.assertive["sys_prompt"])},
            {"role": "user", "content": dedent(prompts.assertive["task_prompt"])},
            {"role": "user", "content": dedent(f"Essay: {essay}")},
        ]
        return await call_api("assert", messages, prompts.assertive["response_format"])

    async def run_prompts(essay, source_text):
        """Run tasks in defined order at the same time."""
        tasks = []
        async with asyncio.TaskGroup() as group:
            tasks.append(group.create_task(run_simplify(essay)))
            tasks.append(group.create_task(run_exemplify(essay)))
            tasks.append(group.create_task(run_factcheck(essay, source_text)))
            tasks.append(group.create_task(run_clarify(essay)))
            tasks.append(group.create_task(run_assertify(essay)))
        return await asyncio.gather(*tasks)

    # Run prompts in parallel
    results = asyncio.run(run_prompts(essay, source_text))

    # return results list
    return results


### DATABASE OPERATIONS ###


def init_db():
    """Create the edits table if it doesn't already exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
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
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                startIndex INTEGER NOT NULL,
                endIndex INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                edit_content TEXT NOT NULL
            )
        """
        )

        conn.commit()


def get_db_connection():
    """Establish and return a database connection."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def calculate_edit(old_text, new_text):
    """Calculate the edit details: start, end indices, type, and content of the change."""
    diff = difflib.SequenceMatcher(None, old_text, new_text)
    start_index = None
    end_index = None
    added_words = []
    deleted_words = []

    # Find changes in the text
    for tag, i1, i2, j1, j2 in diff.get_opcodes():
        if tag == "replace":
            deleted_words.append(old_text[i1:i2])
            added_words.append(new_text[j1:j2])
            if start_index is None:
                start_index = j1
            end_index = j2
        elif tag == "delete":
            deleted_words.append(old_text[i1:i2])
            if start_index is None:
                start_index = j1
            end_index = j2
        elif tag == "insert":
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


# Create Flask app
app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return "Running!"


@app.route("/generate", methods=["POST"])
def generate_essay():
    data = request.json

    # Prepare messages for ChatGPT API
    messages = [
        {"role": "system", "content": dedent(prompts.rewrite["sys_prompt"])},
        {"role": "user", "content": dedent(f"Textbook: {data.get('source_text')}")},
        {"role": "user", "content": dedent(f"Assignment: {data.get('essay_prompt')}")},
    ]

    # Call the OpenAI chat completion API
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",  # Change this to the appropriate model as needed
            response_format=prompts.rewrite["response_format"],
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        rewritten_text = result.get("final_answer", "No answer provided.")

    except Exception as e:
        rewritten_text = "An unexpected error occurred: " + str(e)

    return jsonify({"response": rewritten_text})


@app.route("/evaluate", methods=["POST"])
def evaluate_essay():
    data = request.json
    essay = data.get("essay")
    source_text = data.get("source_text")

    # run evaluation prompts async
    results = run_evaluation_prompts(essay, source_text)

    # send back results
    return jsonify(results)


@app.route("/clear-tables")
def clear_tables():
    """Clear all data in the edits table."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM edits")
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="edits"')
        cursor.execute("DELETE FROM user_edits")
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="user_edits"')
        conn.commit()
    return "Success!"


@app.route("/store-edits", methods=["POST"])
def store_llm_edits():
    """Store edits in the database."""
    try:
        # Get data from request
        data = request.get_json()
        if not data or "edits" not in data:
            return jsonify({"error": "Invalid request, 'edits' key missing"}), 400

        # Handle single edit or multiple edits
        if "edits" in data:
            edits = data["edits"]
        else:
            edits = [data]

        # Store edits in the SQLite database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for edit in edits:
                cursor.execute(
                    """
                    INSERT INTO edits (type, phrase, suggestion, reasoning, startIndex, endIndex, completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        edit["type"],
                        edit["phrase"],
                        edit["suggestion"],
                        edit["reasoning"],
                        edit.get("startIndex"),
                        edit.get("endIndex"),
                        int(edit.get("completed", False)),  # Store completed as 0 or 1
                    ),
                )
            conn.commit()

        return jsonify({"message": "Edits stored successfully", "edits_count": len(edits)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update-completion", methods=["POST"])
def update_completion():
    try:
        data = request.get_json()

        highlight_id = data.get("highlightId")
        completed = data.get("completed")

        if highlight_id is None or completed is None:
            return jsonify({"error": "Missing highlightId or completed status"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE edits
                SET completed = ?
                WHERE highlight_id = ?
            """,
                (completed, highlight_id),
            )
            conn.commit()

        return jsonify({"message": "Completion status updated successfully"}), 200

    except Exception as e:
        print("Error updating completion status:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/track-edits", methods=["POST"])
def store_user_edits():
    global last_response_text
    try:
        # Get the current text from the request
        current_text = request.json.get("responseBoxText", "")
        if current_text is None:
            return jsonify({"error": "responseBoxText is missing"}), 400

        # Compare the current text with the last known text
        if last_response_text != current_text:
            # Find the difference
            start_index, end_index, change_type, edit_content = calculate_edit(last_response_text, current_text)

            # Save the change to the database
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_edits (start_index, end_index, change_type, edit_content)
                    VALUES (?, ?, ?, ?)
                """,
                    (start_index, end_index, change_type, edit_content),
                )
                conn.commit()

            # Update the last known text
            last_response_text = current_text

        return jsonify({"message": "Edit tracked successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-edits", methods=["GET"])
def get_edits():
    """Retrieve all edits from the database."""
    try:
        with get_db_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL for better concurrency
            conn.commit()  # Ensure all pending writes are committed
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edits ORDER BY id ASC")  # Ensure consistent order
            edits = [dict(row) for row in cursor.fetchall()]

        return jsonify({"edits": edits}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="localhost", port=int(os.environ.get("PORT", 3001)), debug=True)
