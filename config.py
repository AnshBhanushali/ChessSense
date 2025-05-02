# config.py
import sys, re, urllib.parse

# 1) Grab your game URL (either argv[1] or prompt)
if len(sys.argv) > 1:
    game_url = sys.argv[1]
else:
    game_url = input("Enter Chess.com live game URL: ")

# 2) Extract the numeric game ID
m = re.search(r"/game/(?:live|daily)/(\d+)", game_url)
if not m:
    raise ValueError(f"Invalid game URL: {game_url}")
GAME_ID = m.group(1)

# 3) (Optional) Pull out the username query-param (for PGN export)
parsed = urllib.parse.urlparse(game_url)
qs = urllib.parse.parse_qs(parsed.query)
USERNAME = qs.get("username", [None])[0]

# 4) Build the PGN export endpoint
PGN_URL = f"https://www.chess.com/game/export/{GAME_ID}.pgn"

# 5) Other constants
STOCKFISH_API_URL = "https://api.stockfish.example.com/analyse"
STOCKFISH_API_KEY = "YOUR_STOCKFISH_API_KEY"
GEMINI_API_KEY    = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL      = "chat-bison-001"
POLL_INTERVAL     = 2     # seconds
DEPTH             = 15    # Stockfish depth
SWING_THRESHOLD   = 0.10  # 10% swing
