import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

def explain_turning_point(halfmove: int, san: str, prev_p: float, new_p: float) -> str:
    """
    Explain a critical turning point using Gemini."""
    prompt = (
        f"On half-move {halfmove}, after '{san}', White’s win probability jumped "
        f"from {prev_p:.2f} to {new_p:.2f}. Explain what happened on the board."
    )
    response = genai.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[{"author": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content