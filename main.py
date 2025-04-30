import time
import chess
from config import POLL_INTERVAL, SWING_THRESHOLD
from fetcher import fetch_moves
from evaluator import stockfish_eval, cp_to_prob
from llm_explainer import explain_turning_point


def main():
    board = chess.Board()
    last_moves = []
    time_series = [] 

    print("Starting live analysis...")
    while True:
        try:
            moves = fetch_moves()
            new_moves = moves[len(last_moves):]
            for san in new_moves:
                board.push_san(san)
                fen = board.fen()
                cp = stockfish_eval(fen)
                prob = cp_to_prob(cp)
                idx = len(time_series) + 1
                time_series.append((idx, san, cp, prob))
                print(f"[{idx}] {san} -> cp={cp}, win_prob={prob:.2f}")
                if idx > 1:
                    prev_p = time_series[-2][3]
                    if abs(prob - prev_p) >= SWING_THRESHOLD:
                        expl = explain_turning_point(idx, san, prev_p, prob)
                        print(f"--> Turning point at {idx} ({san}):")
                        print(expl)
                        print("-"*40)
            last_moves = moves
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()