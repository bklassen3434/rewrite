from flask import Flask, render_template, request, jsonify
import json
from textwrap import dedent
from openai import OpenAI
import os
from dotenv import load_dotenv

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

clarify_task = '''
    You are a helpful editor. You will be provided with an essay, and your task is to scan the essay for clarity of 
    expression. In other words, find sentences that were unclear.
'''

@app.route('/')
def index():
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


@app.route('/clarify', methods=['POST'])
def clarify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(clarify_task)},
        {"role": "user", "content": dedent(f"Please provide the number of sentences that were unclear.")},
        {"role": "user", "content": dedent(f"Essay: {essay}")}
    ]

    # Call the OpenAI chat completion API for evaluation
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",  # Change this to the appropriate model as needed
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "number_of_unclear_sentences": {"type": "integer"},
                        },
                        "required": ["number_of_unclear_sentences"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        number_of_unclear_sentences = result.get('number_of_unclear_sentences', 0)

    except Exception as e:
        number_of_unclear_sentences = 0

    return jsonify({"number_of_unclear_sentences": number_of_unclear_sentences,})

if __name__ == "__main__":
    app.run(debug=True)