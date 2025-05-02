#!/usr/bin/env python3
"""
main.py

Live Chess.com game analysis script:
- Polls Chess.com live PGN callback endpoint with your session cookie
- Uses Stockfish HTTP API for evaluation
- Converts centipawn scores to win probability
- Plots a live-updating Matplotlib graph move-by-move
- Explains major swings via Google Gemini API

Usage:
  pip install python-chess requests google-generative-ai matplotlib
  # Set SESSION_COOKIE from your browser DevTools
  python main.py '<live_game_url>'
"""
import sys
import re
import urllib.parse
import io
import time
import math
import requests
import chess
import chess.pgn
import matplotlib.pyplot as plt
import google.generativeai as genai

# ===== Configuration =====
if len(sys.argv) < 2:
    print("Usage: python main.py '<live_game_url>'")
    sys.exit(1)
LIVE_URL = sys.argv[1]

# Extract game ID
m = re.search(r"/game/live/(\d+)", LIVE_URL)
if not m:
    raise ValueError(f"Invalid live game URL: {LIVE_URL}")
GAME_ID = m.group(1)

# Extract optional username param for PGN
parsed = urllib.parse.urlparse(LIVE_URL)
qs = urllib.parse.parse_qs(parsed.query)
USERNAME = qs.get('username', [None])[0]

# Live PGN endpoint and your session cookie
LIVE_PGN_URL  = f"https://www.chess.com/callback/live/game/{GAME_ID}/pgn"
SESSION_COOKIE = "YOUR_SESSION_COOKIE_HERE"

# Analysis parameters
POLL_INTERVAL   = 2    # seconds
DEPTH           = 15   # Stockfish search depth
SWING_THRESHOLD = 0.10 # 10% win-prob swing

# Stockfish HTTP API (no auth)
STOCKFISH_API_URL = "https://api.stockfish.example.com/analyse"

def stockfish_eval(fen: str) -> int:
    r = requests.post(
        STOCKFISH_API_URL,
        json={'fen': fen, 'depth': DEPTH}
    )
    r.raise_for_status()
    return r.json().get('cp', 0)

def cp_to_prob(cp: int) -> float:
    return 1 / (1 + math.exp(-cp/200.0))

# Gemini API setup
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL   = "chat-bison-001"
genai.configure(api_key=GEMINI_API_KEY)

def explain_turn(idx: int, san: str, prev_p: float, curr_p: float) -> str:
    prompt = (
        f"On half-move {idx}, after '{san}', win probability jumped "
        f"from {prev_p:.2f} to {curr_p:.2f}. Explain what happened on the board."
    )
    resp = genai.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[{'author':'user','content':prompt}],
        temperature=0.7
    )
    return resp.choices[0].message.content

# Fetch live moves

def fetch_moves():
    headers = {'Cookie': SESSION_COOKIE}
    params = {}
    if USERNAME:
        params['username'] = USERNAME
    r = requests.get(LIVE_PGN_URL, headers=headers, params=params)
    r.raise_for_status()
    game = chess.pgn.read_game(io.StringIO(r.text))
    return [node.san() for node in game.mainline()]

# Main loop

def main():
    board = chess.Board()
    seen = []  # last seen moves
    timeseries = []  # list of (idx, san, cp, prob)

    # Setup plot
    plt.ion()
    fig, ax = plt.subplots()
    ax.set_title('Live Win Probability')
    ax.set_xlabel('Half-move')
    ax.set_ylabel('White Win Probability')
    line, = ax.plot([], [], marker='o')
    plt.show()

    print("Starting live analysis...")
    while True:
        moves = fetch_moves()
        new_moves = moves[len(seen):]
        for san in new_moves:
            board.push_san(san)
            cp = stockfish_eval(board.fen())
            prob = cp_to_prob(cp)
            idx = len(timeseries) + 1
            timeseries.append((idx, san, cp, prob))
            print(f"[{idx}] {san} -> cp={cp}, prob={prob:.2f}")

            # Update plot
            xs = [p[0] for p in timeseries]
            ys = [p[3] for p in timeseries]
            line.set_data(xs, ys)
            ax.relim(); ax.autoscale_view()
            fig.canvas.draw(); fig.canvas.flush_events()

            # Detect turning point
            if idx > 1 and abs(prob - timeseries[-2][3]) >= SWING_THRESHOLD:
                explanation = explain_turn(idx, san, timeseries[-2][3], prob)
                print("--> Turning point explanation:")
                print(explanation)
                print('-'*60)

        seen = moves
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()