"""OpenAI API prompts."""

__author__ = "Ben Klassen"
__license__ = "MIT"
__version__ = "0.1.0"
__email__ = "bklassen3434@gmail.com"


rewrite = {
    "sys_prompt": """
        You are a helpful educational assistant. You will be provided with a section of a textbook and an essay prompt,
        and your task is to write an essay that answers the essay prompt using the textbook section to support your answer.
    """,
    "task_prompt": None,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "essay_response",
            "schema": {
                "type": "object",
                "properties": {"final_answer": {"type": "string"}},
                "required": ["final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}

simplify = {
    "sys_prompt": """
        You are a precise and discerning editor. You will be provided with an essay, and your task is to identify only words that are exceptionally academic or overly complicated.
        These words must represent a significant barrier to comprehension for a general audience, requiring advanced knowledge or niche expertise to understand easily.
        Ignore words that are simply formal or uncommon but can still be understood in context.
    """,
    "task_prompt": """
        Provide:
        - A list where each entry is an identified word that meets the criteria for being overly academic or complex (as simplify_context).
        - A list where each entry provides an explanation of why the identified word is overly academic or complex and presents a significant barrier to comprehension (as simplify_reasoning).
        - A list where each entry suggests a simpler, equally precise alternative or improvement, ensuring the meaning and tone remain appropriate for the audience (as simplify_suggestion).
    """,
    "response_format": {
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
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}

exemplify = {
    "sys_prompt": """
        You are a meticulous and insightful editor. You will be provided with an essay, and your task is to identify only the most critical spots where an example is essential to enhance clarity, engagement, or persuasiveness.
        Focus on sections that genuinely lack evidence, are difficult to grasp, or feel overly abstract. Ignore areas that are already clear or adequately detailed, even if they could theoretically be improved by an example.
    """,
    "task_prompt": """
        Provide:
        - A list where each entry includes the four words closest to the identified spot that clearly indicate where an example would enhance the content (as exemplify_context).
        - A list where each entry provides a clear reasoning for why the identified spot critically lacks an example, emphasizing how it impacts clarity, engagement, or persuasiveness (as exemplify_reasoning).
        - A list where each entry suggests a specific type of example or approach the user could take to improve the spot, ensuring the suggestion aligns with the context and enhances relatability or evidence (as exemplify_suggestion).
    """,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "evaluation_response",
            "schema": {
                "type": "object",
                "properties": {
                    "exemplify_context": {"type": "array", "items": {"type": "string"}},
                    "exemplify_reasoning": {"type": "array", "items": {"type": "string"}},
                    "exemplify_suggestion": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["exemplify_context", "exemplify_reasoning", "exemplify_suggestion"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}

factcheck = {
    "sys_prompt": """
        You are a meticulous and skeptical editor. You will be provided with an essay and a source text. Your task is to identify only the most critical spots in the essay that require fact-checking for accuracy.
        Focus on statements that directly contradict the source text, make bold or improbable claims without evidence, or are likely to mislead readers if incorrect.
        Avoid flagging general statements or minor details unless they are integral to the argument or significantly impact credibility.
    """,
    "task_prompt": """
        Provide:
        - A list where each entry includes the four words closest to the identified spot that clearly indicate the statement or claim requiring fact-checking (as factcheck_context).
        - A list where each entry provides an explanation of why the identified spot was chosen, focusing on significant claims that appear unsupported, contradictory, or potentially misleading (as factcheck_reasoning).
        - A list where each entry suggests a specific improvement, such as verifying the claim with credible sources, rephrasing for accuracy, or removing unsupported statements (as factcheck_suggestion).
    """,
    "response_format": {
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
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}

clarify = {
    "sys_prompt": """
        You are an incisive and thoughtful editor. You will be provided with an essay, and your task is to identify only the most compelling opportunities for deeper exploration of the text’s ideas.
        Focus on areas where key ethical, moral, social, or practical implications are glaringly unexplored or where a deeper investigation would significantly enhance the argument’s depth and nuance.
        Avoid suggesting reflection for sections that are already clear or sufficiently detailed unless the lack of depth weakens the essay.
    """,
    "task_prompt": """
        Provide:
        - A list where each entry includes the four words closest to the identified spot that highlight where deeper exploration or clarification is needed (as clarify_context).
        - A list where each entry provides an explanation of why the identified spot was chosen, focusing on areas where key implications, assumptions, or consequences are notably unexplored or vague (as clarify_reasoning).
        - A list where each entry suggests a specific way the user could enhance the spot, such as expanding on implications, questioning assumptions, or exploring ethical, moral, social, or practical consequences (as clarify_suggestion).
    """,
    "response_format": {
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
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}


assertive = {
    "sys_prompt": """
        You are a discerning and assertive editor. You will be provided with an essay, and your task is to identify only the areas where the essay most critically lacks originality or conviction.
        Focus on sections that feel notably weak, neutral, or overly cautious, and suggest ways for the user to add a bold, distinctive perspective or stronger reasoning.
        Avoid flagging statements that are already clear or sufficiently assertive unless taking a more definitive stance would meaningfully enhance the essay's persuasiveness and engagement.
    """,
    "task_prompt": """
        Provide:
        - A list where each entry includes the four words closest to the identified spot that clearly indicate where a stronger or more original stance is needed (as assert_context).
        - A list where each entry provides an explanation of why the identified spot was chosen, focusing on areas that appear overly neutral, lack conviction, or fail to present a distinct perspective (as assert_reasoning).
        - A list where each entry suggests a specific way the user could improve the spot, such as by taking a definitive stance, adding stronger reasoning, or presenting a unique perspective to enhance engagement and persuasiveness (as assert_suggestion).
    """,
    "response_format": {
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
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
}
