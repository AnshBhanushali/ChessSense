import math
import requests
from config import STOCKFISH_API_URL, STOCKFISH_API_KEY, DEPTH

# Prepare headers for Stockfish API authentication
headers = {"Authorization": f"Bearer {STOCKFISH_API_KEY}"}

def stockfish_eval(fen: str, depth: int = DEPTH) -> int:
    """Call Stockfish API for a centipawn score of the given FEN position."""
    payload = {"fen": fen, "depth": depth}
    resp = requests.post(STOCKFISH_API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    # Expecting a JSON response like {"cp": int, "mate": Optional[int]}
    return data.get("cp", 0)


def cp_to_prob(cp: int) -> float:
    """Convert centipawn to White win probability via a logistic function."""
    return 1 / (1 + math.exp(-cp / 200.0))