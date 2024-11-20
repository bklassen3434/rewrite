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

simplify_task = '''
    You are a helpful editor. You will be provided with an essay, and your task is to identify words that are overly academic or complicated.
    These are words that may be challenging for a general audience to understand easily.
'''

exemplify_task = '''
    You are a helpful editor. You will be provided with an essay, and your task is to identify up to two specific spots within the essay where an example could enhance the content.
    Focus on sections that lack evidence or sound too robotic, and suggest areas where a human or personal experience could make the point more relatable.
'''

factcheck_task = '''
    You are a helpful editor. You will be provided with an essay and a source text. Your task is to identify spots in the essay that may require fact-checking for accuracy.
    Focus on statements that appear unsupported by the source text, lack concrete evidence, or seem questionable in their accuracy.
'''

clarify_task = '''
    You are a helpful editor. You will be provided with an essay, and your task is to identify spots in the text where the user can explore deeper implications of their statements.
    Look for opportunities to investigate ethical, moral, social, or practical consequences or assumptions behind the assertions made in the essay.
    Focus on areas where further reflection or questioning could add depth to the argument or discussion.
'''

assert_task = '''
    You are a helpful editor. You will be provided with an essay, and your task is to identify spots in the text where the user could take a more original and definitive stance.
    Focus on areas that currently seem impartial or neutral, and suggest where the user could add conviction and defend their viewpoint with stronger reasoning and passion.
    Encourage them to assert a unique perspective or argument, creating a more engaging and persuasive essay.
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


####### SIMPLIFY #######

@app.route('/simplify', methods=['POST'])
def simplify():
    data = request.json
    essay = data.get('essay')

    # Prepare messages for evaluation
    messages = [
        {"role": "system", "content": dedent(simplify_task)},
        {"role": "user", "content": dedent('''Provide:
                                           - the count of the number of words (as simplify_number)
                                           - a list with each entry being a word (as simplify_context)
                                           - a list with each entry being a suggestion for a simpler alternative or improvement (as simplify_suggestion)
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
                            "simplify_number": {"type": "integer"},
                            "simplify_context": {"type": "array", "items": {"type": "string"}},
                            "simplify_suggestion": {"type": "array", "items": {"type": "string"}},

                        },
                        "required": ["simplify_number", "simplify_context", "simplify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        simplify_number = result.get('simplify_number', 0)
        simplify_context = result.get('simplify_context', [])
        simplify_suggestion = result.get('simplify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        simplify_number = 0
        simplify_context = []
        simplify_suggestion = []

    return jsonify({
        "simplify_number": simplify_number,
        "simplify_context": simplify_context,
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
                                           - the count of the number of spots (as exemplify_number)
                                           - a list (of length 0, 1 or 2) with each entry being the four words closet to the corresponding spot (as exemplify_context)
                                           - a list (of length 0, 1 or 2) with each entry being the reasoning why each spot was chosen (as exemplify_reasoning)
                                           - a list (of length 0, 1 or 2) with each entry being a suggestion on how the user could improve the spot (as exemplify_suggestion)
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
                            "exemplify_number": {"type": "integer"},
                            "exemplify_context": {"type": "array", "items": {"type": "string"}},
                            "exemplify_reasoning": {"type": "array", "items": {"type": "string"}},
                            "exemplify_suggestion": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["exemplify_number", "exemplify_context", "exemplify_reasoning", "exemplify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        exemplify_number = result.get('exemplify_number', 0)
        exemplify_context = result.get('exemplify_context', [])
        exemplify_reasoning = result.get('exemplify_reasoning', [])
        exemplify_suggestion = result.get('exemplify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        exemplify_number = 0
        exemplify_context = []
        exemplify_reasoning = []
        exemplify_suggestion = []



    return jsonify({
        "exemplify_number": exemplify_number,
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
                                           - the count of the number of spots (as factcheck_number)
                                           - a list with each entry being the four words closet to the corresponding spot (as factcheck_context)
                                           - a list with each entry being the reasoning why each spot was chosen (as factcheck_reasoning)
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
                            "factcheck_number": {"type": "integer"},
                            "factcheck_context": {"type": "array", "items": {"type": "string"}},
                            "factcheck_reasoning": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["factcheck_number", "factcheck_context", "factcheck_reasoning"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        factcheck_number = result.get('factcheck_number', 0)
        factcheck_context = result.get('factcheck_context', [])
        factcheck_reasoning = result.get('factcheck_reasoning', [])

    except Exception as e:
        print(f"Error: {e}")
        factcheck_number = 0
        factcheck_context = []
        factcheck_reasoning = []


    return jsonify({
        "factcheck_number": factcheck_number,
        "factcheck_context": factcheck_context,
        "factcheck_reasoning": factcheck_reasoning
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
                                           - the count of the number of spots (as clarify_number)
                                           - a list with each entry being the four words closet to the corresponding spot (as clarify_context)
                                           - a list with each entry being the reasoning why each spot was chosen (as clarify_reasoning)
                                           - a list with each entry being a suggestion on how the user could improve the spot (as clarify_suggestion)
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
                            "clarify_number": {"type": "integer"},
                            "clarify_context": {"type": "array", "items": {"type": "string"}},
                            "clarify_reasoning": {"type": "array", "items": {"type": "string"}},
                            "clarify_suggestion": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["clarify_number", "clarify_context", "clarify_reasoning", "clarify_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        clarify_number = result.get('clarify_number', 0)
        clarify_context = result.get('clarify_context', [])
        clarify_reasoning = result.get('clarify_reasoning', [])
        clarify_suggestion = result.get('clarify_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        clarify_number = 0
        clarify_context = []
        clarify_reasoning = []
        clarify_suggestion = []


    return jsonify({
        "clarify_number": clarify_number,
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
                                           - the count of the number of spots (as assert_number)
                                           - a list with each entry being the four words closet to the corresponding spot (as assert_context)
                                           - a list with each entry being the reasoning why each spot was chosen (as assert_reasoning)
                                           - a list with each entry being a suggestion on how the user could improve the spot (as assert_suggestion)
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
                            "assert_number": {"type": "integer"},
                            "assert_context": {"type": "array", "items": {"type": "string"}},
                            "assert_reasoning": {"type": "array", "items": {"type": "string"}},
                            "assert_suggestion": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["assert_number", "assert_context", "assert_reasoning", "assert_suggestion"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )

        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        assert_number = result.get('assert_number', 0)
        assert_context = result.get('assert_context', [])
        assert_reasoning = result.get('assert_reasoning', [])
        assert_suggestion = result.get('assert_suggestion', [])

    except Exception as e:
        print(f"Error: {e}")
        assert_number = 0
        assert_context = []
        assert_reasoning = []
        assert_suggestion = []


    return jsonify({
        "assert_number": assert_number,
        "assert_context": assert_context,
        "assert_reasoning": assert_reasoning,
        "assert_suggestion": assert_suggestion,

        })



if __name__ == "__main__":
    app.run(debug=True)