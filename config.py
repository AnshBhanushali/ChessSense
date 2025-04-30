import os

STOCKFISH_PATH = "/Users/anshbhanushali/Downloads/stockfish/stockfish"

# Gemini / Google Generative AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "MISSING_KEY")
GEMINI_MODEL   = "gemini-pro"

# Chess.com Game Config
GAME_ID        = "" 
GAME_PGN_URL   = f"https://www.chess.com/game/export/{GAME_ID}"

# Analysis Settings
POLL_INTERVAL   = 2     # in seconds
DEPTH           = 15    # Stockfish search depth
SWING_THRESHOLD = 0.10  # Evaluation swing threshold
