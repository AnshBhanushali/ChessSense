import io
import requests
import chess.pgn
from config import GAME_PGN_URL

def fetch_moves():
    """
    Fetches PGN and returns list of SAN moves.
    """
    r = requests.get(GAME_PGN_URL)
    r.raise_for_status()
    game = chess.pgn.read_game(io.StringIO(r.text))
    return [node.san() for node in game.mainline()]