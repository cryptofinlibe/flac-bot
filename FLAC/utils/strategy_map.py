import json
import os

STRATEGY_FILE = "FLAC/data/logs/strategy_map.json"

def load_strategy_map():
    if not os.path.exists(STRATEGY_FILE):
        return {}
    with open(STRATEGY_FILE, "r") as f:
        return json.load(f)

def save_strategy_map(strategy_map):
    with open(STRATEGY_FILE, "w") as f:
        json.dump(strategy_map, f, indent=2)

