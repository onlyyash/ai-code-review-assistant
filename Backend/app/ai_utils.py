import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def get_gemini_feedback(language: str, code: str, review_mode: str = "General") -> str:
    mode_instructions = {
        "General": "Review the code for correctness, bugs, readability, and efficiency.",
        "Security": "Focus on security issues (input validation, injection risks, secrets, unsafe functions) and recommend fixes.",
        "Performance": "Focus on performance bottlenecks, algorithmic complexity, memory usage, and suggest optimizations.",
        "Code Style": "Focus on code style, maintainability, naming, structure, and best practices for the given language.",
    }

    instruction = mode_instructions.get(review_mode, mode_instructions["General"])

    prompt = (
        f"You are a senior software engineer.\n"
        f"{instruction}\n\n"
        f"Analyze this {language} code and provide:\n"
        f"- Bugs\n"
        f"- Suggestions\n"
        f"- Readability score (1-10)\n"
        f"- Efficiency score (1-10)\n"
        f"- Improved version if needed.\n\n"
        f"IMPORTANT: Use Markdown headings exactly as:\n"
        f"### Bugs\n"
        f"### Suggestions\n"
        f"### Readability: X/10\n"
        f"### Efficiency: X/10\n"
        f"### Improved Version\n\n"
        f"Code:\n{code}"
    )

    model = genai.GenerativeModel("models/gemini-2.5-pro")
    response = model.generate_content(prompt)
    return response.text


def parse_ai_feedback(text: str) -> dict:
    # Extract scores
    readability_match = re.search(r"Readability[:\-]?\s*(\d+)/10", text, re.IGNORECASE)
    efficiency_match = re.search(r"Efficiency[:\-]?\s*(\d+)/10", text, re.IGNORECASE)

    readability_score = int(readability_match.group(1)) if readability_match else 0
    efficiency_score = int(efficiency_match.group(1)) if efficiency_match else 0

    # Extract Suggestions
    suggestions = []
    if "### Suggestions" in text:
        suggestions_block = text.split("### Suggestions")[1].split("###")[0]
        suggestions = re.findall(r"\*{1,2}\s*(.+)", suggestions_block)

    # Extract Bugs
    errors = []
    if "### Bugs" in text:
        bugs_block = text.split("### Bugs")[1].split("###")[0]
        errors = re.findall(r"\*{1,2}\s*(.+)", bugs_block)

    # Extract corrected code from Improved Version
    corrected_code = None
    if "### Improved Version" in text:
        improved_block = text.split("### Improved Version", 1)[1]

        # Match the first code block inside that section
        code_match = re.search(r"```(?:[^\n]*)\n(.*?)```", improved_block, re.DOTALL)
        if code_match:
            corrected_code = code_match.group(1).strip()

    return {
        "readability_score": readability_score,
        "efficiency_score": efficiency_score,
        "suggestions": suggestions,
        "errors": errors,
        "corrected_code": corrected_code
    }
