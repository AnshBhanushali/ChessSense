#!/usr/bin/env python3
"""
main.py

Self-contained script for live analysis of a Chess.com game using Selenium for live PGN retrieval:
- Prompts for Chess.com credentials (username & password)
- Automates login to Chess.com via Selenium (headless)
- Fetches live PGN by clicking the "Download PGN" button each poll
- Uses Stockfish API to evaluate each position
- Converts centipawn scores to win probability
- Plots a live-updating graph of win probability vs. half-move
- Detects major probability swings and explains them via Google Gemini API

Usage:
  pip install python-chess requests google-generative-ai matplotlib selenium
  # Ensure chromedriver is installed and in PATH
  python main.py '<live_game_url>'
"""
import sys
import re
import urllib.parse
import io
import time
import math
import getpass

import chess
import chess.pgn
import requests
import matplotlib.pyplot as plt
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===== Configuration =====
def get_game_url():
    return sys.argv[1] if len(sys.argv) > 1 else input("Enter Chess.com live game URL: ")

GAME_URL = get_game_url()

# Extract game ID and optional username param
m = re.search(r"/game/(?:live|daily)/(\d+)", GAME_URL)
if not m:
    raise ValueError(f"Invalid game URL: {GAME_URL}")
GAME_ID = m.group(1)
parsed = urllib.parse.urlparse(GAME_URL)
qs = urllib.parse.parse_qs(parsed.query)
USERNAME_PARAM = qs.get("username", [None])[0]

# Chess.com callback endpoint for PGN
def build_callback_url():
    return f"https://www.chess.com/callback/live/game/{GAME_ID}/pgn"

CALLBACK_PGN_URL = build_callback_url()
# Analysis parameters
POLL_INTERVAL   = 5      # seconds between polls
DEPTH           = 15     # Stockfish search depth
SWING_THRESHOLD = 0.10   # 10% probability swing threshold

# Stockfish API
STOCKFISH_API_URL = "https://api.stockfish.example.com/analyse"
STOCKFISH_API_KEY = "YOUR_STOCKFISH_API_KEY"
headers_sf = {"Authorization": f"Bearer {STOCKFISH_API_KEY}"}

def stockfish_eval(fen: str) -> int:
    payload = {'fen': fen, 'depth': DEPTH}
    r = requests.post(STOCKFISH_API_URL, json=payload, headers=headers_sf)
    r.raise_for_status()
    return r.json().get('cp', 0)

def cp_to_prob(cp: int) -> float:
    return 1 / (1 + math.exp(-cp/200.0))

# Gemini LLM
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL   = "chat-bison-001"
genai.configure(api_key=GEMINI_API_KEY)

def explain_turning_point(idx, san, prev_p, curr_p):
    prompt = (
        f"On half-move {idx}, after '{san}', win probability jumped from {prev_p:.2f} to {curr_p:.2f}. "
        "Explain what happened on the board."
    )
    resp = genai.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[{'author':'user','content':prompt}],
        temperature=0.7
    )
    return resp.choices[0].message.content

# ===== Selenium Setup =====
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# Prompt user for credentials
env_user = input('Chess.com Username: ')
env_pass = getpass.getpass('Chess.com Password: ')

# Login via Selenium
def selenium_login():
    driver.get(f"https://www.chess.com/login_and_go?returnUrl={GAME_URL}")
    wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(env_user)
    driver.find_element(By.ID, 'password').send_keys(env_pass)
    driver.find_element(By.CSS_SELECTOR, 'button.login-button').click()
    wait.until(EC.url_contains('/game/live/'))
    print('Logged in to Chess.com via Selenium')

# Fetch PGN using Selenium
def fetch_moves():
    driver.get(GAME_URL)
    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-export-key='pgn']")))
    btn.click()
    pgn_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea.pgn-data')))
    pgn_text = pgn_area.get_attribute('value')
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    return [node.san() for node in game.mainline()]

# ===== Main Loop =====
def main():
    selenium_login()
    board = chess.Board()
    last_moves = []
    time_series = []  # (idx, san, cp, prob)

    # Setup live plot
    plt.ion()
    fig, ax = plt.subplots()
    ax.set_title('Live Win Probability')
    ax.set_xlabel('Halfmove')
    ax.set_ylabel('White Win Probability')
    line, = ax.plot([], [], marker='o')
    plt.show()

    print('Starting live analysis...')
    while True:
        try:
            moves = fetch_moves()
            print(f"Polled {len(moves)} moves so far.")
            new_moves = moves[len(last_moves):]
            for san in new_moves:
                board.push_san(san)
                cp = stockfish_eval(board.fen())
                prob = cp_to_prob(cp)
                idx = len(time_series) + 1
                time_series.append((idx, san, cp, prob))
                print(f"[{idx}] {san} -> cp={cp}, prob={prob:.2f}")

                # Update plot
                xs = [p[0] for p in time_series]
                ys = [p[3] for p in time_series]
                line.set_data(xs, ys)
                ax.relim(); ax.autoscale_view()
                fig.canvas.draw(); fig.canvas.flush_events()

                # Turning point detection
                if idx > 1 and abs(prob - time_series[-2][3]) >= SWING_THRESHOLD:
                    explanation = explain_turning_point(idx, san, time_series[-2][3], prob)
                    print(f"--> Turning point at {idx} ({san}):")
                    print(explanation)
                    print('-'*60)
            last_moves = moves
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
