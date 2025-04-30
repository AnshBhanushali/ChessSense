import math
import chess
import chess.engine
from config import STOCKFISH_PATH, DEPTH

def stockfish_eval(fen: str, depth: int = DEPTH) -> int:
    """
    Run Stockfish locally to get centipawn evaluation for a FEN.
    """
    board = chess.Board(fen)
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    result = engine.analyse(board, chess.engine.Limit(depth=depth))
    score = result["score"].relative.score(mate_score=10000)
    engine.quit()
    return score if score is not None else 0

def cp_to_prob(cp: int) -> float:
    """
    Convert centipawn score to win probability (approximation).
    """
    return 1 / (1 + math.exp(-cp / 200.0))
